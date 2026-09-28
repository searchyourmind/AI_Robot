# Offline motor/camera/AI tests

Run `python -m pytest tests/hardware_mock -q` from the repository root after
installing `requirements.txt` in a virtual environment. Session environment and
results are recorded in `hardware/rev_a/validation/software_test_report.md`.

The motor backend stores four output demands in memory; no GPIO provider is
imported. Fake clocks advance deterministically; the stop/motion race test uses
two synchronized Python threads. HTTP is represented by Flask test clients and
fake responses. Camera reads/encoding and model responses are injected. The
autouse socket guard fails accidental real connections.

The system integration tests connect the real Flask routes through in-memory
HTTP adapters. They cover browser arm/motion → camera snapshot → AI false/true
detections → latched stop, rejection of old leases after rearm, stale camera
rejection before model use, and nonrenewing status polling.

This suite is not a hardware-in-the-loop test, real browser execution, a real
camera/model accuracy evaluation, a GPIO waveform test or an electrical safety
certification. Mock durations and pin placeholders cannot authorize live motion.
