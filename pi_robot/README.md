# Pi Mobile Robot – Vision, Web Control, and AI Hooks

> **Rev A work in progress (2026-09-28):** The confirmed physical robot has **four DC motors and two TB6612FNG devices/modules**. The historical A/B code below describes two logical groups; it does not establish four-channel GPIO wiring. The user now confirms direct Pi 5 control, no Arduino in the motor loop, and the driver-to-wheel map recorded below.

Current engineering work: [../hardware/rev_a/README.md](../hardware/rev_a/README.md). See the [audit](../hardware/rev_a/docs/existing_system_audit.md), [requirements](../hardware/rev_a/docs/requirements.md), [architecture review](../hardware/rev_a/docs/architecture_review.md) and [resume point](../hardware/rev_a/PROGRESS.md).

The current motor implementation is **mock-only**, starts disarmed and requires explicit ownership/arming with expiring commands. No real GPIO backend is enabled. AI has stop-only authority; it cannot arm or issue motion. Read the [current software/API guide](../hardware/rev_a/docs/software_safety_api.md) and [vision/client guide](../docs/vision_safety_integration.md) before running anything.

State: existing software audited; board proposed; offline software tests recorded. Native schematic/PCB **not created or checked**, Rev A **not fabricated, assembled or physically tested**. Motor/source/controller/mechanical requirements and architecture/electrical review remain open. No fabrication files are released.

## Historical software notes (baseline `034882c`)

The following original project description is retained for history. Its single-driver/two-motor wording is incomplete, wiring is unverified, and run/API examples describe the old behavior. Use the current guides above for this draft; do not use the historical section as a validated wiring or actuation procedure.

This repo is a **showcase** of a Raspberry Pi mobile robot project. It’s designed to be read by recruiters and classmates – you can browse the code in VS Code or run it on real hardware.

At a high level, the system has three main parts:

1. **Motor Control Web API** (`web_motor.py`)
   - Runs on the Raspberry Pi.
   - Exposes simple HTTP endpoints on port **8088** so *any* client (web UI, Python script, or AI agent) can drive the robot.
   - Uses a **TB6612FNG** dual H‑bridge motor driver to control two DC motors.

2. **Camera + Web UI** (`web_vision_drive_picam_ai.py`)
   - Streams live MJPEG video from the Pi camera.
   - Serves a **browser UI** (HTML/JS) on port **8090** with buttons for forward / back / left / right / stop and a speed slider.
   - Uses OpenCV to grab frames from `/dev/video0`.

3. **Vision Policy Daemon (AI hook)** (`vision_policy_daemon.py`)
   - Periodically grabs frames from the camera stream.
   - Sends the frame to OpenAI’s **vision model** (`gpt-4o-mini` by default).
   - Parses the model output and decides how the robot should move, e.g.:
     - If a **stop sign** is detected → stop.
     - If a **person** is close ahead → slow down.
   - Exposes an overlay MJPEG stream with a status annotation (`action: stop / slow / go`).

There is also a **simple CLI controller** (`voice_ai_motor_simple.py`) that lets you send commands to the motor server from a terminal, which is handy while debugging or if voice control is not available.

> Note: I originally experimented with full voice control (wake words, speech‑to‑text, and text‑to‑speech) and OpenAI’s Realtime API. That code depended on a VPN + SOCKS proxy and external microphones/speakers. For this public repo I’m including a simplified, robust subset that demonstrates the architecture without the fragile networking bits.

---

## 1. Hardware Setup (High Level)

### Raspberry Pi

- Raspberry Pi 4 or 5 (I used Pi 5).
- Official Raspberry Pi camera (or compatible Pi‑camera module).
- USB audio interface + mic/speaker **optional** (for voice experiments).

### Motor Driver: TB6612FNG

The TB6612FNG controls two DC motors with separate direction and PWM inputs.

**Power:**

- `VM` → motor battery **+** (e.g. 6–9 V).
- `VCC` → Pi **3.3 V**.
- `GND` → Pi **GND** and battery **−** (common ground).

**Motor outputs:**

- `A01`, `A02` → Motor A.
- `B01`, `B02` → Motor B.

**Logic signals (connected to Pi in BCM numbering):**

- `PWMA` → GPIO **18** (pin 12) – PWM for motor A.
- `AIN1` → GPIO **23** (pin 16).
- `AIN2` → GPIO **24** (pin 18).

- `PWMB` → GPIO **13** (pin 33) – PWM for motor B.
- `BIN1` → GPIO **5**  (pin 29).
- `BIN2` → GPIO **6**  (pin 31).

- `STBY` → GPIO **25** (pin 22) – set HIGH to enable the driver.

**Important:** the Pi’s ground and the motor battery’s negative terminal **must** be connected together.

---

## 2. Software Overview

### 2.1 `web_motor.py` — Motor HTTP API

- Uses `RPi.GPIO` to configure pins, create PWM channels, and drive the TB6612FNG.
- Serves a simple JSON API via **Flask**:
  - `GET /cmd?c=fwd` – drive forward.
  - `GET /cmd?c=back` – drive backward.
  - `GET /cmd?c=left` – turn left.
  - `GET /cmd?c=right` – turn right.
  - `GET /cmd?c=stop` – stop both motors.
  - `GET /cmd?c=speed&v=60` – set speed (0–100).
  - `GET /cmd?c=pulse_fwd&v=0.5` – move forward briefly then stop.

All other modules talk to the robot **only** through this API, which keeps the architecture clean and modular.

### 2.2 `web_vision_drive_picam_ai.py` — Camera & Web UI

- Opens `/dev/video0` with OpenCV and sets resolution + FPS.
- Provides:
  - `/stream.mjpg` — MJPEG camera stream.
  - `/` — a small HTML+JS UI that shows the camera and drive controls.
- The UI sends HTTP requests directly to the motor server (`web_motor.py`).

This is what I used while tuning PID‑like constants and making sure the robot drove straight before turning on any AI.

### 2.3 `vision_policy_daemon.py` — AI Vision Policy

- Consumes the MJPEG stream exposed by `web_vision_drive_picam_ai.py`.
- Encodes a single JPEG frame as Base64 and sends it to OpenAI’s **vision model** using the official Python SDK.
- Asks the model to describe:
  - Whether a **person** is ahead and roughly how far (near / mid / far).
  - Whether a **red stop sign** is visible.
- Parses the response and maps it to a small policy:
  - `action = "stop"` → `/cmd?c=stop`
  - `action = "slow"` → `/cmd?c=speed&v=30` + `/cmd?c=fwd`
  - `action = "go"` → `/cmd?c=speed&v=70` + `/cmd?c=fwd`
- Draws a simple overlay that shows the action on top of the camera frame and exposes it as `/overlay.mjpg`.

This demonstrates how a cloud AI model can be integrated into a real‑time control loop on an embedded robot.

### 2.4 `voice_ai_motor_simple.py` — CLI Controller

This file provides a very small interactive CLI:

```text
Commands:
  f / forward   - go forward
  b / back      - go backward
  l / left      - turn left
  r / right     - turn right
  s / stop      - stop
  sp <0-100>    - set speed
  q             - quit
```

It talks to the same motor server (`/cmd` endpoints) and is useful for manual testing or demos without any web UI.

---

## 3. Requirements

Python packages (see `requirements.txt`):

- `flask`
- `opencv-python`
- `requests`
- `openai`
- `httpx`
- `numpy`

On a Raspberry Pi I used a mix of Debian packages (`python3-opencv`, `python3-flask`) and virtualenv packages (`openai`, `httpx`, etc.), but for a generic environment these `pip` requirements are enough.

On the hardware side, the code assumes:

- `/dev/video0` is a valid camera device (Pi camera or USB camera).
- `RPi.GPIO` is available and the code is running on a Pi.

---

## 4. Running the System (Typical Flow)

Below is a typical multi‑terminal setup on the Pi.

### 4.1 Motor server

```bash
cd ~/robot
python web_motor.py
```

The motor server listens on port **8088**.

### 4.2 Camera web UI

```bash
cd ~/robot
MOTOR_URL="http://127.0.0.1:8088" CAM_W=320 CAM_H=240 CAM_FPS=15 python web_vision_drive_picam_ai.py
```

Then, on a laptop on the same network, open:

- `http://<pi-ip>:8090/`

You should see the live camera head and drive buttons.

### 4.3 Vision policy daemon (OpenAI)

```bash
cd ~/robot
export OPENAI_API_KEY=sk-...   # your real key

MOTOR_URL="http://127.0.0.1:8088" STREAM_URL="http://127.0.0.1:8090/stream.mjpg" POLICY_PORT=8091 AI_MODEL="gpt-4o-mini" AI_PERIOD=3.0 python vision_policy_daemon.py
```

Then open:

- `http://<pi-ip>:8091/overlay.mjpg`

The robot will adjust speed/stop based on what the model sees (subject to the usual vision/model limitations and network latency).

### 4.4 CLI controller

```bash
cd ~/robot
MOTOR_URL="http://127.0.0.1:8088" python voice_ai_motor_simple.py
```

Type commands like `f`, `b`, `sp 60`, `s`, `q`.

---

## 5. Notes for Recruiters / Reviewers

- The focus of this repo is **system architecture**: how to structure a robot project so that **motors, camera, and AI** are cleanly decoupled and can be replaced or extended.
- The motor driver talking over HTTP means the robot can be controlled from:
  - A browser,
  - A Python script,
  - A cloud agent,
  - Or a voice/UI front‑end.
- All AI integration is done via small, inspectable Python scripts using the official OpenAI Python SDK.

If you’d like to see the full hardware (chassis, wiring, photos), I can provide them during an interview – this repo focuses on the code and architecture side.
