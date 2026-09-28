"""Serialized, expiring motor demands for a mock-only four-channel service."""
import math
import re
import secrets
import threading
import time
from typing import Callable, Mapping

try:
    from .motor_backend import MockBackend, MotorBackend
    from .motor_config import (
        ARM_TIMEOUT_S, CHANNELS, DEFAULT_DURATION_S, DEFAULT_SPEED,
        MAX_DURATION_S, MAX_SERVICE_GAP_S, MAX_SPEED, REVERSAL_HOLDOFF_S,
        Channel, validate_channels,
    )
except ImportError:  # Allow the existing `python pi_robot/web_motor.py` entry point.
    from motor_backend import MockBackend, MotorBackend
    from motor_config import (
        ARM_TIMEOUT_S, CHANNELS, DEFAULT_DURATION_S, DEFAULT_SPEED,
        MAX_DURATION_S, MAX_SERVICE_GAP_S, MAX_SPEED, REVERSAL_HOLDOFF_S,
        Channel, validate_channels,
    )


class CommandError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def bounded_number(value, name: str, low: float, high: float,
                   *, exclusive_low: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise CommandError(f"{name} must be a finite number")
    if isinstance(value, str) and not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value):
        raise CommandError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (ValueError, OverflowError):
        raise CommandError(f"{name} must be a finite number") from None
    if not math.isfinite(number) or number > high or number < low or (exclusive_low and number == low):
        raise CommandError(f"{name} must be {'>' if exclusive_low else '>='} {low} and <= {high}")
    return number


class MotorController:
    """Lock authorization, expiry, every output write, and shutdown together.

    This is software containment only. A frozen process cannot call disable().
    The physical implementation remains gated on architecture/electrical review.
    """

    def __init__(self, backend: MotorBackend | None = None,
                 clock: Callable[[], float] = time.monotonic,
                 channels: tuple[Channel, ...] = CHANNELS):
        validate_channels(channels)
        self.channels = channels
        self.backend = backend if backend is not None else MockBackend(tuple(c.name for c in channels))
        if self.backend.name != "mock":
            raise ValueError("only the mock backend is permitted until GPIO pins and electrical requirements are verified")
        self.clock = clock
        self.lock = threading.RLock()
        self.speed = DEFAULT_SPEED
        self.armed = False
        self.latched = False
        self.faulted = False
        self.closed = False
        self.reason = "startup-disarmed"
        self.owner: tuple[str, str] | None = None
        self.lease: str | None = None
        self.deadline: float | None = None
        self.pending: dict[str, float] | None = None
        self.pending_at: float | None = None
        self.outputs = dict.fromkeys((c.name for c in channels), 0.0)
        self.last_direction = dict.fromkeys(self.outputs, 0)
        self.zero_since = dict.fromkeys(self.outputs, float("-inf"))
        self.outputs_uncertain = False
        self.recovery_holdoff_until = float("-inf")
        self.last_service = self.clock()
        self.disable_confirmed = False
        self._disable(self.last_service)

    def _disable(self, now: float) -> bool:
        try:
            self.backend.disable()
            for name, value in self.outputs.items():
                if value or self.outputs_uncertain:
                    self.zero_since[name] = now
            if self.outputs_uncertain:
                # A failed apply may have energized a channel whose direction
                # was never recorded. Recovery must hold ALL channels disabled.
                self.recovery_holdoff_until = now + REVERSAL_HOLDOFF_S
            self.outputs = dict.fromkeys(self.outputs, 0.0)
            self.outputs_uncertain = False
            self.disable_confirmed = True
            return True
        except Exception:
            # A failed physical write could leave energized hardware. Never report
            # confirmed disable, and never clear the fault on a failed retry.
            self.disable_confirmed = False
            self.outputs_uncertain = True
            self.faulted = self.latched = True
            self.reason = "backend-disable-failed"
            return False

    def _trip(self, reason: str, now: float, *, fault: bool = False) -> None:
        self.armed = False
        self.latched = True
        self.faulted = self.faulted or fault
        self.reason = reason
        self.owner = self.lease = None
        self.pending = self.pending_at = self.deadline = None
        self._disable(now)

    def fault(self, reason: str = "invalid-request") -> None:
        with self.lock:
            self._trip(reason, self.clock(), fault=True)

    def _write(self, values: dict[str, float], now: float) -> None:
        try:
            if any(values.values()):
                self.backend.apply(values)
            else:
                self.backend.disable()
            for name, value in values.items():
                if self.outputs[name] and not value:
                    self.zero_since[name] = now
                if value:
                    self.last_direction[name] = 1 if value > 0 else -1
            self.outputs = dict(values)
            self.disable_confirmed = not any(values.values())
        except Exception:
            self.outputs_uncertain = True
            self._trip("backend-write-failed", now, fault=True)
            raise CommandError("backend write failed; fault latched", 503) from None

    def _advance(self, now: float) -> None:
        gap = now - self.last_service
        self.last_service = now
        if not math.isfinite(now) or gap < 0:
            self._trip("invalid-clock", now, fault=True)
            return
        if self.closed:
            return
        if self.armed and gap > MAX_SERVICE_GAP_S:
            self._trip("software-watchdog-gap", now, fault=True)
            return
        if self.deadline is not None and now >= self.deadline:
            self._trip("command-expired", now)
            return
        if self.pending is not None and now >= self.pending_at:
            values = self.pending
            self.pending = self.pending_at = None
            self._write(values, now)

    def tick(self) -> None:
        with self.lock:
            self._advance(self.clock())

    def _identity(self, data: Mapping) -> tuple[str, str]:
        source, session = data.get("source"), data.get("session")
        if not isinstance(source, str) or source not in {"manual", "browser", "voice"}:
            raise CommandError("only manual, browser, or voice may own motion", 403)
        if not isinstance(session, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", session):
            raise CommandError("session must contain 8..128 letters, digits, underscores, or hyphens")
        return source, session

    def _authorize(self, data: Mapping) -> None:
        identity = self._identity(data)
        if not self.armed or self.latched:
            raise CommandError("disarmed or latched; explicit reset and arm required", 409)
        lease = data.get("lease")
        if (self.owner != identity or not isinstance(lease, str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{32}", lease)
                or not secrets.compare_digest(lease, self.lease or "")):
            raise CommandError("owner/session/lease mismatch", 409)

    def execute(self, data: Mapping) -> dict:
        with self.lock:
            now = self.clock()
            try:
                if not isinstance(data, dict) or not isinstance(data.get("c"), str):
                    raise CommandError("a command object with string c is required")
                c = data["c"]
                if c == "stop":
                    # Stop always wins, even from an expired or untrusted session.
                    self._trip("stop-requested", now)
                    if not self.disable_confirmed:
                        raise CommandError("disable failed; stop is latched but outputs are uncertain", 503)
                    return self._result(c)
                self._advance(now)
                if self.closed:
                    raise CommandError("controller is shut down", 409)
                fields = {"c", "source", "session", "lease"}
                if c in {"fwd", "back", "left", "right", "pulse_fwd"}:
                    fields |= {"speed", "duration"}
                    if c == "pulse_fwd":
                        fields.add("v")
                elif c == "speed":
                    fields |= {"v", "speed"}
                elif c not in {"arm", "reset"}:
                    raise CommandError("unknown command")
                if set(data) - fields:
                    raise CommandError("unknown command fields")
                if c == "reset":
                    self._identity(data)
                    if self.armed:
                        raise CommandError("stop before resetting", 409)
                    if not self._disable(now):
                        raise CommandError("disable failed; fault remains latched", 503)
                    self.latched = self.faulted = False
                    self.reason = "reset-disarmed"
                    self.owner = self.lease = None
                    return self._result(c)
                if c == "arm":
                    identity = self._identity(data)
                    if self.armed or self.latched:
                        raise CommandError("already armed or latched; stop/reset before arming", 409)
                    if not self._disable(now):
                        raise CommandError("disable failed; cannot arm", 503)
                    self.armed = True
                    self.reason = "armed-idle"
                    self.owner = identity
                    self.lease = secrets.token_urlsafe(24)
                    self.deadline = now + ARM_TIMEOUT_S
                    return {**self._result(c), "lease": self.lease}
                self._authorize(data)
                if c == "speed":
                    if ("speed" in data) == ("v" in data):
                        raise CommandError("supply exactly one speed or v")
                    self.speed = bounded_number(data.get("speed", data.get("v")), "speed", 0, MAX_SPEED)
                    return self._result(c)
                if "duration" in data and "v" in data:
                    raise CommandError("supply duration or legacy pulse v, not both")
                speed = bounded_number(data.get("speed", self.speed), "speed", 0, MAX_SPEED)
                duration = bounded_number(data.get("duration", data.get("v", DEFAULT_DURATION_S)), "duration", 0, MAX_DURATION_S, exclusive_low=True)
                signs = {"fwd": (1, 1), "pulse_fwd": (1, 1), "back": (-1, -1), "left": (-1, 1), "right": (1, -1)}[c]
                values = {ch.name: speed * signs[ch.simulation_side == "right"] for ch in self.channels}
                reversing = [name for name, value in values.items() if value and self.last_direction[name] and (1 if value > 0 else -1) != self.last_direction[name]]
                if any(self.outputs[name] for name in reversing):
                    if not self._disable(now):
                        self._trip("backend-disable-failed", now, fault=True)
                        raise CommandError("disable failed; fault latched", 503)
                ready = max([now, self.recovery_holdoff_until if any(values.values()) else now]
                            + [self.zero_since[name] + REVERSAL_HOLDOFF_S for name in reversing])
                self.pending = self.pending_at = None
                self.deadline = now + duration
                self.speed = speed
                if ready > now:
                    self.pending, self.pending_at = values, ready
                    self.reason = "reversal-holdoff"
                else:
                    self._write(values, now)
                    self.reason = "motion-command"
                return self._result(c)
            except CommandError as exc:
                if exc.status == 400:
                    self._trip("invalid-command", now, fault=True)
                raise

    def _result(self, command: str | None = None) -> dict:
        return {
            "ok": True, "cmd": command, "backend": self.backend.name,
            "physical_actuation_enabled": False,
            "state": "shutdown" if self.closed else "fault" if self.faulted else "stopped" if self.latched else "armed" if self.armed else "disarmed",
            "armed": self.armed, "latched": self.latched, "reason": self.reason,
            "speed": self.speed, "outputs": dict(self.outputs),
            "standby": bool(any(self.outputs.values())),
            "disable_confirmed": self.disable_confirmed,
            "outputs_uncertain": self.outputs_uncertain,
            "owner": {"source": self.owner[0], "session": self.owner[1]} if self.owner else None,
            "expires_in_s": max(0.0, self.deadline - self.clock()) if self.deadline is not None else None,
            "pending_reversal": self.pending is not None,
        }

    def status(self) -> dict:
        with self.lock:
            self._advance(self.clock())
            return self._result()

    def shutdown(self) -> None:
        with self.lock:
            self._trip("shutdown", self.clock())
            self.closed = True
