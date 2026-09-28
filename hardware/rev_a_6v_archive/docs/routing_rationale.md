# Routing and shared-board thermal rationale

**6 V REFERENCE ONLY — DIRECT 12 V INPUT INCOMPATIBLE.** The 2026-09-28 purchase-record update establishes listed 12 V motors and packs. This document retains the existing 5.5–6.5 V design; its calculations, parts and checks have not been qualified for that system. See the [12 V impact review](12v_design_impact.md) and [current hardware evidence](actual_hardware_evidence.md).

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
**DRAFT — NOT RELEASED FOR FABRICATION.** These calculations and review targets use the integrated component manifest and the accepted 0.25 A RMS/channel envelope. Physical temperatures, current waveforms and supply behavior remain NOT TESTED. The [final electrical layout review](electrical_layout_review.md) and native connectivity/DRC evidence are separate.

## Current paths and placement intent

Keep J1→F1→D1→Q1→VM bulk capacitors as a short input path. D2 returns transient current directly to the bulk-capacitor ground region. U1 serves the front pair and U2 the rear pair, with their motor connectors close to the output side. Place each VM and VCC ceramic at the relevant IC pins, followed closely by its 47 µF electrolytic. Connect every duplicate output/PGND terminal and every VM terminal. Do not route a motor return through the Pi cable or through a thin logic-ground trace.

Use a continuous common-ground zone on both layers where routing permits, with stitching vias around the driver power returns and between the input, bulk capacitors and drivers. Separate the high-current loop geometrically from the Pi header, heartbeat/arm circuitry and VM sense nodes while keeping a common reference plane. A split ground with only a narrow join would increase return impedance and is not the intended topology. Logic signals need adjacent continuous return copper; review plane slots created by motor tracks and vias.

Routing uses 0.60 mm motor outputs and 1.00 mm MOTOR_IN/FUSED_IN/REV_PROTECTED/VM trunks. The individual VM branches feeding one TB6612 may be 0.40 mm wide for 27.09 mm: these carry at most the sum of two 0.25 A RMS channel currents, bounded by 0.50 A RMS per package. They are branches, not short pad necks; their full length is included below. Ground connections and PI_3V3 use a nominal 0.40 mm plus ground zones. Signal routes have a 0.25 mm nominal class with 0.20 mm actual routing permitted, including sections approximately 10 mm long. The low-current logic routes do not need a 0.25 mm ampacity claim. Local pad fanout geometry is reviewed against the actual board. These choices supersede the preliminary 1.0/1.5 mm width defaults and the earlier restriction of all 0.40 mm VM copper to 2 mm necks.

## Copper loss screening

For nominal 35 µm copper and 20 C resistivity `rho=1.724e-8 ohm·m`, use `R=rho×L/(width×thickness)` and `R(T)=R20×[1+0.00393×(T−20)]`. A 60 C conductor is a sensitivity case, not a predicted temperature.

| Conductor example | R at 20 C | R at 60 C | Reference loss/drop at 60 C |
| --- | ---: | ---: | --- |
| 1.00 mm wide, 50 mm long trunk | 24.63 mΩ | 28.50 mΩ | At 1.05 A: 31.4 mW and 29.9 mV; at 2.4 A peak: 68.4 mV |
| 0.60 mm wide, 50 mm long motor output | 41.05 mΩ | 47.50 mΩ | At 0.25 A RMS: 2.97 mW; at 0.60 A peak: 28.5 mV |
| 0.40 mm wide, 27.09 mm individual VM branch | 33.36 mΩ | 38.60 mΩ | At 0.50 A RMS: 9.65 mW and 19.3 mV; at 1.20 A coincident peak: 46.3 mV |
| 0.40 mm wide, 2 mm local neck | 2.46 mΩ | 2.85 mΩ | At 1.05 A: 3.14 mW and 2.99 mV |
| 0.20 mm wide, 10 mm logic route | 24.63 mΩ | 28.50 mΩ | Illustrative 10 mA: 2.85 µW and 0.285 mV; not a claim that every signal draws 10 mA |
| 0.30 mm hole, 1.6 mm long, 25 µm plated via barrel | 1.17 mΩ | 1.35 mΩ | Resistance-only model; two equally loaded parallel vias halve it |

The final native-board inventory is recorded in [electrical_board_review.json](../validation/design/electrical_board_review.json). The longest individual 0.40 mm VM segment is 22.7635 mm; adding its adjoining 0.8092 mm, 0.2635 mm and 3.2508 mm segments gives a 27.0870 mm branch. The other 0.40 mm feed branch totals approximately 10.8822 mm. Motor output pad joins include 0.40 mm × 0.65 mm links and short 0.36 mm × 0.1075 mm / 0.4506 mm × 1.162 mm fanouts; they remain above the 0.20 mm minimum. The 0.36 mm neck contributes only about 0.17 mΩ at the illustrative 60 C copper temperature. PI_3V3 and logic-ground fanouts also include 0.24–0.31 mm widths. These are explicit actual geometry, not a blanket assertion that every route equals its nominal net-class width.

The final board uses individual 0.80/0.30 mm vias on REV_PROTECTED, VM and several motor outputs, superseding the preliminary paired-via preference. With the stated 25 µm plating assumption, one via screens at 1.35 mΩ at 60 C. Its loss is approximately 1.49 mW at 1.05 A input-path RMS, 0.338 mW at 0.50 A package-branch RMS, or 0.084 mW at 0.25 A output RMS. Peak drops at 2.4/1.2/0.6 A are respectively 3.24/1.62/0.81 mV. Series vias add; vias are not presumed parallel merely because their net names match. These small resistance losses justify retaining the reference geometry for design review, while plated-hole construction, thermal behavior, fault energy and fabrication acceptance remain unverified.

A motor loop includes two output conductors; a supply loop includes both supply and return. Add contacts, vias, fuse, diode and MOSFET loss. These examples cannot be multiplied into a whole-board claim without extracting actual lengths and current splits. Copper temperature requires a thermal method/model or measurements that include plane coverage, neckdowns, finished thickness and enclosure conditions. Do not assign a generic amps-per-via figure.

## Power and logic budget update

The driver calculation remains `2×0.25²×1.4+0.05=0.225 W` per package, or 0.45 W for both. The 1.4 ohm hot-state assumption and 50 mW overhead are screening allowances, not Toshiba guarantees at 3.3 V. The IC-only 160 C/W reference produces 76 C at 40 C ambient for one package, but does not model mutual board heating.

| Heat source | Reference screening allocation | Important limit |
| --- | ---: | --- |
| Two TB6612 packages | 0.45 W total | Both channels and both ICs active; physical thermal validation deferred |
| D1 | Approximately 0.51 W at 1.05 A | Uses 0.49 V manufacturer test-point drop; actual operating drop/temperature depend on layout |
| Q1 | 0.141 W | 1.05 A RMS with 1.5× sensitivity on 85 mΩ room-temperature limit |
| F1 | 0.040 W | Nominal 36.7 mΩ; fuse resistance changes with heat |
| R5 | <=0.135 W at 6.5 V | Includes −5% resistance tolerance; this is a continuous discharge load |
| Pi-supplied board logic | Reserve 60 mA at 3.3 V; approximately 0.204 W at 3.4 V | 50 mA interface allowance plus 10 mA for driver VCC uncertainty; not measured spare Pi capacity |

These entries total approximately 1.48 W before copper/harness loss. The extracted 27.09 mm and 10.88 mm VM branches together add approximately 13.5 mW in the 60 C resistivity sensitivity case when each is screened at 0.50 A RMS. This bounds two-channel current per package; it does not assume equal internal sharing among VM pins. Some logic allowance overlaps the driver overhead, so this is a conservative planning sum rather than a measured efficiency result. Do not convert the sum to a single junction temperature. Preserve copper around D1/Q1 and space them away from driver packages and electrolytics where possible.

The seven 1k pullups on six motor-control signals and STBY can draw approximately 24 mA when their open-drain outputs are low. The complete Pi load also includes supervisor, watchdog, gates, pull resistors and driver logic. The new board does not power the Pi Camera, microphone or speaker; those still consume the independent Pi supply budget. PI_3V3 must remain within the derived 3.2–3.4 V operating requirement at the board.

The two VCC 47 µF electrolytics contribute 94 µF nominal, 112.8 µF maximum initial capacitance. Including ceramics gives roughly 115 µF total logic-rail load. A hypothetical 1 ms rise to 3.3 V requires approximately 0.38 A capacitive charging current before operating load; the actual Pi rail ramp/current margin is unknown. This calculation explains why live cable insertion and power sequencing cannot be approved from a steady-state 60 mA budget alone.

## Layout review checkpoints

Confirm actual widths and local neckdown lengths, intact ground return areas, each driver cap loop, input clamp loop, no output paralleling, no motor current through J6 grounds, sense routing away from switched outputs, solder-mask openings, motor/power connector labels and mechanical courtyard spacing. Preserve access to VM, PI_3V3, GND, LOGIC_GOOD, VM_OK, WD_RAW, HB, ARM_Q, ALL_OK and STBY test pads.

Ground-zone fill and DRC must be rerun after any placement or route change. Counts of unrouted connections and any reviewed rule exceptions belong in the actual report, not in this rationale. A screenshot with traces does not establish netlist equality. [reference_electrical_spec.md](reference_electrical_spec.md), [power_circuit_spec.md](power_circuit_spec.md) and [enable_interface_spec.md](enable_interface_spec.md) contain the primary electrical sources and source-revision records used here.
