# Evidence index

[design/](design/) is the designated location for current 12 V CAD, netlist, export and desk-review evidence. Read the [design check report](design/design_check_report.md) for actual status and input hashes. A filename alone does not make a report current: use it only when the check report identifies its redesigned inputs and result. The [old 6 V CAD reports](../../rev_a_6v_archive/validation/design/) are preserved separately and do not apply to the new design.

The original [software_test_report.md](software_test_report.md), `mock_tests.junit.xml`, `test_environment.txt`, `software_input_hashes.json`, `baseline_parser_reproduction.json`, `verification_checks.json`, `changed_files.txt` and `bom_manifest_check.json` are preserved records of earlier checkpoints. Claims about CAD availability, BOMs, links or Git state inside those files apply only to the recorded checkpoint. Current hardware BOM evidence lives under `design/`; the historical 132-test report is not hardware validation. A fresh offline rerun is recorded separately under `design/`.

The [bring-up plan](bring_up.md) remains unexecuted, and [physical_test_records.csv](physical_test_records.csv) contains no measured results. Fabrication **DEFERRED**; assembly **NOT ASSEMBLED**; physical validation **NOT TESTED**. No motor, battery, Pi GPIO or camera hardware was operated for these checks.
