# Remaining risks and design-review disposition

**Evidence update — 2026-09-28:** Earlier unknown motor voltage/ratio and encoder presence are superseded by the [purchase-record evidence](actual_hardware_evidence.md): listed 12 V, 30:1, 500-line GMR motors. The remaining text records earlier reviews, not current hardware verification. The preserved 6 V PCB is [incompatible with direct 12 V input](12v_design_impact.md); actual currents, battery voltage bounds/topology and GPIO wiring remain unresolved.

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
Updated 2026-09-28 after native reference-CAD completion. Severity is engineering
priority, not a certified risk classification. Closing a design task does not
close the physical risk it addresses.

| ID | Priority | Current disposition | Remaining evidence / restriction |
|---|---|---|---|
| K01 | High | Reference motor envelope and thermal screening completed | Actual motor rating/current unknown; measurements needed before compatibility claim |
| K02 | High | Bounded protection/source/regen circuit documented | Actual battery/BMS unknown; initial <=0.10 A charging, <=3 A ceiling and <=100 ms external overload interruption required |
| K03 | High | New J6 mapping and four separate output pairs implemented | Existing GPIO fanout/VCC/polarity unverified; no hardware backend deployment |
| K04 | High | Independent watchdog/inhibit/arm latch implemented in CAD | Physical timeout/fault behavior NOT TESTED; continued false heartbeat, failed devices and startup grace interval remain limitations |
| K05 | High | Rail sequencing and partial-power restrictions explicit | Abrupt Pi loss with stored VM remains unvalidated; Pi-first, VM-off/discharge-before-Pi-off required |
| K06 | High | Current/thermal and routed copper screening recorded | Junction/trace temperature, simultaneous loading, return behavior and EMC unmeasured |
| K07 | Medium | Future Pi handshake contract documented | Actual GPIO provider/PWM levels and scheduling need implementation and scope testing |
| K08 | Medium | AI remains inhibit-only with structured/freshness checks | Acquisition timestamp is not proof of sensor exposure freshness; camera buffering unqualified |
| K09 | Medium | Mock expiry/reversal behavior preserved | Mechanical stopping time, reversal current and motion limits unmeasured |
| K10 | Medium | Local mock-development deployment boundary retained | HTTP authentication/network trust requires a separate deployment review |
| K11 | Medium | Accepted 100×80 mm reference and native placement complete | Actual chassis fit, connector access, assembly process and budget deferred |
| K12 | Design task closed | KiCad 10.0.6 available; native schematic and routed PCB completed | ERC/DRC zero under recorded configuration; reopening is required if source/rules change |
| K13 | Deferred | Fabrication NOT BUILT; assembly NOT ASSEMBLED | Physical validation and integration NOT TESTED; no order or build implied |
| K14 | High | Prototype inhibit clearly distinguished from emergency stop | No certified emergency-stop, redundant fault coverage or guaranteed mechanical stop |
| K15 | Medium | Source-reviewed local footprints/models included | TB land-pattern registration margin, IDC hole/pin tolerance and actual stencil/process acceptance remain unresolved; 3D is approximate |
| K16 | High | Source-limited reference operation explicitly bounded | PCB lacks controlled inrush/per-channel limiting; arbitrary battery hot-plug and sustained stalls excluded |

The recorded native [ERC](../validation/design/erc_final.json) and
[DRC](../validation/design/drc_final.json) have zero violations, with DRC also
reporting zero unconnected and schematic-parity findings. This is the result
under the stored check configuration; ignored classes are visible in the
reports. [schematic_review.md](schematic_review.md) explains pin/net comparison,
not a hardware functional test. The operating restrictions are governed by
[reference_electrical_spec.md](reference_electrical_spec.md),
[power_circuit_spec.md](power_circuit_spec.md) and
[enable_interface_spec.md](enable_interface_spec.md).

False AI detections are not proof of obstacle clearance. AI cannot arm/reset/
drive in the current draft. The 132 preserved mock tests do not validate the
independent hardware or permit autonomous motion. The historical risk register
below is retained with its original status language for audit continuity.

## Historical pre-CAD evaluation — preserved

The material below records the earlier requirements/audit gate. Statements such
as “no native CAD,” “not run,” “TBD circuit,” or “before schematic capture” refer
to that earlier stage and are superseded by the current section above and its
linked design records. The earlier calculations remain examples, not the
accepted reference operating specification. Real-robot unknowns remain unknown.

### Remaining risks and decision register

All entries are open unless supported by evidence. Severity is engineering priority for this prototype, not a certified risk assessment.

| ID | Priority | Open issue | Closure evidence / next action |
|---|---|---|---|
| K01 | High | Motor current/voltage unknown; candidate IC may be unsuitable | Exact datasheet and simultaneous-load/thermal review; reject TB6612 if inadequate |
| K02 | High | Motor source and protection unknown | Battery range/BMS behavior, fuse/cable/connector and reverse-energy calculation |
| K03 | High | Direct Pi and driver-to-wheel map confirmed; exact GPIO fanout/polarity still unknown | Complete pin/wire map and Pi GPIO provider inventory; no real GPIO backend until electrical review |
| K04 | High | Software cannot guarantee disable during kernel/process/peripheral faults | Reviewed independent enable timeout and physical disable, then constrained physical test |
| K05 | High | Power sequencing/back-power not established | Device I/O limits, partial-power-down circuit review and measured leakage tests |
| K06 | High | Simultaneous channel losses and copper temperature unknown | Stackup/ambient/load data, worst-case calculations and measurements |
| K07 | Medium | Pi 5 GPIO provider/timing unspecified | Inspect actual interpreter/distribution/source; scope selected PWM under load |
| K08 | Medium | Camera buffering/time provenance not sensor exposure | Camera timestamp/buffering characterization; AI remains inhibit-only |
| K09 | Medium | Mock expiry/reversal durations are unvalidated mechanical settings | Current/stopping-distance tests and reviewed limits before actuation |
| K10 | Medium | HTTP interface has no production authentication/security boundary | Local mock development only; review trusted-network/auth/deployment separately |
| K11 | Medium | Board dimensions and assembly route unknown | Mounting sketch/budget/instruments/assembler selection |
| K12 | High | No KiCad available, no schematic/layout/release | Install or identify tool, perform reviewed native design and all checks |
| K13 | Medium | No fabricated/assembled/physical validation evidence | Execute staged plan only after explicit authorization; retain raw results |
| K14 | Medium | Prototype disable is not an emergency-stop system | Document permissible operating context, energy and accessible physical interruption |

The original open-loop vision policy cannot establish obstacle clearance. AI false/false detections may be wrong and must not be used as a safety guarantee. This draft deliberately limits AI authority; any later autonomous-motion requirement needs its own freshness, supervision and physical-risk review.
