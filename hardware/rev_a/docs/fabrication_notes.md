# Fabrication notes — 12 V redesign

**DRAFT — NOT RELEASED FOR FABRICATION.** Fabrication: **DEFERRED**. Assembly: **NOT ASSEMBLED**. Physical validation: **NOT TESTED**. Updated 2026-09-28 for the provisional 12 V redesign; the former 6 V files are preserved in `hardware/rev_a_6v_archive`.

No fabrication or assembly vendor has been selected or contacted. No quote, purchase or physical process approval is represented by these notes.

## Board and process requirements

| Item | Current design requirement | Remaining qualification |
| --- | --- | --- |
| Outline | **100×100 mm** rectangle, expanded from the archived 100×80 mm reference | Actual chassis, mounting and cable clearance remain unverified |
| Copper layers | Two: F.Cu/B.Cu; nominal 1 oz /35 µm | Confirm finished copper, etching tolerance and local copper loss |
| Thickness and material | Provisional 1.6 mm FR-4 | Select laminate/Tg, thickness tolerance and process stack-up |
| Ordinary spacing | 0.20 mm net-class clearance; 0.20 mm minimum track width | Confirm achievable finished geometry |
| Local spacing exception | Q1 exact TI source/gate pattern uses **0.15 mm** copper gap; board absolute minimum is 0.15 mm | This documented local exception does not reduce every route's 0.20 mm clearance target |
| Copper to edge | At least 0.50 mm | Verify final outline, machining tolerance and mechanical hardware |
| Routed vias | 0.80/0.30 mm for power transitions; 0.60/0.30 mm for signal/sense and the local U20 ceramic-return transitions | At least 25 µm barrel plating is the electrical calculation assumption; finished drill/plating require agreement. Vias intersecting paste require the selective process below |
| Thermal plated holes | Four 0.60/0.30 mm holes per DRV8874 and four per TPS26630 | Package-specific treatment below; these are plated ground connections, not NPTH mounting holes |
| Mounting | Four 3.2 mm non-plated holes | Fasteners and standoffs are not purchased BOM components; fit is unverified |
| Solder mask | Top and bottom; explicit local mask geometry in custom footprints | Q1 nominal mask web 0.10 mm; DRV lead web 0.14 mm; QFN lead web 0.20 mm. Registration must be reviewed |
| Silkscreen | Function, polarity, pin-1 and connector identification | Keep off solderable pads; do not rely on color for safety or identification |
| Finish | Not selected | Must support the 0.5 mm-pitch QFN and exposed-pad planarity requirements |
| Panel, stencil and tooling | Not selected | No panel rails, fiducials, stencil thickness or tooling are approved |

## Selective hole treatment is mandatory

**U13 TPS26630:** four 0.30 mm plated holes at footprint-relative x/y=±0.70 mm lie beneath exposed-pad paste. Require **filled, capped and planarized holes** compatible with the chosen finish and solder process. Ordinary open vias or an unspecified tenting substitution are not accepted for this design. The Gerber/drill data alone do not encode a qualified fill material, cap thickness or planarity tolerance; these manufacturing notes and a later agreed process specification must accompany a release.

**All routed via holes intersecting solder-paste apertures require the same filled, capped and planarized process.** This includes holes under component lead/resistor pads as well as thermal pads. The final [selective process coordinate map](../exports/draft/drills/selective_via_fill_map.csv) identifies each selected feature by component association, net, UUID, native/export X/Y coordinates, drill dimensions and layer. The [native polygon-intersection report](../validation/design/selective_via_fill_review.json) records the exact source PCB hash and actual aperture intersections. The final list contains 13 holes: four U13 thermal holes and nine routed vias. The selected list must be regenerated after any routing, pad, drill, paste or footprint change; it is not limited to the four U13 holes.

Supply this coordinate map with the matching Gerbers, plated drill file and these notes. Ordinary tenting does not satisfy the specified fill/cap/planarity process, and a via tenting setting does not negate an overlapping component pad opening. Before a later release, obtain explicit fabricator/assembler agreement on fill material, cure, copper cap/plating, finish, planarity, cleaning and inspection acceptance. No supplier has accepted this process, and the additional complexity and cost are **unquoted**. This is a deferred process requirement, not fabrication authorization. TI discusses the underlying solder-loss mechanism in its [PowerPAD assembly guidance](https://www.ti.com/lit/an/slma002h/slma002h.pdf).

**U20–U23 DRV8874:** four 0.30 mm plated holes per device are placed at x=±0.70 mm, y=±2.20 mm, outside the central paste aperture. Both sides are tented in the current footprint. The nearest hole edge is 0.275 mm from the paste opening. This is a project-selected thermal-hole array, not a claim that TI prescribed these coordinates. Confirm tenting integrity and solder-wicking control. Changes to hole treatment or paste geometry require a new footprint/process review.

U4's inherited watchdog exposed pad and Q1's drain land also need stencil/solder-joint review. Q1's large exposed metal is **EFUSE_IN**, not GND. No solderable land should be converted to a drill merely because it appears as a thermal feature in a render.

## Power copper and final export checks

The current routing plan uses 3 mm MOTOR_IN/main VM copper, 2/1 mm FUSED_IN sections, a 1.5 mm EFUSE_IN trunk, 1 mm VM branches and 0.8 mm motor routes. Short package escapes are 0.40 mm at Q1/DRV leads and two 0.30 mm paths at eFuse input/output pairs; the output expands through 1.2 mm copper and paired 0.80/0.30 mm vias into the main VM bus. The [final geometry inventory](../validation/design/routing_geometry.md) records the actual widths, lengths and branch roles. Long aggregate-current 1 mm sections must be assessed by actual length; a class name alone does not establish current capability. See [power_path_review_12v.md](power_path_review_12v.md).

Before any later release, generate exports from the final saved native board and reconcile outline, copper, solder mask, paste, plated/NPTH drills, origin and component placement. Do not mirror output layers manually. Exports remain in `exports/draft/`; a render or PDF is not a fabrication layer. Verify every plated thermal hole remains in the plated drill data, and every H1–H4 hole remains non-plated.

Reconcile every selective-process map row to the plated drill coordinates using the stated export origin, and confirm that the map's PCB hash matches the released native board. The drilling file continues to contain the selected holes; filling is a later manufacturing operation, not deletion from the drill data. Verify the sixteen DRV8874 thermal holes remain outside paste and retain their separately specified tented treatment.

The new complete-board ERC, DRC and schematic/PCB parity results must be read from their actual final reports. The isolated footprint geometry check does not establish whole-board connectivity. No unfinished check is reported as passed here. Even a clean final report does not qualify soldering, thermal performance, motor compatibility or an actual battery.
