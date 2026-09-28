# Mock motor control and API contract

Status: IMPLEMENTED AND MOCK TESTED. The user confirmed the direct Pi 5
controller path and four driver-channel identities. Actual GPIO assignments,
polarity, installed GPIO provider, and electrical behavior remain unverified.
This change is a safe software integration scaffold for the existing robot.

## Scope and architecture

The original `web_motor.py` drove two logical groups directly through seven
BCM-numbered signals with `RPi.GPIO`. That code did not identify four separate
motor/driver channels or establish whether the installed robot has an
intermediate controller. The user subsequently confirmed direct Raspberry Pi 5
GPIO control of both TB6612 boards with no Arduino in the control loop. This
revision supplies **only a mock backend** and invents no four-channel BCM pins.

`motor_config.py` explicitly lists four distinct outputs (`motor_1` through
`motor_4`). User-confirmed metadata maps motor_1 to front-left, Board A channel A;
motor_2 to back-left, Board B channel A; motor_3 to front-right, Board A channel B;
and motor_4 to back-right, Board B channel B. The controller field records
`raspberry_pi_5_direct_gpio`. Control pins and polarity remain `None` (TBD).
`simulation_side` exercises the corresponding paired left/right commands;
this mapping is user-confirmed, not measured or physically tested. No H-bridge
outputs are combined. The injected backend receives all four independent
signed duty demands on each write. The same interface can later accept a
verified map without changing the browser command vocabulary; a physical
backend is deliberately absent pending review.

`motor_control.py` owns the state machine, clock, lock, parsing, expiry, output
writes, and owner lease. `motor_backend.py` defines the injectable boundary and
an in-memory `MockBackend`. `web_motor.py` supplies `/cmd`, `/status`, and the
software ticker. Importing these modules initializes an in-memory disabled mock;
it opens no GPIO, camera, network socket, or model connection and starts no
thread. `create_app(controller)` supports in-process testing.

Use the supported development launcher from the repository root:

```sh
python -m pi_robot.web_motor
```

It binds `127.0.0.1:8088`, enables the software ticker, disables the Flask
reloader, and attempts disable on normal shutdown, KeyboardInterrupt, and
SIGTERM. `PORT` may select another local port. Any `MOTOR_BACKEND` other than
`mock` is rejected. The Flask development server is a mock test tool, not a
production actuator deployment. A bare WSGI import or `flask run` does not
start the ticker and is **not a supported actuator launcher**; injected tests
advance the clock and call `tick()` explicitly. Do not add multiple independent
WSGI workers to a physical controller: state and ownership would diverge.

## State and output rules

- Startup: disarmed, disabled; neither import nor arm commands motion.
- Explicit `arm` requires an unlatched, disarmed controller and a fresh client
  session. It returns a new random lease and starts a 1.0 s idle deadline.
- Motion requires the exact source, session, and lease. One owner at a time;
  another browser/voice/manual session cannot steal ownership.
- Every motion demand is a finite pulse: default 0.25 s, maximum 1.0 s. There
  is no indefinite forward/back/turn command. Expiry disarms, revokes the
  lease, disables outputs, cancels pending demands, and latches a stop.
- `stop` is accepted from any source, including AI and obsolete sessions. It
  takes the lock before any pending reversal can be applied, disables all
  outputs, revokes the lease, and latches. A completed stop prevents a queued
  old-lease motion request from re-enabling outputs.
- `reset` clears the latch only while disarmed and after the mock disable call
  succeeds. It leaves the controller disarmed. A separate `arm` is required.
  Source `ai` is prohibited from reset, arm, speed, and motion.
- Invalid command syntax/numbers fail closed into a fault. Wrong owner/lease,
  attempts while disarmed, and prohibited AI motion are rejected without
  refreshing expiry or changing the legitimate demand. A fault must be
  explicitly reset; the next valid movement never clears it implicitly.
- Backend write errors attempt disable and latch a fault. Failed disable
  reports `disable_confirmed=false`; the program cannot claim the hardware
  has stopped. A stop request whose disable fails returns HTTP 503 and
  `ok=false`, while remaining latched and disarmed with uncertain outputs.
  Shutdown cancels pending work and permanently rejects rearm.
- All authorization, expiry, state transitions, and writes share one lock.
  Pulse handlers never sleep. A backend call must be short and bounded;
  a blocking backend would still delay a stop and needs separate mitigation.

In the retained mock/legacy backend contract, "disabled" means zero PWM
demands and **STBY false for both drivers**, not short braking. This is a
software abstraction, not the new DRV8874 board's physical handshake or telemetry.
For the historical TB6612FNG interface, STBY low selects
high-impedance outputs (standby). Software stop cannot guarantee zero wheel
speed or remove motor supply energy. This is distinct from physical motor
power interruption. The original 0/0/PWM0/STBY1 combination is not used as a
claimed, verified brake/coast state. See the Toshiba TB6612FNG truth table,
page 4, in [the original manufacturer datasheet](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660)
and the version/section record in [design_sources.md](design_sources.md).

Reversal first disables all four mock outputs, then queues the replacement
until at least **100 ms** after any reversing channel was successfully disabled. An expired
pulse or stop cancels that queue. Stop/reset/arm does not erase direction
history to bypass the holdoff. A failed disable does not start the holdoff.
After any uncertain partial write/failed disable, a successful disable starts
a fresh 100 ms holdoff for every channel, including a channel whose direction
was never recorded. This interval is **PROPOSED for simulation**;
it is not a motor-current decay calculation, datasheet dead time, proven
safe braking policy, or assurance against regeneration. Actual reversal
behavior requires motor/load/supply and driver review, followed by controlled
measurement. The driver provides its own internal switching behavior; Python
is not controlling transistor-level dead time.

## API

Preferred interface: `POST /cmd` with `Content-Type: application/json` and an
object. Legacy `GET /cmd?...` remains for the existing command names. Use POST
for new clients; query strings expose leases to URL logs/history. Duplicate
JSON/query fields, unknown fields, malformed objects, and payloads over 4096
bytes are rejected. Do not issue live robot commands from tests.

| Field | Contract |
|---|---|
| `c` | `reset`, `arm`, `stop`, `fwd`, `back`, `left`, `right`, `pulse_fwd`, `speed` |
| `source` | `manual`, `browser`, or `voice` for reset/arm/motion; any source may stop |
| `session` | New random identifier per client page/process connection, 8–128 ASCII letters/digits/underscore/hyphen |
| `lease` | Random 32-character token returned only by successful arm; required for speed and motion |
| `speed` | Finite numeric percent from 0 through 100; default 50 or last configured speed |
| `duration` | Finite seconds strictly greater than 0 and at most 1.0; default 0.25 |
| `v` | Legacy alias: speed value for `c=speed`, pulse duration for `c=pulse_fwd` |

JSON Booleans are not numbers. NaN, infinity, overflow, out-of-range values,
blank/whitespace numeric strings, and nonnumeric strings are rejected rather
than silently clamped. `speed` accepts exactly one of `speed` or `v`; pulses
accept `duration` or legacy `v`, never both. A speed change affects the next
motion demand; it neither changes an already running demand nor renews its
deadline. `speed=0` disables outputs while the command still expires normally.

Example request sequence for an in-process mock client (tokens are responses,
not preconfigured credentials):

```python
identity = {"source": "manual", "session": "new_random_session_id"}
client.post("/cmd", json={"c": "reset", **identity})
reply = client.post("/cmd", json={"c": "arm", **identity}).get_json()
client.post("/cmd", json={"c": "fwd", **identity, "lease": reply["lease"],
                         "speed": 25, "duration": 0.20})
client.post("/cmd", json={"c": "stop"})
```

A successful response includes `ok`, `cmd`, `state`, `armed`, `latched`,
`reason`, `speed`, `outputs`, `standby`, `disable_confirmed`, `outputs_uncertain`, `owner`,
`expires_in_s`, `pending_reversal`, `backend="mock"`, and
`physical_actuation_enabled=false`. Only arm includes `lease`. `/status`
returns the same snapshot without a lease. Output/standby values are
**commanded states**, never hardware telemetry. `disable_confirmed` currently
means the in-memory disable operation succeeded, not measured power removal.
Errors return `ok=false`, an explanatory `error`, and HTTP 400 (invalid input),
403 (prohibited source), 409 (state/owner conflict), 413 (oversize), or 503
(backend failure). The HTTP error handler may return a shorter error object.

Session/source/lease establish software ownership and prevent stale requests
after rearm. They are **not user authentication, authorization for untrusted
networks, or a security boundary against a client that lies about its source**.
AI inhibit-only is enforced for the AI source and in the supplied clients;
an untrusted process with network access can impersonate a manual source.
Keep this mock service local. A reviewed deployment would need real access
controls and a single trusted arbiter in addition to electrical protection.

## Reconnection, AI, and remaining failure cases

A new browser page or CLI process creates a new session; do not persist or
recover an old lease. Request stop, then explicitly reset and arm when the
operator chooses to resume. Network recovery, camera recovery, an AI "go",
or model heartbeats never arm the controller. The AI daemon may only inhibit
with stop. A valid false/false AI detection is not evidence that motion is
safe. AI structure and capture-time freshness are enforced in the vision
policy layer and tested separately.

The ticker services expiry every 20 ms in the supported mock launcher. A
service gap greater than 150 ms while armed latches a software-watchdog fault
**when Python next runs**. Status/command processing also checks expiry but
never renews it. These are provisional scheduling constants, not real-time
limits. If the process/OS stalls, a backend blocks, the Pi loses power, GPIO
retains a level, or SIGKILL bypasses cleanup, Python cannot call disable at
the desired deadline. A ticker in the same process is not an independent
hardware watchdog. A request delayed before server receipt can still be
accepted within a currently valid owner lease; transport delay is not a
motor observation timestamp.

The reported prototype uses direct Pi 5 control, but its installed battery graph and both module GPIO/VCC mappings remain unresolved. The earlier one-battery/two-VM account is historical and must be reconciled with two purchased packs. The mock backend's `standby`/STBY terminology is a retained software abstraction; it is not new-board nSLEEP/SHDN telemetry and does not implement its handshake.

The proposed 12 V board already contains an independent TPS3431 watchdog, arm latch, command gates and physical feed/sleep inhibition. A real backend must implement its PWM/DIR plus RUN/ARM/heartbeat contract, including deliberate re-arming and no automatic motion restart. See [enable_interface_spec.md](enable_interface_spec.md) and [pin_map.md](pin_map.md). No physical GPIO backend is enabled. The Pi retains a separate supply and a common signal ground under the reference design; real power sequencing, return paths and fault responses remain untested. Physical inhibit is not a certified emergency stop, and VM stored energy remains after feed shutdown. Software mocks do not qualify this circuit.

## Verification recorded in this session

Executed with Python 3.14.0, Flask 3.1.3, and pytest 9.1.1 in the task's isolated
`work/venv` on the development host:

```sh
python -m pytest tests/hardware_mock/test_motor_control.py tests/hardware_mock/test_motor_api.py -q
```

Initial run: **65 passed in 0.17 s**, exit 0. After independent review and
uncertain-output recovery regressions: **69 passed in 0.19 s**, exit 0. Final
motor-only rerun with the stop-failure HTTP regression: **70 passed in 0.19 s**,
exit 0. See
[`software_test_report.md`](../validation/software_test_report.md) for
the final rerun and complete verification record. Tests use an injected
monotonic fake clock, in-memory outputs, threads synchronized with a barrier,
and Flask's in-process HTTP client; no listening socket, Pi, physical GPIO,
camera, HTTP service, or paid model was invoked by this suite. Covered: four
separate channels, disarmed startup, numeric bounds and malformed input,
latched stop/reset, source/session/lease arbitration, reconnect token
revocation, command and arm expiry, nonrenewing status/speed, reversal timing
and cancellation, stop/motion race, backend failure, and final shutdown.

NOT TESTED: electrical outputs, installed Pi GPIO provider, PWM timing or
Pi 5 compatibility, driver behavior, real emergency disable, physical
four-channel Pi pin mapping, motor current/temperature, operating system freezes,
network deployment, hardware assembly, or robot motion.
