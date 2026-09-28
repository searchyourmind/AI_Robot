# Draft 12 V design exports

**DRAFT — NOT RELEASED FOR FABRICATION.** **NOT VERIFIED FOR THE EXISTING ROBOT.**

The current source is a provisional single-source 9–15 V, four-DRV8874 design. Actual battery limits/topology, motor identity, GPIO harness and chassis fit remain unresolved. The previous 6 V CAD and exports are in the separate archive; do not mix files between revisions.

- [Schematic PDF](schematic.pdf): seven editable-source sheets plotted by KiCad.
- [PCB copper PDF](pcb_layout.pdf): front/back layers, both viewed from above.
- [Assembly PDF](assembly_top.pdf): separate fabrication and silkscreen pages; use both with the BOM.
- [Fitted BOM](bom_fitted.csv), [grouped BOM](bom_grouped.csv), [copper testpoints](bom_testpoints.csv): 121 fitted placements, 43 MPN groups, 14 unpurchased copper features.
- [Placement CSV](placement_all.csv): all fitted references, mm, top side, lower-left board origin. Vendor rotation and package acceptance are unqualified.
- [Top view](views/pcb_top.png), [mirrored bottom](views/pcb_bottom.png), [actual KiCad 3D render](views/kicad_3d_render.png): CAD review images, not hardware photographs.
- `gerbers/`: front/back copper, front paste, front/back mask, front/back silk and outline.
- `drills/`: separate plated/nonplated Excellon holes, maps and a drill report. The [selective fill coordinate map](drills/selective_via_fill_map.csv) marks 13 under-paste holes requiring filled/capped/planarized processing, including TPS26630 thermal holes and routed vias. Ordinary open or merely tented holes are not equivalent.

The board is provisionally 100×100 mm, two layers, 1 oz copper. Nominal models do not establish installed height clearance. Read [fabrication notes](../../docs/fabrication_notes.md), [assembly notes](../../docs/assembly_notes.md), [electrical limits](../../docs/reference_electrical_spec.md) and [actual check report](../../validation/design/design_check_report.md). A clean CAD result is not a release approval.

No board was fabricated, assembled or physically tested. No vendor was contacted and no order was placed. GitHub publication shares draft design evidence only.
