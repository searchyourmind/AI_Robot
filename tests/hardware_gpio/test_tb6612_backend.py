"""TB6612 GPIO protocol tests with a fake clock and chip; no real GPIO is opened."""
import json
import math
from pathlib import Path

import pytest

from pi_robot import motor_runtime
from pi_robot.motor_backend import BackendNotReady, MockBackend
from pi_robot.tb6612_backend import (
    NAMES, GPIOError, TB6612Backend, TB6612Channel, TB6612Config,
)

# Left pair and right pair each wired in parallel to one pin triple, one STBY.
SHARED = {"motor_1": (18, 23, 24), "motor_2": (18, 23, 24),
          "motor_3": (13, 5, 6), "motor_4": (13, 5, 6)}
# Every carrier channel on its own GPIOs, one STBY per carrier.
SEPARATE = {"motor_1": (18, 23, 24), "motor_2": (12, 16, 20),
            "motor_3": (13, 5, 6), "motor_4": (19, 26, 21)}
EXAMPLE = Path(motor_runtime.__file__).parent / "config" / "tb6612_dual.example.json"


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakeGPIO:
    """Track levels and PWM workers; inject an error or negative status on demand."""

    def __init__(self, labels=None):
        self.labels = labels or {0: "pinctrl-rp1"}
        self.events = []
        self.claimed = set()
        self.levels = {}
        self.pwm = {}  # Active software PWM: pin -> duty percent.
        self.failure = None

    def _record(self, op, *args):
        self.events.append((op, args))
        if self.failure and self.failure[0](op, args):
            _, result, once = self.failure
            if once:
                self.failure = None
            if isinstance(result, BaseException):
                raise result
            return result
        return 0

    def gpiochip_open(self, chip):
        result = self._record("open", chip)
        return result if result < 0 else chip + 100

    def gpio_get_chip_info(self, handle):
        result = self._record("info", handle - 100)
        return [result, 54, f"gpiochip{handle - 100}", self.labels[handle - 100]]

    def gpiochip_close(self, handle):
        return self._record("close", handle - 100)

    def gpio_claim_output(self, handle, pin, level=0):
        result = self._record("claim", pin, level)
        if result >= 0:
            self.claimed.add(pin)
            self.levels[pin] = level
        return result

    def gpio_write(self, handle, pin, level):
        result = self._record("write", pin, level)
        if result >= 0:
            assert pin in self.claimed
            self.levels[pin] = level
        return result

    def tx_pwm(self, handle, pin, hz, duty):
        result = self._record("pwm", pin, hz, duty)
        if result < 0:
            return result
        assert pin in self.claimed
        if hz == 0:
            if pin not in self.pwm:
                return -86
            del self.pwm[pin]
        else:
            self.pwm[pin] = duty
        return 7  # Successful PWM does not necessarily return zero.

    def gpio_free(self, handle, pin):
        result = self._record("free", pin)
        if result >= 0:
            self.claimed.discard(pin)
        return result


def make_config(pins=SHARED, polarity=(1, 1, -1, -1), stby=(25,), max_duty_percent=40, **extra):
    channels = {name: TB6612Channel(*pins[name], polarity[index])
                for index, name in enumerate(NAMES)}
    return TB6612Config(channels, stby, max_duty_percent, **extra)


def make_backend(**config):
    clock, gpio = Clock(), FakeGPIO()
    backend = TB6612Backend(make_config(**config), gpio_module=gpio, clock=clock,
                            candidate_chips=[0])
    return backend, gpio, clock


def armed(**config):
    backend, gpio, clock = make_backend(**config)
    backend.arm(clock())
    gpio.events.clear()
    return backend, gpio, clock


def demands(left, right):
    return dict(zip(NAMES, (left, left, right, right)))


def ramp(backend, clock, ticks=40):
    for _ in range(ticks):
        clock.advance(.02)
        backend.service(clock())


def writes(gpio):
    return [args for op, args in gpio.events if op == "write"]


@pytest.mark.parametrize("args", [
    (1, 23, 24, 1), (28, 23, 24, 1), (18, True, 24, 1), (18.0, 23, 24, 1),
    (18, 18, 24, 1), (18, 23, 24, 0), (18, 23, 24, True), (18, 23, 24, None),
])
def test_rejects_invalid_channel(args):
    with pytest.raises(ValueError):
        TB6612Channel(*args)


@pytest.mark.parametrize("kwargs", [
    {"stby": ()}, {"stby": (25, 17, 27)}, {"stby": (25, 25)}, {"stby": [25]},
    {"stby": (24,)}, {"stby": (1,)},
    {"max_duty_percent": 0}, {"max_duty_percent": 101}, {"max_duty_percent": math.nan},
    {"max_duty_percent": True},
    {"pwm_hz": 10001}, {"ramp_percent_per_s": 0}, {"reversal_holdoff_s": 0},
    {"gpiochip": True}, {"gpiochip": -1},
    # Same PWM pin but different direction pins is not one complete triple.
    {"pins": {**SEPARATE, "motor_2": (18, 16, 20)}},
    # Left and right receive different demand in a turn, so must not share,
    # even as one complete triple with equal polarity.
    {"pins": {**SEPARATE, "motor_3": (18, 23, 24)}, "polarity": (1, 1, 1, -1)},
    # A shared triple cannot give its two motors different polarity.
    {"polarity": (1, -1, -1, -1)},
])
def test_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        make_config(**kwargs)


def test_rejects_missing_or_extra_motor():
    channels = dict(make_config().channels)
    with pytest.raises(ValueError):
        TB6612Config({**channels, "motor_5": channels["motor_1"]}, (25,), 40)
    del channels["motor_4"]
    with pytest.raises(ValueError):
        TB6612Config(channels, (25,), 40)


def test_startup_claims_standby_first_and_every_output_low_without_arming():
    backend, gpio, clock = make_backend()
    assert gpio.events == [("open", (0,)), ("info", (0,))] + [
        ("claim", (pin, 0)) for pin in (25, 18, 23, 24, 13, 5, 6)]
    status = backend.describe(clock())
    assert status["ready"] and not status["armed_commanded"] and status["stby_commanded"] is False
    assert not gpio.pwm and not any(gpio.levels.values())


def test_separate_wiring_claims_each_triple_and_both_standby_pins():
    backend, gpio, clock = make_backend(pins=SEPARATE, stby=(25, 17), polarity=(1, -1, -1, 1))
    assert [args[0] for op, args in gpio.events if op == "claim"] == [
        25, 17, 18, 23, 24, 12, 16, 20, 13, 5, 6, 19, 26, 21]
    backend.arm(clock())
    assert gpio.levels[25] == gpio.levels[17] == 1
    # Without shared inputs each motor has its own polarity and demand.
    backend.apply(dict(zip(NAMES, (50, 50, 50, 50))))
    assert [gpio.levels[pin] for pin in (23, 24, 16, 20, 5, 6, 26, 21)] == [1, 0, 0, 1, 0, 1, 1, 0]
    backend.apply(dict(zip(NAMES, (50, 20, 50, 50))))
    ramp(backend, clock)
    assert gpio.pwm == {18: 20, 12: 8, 13: 20, 19: 20}


def test_hardware_mode_requires_lgpio():
    with pytest.raises(RuntimeError, match="lgpio"):
        TB6612Backend(make_config())


def test_demand_before_arm_is_rejected_and_standby_stays_low():
    backend, gpio, clock = make_backend()
    with pytest.raises(BackendNotReady):
        backend.apply(demands(30, 30))
    assert gpio.levels[25] == 0 and not gpio.pwm
    assert not any(gpio.levels[pin] for pin in (23, 24, 5, 6))


def test_arm_lowers_every_input_before_raising_standby():
    backend, gpio, clock = make_backend()
    gpio.events.clear()
    backend.arm(clock())
    assert writes(gpio)[-1] == (25, 1)
    assert {pin for pin, level in writes(gpio)[:-1] if level == 0} == {18, 23, 24, 13, 5, 6}
    assert backend.describe(clock())["stby_commanded"] is True
    with pytest.raises(BackendNotReady, match="already armed"):
        backend.arm(clock())
    # A rejected request revokes permission rather than leaving it ambiguous.
    assert gpio.levels[25] == 0 and not backend.describe(clock())["armed_commanded"]


def test_forward_sets_direction_then_ramps_to_the_scaled_duty():
    backend, gpio, clock = armed()
    backend.apply(demands(50, 50))
    # Left polarity +1 drives IN1; right polarity -1 drives IN2.
    assert [gpio.levels[pin] for pin in (23, 24, 5, 6)] == [1, 0, 0, 1]
    assert not gpio.pwm, "PWM starts from the controller tick, not at full target"
    seen = []
    for _ in range(5):
        clock.advance(.02)
        backend.service(clock())
        seen.append(gpio.pwm.get(18))
    # 400 %/s for 20 ms is 8 %; 50 % demand of a 40 % ceiling is 20 %.
    assert seen == pytest.approx([8, 16, 20, 20, 20])
    assert gpio.pwm[13] == pytest.approx(20)
    assert sum(op == "pwm" for op, _ in gpio.events) == 6, "no PWM calls once settled"
    assert backend.describe(clock())["duty_percent"] == pytest.approx(dict.fromkeys(NAMES, 20))


def test_full_demand_never_exceeds_the_configured_ceiling():
    backend, gpio, clock = armed(max_duty_percent=35)
    backend.apply(demands(100, -100))
    ramp(backend, clock)
    duties = [args[2] for op, args in gpio.events if op == "pwm"]
    assert max(duties) == 35 and gpio.pwm == {18: 35, 13: 35}
    # Forward on left drives IN1; reverse on the inverted right side also drives IN1.
    assert [gpio.levels[pin] for pin in (23, 24, 5, 6)] == [1, 0, 1, 0]


def test_late_tick_is_one_bounded_step_not_a_jump_to_target():
    backend, gpio, clock = armed(max_duty_percent=100, ramp_percent_per_s=100)
    backend.apply(demands(100, 100))
    clock.advance(5)
    backend.service(clock())
    assert gpio.pwm == {18: pytest.approx(10), 13: pytest.approx(10)}


def test_slowing_down_is_immediate_and_repeated_demand_keeps_ramp_progress():
    backend, gpio, clock = armed()
    backend.apply(demands(100, 100))
    clock.advance(.02)
    backend.service(clock())
    backend.apply(demands(100, 100))
    clock.advance(.02)
    backend.service(clock())
    assert gpio.pwm[18] == pytest.approx(16), "a repeated command must not restart the ramp"
    ramp(backend, clock)
    backend.apply(demands(25, 25))
    assert gpio.pwm == {18: 10, 13: 10}


def test_direction_change_removes_drive_and_never_raises_both_inputs():
    backend, gpio, clock = armed()
    backend.apply(demands(50, 50))
    ramp(backend, clock)
    gpio.events.clear()
    backend.apply(demands(-50, -50))
    left = [(op, args) for op, args in gpio.events if args[0] in (18, 23, 24)]
    assert left == [("pwm", (18, 0, 0)), ("write", (18, 0)), ("write", (23, 0)), ("write", (24, 1))]
    assert not gpio.pwm, "the opposite direction ramps again from zero"
    ramp(backend, clock)
    assert gpio.pwm == {18: 20, 13: 20}


def test_one_stopped_side_does_not_disturb_the_other():
    backend, gpio, clock = armed()
    backend.apply(demands(50, 50))
    ramp(backend, clock)
    backend.apply(demands(0, 50))
    assert gpio.pwm == {13: 20}
    assert [gpio.levels[pin] for pin in (18, 23, 24, 25)] == [0, 0, 0, 1]


def test_quiesce_stops_channels_but_keeps_standby_for_the_next_command():
    backend, gpio, clock = armed()
    backend.apply(demands(50, 50))
    ramp(backend, clock)
    backend.quiesce()
    assert not gpio.pwm and gpio.levels[25] == 1
    assert not any(gpio.levels[pin] for pin in (18, 23, 24, 13, 5, 6))
    backend.apply(demands(50, 50))
    ramp(backend, clock)
    assert gpio.pwm == {18: 20, 13: 20}


def test_disable_lowers_standby_before_anything_else_and_can_repeat():
    backend, gpio, clock = armed()
    backend.apply(demands(50, 50))
    ramp(backend, clock)
    gpio.events.clear()
    backend.disable()
    assert gpio.events[0] == ("write", (25, 0))
    assert not gpio.pwm and not any(gpio.levels.values())
    with pytest.raises(BackendNotReady):
        backend.apply(demands(50, 50))
    gpio.events.clear()
    backend.disable()
    assert not any(op == "pwm" for op, _ in gpio.events), "inactive PWM is not cancelled twice"


def test_unequal_demand_on_a_shared_triple_is_rejected_before_any_output():
    backend, gpio, clock = armed()
    with pytest.raises(ValueError, match="equal demand"):
        backend.apply(dict(zip(NAMES, (50, 40, 50, 50))))
    assert writes(gpio) == [(25, 0)] and not gpio.pwm


@pytest.mark.parametrize("bad", [math.nan, math.inf, 101, True, "50"])
def test_invalid_demand_value_is_rejected(bad):
    backend, gpio, clock = armed()
    with pytest.raises(ValueError):
        backend.apply(demands(bad, 50))
    assert gpio.levels[25] == 0 and not gpio.pwm


def test_incomplete_demand_is_rejected():
    backend, gpio, clock = armed()
    with pytest.raises(ValueError, match="all four"):
        backend.apply({"motor_1": 10})
    assert gpio.levels[25] == 0 and not gpio.pwm


@pytest.mark.parametrize("result", [-1, OSError("bus error")])
def test_gpio_failure_latches_the_backend_and_requests_standby(result):
    backend, gpio, clock = armed()
    backend.apply(demands(50, 50))
    gpio.failure = (lambda op, args: op == "pwm" and args[0] == 13, result, True)
    clock.advance(.02)
    with pytest.raises(GPIOError):
        backend.service(clock())
    status = backend.describe(clock())
    assert status["failed"] and status["gpio_write_state"] == "uncertain" and not status["ready"]
    assert gpio.levels[25] == 0
    with pytest.raises(GPIOError, match="restart"):
        backend.arm(clock())
    # A started-but-unacknowledged PWM worker is still cancelled on disable.
    gpio.pwm[13] = 8
    backend.disable()
    assert not gpio.pwm and not any(gpio.levels.values())


def test_disable_attempts_every_pin_when_one_write_fails():
    backend, gpio, clock = armed()
    backend.apply(demands(50, 50))
    ramp(backend, clock)
    gpio.failure = (lambda op, args: op == "write" and args == (18, 0), -1, False)
    with pytest.raises(GPIOError):
        backend.disable()
    assert gpio.levels[25] == 0 and not gpio.pwm
    assert not any(gpio.levels[pin] for pin in (23, 24, 13, 5, 6))
    assert backend.describe(clock())["failed"]


def test_failed_standby_write_is_reported_as_unknown():
    backend, gpio, clock = armed()
    gpio.failure = (lambda op, args: op == "write" and args == (25, 0), -1, False)
    with pytest.raises(GPIOError):
        backend.disable()
    assert backend.describe(clock())["stby_commanded"] is None


def test_clock_moving_backwards_or_invalid_revokes_permission():
    backend, gpio, clock = armed()
    with pytest.raises(RuntimeError, match="backwards"):
        backend.check_health(clock() - 1)
    assert gpio.levels[25] == 0
    backend, gpio, clock = armed()
    with pytest.raises(ValueError):
        backend.service(math.nan)
    assert gpio.levels[25] == 0
    status = backend.describe(math.nan)
    assert status["timing_valid"] is False and status["ready"] is False
    json.dumps(status, allow_nan=False)


def test_close_releases_every_line_and_is_idempotent():
    backend, gpio, clock = armed()
    backend.apply(demands(50, 50))
    ramp(backend, clock)
    backend.close()
    assert not gpio.claimed and not gpio.pwm and gpio.events[-1] == ("close", (0,))
    count = len(gpio.events)
    backend.close()
    backend.disable()
    assert len(gpio.events) == count
    with pytest.raises(RuntimeError, match="closed"):
        backend.check_health(clock())


def test_discovers_rp1_by_label_and_closes_other_candidates():
    gpio = FakeGPIO({0: "gpio-brcmstb@107d508500", 4: "pinctrl-rp1"})
    backend = TB6612Backend(make_config(), gpio_module=gpio, clock=Clock(), candidate_chips=[0, 4])
    assert backend.describe(10.0)["gpiochip"] == 4
    assert ("close", (0,)) in gpio.events and ("close", (4,)) not in gpio.events


@pytest.mark.parametrize("labels,config", [
    ({0: "gpio-brcmstb@107d508500"}, {}),
    ({0: "pinctrl-rp1", 4: "pinctrl-rp1"}, {}),
    ({0: "pinctrl-rp1", 4: "gpio-brcmstb@107d508500"}, {"gpiochip": 4}),
])
def test_unverified_chip_claims_no_lines_and_leaks_no_handle(labels, config):
    gpio = FakeGPIO(labels)
    with pytest.raises(RuntimeError):
        TB6612Backend(make_config(**config), gpio_module=gpio, clock=Clock(),
                      candidate_chips=list(labels))
    opened = [args for op, args in gpio.events if op == "open"]
    assert opened == [args for op, args in gpio.events if op == "close"]
    assert not any(op == "claim" for op, _ in gpio.events)


def test_failed_claim_releases_lines_already_claimed():
    gpio = FakeGPIO()
    gpio.failure = (lambda op, args: op == "claim" and args[0] == 23, -1, True)
    with pytest.raises(GPIOError):
        TB6612Backend(make_config(), gpio_module=gpio, clock=Clock(), candidate_chips=[0])
    assert not gpio.claimed and gpio.events[-1] == ("close", (0,))


# Service configuration.

def config_file(tmp_path, **changes):
    data = json.loads(EXAMPLE.read_text())
    for name, polarity in zip(NAMES, (1, 1, -1, -1)):
        data["channels"][name]["polarity"] = polarity
    data.update(changes)
    path = tmp_path / "motor.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_example_configuration_must_be_edited_before_use():
    with pytest.raises(ValueError, match="polarity"):
        motor_runtime.load_tb6612_config(EXAMPLE)


def test_example_configuration_loads_once_polarity_is_set(tmp_path):
    config = motor_runtime.load_tb6612_config(config_file(tmp_path))
    assert {name: channel.pins for name, channel in config.channels.items()} == SHARED
    assert config.stby == (25,) and config.max_duty_percent == 40


@pytest.mark.parametrize("changes", [
    {"stby": 25}, {"stby": []}, {"channels": []}, {"channels": {}},
    {"max_duty_percent": None}, {"max_duty_percent": "40"}, {"pins": [1, 2, 3]},
    {"channels": {name: {"pwm": 18, "in1": 23, "in2": 24} for name in NAMES}},
    {"channels": {name: {"pwm": 18, "in1": 23, "in2": 24, "polarity": 1, "brake": 1}
                  for name in NAMES}},
])
def test_invalid_configuration_fails_before_gpio(tmp_path, changes):
    with pytest.raises(ValueError):
        motor_runtime.create_controller_from_env({
            "MOTOR_BACKEND": "tb6612_dual", "MOTOR_CONFIG": config_file(tmp_path, **changes)})


@pytest.mark.parametrize("missing", ["channels", "stby", "max_duty_percent"])
def test_required_fields_have_no_default(tmp_path, missing):
    path = config_file(tmp_path)
    data = json.loads(Path(path).read_text())
    del data[missing]
    Path(path).write_text(json.dumps(data))
    with pytest.raises(ValueError, match="explicitly set"):
        motor_runtime.load_tb6612_config(path)


def test_backend_selection_names_both_hardware_backends(tmp_path):
    with pytest.raises(ValueError, match="tb6612_dual"):
        motor_runtime.create_controller_from_env({"MOTOR_BACKEND": "tb6612"})
    with pytest.raises(ValueError, match="MOTOR_CONFIG"):
        motor_runtime.create_controller_from_env({"MOTOR_BACKEND": "tb6612_dual"})


def test_explicit_backend_uses_prototype_identities_with_configured_pins(tmp_path, monkeypatch):
    from pi_robot import tb6612_backend

    class RecordingBackend(MockBackend):
        name = "tb6612_dual"

        def __init__(self, config):
            super().__init__(NAMES)
            self.config = config

    monkeypatch.setattr(tb6612_backend, "TB6612Backend", RecordingBackend)
    controller = motor_runtime.create_controller_from_env({
        "MOTOR_BACKEND": "tb6612_dual",
        "MOTOR_CONFIG": config_file(tmp_path, reversal_holdoff_s=0.25)})
    assert [(ch.driver, ch.driver_channel) for ch in controller.channels] == [
        ("board_a", "A"), ("board_b", "A"), ("board_a", "B"), ("board_b", "B")]
    assert [ch.control_pins for ch in controller.channels] == [SHARED[name] for name in NAMES]
    assert [ch.polarity for ch in controller.channels] == [1, 1, -1, -1]
    assert controller.reversal_holdoff_s == 0.25
    assert not controller.armed and not any(controller.outputs.values())
    controller.shutdown()


# Flask API -> controller -> backend -> fake GPIO.

def make_api():
    from pi_robot.motor_control import MotorController
    from pi_robot.web_motor import create_app
    backend, gpio, clock = make_backend()
    controller = MotorController(backend, clock, reversal_holdoff_s=.1)
    client = create_app(controller).test_client()
    identity = {"source": "browser", "session": "gpio_session_123"}
    response = client.post("/cmd", json={"c": "arm", **identity})
    assert response.status_code == 200, response.json
    identity["lease"] = response.json["lease"]
    return backend, gpio, clock, controller, client, identity


def tick(controller, clock, count):
    for _ in range(count):
        clock.advance(.019)
        controller.tick()


def test_api_arm_raises_standby_without_any_drive():
    backend, gpio, clock, controller, client, identity = make_api()
    assert gpio.levels[25] == 1 and not gpio.pwm
    assert not any(gpio.levels[pin] for pin in (18, 23, 24, 13, 5, 6))
    status = client.get("/status").json
    assert status["backend"] == "tb6612_dual" and status["physical_backend"] is True
    assert status["physical_actuation_enabled"] is None
    assert status["hardware"]["hardware_watchdog"] is False
    controller.shutdown()


def test_api_forward_ramps_then_reversal_waits_with_drive_removed():
    backend, gpio, clock, controller, client, identity = make_api()
    forward = client.post("/cmd", json={"c": "fwd", "speed": 50, "duration": .8, **identity})
    assert forward.status_code == 200
    tick(controller, clock, 4)
    assert gpio.pwm == {18: 20, 13: 20}
    reverse = client.post("/cmd", json={"c": "back", "speed": 50, "duration": .8, **identity})
    assert reverse.status_code == 200 and reverse.json["pending_reversal"]
    assert not gpio.pwm and gpio.levels[25] == 1
    assert not any(gpio.levels[pin] for pin in (23, 24, 5, 6))
    tick(controller, clock, 4)
    assert not gpio.pwm, "holdoff has not elapsed"
    tick(controller, clock, 2)
    assert [gpio.levels[pin] for pin in (23, 24, 5, 6)] == [0, 1, 1, 0]
    tick(controller, clock, 4)
    assert gpio.pwm == {18: 20, 13: 20}
    controller.shutdown()


def test_api_turn_drives_the_two_sides_in_opposite_directions():
    backend, gpio, clock, controller, client, identity = make_api()
    assert client.post("/cmd", json={"c": "left", "speed": 100, "duration": .5, **identity}).status_code == 200
    tick(controller, clock, 8)
    # Left side reverses (IN2); the inverted right side goes forward (IN2).
    assert [gpio.levels[pin] for pin in (23, 24, 5, 6)] == [0, 1, 0, 1]
    assert gpio.pwm == {18: 40, 13: 40}
    controller.shutdown()


def test_api_command_expiry_and_stop_both_lower_standby_and_cancel_pwm():
    backend, gpio, clock, controller, client, identity = make_api()
    assert client.post("/cmd", json={"c": "fwd", "speed": 50, "duration": .08, **identity}).status_code == 200
    tick(controller, clock, 5)
    assert client.get("/status").json["reason"] == "command-expired"
    assert gpio.levels[25] == 0 and not gpio.pwm and not any(gpio.levels.values())

    backend, gpio, clock, controller, client, identity = make_api()
    assert client.post("/cmd", json={"c": "fwd", "speed": 50, "duration": .8, **identity}).status_code == 200
    tick(controller, clock, 4)
    stopped = client.post("/cmd", json={"c": "stop"})
    assert stopped.status_code == 200 and stopped.json["state"] == "stopped"
    assert gpio.levels[25] == 0 and not gpio.pwm and not any(gpio.levels.values())
    controller.shutdown()


def test_api_gpio_failure_latches_a_fault_that_reset_cannot_clear():
    backend, gpio, clock, controller, client, identity = make_api()
    gpio.failure = (lambda op, args: op == "write" and args == (23, 1), -1, True)
    failed = client.post("/cmd", json={"c": "fwd", "speed": 50, "duration": .8, **identity})
    assert failed.status_code == 503 and failed.json["state"] == "fault"
    assert gpio.levels[25] == 0 and not gpio.pwm
    client.post("/cmd", json={"c": "reset", "source": "browser", "session": identity["session"]})
    rearm = client.post("/cmd", json={"c": "arm", "source": "browser", "session": identity["session"]})
    assert rearm.status_code == 503 and gpio.levels[25] == 0
    controller.shutdown()
