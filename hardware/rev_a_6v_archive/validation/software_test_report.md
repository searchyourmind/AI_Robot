# Session 1 verification record

Date: **2026-09-28 America/New_York**. Baseline: `034882cb2ce8106982508cf1a8309b4fa69673ff`; changes are uncommitted in the session's local clone. Host: macOS, Python 3.14.0. Interpreter: task-local `work/venv/bin/python`, outside this repository. Test dependencies: Flask 3.1.3, pytest 9.1.1, requests 2.34.2; complete installed-package snapshot in [test_environment.txt](test_environment.txt). This host also has NumPy installed; the test-only dependency file does not require it.

## Checks actually run

Commands below ran from the repository root unless stated otherwise. `../../work/venv/bin/python` is the exact relative interpreter path used in this checkout.

| ID | Command / method | Exit status | Actual result |
|---|---|---:|---|
| S01 | `git status --short --branch`; `git rev-parse HEAD`; `git log --oneline --all`; tracked file inventory | 0 | Initial checkout clean, main, all three original commits retained; no tracked instructions/CAD/tests |
| S02 | AST-extract baseline `parse_policy` from `git show 034882c:pi_robot/vision_policy_daemon.py`; execute only that pure function | 0 | Required false/false case incorrectly returned `stop`; [exact reproduction](baseline_parser_reproduction.json). No baseline module import/device initialization |
| S03 | `../../work/venv/bin/python -m pytest tests/hardware_mock -q --junitxml=hardware/rev_a/validation/mock_tests.junit.xml` | 0 | **132 passed in 0.26 s; 0 failed, 0 errors, 0 skipped** |
| S04 | `../../work/venv/bin/python -m compileall -q pi_robot tests/hardware_mock` | 0 | Python syntax compilation passed; compilation does not execute module startup |
| S05 | `git diff --check` | 0 | No whitespace errors in tracked changes |
| S06 | Python CSV parsing and blank-record assertions | 0 | Candidate BOM: 15 rows. Physical records: 17, all NOT TESTED; measured result/instrument/date/evidence fields blank |
| S07 | Relative Markdown link validation across current README/hardware/docs | 0 | Final check records no missing local targets; see [verification_checks.json](verification_checks.json) |
| S08 | `command -v kicad-cli`, Applications/PATH filename inspection | See CAD record | KiCad not available in inspected locations; no CAD checks attempted |

Machine-readable test output: [mock_tests.junit.xml](mock_tests.junit.xml). Tested Python input fingerprints: [software_input_hashes.json](software_input_hashes.json). The JUnit timestamp and package snapshot identify this actual test environment; they are not deployment claims.

Earlier targeted runs were used during implementation. The final combined run above supersedes their counts. A review found and fixed an uncertain-output recovery defect: a failed disable must not start the reversal holdoff. Added tests ensure the first successful disable after uncertainty starts a new wait, including partial-output-write failure where direction history is unavailable. A final error-response review also ensured failed disable returns HTTP 503/ok=false, rather than being mistaken by clients for successful stop delivery.

## What the 132 cases exercise

| Area | Cases | Evidence scope |
|---|---:|---|
| Motor state machine and Flask API | 70 | Four distinct outputs; default disarm; ownership/lease/reset/stop; malformed/duplicate/oversized/nonfinite inputs; expiry; reversal and uncertain-write recovery; stop/motion race; shutdown |
| Vision, camera, browser proxy and CLI | 58 | Structured Boolean parsing, missing/malformed/duplicate JSON, false/false regression; snapshot size/time/boot checks; stale post-inference result; mocked capture order; stop-only AI; safe imports; browser proxy limits; CLI errors/quit-stop |
| Cross-service integration | 4 | Browser→motor and camera→AI→stop using real Flask routes with in-memory HTTP adapters; revoked leases; stale snapshot blocked before model use; status polling cannot extend motion; failed backend disable propagates through AI stop delivery as an error |

Time is injected; no live sleep is needed for command expiry. One concurrency test uses synchronized Python threads and checks the stop/motion ordering invariant. Camera frames/encoding, HTTP responses, model clients/results and CLI input are mocked. Flask test clients do not listen on TCP ports. An autouse socket guard rejects accidental real connections. Source imports do not initialize GPIO, OpenCV camera capture or an OpenAI client.

## Not run or not established

- No live motor commands, physical GPIO, actual Raspberry Pi 5 service, camera device, model request or paid API call.
- No browser JavaScript execution in a real browser; HTML/proxy behavior and lease transport were tested, actual browser disconnect timing remains unverified.
- No real network deployment, authentication validation, Linux scheduler/peripheral timing or process/OS-hang protection test.
- No installed target `RPi.GPIO` provider identification, real PWM frequency/jitter, encoder, supply, current, thermal, back-power, physical disable or stopping-distance measurements.
- No native CAD files; ERC/DRC, schematic–PCB consistency, unconnected-net checks, schematic/layout PDF visual QA and manufacturing output verification are **NOT RUN**, not passed.
- No fabricated/assembled Rev A or manufacturing release. All physical tests remain NOT TESTED.

Mock success demonstrates the named software cases only. It cannot qualify TB6612FNG ratings, prove real GPIO behavior, replace hardware watchdogs or establish that a robot can move safely.
