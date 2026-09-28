# Project-local KiCad libraries

Keep this directory with the project. `sym-lib-table` and `fp-lib-table` resolve libraries via `${KIPRJMOD}`. Exact reference/MPN/pin nets are defined in the schematic and validated against the final manifest/netlist/board. Standard footprints/models were copied from KiCad 10.0.6; AI_Robot custom footprints cover documented package-specific geometries.

The current custom high-current packages are DRV8874PWP0016J, TPS26630RGE0024H and CSD19537Q3. See the [footprint review](../docs/footprint_review.md), including the TPS26630 filled/capped/planarized thermal-hole requirement. Repeated-number thermal pads are intentional. Empty-number aperture pads carry mask/paste geometry only.

[3D model limitations](3dmodels/README.md). Unused historical library entries, if present, are not BOM parts or evidence of fitted devices. The active PCB/netlist/BOM determine population. The 6 V source remains separately archived.

[Third-party library attribution and retained licenses](../../third_party/README.md).
