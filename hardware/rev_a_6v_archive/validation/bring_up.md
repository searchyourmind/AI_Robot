# Rev A staged bring-up procedure

**Current hold — 2026-09-28:** This remains an unperformed procedure for the 6 V reference. Do not use the purchased 12 V packs as its source. See the [12 V impact review](../docs/12v_design_impact.md). All physical work remains deferred.

**NOT EXECUTED / NOT TESTED.** Fabrication: **DEFERRED / NOT BUILT**. Assembly: **DEFERRED / NOT ASSEMBLED**. Integration with the proposed PCB: **NOT TESTED**. Use `physical_test_records.csv` for later results. Every row requires setup, expected result, measured result, instrument, date, pass/fail and evidence location. Measurements/dates/evidence remain blank until performed. The accepted reference envelope is documented in [reference_electrical_spec.md](../docs/reference_electrical_spec.md); it is not proof that the existing motors or battery meet it.

## Preconditions and authority

1. Architecture, source voltage/current, component ratings, fuse/connector/cable coordination and motor limits are approved. Native CAD, schematic-to-board checks, BOM, orientation and assembly inspection are complete.
2. Operator has explicit authorization for live actuation, required equipment and a rated accessible physical disable. Start with wheels off the surface and keep loose wiring/tools clear of moving parts.
3. Record board revision/serial, motor IDs, battery/supply model, software commit, Pi OS/GPIO provider, probe connections and instrument settings. Define current limits and temperature/voltage abort thresholds from actual ratings. Do not choose limits from this blank procedure.
4. A powered test stops on unexpected voltage/current/temperature, lost control, smell, damaged wiring or uncertain polarity. Investigate with power removed. Never deliberately short the supply, reverse polarity, or perform an uncontrolled stall.
5. The current motor backend is MOCK ONLY. Live motor tests require a separately implemented/reviewed hardware backend or a controlled test fixture; mock tests do not meet this precondition.

## Reference power sequence for a later authorized test

Keep the Pi and all motors disconnected for initial bench checks. A known, regulated, current-limited logic source may supply PI_3V3 at 3.2–3.4 V only if approved for that future setup, with no Pi supply rail connected in parallel. Share the intended ground and hold the physical switch in INHIBIT. If no suitable logic source is available, leave the powered test unexecuted. Applying motor input alone is not expected to power VM: Q1 defaults off without qualified LOGIC_GOOD.

Establish logic power first. Set motor input to the reviewed 5.5–6.5 V range with an initial **0.10 A** current limit and motion inhibited; observe bulk charging. Verify LOGIC_GOOD, VM and VM_OK, then raise the operating source ceiling to no more than **3.0 A** only after VM_OK is stable. The source must independently disconnect a persistent overload outside the normal pulse envelope within **100 ms**. These are additional derived reference operating restrictions, not confirmed features of the user's battery. The board fuse does not enforce 0.60 A/channel or provide the timed electronic cutoff.

For controlled shutdown, disarm, stop mechanical motion, switch off motor input upstream, wait at least **5 seconds**, and verify **VM <0.3 V** while logic power remains present. Only then turn off logic/Pi power. A timer alone is insufficient if motors are back-driven. Do not use the Phoenix plugs as switches under voltage or load. Abrupt Pi/VCC loss while VM remains charged is an explicitly unvalidated partial-power condition; it is not an approved fault test in this reference procedure.

## Test sequence

| ID | Setup / action | Expected result / evidence |
|---|---|---|
| V01 | Unpowered magnified inspection against schematic, assembly drawing and manufacturer pin-1 marks; check all connectors/capacitor polarity, solder joints and mounting clearances | No unexplained bridges, missing parts, reversed ICs or unsafe clearances; photos annotated with revision |
| V02 | Unpowered DMM checks of ground, VM/VCC paths, fuse continuity and intended isolated supply outputs; allow capacitors to settle | No unintended shorts; continuity matches reviewed netlist; record measured resistance and DMM mode rather than only a buzzer verdict |
| V03 | Pi and motors disconnected; approved bench logic feed first at 3.2–3.4 V, switch INHIBIT. Apply motor input with 0.10 A initial charging limit. Increase ceiling to <=3.0 A only after VM_OK is stable | Logic and protected VM match reviewed ranges; Q1 remains off without valid LOGIC_GOOD. Record charging waveform/current and absence of unexpected heating. No parallel bench/Pi logic supplies |
| V04 | Perform only the controlled startup/shutdown sequence above, initially with GPIO interfaces disconnected, then with the reviewed signal protection arrangement | Measure rail and interface currents; VM <0.3 V before logic removal. Abrupt VCC loss with charged VM remains NOT TESTED and outside this procedure |
| V05 | Motors absent. Observe PWM/direction/STBY during controlled startup, software restart, disarm and controlled shutdown; switch INHIBIT | STBY stays inactive until explicit arm and valid conditions; no output drive pulse while logic is valid. Record oscilloscope capture or instrument limitation; do not infer unpowered behavior |
| V06 | Motors absent, then one approved unloaded motor with robot supported. Activate physical disable while commanding with limited source energy | All channels disabled independently of software; voltage/state evidence; no output GPIO short. Releasing disable must not restart motion |
| V07 | One motor/channel at a time, approved low energy/duty, wheels lifted; trace channel ID to actual wheel and lead polarity | Correct wheel only, expected direction and duty. Complete `pin_map.md` with measured polarity |
| V08 | Per channel and both channels per IC, check stop versus standby and any explicitly supported brake mode | Measured response matches selected mode; quantify stopping behavior; no claim that standby immediately halts mechanics |
| V09 | Command forward then reverse using approved profile, limited speed/load | Required zero-drive interval observed; current/voltage within approved envelope. No arbitrary full-speed reversal |
| V10 | Stop command while pulse active; repeated stop; disarm/rearm; server restart; old session replay | Stop takes precedence, latches as specified; stale leases fail; restart disabled |
| V11 | Browser and CLI conflict; AI stop during manual pulse; malformed values and concurrent requests | Deterministic ownership, independent stop acceptance, no unintended takeover or restart |
| V12 | Drop client connection, expire command, pause/kill process or remove the heartbeat/signal path in a constrained approved fixture while maintaining qualified logic power and ground | Software expiry works when the process runs; separately verify the independent hardware timeout and re-arm behavior. Abrupt logic-power removal is excluded. Record failures; do not claim Python covers OS failure |
| V13 | Mock/injected camera loss, stale captures, slow model responses, malformed JSON and replayed frames; no paid calls needed | No AI motion grant; invalid/stale observations cause inhibit/stop; no heartbeat extends an old decision |
| V14 | Approved controlled mechanical load or dynamometer with current limit; record each channel and both channels/IC at real simultaneous duty | Running/startup current, source droop, VM overshoot, IC/connector/trace temperature satisfy reviewed limits; log ambient, duration and measurement uncertainty |
| V15 | Approved deceleration/load cases with source/BMS behavior understood; measure protected VM transient | Returned energy remains within approved component/rail limits; no deliberate supply-disconnect under load unless separately reviewed |
| V16 | Sensor/encoder checks only if a justified feature is populated | Compare against selected device limits and known stimulus; otherwise NOT APPLICABLE only after population decision |
| V17 | Final mounting/connector access/cable retention and supported-system acceptance | No cable contact with wheels, correct labels, accessible disable, documented residual failures |

Do not progress to V07 until V01–V06 pass. Do not run V14–V15 until all basic control tests pass and the load method, ratings and abort limits have been approved. Keep motors physically disconnected for model/parser/network tests where practical. No deliberate design faults are added for demonstrations.

## Evidence discipline

Store real evidence under a dated board-specific folder and reference relative paths in the CSV. Include raw captures and instrument setup, not only annotated screenshots. A simulation/mock test is not a substitute for V03–V15. If no oscilloscope/current-limited source/temperature measurement is available, leave the affected criterion unresolved and revise the plan before live tests. Derive Rev B only from recorded failures or measured requirements.
