"""Raspberry Pi 5 GPIO transport for the prototype's two TB6612FNG carriers.

Each motor channel has PWM, IN1 and IN2 inputs; STBY enables a carrier. The two
motors on one side may share a complete pin triple when their carrier inputs
are wired in parallel. lgpio PWM is software timed, not RP1 hardware PWM.

The carriers have no hardware watchdog or arm latch: a frozen process cannot
stop the motors, so a reachable switch on the motor supply is required. GPIO
write success is not feedback from a driver, a motor, or the supply.
"""
from dataclasses import asdict, dataclass
import glob
import importlib
import math
import time
from typing import Mapping

try:
    from .motor_backend import BackendNotReady
except ImportError:
    from motor_backend import BackendNotReady

NAMES = ("motor_1", "motor_2", "motor_3", "motor_4")
# The controller gives equal demand only to the two motors on one side, so
# only they may be wired to the same driver inputs.
SIDE_PAIRS = (("motor_1", "motor_2"), ("motor_3", "motor_4"))


def _is_header_gpio(pin):
    # BCM numbering. GPIO0/1 belong to the HAT ID EEPROM.
    return type(pin) is int and 2 <= pin <= 27


def _require_number(value, name, low, high):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not low <= value <= high):
        raise ValueError(f"{name} must be finite and between {low} and {high}")


@dataclass(frozen=True)
class TB6612Channel:
    pwm: int
    in1: int
    in2: int
    polarity: int

    def __post_init__(self):
        if not all(_is_header_gpio(pin) for pin in self.pins):
            raise ValueError("pwm, in1 and in2 must be BCM GPIO numbers from 2 to 27")
        if len(set(self.pins)) != 3:
            raise ValueError("pwm, in1 and in2 must be three different GPIOs")
        if isinstance(self.polarity, bool) or self.polarity not in (-1, 1):
            raise ValueError("polarity must be explicitly set to -1 or +1")

    @property
    def pins(self):
        return (self.pwm, self.in1, self.in2)


@dataclass(frozen=True)
class TB6612Config:
    channels: Mapping[str, TB6612Channel]
    stby: tuple[int, ...]
    # Full demand maps to this duty. Required: the candidate motor's stall
    # current sits at the TB6612FNG's absolute limit at full supply voltage.
    max_duty_percent: float
    pwm_hz: float = 1000.0
    ramp_percent_per_s: float = 400.0
    reversal_holdoff_s: float = 0.1
    gpiochip: int | None = None

    def __post_init__(self):
        if (not isinstance(self.channels, Mapping) or set(self.channels) != set(NAMES)
                or not all(isinstance(item, TB6612Channel) for item in self.channels.values())):
            raise ValueError("channels must define exactly motor_1 to motor_4")
        object.__setattr__(self, "channels", {name: self.channels[name] for name in NAMES})
        if (not isinstance(self.stby, tuple) or not 1 <= len(self.stby) <= 2
                or len(set(self.stby)) != len(self.stby)
                or not all(_is_header_gpio(pin) for pin in self.stby)):
            raise ValueError("stby must list one or two different BCM GPIO numbers from 2 to 27")
        for index, first in enumerate(NAMES):
            a = self.channels[first]
            if set(a.pins) & set(self.stby):
                raise ValueError(f"{first} reuses a STBY GPIO")
            for second in NAMES[index + 1:]:
                b = self.channels[second]
                if not set(a.pins) & set(b.pins):
                    continue
                if (first, second) not in SIDE_PAIRS or a != b:
                    raise ValueError(
                        f"{first} and {second} may share GPIOs only as one complete "
                        "pwm/in1/in2 triple with equal polarity on the same side")
        for name, low, high in (("max_duty_percent", 1, 100), ("pwm_hz", 0.1, 10000),
                                ("ramp_percent_per_s", 1, 100000),
                                ("reversal_holdoff_s", 0.001, float("inf"))):
            _require_number(getattr(self, name), name, low, high)
        if self.gpiochip is not None and (type(self.gpiochip) is not int or self.gpiochip < 0):
            raise ValueError("gpiochip must be a nonnegative device index")


class GPIOError(RuntimeError):
    """An output operation failed; the backend must be restarted."""


class _Group:
    """One electrical pwm/in1/in2 triple and the motors wired to it."""

    def __init__(self, channel):
        self.pwm, self.in1, self.in2 = self.pins = channel.pins
        self.polarity = channel.polarity
        self.names = []
        self.direction = 0  # Commanded inputs: +1 IN1 high, -1 IN2 high, 0 both low.
        self.duty = 0.0  # Percent most recently requested from the PWM worker.
        self.target = 0.0
        self.pwm_active = False
        self.stepped_at = None  # Start of the next soft-start step; None when settled.


def _open_rp1_chip(gpio, explicit, candidates, highest_pin):
    """Return (handle, index) of the single gpiochip labelled as the Pi 5 header.

    Pi 5 chip numbering differs across kernels, so the label is verified before
    any line is claimed. Mirrors DRV8874RevABackend._open_chip.
    """
    if explicit is not None:
        candidates = [explicit]
    elif candidates is None:
        candidates = sorted(int(path.rsplit("gpiochip", 1)[1])
                            for path in glob.glob("/dev/gpiochip[0-9]*"))
    errors, opened, matches, selected = [], [], [], None
    try:
        for chip in dict.fromkeys(candidates):
            if type(chip) is not int or chip < 0:
                raise ValueError("candidate gpiochip indices must be nonnegative integers")
            try:
                # A non-RP1 chip may be inaccessible. No lines are claimed here.
                handle = gpio.gpiochip_open(chip)
                if not isinstance(handle, int) or handle < 0:
                    raise RuntimeError(f"open returned {handle!r}")
                opened.append(handle)
                info = gpio.gpio_get_chip_info(handle)
                if len(info) != 4 or info[0] < 0:
                    raise RuntimeError("invalid gpiochip info response")
                _, lines, _, label = info
                if isinstance(label, bytes):
                    label = label.decode("ascii")
                if label != "pinctrl-rp1" or lines <= highest_pin:
                    raise RuntimeError(f"expected pinctrl-rp1 with GPIO{highest_pin}, found {label!r}")
                matches.append((handle, chip))
            except Exception as exc:
                errors.append(f"gpiochip{chip}: {exc}")
        if len(matches) > 1:
            raise RuntimeError("multiple RP1 GPIO devices; select an explicit gpiochip index")
        if not matches:
            raise RuntimeError("No verified RP1 GPIO device: " + ("; ".join(errors) or "none found"))
        selected = matches[0]
        return selected
    finally:
        # Every handle except a successfully selected one is released. A close
        # failure here must not replace the selection result or its error.
        for handle in opened:
            if selected is None or handle != selected[0]:
                try:
                    gpio.gpiochip_close(handle)
                except Exception:
                    pass


class TB6612Backend:
    name = "tb6612_dual"
    NAMES = NAMES
    # A late tick must not turn the accumulated time into one large duty step.
    MAX_RAMP_STEP_S = 0.1

    def __init__(self, config: TB6612Config, *, gpio_module=None,
                 clock=time.monotonic, candidate_chips=None):
        self.config = config
        self.clock = clock
        self._gpio = gpio_module
        self._handle = None
        self._chip_number = None
        self._claimed = []
        self._groups: list[_Group] = []
        for name in NAMES:
            channel = config.channels[name]
            group = next((item for item in self._groups if item.pins == channel.pins), None)
            if group is None:
                group = _Group(channel)
                self._groups.append(group)
            group.names.append(name)
        self._outputs = dict.fromkeys(NAMES, 0.0)
        self._armed = False
        self._stby = False  # Commanded level; None after a failed STBY write.
        self._failed = False
        self._failure_reason = None
        self._closed = False
        self._started = self._time(clock())
        try:
            if self._gpio is None:
                try:
                    self._gpio = importlib.import_module("lgpio")
                except ImportError as exc:
                    raise RuntimeError("TB6612 hardware mode requires lgpio on Raspberry Pi 5") from exc
            pins = list(config.stby) + [pin for group in self._groups for pin in group.pins]
            self._handle, self._chip_number = _open_rp1_chip(
                self._gpio, config.gpiochip, candidate_chips, max(pins))
            # Claim STBY first and atomically request each output's initial low.
            for pin in pins:
                self._call("gpio_claim_output", self._handle, pin, 0)
                self._claimed.append(pin)
        except BaseException:
            self._fail_closed("initialization failed")
            self._release_resources()
            raise

    @staticmethod
    def _time(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("monotonic clock must return a finite number")
        return float(value)

    def _call(self, method, *args):
        try:
            result = getattr(self._gpio, method)(*args)
            status = result[0] if isinstance(result, (list, tuple)) else result
            if isinstance(status, (int, float)) and status < 0:
                raise RuntimeError(f"negative status {status}")
            return result
        except Exception as exc:
            self._failed = True
            self._failure_reason = f"{method}: {exc}"
            raise GPIOError(self._failure_reason) from exc

    def _fail_closed(self, reason):
        """Request standby on every carrier without trusting earlier state."""
        self._armed = False
        if self._handle is not None:
            confirmed = True
            for pin in self.config.stby:
                if pin in self._claimed:
                    try:
                        self._call("gpio_write", self._handle, pin, 0)
                    except BaseException:
                        confirmed = False
            self._stby = False if confirmed else None
        if self._failed and self._failure_reason is None:
            self._failure_reason = str(reason)

    def check_health(self, now):
        try:
            if self._closed:
                raise RuntimeError("TB6612 backend is closed")
            if self._failed:
                raise GPIOError(f"GPIO state uncertain; restart backend: {self._failure_reason}")
            if self._time(now) < self._started:
                raise RuntimeError("monotonic clock moved backwards")
        except BaseException as exc:
            self._fail_closed(exc)
            raise

    def _set_duty(self, group, duty):
        if duty <= 0:
            if group.pwm_active:
                self._call("tx_pwm", self._handle, group.pwm, 0, 0)
                group.pwm_active = False
            self._call("gpio_write", self._handle, group.pwm, 0)
            group.duty = 0.0
        elif not group.pwm_active or duty != group.duty:
            # A library failure may occur after the worker starts PWM.
            # Retain a cancellation obligation even without an ACK.
            group.pwm_active = True
            self._call("tx_pwm", self._handle, group.pwm, self.config.pwm_hz, duty)
            group.duty = duty

    def _stop_group(self, group):
        """PWM low, then IN1=IN2=low: the TB6612FNG stop (outputs off) request."""
        group.target = 0.0
        group.stepped_at = None
        self._set_duty(group, 0.0)
        self._call("gpio_write", self._handle, group.in1, 0)
        self._call("gpio_write", self._handle, group.in2, 0)
        group.direction = 0

    def service(self, now):
        """Advance soft start from the controller tick; no watchdog exists to feed."""
        try:
            self.check_health(now)
            now = self._time(now)
            for group in self._groups:
                if not self._armed or group.stepped_at is None:
                    continue
                elapsed = min(max(now - group.stepped_at, 0.0), self.MAX_RAMP_STEP_S)
                self._set_duty(group, min(group.target, group.duty
                                          + self.config.ramp_percent_per_s * elapsed))
                group.stepped_at = now if group.duty < group.target else None
        except BaseException as exc:
            self._fail_closed(exc)
            raise

    def arm(self, now):
        try:
            self.check_health(now)
            if self._armed:
                raise BackendNotReady("already armed; disable before arming again")
            # Leaving standby with a stale input would move a motor at once.
            for group in self._groups:
                self._stop_group(group)
            for pin in self.config.stby:
                self._stby = None
                self._call("gpio_write", self._handle, pin, 1)
            self._stby = True
            self._armed = True
        except BaseException as exc:
            self._fail_closed(exc)
            raise

    def apply(self, outputs: Mapping[str, float]):
        try:
            now = self._time(self.clock())
            self.check_health(now)
            if not self._armed:
                raise BackendNotReady("explicit ARM is required before applying motor demand")
            if set(outputs) != set(NAMES):
                raise ValueError("all four motor channels must be supplied")
            for value in outputs.values():
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or abs(value) > 100):
                    raise ValueError("motor demand must be finite percent in [-100, 100]")
            if any(len({outputs[name] for name in group.names}) != 1 for group in self._groups):
                raise ValueError("motors sharing one pwm/in1/in2 triple require equal demand")
            for group in self._groups:
                demand = float(outputs[group.names[0]])
                if not demand:
                    self._stop_group(group)
                    continue
                direction = group.polarity if demand > 0 else -group.polarity
                if direction != group.direction:
                    # Remove drive first, then lower the old input before raising
                    # the new one: IN1=IN2=high would request a short brake.
                    self._set_duty(group, 0.0)
                    high, low = (group.in1, group.in2) if direction > 0 else (group.in2, group.in1)
                    self._call("gpio_write", self._handle, low, 0)
                    self._call("gpio_write", self._handle, high, 1)
                    group.direction = direction
                    group.stepped_at = None
                group.target = abs(demand) * self.config.max_duty_percent / 100
                if group.target <= group.duty:
                    # Slowing down is immediate; only increases are ramped.
                    self._set_duty(group, group.target)
                    group.stepped_at = None
                elif group.stepped_at is None:
                    group.stepped_at = now
            self._outputs = dict(outputs)
        except BaseException as exc:
            self._fail_closed(exc)
            raise

    def quiesce(self):
        """Stop every channel while keeping STBY high for a following command."""
        try:
            self.check_health(self.clock())
            for group in self._groups:
                self._stop_group(group)
            self._outputs = dict.fromkeys(NAMES, 0.0)
        except BaseException as exc:
            self._fail_closed(exc)
            raise

    def disable(self):
        """STBY low first; attempt every remaining write even if one fails."""
        self._armed = False
        if self._closed:
            return
        errors = []

        def attempt(method, pin, *args):
            if pin not in self._claimed:
                return False
            try:
                self._call(method, self._handle, pin, *args)
                return True
            except BaseException as exc:
                errors.append(exc)
                return False

        lowered = [attempt("gpio_write", pin, 0) for pin in self.config.stby]
        self._stby = False if all(lowered) else None
        for group in self._groups:
            group.target = 0.0
            group.stepped_at = None
            if group.pwm_active and attempt("tx_pwm", group.pwm, 0, 0):
                group.pwm_active = False
            if attempt("gpio_write", group.pwm, 0):
                group.duty = 0.0
            if all([attempt("gpio_write", group.in1, 0), attempt("gpio_write", group.in2, 0)]):
                group.direction = 0
        self._outputs = dict.fromkeys(NAMES, 0.0)
        if errors:
            self._fail_closed(errors[0])
            raise errors[0]

    def _release_resources(self):
        errors = []
        if self._handle is not None:
            for pin in reversed(self._claimed):
                try:
                    self._call("gpio_free", self._handle, pin)
                except BaseException as exc:
                    errors.append(exc)
            try:
                self._call("gpiochip_close", self._handle)
            except BaseException as exc:
                errors.append(exc)
            self._handle = None
        self._claimed.clear()
        self._closed = True
        return errors

    def close(self):
        if self._closed:
            return
        errors = []
        try:
            self.disable()
        except BaseException as exc:
            errors.append(exc)
        errors.extend(self._release_resources())
        if errors:
            raise errors[0]

    def _per_motor(self, field):
        return {name: getattr(group, field) for group in self._groups for name in group.names}

    def describe(self, now):
        try:
            self._time(now)
            timing_valid = True
        except ValueError:
            timing_valid = False
        return {
            "ready": timing_valid and not self._closed and not self._failed,
            "armed_commanded": self._armed, "timing_valid": timing_valid,
            "stby_commanded": self._stby, "closed": self._closed,
            "failed": self._failed, "failure_reason": self._failure_reason,
            "gpio_write_state": "uncertain" if self._failed else "commanded",
            "outputs_commanded": dict(self._outputs),
            "duty_percent": self._per_motor("duty"),
            "target_duty_percent": self._per_motor("target"),
            "physical_enable_observed": None, "physical_stop_confirmed": None,
            "fault_feedback_available": False, "hardware_watchdog": False,
            "pwm_type": "software-timed", "gpiochip": self._chip_number,
            "config": asdict(self.config),
        }
