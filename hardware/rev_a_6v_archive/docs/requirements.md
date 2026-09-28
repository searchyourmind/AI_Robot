# Rev A requirements — completed design-only milestone

**Evidence update — 2026-09-28:** Earlier unknown motor voltage/ratio and encoder presence are superseded by the [purchase-record evidence](actual_hardware_evidence.md): listed 12 V, 30:1, 500-line GMR motors. The remaining text records earlier reviews, not current hardware verification. The preserved 6 V PCB is [incompatible with direct 12 V input](12v_design_impact.md); actual currents, battery voltage bounds/topology and GPIO wiring remain unresolved.

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
Current status: 2026-09-28. The user accepted a bounded reference specification
and design-only scope; native schematic and routed-PCB work is complete.
[scope_design_only.md](scope_design_only.md) supersedes the earlier requirement
to finish fabrication, assembly and physical tests in this phase.
[requirements_assumptions.md](requirements_assumptions.md) is the governing
parameter/source/status/consequence table. No fabrication release is implied.

| ID | Current evidence / disposition | Remaining boundary |
|---|---|---|
| R01 | Four separate H-bridges in two TB6612 ICs; confirmed wheel assignment captured in native nets | Existing motor leads/polarity not verified |
| R02 | Camera/browser/AI paths retained in recorded software; 132 offline mock cases preserved | No new physical integration test |
| R03 | Direct Pi 5, no Arduino confirmed; new J6 allocation documented | Existing GPIO wires/provider remain unknown |
| R04 | Bounded 0.25 A RMS /0.60 A peak motor envelope and package screening completed | Actual motor suitability and temperature NOT TESTED |
| R05 | Selected protection, VM qualification and bounded energy/source calculations recorded | Actual battery/BMS unknown; derived source and rail-sequence restrictions retained |
| R06 | Four motor connectors, power/logic connector and ten labeled copper test points in CAD | Physical polarity, access and behavior NOT TESTED |
| R07 | Independent watchdog, physical inhibit and deliberate-arm latch captured | No emergency-stop certification or physical disable-time claim |
| R08 | Separate Pi supply retained; common reference, Pi-supplied 3.3 V logic | Actual rail margin and abrupt-loss behavior unverified |
| R09 | Mock command validation/lease/arm/expiry behaviors recorded | No physical backend qualification |
| R10 | Inhibit-only AI and structured/freshness parsing tested with mocks | Camera exposure age/buffering and autonomous motion unqualified |
| R11 | Five-sheet native schematic, routed two-layer PCB and local libraries exist; actual ERC/DRC zero under recorded configuration | Not fabrication or hardware validation |
| R12 | Draft native exports/BOM are generated for review; no release/ordering | Vendor/process review and fabrication authorization deferred |
| R13 | Accepted 100×80 mm two-layer/1 oz reference; four 3.2 mm mounting holes at 5 mm offsets | Actual chassis fit, assembly route and equipment deferred |
| R14 | No extra MCU, speculative sensor, Pi supply, camera or audio circuit added | Concrete future requirements would change scope |
| R15 | Historical software and blank physical records preserved; AI assistance disclosed | Personal review and independently reproduced checks still need ownership entries |

The schematic contains 107 instances: **97 planned fitted parts**, ten copper
test points excluded from BOM; four mounting holes are PCB-only. Actual
[ERC](../validation/design/erc_final.json), [DRC](../validation/design/drc_final.json)
and [netlist parity](../validation/design/schematic_parity.json) are saved.
DRC reports zero violations, zero unconnected items and zero schematic-parity
findings; ignored check classes remain disclosed by the JSON reports.

The minimum real-robot inputs still needed for later compatibility are exact
motor ratings/current envelope, source voltage/protection/energy behavior and
actual GPIO/VCC/polarity wiring. Do not ask again for already confirmed motor
count, board/channel positions, direct Pi controller path, separate Pi supply
or common ground. Budget, instruments, vendor choice and assembly route are
deferred by the accepted scope and do not block this completed reference-CAD
milestone. They do matter before a later physical release.

Fabrication **DEFERRED / NOT BUILT**; assembly **DEFERRED / NOT ASSEMBLED**;
physical validation and integration **NOT TESTED**. The historical review gate
below was superseded by reference-scope acceptance; it is not a new request for
permission or a claim that the actual robot's unknown specifications were solved.

## Historical pre-CAD evaluation — preserved

The material below records the earlier requirements/audit gate. Statements such
as “no native CAD,” “not run,” “TBD circuit,” or “before schematic capture” refer
to that earlier stage and are superseded by the current section above and its
linked design records. The earlier calculations remain examples, not the
accepted reference operating specification. Real-robot unknowns remain unknown.

### Rev A requirements and open inputs

Status: **DRAFT — architecture/electrical review pending**. Evidence baseline and vocabulary: `existing_system_audit.md`. Request owner: project student. Decisions remain reviewable; no fabrication release.

| ID | Requirement | Evidence / acceptance gate | State |
|---|---|---|---|
| R01 | Extend this Pi robot with four separately wired motor channels using two candidate TB6612FNG ICs | User hardware count; every channel traced to one motor; no paralleled H-bridge outputs | Count and driver/channel-to-wheel mapping user-confirmed; GPIO wires/polarity TBD |
| R02 | Preserve existing Pi/camera/browser/AI structure where practical | Mock integration tests; explicitly documented API changes | Draft software in progress |
| R03 | Determine actual controller path before pin allocation | Wire table/photos and installed software inventory | USER-CONFIRMED: direct Pi 5 GPIO; Arduino not in motor loop; actual pin fanout TBD |
| R04 | Qualify motors and both-channel IC loading | Rated voltage, operating/startup/stall envelopes, duty/load, thermal calculation | BLOCKED: specifications |
| R05 | Qualify source/protection and regenerative energy | Minimum/nominal/fully charged voltage; battery/BMS/current limit; fuse/cable/connector coordination | BLOCKED: specifications |
| R06 | Four labeled motor outputs; logic/input/test labels and hardware disabled startup | Reviewed netlist, pin/pad mapping, fault/power-sequence tests | Proposed |
| R07 | Physical disable independent of HTTP/Python, no shorted output GPIO | Reviewed circuit plus measured disable and power tests | Proposed; not a certified emergency stop |
| R08 | Preserve appropriate existing Pi supply | Separate supply domains, common reference review, no tied outputs/back-power | Existing supply details TBD |
| R09 | Strict command validation, arm/latch/ownership, expiry, nonblocking commands | Offline mock tests; hardware tests separate | Draft software |
| R10 | No AI decision can arm, defeat disable, or resurrect stale motion | Capture provenance/schema/age tests; false/false is not clearance | Draft inhibit-only AI |
| R11 | Native editable KiCad + verifiable libraries and manufacturer rules | Reviewed architecture, installed version, ERC/DRC/consistency and visual inspection | BLOCKED; no native CAD yet |
| R12 | Manufacturing data only from reviewed design | BOM/MPN/orientation, Gerbers/drills/placement/assembly drawings verified to selected assembler | NOT RELEASED |
| R13 | Board outline/mounting/assembly feasible for student | Dimensions, hole coordinates/keep-outs, cable exit, method, budget | TBD |
| R14 | No speculative sensors or extra controller | Each populated sensor/regulator/MCU must solve a recorded requirement | No additions selected |
| R15 | Honest validation and ownership records | Blank physical measurements until tested; reviewed contributions documented | Required throughout |

#### Hardware response and remaining information

The user answered the compact batch on 2026-09-28: four geared DC motors; two TB6612 boards with the mapping in `pin_map.md`; direct Pi 5 GPIO; no Arduino in the loop; Pi separately powered; motor battery feeds both VM inputs; Pi/driver grounds and battery negative share ground. Pi Camera, USB microphone and speaker are present. Encoders are not integrated; their physical presence is TBD. The new board should consolidate jumper-wire motor/power/control connections. All motor/source ratings, mechanical constraints, budget, assembly method, instruments and vendor remain TBD. These are user confirmations, not measured validation.

Remaining inputs (do not ask again for already confirmed counts/controller/channel positions):

1. Exact motor model, rated voltage, running current at a stated load, startup/stall current and permitted duration from a datasheet or existing controlled measurements. Do not perform an uncontrolled stall to fill the table.
2. Motor source type, minimum/nominal/maximum charged voltage, source current capability, BMS/fuse/reverse-polarity/transient protection; existing Pi supply model and wiring.
3. Exact GPIO-to-input wires on both boards, especially whether Board B shares A/B PWM/direction/STBY signals with Board A; motor lead polarity; actual VCC connection and breakout schematic/parts. The direct Pi path and channel positions are already confirmed.
4. Maximum board dimensions, mounting-hole coordinates/heights/keep-outs, connector access, budget/currency, hand assembly versus PCBA, preferred assembler, and available DMM/scope/current-limited supply/load/temperature instruments.

Unknown quantities stay TBD. README's example 6–9 V is not a resolved supply range. No second confirmation of motor/driver count is requested.

#### Electrical input worksheet

| Quantity | Value | Source / conditions |
|---|---|---|
| Motor manufacturer/model | Four geared DC motors; exact model TBD | User response; primary datasheet still required |
| Rated motor voltage | TBD | |
| Running current, each motor | TBD | Load, speed, ambient, duty |
| Startup/stall current and permitted transient | TBD | No uncontrolled stall test |
| Maximum simultaneous startup/reversal events | TBD | Four channels must be included |
| Source minimum / nominal / charged maximum | TBD / TBD / TBD | Include charging state if connected |
| Source sink capability / BMS disconnect behavior | TBD | Regenerative energy review |
| Existing fuse and wiring/connector ratings | TBD | Manufacturer part numbers |
| Pi supply model / grounding | Separate Pi supply confirmed; model TBD; Pi/driver/battery common ground confirmed | User response 2026-09-28 |
| Controller and GPIO provider | Direct Pi 5 GPIO confirmed; installed provider/OS and exact fanout TBD | User response plus target inventory still needed |
| Ambient / allowable surface and junction temperatures | TBD | Enclosure/ventilation |
| Board outline, copper stackup, mounting | TBD | No invented dimensions |
| Maximum safe command age / stopping distance | TBD | Mock intervals are not safety limits |

#### Review gate before schematic/layout freeze

Review `architecture_review.md`, `pin_map.md`, `circuit_review.md`, `electrical_budget.md`, and this worksheet together. Record reviewer/date, chosen A or B logic arrangement, verified controller path, driver acceptance/rejection with numerical margin, supply/protection architecture, mechanical constraints, assembly route, and remaining exceptions. An unanswered request is not approval. Incomplete evidence permits draft analysis/mock tests only.
