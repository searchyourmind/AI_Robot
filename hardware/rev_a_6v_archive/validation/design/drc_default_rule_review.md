# Supplemental DRC default-rule review

KiCad 10.0.6 ran the copied final board, project, hierarchical schematics and library references with all five default-ignored checks set to warnings. All other severities and geometric rules were retained. The command included all severities, all track errors, schematic parity and a zone refill.

**Result: 0 violations, 0 unconnected items, 0 schematic parity findings, and no ignored checks.**

| Check | Warning count | Disposition |
|---|---:|---|
| `missing_courtyard` | 0 | No missing courtyards reported; keeping the check enabled improves future footprint review. |
| `track_not_centered_on_via` | 0 | No off-center track/via connections reported; there is no present geometry exception requiring an ignore. |
| `tuning_profile_track_geometries` | 0 | No tuning-profile geometry findings; no tuned high-speed routing requirement is claimed. |
| `footprint_filters_mismatch` | 0 | No footprint filter mismatches reported with schematic parity enabled. |
| `footprint_type_mismatch` | 0 | No footprint component-type/pad-type mismatches reported with schematic parity enabled. |

There is no observed board condition requiring a blanket ignore for these classes. This result informed the decision to enable all five as warnings in the final project. The root task performs and reports the final DRC after that change. The original PCB was not changed by this review. A zero-warning result does not establish manufacturing or physical readiness.

The [JSON record](drc_default_rule_review.json) contains the actual native report, command and source-file hashes.
