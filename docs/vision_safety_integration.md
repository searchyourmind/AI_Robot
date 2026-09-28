# Vision and manual-client integration: Rev A draft

Status: software changes verified with injected mock dependencies only. No camera,
OpenAI service, network socket, GPIO, or real motor was exercised by these tests.
This implementation is an advisory prototype; it does not establish collision
avoidance or a safety-rated stop function.

## Existing code and narrow changes

At baseline commit `034882cb2ce8106982508cf1a8309b4fa69673ff`:

| Source | Confirmed in code | Change in this draft |
|---|---|---|
| `vision_policy_daemon.py:parse_policy` | Searching for `stop_sign` also matched the key when its Boolean value was false. Other string matches could produce automatic `speed` and `fwd` requests. | Strict nested JSON Boolean parsing in `vision_safety.py`; true stop signs or near/mid persons request stop. No valid result grants motion. |
| `vision_policy_daemon.py:get_frame_from_stream` | Unbounded MJPEG accumulation, no capture provenance or model-result expiry. | One bounded snapshot with provenance; same-host boot identity and acquisition-age checks before and after inference. |
| `vision_policy_daemon.py` module scope | Constructed an OpenAI client at import. | SDK import and client creation only inside an explicitly invoked model function; injected fake model supported. |
| `web_vision_drive_picam_ai.py` module scope | Opened camera device zero at import. | One lazy capture worker, latest-frame cache, explicit startup, injected camera supported. |
| `web_vision_drive_picam_ai.py` browser script | Direct requests to the configured motor origin; no visible backend errors, ownership, arming, or disconnect stop. | Same-origin proxy; explicit reset/arm; source/session/lease; errors displayed; best-effort stop on hiding/leaving page. |
| `voice_ai_motor_simple.py` module scope | Input/network loop ran on import, with no timeouts or quit-stop. | Explicit `main`, bounded HTTP idle timeouts, lease handling, stop on quit/EOF/interrupt/errors. |

The camera `/stream.mjpg`, drive buttons, speed selection, AI model integration,
and `/overlay.mjpg` remain available. The overlay includes an advisory action and
recommendation. Python/OpenCV errors and failed stop delivery are reported; a stop
request must not be presented as proof that physical motion stopped.

## AI authority and parser contract

The expected model result is a JSON object containing both objects:

```json
{"person":{"present":false},"stop_sign":{"present":false}}
```

Both `present` values must be actual JSON booleans. Strings, integers, missing
objects/flags, duplicate fields, nonstandard JSON numbers, non-JSON text, and
oversized responses produce an invalid result and request stop. A present person
requires `distance` equal to `near`, `mid`, or `far`; any supplied distance must
also use one of these values. Markdown fences are not silently repaired.

The example above is valid and produces `action: none`; the `stop_sign` key alone
does not detect a sign. This means only that this result reported no selected
hazard. It does not mean the scene is clear. A far person likewise grants no
movement. A true stop-sign detection or a near/mid person yields `action: stop`.
The original "slow" advice remains visible as a recommendation for a close
person, but this daemon does not issue speed or direction changes.

`apply_policy` can send only `POST /cmd` with `c: stop`, `source: ai`, and a process
session. It cannot reset, arm, obtain a lease, set speed, or move. Invalid/missing
camera or model data and stale results request the same latched stop. A valid
negative detection does not clear a previous stop. A person must reassess and
explicitly reset/arm through a manual client. No AI heartbeat or status read
renews a movement command. Physical disable remains outside this advisory logic.

A cloud request can be slow or unavailable, and this daemon can crash. Manual
movement uses the motor service's short deadlines regardless of AI availability.
The daemon is not a reliable obstacle detector or a hardware watchdog.

## Provenance and bounded acquisition

The display MJPEG stream is no longer the policy input. The policy uses
`FRAME_URL`, default `http://127.0.0.1:8090/snapshot.jpg`, and requires:

| Header | Meaning |
|---|---|
| `X-Capture-Monotonic` | Camera worker's monotonic timestamp immediately **before** the OpenCV `read` call. |
| `X-Capture-Boot-ID` | Linux `/proc/sys/kernel/random/boot_id`, shared by producer and consumer on the same host. |
| `X-Camera-Session` | Random producer session; changes after capture reconnection. |
| `X-Frame-Sequence` | Increasing sequence within the producer session. |
| `Content-Length` | Required JPEG body size, at most 1 MiB. |

The immutable observation retains the original timestamp through encoding,
transport, and model inference. Both pre-inference and post-inference checks
reject age greater than 2 seconds, future timestamps, invalid numbers, absent
identity, or a different/unavailable boot ID. Arrival time never replaces the
acquisition timestamp. Re-reading a cached frame does not renew its age.

**Acquisition start is not verified sensor exposure time.** OpenCV/device/driver
buffers may contain older images. Requesting buffer size 1 is best-effort and is
not proof of a bound. This is an explicit remaining limitation; no observation,
even one passing the software age checks, authorizes motion. Future autonomous
motion would require a validated sensor timestamp/clock mapping or a measured
conservative buffering bound and an independently reviewed safety architecture.

Snapshot HTTP requires a literal loopback IP and the matching Linux boot ID;
remote camera hosts and clock-domain assumptions are rejected. macOS lacks this
Linux boot-ID source: its unmodified camera snapshots fail policy validation;
tests inject a boot identity and clock. Display MJPEG can still show camera
frames without serving as evidence of validated observation age.

The camera HTTP handler reads only a cached frame, so a blocked device read does
not block snapshot handling. Snapshot fetch uses 0.5-second connection and read
idle timeouts, a 2-second total read deadline checked at each one-byte iteration,
no redirects, and a size bound. A blocked socket operation may extend the total
loop deadline by its remaining idle timeout. Literal local IPs avoid DNS waits.
Missing headers, multipart streams, overlength/truncated bodies, and stale
snapshots are rejected; the response is closed on success and failure. Display
MJPEG and overlay remain intentional long-lived streams, not policy buffers.

The model client has a 5-second timeout and no SDK retries. A result returning
after the 2-second acquisition-age budget is rejected. Those draft values are
conservative software limits, not measured camera or model performance claims.

## Manual API and client behavior

See `hardware/rev_a/docs/software_safety_api.md` for the authoritative motor
contract. The current motor service is mock-only until the exact GPIO/VCC wiring, polarity and electrical requirements are reviewed.
Direct Pi 5 control and the driver-to-wheel map are now user-confirmed. The clients still demonstrate real command paths
against its in-process Flask test client without opening network sockets.

1. A client creates a new random session on startup/reload. It does not restore
   an old lease after reconnect.
2. `reset` explicitly clears a latch while leaving the service disarmed.
3. `arm` explicitly acquires a lease for the client's source and session.
4. A direction command carries that lease and expires after 0.25 seconds in these
   clients. It is a short discrete movement command, not hold-to-drive behavior.
5. Expiry/stop revokes the lease and requires a new explicit reset/arm sequence.
   Changing speed or polling status does not extend motion.
6. The browser displays non-success responses, clears its lease, and requests
   stop after command errors. Hiding/leaving the page requests stop best-effort.
   A connection failure during an armed session also requests stop best-effort.
   Abrupt browser/process/network failure may prevent delivery; the independent
   motor command deadline remains necessary.
7. The CLI uses `source: voice` for compatibility with its filename, but is a
   manual text CLI. It stops best-effort on quit, EOF, Ctrl-C, and command errors.

The browser serves `/motor/cmd` and `/motor/status` proxies on its own origin;
users no longer need cross-origin access to a motor server at a browser-local
`127.0.0.1`. Proxy commands have a 4096-byte limit, reject duplicate JSON fields,
and force `source: browser`. This local prototype has no authentication/TLS and
must not be exposed to an untrusted network. All service scripts bind loopback
by default. Remote access needs an explicitly chosen protected access mechanism;
changing a bind address is deployment work, not part of these mock checks.

## Running and checking without actuation

Imports and tests do not instantiate a camera or OpenAI client. Run the suite
from the repository root with the installed test interpreter:

```sh
python -m pytest tests/hardware_mock/test_vision_policy.py tests/hardware_mock/test_clients_camera.py -q
```

The tests inject camera reads/encoding, monotonic time, frame bytes/headers,
HTTP responses, model output, and CLI input. They cover the false-detection
regression; invalid Boolean/structure cases; stop-only authority; stale frames
and late model completion; wrong-boot/future timestamps; bounded fetching and
response closure; import behavior; camera timestamp ordering; snapshot/MJPEG
routes; browser rejection paths; lease propagation; and CLI shutdown/error paths.
Browser JavaScript handlers are inspected as served HTML; real browser execution
and physical disconnect timing have not been validated by those unit tests.

Running `vision_policy_daemon.py` without flags exits before camera/model work.
Its `--enable-paid-model` flag is required for a user-authorized live camera/model
run; no such run was performed. Normal camera-script startup does open the camera,
so it is also excluded from this session's mock tests. The old README invocation
using `STREAM_URL` and automatic AI speed/forward commands describes the baseline,
not this draft's deliberately restricted authority. Use this document and the
software API documentation when reviewing the changed behavior.

## Remaining validation

Actual camera device/Pi 5 compatibility, sensor exposure/buffering age, dropped
frames, optical coverage, AI accuracy/latency, hardware interlock response,
physical wiring, motor stopping distance, and real browser disconnect behavior
remain NOT TESTED. There is no autonomous "go" mode in this draft. Enabling one
would be a new requirements and safety review, not a configuration toggle.
