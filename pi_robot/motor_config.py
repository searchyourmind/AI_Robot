"""User-confirmed channel identities; GPIO pins and polarity remain unverified."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Channel:
    name: str
    simulation_side: str
    physical_position: str | None = None
    driver: str | None = None
    driver_channel: str | None = None
    control_pins: tuple[int, int, int] | None = None
    polarity: int | None = None
    controller: str | None = None


# Channel identities/controller path are user-confirmed, not physically tested.
# No physical backend may use these entries until GPIO pins and ratings are reviewed.
CHANNELS = (
    Channel("motor_1", "left", "front_left", "board_a", "A", controller="raspberry_pi_5_direct_gpio"),
    Channel("motor_2", "left", "back_left", "board_b", "A", controller="raspberry_pi_5_direct_gpio"),
    Channel("motor_3", "right", "front_right", "board_a", "B", controller="raspberry_pi_5_direct_gpio"),
    Channel("motor_4", "right", "back_right", "board_b", "B", controller="raspberry_pi_5_direct_gpio"),
)

DEFAULT_SPEED = 50.0
MAX_SPEED = 100.0
DEFAULT_DURATION_S = 0.25
MAX_DURATION_S = 1.0
ARM_TIMEOUT_S = 1.0
# A simulation policy, NOT an electrically validated dead time or brake period.
REVERSAL_HOLDOFF_S = 0.10
TICK_INTERVAL_S = 0.02
MAX_SERVICE_GAP_S = 0.15


def validate_channels(channels: tuple[Channel, ...]) -> None:
    if len(channels) != 4 or len({item.name for item in channels}) != 4:
        raise ValueError("exactly four distinctly named channels are required")
    if any(item.simulation_side not in {"left", "right"} for item in channels):
        raise ValueError("each simulation channel needs an explicit side")
    if {item.simulation_side for item in channels} != {"left", "right"}:
        raise ValueError("the simulation must include both sides")
