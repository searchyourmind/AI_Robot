# Component count and BOM review — 12 V redesign

**Current design-only reference: 121 fitted placements, 43 distinct fitted MPN/footprint groups, and 14 non-purchased copper testpoints.** Reviewed against the final 135-item electrical manifest on 2026-09-28. This is a provisional 9–15 V source design, not a verified match for the installed robot. Fabrication is **DEFERRED / NOT BUILT**, assembly **DEFERRED / NOT ASSEMBLED**, and physical/integration tests **NOT TESTED**. BOM completion is not a procurement or fabrication release.

The [fitted per-reference CSV](../exports/draft/bom_fitted.csv) contains one row per placement; the [grouped purchasing CSV](../exports/draft/bom_grouped.csv) combines identical MPNs and footprints; the [testpoint CSV](../exports/draft/bom_testpoints.csv) assigns purchased quantity zero to each copper pad. Every fitted row supplies manufacturer, exact MPN, package/footprint, circuit purpose, source and **procurement unconfirmed** status. The quantities cover one PCB, without attrition allowance.

## What the count includes

| Category | Fitted placements | Explanation |
| --- | ---: | --- |
| Resistors | 54 | 53 SMD resistors plus the axial R5 VM bleed resistor |
| Capacitors | 38 | 6 electrolytics, 24 × 100 nF, 4 × 22 nF, 1 × 1 nF, 1 × 2.2 µF, 2 × 1 µF |
| ICs | 17 | Four DRV8874 motor drivers, one eFuse, and twelve logic/monitor/watchdog ICs |
| Board connectors | 6 | J1 source, J2–J5 motors, J6 logic harness |
| Diodes | 2 | Input and VM TVS devices |
| Transistors | 2 | Reverse-input/reverse-block control network |
| Fuse | 1 | F1 input backup fuse |
| Switch | 1 | SW1 physical logic inhibit |
| **Total fitted** | **121** | **108 SMD + 13 THT placements** |
| Copper access pads | **14, excluded** | TP1–TP10 and TP20–TP23; no purchased test pins |

The 13 THT placements are six electrolytics, six connectors and R5. IC thermal holes do not turn an SMD IC into a through-hole component. PCB mounting holes H1–H4 are mechanical features, not fitted placements. Off-board connector plugs, the harness, Pi, motors, battery packs and fasteners are excluded; the BOM is not a complete robot shopping list. J1–J5 require separately selected mating plugs, with Phoenix Contact 1757019 the documented mating candidate.

The grouped BOM has **43 rows, not 121 unique part types**. Grouping uses the exact MPN and footprint, not free-text value formatting. For example, the fifteen Vishay `TNPW080510K0BEEA` placements share one purchasing line even though the manifest contains both “10k 0.1%” and “10k 0.1% 25ppm/K.” Both original value strings are retained as aliases. No electrical value or selected MPN was changed to reduce the line count.

## Functional accounting

These reference sets are disjoint and cover all 121 fitted parts. A component is allocated to one accounting block even when its electrical function affects several blocks.

| Block | Count | Exact references |
| --- | ---: | --- |
| Four drivers and local support | 40 | U20–U23; C20–C39; R20–R35 |
| Board connectors | 6 | J1–J6 |
| Input protection, feed, bulk and bleed | 19 | F1; D1–D2; Q1–Q2; U13; R5; R40–R46; C1–C2; C40–C42 |
| VM window monitor | 7 | U11; R6–R10; C11 |
| Sleep/feed qualification | 4 | U14; R11–R12; C12 |
| PWM/DIR decoding and input conditioning | 14 | U3, U15, U16; C101, C13, C14; R100, R101, R104, R105, R112, R113, R116, R117 |
| RUN/ARM/HB and fault conditioning | 13 | U8, U9, U12; C106, C107, C109; R124–R129; R132 |
| Physical inhibit and filter | 4 | SW1; R133–R134; C100 |
| Watchdog | 4 | U4; R130–R131; C102 |
| Logic-rail supervisor | 3 | U7; R138; C105 |
| Arm latch and permission gates | 7 | U5–U6; R139–R141; C103–C104 |
| **Total** | **121** | No repeated or omitted fitted reference |

Each motor now has a separate DRV8874 and local current-regulation network. Four current-sense access pads are included as copper features; there is no ADC or encoder interface in this count. The command inputs remain paired left/right. See the [driver margin review](driver_margin_review.md), [power circuit specification](power_circuit_spec.md) and [enable interface specification](enable_interface_spec.md) for the functions and their limits.

## Why this differs from the archived 97-part design

The frozen [6 V component review](../../rev_a_6v_archive/docs/component_count_review.md) remains historical. Its arithmetic simplification candidates and old STBY/VCC discussion do not describe the current circuit.

| Category | Archived 6 V | Current 12 V class | Change |
| --- | ---: | ---: | ---: |
| Resistors | 52 | 54 | +2 |
| Capacitors | 21 | 38 | +17 |
| ICs | 12 | 17 | +5 |
| Connectors, diodes, transistors, fuse, switch | 12 | 12 | 0 |
| **Total** | **97** | **121** | **+24** |

The revision replaces two dual drivers with four single-channel drivers and adds their charge-pump, current-reference and current-sense support. It also introduces the eFuse power path and changes command decoding. This explains the larger count; **121 has not been established as a minimum or cost optimum**. The BOM contains no price or assembly quotation. Reducing quantities, merging capacitor types or replacing resistor grades would require a separate electrical and layout review, not an unrecorded BOM substitution.

## Source and reconciliation limits

The generated tables were read back through the spreadsheet runtime and independently parsed with Python. All 121 fitted references and their MPNs/footprints match the electrical manifest; grouped quantities sum to 121; every testpoint has purchased quantity zero. The functional partition also matches that same fitted set. Final native schematic/PCB parity is a separate CAD validation step.

Manufacturer data, rather than distributor stock listings, supplies the source register. New examples include the [DRV8874](https://www.ti.com/lit/gpn/drv8874), [TPS2663 family](https://www.ti.com/lit/gpn/tps2663), [CSD19537Q3](https://www.ti.com/lit/gpn/csd19537q3), [Panasonic 1000 µF](https://industrial.panasonic.com/sa/products/pt/aluminum-cap-lead/models/EEUFR1H102) and [220 µF capacitors](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1H221), and [Vishay resistor ordering data](https://www.vishay.com/docs/28758/tnpw_e3.pdf). Family and ordering-code review does not establish exact-suffix availability. The Murata primary list confirms the C100 base part `GRM1885C1H102JA01`; its exact `D` delivery suffix still needs procurement confirmation. No stock, price, authorized supplier, purchase or assembler acceptance is claimed.

The eFuse footprint's under-paste thermal holes require a filled, capped and planarized process qualification. This assembly requirement is not visible in a simple component count and remains deferred. Component quantities also do not establish thermal performance, starting torque, current-limit compatibility or battery suitability.

Several inherited manifest `role` strings describe the old circuit. The BOM uses current net connectivity and specifications for its purpose column: SW1 puts the drivers to sleep and inhibits the eFuse feed; J6 is the new PWM/DIR harness; U9 conditions fault and heartbeat; R132 defaults the buffered heartbeat low; R141 defaults `DRIVE_ENABLE_CMD` low; and C109 bypasses U12, while C11 bypasses U11. These descriptive corrections do not change the manifest, native CAD or selected parts.
