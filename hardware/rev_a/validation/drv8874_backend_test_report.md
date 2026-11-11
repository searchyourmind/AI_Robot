# Rev A DRV8874 backend software verification

Date: 2026-11-11. Base revision: `5fd6036`.

The implementation targets the custom Rev A J6 interface, with four separate
DRV8874 bridges commanded as left/right pairs. It does not target the installed
TB6612 boards or four stand-alone DRV8874 breakout modules.

## Executed checks

Development host: macOS, Python 3.13.16, Flask 3.1.3, pytest 9.1.1. Dependencies
were installed in an isolated `.venv` from `tests/hardware_mock/requirements.txt`.
The original mock suite passed all 132 tests before the backend changes.

Final commands, run from the repository root:

```sh
.venv/bin/python -m pytest tests/hardware_mock tests/hardware_gpio -q
.venv/bin/python -m compileall -q pi_robot
git diff --check
```

Result: **225 passed in 0.19 s**; all three commands exited successfully.

The tests use fake clocks, GPIO providers, network transports, camera frames,
and model responses. Flask integration tests use its in-process test client.
The hardware test fixtures prevent importing real `lgpio` and opening network
connections. No real GPIO, motors, camera, or paid model service was operated.

## Behaviors checked

- Explicit backend/config selection, strict config parsing, inert module
  imports, correct Rev A channel identities, and cleanup on startup failure.
- RP1 label verification, ambiguous-chip rejection, RUN-first low startup,
  paired demands, side polarity, and equal forward/reverse duty magnitude.
- Heartbeat high/low intervals, startup qualification, delayed-pulse
  requalification, explicit ARM sequencing, and no heartbeat from HTTP polling.
- Full API-to-backend motion, PWM-zero reversal without an extra ARM edge,
  stop/expiry cancellation, stale-heartbeat faults, and owner/lease behavior.
- Reversal and uncertain-write recovery intervals measured from completed
  zero writes, including delayed calls and invalid completion clocks.
- Partial GPIO/PWM failures, persistent I/O fault state, cleanup after
  interruption, shutdown resource release, and readable failure status.

An independent code review found two timing defects: stale disarmed heartbeat
qualification after a delayed GPIO call, and holdoff measured before the zero
write completed. Both were corrected and covered by regression tests.

## Limits

Fake-clock delays verify the software's requested timing and ordering; they
are not measurements of Linux scheduling, `lgpio` PWM, or electrical waveforms.
Real Pi 5 library/device compatibility, GPIO levels under load, the assembled
PCB, power sequencing, motor polarity/current/temperature, braking and reversal,
and hardware watchdog/fault response remain **not physically tested**.

Rev A J6 has no enable or fault feedback. Successful GPIO calls cannot establish
physical readiness, motion, stopping, or fault clearance. The default startup
allowance, 1 kHz software PWM, and 100 ms reversal policy need bench evaluation.

See the [backend setup and bench guide](../../../pi_robot/DRV8874_REVA.md) and
[offline test guide](../../../tests/hardware_gpio/README.md).
