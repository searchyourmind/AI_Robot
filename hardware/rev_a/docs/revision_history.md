# Revision history

| Stage | Evidence and decision | Physical state |
|---|---|---|
| Existing prototype | User reports four motors, two TB6612 modules, Pi 5, camera, USB microphone and speaker; motor outputs mapped front/rear A/B | Existing prototype reported; proposed PCB not involved |
| Initial Rev A reference | User accepted bounded 5.5–6.5 V, ≤0.25 A RMS/motor and restricted startup assumptions while hardware facts were TBD. A 100 × 80 mm, 97-fitted-component dual-TB draft was completed | Design only; never fabricated |
| Purchase-record audit | Two WHEELTEC R3 sets establish listed 12 V / 30:1 / 500-line GMR motors and two listed 12 V packs. Exact motor/pack identity and installed wiring remain unknown | Documentary evidence, not bench measurements |
| Pre-fabrication design review | SMBJ7.0A and approximately 7.16 V VM overvoltage boundary conflict with direct 12 V input. Candidate motor's 3.2 A stall also requires a driver margin review | **No physical failure occurred** |
| Rev A-12V redesign | Dual-TB branch rejected for the provisional envelope; four DRV8874 with current regulation, TPS26630 eFuse/reverse FET stage, higher-rated bulk/ceramics, new TVS/monitor bounds, command decode/awake-before-arm behavior, 100 × 100 mm draft layout and 121 fitted components | Draft, not released |

The [frozen 6 V archive](../../rev_a_6v_archive/ARCHIVE_NOTICE.md) retains the old CAD, exports and passing CAD reports. They are not reused as evidence for the changed board. The [new report](../validation/design/design_check_report.md) records actual new checks and old/new counts. No test outcome or hardware-failure narrative is invented.

The design is still a reference envelope. Changing to a 12 V class architecture does not establish that it matches the installed robot. In particular, “12 V lithium” is not a documented 3S/12.6 V pack. Fabrication is deferred; assembly and physical validation have not occurred.
