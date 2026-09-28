# Draft export package

**HOLD: 6 V REFERENCE — DIRECT 12 V INPUT INCOMPATIBLE.** All CAD-derived files in this directory preserve the original 5.5–6.5 V reference and have not been regenerated for the purchased 12 V system. Read the [12 V impact review](../../docs/12v_design_impact.md). A filename, clean CAD report or 25 V capacitor rating does not qualify the assembled circuit for 12 V.

**DRAFT — NOT RELEASED FOR FABRICATION.**
**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**

This folder contains design-review outputs only. No manufacturer acceptance, quote, purchase, fabrication, assembly or physical validation is implied. Actual export/check status is recorded in the project progress and validation reports; the presence of an export does not establish electrical safety or physical operation.

- [Schematic PDF](schematic.pdf): five native schematic sheets.
- [PCB layout PDF](pcb_layout.pdf): F.Cu then B.Cu, viewed from above, scaled 1.45:1.
- [Top assembly drawing](assembly_top.pdf): two monochrome pages (fabrication outlines and silkscreen), scaled 1.45:1.
- [Top layout PNG](views/pcb_top.png) and [mirrored bottom layout PNG](views/pcb_bottom.png), with editable vector SVG companions.
- [Actual KiCad 3D render](views/kicad_3d_render.png): rendering only, not a board photograph.
- `gerbers/`: eight native plots (F.Cu, B.Cu, F.Paste, F.Mask, B.Mask, F.SilkS, B.SilkS, Edge.Cuts). No bottom-paste layer is needed for this all-top assembly.
- `drills/`: separate plated/nonplated Excellon files, SVG maps and [drill report](drills/drill_report.txt).
- [Draft placement data](placement_all.csv): 97 top-side fitted parts including THT; not an assembler-specific SMD upload. Millimetres, native KiCad angles, origin at the board bottom-left; X increases right and Y up.
- [Grouped candidate BOM](bom_reference.tsv): board components, real manufacturer part numbers and source links.
- [Per-reference candidate BOM](bom_per_reference.tsv): one row per fitted component for CAD/assembly comparison.
- [Off-board connector candidates](bom_offboard_candidates.tsv): mating plugs, kept outside the board assembly count.
- [Historical early BOM worksheet](bom_candidates.csv): retained pre-reference audit record containing unresolved TBD rows; do not merge it into the current BOM or treat it as the assembled-board bill.

TP copper and mounting-hole features are excluded from purchased components. Read the [BOM review](../../docs/bom_review.md), [assembly notes](../../docs/assembly_notes.md), [fabrication notes](../../docs/fabrication_notes.md) and [routing rationale](../../docs/routing_rationale.md) with the native project. Exported placement rotations and origins require package-specific assembly review before any future use.

Fabrication: **DEFERRED / NOT BUILT**. Assembly: **DEFERRED / NOT ASSEMBLED**. Physical validation: **NOT TESTED**. Integration with the proposed PCB: **NOT TESTED**.

The drill data contains 145 plated holes (105 vias and 40 component holes) and six nonplated holes (four mounting holes and two switch locating holes). The auxiliary origin is native (50,130) mm; the Edge.Cuts centreline is 100 × 80 mm. Native centre coordinates and rotations need package-specific assembler review. The [export consistency report](../../validation/design/export_consistency.json) and [artifact hashes](../../validation/design/artifact_hashes.json) identify this exact draft. A historical candidate worksheet is retained but excluded from the current manufacturing counts.
