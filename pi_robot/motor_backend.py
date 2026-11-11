"""Injected motor output and explicit hardware lifecycle boundary."""
from typing import Mapping, Protocol


class BackendNotReady(RuntimeError):
    """An explicit arm attempt needs more qualification or configuration."""


class MotorBackend(Protocol):
    name: str

    def arm(self, now: float) -> None:
        """Request permission once, only after a deliberate operator command."""

    def service(self, now: float) -> None:
        """Service hardware supervision after the arbiter validates its state."""

    def check_health(self, now: float) -> None:
        """Reject stale or failed command state without feeding supervision."""

    def apply(self, outputs: Mapping[str, float]) -> None:
        """Apply signed percent demand to four electrically separate channels."""

    def quiesce(self) -> None:
        """Request zero demand while preserving an existing arm permission."""

    def disable(self) -> None:
        """Request zero PWM and revoke hardware motion permission."""

    def close(self) -> None:
        """Release owned hardware resources after requesting disable."""

    def describe(self, now: float) -> dict:
        """Describe commanded state, without asserting unobserved feedback."""


class MockBackend:
    name = "mock"

    def __init__(self, names: tuple[str, ...]):
        self.names = names
        self.outputs = dict.fromkeys(names, 0.0)
        self.standby = False
        self.events: list[dict] = []

    def arm(self, now: float) -> None:
        pass

    def service(self, now: float) -> None:
        pass

    def check_health(self, now: float) -> None:
        pass

    def apply(self, outputs: Mapping[str, float]) -> None:
        if set(outputs) != set(self.names):
            raise ValueError("all four channels must be supplied")
        self.outputs = dict(outputs)
        self.standby = any(self.outputs.values())
        self.events.append({"outputs": dict(self.outputs), "standby": self.standby})

    def quiesce(self) -> None:
        self.disable()

    def disable(self) -> None:
        self.outputs = dict.fromkeys(self.names, 0.0)
        self.standby = False
        self.events.append({"outputs": dict(self.outputs), "standby": False})

    def close(self) -> None:
        pass

    def describe(self, now: float) -> dict:
        return {"simulated": True, "fault_feedback_available": False}
