"""Controller integration against a latch/heartbeat model, with no GPIO access."""
import json

import pytest

from pi_robot.motor_backend import BackendNotReady
from pi_robot.motor_config import CHANNELS
from pi_robot.motor_control import CommandError, MotorController


class Clock:
    now = 100.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class LatchBackend:
    """Model the key distinction between PWM-zero and a cleared RUN latch."""

    name = "drv8874_reva"

    def __init__(self, clock):
        self.clock = clock
        self.events = []
        self.outputs = dict.fromkeys((ch.name for ch in CHANNELS), 0.0)
        self.run = False
        self.ready = True
        self.last_heartbeat = clock()
        self.fail_arm = self.fail_health = self.fail_close = False

    def arm(self, now):
        self.events.append("arm")
        if not self.ready:
            raise BackendNotReady("heartbeat qualification still pending")
        if self.fail_arm:
            raise OSError("GPIO ARM write failed")
        self.run = True

    def service(self, now):
        self.events.append("heartbeat")
        self.last_heartbeat = now

    def check_health(self, now):
        self.events.append("health")
        if self.fail_health or now - self.last_heartbeat > .05:
            raise RuntimeError("heartbeat stale or GPIO failed")

    def apply(self, values):
        assert self.run, "motion cannot resume after RUN cleared the latch"
        self.events.append("apply")
        self.outputs = dict(values)

    def quiesce(self):
        self.events.append("quiesce")
        self.outputs = dict.fromkeys(self.outputs, 0.0)

    def disable(self):
        self.events.append("disable")
        self.outputs = dict.fromkeys(self.outputs, 0.0)
        self.run = False

    def close(self):
        self.events.append("close")
        if self.fail_close:
            raise OSError("GPIO release failed")

    def describe(self, now):
        return {"run_commanded": self.run, "physical_enable_observed": None,
                "fault_feedback_available": False}


class RecordingGPIO:
    def __init__(self):
        self.events = []

    def gpiochip_open(self, _chip):
        return 1

    def gpio_get_chip_info(self, _handle):
        return (0, 54, "gpiochip0", "pinctrl-rp1")

    def __getattr__(self, method):
        def call(*args):
            self.events.append((method, *args))
            return 0
        return call


@pytest.fixture
def rig():
    clock = Clock()
    backend = LatchBackend(clock)
    controller = MotorController(backend, clock, reversal_holdoff_s=.08)
    return controller, backend, clock


IDENTITY = {"source": "manual", "session": "test_operator"}


def arm(controller):
    response = controller.execute({"c": "arm", **IDENTITY})
    return {**IDENTITY, "lease": response["lease"]}


def tick_for(controller, clock, seconds):
    while seconds > 0:
        step = min(.02, seconds)
        clock.advance(step)
        controller.tick()
        seconds -= step


def test_only_deliberate_arm_emits_arm_edge_and_stop_revokes_lease(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    controller.status()
    tick_for(controller, clock, .02)
    assert backend.events.count("arm") == 1
    controller.execute({"c": "stop"})
    assert not backend.run
    with pytest.raises(CommandError, match="latched"):
        arm(controller)
    controller.execute({"c": "reset", **IDENTITY})
    assert not backend.run
    new_owner = arm(controller)
    assert backend.events.count("arm") == 2
    assert new_owner["lease"] != owner["lease"]
    with pytest.raises(CommandError, match="mismatch"):
        controller.execute({"c": "fwd", **owner})


def test_status_and_http_commands_never_feed_heartbeat(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.status()
    controller.execute({"c": "fwd", **owner})
    controller.execute({"c": "speed", "speed": 20, **owner})
    assert "heartbeat" not in backend.events
    tick_for(controller, clock, .02)
    assert backend.events.count("heartbeat") == 1
    controller.fault("invalid-request")
    tick_for(controller, clock, .02)
    assert backend.events.count("heartbeat") == 1
    controller.execute({"c": "reset", **IDENTITY})
    tick_for(controller, clock, .02)
    assert backend.events.count("heartbeat") == 2


def test_reversal_and_zero_demand_preserve_run_permission(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    disable_count = backend.events.count("disable")
    controller.execute({"c": "back", "duration": .5, **owner})
    assert backend.run and not any(backend.outputs.values())
    assert controller.pending is not None
    tick_for(controller, clock, .081)
    assert set(backend.outputs.values()) == {-50}
    controller.execute({"c": "back", "speed": 0, **owner})
    assert backend.run and not any(backend.outputs.values())
    assert controller.status()["disable_confirmed"] is False
    assert backend.events.count("disable") == disable_count
    assert backend.events.count("arm") == 1
    assert backend.events.count("quiesce") == 2


@pytest.mark.parametrize("entry", ["status", "execute", "tick"])
def test_stale_heartbeat_is_checked_before_pending_motion(entry, rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    controller.execute({"c": "back", "duration": .5, **owner})
    apply_count = backend.events.count("apply")
    heartbeat_count = backend.events.count("heartbeat")
    clock.advance(.081)  # Below software gap, above heartbeat and reversal limits.
    if entry == "execute":
        with pytest.raises(CommandError):
            controller.execute({"c": "fwd", **owner})
    else:
        getattr(controller, entry)()
    assert backend.events.count("apply") == apply_count
    assert backend.events.count("heartbeat") == heartbeat_count
    assert not backend.run and not any(backend.outputs.values())
    assert controller.status()["reason"] == "backend-health-failed"
    assert not controller.pending and controller.latched and controller.faulted


def test_not_ready_arm_has_no_owner_or_lease_and_can_be_retried_explicitly(rig):
    controller, backend, _ = rig
    backend.ready = False
    with pytest.raises(CommandError) as failure:
        arm(controller)
    assert failure.value.status == 409
    assert not controller.armed and not controller.latched
    assert controller.owner is controller.lease is controller.deadline is None
    backend.ready = True
    controller.tick()
    controller.status()
    assert backend.events.count("arm") == 1
    arm(controller)
    assert backend.events.count("arm") == 2


def test_arm_io_failure_latches_fault_and_returns_503(rig):
    controller, backend, _ = rig
    backend.fail_arm = True
    with pytest.raises(CommandError) as failure:
        arm(controller)
    assert failure.value.status == 503
    assert controller.status()["reason"] == "backend-arm-failed"
    assert not backend.run and controller.faulted and controller.lease is None


def test_status_stays_readable_after_persistent_backend_health_error(rig):
    controller, backend, _ = rig
    arm(controller)
    backend.fail_health = True
    status = controller.status()
    assert status["state"] == "fault" and status["reason"] == "backend-health-failed"
    health_count = backend.events.count("health")
    assert controller.status()["state"] == "fault"
    controller.tick()
    assert backend.events.count("health") == health_count


def test_hardware_status_distinguishes_commands_from_feedback(rig):
    controller, _, _ = rig
    arm(controller)
    status = controller.status()
    assert status["physical_backend"] is True
    assert status["physical_actuation_enabled"] is None
    assert status["physical_motion_observed"] is None
    assert status["outputs_scope"] == "requested_signed_percent"
    assert status["disable_confirmation_scope"] == "accepted_disable_write_not_physical_feedback"
    assert status["hardware"]["physical_enable_observed"] is None
    assert status["hardware"]["fault_feedback_available"] is False


@pytest.mark.parametrize("failed", [False, True])
def test_shutdown_closes_once_and_reports_cleanup_failure(failed, rig):
    controller, backend, _ = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    backend.fail_close = failed
    if failed:
        with pytest.raises(CommandError) as failure:
            controller.shutdown()
        assert failure.value.status == 503
    else:
        controller.shutdown()
    event_count = len(backend.events)
    controller.shutdown()
    controller.tick()
    status = controller.status()
    assert len(backend.events) == event_count
    assert backend.events[-2:] == ["disable", "close"]
    assert status["state"] == "shutdown" and not backend.run
    if failed:
        assert status["reason"] == "backend-close-failed"
        assert status["outputs_uncertain"] and not status["disable_confirmed"]


def test_configured_holdoff_applies_after_partial_write_failure(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    original_apply = backend.apply

    def fail_after_apply(values):
        original_apply(values)
        raise OSError("partial output write")

    backend.apply = fail_after_apply
    with pytest.raises(CommandError):
        controller.execute({"c": "fwd", **owner})
    backend.apply = original_apply
    controller.execute({"c": "reset", **IDENTITY})
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    tick_for(controller, clock, .079)
    assert not any(backend.outputs.values())
    tick_for(controller, clock, .002)
    assert set(backend.outputs.values()) == {50}


@pytest.mark.parametrize("disable_fails", [False, True])
def test_rejected_arm_retries_disable_after_partial_arm(disable_fails, rig):
    controller, backend, _ = rig
    original_disable = backend.disable

    def reject_after_run(now):
        backend.run = True
        raise BackendNotReady("heartbeat became stale after RUN")

    def fail_after_partial_arm():
        if backend.run and disable_fails:
            raise OSError("RUN low write failed")
        original_disable()

    backend.arm, backend.disable = reject_after_run, fail_after_partial_arm
    with pytest.raises(CommandError) as failure:
        arm(controller)
    assert failure.value.status == (503 if disable_fails else 409)
    status = controller.status()
    assert not status["armed"] and controller.lease is None
    assert status["disable_confirmed"] is (not disable_fails)
    if disable_fails:
        assert status["state"] == "fault" and status["outputs_uncertain"]
    else:
        assert not backend.run and status["state"] == "disarmed"


def test_actual_reva_backend_qualifies_arms_reverses_and_expires_without_feedback():
    from pi_robot.drv8874_backend import DRV8874Config, DRV8874RevABackend

    clock, gpio = Clock(), RecordingGPIO()
    backend = DRV8874RevABackend(
        DRV8874Config(1, -1), gpio_module=gpio, clock=clock,
        sleep=clock.advance, candidate_chips=[0])
    controller = MotorController(backend, clock, reversal_holdoff_s=.08)
    with pytest.raises(CommandError) as failure:
        arm(controller)
    assert failure.value.status == 409
    tick_for(controller, clock, 2.05)
    assert backend.describe(clock())["ready"]
    owner = arm(controller)
    controller.execute({"c": "fwd", "duration": .5, **owner})
    assert backend.describe(clock())["outputs_commanded"] == dict.fromkeys(backend.NAMES, 50)
    run_lows = gpio.events.count(("gpio_write", 1, backend.RUN, 0))
    controller.execute({"c": "back", "duration": .3, **owner})
    tick_for(controller, clock, .081)
    assert backend.describe(clock())["outputs_commanded"] == dict.fromkeys(backend.NAMES, -50)
    assert gpio.events.count(("gpio_write", 1, backend.RUN, 0)) == run_lows
    assert gpio.events.count(("gpio_write", 1, backend.ARM, 1)) == 1
    tick_for(controller, clock, .23)
    status = controller.status()
    assert status["reason"] == "command-expired"
    assert not status["hardware"]["run_commanded"]
    assert status["physical_actuation_enabled"] is None
    controller.shutdown()


@pytest.mark.parametrize("invalid_time", [float("nan"), float("inf"), float("-inf")])
def test_invalid_clock_fault_remains_readable_with_real_backend(invalid_time):
    from pi_robot.drv8874_backend import DRV8874Config, DRV8874RevABackend

    clock = Clock()
    backend = DRV8874RevABackend(
        DRV8874Config(1, -1), gpio_module=RecordingGPIO(), clock=clock,
        sleep=clock.advance, candidate_chips=[0])
    controller = MotorController(backend, clock)
    clock.now = invalid_time
    status = controller.status()
    assert status["state"] == "fault" and status["reason"] == "invalid-clock"
    assert status["expires_in_s"] is None
    assert not status["hardware"]["run_commanded"]
    assert json.loads(json.dumps(status, allow_nan=False))["state"] == "fault"
    controller.shutdown()


@pytest.mark.parametrize("zero_operation", ["quiesce", "disable"])
def test_holdoff_starts_after_zero_write_completes(zero_operation, rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    original_zero = getattr(backend, zero_operation)

    def delayed_zero():
        clock.advance(.02)
        original_zero()

    setattr(backend, zero_operation, delayed_zero)
    request_time = clock()
    if zero_operation == "disable":
        controller.execute({"c": "stop"})
        setattr(backend, zero_operation, original_zero)
        completed = clock()
        controller.execute({"c": "reset", **IDENTITY})
        owner = arm(controller)
        request_time = clock()
        controller.execute({"c": "back", "duration": .3, **owner})
    else:
        controller.execute({"c": "back", "duration": .3, **owner})
        completed = clock()
    assert controller.deadline == pytest.approx(request_time + .3)
    assert set(controller.zero_since.values()) == {completed}
    assert controller.pending_at == pytest.approx(completed + .08)
    tick_for(controller, clock, .079)
    assert not any(backend.outputs.values())
    tick_for(controller, clock, .002)
    assert set(backend.outputs.values()) == {-50}


def test_failed_write_recovery_holdoff_starts_after_disable_completes(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    original_apply, original_disable = backend.apply, backend.disable

    def partial_write(values):
        original_apply(values)
        raise OSError("partial output failure")

    def delayed_disable():
        clock.advance(.02)
        original_disable()

    backend.apply, backend.disable = partial_write, delayed_disable
    with pytest.raises(CommandError):
        controller.execute({"c": "fwd", **owner})
    completed = clock()
    assert controller.recovery_holdoff_until == pytest.approx(completed + .08)
    backend.apply, backend.disable = original_apply, original_disable
    controller.execute({"c": "reset", **IDENTITY})
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    tick_for(controller, clock, .079)
    assert not any(backend.outputs.values())
    tick_for(controller, clock, .002)
    assert set(backend.outputs.values()) == {50}


@pytest.mark.parametrize("bad_completion", [float("nan"), 99.0])
@pytest.mark.parametrize("zero_operation", ["quiesce", "disable"])
def test_invalid_zero_completion_cannot_bypass_holdoff_after_reset(
        bad_completion, zero_operation, rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    original_zero = getattr(backend, zero_operation)

    def invalid_clock_after_zero():
        original_zero()
        clock.now = bad_completion

    setattr(backend, zero_operation, invalid_clock_after_zero)
    if zero_operation == "quiesce":
        with pytest.raises(CommandError) as failure:
            controller.execute({"c": "back", **owner})
        assert failure.value.status == 503
    else:
        controller.execute({"c": "stop"})
    assert controller.faulted and controller.zero_timing_uncertain
    assert controller.recovery_holdoff_until == float("inf")
    setattr(backend, zero_operation, original_zero)
    clock.now = 101.0
    controller.execute({"c": "reset", **IDENTITY})
    assert not controller.zero_timing_uncertain
    assert controller.recovery_holdoff_until == pytest.approx(101.08)
    controller.tick()
    owner = arm(controller)
    controller.execute({"c": "back", **owner})
    tick_for(controller, clock, .079)
    assert not any(backend.outputs.values())
    tick_for(controller, clock, .002)
    assert set(backend.outputs.values()) == {-50}
