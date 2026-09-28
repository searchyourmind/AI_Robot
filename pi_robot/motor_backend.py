"""Injected output boundary. This revision deliberately supplies no GPIO backend."""
from typing import Mapping, Protocol


class MotorBackend(Protocol):
    name: str

    def apply(self, outputs: Mapping[str, float]) -> None:
        """Apply signed percent demand to four electrically separate channels."""

    def disable(self) -> None:
        """Demand zero PWM and STBY=False for BOTH drivers, not active braking."""


class MockBackend:
    name = "mock"

    def __init__(self, names: tuple[str, ...]):
        self.names = names
        self.outputs = dict.fromkeys(names, 0.0)
        self.standby = False
        self.events: list[dict] = []

    def apply(self, outputs: Mapping[str, float]) -> None:
        if set(outputs) != set(self.names):
            raise ValueError("all four channels must be supplied")
        self.outputs = dict(outputs)
        self.standby = any(self.outputs.values())
        self.events.append({"outputs": dict(self.outputs), "standby": self.standby})

    def disable(self) -> None:
        self.outputs = dict.fromkeys(self.names, 0.0)
        self.standby = False
        self.events.append({"outputs": dict(self.outputs), "standby": False})
