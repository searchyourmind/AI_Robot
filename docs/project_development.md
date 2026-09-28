# Project development

AI Robot combines a Raspberry Pi mobile platform, browser and terminal control, a live camera view, and an AI vision service. The software is organized around a motor API so that camera handling, user interfaces, and image interpretation can evolve separately from the motor driver. The custom motor-interface PCB extends that robot project by consolidating its power, motor, and control wiring.

## Robot platform and software architecture

The prototype uses a Raspberry Pi 5, four geared DC motors, two TB6612 dual-channel driver boards, a Pi camera, USB microphone, and speaker. It was assembled from two WHEELTEC R3 two-wheel kits. Each kit was sold with 12 V, 30:1, 500-line GMR encoder motors and a regulated dual-channel TB6612 driver. Board A serves the front-left and front-right motors; board B serves the back-left and back-right motors. The Pi directly controls the drivers and has a separate supply, with a common ground shared by Pi logic and motor power.

Four Python services provide the main project functions:

| Module | Role in the robot |
|---|---|
| `web_motor.py` | Flask motor API on port 8088; owns command state, arming, expiry, and the motor backend. |
| `web_vision_drive_picam_ai.py` | Camera acquisition, MJPEG display, timestamped JPEG snapshots, and browser controls on port 8090. Browser commands pass through a same-origin proxy to the motor API. |
| `vision_policy_daemon.py` | Requests camera observations, calls a vision model, interprets structured detections, and serves an annotated overlay on port 8091. |
| `voice_ai_motor_simple.py` | Manual terminal controller using the same motor API. The filename comes from earlier voice experiments; this version accepts text commands. |

This separation keeps one command owner while allowing multiple interfaces. The browser combines the live camera view, direction buttons, speed selection, reset/arm controls, status, and an optional AI overlay. The CLI provides the same basic manual control path without requiring a browser. Earlier work explored wake words, speech recognition, speech synthesis, and the Realtime API; the checked-in client is the simpler terminal interface.

The vision service identifies stop signs and people from camera images. The original policy translated model advice into stop, speed, and forward requests. The current implementation keeps the camera and model integration while restricting the model's command authority to stop. A negative detection cannot start movement or clear a previous stop. Camera acquisition, model inference, and motor command expiry remain separate responsibilities.

## Command and camera handling

The current motor backend is a mock implementation. Clients explicitly reset and arm, receive a control lease tied to their source and session, and submit commands with short deadlines. Browser and CLI direction commands expire after 0.25 seconds. Speed changes and status reads do not renew motion; expiry and stop revoke the lease. The CLI requests stop on quit, EOF, interrupt, or command error, while the browser also requests stop when its page is hidden or left.

The camera worker captures once and maintains a latest-frame cache for the display and snapshot endpoints. The vision service consumes one bounded JPEG snapshot rather than accumulating an MJPEG stream. Camera session, sequence, monotonic capture-start time, and Linux boot identity accompany each observation. Age is checked before and after inference, so a slow model response cannot make an old observation fresh. The acquisition timestamp precedes the OpenCV read call; it does not measure sensor exposure time or eliminate driver buffering.

A parser regression in the original policy could treat the text `stop_sign` as a detection even when its value was false. The revised parser requires actual JSON booleans, validates the nested structure and person distance, and rejects malformed or stale observations. Invalid observations request stop. The [vision integration guide](vision_safety_integration.md) documents this behavior and the current camera and client interfaces.

The offline test suite covers command ownership, state transitions, deadlines, parsing, observation age, camera routes, client errors, and shutdown handling. Both the retained test record and the later pre-publication rerun passed 132 mock cases. These tests use injected camera, model, HTTP, clock, and motor dependencies. The new PCB's RUN/ARM/heartbeat/PWM/DIR interface still needs a real GPIO backend and robot integration.

## From jumper wiring to a custom motor interface

The PCB work began to replace the prototype's jumper-wire motor, power, and control connections with a more serviceable board. Its first design used an agreed 6 V reference envelope while motor and battery details were incomplete. Purchase records later established the 12 V system family, which changed the design requirements.

The audit found that the first draft's 7 V TVS and roughly 7.16 V overvoltage window were incompatible with direct 12 V input. It also prompted a driver-current review. Public MG513P30_12V figures give approximately 0.36 A rated and 3.2 A stall current, but the installed motor label has not yet confirmed that exact model. Toshiba's 3.2 A TB6612 figure is a restricted single 10 ms absolute peak; its recommended VM maximum is 13.5 V. Those limits did not provide sufficient margin for the new reference envelope.

The correction happened before manufacture. The [revision history](../hardware/rev_a/docs/revision_history.md) and [6 V design archive](../hardware/rev_a_6v_archive/ARCHIVE_NOTICE.md) record the original assumptions and the change to the current 12 V-class design.

## The 12 V motor-interface design

The new board uses four DRV8874 bridges, one per motor. Each bridge has its own motor connector, current-limit network, and current-indication test point. Front and rear motors still share commands by side for differential drive, so there are four separate electrical outputs and two independently commanded sides. Bridge outputs are never paralleled. Encoder feedback and four independent wheel-speed commands are outside the current interface.

The design adopts a provisional 9–15 V motor-source envelope, a separately powered Pi, 3.2–3.4 V logic, and an ambient limit of 40°C. The per-channel current threshold is approximately 0.791 A nominal, with a calculated 0.708–0.888 A range. This limits winding current rather than trying to supply unrestricted candidate-motor stall current. Available starting torque remains a measurement task.

A TPS26630 eFuse, reverse-current FET stage, fuse, and transient suppressors protect the common motor input. The eFuse's nominal aggregate threshold is approximately 2.98 A, while the normal source-current assumption is at most 2 A. Four simultaneous motor starts can exceed the lower eFuse threshold and cause a protective trip. Battery current and winding current differ during PWM recirculation, so final settings depend on measured starts and loaded operation.

Two 1000 µF central capacitors and four 220 µF local capacitors provide 2.88 mF nominal, or 2.304 mF at the stated minimum tolerance. In the ideal energy calculation, returning 0.1 J to that minimum capacitance from 15 V raises VM to approximately 17.66 V. The capacitors are rated 50 V; the separate transient ceiling is 32 V. Local ceramics supply the fast switching loops, while charge-pump capacitors support the driver circuitry. The TVS pulse limits and returned-energy bounds remain part of the [power specification](../hardware/rev_a/docs/power_circuit_spec.md).

The Pi remains independently supplied to keep its CPU, camera, and startup load out of the motor regulator path. Common ground is still necessary for GPIO reference. Motor and bypass return currents use the board's power area; separate supplies do not remove ground impedance or switching noise.

## Permission, stopping, and restart behavior

The hardware separates driver wake-up from permission to drive. `FEED_ENABLE = LOGIC_GOOD AND PHYS_OK` wakes the drivers and allows the eFuse path to charge VM while the command gates hold both bridge inputs low. Power-good, fault state, RUN, and heartbeat then qualify a fresh ARM edge. This avoids allowing the DRV8874's normal wake-up fault pulse to put its own driver back to sleep through the arm loop.

The watchdog has a specified 170–230 ms timeout range; the proposed Pi interface supplies heartbeat edges at intervals no greater than 50 ms. Losing qualification clears the external arm latch. Restored power or heartbeat does not restart motion without a new ARM edge.

While armed, PWM-off intervals produce `11` at the driver inputs for braking/slow-decay recirculation. Disarming produces `00` for coast. Physical disable also asserts driver sleep and shuts off the eFuse feed independently of Python or HTTP progress. Stored capacitor energy and motor backdrive can remain after that action, so physical disable is distinct from electrical isolation. The [enable-interface specification](../hardware/rev_a/docs/enable_interface_spec.md) gives the signal-level behavior.

## Board layout and design checks

The board has seven schematic sheets and a 100 × 100 mm outline with two nominal 1 oz copper layers. The larger outline accommodates four driver stages, local bulk capacitors, connectors, and copper for heat spreading. The component inventory contains 121 fitted placements and 14 copper test points, plus four mounting holes. The [component review](../hardware/rev_a/docs/component_count_review.md) accounts for power protection, current regulation, logic qualification, bypassing, and connectors.

Main power trunks carry aggregate current; motor branches carry individual winding current; fine-pitch package escapes are shorter and narrower. Ground zones, vias, and short ceramic return loops complete those current paths. The [routing audit](../hardware/rev_a/docs/routing_rationale.md) records the actual widths and lengths. The thermal screen allows about 0.90 W per driver and targets an effective junction-to-ambient resistance no worse than 80°C/W. Local copper areas overlap, so area alone cannot establish temperature rise.

The saved design passed ERC, DRC, unconnected-net, and schematic-parity checks with zero findings. Independent checks reconciled 135 electrical entries, 434 logical pins, 459 physical numbered pads, and 15 intentional NCs across the manifest, native schematic, and board. The [check report](../hardware/rev_a/validation/design/design_check_report.md) records file identities, enabled checks, and results. PDFs, BOM, Gerbers, drill data, placement files, and KiCad 3D views accompany the editable design.

## Next integration work

The custom PCB is currently a completed CAD design awaiting fabrication and bench qualification. The remaining robot-specific work is to confirm motor labels and current waveforms; battery chemistry, voltage range, connections, and BMS behavior; the full GPIO harness and Pi supply; switch wiring; and chassis dimensions. Two packs sold as “12 V lithium” do not establish their topology or full-charge voltage.

Those measurements will determine whether the current-limit settings deliver enough starting torque, whether simultaneous starts trip the common input, and whether the layout meets thermal and mechanical requirements. The assembly process also needs confirmation for the 13 holes specified for selective filling, capping, and planarization. Software integration then connects the real GPIO backend to the existing motor API, followed by camera, control, and power-system testing on the robot.
