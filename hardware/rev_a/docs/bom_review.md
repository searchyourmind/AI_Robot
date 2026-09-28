# 12 V candidate BOM review

The BOM was generated from `design_manifest.json`, SHA-256 `71b76047da224433f414b0c205fbe67ba003c064f2e59530479020ec6d2da83c`. BOM generation does not modify CAD or the electrical manifest.

| Output | Data rows | Meaning |
| --- | ---: | --- |
| [Fitted BOM](../exports/draft/bom_fitted.csv) | 121 | One fitted placement per row |
| [Grouped BOM](../exports/draft/bom_grouped.csv) | 43 | Exact MPN + footprint purchasing groups; quantities sum to 121 |
| [Copper testpoints](../exports/draft/bom_testpoints.csv) | 14 | Copper pads; purchased quantity zero |
| [Manufacturer sources](../validation/design/bom_source_registry.json) | 43 MPNs | Manufacturer sources, evidence basis and procurement limits |
| [BOM check record](../validation/design/bom_review.json) | — | Manifest/output hashes, disjoint functional partition and checks |

Counts: 54 resistors + 38 capacitors + 17 ICs + 6 connectors + 2 diodes + 2 transistors + 1 fuse + 1 switch = 121. Planned assembly has 108 SMD and 13 THT placements. Relative to the archived 6 V design, the fitted count rises by 24: +2 resistors, +17 capacitors, +5 ICs. There are 26 new distinct MPNs and 17 retained fitted MPNs.

`build_bom.mjs` creates the tables through the bundled artifact spreadsheet runtime and verifies exact table readback and CSV roundtrip. Independent Python CSV parsing also confirmed all fitted references, exact MPNs and footprints, grouped quantity totals, and zero purchased testpoint quantities. The role-description corrections and harmless 10 kΩ value aliases are explicit in the JSON report. Final native CAD parity is a separate check whose current status is tracked in the [design check report](../validation/design/design_check_report.md).

All purchasing is **UNCONFIRMED**. Sources support selected part/package specifications or manufacturer ordering formats; no prices, stock, supplier acceptance or purchases were checked. The exact Murata C100 `D` delivery suffix was not refreshed from a current primary part-specific document. Its base part is present in the manufacturer list, and the archived manufacturer-authored source is retained. Off-board plugs, cables, Pi, motors, packs and mounting hardware are excluded.

Regenerate offline with the bundled Node runtime after any manifest change. The script asserts this revision's 135/121/14/43 counts and fails on an unknown part or unassigned purpose. It must be reviewed before adapting to another revision. It writes only within `work/redesign12v`.
