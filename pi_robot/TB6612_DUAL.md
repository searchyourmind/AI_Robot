# Raspberry Pi 5 backend for the prototype's two TB6612FNG boards

`TB6612Backend` drives the robot as it is built today: a Pi 5 wired directly to
two TB6612FNG carrier boards, four motors. It is real GPIO code, verified
offline against a fake GPIO chip. **It has not been run on the robot.** Pin
wiring, polarity, PWM timing and motor current still need the bench checks below.

The custom [Rev A DRV8874 board](DRV8874_REVA.md) has its own backend. Both sit
behind the same controller, API, browser page and CLI; `MOTOR_BACKEND` selects one.

## Read this before powering motors

- **No hardware watchdog.** If the Python process freezes or is killed hard
  (`kill -9`, a crash), nothing lowers the pins. A PWM pin can stay high, which
  is full power. Keep a switch on the motor supply within reach.
- **Stall current is at the driver's limit.** A TB6612FNG channel allows 1.2 A
  average and a single 3.2 A, 10 ms pulse. The candidate motor's published stall
  current is 3.2 A at 12 V. That is why `max_duty_percent` is required and why
  speed increases are ramped. Do not block a driven wheel.
- **Motor supply must stay below 13.5 V**, the TB6612FNG's operating maximum
  (15 V absolute). Measure the pack at full charge; "12 V" on a label is not enough.
- Run the first trials with the wheels off the ground.

## Wiring the backend expects

Each motor channel uses three Pi outputs, and each carrier has one STBY input:

| TB6612FNG input | Meaning |
|---|---|
| `PWMA` / `PWMB` | Speed (PWM) |
| `AIN1`,`AIN2` / `BIN1`,`BIN2` | Direction. IN1 high = one way, IN2 high = the other, both low = stop |
| `STBY` | High enables the carrier; low puts its outputs in standby |

| Software channel | Wheel | Carrier, channel |
|---|---|---|
| `motor_1` | Front left | Board A, channel A |
| `motor_2` | Back left | Board B, channel A |
| `motor_3` | Front right | Board A, channel B |
| `motor_4` | Back right | Board B, channel B |

Two wiring styles are supported:

- **Shared inputs.** The two left channels are joined to the same three Pi pins,
  and likewise the two right channels. Give both motors of a side the same
  `pwm`/`in1`/`in2` and the same `polarity`. This is what the example file
  describes. If the front and rear wheel of one side then turn opposite ways,
  swap one motor's two leads; software cannot correct it.
- **Separate inputs.** Every channel has its own three pins and its own `polarity`.

Sharing is all-or-nothing: one complete triple, same side only. `stby` lists one
pin if both carriers' STBY inputs are joined, or two pins if they are separate.

## Configure

```sh
cp pi_robot/config/tb6612_dual.example.json /path/to/robot-motor.json
```

The example's pin numbers come from the original January control script
(BCM numbering; physical header pin in brackets): left PWM 18 [12], IN1 23 [16],
IN2 24 [18]; right PWM 13 [33], IN1 5 [29], IN2 6 [31]; STBY 25 [22].
**Check them against the actual wires.** That script named one set of pins and
did not say how the second carrier is connected.

| JSON field | Value / default | Meaning |
|---|---|---|
| `channels` | Required | `motor_1` to `motor_4`, each with `pwm`, `in1`, `in2` (BCM 2–27) and `polarity`. |
| `polarity` | Required: `1` or `-1` | Which input a forward demand raises. The example leaves it `null`, so an unedited copy is rejected. |
| `stby` | Required: one or two pins | Carrier enable outputs. |
| `max_duty_percent` | Required: 1–100 | PWM duty at speed 100. Actual duty = speed × this ÷ 100, so speed 50 with a ceiling of 40 is 20 % duty. |
| `ramp_percent_per_s` | `400` | Fastest duty increase. 400 reaches 40 % in 0.1 s. Decreases and stops are immediate. |
| `pwm_hz` | `1000` | Software PWM frequency, 0.1–10,000 Hz. |
| `reversal_holdoff_s` | `0.1` | Time with drive removed before the opposite direction is applied. Unvalidated. |
| `gpiochip` | `null` | Find the Pi 5 header chip by its `pinctrl-rp1` label; an integer selects and still verifies one. |

## Install and start on the Pi

```sh
sudo apt install python3-lgpio
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
python -m pip install Flask
MOTOR_BACKEND=tb6612_dual MOTOR_CONFIG=/path/to/robot-motor.json \
  python -m pi_robot.web_motor
```

The January script reached the pins through the `RPi.GPIO` interface; this
backend calls `lgpio` directly, so `lgpio` is the only GPIO package it needs.
Use this launcher, not `flask run`: it starts the controller ticker that expires
commands and advances the ramp. Only one process may own these GPIOs.

## What the backend does

- **Startup:** claims STBY low first, then every PWM and direction pin low. It
  never arms or moves on its own.
- **`arm`:** lowers every input, then raises STBY.
- **Motion:** sets direction, then the ticker raises duty step by step to the
  target. A direction change removes drive first and lowers the old input before
  raising the new one, so both are never high together.
- **Stop, command expiry, fault, shutdown:** STBY low first, then PWM cancelled
  and all inputs low. Moving again needs `reset` and `arm`.
- **GPIO error:** STBY is lowered and the backend refuses further use until the
  service is restarted.

`status` reports what was *written* to the pins. The carriers give no feedback,
so `physical_actuation_enabled` is `null` and nothing confirms a wheel stopped.

## First bench session

1. Trace and write down the wires from each carrier's PWM, IN1, IN2 and STBY to
   the Pi, then edit the configuration to match.
2. Measure the motor supply voltage. Lift the wheels. Know where the supply switch is.
3. Guess each `polarity`, keep `max_duty_percent` at 40, and start the service.
4. In a second terminal run `python pi_robot/voice_ai_motor_simple.py`, then
   `reset`, `arm`, `sp 100`. The speed setting is kept. The arm lapses after one
   idle second, which is expected.
5. `reset`, `arm`, then `f` within one second. The wheels run for 0.25 s and the
   service latches stopped again; repeat `reset`, `arm`, `f` for another run.
6. Every wheel should turn forward. If a whole side turns backward, flip that
   `polarity` and restart. If wheels do not turn, raise `max_duty_percent` in
   small steps.
7. Try `b`, `l`, `r` the same way, and `s` to stop. Feel the driver chips for
   heat between trials.

## Offline tests

```sh
python -m pip install -r tests/hardware_mock/requirements.txt
python -m pytest tests/hardware_mock tests/hardware_gpio -q
```

`tests/hardware_gpio/test_tb6612_backend.py` checks pin order, polarity, the duty
ceiling, the ramp, reversal, stop and failure paths, configuration rules, and
the path from the HTTP API to the fake pins. It cannot check real timing,
current, heat, or that a wheel moves.

The driver limits and motor figures above are those collected in the
[driver margin review](../hardware/rev_a/docs/driver_margin_review.md); the
known and unknown facts about the installed wiring are in the
[hardware evidence record](../hardware/rev_a/docs/actual_hardware_evidence.md).
