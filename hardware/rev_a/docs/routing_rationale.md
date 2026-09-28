# Routing and return-path rationale — final 12 V draft

**DRAFT — NOT RELEASED FOR FABRICATION.** Native KiCad 10.0.6 geometry was read after final zone fill. [Detailed inventory](../validation/design/routing_geometry.md) and [machine-readable paths](../validation/design/routing_geometry.json) identify the exact PCB hash. The calculations below are desk screens, not measured ampacity, temperature, inductance or EMC.

## Placement and board size

The 100 × 100 mm, two-layer, 1 oz outline is provisional. It expands the old 100 × 80 mm reference to accommodate four driver packages and their local thermal copper, the eFuse/reverse-blocking stage and larger 50 V bulk cans. It is not a minimum-size claim or a verified chassis fit. Two layers keep the design and fabrication requirements understandable; they also constrain return routes and copper spreading. The selected filled/capped-hole process adds complexity even though the board has only two copper layers.

J1 enters the fuse/reverse-block/eFuse path. Four separate motor output pairs reach J2–J5; outputs are never tied together. Left/right command pairing occurs in logic. The separately supplied Pi connects only logic and the common reference through J6. Motor return must remain in the board/source wiring, not the Pi cable. Actual two-pack wiring remains unknown.

## Actual current-path geometry

| Current path | Saved geometry and role |
| --- | --- |
| J1.1 → F1.1 | 3.00 mm × 39.55 mm on F.Cu; aggregate input current |
| F1.2 → Q1 sources | 2/1 mm trunk sections; each 0.40 mm terminal escape is 1.065 mm, with short 0.60 mm joins where present; three source pads connect |
| Q1 drain → U13 IN1/IN2 | 1.50 mm trunk for 7.024 mm; short 0.80/0.60 mm spreading links; individual 0.30 mm terminal paths 0.7375 and 1.2375 mm |
| U13 OUT17/OUT18 → VM bus | Individual 0.30 mm escapes are 1.6375 mm, then 1.20 mm copper and two 0.80/0.30 mm vias into 3.00 mm B.Cu distribution |
| VM distribution → each driver | 1.00 mm branches and 0.40 mm × 1.90 mm final lead fanout; four separate driver feeds, with local capacitors |
| Each motor output | 0.80 mm main conductor; 0.40 mm lead fanout of 1.30 mm or 2.0814 mm. Total pad-to-connector paths are 11.30–24.13 mm; power layer transitions use 0.80/0.30 mm vias |
| Low-current sensing/support | FUSED_IN includes 0.20 mm routing to U13 VSNS, and EFUSE_IN includes a 0.2402 mm support segment. Their shared net names do not make these the aggregate-current trunk |

The longest motor 0.40 mm escape is explicitly 2.0814 mm, not rounded down to 2 mm. At the 1 A conductor screen it adds about 3.18 mΩ and 3.18 mW. The stricter 2 mm provisional eFuse-escape target is met by all four IN/OUT terminal paths. The JSON separates connected narrow-run sums from actual individual paths and distinguishes sensing branches from motor-current flow.

At 35 µm copper, resistivity 1.724×10⁻⁸ Ωm and a 1.24 hot-resistance multiplier, the actual input trunk screens at 8.052 mΩ: approximately 26.7 mV/88.3 mW at 3.311 A. Motor output candidate paths, including a single via where used, screen at approximately 11.1–21.0 mΩ each; at 1 A that is 11.1–21.0 mV and mW per conductor. The calculation assumes 1.6 mm board thickness and 25 µm via-barrel plating. It excludes solder/contact resistance, pad spreading, transient heating and fabrication tolerances.

The audit selects a trace/via path; it does not solve parallel current sharing. For example, one route through an eFuse terminal does not imply that terminal carries every ampere by itself, nor prove equal sharing. Likewise an eFuse-to-driver path contains both aggregate trunks and a single-driver branch: applying 1 A or 3.31 A uniformly to every segment would be misleading. Normal input remains limited by the provisional ≤2 A allocation; current-limit tolerance and short-fault overshoot are separate cases.

## Ground, bypass and heat spreading

Two filled GND zones cover about 7457 mm² on F.Cu and 7523 mm² on B.Cu before small rounding differences. Multiple polygons and stitching/thermal connections form a common net; there is no intentional split ground. The bridge power grounds connect to the exposed-pad ground structure. Inspect the real filled copper rather than treating an unrouted ratsnest or a net label as a return path.

Each driver has a VM ceramic about 3.24 mm pad-center distance from VM; the saved positive trace path is 3.415 mm. CPH/CPL flying-capacitor paths remain local at approximately 2.94–6.28 mm per leg. VCP reservoir traces are about 10.73–12.18 mm, and their VM-side paths about 9.97–15.33 mm. These actual routes are longer than straight-line distances; no minimum-loop-inductance or waveform qualification is claimed.

The trace-only audit exposed an unnecessarily indirect U20 ceramic-ground connection. An explicit 0.40 mm local return with two 0.60/0.30 mm vias now gives a 12.05 mm trace/via route to PGND. U21–U23 capacitor/PGND pairs share the same saved F.Cu ground polygon; their much longer trace-only graph routes exclude the intervening plane and must not be presented as the physical return lengths. Same-island membership still does not quantify high-frequency impedance. The next physical phase must measure local rail ringing and ground movement at the IC, including maximum PWM/current-chopping conditions.

Each DRV exposed pad has four 0.30 mm thermal holes. Saved GND zone area in a 20 × 20 mm window around each driver is approximately 228–264 mm² on the front and 199–275 mm² on the back. Two-layer totals exceed the initial 400 mm² area heuristic, but windows overlap slightly and copper is shared: those totals are not independent heat sinks. The effective ≤80°C/W thermal target and four-driver temperature rise remain unverified. Exposed-pad solder coverage, copper continuity, surrounding components, enclosure and airflow matter.

## Vias, solder process and verification limits

Main current transitions use 0.80/0.30 mm vias. Fine signal/sense and the added local ceramic-return transitions use 0.60/0.30 mm vias. Both use the same provisional 0.30 mm drill/25 µm barrel basis; annular geometry and fabrication tolerances require qualification. There are 191 routed vias in the final board, plus component and thermal plated holes.

The actual hole/paste polygon check selects **13 holes** for **filled, capped and planarized** treatment: four U13 thermal holes and nine routed vias beneath or intersecting component paste. Use the [coordinate map](../exports/draft/drills/selective_via_fill_map.csv), [intersection report](../validation/design/selective_via_fill_review.json) and [fabrication notes](fabrication_notes.md). The sixteen DRV thermal holes remain outside paste, with minimum hole-edge spacing 0.275 mm, and retain their specified tenting. Ordinary tenting is not a substitute for the mapped fill/cap process.

Native ERC/DRC, connectivity and schematic parity pass for the recorded final source. These checks do not prove capacitor ripple sharing, TVS clamp overshoot, reverse-fault behavior, thermal performance, starting torque, motor stall protection, EMC or physical compatibility. No board was fabricated, assembled or operated. Manufacturing exports remain drafts.
