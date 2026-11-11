# Raspberry Pi 5 backend for the four-DRV8874 Rev A board

`DRV8874RevABackend` drives the custom board described by the repository's
[J6 pin map](../hardware/rev_a/docs/pin_map.md) and
[enable contract](../hardware/rev_a/docs/enable_interface_spec.md). It is real
GPIO code with offline fake-GPIO verification. The board, installed harness,
PWM timing, and motor behavior still require bench validation.

The existing robot's two TB6612 boards and four independent DRV8874 breakout
modules do **not** use this interface. This backend requires the Rev A decoder,
watchdog, and ARM latch between the Pi and the drivers.

## Four bridges, two command groups

| Software channel | Wheel | Rev A bridge | Command group |
|---|---|---|---|
| `motor_1` | Front left | U20 | Left |
| `motor_2` | Back left | U22 | Left |
| `motor_3` | Front right | U21 | Right |
| `motor_4` | Back right | U23 | Right |

Each motor has its own H bridge and two-terminal output. Left front/rear share
PWM/DIR commands, as do right front/rear. The backend rejects unequal demands
within either pair. It cannot compensate for opposite front/rear wiring with
per-wheel software inversion; those motors must be wired consistently.

| Signal | BCM GPIO | Pi physical pin | Board J6 pin |
|---|---:|---:|---:|
| Left PWM | 18 | 12 | 3 |
| Left DIR | 23 | 16 | 5 |
| Right PWM | 13 | 33 | 7 |
| Right DIR | 5 | 29 | 9 |
| RUN request | 25 | 22 | 11 |
| Explicit ARM pulse | 17 | 11 | 12 |
| Watchdog heartbeat | 27 | 13 | 13 |

J6.1 receives Pi 3.3 V. J6.2/4/8/14/15/16 are grounds. J6.6 and J6.10 are
unconnected, **not grounds**. J6 is a custom 16-pin connector, not the Pi's
40-pin header; use the full pin map to identify connector orientation. The
Pi remains separately powered. No Pi 5 V pin connects to this board.

## Install and configure on the Pi

Use Python 3.10+ and a Linux image with the Pi 5 RP1 GPIO character device.
The backend imports `lgpio` only when hardware mode is selected. One installation
path on Raspberry Pi OS is:

```sh
sudo apt install python3-lgpio
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
python -m pip install Flask
```

Alternatively, install `pi_robot/requirements-hardware.txt` into the intended
environment; building `lgpio` from source may require the distribution's build
dependencies. The service account needs access to the RP1 `/dev/gpiochip*`
device. Keep a single motor-service process responsible for those lines.

The backend discovers a GPIO chip whose label is `pinctrl-rp1`, then verifies
that label before claiming any outputs. It does not assume `gpiochip4`: Pi 5
chip numbering differs across kernel versions. An explicitly configured chip
number must pass the same verification.

Copy and edit the configuration:

```sh
cp pi_robot/config/drv8874_reva.example.json /path/to/robot-motor.json
```

The template deliberately leaves both polarities unset. Set each to `1` or
`-1` according to the actual wheel wiring before hardware startup. Unknown or
invalid configuration is rejected; no fallback starts a different backend.

| JSON field | Value / default | Meaning |
|---|---|---|
| `left_polarity` | Required: `1` or `-1` | Maps positive left demand to electrical direction. |
| `right_polarity` | Required: `1` or `-1` | Maps positive right demand to electrical direction. |
| `pwm_hz` | `1000` | Software PWM frequency; permitted range 0.1–10,000 Hz. |
| `startup_settle_s` | `1.0` | Configured startup allowance, followed by at least one additional second of heartbeat qualification. |
| `reversal_holdoff_s` | `0.1` | Controller's zero-demand interval before applying an opposite direction. This default is unvalidated. |
| `gpiochip` | `null` | Discover RP1 automatically; an integer explicitly selects and verifies that chip. |

The PWM implementation uses `lgpio.tx_pwm`, which is **software timed**. It
does not use the RP1 hardware PWM peripheral just because GPIO18/13 can support
PWM. Frequency, pulse jitter, and behavior under system load need measurement.
The selected frequency must also suit the motors, board, and application.

Start the supported launcher from the repository root:

```sh
MOTOR_BACKEND=drv8874_reva MOTOR_CONFIG=/path/to/robot-motor.json \
  python -m pi_robot.web_motor
```

This binds to `127.0.0.1:8088` and starts the controller ticker. A bare WSGI
import or `flask run` does not start the ticker and is not a supported hardware
launcher. Importing `web_motor` alone still creates only the default mock app.
The HTTP interface is local and has no user authentication; leases coordinate
clients, rather than authenticate them.

## Output and lifecycle behavior

- Startup claims RUN low first and initializes ARM, heartbeat, PWM, and DIR
  low. Selecting hardware mode does not send an ARM pulse or a motion demand.
- The controller's healthy tick sends the heartbeat with ordinary GPIO writes.
  High/low intervals must be at least 1 ms and falling edges at most 50 ms
  apart. No independent keepalive thread or PWM generator feeds the watchdog.
  Status polling and command requests cannot substitute for the ticker.
- Software qualification requires continuous heartbeat for at least
  `startup_settle_s + 1` seconds and at least three completed cycles. An early
  explicit `arm` request returns HTTP 409. A later attempt must be deliberate;
  there is no automatic ARM retry.
- On an accepted software ARM request, PWM remains low, RUN goes high, and
  after at least 1 ms ARM is pulsed high for at least 1 ms, then low. The API
  returns the ordinary owner lease and starts its one-second idle deadline.
- Positive/negative demands select direction after side polarity is applied.
  Duty is `abs(demand)` for **both** directions; reverse duty is not inverted.
- While armed, zero PWM requests braking through the Rev A decoder. A zero
  speed command or reversal holdoff preserves RUN and uses this brake state.
  PWM is lowered before DIR changes, followed by logic settling. The controller
  also waits the configured reversal holdoff; this is not transistor dead time
  or a measured motor-current decay interval.
- Stop, expiry, fault, and shutdown lower RUN before clearing PWM/ARM. RUN low
  clears the board's ARM latch and requests coast. It does not remove VM power
  or necessarily put the drivers to sleep. Resuming requires explicit reset
  and ARM; applying a demand never creates another ARM edge.
- GPIO errors attempt disable and latch the backend failure. Reinitializing
  the service is required after an I/O failure. Shutdown attempts all cleanup
  steps, including releasing GPIO resources, even when one operation fails.

The independent TPS3431 watchdog is specified for 170–230 ms after the last
accepted falling edge. Linux/Python cannot guarantee the ticker's timing;
late service is treated as a fault. The watchdog interval is an electrical
timeout specification, not a guaranteed wheel-stopping time.

## What status can establish

J6 provides **no feedback** for hardware enable, ALL_OK, faults, physical
switch position, motor current, or wheel speed. `physical_backend: true`
means that actual GPIO is selected. `physical_actuation_enabled: null` means
that physical enable is unknown. `armed`, output values, and the nested
`hardware` status describe software requests and timing qualification.
`disable_confirmed` records acceptance of the software disable operation;
it cannot establish that the motors stopped.

Software readiness also cannot detect when the physical switch was enabled.
After changing physical enable or motor power, allow the actual rail/driver
startup to settle and the specified heartbeat qualification time before a
fresh explicit ARM, even if software already reports ready. The hardware gates
reject an ARM edge while unqualified, and the backend cannot observe or retry
that rejection automatically.

A hardware fault clears the board's latch independently of Python. Clearing
that fault does not restore motion permission. `reset` clears only the
software latch; a DRV8874 internal overcurrent latch can require physical
disable/re-enable or motor-power cycling, followed by startup qualification
and a new ARM. Never interpret software reset as measured fault clearance.

## First bench checks and offline tests

Before a powered motion trial, check the assembled Rev A board and J6 continuity
against the design. With motors disconnected, measure startup levels, the
ARM sequence, PWM/direction, and heartbeat. Exercise stop and heartbeat loss
while observing the board's actual drive permission. Confirm the selected
startup allowance and reversal policy against the real supply and load.

For the first motor trial, raise the wheels clear of the surface and use short,
low-duty commands to establish both sides' direction. A forward request must
turn both motors on each side consistently; correct wiring/polarity before
increasing demand. The existing API limits each movement command to at most
one second and latches stop on expiry. It provides no encoder feedback.

Run offline regression checks on a development machine:

```sh
python -m pip install -r tests/hardware_mock/requirements.txt
python -m pytest tests/hardware_mock tests/hardware_gpio -q
```

These use injected clocks and a fake GPIO provider. They check software
ordering, pairing, duty, heartbeat qualification, explicit ARM, failure paths,
and cleanup. They do not open real GPIO or validate electrical timing,
waveforms, physical braking, current, or temperature.

Implementation references: [lgpio Python API source](https://github.com/joan2937/lg/blob/master/PY_LGPIO/lgpio_extra.py),
[Raspberry Pi GPIO guidance](https://pip-assets.raspberrypi.com/categories/685-whitepapers-app-notes-compliance-guides/documents/RP-006553-WP/A-history-of-GPIO-usage-on-Raspberry-Pi-devices-and-current-best-practices),
[DRV8874 datasheet](https://www.ti.com/lit/ds/symlink/drv8874.pdf), and
[TPS3431 datasheet](https://www.ti.com/lit/ds/symlink/tps3431.pdf).
