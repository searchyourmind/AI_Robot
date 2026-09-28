# Draft assembly and inspection notes

**DRAFT — NOT RELEASED FOR FABRICATION.** Assembly: **DEFERRED / NOT ASSEMBLED**. These are instructions for a later authorized assembly phase; they are not records of work performed.

Use the native PCB, its Fab/reference layers, [per-reference BOM](../exports/draft/bom_per_reference.tsv), [footprint review](footprint_review.md), [power circuit](power_circuit_spec.md) and [enable circuit](enable_interface_spec.md) together. Renders illustrate nominal placement and do not show actual solder joints. Project-authored models simplify SW1, the F1 fuse (6.10 × 2.69 × 2.69 mm nominal), and C1/C2 (10 mm diameter × 20 mm nominal height, 5 mm pitch). They illustrate nominal envelopes and polarity; they do not certify tolerance or fit. U4/U5 generic bodies do not certify their exact underside geometry. Manufacturer/package pin1 markings govern placement; a generic pick-and-place rotation convention is not sufficient.

## Orientation and polarity

| References | Required inspection |
| --- | --- |
| U1/U2 | Toshiba SSOP24 pin1 matches the local footprint triangle/chamfer. All duplicate physical terminals must be soldered. There is no exposed thermal pad. Never bridge adjacent separate outputs. |
| U3/U6 | TSSOP14 pin1 marker matches the Fab outline. Confirm exact LVC07 versus LVC11 MPN before placement. |
| U4 | DRB8 pin1 and ground exposed pad9 follow the local footprint drawing. Review stencil aperture and thermal-pad solder coverage before assembly; the render cannot establish them. |
| U5 | Use the custom TI_DCU0008A footprint with the DCUR package. Inspect 0.5 mm pitch for bridges. |
| U7–U12 | Several distinct SOT pinouts coexist. Match each reference to its exact MPN; do not interchange identical-looking packages. |
| Q1/Q2 | Q1 is P-MOS pin1G/2S/3D; Q2 is NPN pin1B/2E/3C. Marking similarity does not imply interchangeable pin functions. |
| D1 | Cathode band/pad1 faces REV_PROTECTED; anode/pad2 faces FUSED_IN. |
| D2 | Cathode band/pad1 to VM; anode/pad2 to GND. Use the unidirectional A suffix, not a bidirectional CA replacement. |
| C1/C2/C3/C5/C7/C9 | Electrolytic positive lead to square/positive pad1; negative stripe to ground pad2. Check 25 V rating. C1/C2 nominal 20 mm body length can reach 22 mm from tolerance before board stand-off. Do not use the render as enclosure clearance approval. |
| F1 | Nonpolar fuse; confirm 2 A marking and body size. It is not a resettable PTC. |
| SW1 | Pin2 is common PHYS_RAW; pin1 is ENABLE through PHYS_SUPPLY; pin3 is INHIBIT/GND. Verify actuator direction and silk labels from the actual switch drawing. |
| J1–J5 | J1.1 positive motor source, J1.2 ground. J2/J3/J4/J5 are FL/FR/BL/BR output pairs respectively. Motor connectors carry two switched outputs; neither conductor is ground. |
| J6 | Key/notch and pin1 marker follow the project IDC footprint. The 16-pin mapping is a custom cable interface, not a Pi header pinout. Verify each conductor independently. |

All listed SMD components are intended for top-side placement, followed by the radial capacitors, axial R5 and through-hole connectors using a reviewed soldering process. Temperature profiles must satisfy the most restrictive component/package requirement. No reflow profile, solder alloy, stencil thickness, paste reduction, assembly-house capability or minimum-order arrangement is approved in this phase. Do not indiscriminately reflow the radial electrolytics or assume the through-hole header is reflow-qualified.

Inspect the local SSOP and DCU footprints' tolerance exceptions before fabrication release. Inspect polarity, package markings, bridges, unsoldered duplicate driver pins, through-hole fill and the U4 exposed-pad process after a future assembly. SW1's silver contacts carry a small logic current; contact reliability must be checked under the intended environment. Keep connector insertion loads off unsupported solder joints and provide cable strain relief in the later mechanical design.

Do not fit components to TP1–TP10: they are copper probe pads. H1–H4 are non-plated holes; screws/standoffs are outside this BOM, and conductive hardware requires a separate copper-clearance/mechanical review. Cables, motor polarity and external source/disconnect equipment remain unverified.

A future first power-up follows the deferred [bring-up procedure](../validation/bring_up.md) and the stricter reference power sequence: initially inhibit motion, supply Pi logic, charge VM with a 0.10 A source limit, verify VM_OK and rail levels, and only then raise the source ceiling for the permitted motor profile. On shutdown keep Pi logic present until motor input is off, mechanics stop, at least 5 seconds have elapsed and measured VM is below 0.3 V. No assembly inspection or power test has been performed here.
