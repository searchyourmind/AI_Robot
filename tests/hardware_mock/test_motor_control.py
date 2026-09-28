"""Mock-only state, race, expiry, backend-failure, and parsing checks."""
import threading

import pytest

from pi_robot.motor_backend import MockBackend
from pi_robot.motor_config import CHANNELS, Channel
from pi_robot.motor_control import CommandError, MotorController


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def rig():
    clock = Clock()
    backend = MockBackend(tuple(c.name for c in CHANNELS))
    controller = MotorController(backend, clock)
    return controller, backend, clock


def arm(controller, source="browser", session="session_123"):
    identity = {"source": source, "session": session}
    reply = controller.execute({"c": "arm", **identity})
    return {**identity, "lease": reply["lease"]}


def advance(controller, clock, seconds):
    # Emulate the ticker without sleeping or invoking an OS timer.
    whole_ticks = int(seconds / .02)
    for _ in range(whole_ticks):
        clock.advance(.02)
        controller.tick()
    clock.advance(seconds - whole_ticks * .02 + 1e-10)
    controller.tick()


def test_startup_four_disabled_channels_no_physical_mapping(rig):
    controller, backend, _ = rig
    status = controller.status()
    assert status["state"] == "disarmed"
    assert status["physical_actuation_enabled"] is False
    assert status["disable_confirmed"] is True
    assert len(backend.outputs) == 4
    assert not backend.standby and not any(backend.outputs.values())
    assert all(c.control_pins is None and c.polarity is None for c in CHANNELS)
    assert all(c.controller == "raspberry_pi_5_direct_gpio" for c in CHANNELS)
    assert [(c.physical_position, c.driver, c.driver_channel) for c in CHANNELS] == [
        ("front_left", "board_a", "A"), ("back_left", "board_b", "A"),
        ("front_right", "board_a", "B"), ("back_right", "board_b", "B"),
    ]
    with pytest.raises(CommandError, match="disarmed"):
        controller.execute({"c": "fwd", "source": "browser", "session": "session_123"})


@pytest.mark.parametrize("command, signs", [
    ("fwd", (1, 1, 1, 1)), ("back", (-1, -1, -1, -1)),
    ("left", (-1, -1, 1, 1)), ("right", (1, 1, -1, -1)),
    ("pulse_fwd", (1, 1, 1, 1)),
])
def test_four_separate_demands_and_nonblocking_pulse(rig, command, signs):
    controller, backend, clock = rig
    identity = arm(controller)
    before = clock.now
    reply = controller.execute({"c": command, **identity, "speed": 37, "duration": .25})
    assert clock.now == before
    assert tuple(backend.outputs.values()) == tuple(37 * sign for sign in signs)
    assert backend.standby
    assert "lease" not in reply and "lease" not in controller.status()
    advance(controller, clock, .25)
    assert not backend.standby and not any(backend.outputs.values())
    assert controller.status()["reason"] == "command-expired"
    assert controller.status()["latched"]


def test_stop_latches_and_revokes_stale_lease(rig):
    controller, backend, _ = rig
    old = arm(controller)
    controller.execute({"c": "fwd", **old})
    controller.execute({"c": "stop", "source": "ai"})
    assert not backend.standby
    with pytest.raises(CommandError):
        controller.execute({"c": "arm", "source": "browser", "session": "session_123"})
    controller.execute({"c": "reset", "source": "browser", "session": "session_123"})
    assert not controller.status()["armed"]
    new = arm(controller)
    assert new["lease"] != old["lease"]
    with pytest.raises(CommandError, match="mismatch"):
        controller.execute({"c": "fwd", **old})
    assert not backend.standby


def test_owner_arbitration_and_reconnect(rig):
    controller, backend, _ = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    before = dict(backend.outputs)
    for changed in ({"source": "voice"}, {"session": "new_session"}, {"lease": "é" * 32}, {"lease": True}):
        with pytest.raises(CommandError):
            controller.execute({"c": "back", **owner, **changed})
        assert backend.outputs == before
    with pytest.raises(CommandError, match="already armed"):
        arm(controller, "voice", "new_session")
    controller.execute({"c": "stop", "source": "voice", "session": "new_session"})
    assert not backend.standby


@pytest.mark.parametrize("command", ["arm", "reset", "fwd", "back", "speed", "pulse_fwd"])
def test_ai_never_arms_or_moves(rig, command):
    controller, backend, _ = rig
    owner = arm(controller)
    with pytest.raises(CommandError) as failure:
        controller.execute({"c": command, **owner, "source": "ai"})
    assert failure.value.status == 403
    assert not backend.standby


@pytest.mark.parametrize("value", [True, False, None, [], {}, float("nan"), float("inf"), -1, 101, "NaN", "inf", "1e9999", " 50", "50%"])
def test_invalid_speed_fails_closed(rig, value):
    controller, backend, _ = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    with pytest.raises(CommandError) as failure:
        controller.execute({"c": "fwd", **owner, "speed": value})
    assert failure.value.status == 400
    assert controller.status()["state"] == "fault"
    assert not backend.standby


@pytest.mark.parametrize("value", [True, None, 0, -1, 1.001, float("nan"), "-inf", [], {}])
def test_invalid_duration_fails_closed(rig, value):
    controller, backend, _ = rig
    owner = arm(controller)
    with pytest.raises(CommandError):
        controller.execute({"c": "pulse_fwd", **owner, "v": value})
    assert controller.status()["state"] == "fault"
    assert not backend.standby


@pytest.mark.parametrize("speed", [0, "0", 100, "100", "1e1"])
def test_speed_bounds_and_zero_disable(rig, speed):
    controller, backend, _ = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner, "speed": speed, "duration": 1})
    assert backend.standby is (float(speed) > 0)


def test_speed_and_status_do_not_extend_expiry(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner, "speed": 40, "duration": .25})
    deadline = controller.deadline
    advance(controller, clock, .1)
    controller.execute({"c": "speed", **owner, "v": "30"})
    controller.status()
    assert controller.deadline == deadline
    assert set(backend.outputs.values()) == {40}
    advance(controller, clock, .15)
    assert not controller.status()["armed"] and not backend.standby


def test_arm_timeout_without_motion(rig):
    controller, backend, clock = rig
    arm(controller)
    advance(controller, clock, 1)
    assert controller.status()["reason"] == "command-expired"
    assert not backend.standby


def test_stalled_ticker_fails_closed_on_next_service(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner, "duration": 1})
    clock.advance(.151)
    # Before the interpreter runs again, Python cannot affect latched outputs.
    assert backend.standby
    controller.tick()
    assert controller.status()["reason"] == "software-watchdog-gap"
    assert not backend.standby


def test_reversal_disables_all_then_waits(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    controller.execute({"c": "back", **owner, "duration": .3})
    assert not backend.standby and controller.status()["pending_reversal"]
    advance(controller, clock, .099)
    assert not backend.standby
    advance(controller, clock, .002)
    assert set(backend.outputs.values()) == {-50}


def test_expiry_wins_over_pending_reversal(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    controller.execute({"c": "back", **owner, "duration": .05})
    advance(controller, clock, .11)
    assert not backend.standby
    assert not any(any(v < 0 for v in event["outputs"].values()) for event in backend.events)


def test_stop_at_pending_start_never_applies_pending_motion(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    controller.execute({"c": "back", **owner})
    clock.advance(.1)
    controller.execute({"c": "stop"})
    assert not any(any(v < 0 for v in event["outputs"].values()) for event in backend.events)
    assert not controller.pending and not backend.standby


def test_stop_reset_does_not_bypass_reversal_holdoff(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    controller.execute({"c": "stop"})
    controller.execute({"c": "reset", "source": "browser", "session": "session_123"})
    owner = arm(controller)
    controller.execute({"c": "back", **owner})
    assert not backend.standby
    advance(controller, clock, .101)
    assert set(backend.outputs.values()) == {-50}


def test_stop_and_motion_race_ends_disabled(rig):
    controller, backend, _ = rig
    owner = arm(controller)
    barrier = threading.Barrier(3)
    errors = []

    def command(c):
        barrier.wait()
        try:
            controller.execute({"c": c, **owner})
        except CommandError as exc:
            errors.append(exc.status)

    workers = [threading.Thread(target=command, args=(c,)) for c in ("stop", "fwd")]
    for worker in workers:
        worker.start()
    barrier.wait()
    for worker in workers:
        worker.join(timeout=1)
        assert not worker.is_alive()
    assert errors in ([], [409])
    assert not backend.standby and controller.status()["latched"]


def test_shutdown_is_final_and_cancels_pending(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    controller.execute({"c": "back", **owner})
    controller.shutdown()
    advance(controller, clock, .12)
    for c in ("arm", "reset", "fwd"):
        with pytest.raises(CommandError, match="shut down"):
            controller.execute({"c": c, **owner})
    assert controller.status()["state"] == "shutdown"
    assert not backend.standby


def test_output_failure_latches_and_attempts_disable(rig):
    controller, backend, _ = rig
    owner = arm(controller)

    def fail(_outputs):
        raise OSError("simulated backend fault")

    backend.apply = fail
    with pytest.raises(CommandError) as failure:
        controller.execute({"c": "fwd", **owner})
    assert failure.value.status == 503
    assert controller.status()["state"] == "fault"
    assert not backend.standby


def test_disable_failure_never_reports_confirmation(rig):
    controller, backend, _ = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})

    def fail():
        raise OSError("simulated stuck output")

    backend.disable = fail
    with pytest.raises(CommandError) as failure:
        controller.execute({"c": "stop"})
    assert failure.value.status == 503
    assert controller.status()["state"] == "fault"
    assert controller.status()["disable_confirmed"] is False
    # Do not assert hardware is off when disable failed.
    assert backend.standby
    with pytest.raises(CommandError):
        controller.execute({"c": "reset", "source": "browser", "session": "session_123"})


def test_configuration_and_backend_gate():
    with pytest.raises(ValueError, match="four"):
        MotorController(channels=(Channel("one", "left"),))
    backend = MockBackend(tuple(c.name for c in CHANNELS))
    backend.name = "gpio"
    with pytest.raises(ValueError, match="only the mock"):
        MotorController(backend)


def test_failed_disable_recovery_starts_holdoff_at_success(rig):
    controller, backend, clock = rig
    owner = arm(controller)
    controller.execute({"c": "fwd", **owner})
    real_disable = backend.disable

    def fail():
        raise OSError("disable failed while forward remains energized")

    backend.disable = fail
    with pytest.raises(CommandError) as failure:
        controller.execute({"c": "stop"})
    assert failure.value.status == 503
    assert backend.standby and controller.status()["outputs_uncertain"]
    clock.advance(1)
    backend.disable = real_disable
    controller.execute({"c": "reset", "source": "browser", "session": "session_123"})
    owner = arm(controller)
    controller.execute({"c": "back", **owner})
    assert not backend.standby
    advance(controller, clock, .099)
    assert not backend.standby
    advance(controller, clock, .002)
    assert set(backend.outputs.values()) == {-50}


@pytest.mark.parametrize("next_command", ["fwd", "back"])
def test_partial_apply_failure_recovers_with_all_channel_holdoff(rig, next_command):
    controller, backend, clock = rig
    owner = arm(controller)
    real_apply, real_disable = backend.apply, backend.disable

    def partial_apply(values):
        real_apply(values)
        raise OSError("failed after outputs were already changed")

    def fail_disable():
        raise OSError("disable also failed")

    backend.apply, backend.disable = partial_apply, fail_disable
    with pytest.raises(CommandError):
        controller.execute({"c": "fwd", **owner})
    assert backend.standby and controller.outputs_uncertain
    assert not any(controller.last_direction.values())
    clock.advance(1)
    backend.apply, backend.disable = real_apply, real_disable
    controller.execute({"c": "reset", "source": "browser", "session": "session_123"})
    owner = arm(controller)
    controller.execute({"c": next_command, **owner})
    assert not backend.standby
    advance(controller, clock, .099)
    assert not backend.standby
    advance(controller, clock, .002)
    assert backend.standby
    assert set(backend.outputs.values()) == ({50} if next_command == "fwd" else {-50})
