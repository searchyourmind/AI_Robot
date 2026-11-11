# Motor control and API contract

Status: mock backend and opt-in Raspberry Pi 5 / Rev A DRV8874 GPIO backend
implemented, with offline verification. The Rev A board remains a design-stage
subsystem; electrical behavior and robot motion have not been bench-validated.
See the [hardware backend guide](../../../pi_robot/DRV8874_REVA.md) for setup,
configuration, signal mapping, and first bench checks.

## Scope and architecture

`motor_control.py` owns the state machine, clock, lock, parsing, expiry, output
writes, and owner lease. `motor_backend.py` defines the injected lifecycle and
in-memory `MockBackend`. `drv8874_backend.py` implements the new board's GPIO
contract. `web_motor.py` supplies `/cmd`, `/status`, and the controller ticker.

The historical mock metadata records the user-reported TB6612 arrangement:
`motor_1` front-left/Board A channel A; `motor_2` back-left/Board B channel A;
`motor_3` front-right/Board A channel B; and `motor_4` back-right/Board B channel B.
Its physical GPIO mapping remains unspecified. Rev A maps those same wheel
names to U20, U22, U21, and U23 respectively. Its four bridges have separate
power outputs but share left/right commands. The backend rejects unequal
front/rear demands within a side. It is not a backend for the installed TB6612
harness or four independent DRV8874 breakout modules.

The Rev A GPIO mapping is fixed by [pin_map.md](pin_map.md): BCM18/23 left
PWM/DIR, BCM13/5 right PWM/DIR, BCM25 RUN, BCM17 ARM, and BCM27 heartbeat.
Side polarity must be explicitly configured. `lgpio` discovers and verifies
the RP1 GPIO chip by label; motor PWM is software timed, with a default of
1 kHz. There are no fault, enable, ALL_OK, current, or encoder inputs on J6.

Importing the service initializes only an in-memory disabled mock; it opens
no GPIO, camera, network socket, or model connection and starts no thread.
`create_app(controller)` supports in-process testing. Use the supported
single-process launcher from the repository root:

```sh
MOTOR_BACKEND=mock python -m pi_robot.web_motor
```

Hardware mode additionally requires an explicit JSON configuration:

```sh
MOTOR_BACKEND=drv8874_reva MOTOR_CONFIG=/path/to/robot-motor.json \
  python -m pi_robot.web_motor
```

The launcher binds `127.0.0.1:8088`, starts the ticker, disables the Flask
reloader, and attempts disable/resource cleanup on normal shutdown,
KeyboardInterrupt, and SIGTERM. `PORT` may select another local port. An
unknown backend or invalid hardware configuration is rejected. A bare WSGI
import or `flask run` does not start the ticker and is not a supported hardware
launcher. Multiple motor-service workers would have conflicting ownership and
must not share one robot.

## State and output rules

- Startup is disarmed with RUN/PWM/ARM low. It sends no nonzero motor demand
  and does not create an ARM edge.
- Explicit `arm` requires an unlatched, disarmed controller and a fresh client
  session. In Rev A mode it additionally requires continuous software heartbeat
  qualification for `startup_settle_s + 1` seconds and at least three cycles.
  Early requests return 409; there is no automatic retry. An accepted request
  raises RUN, waits at least 1 ms, pulses ARM high for at least 1 ms, then lowers
  ARM. It returns a fresh lease and starts a one-second idle deadline.
- Motion requires the exact source, session, and lease. One owner holds control
  at a time; another browser/voice/manual session cannot steal ownership.
- Every motion demand expires: default duration is 0.25 s, maximum 1 s.
  Expiry disarms, revokes the lease, disables outputs, cancels pending demands,
  and latches stop.
- `stop` is accepted from any source, including AI and obsolete sessions. It
  takes the controller lock, disables outputs, revokes the lease, and latches.
  A completed stop prevents old-lease requests from restoring motion.
- `reset` clears the software latch only while disarmed and after a successful
  backend disable operation. It leaves the controller disarmed. It cannot
  establish hardware fault clearance or reset the DRV8874 internal OCP latch.
  Source `ai` cannot reset, arm, select speed, or request motion.
- Invalid command syntax/numbers latch a fault. Wrong owner/lease, requests
  while disarmed, and prohibited AI motion are rejected without extending
  expiry or changing a legitimate demand. A movement request never implicitly
  clears a fault.
- Backend errors attempt disable and latch a fault. Failed disable reports
  `disable_confirmed=false`, uncertain outputs, and HTTP 503 for stop. A Rev A
  GPIO I/O failure also latches the backend and requires service reinitialization.
  Shutdown cancels pending work, permanently rejects rearm, and releases GPIO.
- Authorization, expiry, state transitions, and writes share one lock. The
  reversal delay is queued rather than sleeping in a motion handler. GPIO
  heartbeat/ARM/direction sequencing has short settling waits; a stalled call
  can still delay software stop, so the board's independent watchdog remains
  part of the hardware contract.

For Rev A, **RUN low clears the ARM latch and requests coast**. It does not
remove VM power or necessarily put the drivers to sleep. An armed PWM-low
state requests brake through the board's decoder. Reversal and zero-speed
commands use that state while retaining RUN; calling full disable for a
reversal would destroy the latch and require a fresh deliberate ARM edge.
The backend never re-arms from `apply()`. Duty is the absolute demand for
both directions, after side-polarity selection.

Reversal first sets all demands to zero, then queues the new demand until the
configured `reversal_holdoff_s` has elapsed. The default 100 ms is a policy
value, not validated electrical dead time or a proven motor deceleration
period. PWM is held low before changing DIR, followed by logic settling.
Stop or expiry cancels queued reversal. Stop/reset/arm preserves direction
history. An uncertain partial write starts a fresh recovery holdoff only after
a successful full disable; a failed disable does not start it. Physical
braking, regeneration, current decay, and the suitable delay require testing
with the actual load and supply. Mock quiescence retains its zero-output
behavior and does not simulate physical braking torque.

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
deadline. `speed=0` requests zero demand while the command still expires
normally. In Rev A hardware mode this is an armed PWM-low brake request;
explicit stop lowers RUN and requests coast.

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
`expires_in_s`, `pending_reversal`, the selected `backend`, and
`physical_backend`. `physical_actuation_enabled` is false for mock and null
for Rev A because actual hardware enable is unobserved. Only arm includes
`lease`. `/status` returns the same snapshot without a lease. Output/standby
values are **commanded states**, never hardware telemetry. The nested
`hardware` object reports backend requests and software timing qualification.
`disable_confirmed` means the backend disable operation succeeded, not
measured power removal or physical stopping. An armed zero-demand brake
interval is different from full disable.
Errors return `ok=false`, an explanatory `error`, and HTTP 400 (invalid input),
403 (prohibited source), 409 (state/owner conflict or incomplete software ARM
qualification), 413 (oversize), or 503 (backend failure). The HTTP error handler
may return a shorter error object.

Session/source/lease establish software ownership and prevent stale requests
after rearm. They are **not user authentication, authorization for untrusted
networks, or a security boundary against a client that lies about its source**.
AI inhibit-only is enforced for the AI source and in the supplied clients;
an untrusted process with network access can impersonate a manual source.
Keep the service local. Deployment beyond trusted local clients requires
real access controls and a single motor arbiter in addition to electrical
protection.

## Reconnection, heartbeat, and physical-state limits

A new browser page or CLI process creates a new session; do not restore an old
lease. Request stop, then explicitly reset and arm when the operator chooses
to resume. Network recovery, camera recovery, an AI “go,” and model heartbeats
never arm the controller. The AI daemon may only inhibit with stop. A valid
negative detection does not establish that motion is safe.

The supported launcher ticks every 20 ms. The existing software service-gap
check faults after an armed gap greater than 150 ms when Python next runs.
The Rev A backend additionally requires heartbeat falling edges no more than
50 ms apart, with high/low intervals at least 1 ms. Only a healthy controller
tick emits heartbeat; HTTP commands/status cannot feed it. Heartbeat is not
produced by an independent timer or the `lgpio` PWM worker. A stale heartbeat
is checked before subsequent demands and pending reversal can be applied.

The TPS3431 watchdog independently clears the board's ARM latch 170–230 ms
after its last accepted falling edge, subject to the electrical conditions in
[enable_interface_spec.md](enable_interface_spec.md). That interval is not a
physical stopping-time guarantee. Linux scheduling, process stalls, blocking
GPIO calls, and abrupt termination can prevent Python from disabling outputs
on schedule. Recovered heartbeat alone does not re-arm the hardware.

The Pi cannot observe ALL_OK, a rejected ARM edge, actual enable, physical
switch changes, or motor faults through J6. Thus API `armed` and readiness are
software states only. Software qualification cannot know when physical enable
was last changed. After a power/physical-enable change, allow actual startup
to settle and the required heartbeat time before deliberate ARM, even if the
software timer already completed. The board rejects an unqualified ARM edge;
software must not retry automatically. Driver-internal OCP may require a
physical-enable/power cycle before the new ARM sequence.

`standby` remains a compatibility field for nonzero commanded demand; it is
not measured nSLEEP, drive permission, or STBY. GPIO disable success does not
prove physical stop or supply removal. The Pi has a separate supply and a
common signal reference under the reference design. The Rev A circuit,
power sequencing, return paths, and stopping behavior still need bench
qualification; offline tests cannot qualify them.

## Current offline verification

```sh
python -m pip install -r tests/hardware_mock/requirements.txt
python -m pytest tests/hardware_mock tests/hardware_gpio -q
```

The GPIO tests inject a fake provider and clock. They exercise initialization,
paired demand validation, direction/duty ordering, qualification, explicit ARM,
controller-only heartbeat, reversal/stop behavior, errors, and cleanup without
opening GPIO. They do not measure PWM jitter, current, physical braking,
watchdog propagation, or motor motion. The historical test record below
belongs to the earlier mock-only revision.

## Historical mock-only verification

The earlier mock-only revision was executed with Python 3.14.0, Flask 3.1.3, and pytest 9.1.1 in the task's isolated
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

Not tested by those historical runs: electrical outputs, installed Pi GPIO provider, PWM timing or
Pi 5 compatibility, driver behavior, real emergency disable, physical
four-channel Pi pin mapping, motor current/temperature, operating system freezes,
network deployment, hardware assembly, or robot motion.
