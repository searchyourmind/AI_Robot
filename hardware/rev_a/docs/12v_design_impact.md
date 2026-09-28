# 12 V audit finding and redesign

The initial unbuilt Rev A was designed for an accepted 5.5–6.5 V reference while hardware data were unknown. Purchase records later established a listed 12 V platform. The old SMBJ7.0A TVS and roughly 7.16 V overvoltage monitor made direct 12 V input incompatible. This was a **pre-fabrication design-review finding**, not a failed-board test.

The [original detailed impact review](../../rev_a_6v_archive/docs/12v_design_impact.md) remains archived. The active design now has a full [power-path review](power_path_review_12v.md), [driver-margin comparison](driver_margin_review.md), [new reference bounds](reference_electrical_spec.md), and [revision history](revision_history.md). It uses four DRV8874 bridges instead of retaining dual TB6612 under an unsupported stall-current assumption. The [actual checks](../validation/design/design_check_report.md) refer to new CAD and exports.

The actual battery's minimum, nominal and maximum voltage, chemistry and installed connections remain unknown, as does the exact motor label. Nine to fifteen volts is a provisional design envelope for one source, not an asserted battery specification. Real-robot compatibility is not claimed. Fabrication **DEFERRED**; assembly **NOT ASSEMBLED**; physical validation **NOT TESTED**.
