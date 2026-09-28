# Robot software: camera, manual control, and AI observation

This directory contains the Raspberry Pi software for the four-wheel AI Robot: a motor command service, a camera stream and browser interface, a terminal controller, and an optional AI vision process. The [project README](../README.md) describes the complete robot and its development. The [Rev A hardware directory](../hardware/rev_a/README.md) contains the custom board design.

The current motor backend stores commands in memory. It does not write GPIO or move motors. The camera and AI processes are separate: starting the camera script opens the camera; explicitly enabling the AI process sends images to the configured model service. This separation lets us develop and check the control logic without requiring the physical drivetrain.

## How the software fits together

```text
Browser controls ── camera/web service ─┐
                                      ├── motor HTTP service ── controller ── mock outputs
Terminal controller ──────────────────┘                          │
                                                                └── four channel demands
Camera worker ── latest-frame cache ── MJPEG display
                         │
                         └── JPEG snapshot ── AI observation ── stop request
                                                      └─────── annotated overlay
```

Manual clients share one motor API. The controller owns command parsing, client ownership, output state, reversal timing, and expiration. The vision process can request a stop but cannot arm, reset, select a speed, or initiate movement.

| File | Responsibility |
|---|---|
| [`web_motor.py`](web_motor.py) | Flask motor API, local development launcher, and periodic controller tick. |
| [`motor_control.py`](motor_control.py) | Four-channel command state machine, owner leases, latched stops, finite movement commands, and backend error handling. |
| [`motor_config.py`](motor_config.py) | Channel identities and controller timing constants. |
| [`motor_backend.py`](motor_backend.py) | Backend interface and in-memory `MockBackend`. |
| [`web_vision_drive_picam_ai.py`](web_vision_drive_picam_ai.py) | Camera capture worker, MJPEG display, snapshot endpoint, browser controls, and same-origin motor/overlay proxies. |
| [`vision_policy_daemon.py`](vision_policy_daemon.py) | Snapshot acquisition, optional model calls, stop-only policy application, and annotated MJPEG overlay. |
| [`vision_safety.py`](vision_safety.py) | Observation timestamps, freshness checks, and strict model-result parsing. |
| [`voice_ai_motor_simple.py`](voice_ai_motor_simple.py) | Interactive text controller with explicit reset/arm and best-effort stop on exit. |

## Four wheels and paired commands

The existing robot uses four motors on two TB6612 dual-channel boards. The software records the following reported channel identities:

| Software channel | Wheel | Existing driver output | Command group |
|---|---|---|---|
| `motor_1` | Front left | Board A, channel A | Left |
| `motor_2` | Back left | Board B, channel A | Left |
| `motor_3` | Front right | Board A, channel B | Right |
| `motor_4` | Back right | Board B, channel B | Right |

Forward, reverse, and turning commands are expressed as paired left/right demands, while the backend receives four distinct signed duty values. The motor outputs remain separate; pairing commands does not mean connecting H-bridge outputs together. Encoder feedback and closed-loop wheel-speed control are not implemented in this software.

Physical GPIO assignments and polarity remain unset in `motor_config.py`. The current `standby`/STBY fields belong to the retained mock interface. The new four-DRV8874 board has a different PWM/DIR, RUN, ARM, and heartbeat contract; its physical backend has not been implemented. See the board's [pin map](../hardware/rev_a/docs/pin_map.md) and [enable interface](../hardware/rev_a/docs/enable_interface_spec.md) for that integration work.

## Install and run the offline checks

Run these commands from the repository root. Use Python 3.10 or newer; the recorded test environment uses Python 3.14.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r tests/hardware_mock/requirements.txt
python -m pytest tests/hardware_mock -q
```

The test dependencies are sufficient for the mock controller and injected camera/model tests. The suite uses fake clocks, in-memory HTTP adapters, camera substitutes, and model responses. It does not open a camera, call a model service, or use GPIO. The recorded full suite has 132 passing tests; details are in the [test guide](../tests/hardware_mock/README.md) and [software test report](../hardware/rev_a/validation/software_test_report.md).

For camera display and optional live model use, install the application dependencies in the same environment:

```sh
python -m pip install -r pi_robot/requirements.txt
```

These include Flask, Requests, OpenCV, NumPy, OpenAI, and HTTPX. Camera startup also requires an operating-system camera interface that OpenCV can open as device index `0`. The script does not use Picamera2 or select a device through an environment variable.

## Run the motor service and terminal controller

In one terminal, from the repository root:

```sh
MOTOR_BACKEND=mock python -m pi_robot.web_motor
```

The service listens on `http://127.0.0.1:8088`. Its supported launcher starts the controller ticker and disables the Flask reloader. Use this module launcher rather than a bare `flask run` or WSGI import, which does not start the ticker. Only `MOTOR_BACKEND=mock` is accepted.

In a second terminal with the same virtual environment active:

```sh
MOTOR_URL=http://127.0.0.1:8088 python -m pi_robot.voice_ai_motor_simple
```

The filename comes from the earlier voice-control experiments; this program accepts typed commands and does not record audio or perform speech recognition.

| Command | Behavior |
|---|---|
| `reset` | Clear a stop/fault latch while remaining disarmed. |
| `arm` | Request a new owner lease; start a 1-second idle deadline. |
| `f` / `forward` | Send a forward demand lasting 0.25 seconds. |
| `b` / `back` | Send a reverse demand lasting 0.25 seconds. |
| `l` / `left`, `r` / `right` | Send a turn demand lasting 0.25 seconds. |
| `sp 25` | Set the next command's speed to 25%; requires an active lease. |
| `s` / `stop` | Stop, disarm, and latch. |
| `q` | Request stop and exit. |

Send the movement command promptly after arming: the idle deadline is only one second. After any stop or movement expiry, use `reset` followed by `arm` again. These are discrete commands, not continuous keyboard driving. Changing speed or reading status does not extend an active command. The CLI clears its lease and requests stop after command errors, and requests stop on quit, EOF, or Ctrl-C.

## Camera and browser controls

With the motor service running, start the camera/web process in another terminal:

```sh
MOTOR_URL=http://127.0.0.1:8088 CAM_W=320 CAM_H=240 CAM_FPS=15 \
  python -m pi_robot.web_vision_drive_picam_ai
```

This command opens the camera. Visit `http://127.0.0.1:8090/` on the same machine for the video, speed slider, reset/arm buttons, direction buttons, and stop button. Each direction button sends a 0.25-second demand to the mock motor service. The selected speed is included in that demand.

The page talks to `/motor/cmd` and `/motor/status` on its own origin; the camera service forwards those requests to `MOTOR_URL`. A new page receives a new client session. The page displays server errors, discards expired leases, and requests stop when hidden or closed. Those browser requests are best-effort; command expiration is enforced independently by the motor service.

| Camera/web route | Purpose |
|---|---|
| `/` | Browser video and manual controls. |
| `/stream.mjpg` | MJPEG display stream. |
| `/snapshot.jpg` | One JPEG with capture timestamp, boot identity, camera session, and frame sequence headers. |
| `/status` | Camera readiness and frame sequence. |
| `/motor/cmd` | Same-origin JSON command proxy. |
| `/motor/status` | Same-origin motor status proxy. |
| `/overlay.mjpg` | Proxy to the optional AI overlay service. |

One capture worker keeps the latest frame in memory; HTTP handlers do not perform camera reads. Failed capture clears the cached frame and triggers reconnection. The MJPEG display is separate from the bounded snapshot interface used by the policy process.

All services bind to loopback by default. The current HTTP services have no authentication or TLS. For access from another computer, use an explicitly configured protected connection such as an SSH tunnel; changing a bind address alone does not provide access control.

## Optional AI observation and overlay

The policy process asks the model to report whether a person and a stop sign are present. A valid response looks like:

```json
{"person":{"present":false},"stop_sign":{"present":false}}
```

The parser requires actual JSON booleans. A present person also needs `distance` set to `near`, `mid`, or `far`. A detected stop sign or a near/mid person requests a latched stop. Invalid responses, unavailable camera/model data, and stale observations also request stop. A valid result without these detections produces `action: none`; it never authorizes movement or clears an earlier stop. The overlay shows the advisory action and recommendation.

The process uses `FRAME_URL`, not the display MJPEG stream. Snapshots must come from a literal loopback IP on the same Linux host and carry the matching boot identity. The acquisition timestamp is checked before and after inference against a 2-second age limit. This timestamp marks the start of the OpenCV read, not verified sensor exposure time; camera buffering remains a separate integration concern. Unmodified macOS snapshots lack the required Linux boot identity and are rejected by the policy.

For an intentional live camera/model run, first supply `OPENAI_API_KEY` through your shell environment, then start:

```sh
MOTOR_URL=http://127.0.0.1:8088 \
FRAME_URL=http://127.0.0.1:8090/snapshot.jpg \
AI_MODEL=gpt-4o-mini AI_PERIOD=2.0 POLICY_PORT=8091 \
  python -m pi_robot.vision_policy_daemon --enable-paid-model
```

The flag explicitly enables camera requests and paid model calls. Without it, the script exits before that work. The model name above is the code default, not a claim about account availability. Model calls have a 5-second timeout and no SDK retries, but a result older than the 2-second acquisition budget is still rejected.

View the overlay at `http://127.0.0.1:8091/overlay.mjpg` or expand the overlay panel in the camera page. The camera and model processes do not form an autonomous navigation system. A stop request is not a measurement that the wheels stopped. The full parser, acquisition, and client behavior is documented in [vision integration](../docs/vision_safety_integration.md).

## Motor API

Use `POST /cmd` with an `application/json` body for new clients. `GET /status` returns the current state. Legacy `GET /cmd?...` remains supported, but query strings can expose leases in URL logs and history.

The command sequence is reset if latched, arm to obtain a lease, then motion with that lease. This complete example uses Flask's in-process client and the mock backend; it opens no listening socket:

```python
import uuid
from pi_robot.web_motor import create_app

client = create_app().test_client()
identity = {"source": "manual", "session": str(uuid.uuid4())}

client.post("/cmd", json={"c": "reset", **identity})
armed = client.post("/cmd", json={"c": "arm", **identity}).get_json()
assert armed["ok"]
reply = client.post("/cmd", json={
    "c": "fwd", **identity, "lease": armed["lease"],
    "speed": 25, "duration": 0.20,
}).get_json()
assert reply["ok"] and reply["physical_actuation_enabled"] is False
client.post("/cmd", json={"c": "stop"})
```

Motion accepts speed from 0–100% and duration greater than zero through 1 second; the defaults are 50% and 0.25 seconds. Only one source/session owns the controller at a time. An expired or revoked lease cannot be reused. Any source may stop, including the AI source; AI cannot reset, arm, set speed, or move.

Responses include state, owner, commanded outputs, expiry, latch reason, and `backend: "mock"`. These fields describe software state, not measured voltage, current, or wheel motion. Session and lease fields coordinate clients; they do not authenticate users. See the [complete motor API contract](../hardware/rev_a/docs/software_safety_api.md) for validation rules, error codes, reversal handling, and shutdown behavior.

## Configuration reference

| Variable | Default | Used by |
|---|---|---|
| `MOTOR_BACKEND` | `mock` | Motor launcher; other values are rejected. |
| `PORT` | `8088` for motor; `8090` for camera | Respective service launcher. Set it per process. |
| `MOTOR_URL` | `http://127.0.0.1:8088` | Camera proxy, CLI, and policy. |
| `CAM_W`, `CAM_H`, `CAM_FPS` | `320`, `240`, `15` | Camera capture requests. |
| `BIND_HOST` | `127.0.0.1` | Camera and policy launchers; motor remains loopback. |
| `FRAME_URL` | `http://127.0.0.1:8090/snapshot.jpg` | Policy snapshot source. |
| `OVERLAY_URL` | `http://127.0.0.1:8091/overlay.mjpg` | Camera service's overlay proxy. |
| `POLICY_PORT` | `8091` | Policy overlay server. |
| `AI_MODEL` | `gpt-4o-mini` | Model name passed by the policy. |
| `AI_PERIOD` | `2.0` | Wait between policy cycles in seconds, in addition to each cycle's processing time. |
| `OPENAI_API_KEY` | No project default | SDK credential for explicitly enabled model calls. |

## Voice work and next integration steps

Earlier robot experiments included a USB microphone and speaker, wake words, speech-to-text, text-to-speech, and an OpenAI Realtime connection. This repository currently keeps the typed controller and shared command interface; the full speech pipeline is not included. A future voice client can use that interface while leaving ownership, command expiration, and stop handling in the motor controller.

The next physical integration work is to reconcile the installed GPIO map and power wiring, implement the selected board's backend and enable handshake, and measure actual PWM, motor current, reversal, and fault behavior. Camera buffering and end-to-end observation latency also need measurement before expanding the AI's role. These tasks build on the existing camera/control project and the [12 V board design](../hardware/rev_a/README.md).
