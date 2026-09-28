# 12 V redesign — deferred physical validation plan

**NOT EXECUTED / NOT TESTED.** This document is a future test plan, not a record of completed work or authorization to operate hardware. Fabrication: **DEFERRED / NOT BUILT**. Assembly: **DEFERRED / NOT ASSEMBLED**. Physical validation and robot integration: **NOT TESTED**. No hardware, camera, network model or live GPIO was operated to produce this plan.

This plan applies to the new four-DRV8874 design with a provisional 9–15 V source and 100×100 mm PCB. The [archived 6 V plan](../../rev_a_6v_archive/validation/bring_up.md) is historical and does not apply. The new [physical_test_records.csv](physical_test_records.csv) contains 22 planned cases, each marked **NOT EXECUTED**. All measured-result, instrument, date, pass/fail, evidence, serial, software-version, operator and uncertainty fields are intentionally blank. Planned expected results are criteria, not observations.

The authority for limits is the [reference electrical specification](../docs/reference_electrical_spec.md), [power circuit](../docs/power_circuit_spec.md), [power-path review](../docs/power_path_review_12v.md), [driver review](../docs/driver_margin_review.md) and [enable interface](../docs/enable_interface_spec.md). Actual motor model, source voltage extrema, two-pack connection graph, BMS behavior, current/torque requirements and GPIO wiring remain unresolved. Purchase descriptions do not qualify this setup.

## Gates before any later powered work

1. Confirm actual parts, source and motor limits; approve a bounded fixture, instruments, probe references, energy/current limits and abort criteria. Source/probe settings must follow actual ratings and the reviewed test case, not be inferred from a blank template. No uncontrolled stall, deliberate battery short, reversed live wiring or arbitrary power disconnection under load is part of this plan.
2. Complete native CAD/parity review, BOM/orientation checks, assembly inspection and fabricator process confirmation. TPS26630 holes under paste require filled, capped and planarized construction. DRV heat vias are tented outside paste. An ERC/DRC pass does not establish assembly quality or thermal performance.
3. Identify board revision/serial, motor and source models, installed harness endpoints, fixture version and measurement uncertainty. Keep motors and Pi disconnected for initial bench qualification. A standalone approved logic fixture must not be paralleled with the Pi's 3.3 V rail.
4. Obtain explicit authorization for the future live setup. Use a supported, bounded mechanical fixture before any wheel actuation. An unexpected rail/current/temperature, incorrect polarity, lost control or unresolved measurement pauses progression; no failure is converted into a pass by assumption.
5. The existing software backend is **MOCK ONLY**. Hardware-handshake and live integration cases require a separately implemented and reviewed GPIO backend or controlled fixture. The preserved 132 mock tests do not meet these prerequisites.

## Reference cases and acceptance boundaries

| Quantity | Design reference for future comparison | Limit of the claim |
| --- | --- | --- |
| Normal source / logic | J1 9–15 V; PI_3V3 3.2–3.4 V | Not measured pack or Pi limits; no assumed 3S chemistry |
| Normal total input | ≤2.0 A including board overhead | Separate from overload limiting; not four independent 1 A allocations |
| Per-motor regulation | 0.791 A nominal; 0.708–0.888 A static screen | Dynamic peaks, starting torque and motor heating require evidence |
| Aggregate eFuse limit | 2.980 A nominal; 2.656–3.311 A static screen | Not an instantaneous hard ceiling; overload mode is latch-off |
| Cold startup | Approx. 0.686 s nominal ramp at 15 V; cap-only 0.101/0.126 A screens; about 0.18 A total input screen | Includes awake drivers, bleed and eFuse overhead; calculated estimates, not guaranteed source settings |
| Warm recovery | Retained VM above PGTH falling threshold may select fast recovery | The cold dV/dt/current screen cannot be reused as a universal bound |
| Transients | VM ≤32 V; upstream protected path ≤45 V | Must include ringing, probe uncertainty, pulse current and temperature |
| Regeneration | Initial VM ≤15 V; ≤0.1 J total/event, ≤0.1 Hz; rail recovered before next event | No continuous back-driving; actual robot braking energy unknown |
| Thermal | Ambient ≤40 °C; driver junction target <125 °C | Board copper/adjacent heating and junction-estimation method need validation |
| Discharge | Remove source and mechanical input; wait ≥15 s **and measure VM <0.3 V** | Time alone cannot establish a discharged rail |

The 2.88 mF nominal electrolytic storage has a 2304 µF initial minimum screen. At that capacitance, 0.1 J returned from 15 V reaches about 17.658 V, leaving only about 4.4 mJ to the conservative 17.766 V VM-overvoltage threshold. Effective capacitance over temperature and service life, actual energy and waveform overshoot must be checked separately. An early monitor trip may inhibit motion; a monitor is not an energy absorber.

## Startup, stop and recovery behavior to distinguish

Initial qualification uses an approved logic source, PWM/RUN/ARM low, no motors and physical INHIBIT. Physical enable allows `FEED_ENABLE = LOGIC_GOOD AND PHYS_OK` to raise driver nSLEEP and eFuse SHDN. **The drivers wake before ARM and during the motor-rail ramp.** U3 holds each bridge's inputs at 00/coast while the arm permission is cleared. A normal wake fault, rail qualification or supply recovery must not be interpreted as an ARM request.

Only after supply/fault qualification and the reviewed initialization/heartbeat sequence may a later authorized fixture present a fresh explicit ARM edge. The proposed firmware contract includes falling heartbeat edges no more than 50 ms apart, at least 1 s and three valid cycles before operator ARM, and no automatic retry after a rejected ARM. The harness carries no ALL_OK feedback to the Pi; the software cannot claim to have observed a clearance that it cannot sense. Hardware observation is required for the planned validation.

| State | Expected command/power behavior |
| --- | --- |
| RUN low, watchdog expiry or reported fault | Clear ARM and drive inputs 00/coast; drivers can remain awake with VM supplied |
| Armed PWM low | Inputs 11: electrical brake/slow decay; raising PWM can drive immediately |
| Armed PWM high, DIR low/high | Inputs 01 reverse / 10 forward; actual wheel polarity is not yet known |
| Physical INHIBIT | Clear ARM, inputs 00, lower nSLEEP and eFuse SHDN; retained VM is not instantly removed |
| Fault clears or physical enable returns | Supply/wake may recover; no automatic re-arm |
| Internal driver OCP latch | Deliberate sleep/wake or motor-power reset is needed, followed by fresh external ARM |

The watchdog's 170–230 ms timeout plus downstream propagation is an electrical response criterion, not a mechanical stopping guarantee. Current chopping itself need not assert nFAULT and does not provide a motor-specific stall timer. Keep PWM low for direction changes and use a later validated deceleration/reversal interval; no hardware reversal timer is present.

The eFuse's MODE-open overload latch, UV/OV recovery, physical SHDN reset and retained-VM fast-recovery cases must be distinguished. Record current peaks and rail/command behavior during recovery. Four simultaneous starts may fail or trip the aggregate limiter; **successful startup is not guaranteed**. Do not increase limits simply to hide a failed start.

For a later controlled shutdown, stop mechanical energy input, disarm, select physical INHIBIT and remove the source upstream. Before handling, wait at least **15 seconds** and establish **VM below 0.3 V**. An active source or back-driven motor invalidates passive decay estimates. The removable Phoenix connectors are not intended to act as energized switches. DRV8874's single-VM architecture removes the old TB6612 separate-VCC dependency, but arbitrary Pi collapse, broken ground and external signal faults remain unvalidated cases.

## Planned progression

The CSV is the detailed case-by-case template; no stage below has been executed.

| IDs | Planned scope | Evidence required before progression |
| --- | --- | --- |
| V01–V03 | Build/process review, unpowered connectivity, logic-only defaults | Identified assembled board, approved fixture and recorded inspection/connectivity/default results |
| V04–V06 | Cold awake-before-ARM ramp, rail qualification, physical inhibit | Captured power/current/command waveforms and retained-energy behavior with motors absent |
| V07–V12 | Truth table, watchdog, faults, eFuse/warm recovery, discharge and separately approved partial-power cases | No unexpected command, clear distinctions between feed/sleep/arm, documented reset behavior |
| V13–V16 | Harness/wheel identity, individual current regulation, torque/simultaneous starts, coast/brake/reversal | Approved motor identity and bounded mechanical load; electrical and mechanical results recorded separately |
| V17–V18 | Regeneration/transients and coupled thermal behavior | Bounded energy/load fixture, source behavior known, waveform bandwidth and uncertainty documented |
| V19 | Real software/handshake integration | Reviewed hardware backend; observed hardware response alongside protocol tests |
| V20 | Isolated vision/model failure cases | Classified as software/mock evidence; no physical-pass credit |
| V21 | Encoder/sensor interface boundary | Separate exact interface requirements; no acquisition interface fitted to this PCB |
| V22 | Mechanical/system acceptance | Actual mounting/harness fit and residual limitations recorded |

Keep raw waveforms, instrument settings, revision identifiers and measurement uncertainty with each real evidence record when future work is authorized. A missing instrument or an unapproved load case leaves its criterion unresolved. Failed or not-run cases must remain visible. A nominal 3D model, a calculated current screen or a software mock result must never fill a physical measurement field.
