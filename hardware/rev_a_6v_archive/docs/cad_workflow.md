# Native KiCad workflow and evidence

**DRAFT — NOT RELEASED FOR FABRICATION.**

The initial environment inspection found no KiCad in PATH or the inspected application directories. That blocker was resolved by running the official KiCad **10.0.6** macOS universal bundle from this task's `work/kicad_runtime/` directory. No global application installation, security-policy change or system library replacement was required. The actual [version output](../validation/design/tool_version.txt), [command log](../validation/design/command_log.json) and [final check report](../validation/design/design_check_report.md) are retained.

The editable project contains a five-sheet native schematic, routed two-layer native PCB, project-local symbols, footprints, and 3D models. Native KiCad schematic loading/ERC/netlist/PDF export and PCB loading/DRC/plot/render succeeded. An attempted GUI launch did not produce a usable window; no successful interactive GUI session is claimed. Open `ai_robot_interface.kicad_pro` in KiCad 10 for interactive editing. Keep the whole project directory together so `${KIPRJMOD}` library/model paths resolve.

## Reproduce the checks

Run from `hardware/rev_a/` with the supported `kicad-cli` 10.0.6 executable on PATH. Commands below are examples corresponding to the actual logged invocations; preserve prior reports if reviewing another revision.

```sh
kicad-cli version
kicad-cli sch erc --format json --severity-all --exit-code-violations -o validation/design/erc_final.json ai_robot_interface.kicad_sch
kicad-cli pcb drc --format json --schematic-parity --severity-all --exit-code-violations -o validation/design/drc_final.json ai_robot_interface.kicad_pcb
kicad-cli pcb drc --format report --schematic-parity --severity-all --exit-code-violations -o validation/design/drc_final.rpt ai_robot_interface.kicad_pcb
```

The final DRC has no ignored rule classes or marker exclusions. Five default-ignored classes were independently enabled and checked, then retained as warnings in the delivered project. ERC ignores only missing/invalid SPICE simulation models: no circuit simulation is claimed. All other reported ERC classes are active under KiCad's rules; no ERC markers are excluded. The independent numbered-pad/net/footprint comparison is recorded separately from native DRC.

## Placement and routing

Native pcbnew APIs loaded the project-local footprints, assigned reviewed numbered-pad nets, placed 107 schematic items plus four board-only mounting holes, created the outline and ground zones, and saved the native board. Freerouting **2.4.1** supplied routing candidates through KiCad Specctra DSN/SES exchange, locally with analytics disabled. Native DRC then drove manual corrections, including fuse clearance, minimum signal widths, removal of the former J6.15 STBY branch, and completion of VM routing. The delivered board, not an autorouter's success message, is the checked artifact.

High-current copper, source/return paths and the final via inventory have a separate [electrical board review](../validation/design/electrical_board_review.json). The [routing rationale](routing_rationale.md) distinguishes main trunks, branch currents and short package fanouts. Nominal geometry/rules are provisional; no selected vendor has reviewed them.

## Exports and visual review

Actual KiCad commands exported the schematic PDF, two copper-layer PDF pages, monochrome assembly drawing, top and mirrored bottom SVGs, eight Gerber layers, separate PTH/NPTH drills, drill maps/report, placement CSV, and a ray-traced 3D PNG. PDF/SVG rasterizations were used for visual QA. The layout PDF shows F.Cu then B.Cu, both viewed from above (unmirrored). The separate bottom PNG/SVG is mirrored to view the underside. PDF PCB plots use 1.45:1 review scaling; use native dimensions/drill data, not a printed image, for geometry.

The 3D image is a **KiCad render**, not a photograph or fit certification. Some included models are nominal approximations; see [model limitations](../libraries/3dmodels/README.md). Actual command exit codes/stdout/stderr, final hashes and export consistency checks are in `validation/design/`. A benign Fontconfig warning appeared on this local macOS runtime; successful output creation and visual inspection are recorded separately.

## Next review boundary

Design checks do not establish real motor compatibility, thermal performance, fault timing, mechanical fit or hardware/software integration. The existing robot's electrical/mechanical data remain unknown. Keep all manufacturing artifacts in `exports/draft/`. Fabrication, assembly and physical testing are deferred; no upload, vendor contact, order or publication occurred.
