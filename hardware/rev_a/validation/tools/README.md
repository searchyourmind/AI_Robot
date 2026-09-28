# Read-only verification scripts

These are the exact script snapshots used for the final native circuit, export and hole/paste checks. They write scratch evidence and do not save or refill the source PCB. Their original default paths describe the authoring workspace; **pass every path explicitly** when checking this delivered project. Do not overwrite the recorded final evidence with a local recheck.

Requirements: KiCad **10.0.6** Python with `wx` and `pcbnew`, its `kicad-cli`, and a separate Python environment with PyMuPDF and Shapely 2.x. Set the following paths to the local installation and a new writable scratch directory. From `hardware/rev_a`:

```sh
export ROBOT_KICAD_PYTHON=/absolute/path/to/kicad/python3
export ROBOT_KICAD_CLI=/absolute/path/to/kicad-cli
export ROBOT_REPORT_PYTHON=/absolute/path/to/python-with-pymupdf-and-shapely
export ROBOT_AUDIT_DIR=/absolute/path/to/new-scratch-directory

"$ROBOT_KICAD_PYTHON" validation/tools/verify12v.py --project-dir . --manifest validation/design/schematic_manifest.json --output-dir "$ROBOT_AUDIT_DIR/native" --cli "$ROBOT_KICAD_CLI" --stage routed
"$ROBOT_KICAD_PYTHON" validation/tools/check_exports12v.py --project-dir . --manifest validation/design/schematic_manifest.json --output-dir "$ROBOT_AUDIT_DIR/exports" --cli "$ROBOT_KICAD_CLI" --pdf-python "$ROBOT_REPORT_PYTHON" --retained-mock-dir validation
"$ROBOT_KICAD_PYTHON" validation/tools/check_via_paste.py --project-dir . --output-dir "$ROBOT_AUDIT_DIR/paste" --geometry-python "$ROBOT_REPORT_PYTHON"
```

The native checker compares manifest, fresh XML, pads, local footprint geometry, logic and routed DRC/parity. The export checker compares BOM, placement, models, Gerbers, drills and PDF inventory. Drill coordinates are matched one-to-one within half the 0.001 mm decimal export resolution; shorter decimal strings omit trailing zeros. The hole/paste checker uses transformed polygons and writes a selective fill map tied to the PCB hash.

A passing result is limited to these checks. It does not establish electrical correctness, thermal performance, assembly-process qualification or compatibility with the actual robot. Visual QA and analogue design reasoning remain separate. The native commands for ERC/DRC are in the [CAD workflow](../../docs/cad_workflow.md).
