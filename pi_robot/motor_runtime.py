"""Explicit service configuration; importing this module never opens GPIO."""
import json
import os
from pathlib import Path
from typing import Mapping

try:
    from .motor_config import Channel
    from .motor_control import MotorController
except ImportError:  # Support python pi_robot/web_motor.py.
    from motor_config import Channel
    from motor_control import MotorController


def _unique_fields(pairs):
    fields = {}
    for key, value in pairs:
        if key in fields:
            raise ValueError(f"duplicate motor configuration field: {key}")
        fields[key] = value
    return fields


def load_drv8874_config(path):
    """Validate the whole configuration before the GPIO provider is loaded."""
    try:
        from .drv8874_backend import DRV8874Config
    except ImportError:
        from drv8874_backend import DRV8874Config

    with Path(path).open("rb") as stream:
        raw = stream.read(4097)
    if len(raw) > 4096:
        raise ValueError("motor configuration exceeds 4096 bytes")
    data = json.loads(raw, object_pairs_hook=_unique_fields)
    if not isinstance(data, dict):
        raise ValueError("motor configuration must be a JSON object")
    allowed = {"left_polarity", "right_polarity", "pwm_hz",
               "startup_settle_s", "reversal_holdoff_s", "gpiochip"}
    if set(data) - allowed:
        raise ValueError("unknown motor configuration fields: " + ", ".join(sorted(set(data) - allowed)))
    if not {"left_polarity", "right_polarity"} <= set(data):
        raise ValueError("left_polarity and right_polarity must be explicitly set to 1 or -1")
    return DRV8874Config(**data)


def create_controller_from_env(environ: Mapping[str, str] | None = None) -> MotorController:
    """Mock by default; the supported Rev A backend requires an explicit config."""
    env = os.environ if environ is None else environ
    name = env.get("MOTOR_BACKEND", "mock")
    if name == "mock":
        if env.get("MOTOR_CONFIG"):
            raise ValueError("MOTOR_CONFIG requires MOTOR_BACKEND=drv8874_reva")
        return MotorController()
    if name != "drv8874_reva":
        raise ValueError("MOTOR_BACKEND must be mock or drv8874_reva")
    path = env.get("MOTOR_CONFIG")
    if not path:
        raise ValueError("MOTOR_BACKEND=drv8874_reva requires MOTOR_CONFIG pointing to a JSON file")
    config = load_drv8874_config(path)
    try:
        from .drv8874_backend import DRV8874RevABackend
    except ImportError:
        from drv8874_backend import DRV8874RevABackend

    # The historical CHANNELS describe the TB6612 prototype. These identities
    # belong specifically to Rev A and its paired PWM/DIR J6 interface.
    # control_pins records (PWM, DIR, shared RUN); ARM/HB are board-wide and
    # managed by the backend, not separate per-motor signals.
    channels = tuple(
        Channel(name, side, position, driver, "H-bridge", pins, polarity,
                "raspberry_pi_5_direct_gpio")
        for name, side, position, driver, pins, polarity in (
            ("motor_1", "left", "front_left", "U20", (18, 23, 25), config.left_polarity),
            ("motor_2", "left", "back_left", "U22", (18, 23, 25), config.left_polarity),
            ("motor_3", "right", "front_right", "U21", (13, 5, 25), config.right_polarity),
            ("motor_4", "right", "back_right", "U23", (13, 5, 25), config.right_polarity),
        )
    )
    backend = DRV8874RevABackend(config)
    try:
        controller = MotorController(backend=backend, channels=channels,
                                     reversal_holdoff_s=config.reversal_holdoff_s)
        if not controller.disable_confirmed:
            raise RuntimeError("initial GPIO disable failed; motor service will not start")
        return controller
    except BaseException:
        # Preserve the original startup failure even if resource cleanup fails.
        try:
            backend.close()
        except Exception:
            pass
        raise
