# 12 V redesign — final design check report

**2026-09-28 — DESIGN-ONLY MILESTONE COMPLETE.**
**DRAFT — NOT RELEASED FOR FABRICATION.**
**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**

The seven-sheet native KiCad schematic, routed two-layer PCB, BOM and draft exports describe the new four-DRV8874 circuit. The following checks were actually run on the saved final source using **KiCad 10.0.6**. Clean CAD checks do not establish electrical correctness, real-robot compatibility or physical performance.

## Old versus new

| Item | Frozen 6 V reference | New 12 V reference |
| --- | --- | --- |
| Drivers | Two dual TB6612 devices | Four DRV8874 bridges |
| Source range | 5.5–6.5 V | Provisional 9–15 V |
| Fitted placements / MPNs | 97 / 33 | 121 / 43 |
| Schematic sheets | 5 | 7 |
| Board outline | 100 × 80 mm | 100 × 100 mm |
| Native ERC violations | 0 | 0 |
| Native DRC violations | 0 | 0 |
| Unconnected items | 0 | 0 |
| Schematic/PCB parity issues | 0 | 0 |

The [archived result](../../../rev_a_6v_archive/validation/design/design_check_report.md) remains tied to its old inputs. The incompatible 6 V assumption was discovered before fabrication; no physical failure is claimed.

## Checks performed and scope

- **Native ERC/DRC:** [ERC JSON](erc_final.json), [DRC JSON](drc_final.json), [readable DRC](drc_final.rpt), [commands and exit codes](command_log.json). All severities were requested. DRC ignores no rule class and has no exclusions. ERC omits only SPICE-model validation because no simulation was performed.
- **Independent native consistency: PASS.** 135 electrical components, 434 logical pins, 459 numbered physical pads, 85 connected nets, 15 explicit NCs and 135 local footprint instances reconciled across manifest, freshly exported native XML and PCB. Four mounting holes are separate. [Detailed comparison](independent_verification.json).
- **Logic desk review:** 32 Boolean command cases / 128 driver outcomes matched separately in each of the three representations. Independent wake, arm-clear, watchdog/fault connectivity, current-regulator pins and repeated power/ground pads were also inspected. This is not analogue or timing simulation. [Circuit audit](final_electrical_audit.md).
- **Saved routing:** 1572 track segments, 191 routed vias and 2 filled GND zones. Actual power widths, path lengths, local capacitor connections, thermal holes and ground-polygon areas are in [routing geometry](routing_geometry.md) and [routing rationale](../../docs/routing_rationale.md). Resistance/loss screens are assumptions, not measured ampacity or temperature rise.
- **Export consistency: PASS.** All 121 fitted references/43 MPN groups, 14 copper testpoints, placement coordinates/rotations, 121 fitted model bindings, eight Gerber layers and every native drilled feature were reconciled. Saved Gerber geometry matches a fresh native export after excluding creation-time comments only. [Detailed export evidence](export_consistency.json).
- **Visual QA: PASS within review scope.** All seven schematic, two copper-layout and two assembly PDF pages were rendered and inspected, along with top/bottom views and the actual KiCad 3D render. [Input hashes and observations](visual_qa.json). Nominal 3D bodies do not establish enclosure fit or solderability.
- **Manufacturing process map:** actual hole/paste intersections identify selective filled, capped and planarized holes. These are not ordinary tented holes. See [fabrication notes](../../docs/fabrication_notes.md) and the draft process map; supplier acceptance remains unqualified.
- **Software:** separate offline rerun **132 passed, zero failures/errors/skips**, retained in [new JUnit](mock_tests_rerun.junit.xml). Original [software report](../software_test_report.md) and [JUnit](../mock_tests.junit.xml) remain byte-for-byte unchanged. Tests are mock-only and do not validate the PCB or its new GPIO protocol.

## Exact input identity

| Final input | SHA-256 |
| --- | --- |
| Native PCB | `3eb423b15c766e0647403a8f4eb8eeb2b4a45bfc8c8c5f838797a18a8cf6e116` |
| KiCad project/rule settings | `5f4f764a134185af23a258a52c1b234519f496fffcc810089392a85886f9389f` |
| Root schematic | `3891378e03a8870dbfa5a57cb0bb6b20c30e69c914f7ab260920f0967cf4ca9a` |
| Electrical manifest | `71b76047da224433f414b0c205fbe67ba003c064f2e59530479020ec6d2da83c` |
| Original software report | `ba52e1a29b1bbdef4f2432df6b0ea7b43c350fd1529ff60e16fccd07312ffaf3` |
| Original JUnit | `db5a70a947769df63656d36b0bc726911738cb661d2122e831d8d5e0c567b473` |

[Complete artifact inventory](artifact_hashes.json) records every delivered source, sheet, library, review and export, excluding only itself and local transient state. [Archive preservation](archive_preservation.json) checks the original 156 hardware files. [Local link check](documentation_links.json) and [blank physical-record check](physical_records_blank_check.json) describe package integrity, not hardware tests. Generated audit paths may identify the staging workspace where the checks ran; identical promoted files are tied by hash.

## Remaining limits

Exact motor label/current, pack chemistry/minimum/maximum/topology, BMS behavior, actual second-driver GPIO harness, Pi supply, installed switch/E-stop wiring and chassis fit remain unresolved. Four simultaneous starts can exceed the eFuse threshold; starting torque, motor stall protection, current-limit overshoot, regeneration, thermal coupling, capacitor ripple, fault/rearm timing and assembly quality require later qualification. The software has no physical GPIO backend for the new RUN/ARM/heartbeat interface.

Fabrication: **DEFERRED / NOT BUILT**. Assembly: **DEFERRED / NOT ASSEMBLED**. Physical validation and proposed-PCB integration: **NOT TESTED**. The 22-case future plan remains unexecuted with blank results. User-authorized GitHub publication shares a design-only draft and does not authorize manufacturing. Git history identifies the published revision; the task's publication receipt records the actual remote verification.
