"""GPIO protocol tests with a fake clock/chip; no real GPIO is opened."""
import math

import pytest

from pi_robot.drv8874_backend import DRV8874Config, DRV8874RevABackend, GPIOError
from pi_robot.motor_backend import BackendNotReady


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class FakeGPIO:
    """Model active PWM cancellation and injectable errors, including negatives."""
    def __init__(self, clock, labels=None):
        self.clock = clock
        self.labels = labels or {0: "pinctrl-rp1"}
        self.events = []
        self.claimed = set()
        self.active_pwm = set()
        self.levels = {}
        self.failure = None

    def _record(self, op, *args):
        self.events.append((op, args, self.clock()))
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
        result = self._record("info", handle)
        return [result, 54, f"gpiochip{handle - 100}", self.labels[handle - 100]]

    def gpiochip_close(self, handle):
        return self._record("close", handle)

    def gpio_claim_output(self, handle, pin, level=0):
        result = self._record("claim", handle, pin, level)
        if result >= 0:
            self.claimed.add(pin)
            self.levels[pin] = level
        return result

    def gpio_write(self, handle, pin, level):
        result = self._record("write", handle, pin, level)
        if result >= 0:
            assert pin in self.claimed
            self.levels[pin] = level
        return result

    def tx_pwm(self, handle, pin, hz, duty):
        result = self._record("pwm", handle, pin, hz, duty)
        if result < 0:
            return result
        if hz == 0:
            if pin not in self.active_pwm:
                return -86
            self.active_pwm.remove(pin)
        else:
            self.active_pwm.add(pin)
        return 7  # Successful PWM does not necessarily return zero.

    def gpio_free(self, handle, pin):
        result = self._record("free", handle, pin)
        if result >= 0:
            self.claimed.discard(pin)
        return result


def make_backend(**config):
    clock = Clock()
    gpio = FakeGPIO(clock)
    backend = DRV8874RevABackend(
        DRV8874Config(left_polarity=1, right_polarity=-1, **config),
        gpio_module=gpio, clock=clock, sleep=clock.sleep, candidate_chips=[0])
    return backend, gpio, clock


def qualify(backend, clock):
    for _ in range(160):
        backend.service(clock())
        if backend.describe(clock())["ready"]:
            return
        clock.sleep(.019)
    pytest.fail("backend did not qualify")


def armed(**config):
    backend, gpio, clock = make_backend(**config)
    qualify(backend, clock)
    backend.arm(clock())
    gpio.events.clear()
    return backend, gpio, clock


def demands(left, right):
    return dict(zip(DRV8874RevABackend.NAMES, (left, left, right, right)))


def events(gpio, op):
    return [(args, timestamp) for kind, args, timestamp in gpio.events if kind == op]


@pytest.mark.parametrize("kwargs", [
    {"left_polarity": 0}, {"right_polarity": True},
    {"pwm_hz": 10001}, {"pwm_hz": math.nan},
    {"startup_settle_s": -1}, {"reversal_holdoff_s": 0},
    {"gpiochip": True}, {"gpiochip": -1},
])
def test_rejects_invalid_configuration(kwargs):
    values = {"left_polarity": 1, "right_polarity": -1, **kwargs}
    with pytest.raises(ValueError):
        DRV8874Config(**values)


def test_startup_claims_run_first_and_every_output_low_without_starting_pwm():
    backend, gpio, clock = make_backend()
    claims = [args[1:] for args, _ in events(gpio, "claim")]
    assert claims == [(25, 0), (17, 0), (27, 0), (18, 0), (13, 0), (23, 0), (5, 0)]
    assert not events(gpio, "pwm")
    assert not backend.describe(clock())["ready"]
    with pytest.raises(BackendNotReady):
        backend.apply(demands(10, 10))
    assert gpio.levels[25] == 0


def test_qualification_is_startup_settle_then_full_second_of_stable_heartbeat():
    backend, gpio, clock = make_backend()
    started = clock()
    with pytest.raises(BackendNotReady):
        backend.arm(clock())
    for _ in range(70):
        backend.service(clock())
        clock.sleep(.019)
    assert clock() - started > 1
    assert not backend.describe(clock())["ready"]
    qualify(backend, clock)
    assert clock() - started >= 2
    pulses = [(args, timestamp) for args, timestamp in events(gpio, "write") if args[1] == 27]
    for high, low in zip(pulses[::2], pulses[1::2]):
        assert high[0][-1] == 1 and low[0][-1] == 0
        assert low[1] - high[1] >= .001 - 1e-12
    assert not events(gpio, "pwm")


def test_arm_requires_deliberate_run_then_arm_pulse_and_does_not_feed_heartbeat():
    backend, gpio, clock = make_backend(startup_settle_s=0)
    qualify(backend, clock)
    gpio.events.clear()
    backend.arm(clock())
    writes = events(gpio, "write")
    assert [args[1:] for args, _ in writes] == [(18, 0), (13, 0), (17, 0), (25, 1), (17, 1), (17, 0)]
    assert writes[-2][1] - writes[-3][1] >= .001 - 1e-12
    assert writes[-1][1] - writes[-2][1] >= .001 - 1e-12
    assert backend.describe(clock())["armed_commanded"]


def test_paired_signed_demands_use_polarity_and_same_magnitude_pwm():
    backend, gpio, clock = armed(startup_settle_s=0)
    backend.apply(demands(32, 47))
    assert gpio.levels[23] == 1  # Left polarity +1.
    assert gpio.levels[5] == 0   # Right polarity -1.
    assert [args[1:] for args, _ in events(gpio, "pwm")] == [(18, 1000, 32), (13, 1000, 47)]
    direction_time = next(t for args, t in events(gpio, "write") if args[1:] == (23, 1))
    assert events(gpio, "pwm")[0][1] - direction_time >= .001 - 1e-12
    gpio.events.clear()
    backend.apply(demands(32, 47))
    assert not events(gpio, "pwm")  # No repeated queue entries.
    assert not any(args[1] in (25, 17, 27) for args, _ in events(gpio, "write"))


def test_reversal_cancels_pwm_and_writes_low_before_direction_then_waits():
    backend, gpio, clock = armed(startup_settle_s=0)
    backend.apply(demands(30, 0))
    gpio.events.clear()
    backend.apply(demands(-30, 0))
    relevant = [(op, args[1:]) for op, args, _ in gpio.events if op in ("write", "pwm")]
    assert relevant[:4] == [("pwm", (18, 0, 0)), ("write", (18, 0)),
                            ("write", (23, 0)), ("pwm", (18, 1000, 30))]
    dir_t = next(t for op, args, t in gpio.events if op == "write" and args[1:] == (23, 0))
    pwm_t = next(t for op, args, t in gpio.events if op == "pwm" and args[2] == 1000)
    assert pwm_t - dir_t >= .001 - 1e-12


@pytest.mark.parametrize("bad", [
    {"motor_1": 1}, demands(math.nan, 0), demands(math.inf, 0),
    demands(True, 0), demands(101, 0),
    {"motor_1": 10, "motor_2": 11, "motor_3": 0, "motor_4": 0},
])
def test_invalid_or_independent_pair_demands_fail_closed(bad):
    backend, gpio, clock = armed(startup_settle_s=0)
    with pytest.raises(ValueError):
        backend.apply(bad)
    assert gpio.levels[25] == 0
    assert not backend.describe(clock())["armed_commanded"]
    assert not events(gpio, "pwm")


def test_quiesce_keeps_run_and_disable_drops_run_before_pwm():
    backend, gpio, clock = armed(startup_settle_s=0)
    backend.apply(demands(30, -40))
    gpio.events.clear()
    backend.quiesce()
    assert gpio.levels[25] == 1
    assert backend.describe(clock())["armed_commanded"]
    assert not gpio.active_pwm
    backend.apply(demands(30, -40))
    gpio.events.clear()
    backend.disable()
    assert gpio.events[0][:2] == ("write", (100, 25, 0))
    assert not gpio.active_pwm
    assert not any(gpio.levels.values())
    assert backend.describe(clock())["ready"]  # Healthy qualification survives stop.


def test_stale_disarmed_service_restarts_qualification():
    backend, gpio, clock = make_backend(startup_settle_s=0)
    qualify(backend, clock)
    clock.sleep(.051)
    backend.service(clock())
    status = backend.describe(clock())
    assert not status["ready"]
    assert status["qualification"]["completed_pulses"] == 1
    qualify(backend, clock)
    assert backend.describe(clock())["ready"]


@pytest.mark.parametrize("operation", ["check_health", "apply", "service"])
def test_stale_armed_heartbeat_drops_run_before_any_new_demand_or_heartbeat(operation):
    backend, gpio, clock = armed(startup_settle_s=0)
    clock.sleep(.051)
    gpio.events.clear()
    with pytest.raises(RuntimeError, match="heartbeat"):
        if operation == "apply":
            backend.apply(demands(20, 20))
        else:
            getattr(backend, operation)(clock())
    assert gpio.levels[25] == 0
    assert not events(gpio, "pwm")
    assert all(args[1] != 27 for args, _ in events(gpio, "write"))
    assert not backend.describe(clock())["ready"]


def test_clock_rollback_and_interrupted_timing_wait_fail_closed():
    backend, gpio, clock = armed(startup_settle_s=0)
    clock.now -= 1
    with pytest.raises(RuntimeError, match="backwards"):
        backend.check_health(clock())
    assert gpio.levels[25] == 0
    backend, gpio, clock = make_backend(startup_settle_s=0)
    backend.sleep = lambda seconds: None
    with pytest.raises(RuntimeError, match="timing wait"):
        backend.service(clock())
    assert gpio.levels[25] == 0


@pytest.mark.parametrize("failure", [-77, RuntimeError("write failed")])
def test_io_failure_latches_uncertainty_and_disables_without_silently_recovering(failure):
    backend, gpio, clock = armed(startup_settle_s=0)
    gpio.failure = (lambda op, args: op == "pwm" and args[2] > 0, failure, True)
    with pytest.raises(GPIOError):
        backend.apply(demands(40, 40))
    assert gpio.levels[25] == 0
    assert backend.describe(clock())["failed"]
    # The failed start might have reached the PWM worker, so cancellation is
    # attempted even when this fake rejected it before starting (error -86).
    with pytest.raises(GPIOError):
        backend.disable()
    with pytest.raises(GPIOError, match="restart"):
        backend.service(clock())
    status = backend.describe(clock())
    assert status["physical_enable_observed"] is None
    assert status["physical_stop_confirmed"] is None
    assert status["fault_feedback_available"] is False


def test_disable_attempts_remaining_outputs_and_close_releases_after_failure():
    backend, gpio, clock = armed(startup_settle_s=0)
    backend.apply(demands(30, 30))
    gpio.events.clear()
    gpio.failure = (lambda op, args: op == "write" and args[1] == 25, -77, False)
    with pytest.raises(GPIOError):
        backend.close()
    assert not gpio.active_pwm
    assert {args[1] for args, _ in events(gpio, "free")} == {25, 17, 27, 18, 13, 23, 5}
    assert events(gpio, "close")
    count = len(gpio.events)
    backend.close()
    assert len(gpio.events) == count


def test_partial_initialization_failure_releases_claimed_pins_and_chip():
    clock = Clock()
    gpio = FakeGPIO(clock)
    gpio.failure = (lambda op, args: op == "claim" and args[1] == 18, -79, True)
    with pytest.raises(GPIOError):
        DRV8874RevABackend(DRV8874Config(1, -1), gpio_module=gpio,
                          clock=clock, sleep=clock.sleep, candidate_chips=[0])
    assert gpio.levels[25] == 0
    assert not gpio.claimed
    assert events(gpio, "close")


def test_discovers_rp1_by_label_and_closes_nonmatching_candidates():
    clock = Clock()
    gpio = FakeGPIO(clock, {0: "gpio-brcmstb", 4: "pinctrl-rp1"})
    backend = DRV8874RevABackend(DRV8874Config(1, -1), gpio_module=gpio,
                               clock=clock, sleep=clock.sleep, candidate_chips=[0, 4])
    assert backend.describe(clock())["gpiochip"] == 4
    assert events(gpio, "close")[0][0] == (100,)
    assert all(args[0] == 104 for args, _ in events(gpio, "claim"))


def test_explicit_chip_still_must_be_rp1_and_never_claims_wrong_lines():
    clock = Clock()
    gpio = FakeGPIO(clock, {0: "gpio-brcmstb"})
    with pytest.raises(RuntimeError, match="expected pinctrl-rp1"):
        DRV8874RevABackend(DRV8874Config(1, -1, gpiochip=0), gpio_module=gpio,
                          clock=clock, sleep=clock.sleep, candidate_chips=[4])
    assert not events(gpio, "claim")
    assert events(gpio, "close")


def test_repeated_disable_does_not_cancel_inactive_pwm():
    backend, gpio, clock = make_backend()
    backend.disable()
    backend.disable()
    backend.close()
    assert not events(gpio, "pwm")


def test_back_to_back_service_pulses_preserve_one_millisecond_low_time():
    backend, gpio, clock = make_backend(startup_settle_s=0)
    backend.service(clock())
    backend.service(clock())
    pulses = [(args, timestamp) for args, timestamp in events(gpio, "write") if args[1] == 27]
    assert len(pulses) == 4
    assert pulses[2][1] - pulses[1][1] >= .001 - 1e-12


@pytest.mark.parametrize("delay_low_wait", [False, True])
def test_disarmed_delayed_pulse_or_low_wait_invalidates_old_qualification(delay_low_wait):
    backend, gpio, clock = make_backend(startup_settle_s=0)
    qualify(backend, clock)
    if not delay_low_wait:
        clock.sleep(.019)  # Avoid low-time wait so the high pulse is delayed.
    backend.sleep = lambda seconds: clock.sleep(.3)
    backend.service(clock())
    backend.sleep = clock.sleep
    status = backend.describe(clock())
    assert not status["ready"]
    assert status["qualification"]["completed_pulses"] == 1
    assert status["qualification"]["stable_heartbeat_s"] == 0
    with pytest.raises(BackendNotReady):
        backend.arm(clock())
    qualify(backend, clock)
    backend.arm(clock())
    assert backend.describe(clock())["armed_commanded"]


def test_failed_pwm_ack_still_cancels_a_partially_started_worker():
    backend, gpio, clock = armed(startup_settle_s=0)
    real_pwm = gpio.tx_pwm

    def fail_after_start(handle, pin, hz, duty):
        result = real_pwm(handle, pin, hz, duty)
        if hz:
            gpio.tx_pwm = real_pwm
            raise RuntimeError("write took effect but acknowledgement failed")
        return result

    gpio.tx_pwm = fail_after_start
    with pytest.raises(GPIOError):
        backend.apply(demands(25, 25))
    assert 18 in gpio.active_pwm
    assert gpio.levels[25] == 0
    backend.disable()
    assert not gpio.active_pwm
    assert (18, 0, 0) in [args[1:] for args, _ in events(gpio, "pwm")]


def test_keyboard_interrupt_during_initialization_still_releases_resources():
    clock = Clock()
    gpio = FakeGPIO(clock)
    gpio.failure = (lambda op, args: op == "claim" and args[1] == 18, KeyboardInterrupt(), True)
    with pytest.raises(KeyboardInterrupt):
        DRV8874RevABackend(DRV8874Config(1, -1), gpio_module=gpio,
                          clock=clock, sleep=clock.sleep, candidate_chips=[0])
    assert gpio.levels[25] == 0
    assert not gpio.claimed
    assert events(gpio, "close")


def test_ambiguous_rp1_candidates_are_closed_without_claiming_outputs():
    clock = Clock()
    gpio = FakeGPIO(clock, {0: "pinctrl-rp1", 4: "pinctrl-rp1"})
    with pytest.raises(RuntimeError, match="multiple RP1"):
        DRV8874RevABackend(DRV8874Config(1, -1), gpio_module=gpio,
                          clock=clock, sleep=clock.sleep, candidate_chips=[0, 4])
    assert not events(gpio, "claim")
    assert {args[0] for args, _ in events(gpio, "close")} == {100, 104}


@pytest.mark.parametrize("invalid_now", [math.nan, math.inf, -math.inf])
def test_fault_status_remains_json_safe_when_clock_is_invalid(invalid_now):
    import json
    backend, gpio, clock = make_backend()
    status = backend.describe(invalid_now)
    assert status["timing_valid"] is False and status["ready"] is False
    assert status["qualification"]["last_fall_age_s"] is None
    json.dumps(status, allow_nan=False)


def make_api():
    from pi_robot.motor_control import MotorController
    from pi_robot.web_motor import create_app
    backend, gpio, clock = make_backend(startup_settle_s=0)
    controller = MotorController(backend, clock, reversal_holdoff_s=.1)
    client = create_app(controller).test_client()
    for _ in range(60):
        controller.tick()
        if backend.describe(clock())["ready"]:
            break
        clock.sleep(.019)
    identity = {"source": "browser", "session": "gpio_session_123"}
    response = client.post("/cmd", json={"c": "arm", **identity})
    assert response.status_code == 200, response.json
    identity["lease"] = response.json["lease"]
    return backend, gpio, clock, controller, client, identity


def test_api_real_backend_reversal_brakes_then_resumes_without_another_arm_edge():
    backend, gpio, clock, controller, client, identity = make_api()
    forward = client.post("/cmd", json={"c": "fwd", "speed": 31, "duration": .8, **identity})
    assert forward.status_code == 200 and gpio.active_pwm == {18, 13}
    reverse = client.post("/cmd", json={"c": "back", "speed": 31, "duration": .8, **identity})
    assert reverse.status_code == 200 and reverse.json["pending_reversal"]
    assert gpio.levels[25] == 1 and not gpio.active_pwm
    for _ in range(4):
        clock.sleep(.019)
        controller.tick()
    assert not gpio.active_pwm
    for _ in range(2):
        clock.sleep(.019)
        controller.tick()
    assert gpio.active_pwm == {18, 13}
    assert gpio.levels[23] == 0 and gpio.levels[5] == 1
    assert sum(args[1:] == (17, 1) for args, _ in events(gpio, "write")) == 1
    # Stop wins over another reversal already queued in the controller.
    pending = client.post("/cmd", json={"c": "fwd", "speed": 31, "duration": .8, **identity})
    assert pending.json["pending_reversal"]
    stopped = client.post("/cmd", json={"c": "stop"})
    assert stopped.status_code == 200
    assert gpio.levels[25] == 0 and not gpio.active_pwm
    for _ in range(7):
        clock.sleep(.019)
        controller.tick()
    assert not gpio.active_pwm and not controller.pending
    assert stopped.json["physical_actuation_enabled"] is None
    controller.shutdown()


def test_api_real_backend_command_expiry_drops_run_and_cancels_both_pwm_workers():
    backend, gpio, clock, controller, client, identity = make_api()
    response = client.post("/cmd", json={"c": "fwd", "speed": 35, "duration": .08, **identity})
    assert response.status_code == 200
    for _ in range(5):
        clock.sleep(.019)
        controller.tick()
    status = client.get("/status").json
    assert status["reason"] == "command-expired"
    assert not gpio.active_pwm and gpio.levels[25] == 0
    controller.shutdown()


def test_api_status_requests_do_not_keep_hardware_heartbeat_alive():
    backend, gpio, clock, controller, client, identity = make_api()
    response = client.post("/cmd", json={"c": "fwd", "speed": 35, "duration": .8, **identity})
    assert response.status_code == 200
    gpio.events.clear()
    for _ in range(4):
        clock.sleep(.02)
        status = client.get("/status").json
    assert status["state"] == "fault"
    assert status["reason"] == "backend-health-failed"
    assert gpio.levels[25] == 0 and not gpio.active_pwm
    assert not any(args[1:] == (27, 1) for args, _ in events(gpio, "write"))
    controller.shutdown()
