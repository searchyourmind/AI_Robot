# Rev A backend offline tests

From the repository root:

```sh
python -m pip install -r tests/hardware_mock/requirements.txt
python -m pytest tests/hardware_mock tests/hardware_gpio -q
```

No `lgpio` installation, Raspberry Pi, or motor board is required. The fixtures
block real GPIO imports and network connections; GPIO operations and elapsed
time are supplied by test substitutes.

- `test_drv8874_backend.py`: RP1 identification, initial output levels, paired
  demands, polarity/duty, heartbeat timing and qualification, ARM sequencing,
  write/cleanup failures, and Flask-to-backend integration.
- `test_controller_lifecycle.py`: ownership, heartbeat starvation, reversal
  and recovery timing, partial ARM cleanup, readable faults, and final shutdown.
- `test_motor_runtime.py`: explicit backend selection, strict JSON config,
  inert imports, startup failure cleanup, and service shutdown.

These checks verify software behavior and requested operation order. They do
not measure real GPIO timing, motor current, physical stopping, or PCB function.
See the [backend setup and bench guide](../../pi_robot/DRV8874_REVA.md).
