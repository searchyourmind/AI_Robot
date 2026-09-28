# Engineering review and interview notes

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
Fabrication **DEFERRED**; assembly **NOT ASSEMBLED**; physical validation and proposed-PCB integration **NOT TESTED**.

The project is a pre-fabrication engineering exercise with AI-assisted analysis, native CAD authoring and software verification. It does not claim that an assembled custom board has run the robot. Before presenting the work as engineering experience, personally review the files, reproduce the checks and be prepared to explain the circuit.

## The actual engineering story

The reported prototype uses a Pi 5, four motors, two TB6612 breakout boards, camera, USB microphone and speaker. Its first custom-board draft accepted a bounded 6 V reference while motor/source details were unknown. Purchase records subsequently established a listed 12 V platform: two WHEELTEC R3 kits, four 12 V/30:1/500-line GMR motors and two 12 V-labeled packs.

That audit exposed the old 7 V TVS and roughly 7.16 V overvoltage window as incompatible with direct 12 V input. It also required a current-margin review. Public MG513P30_12V data gives approximately 0.36 A rated and 3.2 A stall, but the exact installed motor label remains unconfirmed. Toshiba’s 3.2 A figure is a restricted absolute peak, not continuous capability; the dual-TB branch was rejected for the new reference envelope.

The replacement draft uses four DRV8874 bridges with individual current regulation, a TPS26630 eFuse and source-referenced reverse FET stage, revised protection and energy bounds, larger 50 V bulk capacitors, and updated command, wake and arming logic. The provisional board has two layers, measures 100 × 100 mm, and contains 121 fitted placements and 14 copper testpoints. This is a design-review correction before manufacture. **No hardware failure, repair outcome or successful motor test is invented.** The [revision history](../../hardware/rev_a/docs/revision_history.md) and [6 V archive](../../hardware/rev_a_6v_archive/ARCHIVE_NOTICE.md) preserve the evidence.

## Explain the decisions

1. **Why two TB6612 boards in the prototype?** Each is a dual bridge; two provide four separate motor channels. The existing front A/B and rear A/B wheel mapping is user-reported. That explains the prototype, but does not establish that its drivers have sufficient stall margin.
2. **Why four DRV8874 in the new board?** One regulated bridge per motor avoids relying on thermal shutdown or a headline peak current. Approximately 0.79 A chopping limits individual winding current; startup torque and motor heating still need qualification. The aggregate eFuse can latch off on four simultaneous starts. No claim is made that selecting a larger headline driver automatically solves all limits.
3. **Why separate outputs but paired commands?** Each winding requires its own bridge output. Front/back wheels on a side receive the same PWM/DIR commands for differential drive. Outputs are never paralleled. This board does not support four independent velocity commands or wheel-encoder feedback.
4. **Why separate Pi power?** Motor startup, current chopping and regenerated energy should not be passed through a new, unqualified Pi regulator path. Grounds are common for signal reference, with the motor return intended to remain in the power area. Separate supplies do not eliminate ground noise or permit arbitrary power sequencing.
5. **Why two layers and 100 × 100 mm?** Two layers are a provisional cost and process choice; the larger outline makes room for four driver stages, bulk capacitors and copper for heat spreading and return paths. Neither size nor mounting-hole layout is based on measured chassis fit. Four layers may be preferable after EMI, thermal and routing review; DRC does not establish that two layers are sufficient.
6. **Why different trace widths?** Aggregate input/VM trunks carry the sum of channels, individual motor branches carry one regulated current, and logic carries small signal current. Fine-pitch pins require short narrower escapes; the [routing review](../../hardware/rev_a/docs/routing_rationale.md) reports actual widths/lengths. Zones and vias must support return current and heat flow; a wide outward trace with a poor return is insufficient.
7. **Why local ceramic and bulk placement?** Short VM ceramic loops supply switching edges, charge-pump capacitors follow driver pin functions, local bulk supports each stage, and central bulk absorbs a bounded returned-energy event. Capacitance tolerance, bias, ESR and ageing matter. The TVS is an abnormal-transient clamp with a stated pulse envelope, not an unlimited braking resistor.
8. **Why default to disabled, with drivers awake before ARM?** Valid heartbeat, RUN, rail and fault states plus a fresh ARM edge are required for command permission. Normal DRV wake produces a fault pulse; tying sleep to the arm/fault loop would prevent clean startup. Drivers instead wake while command gates hold 00/coast, then can be armed after conditions qualify.
9. **What do stop and physical inhibit do?** An armed PWM-off interval gives 11/brake decay. Disarm gates inputs to 00/coast. Physical inhibit additionally asserts driver sleep and eFuse shutdown, independent of process progress. It leaves stored VM energy and possible motor backdrive. It is not a certified E-stop, isolation switch or guaranteed stopping-distance mechanism.
10. **Why 121 components?** [The exact count](../../hardware/rev_a/docs/component_count_review.md) separates power/current regulation, logic qualification, decoupling and connectors. Count alone is not quality: each part needs a purpose. The revision adds per-driver regulation and a more complete power path while retaining a substantial discrete permission circuit. A later simplification must preserve documented behavior and be separately validated.
11. **What does ERC 0 / DRC 0 mean?** Only that the saved CAD passed the enabled rules and connectivity/parity checks. It cannot establish that the battery fits the input envelope, the motor starts, the TVS stays below its hot clamp target, the board remains cool or software drives real GPIO correctly. Refer to the [actual report](../../hardware/rev_a/validation/design/design_check_report.md) for the current result, not the old archive's numbers.

## Evidence and remaining work

The editable design has seven sheets and a native PCB; PDFs, BOM, Gerbers, drills, placement data and 3D images are draft artifacts. A KiCad render is not a photograph. The independent checks compare the manifest, exported XML and all physical pads, including repeated exposed-pad holes and intentional NCs. Boolean truth checks cover control conditions; they do not imply analogue simulation, SPICE, timing analysis or physical fault testing.

The original 132 offline mock-test report is preserved. A separately recorded pre-publication rerun passed 132 cases; this tests software state/API/parser behavior with device/network guards, not the PCB. AI can request stop only. A real backend for the new J6 handshake and actual GPIO mapping is still absent.

Before any fabrication release, resolve exact motor labels and current waveforms; battery chemistry, voltage range, connections, BMS behavior and fault capability; GPIO wiring, voltage levels and polarity; Pi supply; switch/E-stop arrangement; mechanical envelope; and the filled/capped thermal-hole assembly process. “12 V lithium” alone is not a 3S or 12.6 V specification. The actual robot has not yet been shown to meet the provisional 9–15 V, ≤2 A normal input and bounded-transient requirements.

## Supported portfolio wording

“Developed an AI-assisted, pre-fabrication four-motor interface design and corrected a 6 V assumption after a hardware purchase-record audit. Compared driver operating, stall and thermal limits; selected four current-regulated bridges; documented power protection and fault/arming behavior; produced editable KiCad CAD and reproducible digital checks. Fabrication and physical validation remain pending.”

Do not replace “pre-fabrication” with “built,” “tested,” “validated on the robot,” or measured reliability/thermal improvements. Explain the equations and limits in your own words and identify which work was AI-assisted.
