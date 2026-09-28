# Final design-only check report

**DRAFT — NOT RELEASED FOR FABRICATION.**
**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**

This record closes the pre-fabrication reference-design milestone. It reports digital checks and design reviews only. The complete native project and exports remain conditional on the accepted reference envelope plus the explicitly derived supply/energy/sequencing restrictions.

| Actual operation | Tool / evidence | Observed result |
|---|---|---|
| Native schematic loading and ERC | KiCad 10.0.6, [erc_final.json](erc_final.json) | Exit 0; 5 sheets; 0 violations across errors, warnings and exclusions |
| Native PCB loading and DRC | KiCad 10.0.6, [drc_final.json](drc_final.json), [text report](drc_final.rpt) | Exit 0; 0 violations |
| Connectivity | Same native DRC, filled F.Cu/B.Cu ground zones | 0 unconnected items |
| Schematic-to-PCB parity | Same native DRC with `--schematic-parity` | 0 mismatch items |
| Entire netlist versus reviewed manifest | [schematic_parity.json](schematic_parity.json) | 107 components; 322 package pins; 60 connected nets and 2 explicit isolated NC nets; exact membership/metadata comparison passed |
| Native numbered-pad and footprint comparison | [electrical_board_review.json](electrical_board_review.json) | All 107 schematic references match; 4 additional board-only mounting holes; no trace below 0.20 mm |
| BOM and placement | [export_consistency.json](export_consistency.json) | 97 fitted components, 33 distinct MPNs, 97 top-side placement rows; values/packages/MPNs/refsets reconciled with native netlist |
| Gerber/drill exports | Native KiCad logged exports and [drill report](../../exports/draft/drills/drill_report.txt) | 8 Gerber layers; 145 PTH holes (105 vias + 40 component holes); 6 NPTH holes (4 mounting + 2 switch locating) |
| Embedded 3D paths | Export consistency check | 97 model bindings, 20 distinct paths; all resolve using project-relative paths |
| Native PDF/image exports | [command log](command_log.json), [schematic checks](schematic_checks.json), [visual QA](visual_qa.json) | 5-sheet schematic PDF, 2-page copper layout PDF, 2-page assembly PDF, top/bottom SVG/PNG and actual KiCad 3D render |
| Prior software evidence integrity | Export consistency check | Both original report fingerprints unchanged; 132 historical mock cases remain software-only evidence |

## Input identity and traceability

- Native PCB SHA-256: `2a5c00e9b49f78fa7a03420b92d5be16abc4048dd8b17c995c770ec7048457ce`
- Native project/rules SHA-256: `ca8080f0a7f51607089c6b9204283a091f8c83fa7d4565e9fe0fa4d947a64eaf`
- Native schematic root SHA-256: `c02547a42ac1d7aeda9f1fde1ed43a79e3ed2d62783815e6b6b09aba61865646`
- Exact final CAD, local libraries, documents, exports and evidence are listed in [artifact_hashes.json](artifact_hashes.json).

The [command log](command_log.json) preserves actual invocations, exit codes, stdout and stderr; later entries supersede earlier plot/display trials. Source hashes in earlier schematic/logic reviews identify their specific review snapshots. The final artifact manifest and final ERC/DRC are authoritative for the delivered files. No successful interactive GUI launch is claimed: native CLI/API loading and operations succeeded. The supported [reproduction workflow](../../docs/cad_workflow.md) explains how to open and check the project locally.

## Check configuration and reviewed corrections

Final DRC has an empty ignored-check list and no marker exclusions. Five initially default-ignored classes were enabled in a separate copy, passed, then enabled as warnings in the delivered project: footprint filters/types, missing courtyard, via centering and tuning geometries. See the [supplemental rule review](drc_default_rule_review.md). ERC ignores only `simulation_model_issue`, because no SPICE models or circuit simulation are in scope; no ERC marker exclusion conceals a circuit warning.

During CAD review, corrected findings included fuse clearance, undersized autorouter signal segments, the final VM connection and removal of a direct Pi STBY feedback branch. J6.15 is now GND; TP10 carries STBY for probing. The corrected final state was checked again. These are design revisions within this session, not measured Rev A-to-Rev B improvements.

Visual QA changed only export presentation/model meshes: the assembly drawing separates fabrication outlines and silkscreen into two pages to avoid duplicate reference overlays; plots use 1.45:1 review scale with clear title blocks; the 3D camera includes the whole board and the nominal bulk-capacitor mesh loads correctly. Copper/layout geometry was unchanged by these presentation fixes. The 3D render is not a photo, package-fit proof or physical evidence.

## Design evidence boundaries

Manufacturer-based package/pin reviews, Boolean desk checks and hand calculations are documented in the circuit/footprint/electrical reviews. They are neither circuit timing simulation nor independent hardware testing. The [electrical layout review](../../docs/electrical_layout_review.md) and [reference operating specification](../../docs/reference_electrical_spec.md) retain the following material limits:

- The actual motors, stall/startup current, battery/protection, harness/polarity and chassis constraints remain unknown.
- Initial charging, source current/cutoff, regenerative-energy and controlled power-down limits must hold. Abrupt loss of Pi logic with charged VM is an unresolved partial-power condition. The fuse is not per-motor current limiting.
- Local/bulk capacitor ripple sharing at the 1 kHz reference PWM rate requires further analysis before fabrication release and later authorized measurement; motor RMS current alone does not validate capacitor ripple.
- Hot losses, junction temperature, watchdog timing/fault response, EMC, supply transients, mechanical fit, stencil/reflow and finished copper/plating tolerances are not physically verified.
- New RUN/ARM/heartbeat signaling is not integrated into a physical GPIO backend. The earlier Python mock timeout tests do not validate the hardware watchdog or physical disable path.

Fabrication: **DEFERRED / NOT BUILT**. Assembly: **DEFERRED / NOT ASSEMBLED**. Physical validation: **NOT TESTED**. Integration with proposed PCB: **NOT TESTED**. Blank test records remain blank; no scope captures, measurements or physical PASS results were created. No vendor contact, order, quote, push, deployment or release occurred.
