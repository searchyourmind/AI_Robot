# Independent 12 V native consistency review

2026-09-28T12:12:55.619755+00:00

**PASS — routed stage.** Read-only checks; native inputs were not saved, refilled or edited.

Compared 135 manifest/schematic electrical components, 434 logical pins, 459 physical numbered pads and 15 intentional NCs. PCB has 4 separately checked mechanical holes. Resolved 135 local footprint instances and compared all physical pad geometry, preserving repeated EP/drain pad numbers.

Boolean checks: 32 input cases / 128 driver outcomes independently evaluated from each of manifest, native XML and PCB pad nets. Normal PWM off-time brakes; cleared permission coasts. Latch, independent wake, watchdog/fault chain, power-good output sensing, driver mode and duplicate power-pin constraints checked.

Routing: `{"native_connectivity_unconnected": 0, "native_drc_counts": {"schematic_parity": 0, "unconnected_items": 0, "violations": 0}, "stage": "routed", "track_segments": 1572, "vias": 191, "zones": 2}`

Ignored DRC classes: `{}`. DRC exclusions: `[]`.

## Limits

- Matching files can share the same design error; explicit circuit assertions are bounded to documented architecture.
- No analog/timing/SPICE simulation, motor test, thermal measurement or mechanical-fit approval.
- Geometry comparison includes numbered and unnamed pads with shape/position/size/rotation/layers/drill/roundrect data, not manufacturer land-pattern certification.
- No copper width/current-capacity or thermal-area approval is implied by this consistency check.

## Evidence

`independent_verification.json` contains every compared pin, NC, repeated pad and input hash. `independent_schematic_native.net.xml` was freshly exported by KiCad. `independent_command_log.json` contains exact commands and exits; routed mode also creates `independent_native_drc.json`.

## Findings

- None within the checks above.
