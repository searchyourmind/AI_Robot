# Independent 12 V export consistency review

2026-09-28T12:22:22.876556+00:00

**PASS** — digital artifact consistency; no fabrication release.

Inventory: 121 fitted references, 43 fitted MPNs, 14 copper features, 121 placement rows, 121 fitted model bindings.

Board:100×100 mm centerline outline; native export origin (50.0,150.0) mm. Every placement coordinate, rotation and side is compared to pcbnew.

Actual drill inventory: `{"NPTH": {"coordinate_resolution_mm": 0.001, "export_count": 6, "matching": "one-to-one within half native export coordinate resolution", "maximum_axis_rounding_error_mm": 0.0, "native_count": 6, "pad_count": 6, "sha256": "dddee94b6139ee6aa7a6224f7eee1b6b25de7d3a12a07c81e8b68023c63ad869", "via_count": 0}, "PTH": {"coordinate_resolution_mm": 0.001, "export_count": 251, "matching": "one-to-one within half native export coordinate resolution", "maximum_axis_rounding_error_mm": 0.0005000000000023874, "native_count": 251, "pad_count": 60, "sha256": "c34a7f4c52d27706955ac9c5503c01f45800be272ba9b87db0dcfb6d5efec2a5", "via_count": 191}}`.

Gerbers: 8 layers checked against fresh native exports. Schematic PDF: 7 pages.

## Limits

- PDF check covers7 readable pages and manifest reference presence, not visual layout or graphical circuit correctness.
- Model paths/existence/transforms are checked; nominal model geometry and mechanical fit need visual/manufacturer review.
- Fresh Gerber comparison ignores creation-time comment lines only; no source copper was refilled or modified.
- Drill counts and every diameter/coordinate are derived from current native pads/vias, not old-board totals. Slots are explicitly rejected pending a slot-aware audit.
- This report does not evaluate procurement availability, assembly vendor acceptance, thermal behavior or current capacity.

## Findings

- None within these checks.
