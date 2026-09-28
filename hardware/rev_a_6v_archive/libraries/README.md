# Project-local KiCad libraries

The native project uses local symbol and footprint tables and `${KIPRJMOD}` model references. Preserve this directory with the schematic/PCB when moving or opening the design in KiCad 10.0.6.

- `AI_Robot.kicad_sym` contains the project symbols, including manufacturer pin-number mappings and passive/connector symbols.
- `AI_Robot.pretty` contains reviewed custom footprints for Toshiba TB6612FNG SSOP24, TI TPS3431 DRB8, TI DCU0008A, Würth 61201621621, and the Littelfuse 451 fuse.
- Other `.pretty` directories are project-local copies of footprints from the official KiCad 10.0.6 bundle. The capacitor and switch entries bind project nominal models where the generic model differed from the selected part's envelope.
- `3dmodels/` includes the copied KiCad STEP models and project-authored nominal VRML models. Read [their limitations](3dmodels/README.md); visual appearance is not manufacturer mechanical approval.

KiCad-library content is redistributed under the bundled [KiCad library license](LICENSE_KICAD.md), with its attribution and exception. Custom project content is identified in the footprint/model review. The [final artifact hash manifest](../validation/design/artifact_hashes.json) identifies the exact local files used; the project does not depend on a future remote library update.

The [footprint review](../docs/footprint_review.md), [enable-interface review](../docs/enable_interface_spec.md), [header check](../validation/design/header_native_check.json), [schematic parity check](../validation/design/schematic_parity.json) and [final electrical board comparison](../validation/design/electrical_board_review.json) document numbered-pin/pad checks. All 107 schematic items were compared with the board; four mounting holes are explicitly board-only. Supplier variants, fabrication tolerances, stencil/reflow details and connector mating fit require later review. None of these libraries is a fabrication release.
