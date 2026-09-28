# Rev A — completed 12 V design-only milestone

**2026-09-28 — DESIGN-ONLY MILESTONE COMPLETE.**
**DRAFT — NOT RELEASED FOR FABRICATION.**
**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**

The native project now contains four DRV8874 drivers, revised 9–15 V reference power input with eFuse/reverse blocking and transient protection, 121 fitted placements, 14 copper testpoints, seven schematic sheets and a provisional 100 × 100 mm two-layer board. The [frozen 6 V archive](../rev_a_6v_archive/ARCHIVE_NOTICE.md) preserves the original design and review finding without inventing a hardware failure.

Actual final checks: **ERC 0; DRC 0; unconnected 0; schematic parity 0**. Native pin/footprint/logic and BOM/placement/Gerber/drill/model comparisons passed. The final PDFs, layout images and native 3D render were visually inspected. See the [check report](validation/design/design_check_report.md) for exact hashes, rule exceptions, actual counts and evidence limits.

A separate offline software rerun passed all **132** existing cases. Original report/JUnit bytes remain unchanged. No test operated motors, battery, Pi GPIO, camera or other robot hardware. The new hardware handshake has no real GPIO backend. The 22-case physical plan remains unexecuted.

The latest user instruction authorizes commit/push to the existing GitHub repository. Publication identifies this completed design-only snapshot; Git history and the task's separate receipt identify the actual commit and remote result. It is not a fabrication release.

**Fabrication: DEFERRED / NOT BUILT. Assembly: DEFERRED / NOT ASSEMBLED. Physical validation: NOT TESTED. Proposed-PCB integration: NOT TESTED.**

Future release work requires the physical motor label, battery voltage/topology/protection, actual harness and Pi supply, switch/E-stop wiring, mechanical constraints, required starting torque and supplier acceptance of selective filled/capped/planarized holes. Current source/current/energy/temperature limits remain visible assumptions in the [electrical specification](docs/reference_electrical_spec.md). Passing CAD checks does not resolve those assumptions.
