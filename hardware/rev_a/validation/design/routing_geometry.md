# Native PCB power geometry audit

FINAL SAVED-GEOMETRY INVENTORY; DESK REVIEW ONLY; NOT PHYSICAL VALIDATION

PCB SHA-256: `3eb423b15c766e0647403a8f4eb8eeb2b4a45bfc8c8c5f838797a18a8cf6e116`. KiCad 10.0.6; outline 100.000×100.000 mm.

This report inventories saved native geometry. It does not measure current sharing, heat, impedance, EMC or physical stopping behavior. The detailed JSON retains every candidate path and narrow-run object.

## Width and via inventory

| Net | Layer / width: total length (mm) | Vias |
| --- | --- | ---: |
| MOTOR_IN | F.Cu:3.000000: 39.55 | 0 |
| FUSED_IN | B.Cu:0.200000: 11.34; B.Cu:1.000000: 8.83; F.Cu:0.200000: 2.17; F.Cu:0.400000: 3.19; F.Cu:0.600000: 1.30; F.Cu:1.000000: 36.92; F.Cu:2.000000: 2.05 | 4 |
| EFUSE_IN | F.Cu:0.240200: 0.64; F.Cu:0.300000: 1.98; F.Cu:0.600000: 0.93; F.Cu:0.800000: 1.66; F.Cu:1.000000: 16.14; F.Cu:1.500000: 7.02 | 0 |
| VM | B.Cu:1.000000: 104.29; B.Cu:1.200000: 6.15; B.Cu:3.000000: 155.50; F.Cu:0.300000: 3.27; F.Cu:0.400000: 13.66; F.Cu:1.000000: 65.63; F.Cu:1.200000: 2.30 | 10 |
| FL_OUT1 | B.Cu:0.800000: 10.26; F.Cu:0.400000: 1.30 | 1 |
| FL_OUT2 | F.Cu:0.400000: 2.08; F.Cu:0.800000: 22.05 | 0 |
| FR_OUT1 | B.Cu:0.800000: 10.11; F.Cu:0.400000: 1.30 | 1 |
| FR_OUT2 | B.Cu:0.800000: 18.27; F.Cu:0.400000: 2.08 | 1 |
| BL_OUT1 | B.Cu:0.800000: 10.78; F.Cu:0.400000: 1.30 | 1 |
| BL_OUT2 | B.Cu:0.800000: 21.39; F.Cu:0.400000: 2.08 | 1 |
| BR_OUT1 | B.Cu:0.800000: 10.44; F.Cu:0.400000: 1.30 | 1 |
| BR_OUT2 | B.Cu:0.800000: 18.28; F.Cu:0.400000: 2.08 | 1 |

## Candidate power paths

The graph selects a low-resistance trace/via route; it is not a parallel-network equivalent circuit. Filled zones and arcs are excluded. An unresolved trace graph is not itself a native unconnected-net finding. Shared trunks and individual branches require different current assumptions.

| Path | Trace length mm | Minimum width mm | Vias | Current role |
| --- | ---: | ---: | ---: | --- |
| Input connector to fuse | 39.550 | 3.0 | 0 | Aggregate source current |
| Fuse to Q1 source1 | 4.797 | 0.4 | 0 | Aggregate trunk; terminal-fanout sharing is not inferred |
| Fuse to Q1 source2 | 4.497 | 0.4 | 0 | Aggregate trunk; terminal-fanout sharing is not inferred |
| Fuse to Q1 source3 | 5.147 | 0.4 | 0 | Aggregate trunk; terminal-fanout sharing is not inferred |
| Q1 drain to eFuse IN1 | 9.492 | 0.3 | 0 | Aggregate trunk; each of two final escapes nominally shares current |
| Q1 drain to eFuse IN2 | 9.992 | 0.3 | 0 | Aggregate trunk; each of two final escapes nominally shares current |
| eFuse OUT17 to U20.11 | 83.290 | 0.3 | 2 | Contains shared distribution trunk and one1A-screen driver branch; do not apply one current to every edge |
| eFuse OUT17 to U21.11 | 64.290 | 0.3 | 2 | Contains shared distribution trunk and one1A-screen driver branch; do not apply one current to every edge |
| eFuse OUT17 to U22.11 | 45.290 | 0.3 | 2 | Contains shared distribution trunk and one1A-screen driver branch; do not apply one current to every edge |
| eFuse OUT17 to U23.11 | 46.340 | 0.3 | 2 | Contains shared distribution trunk and one1A-screen driver branch; do not apply one current to every edge |
| eFuse OUT17 to C1.1 | 105.215 | 0.3 | 1 | Bulk storage path; ripple and current sharing unresolved |
| eFuse OUT17 to C2.1 | 84.215 | 0.3 | 1 | Bulk storage path; ripple and current sharing unresolved |
| eFuse OUT18 to U20.11 | 83.290 | 0.3 | 2 | Contains shared distribution trunk and one1A-screen driver branch; do not apply one current to every edge |
| eFuse OUT18 to U21.11 | 64.290 | 0.3 | 2 | Contains shared distribution trunk and one1A-screen driver branch; do not apply one current to every edge |
| eFuse OUT18 to U22.11 | 45.290 | 0.3 | 2 | Contains shared distribution trunk and one1A-screen driver branch; do not apply one current to every edge |
| eFuse OUT18 to U23.11 | 46.340 | 0.3 | 2 | Contains shared distribution trunk and one1A-screen driver branch; do not apply one current to every edge |
| eFuse OUT18 to C1.1 | 105.215 | 0.3 | 1 | Bulk storage path; ripple and current sharing unresolved |
| eFuse OUT18 to C2.1 | 84.215 | 0.3 | 1 | Bulk storage path; ripple and current sharing unresolved |
| U20.8 to J2.1 | 11.298 | 0.4 | 1 | Individual switched motor conductor,1A RMS thermal screen |
| U20.10 to J2.2 | 24.127 | 0.4 | 0 | Individual switched motor conductor,1A RMS thermal screen |
| U21.8 to J3.1 | 11.406 | 0.4 | 1 | Individual switched motor conductor,1A RMS thermal screen |
| U21.10 to J3.2 | 20.355 | 0.4 | 1 | Individual switched motor conductor,1A RMS thermal screen |
| U22.8 to J4.1 | 12.076 | 0.4 | 1 | Individual switched motor conductor,1A RMS thermal screen |
| U22.10 to J4.2 | 23.473 | 0.4 | 1 | Individual switched motor conductor,1A RMS thermal screen |
| U23.8 to J5.1 | 11.743 | 0.4 | 1 | Individual switched motor conductor,1A RMS thermal screen |
| U23.10 to J5.2 | 20.357 | 0.4 | 1 | Individual switched motor conductor,1A RMS thermal screen |

## Thermal-pad geometry and local ground copper

| Device | Thermal plated holes | Ground in20×20 mm window, F/B mm² | Process requirement |
| --- | ---: | --- | --- |
| U20 | 4 | 228.27 / 274.89 | Tented both sides, outside central paste; verify process |
| U21 | 4 | 229.61 / 216.72 | Tented both sides, outside central paste; verify process |
| U22 | 4 | 263.20 / 230.96 | Tented both sides, outside central paste; verify process |
| U23 | 4 | 264.11 / 199.20 | Tented both sides, outside central paste; verify process |
| U13 | 4 | 285.44 / 314.95 | FILLED/CAPPED/PLANARIZED under paste required by fabrication notes |

These clipped areas can overlap and are not guaranteed thermal spreading areas. Confirm the assembled exposed-pad joint and fabrication process separately.

## Local capacitor connections

| Connection | Pad-center distance mm | Trace route mm | Same saved zone island |
| --- | ---: | ---: | --- |
| U20: VM local ceramic | 3.235 | 3.415 | False |
| U20: PGND to VM ceramic return | 3.117 | 12.047 | False |
| U20: VCP reservoir | 5.537 | 10.728 | False |
| U20: reservoir VM return | 3.793 | 10.055 | False |
| U20: CPH flying capacitor | 4.770 | 6.270 | False |
| U20: CPL flying capacitor | 3.281 | 3.553 | False |
| U21: VM local ceramic | 3.235 | 3.415 | False |
| U21: PGND to VM ceramic return | 3.117 | 10.421 | True |
| U21: VCP reservoir | 5.537 | 12.184 | False |
| U21: reservoir VM return | 3.793 | 10.176 | False |
| U21: CPH flying capacitor | 4.770 | 5.319 | False |
| U21: CPL flying capacitor | 3.281 | 2.937 | False |
| U22: VM local ceramic | 3.235 | 3.415 | False |
| U22: PGND to VM ceramic return | 3.117 | 17.902 | True |
| U22: VCP reservoir | 5.537 | 11.692 | False |
| U22: reservoir VM return | 3.793 | 9.971 | False |
| U22: CPH flying capacitor | 4.770 | 6.279 | False |
| U22: CPL flying capacitor | 3.281 | 3.553 | False |
| U23: VM local ceramic | 3.235 | 3.415 | False |
| U23: PGND to VM ceramic return | 3.117 | 52.108 | True |
| U23: VCP reservoir | 5.537 | 11.967 | False |
| U23: reservoir VM return | 3.793 | 15.325 | False |
| U23: CPH flying capacitor | 4.770 | 5.319 | False |
| U23: CPL flying capacitor | 3.281 | 2.937 | False |

A same-island result is geometric continuity, not proof of low loop inductance. Charge-pump loops, VM bypass and ground return still need a layout judgment and later waveform qualification.

## Limits

- Nominal35 µm copper and25 µm via plating are calculation assumptions awaiting fabrication confirmation.
- Both eFuse IN and OUT fanouts must be inspected individually; path selection does not prove equal sharing.
- Fast-fault, ripple, motor and regenerative currents differ from the steady-state screens.
- Final native DRC/parity evidence is separate. No physical test or fabrication release is implied.
