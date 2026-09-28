# Requirements and assumptions — design-only milestone

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
**PURCHASE UPDATE: 6 V REFERENCE DESIGN NOT MATCHED TO THE LISTED 12 V SYSTEM.**

The latest user purchase records identify two WHEELTEC R3 two-wheel chassis
sets, each including two 12 V/30:1/500-line GMR encoder motors and one regulated
TB6612 dual-channel board, two listed 12 V/2500 mAh lithium packs and a Pi 5 4 GB
camera kit. The pack listings state built-in protection, continuous <4 A,
startup <10 A and maximum 48 W. These are purchase/listing facts, not measured
ratings, installed topology or a current-limiter specification. Exact MG513
motor identity remains unknown; MG513P30_12V is a candidate only. See
[actual_hardware_evidence.md](actual_hardware_evidence.md) and
[12v_design_impact.md](12v_design_impact.md).

Rev A retains its completed 5.5–6.5 V reference-input design; it is not suitable
for a direct 12 V source connection. This does not establish that the listed
12 V motors could never operate at lower voltage; that operating case and its
current/performance envelope have not been qualified. No CAD, BOM or reference
rating is silently changed by this evidence update.

Scope authority: user scope update, 2026-09-28, recorded in
[scope_design_only.md](scope_design_only.md). Hardware confirmations are the user
response already captured in [requirements.md](requirements.md) and
[pin_map.md](pin_map.md); they are not measured results. The former requirements
worksheet is retained as history/context. This table governs the design-only
assumption review and does not convert any unknown real-robot rating into a
confirmed specification.

Status vocabulary: **CONFIRMED** means explicitly supplied by the user or
established by the cited repository evidence within its limited scope;
**ASSUMED — ACCEPTED FOR REFERENCE DESIGN** records user acceptance of a design
boundary, not a measured real-robot fact; **PURCHASE-RECORD CONFIRMED** means the supplied listing specifies the item,
not that its installed topology or electrical behavior was measured;
**ASSUMED — REVIEW PENDING** marks a
remaining proposed detail; **UNKNOWN** needs information before compatibility can
be assessed.
The consequence column identifies what must be revisited if a proposed value or
current understanding does not hold.

## Existing system and unresolved electrical inputs

| Parameter | Value or range | Source | Confirmed, assumed, or unknown | Consequence if wrong or unavailable |
|---|---|---|---|---|
| Physical drivetrain | 2× WHEELTEC R3 two-wheel sets, four purchased 12 V/30:1 GMR encoder motors and two regulated TB6612 dual-channel boards | Latest user purchase records; earlier four-motor/two-board answer | PURCHASE-RECORD CONFIRMED; INSTALLED COUNT PREVIOUSLY USER-CONFIRMED | Exact supplied module revisions and motor identities still need association with the installed units |
| Controller path | Direct Pi 5 GPIO; no Arduino in motor-control loop | User response; `pin_map.md` | CONFIRMED | Interface and timeout architecture would need revision; do not invent an intermediate controller |
| Driver-to-wheel assignment | U1/Board A:A front-left, B front-right; U2/Board B:A back-left, B back-right | User response; `pin_map.md` | CONFIRMED | Connector labels, polarity review and command allocation would change; physical continuity remains NOT TESTED |
| Logical drive behavior | Paired left/right commands are the minimum reference behavior; four separate H-bridges | Existing differential-drive API; `architecture_review.md` | ASSUMED — REVIEW PENDING | Independent wheel commands would require more control lines/timing resources and a revised interface |
| Existing code's logical BCM map | PWMA18, AIN1 23, AIN2 24; PWMB13, BIN1 5, BIN2 6; STBY25 | Baseline code audit; `existing_system_audit.md` | CONFIRMED IN CODE ONLY | This does not establish two-board wiring; copying it without a wire map could energize the wrong input |
| Actual Pi-to-board GPIO wires and fanout | Both boards remain unverified; baseline has one logical A/B set, not an observed first-board map or second-board allocation | Baseline source; user highlights second board; no actual endpoint table | UNKNOWN FOR BOTH BOARDS | Neither board can be assigned the baseline GPIOs merely by inference; new reference fanout is not actual wiring |
| Motor lead polarity | TBD for each motor | No recorded polarity/continuity evidence | UNKNOWN | Same logic level may rotate one wheel in the wrong direction; paired input design requires corresponding lead orientation |
| Motor manufacturer/model and rated voltage | Purchased motor listing: 12 V, 30:1, 500-line GMR encoder; exact MG513 MPN unknown; MG513P30_12V candidate only | Latest WHEELTEC R3 purchase records | LISTED VOLTAGE/RATIO/ENCODER PURCHASE-CONFIRMED; EXACT MOTOR UNKNOWN | Completed 6 V reference is not matched to the listed 12 V system; lower-voltage operation needs separate qualification, and candidate-model ratings cannot be treated as actual |
| Real running, startup and stall current | TBD per motor, with load/voltage/duration conditions | No manufacturer data or controlled measurements provided | UNKNOWN | Cannot qualify TB6612FNG loading, thermal margin, connector/fuse ratings, or source demand |
| Real motor battery bounds | Two packs purchased, listed 12 V/2500 mAh lithium, continuous <4 A, startup <10 A, maximum 48 W | Latest user purchase records | PURCHASE-RECORD CONFIRMED; TRUE VOLTAGE/CURRENT BEHAVIOR UNKNOWN | Chemistry/series count, minimum/true nominal/full-charge voltage, rating conditions and current limiting are unresolved; listing values do not qualify the Rev A source |
| Existing source protection/energy absorption | Pack listings state built-in protection board; exact board/BMS, external fuse/reverse protection, cutoffs/delays/recovery/current limiting and sink behavior unknown | Latest purchase record plus remaining circuit evidence gap | PROTECTION PRESENCE LISTED; FUNCTIONS/LIMITS UNKNOWN | A protection-board label does not establish regulated current limiting, fault interruption coordination or regenerative-energy absorption |
| Pi power arrangement | Independent Pi supply and common Pi/driver/battery-negative ground remain the last user report; complete two-pack connection graph pending | Earlier user hardware answer; latest two-pack purchase record | PRIOR ARRANGEMENT USER-CONFIRMED; TOPOLOGY NEEDS RECONCILIATION | Do not infer that two packs are series/parallel, separately assigned, both installed or one spare; installed supply/return graph must resolve the relationship |
| Existing Pi supply rating/model | Pi 5 4 GB camera kit purchased; installed supply/adapter and power budget still unknown; microphone/speaker previously reported | Latest purchase record and earlier peripheral inventory | PI KIT PURCHASE-CONFIRMED; SUPPLY DETAILS UNKNOWN | Kit identity does not establish available 3.3 V capacity, installed power source or connection to either battery |
| Actual existing driver VCC source | Purchased modules described as regulated TB6612 boards; actual VCC source/voltage, regulator and jumpers unresolved for each | Latest module listing; historical README describes Pi3V3 only as documentation | MODULE DESCRIPTION PURCHASE-CONFIRMED; ACTUAL RAIL UNKNOWN | “Regulated” does not establish that VCC is Pi3V3 or 5 V; logic thresholds and power-off behavior require the actual circuit |
| Power sequencing and unplug states | Pi-only, VM-only, and switch/disconnect behavior need circuit review; existing behavior TBD | No measured or schematic evidence for actual breakout connections | UNKNOWN | Requires isolation/gating revision if unpowered inputs can be back-powered or enabled |
| Existing peripherals | Pi 5 4 GB camera kit purchased; USB microphone and speaker previously reported; no new camera/audio interface requirement | Latest purchase record plus earlier user response | PURCHASE-RECORD / USER-CONFIRMED | Installed models/connections and total Pi power budget remain unresolved |
| Encoders | Four purchased motors listed with 500-line GMR encoders | Latest WHEELTEC R3 purchase records; earlier integration reported absent | ENCODER HARDWARE PURCHASE-CONFIRMED; CURRENT INTEGRATION/ELECTRICAL INTERFACE UNKNOWN | Supply/output voltage, output type, pinout, count convention and motor/output-shaft reference are unknown; no encoder circuit or count-per-wheel assumption is added |

### Historical supply report retained

The earlier user answer said one motor battery feeds both VM inputs. That is
preserved as a historical report and is now **superseded as a settled topology
claim / awaiting reconciliation** with the two-pack purchase record. Neither
purchase quantity nor the old code establishes which packs are installed or how
they connect. Earlier unknown motor voltage/ratio and encoder presence are
superseded by the listed 12 V/30:1/500-line hardware; the earlier statement that
encoders were not integrated does not prove their current wiring/integration.
Independent Pi supply and common ground remain the last user report pending the
complete power graph. No old facts are silently overwritten as measurements.

The [manufacturer-source review](wheeltec_source_review.md) now supplies candidate
MG513P30_12V ratings, but no verified identity match to the purchased units.
Those conditional values do not fill the actual per-motor current fields.

## Bounded reference-design specification for review

The user previously accepted the principal reference envelope on 2026-09-28: 6 V nominal,
5.5–6.5 V input, 0.25 A RMS and 0.60 A/20 ms/10% peak per motor, ambient at most
40 C, separate Pi supply with 3.3 V logic, and a 100 × 80 mm two-layer/1 oz board.
This supported the completed native circuit/layout work for that reference
specification; the later 12 V purchase evidence does not extend its voltage
range or establish compatibility. It
does not establish the actual robot's ratings or approve TB6612FNG/protection
choices without circuit checks. Final circuit and
layout calculations must demonstrate the specified margins or explicitly reject
and revise the reference boundary. Numerical rows originate from the electrical
review proposal for this design-only milestone, not from motor measurements.

| Parameter | Value or range | Source | Confirmed, assumed, or unknown | Consequence if wrong or exceeded |
|---|---|---|---|---|
| Reference motor class | Nominal 6 V brushed geared DC loads satisfying every current/time bound below | User reference-scope acceptance, 2026-09-28; electrical/design proposal | ASSUMED — ACCEPTED FOR REFERENCE DESIGN | Actual motors outside this envelope are not supported without requalification |
| Raw motor input at connector | 6.0 V nominal, 5.5–6.5 V | User reference-scope acceptance, 2026-09-28; electrical/design proposal | ASSUMED — ACCEPTED FOR REFERENCE DESIGN | Re-evaluate reverse-protection drop, motor voltage, clamp headroom and component voltage ratings |
| Protected VM and qualification | Initial arm requires approximately >=4.85 V; nominal monitor rising thresholds UV 4.80 V / OV 7.16 V, UV falling approximately 4.73 V | Derived circuit review; `reference_electrical_spec.md`, `power_circuit_spec.md` | ASSUMED — DERIVED OPERATING REQUIREMENT | Protection losses at 5.5 V source and coincident peaks can deliberately disable operation; full peak torque at the low-input corner is not guaranteed |
| Per-channel continuous loading | At most 0.25 A RMS, including recirculation conditions | User reference-scope acceptance, 2026-09-28; electrical/design proposal | ASSUMED — ACCEPTED FOR REFERENCE DESIGN | Package conduction/thermal calculations and copper/contact budgets must be redone |
| Per-channel startup/peak loading | At most 0.60 A; each peak at most 20 ms, duty at most 10% | User reference-scope acceptance, 2026-09-28; electrical/design proposal | ASSUMED — ACCEPTED FOR REFERENCE DESIGN | Driver and protection suitability may fail; a fuse does not enforce this semiconductor current envelope |
| Simultaneous four-channel demand | At most 1.0 A RMS total; at most 2.4 A coincident peak under the above time bounds | Derived from four accepted individual envelopes | ASSUMED — DERIVED FROM ACCEPTED REFERENCE ENVELOPE | Input path, connector, protection and source budgets must be revised |
| Sustained blocked motor | Outside reference operating envelope | Proposed bounded load definition | ASSUMED — REVIEW PENDING | Requires separately designed current limiting/driver capability; do not test by uncontrolled stall |
| Reference enclosure ambient | At most 40 C | User reference-scope acceptance, 2026-09-28; electrical/design proposal | ASSUMED — ACCEPTED FOR REFERENCE DESIGN | Thermal margin and component derating must be recalculated for a hotter enclosure |
| Reference logic supply | Pi 3.3 V rail with existing independent Pi supply; required PCB rail range 3.2–3.4 V | User accepts reference rail; tolerance is a derived circuit requirement, not a measured Pi output | ASSUMED — REFERENCE RAIL ACCEPTED; DERIVED TOLERANCE UNMEASURED | Low rail inhibits enable; actual VCC wiring remains UNKNOWN; never connect two regulator outputs together |
| Reference ground/return topology | Common reference with continuous plane and placement-controlled high-current return paths | Confirmed shared ground plus proposed PCB architecture | ASSUMED — REVIEW PENDING for PCB implementation | Shared impedance or broken references may cause logic errors; arbitrary split grounds are not assumed safe |
| Returned energy | <=3 mJ total into VM per event, <=1 event/s, starting VM <=6.5 V; 2×1000 µF ±20% gives 1.6 mF minimum | Derived energy calculation in `reference_electrical_spec.md` | ASSUMED — DERIVED OPERATING REQUIREMENT | Exceeding this bound invalidates the capacitor/clamp budget; motor inductive and mechanical energy must both be included |
| Transient voltage allowance | Calculated capacitor voltage 6.782 V after the maximum energy event, plus <=0.20 V ESR/ESL/layout overshoot reserve | Derived calculation, not an oscilloscope result | ASSUMED — DERIVED REQUIREMENT, NOT TESTED | Larger overshoot or repetitive energy needs a revised protection design; TVS nominal voltage alone is insufficient |
| Source current and inrush | Charge initially at <=0.10 A with STBY inhibited; after VM_OK is stable operating source ceiling <=3.0 A; external disconnection of persistent overload within <=100 ms | Q1 has no controlled-inrush circuit; `power_circuit_spec.md` | ASSUMED — DERIVED SOURCE REQUIREMENT | An arbitrary battery/BMS or battery hot-plug is outside the reference design; PCB fuse does not enforce per-channel current or timed shutdown |
| Required rail sequence | Pi logic on first; remove motor input, wait at least 5 s and verify VM <0.3 V with mechanics stopped before Pi power off | Derived residual-energy and partial-power limitation; `power_circuit_spec.md` | ASSUMED — DERIVED OPERATING REQUIREMENT | Abrupt Pi loss with stored VM leaves an unvalidated TB6612 partial-power state; default-off feed switching does not discharge all stored energy immediately |
| New hardware/software handshake | J6 GPIO25 RUN, GPIO17 ARM, GPIO27 heartbeat; no STBY-to-Pi feedback; observe STBY at TP10 only | Current native reference schematic and `pin_map.md` | ASSUMED — PROPOSED INTERFACE, NOT IMPLEMENTED BY MOCK BACKEND | Existing direct-STBY software constants cannot operate this reference hardware without a new physical backend and deferred integration validation |
| Independent disable/timeout | Independent supervisor/watchdog and deliberate-arm latch drive default-low STBY; physical disable does not short a Pi output | Native reference circuit; `enable_interface_spec.md` | ASSUMED — IMPLEMENTED IN DRAFT CAD, PHYSICAL TIMING NOT TESTED | No mock result or ERC establishes actual watchdog timing, disable behavior or powered-off safety |

## Deferred mechanical and fabrication assumptions

These assumptions allow placement/routing study. They are not assertions about
the real chassis or any manufacturer's accepted process. Vendor selection,
quotations, assembly arrangements and purchases are deferred.

| Parameter | Value or range | Source | Confirmed, assumed, or unknown | Consequence if wrong or unavailable |
|---|---|---|---|---|
| Reference board envelope | Proposed 100 mm × 80 mm rectangle; no verified chassis fit | User reference-scope acceptance, 2026-09-28; electrical/design proposal | ASSUMED — ACCEPTED FOR REFERENCE DESIGN | Larger keep-outs or smaller chassis space may require a new placement/outline |
| Reference mounting | Proposed four 3.2 mm clearance holes with centers 5 mm from adjacent edges; final copper/component keep-outs reviewed in CAD | Provisional design worksheet | ASSUMED — REVIEW PENDING | Real hole pattern, fasteners, insulating spacers, or access may require relocation |
| Initial stackup study | Two-layer, 1 oz nominal external copper accepted; FR-4 and 1.6 mm nominal thickness retained as fabrication assumptions | User reference-scope acceptance plus provisional fabrication worksheet | ASSUMED — LAYER COUNT/COPPER ACCEPTED; MATERIAL/THICKNESS REVIEW PENDING | Layer count, trace drop/heat and via calculations change with final copper and routing needs |
| Fabrication design-rule study | Signals 0.25 mm nominal class, >=0.20 mm actual routing permitted including approximately 10 mm sections; copper clearance 0.20 mm; finished via hole 0.30 mm / pad 0.80 mm; provisional plating >=25 µm; 0.50 mm copper-to-edge | Reference layout rules and custom-footprint geometry review; no vendor acceptance | ASSUMED — REFERENCE DESIGN RULES, PROCESS REVIEW DEFERRED | These supersede the earlier 0.25 mm clearance proposal; vendor/assembly tolerance review can require rerouting |
| Power copper targets | Motor outputs 0.60 mm; VM/input trunks 1.00 mm; individual IC VM branches 0.40 mm for up to 27.09 mm including fanout/link segments at <=0.50 A RMS per package; GND and PI_3V3 0.40 mm with broad ground zones; individual 0.80 mm pad /0.30 mm finished-hole vias on REV_PROTECTED, VM and some motor outputs, with assumed >=25 µm plating and per-path loss screening; this supersedes the earlier paired-via preference | Derived routing targets and full-branch screening in `reference_electrical_spec.md` and `routing_rationale.md` | ASSUMED — DESIGN TARGETS, NOT MEASURED AMPACITY | Actual path length, copper/plating and temperature determine drop/heat; inspect fanout exceptions and recalculate if exceeded |
| Solder mask / TB6612 pad geometry | Custom TB pads 1.60×0.45 mm at 0.65 pitch, 0.03 mm mask expansion → nominal 0.14 mm web against provisional 0.10 mm target | `footprint_review.md`; geometric package review | ASSUMED — GEOMETRIC DERIVATION, ASSEMBLY REVIEW DEFERRED | No extra guaranteed side coverage for placement/registration is established; not a certified IPC land pattern or assembler acceptance |
| Board edge, hole and connector keep-outs | Must be encoded and checked against the chosen provisional outline and later actual mounting/harness | Native CAD review pending | UNKNOWN | Missing clearances can obstruct assembly/probing or violate electrical spacing |
| Fabricator/assembler and exact process | Deferred; no vendor contact, quote or acceptance claim | User design-only scope | CONFIRMED DEFERRED | Draft exports require a later vendor/process review before release |
| Budget/assembly tools/test equipment | Deferred for this milestone | User design-only scope | CONFIRMED DEFERRED | Changes future procurement, assembly route and physical validation planning, not the truth of present design evidence |
| Fabrication / assembly | DEFERRED / NOT BUILT; DEFERRED / NOT ASSEMBLED | User design-only scope | CONFIRMED STATUS | Do not use design images or old robot footage as evidence of a new built board |
| Physical validation / integration | NOT TESTED / NOT TESTED | No new proposed PCB exists as measured hardware | CONFIRMED STATUS | ERC/DRC and mock results cannot establish physical operation |

## Minimum unresolved information and review record

Do not ask again for the purchased set/motor/driver/pack counts, listed
12 V/30:1/500-line motor description, listed pack figures, Pi 5 4 GB kit, wheel
assignment, direct Pi path or Arduino absence. Retain the last separate-Pi/common-
ground report while reconciling the two-pack graph. Remaining evidence is:

1. Exact motor model/markings tied to the purchased 12 V/30:1 encoder units,
   running current with conditions, manufacturer startup/stall-current and
   permitted duration. MG513P30_12V remains a candidate until identified.
   Applicable existing records are evidence; no new physical test is requested.
2. Pack model/chemistry/series count and minimum, true nominal, full-charge
   maximum voltage; protection cutoffs/delays/current-limit behavior and
   returned-energy handling, plus the complete installed two-pack power graph.
   The listing's <4 A/<10 A figures do not establish controlled current limiting.
3. The actual Pi GPIO wire table for both drivers, including shared-input
   fanout, actual VCC connection, motor lead polarity, and supply order/unplug
   behavior. A labeled existing photo or wire list can fill this gap; the
   controller path and channel positions are already resolved. If encoder
   integration is required, its electrical levels, pinout and count convention
   remain additional unresolved interface evidence.
The principal bounded reference specification has already been accepted. Do not
ask the user to accept those same bounds again. Ask only if a later electrical
review requires changing a bound or deciding a remaining material detail.

Review status: **HISTORICAL 6 V REFERENCE ENVELOPE ACCEPTED; COMPLETED REFERENCE
CAD NOT MATCHED TO LATER 12 V PURCHASE SYSTEM.**
Electrical calculations and native schematic checks have separate evidence records; board-level checks remain governed by the current CAD reports. Motor/battery/
GPIO/VCC details for the actual robot remain unresolved beyond the stated
purchase facts. A 12 V adaptation decision is recorded separately in
[12v_design_impact.md](12v_design_impact.md). Acceptance of the
reference scope is not schematic freeze, physical validation or fabrication
release. Unaccepted detailed assumptions remain explicitly marked in the table.
Track changing assumptions and actual CAD checks in [the progress record](../PROGRESS.md).
