# Design-only scope and publication

The current scope is a full 12 V electrical redesign and native CAD update, with engineering evidence retained. The later user instruction explicitly authorizes **commit and push to the existing GitHub repository when the work is complete**. This supersedes the earlier no-push wording. Publishing source and design drafts does not release a board for manufacture.

Fabrication **DEFERRED**; assembly **NOT ASSEMBLED**; physical validation **NOT TESTED**; proposed-PCB integration **NOT TESTED**. No order, purchase, quotation/vendor contact, soldering, energized test, live actuation or physical deployment is included.

The purchased prototype uses two TB6612 dual-channel boards. The selected custom-board architecture has four DRV8874 bridges following the [driver review](driver_margin_review.md). Four motor outputs remain electrically separate, with paired left/right commands. The Pi retains its own supply; no new MCU, charging circuit, custom Pi regulator or speculative encoder interface is added. The single-source 9–15 V envelope and 100 × 100 mm board are explicit provisional assumptions; they do not establish the installed battery connections or mounting fit.

Completion requires an editable seven-sheet schematic and routed native PCB, exact package and pad mapping, electrical analysis, actual ERC/DRC/connectivity and parity checks, a BOM, PDFs, board views, a 3D render and a draft export set. The [check report](../validation/design/design_check_report.md) records actual results. CAD checks cannot establish motor compatibility, thermal safety, BMS coordination or physical operation.

Existing software and its 132 prior mock-test records remain distinct from hardware evidence. Any fresh offline rerun is identified separately. The new hardware protocol has no real GPIO backend. The [6 V archive](../../rev_a_6v_archive/ARCHIVE_NOTICE.md) retains the pre-fabrication design error and prior CAD evidence without inventing a physical failure.

Test-record fields for measurements, dates, instruments and evidence remain blank until the work is performed. The [bring-up plan](../validation/bring_up.md) describes deferred work. Actual motor identity and current waveforms, pack limits and connections, wiring for both existing modules, Pi PSU, switches/E-stop and mechanical constraints remain unresolved.
