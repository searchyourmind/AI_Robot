# Native KiCad workflow

The design uses the official **KiCad 10.0.6** macOS bundle in the task's workspace. No global installation or security-policy modification was required. The project has seven native schematic sheets and a native two-layer PCB. Keep the complete project and `libraries/` together: symbol, footprint and model tables use `${KIPRJMOD}`.

The [command log](../validation/design/command_log.json), [tool version](../validation/design/tool_version.txt) and [check report](../validation/design/design_check_report.md) record actual tool operations. Native command-line loading, export, checking and rendering provide the evidence; no interactive GUI session is claimed.

## Recheck the delivered source

From `hardware/rev_a`, with KiCad 10.0.6 on PATH:

```sh
kicad-cli sch erc --format json --severity-all --exit-code-violations -o validation/design/erc_recheck.json ai_robot_interface.kicad_sch
kicad-cli sch export netlist --format kicadxml -o validation/design/netlist_recheck.xml ai_robot_interface.kicad_sch
kicad-cli pcb drc --format json --schematic-parity --severity-all --exit-code-violations -o validation/design/drc_recheck.json ai_robot_interface.kicad_pcb
```

The project enables all native DRC rule classes, with no marker exclusions. ERC excludes only SPICE-model validation because simulation is outside this milestone. A zero result applies only to the saved input files and those rules; it is not a simulation or hardware test.

The [read-only audit scripts](../validation/tools/README.md) are included with explicit-path recheck commands for native consistency, exported geometry and the selective hole/paste process map. Use a new scratch output directory so the recorded final evidence stays intact.

## Authoring and review

A manifest specifying every pin generated native symbols and sheets with deterministic identities, explicit NC markers and a separate hierarchy-path map. Native `pcbnew` loaded reviewed local footprints, assigned every numbered pad, placed 135 electrical items plus four board-only holes, and created the 100 × 100 mm outline. Power trunks and fine-pitch power escapes were explicitly prepared. Freerouting 2.4.1 supplied candidates through DSN/SES exchange. The router was invoked locally with analytics disabled (`-da`); its stored configuration template alone is not evidence of that per-run flag.

Final native DRC/parity and the independent manifest → XML → physical-pad checks are authoritative. Ground zones are refilled before checking. Routing candidates and the manually prepared power paths are intermediate work, not replacements for final deliverables. The [routing rationale](routing_rationale.md) and actual width/length inventory distinguish wide current trunks from short IC pad escapes. No rule is ignored merely to make the reported count zero.

## Exports

The final export step produces a native schematic PDF, top/bottom copper PDF, assembly PDF, top and mirrored-bottom SVG/PNG views, eight Gerber layers, separate plated/nonplated Excellon drills with maps and a report, a placement CSV, and an actual KiCad 3D render. Assembly and layout PDFs are review plots; native coordinates, Gerbers and drills control geometry. The copper PDF views both layers from above; the separate bottom image is mirrored to show the underside.

The 3D model is a visualization with nominal package bodies, not a physical photograph or proof of enclosure clearance. PDF and image inspection is recorded separately from command success. The runtime may print a Fontconfig warning; successful parsing/export and visual inspection must still be checked.

The frozen [old 6 V artifacts](../../rev_a_6v_archive/ARCHIVE_NOTICE.md) have separate hashes and check reports. Old zero-error results do not transfer to new CAD. Physical work remains deferred and the board is not released for fabrication.
