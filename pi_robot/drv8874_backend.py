"""Raspberry Pi 5 GPIO transport for the documented four-driver Rev A board.

The PCB pairs motor_1/2 on LEFT and motor_3/4 on RIGHT. lgpio PWM is
software timed, not RP1 hardware PWM. GPIO write success is not feedback from
the board's enable latch, fault chain, motors, or power supplies.
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


@dataclass(frozen=True)
class DRV8874Config:
    left_polarity: int
    right_polarity: int
    pwm_hz: float = 1000.0
    startup_settle_s: float = 1.0
    reversal_holdoff_s: float = 0.1
    gpiochip: int | None = None

    def __post_init__(self):
        for name in ("left_polarity", "right_polarity"):
            value = getattr(self, name)
            if isinstance(value, bool) or value not in (-1, 1):
                raise ValueError(f"{name} must be explicitly set to -1 or +1")
        for name, low, high in (("pwm_hz", 0.1, 10000),
                                ("startup_settle_s", 0, float("inf")),
                                ("reversal_holdoff_s", 0.001, float("inf"))):
            value = getattr(self, name)
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or not low <= value <= high):
                raise ValueError(f"{name} must be finite and between {low} and {high}")
        if self.gpiochip is not None and (type(self.gpiochip) is not int or self.gpiochip < 0):
            raise ValueError("gpiochip must be a nonnegative device index")


class GPIOError(RuntimeError):
    """An output operation failed; the backend must be restarted."""


class DRV8874RevABackend:
    name = "drv8874_reva"
    NAMES = ("motor_1", "motor_2", "motor_3", "motor_4")
    LEFT_PWM, LEFT_DIR = 18, 23
    RIGHT_PWM, RIGHT_DIR = 13, 5
    RUN, ARM, HB = 25, 17, 27
    PULSE_S = 0.001
    MAX_HB_GAP_S = 0.050
    QUALIFICATION_S = 1.0
    MIN_HB_PULSES = 3

    def __init__(self, config: DRV8874Config, *, gpio_module=None,
                 clock=time.monotonic, sleep=time.sleep, candidate_chips=None):
        self.config = config
        self.clock, self.sleep = clock, sleep
        self._gpio = gpio_module
        self._handle = None
        self._claimed = []
        self._active_pwm = set()
        self._duty = {self.LEFT_PWM: 0.0, self.RIGHT_PWM: 0.0}
        self._direction = {self.LEFT_DIR: 0, self.RIGHT_DIR: 0}
        self._outputs = dict.fromkeys(self.NAMES, 0.0)
        self._armed = False
        self._run = False
        self._failed = False
        self._failure_reason = None
        self._closed = False
        self._last_hb_fall = None
        self._qualification_start = None
        self._qualified_pulses = 0
        self._started = self._time(clock())
        self._chip_number = None
        try:
            if self._gpio is None:
                try:
                    self._gpio = importlib.import_module("lgpio")
                except ImportError as exc:
                    raise RuntimeError("DRV8874 hardware mode requires lgpio on Raspberry Pi 5") from exc
            self._open_chip(candidate_chips)
            # Claim RUN first and atomically request each output's initial low.
            for pin in (self.RUN, self.ARM, self.HB, self.LEFT_PWM,
                        self.RIGHT_PWM, self.LEFT_DIR, self.RIGHT_DIR):
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

    def _open_chip(self, candidates):
        explicit = self.config.gpiochip
        if explicit is not None:
            candidates = [explicit]
        elif candidates is None:
            candidates = sorted(int(path.rsplit("gpiochip", 1)[1])
                                for path in glob.glob("/dev/gpiochip[0-9]*"))
        errors, opened, matches = [], [], []
        try:
            for chip in dict.fromkeys(candidates):
                if type(chip) is not int or chip < 0:
                    raise ValueError("candidate gpiochip indices must be nonnegative integers")
                try:
                    # A non-RP1 chip may be inaccessible. No lines are claimed here.
                    handle = self._gpio.gpiochip_open(chip)
                    if not isinstance(handle, int) or handle < 0:
                        raise RuntimeError(f"open returned {handle!r}")
                    opened.append(handle)
                    info = self._gpio.gpio_get_chip_info(handle)
                    if len(info) != 4 or info[0] < 0:
                        raise RuntimeError("invalid gpiochip info response")
                    _, lines, _, label = info
                    if isinstance(label, bytes):
                        label = label.decode("ascii")
                    if label != "pinctrl-rp1" or lines <= self.HB:
                        raise RuntimeError(f"expected pinctrl-rp1 with GPIO27, found {label!r}")
                    matches.append((handle, chip))
                except Exception as exc:
                    errors.append(f"gpiochip{chip}: {exc}")
            if len(matches) > 1:
                raise RuntimeError("multiple RP1 GPIO devices; select an explicit gpiochip index")
            if not matches:
                raise RuntimeError("No verified RP1 GPIO device: " + ("; ".join(errors) or "none found"))
            self._handle, self._chip_number = matches[0]
        finally:
            close_errors = []
            for handle in opened:
                if handle != self._handle:
                    try:
                        result = self._gpio.gpiochip_close(handle)
                        if isinstance(result, int) and result < 0:
                            raise GPIOError("could not close candidate gpiochip")
                    except BaseException as exc:
                        close_errors.append(exc)
            if close_errors:
                raise close_errors[0]

    def _reset_qualification(self):
        self._qualification_start = None
        self._qualified_pulses = 0

    def _fail_closed(self, reason):
        self._armed = False
        if self._failed:
            self._reset_qualification()
        if self._handle is not None and self.RUN in self._claimed:
            try:
                self._call("gpio_write", self._handle, self.RUN, 0)
                self._run = False
            except BaseException:
                self._run = None
        if self._failed and self._failure_reason is None:
            self._failure_reason = str(reason)

    def _available(self):
        if self._closed:
            raise RuntimeError("DRV8874 backend is closed")
        if self._failed:
            raise GPIOError(f"GPIO state uncertain; restart backend: {self._failure_reason}")

    def _fresh(self, now):
        return self._last_hb_fall is not None and 0 <= now - self._last_hb_fall <= self.MAX_HB_GAP_S

    def _ready(self, now):
        return (not self._closed and not self._failed and self._fresh(now)
                and self._qualification_start is not None
                and now - self._qualification_start >= self.QUALIFICATION_S
                and self._qualified_pulses >= self.MIN_HB_PULSES)

    def check_health(self, now):
        try:
            self._available()
            now = self._time(now)
            if now < self._started or (self._last_hb_fall is not None and now < self._last_hb_fall):
                self._reset_qualification()
                raise RuntimeError("monotonic clock moved backwards")
            if self._armed and not self._fresh(now):
                self._reset_qualification()
                raise RuntimeError("DRV8874 heartbeat deadline exceeded (50 ms)")
        except BaseException as exc:
            self._fail_closed(exc)
            raise

    def _wait_at_least(self, duration):
        start = self._time(self.clock())
        self.sleep(duration)
        elapsed = self._time(self.clock()) - start
        # Do not silently accept an interrupted sleep or a broken injected clock.
        if elapsed + 1e-12 < duration:
            raise RuntimeError("GPIO timing wait did not complete")

    def service(self, now):
        """Feed the hardware watchdog only from a successful controller tick."""
        try:
            self.check_health(now)
            if not self._fresh(now):
                self._reset_qualification()
            if self._last_hb_fall is not None:
                low_elapsed = self._time(self.clock()) - self._last_hb_fall
                if low_elapsed < self.PULSE_S:
                    self._wait_at_least(self.PULSE_S - low_elapsed)
            # A delayed sleep or stale caller timestamp must not feed the watchdog.
            self.check_health(self.clock())
            if not self._fresh(self._time(self.clock())):
                self._reset_qualification()
            self._call("gpio_write", self._handle, self.HB, 1)
            self._wait_at_least(self.PULSE_S)
            self._call("gpio_write", self._handle, self.HB, 0)
            fall = self._time(self.clock())
            if self._last_hb_fall is not None and fall - self._last_hb_fall > self.MAX_HB_GAP_S:
                self._reset_qualification()
                if self._armed:
                    raise RuntimeError("heartbeat pulse missed its deadline")
            self._last_hb_fall = fall
            if fall >= self._started + self.config.startup_settle_s:
                if self._qualification_start is None:
                    self._qualification_start = fall
                self._qualified_pulses += 1
        except BaseException as exc:
            self._fail_closed(exc)
            raise

    def _zero_pin(self, pin):
        if pin in self._active_pwm:
            self._call("tx_pwm", self._handle, pin, 0, 0)
            self._active_pwm.remove(pin)
        self._call("gpio_write", self._handle, pin, 0)
        self._duty[pin] = 0.0

    def quiesce(self):
        """Command PWM low while preserving RUN; Rev A decodes this as brake."""
        try:
            self.check_health(self.clock())
            for pin in (self.LEFT_PWM, self.RIGHT_PWM):
                self._zero_pin(pin)
            self._outputs = dict.fromkeys(self.NAMES, 0.0)
        except BaseException as exc:
            self._fail_closed(exc)
            raise

    def arm(self, now):
        try:
            self.check_health(now)
            if self._armed:
                raise BackendNotReady("already armed; disable before another ARM edge")
            if not self._ready(now):
                raise BackendNotReady("wait for startup settling and one second of stable heartbeats")
            self.quiesce()
            self._call("gpio_write", self._handle, self.ARM, 0)
            self._call("gpio_write", self._handle, self.RUN, 1)
            self._run = True
            self._wait_at_least(self.PULSE_S)
            if not self._fresh(self._time(self.clock())):
                raise BackendNotReady("heartbeat became stale during ARM preparation")
            self._call("gpio_write", self._handle, self.ARM, 1)
            self._wait_at_least(self.PULSE_S)
            self._call("gpio_write", self._handle, self.ARM, 0)
            if not self._fresh(self._time(self.clock())):
                raise BackendNotReady("heartbeat became stale during ARM pulse")
            self._armed = True
        except BaseException as exc:
            self._fail_closed(exc)
            raise

    def apply(self, outputs: Mapping[str, float]):
        try:
            self.check_health(self.clock())
            if not self._armed:
                raise BackendNotReady("explicit ARM is required before applying motor demand")
            if set(outputs) != set(self.NAMES):
                raise ValueError("all four motor channels must be supplied")
            for value in outputs.values():
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or abs(value) > 100):
                    raise ValueError("motor demand must be finite percent in [-100, 100]")
            if outputs["motor_1"] != outputs["motor_2"] or outputs["motor_3"] != outputs["motor_4"]:
                raise ValueError("Rev A requires equal demands within each left/right motor pair")
            sides = ((self.LEFT_PWM, self.LEFT_DIR, outputs["motor_1"], self.config.left_polarity),
                     (self.RIGHT_PWM, self.RIGHT_DIR, outputs["motor_3"], self.config.right_polarity))
            for pwm, direction, demand, polarity in sides:
                duty = abs(float(demand))
                if not duty:
                    self._zero_pin(pwm)
                    continue
                level = int(demand * polarity > 0)
                if level != self._direction[direction]:
                    self._zero_pin(pwm)
                    self._call("gpio_write", self._handle, direction, level)
                    self._direction[direction] = level
                    self._wait_at_least(self.PULSE_S)
                self.check_health(self.clock())
                if pwm not in self._active_pwm or self._duty[pwm] != duty:
                    # A library failure may occur after the worker starts PWM.
                    # Retain a cancellation obligation even without an ACK.
                    self._active_pwm.add(pwm)
                    self._call("tx_pwm", self._handle, pwm, self.config.pwm_hz, duty)
                    self._duty[pwm] = duty
            self._outputs = dict(outputs)
        except BaseException as exc:
            self._fail_closed(exc)
            raise

    def disable(self):
        """RUN low first; attempt every remaining cleanup even if one write fails."""
        self._armed = False
        if self._closed:
            return
        errors = []
        for pin in (self.RUN, self.LEFT_PWM, self.RIGHT_PWM, self.ARM,
                    self.HB, self.LEFT_DIR, self.RIGHT_DIR):
            if pin not in self._claimed:
                continue
            if pin in self._active_pwm:
                try:
                    self._call("tx_pwm", self._handle, pin, 0, 0)
                    self._active_pwm.remove(pin)
                except BaseException as exc:
                    errors.append(exc)
            try:
                self._call("gpio_write", self._handle, pin, 0)
                if pin == self.RUN:
                    self._run = False
                if pin in self._duty:
                    self._duty[pin] = 0.0
                if pin in self._direction:
                    self._direction[pin] = 0
            except BaseException as exc:
                errors.append(exc)
                if pin == self.RUN:
                    self._run = None
        self._outputs = dict.fromkeys(self.NAMES, 0.0)
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

    def describe(self, now):
        try:
            now = self._time(now)
            timing_valid = True
        except ValueError:
            now, timing_valid = self._started, False
        stable = 0.0 if self._qualification_start is None else max(0.0, now - self._qualification_start)
        return {
            "ready": timing_valid and self._ready(now), "armed_commanded": self._armed,
            "timing_valid": timing_valid,
            "run_commanded": self._run, "closed": self._closed,
            "failed": self._failed, "failure_reason": self._failure_reason,
            "gpio_write_state": "uncertain" if self._failed else "commanded",
            "outputs_commanded": dict(self._outputs),
            "physical_enable_observed": None, "physical_stop_confirmed": None,
            "fault_feedback_available": False,
            "readiness_basis": "software timer and heartbeat writes only; no board feedback",
            "pwm_type": "software-timed", "gpiochip": self._chip_number,
            "config": asdict(self.config),
            "qualification": {
                "startup_settle_remaining_s": max(0.0, self._started + self.config.startup_settle_s - now) if timing_valid else None,
                "stable_heartbeat_s": (stable if self._fresh(now) else 0.0) if timing_valid else None,
                "completed_pulses": self._qualified_pulses,
                "required_stable_s": self.QUALIFICATION_S,
                "max_gap_s": self.MAX_HB_GAP_S,
                "last_fall_age_s": None if self._last_hb_fall is None or not timing_valid else now - self._last_hb_fall,
            },
        }
