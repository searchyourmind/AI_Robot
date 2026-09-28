# Footprint and pin-to-pad review — 12 V redesign

**DRAFT — NOT RELEASED FOR FABRICATION.** Fabrication: **DEFERRED**. Assembly: **NOT ASSEMBLED**. Physical validation: **NOT TESTED**. Updated 2026-09-28 for the provisional 12 V redesign; the former 6 V files are preserved in `hardware/rev_a_6v_archive`.

This review records source-derived geometry and its limits. It does not certify assembler acceptance, solder-joint reliability, thermal performance or physical fit. The TB6612 footprint analysis belongs to the immutable 6 V archive; the current board uses four DRV8874 bridges.

## Primary package sources and check scope

Primary sources accessed 2026-09-28:

| Device | Document / package drawing | Reviewed physical PDF pages |
| --- | --- | --- |
| DRV8874PWPR | [TI SLVSF66A, December 2019](https://www.ti.com/lit/ds/symlink/drv8874.pdf); PWP0016J, drawing 4223595/B, December 2023 |3, 39–41: pin map, package, example land/stencil |
| TPS26630RGER | [TI SLVSE94G, June 2024](https://www.ti.com/lit/ds/symlink/tps2663.pdf); RGE0024H, drawing 4219016/A, August 2017 |4, 52–54: pin map, package, example land/stencil |
| CSD19537Q3 | [TI SLPS549B, November 2022](https://www.ti.com/lit/ds/symlink/csd19537q3.pdf); Q3 recommended PCB pattern and stencil |1, 8–9: pin map and package/land/stencil |

The team source review rendered the package pages and inspected native copper/paste plots. KiCad 10.0.6 loaded all three custom footprints. The separate geometry fixture reported **zero geometry violations, no ignored checks, and seven unconnected pairs** because it was intentionally unrouted. That result is not a full-board connectivity or parity pass. Nominal models loaded in a native KiCad render; they are project-authored meshes, not official manufacturer CAD. Complete-board final reports are separate and must not be inferred from this fixture.

## New power footprints

| Footprint / refs | Copper and pitch | Mask/paste and thermal treatment |
| --- | --- | --- |
| `AI_Robot:DRV8874_PWP0016J_EP3.4x5`, U20–U23 |16 leads:1.50×0.45 mm, row centers x=±2.90 mm, pitch 0.65 mm; ground pad 17=3.40×5.00 mm | Central mask/paste opening 2.46×3.55 mm. Lead mask expansion 0.03 mm gives 0.14 mm nominal web. Four 0.60/0.30 mm thermal holes at x=±0.70,y=±2.20 mm are outside paste and tented both sides. |
| `AI_Robot:TPS26630_RGE0024H_EP2.7x2.7`, U13 |24 leads:0.58×0.24 mm, row center offset 1.9125 mm, pitch 0.50 mm; ground pad 25=2.70×2.70 mm | Four 1.188 mm square paste windows centered x/y=±0.694 mm; approximately 77.4% square-area coverage before rounded corners. Four 0.60/0.30 mm thermal holes at x/y=±0.70 mm lie under paste and **require filled/capped/planarized processing**. |
| `AI_Robot:CSD19537Q3_Texas_Q3`, Q1 | Sources 1–3 and gate 4:0.63×0.50 mm, x=−1.435 mm, pitch 0.65 mm. Common drain base 1.90×2.45 mm at x=0.39 mm, joined to drain fingers 5–8 | Terminal paste 0.45×0.34 mm; two drain windows 1.445×1.020 mm with 0.25 mm gap. Source 3/gate 4 copper gap 0.15 mm; mask expansion 0.025 mm retains 0.10 mm nominal web. No hole was added inside the solder land. |

The TI drawings provide **example** land/stencil patterns. Their 0.125 mm stencil examples do not approve a single process for this mixed board. Thermal-hole placement is a project choice and still needs thermal/process validation. U13 fill/cap/planarity is a substantive fabrication requirement; unqualified open holes would create solder-wicking and joint-coverage uncertainty.

The Q1 local 0.15 mm clearance is explicit in the custom footprint and supported by a 0.15 mm board absolute minimum; ordinary routing retains 0.20 mm net-class clearance. Do not silently enlarge its mask margin to 0.03 mm or describe its nominal 0.10 mm mask web as a guaranteed manufactured web. PCB registration, placement and solder tolerances still require process review.

At zero footprint rotation, pin 1 is at upper left in the top-side board view. Numbering follows the manufacturer top view after the documented drawing rotation. The DRV ground pad is 17; the eFuse ground pad is 25. Q1's exposed metal is **drain**, represented by the common pad 5 copper and drain pads 5–8—not a hypothetical grounded pad 9. Duplicate pad objects for thermal holes/common drain do not represent additional device pins.

## Pin contract and retained packages

DRV8874 pins 1/2 IN1/IN2, 3 nSLEEP, 4 nFAULT, 5 VREF, 6 IPROPI, 7 IMODE, 8 OUT1, 9 PGND, 10 OUT2, 11 VM, 12 VCP, 13 CPH, 14 CPL, 15 GND, 16 PMODE; exposed pad 17 GND. U13's full 25-pad contract is in [power_circuit_spec.md](power_circuit_spec.md). The manifest maps each exact numbered terminal separately; common function names do not authorize bridging unrelated pins.

| Retained or ordinary package | Current decision / limit |
| --- | --- |
| U4 watchdog | Custom `TPS3431_DRB8_3x3_P0.65`, grounded exposed pad 9; retain source-based copper. Generic model underside is not authoritative. |
| U5 arm latch | Custom `TI_DCU0008A`, 0.5 mm pitch; retain TI 4225266/A, September 2014 land geometry. Generic VSSOP body is only visualization. |
| F1 | Custom Littelfuse 451 land pattern; updated electrical selection is 0451003.MRL, 3 A. Same package family geometry, not the old 2 A bill item. |
| Q2 | Standard SOT-23 BSS138 1G/2S/3D. An identically shaped NPN is not a pin/function-compatible substitute. |
| D1,D2 | Standard SMB footprints. D1=SMBJ24CA bidirectional; D2=SMBJ18A cathode 1/anode 2. |
| C1,C2 | Standard radial D16/P7.5 footprint for EEUFR1H102. Nominal body height 25 mm must be checked separately from generic-model height. |
| C20,C25,C30,C35 | Standard radial D10/P5 footprint for EEUFR1H221. Nominal body height 16 mm; positive lead 1 and negative lead 2. |
| J1–J5 | Phoenix 1757242 board headers with separately specified 1757019 plugs. Datasheet contact rating is not board-current or connector-misplug qualification. |
| J6 | Exact Würth 61201621621 local footprint; retained detailed source/tolerance review below. |

## Check limits and release items

Review the final board's embedded footprint geometry against these libraries after any library update; library edits alone do not change already placed pads. Native DRC must include local mask/copper exceptions openly and check all thermal holes as plated geometry. Confirm copper connectivity of every ground exposed pad and each Q1 drain feature; do not infer nets from a 3D body's color.

Final mounting, hole tolerance, thermal spreading area, solder coverage, cap planarity, component provenance and process compatibility remain open until a physical-phase release. The archived TB6612 package exception does not apply to the new driver footprint, and its old passed checks must not be reused as evidence for the redesigned board.

## J6 — retained exact 16-pin shrouded header review

The following source/geometry review was retained from the earlier design because the selected header and custom footprint are unchanged. Its native checks concern the individual header, not this complete redesigned PCB.

Selected MPN: **Würth Elektronik 61201621621**, WR-BHD vertical male,
2 × 8 positions, 2.54 mm pitch. Primary source inspected on 2026-09-28:
[manufacturer drawing](https://www.we-online.com/components/products/datasheet/61201621621.pdf),
served revision **002.001, 2026-08-30**, eight pages. The first page was rendered
and visually checked. The exact 16-position drawing has `Pl=17.78 mm`, which is
seven 2.54 mm intervals. This selection is for the reference design; no component
has been purchased or physically fitted.

The stock `Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical` has the correct contact
array and nominal 27.98 mm length, but its 8.9 mm body width, 4.1 mm key opening
and 1.0 mm drilled holes are not the exact drawing dimensions. The project
therefore uses [`AI_Robot:IDC_Wurth_61201621621`](../libraries/AI_Robot.pretty/IDC_Wurth_61201621621.kicad_mod),
a project-local native copy with these corrections:

| Feature | Drawing / implemented geometry | Review consequence |
|---|---|---|
| Contact arrangement | Two rows, 2.54 mm apart; eight positions at 2.54 mm pitch | Pad 1 is at (0, 0); odd pads at x=0, even pads at x=2.54; y=0 through 17.78 mm |
| Through holes | Manufacturer recommended diameter 1.10±0.15 mm; nominal 1.10 mm drill implemented | Final finished-hole tolerance and pin insertion remain fabricator/assembly review items; see tolerance note below |
| Copper pads | 1.80 mm diameter; pin 1 rounded rectangle, others round | Project assumption gives nominal 0.35 mm annulus; 0.74 mm adjacent copper gap |
| Body | 9.00±0.15 mm width ×27.98±0.20 mm length | Fab outline nominal width corrected to 9.00 mm; length retained |
| Polarizing opening | 4.50±0.15 mm opening, centered along the odd-pin side | Fab/silk opening corrected from the stock 4.10 mm gap |
| Pin dimensions | 0.64±0.15 mm square; tail 3.00±0.15 mm | Drawing dimensions checked against the nominal hole; no physical insertion claim |
| Courtyard | x=−3.68…6.22; y=−5.60…23.38 mm | Retained stock envelope leaves at least 0.375 mm to width maximum and 0.40 mm to length maximum |
| 3D model | Project-relative copy of KiCad generic IDC-Header_2x08_P2.54mm_Vertical STEP | Approximate visualization: generic body width is 8.9 mm versus selected nominal 9.0 mm; no exact manufacturer mechanical-model claim |

The drawing's broad pin/hole tolerances do not guarantee all worst-case combinations:
a 0.79 mm maximum square pin has approximately 1.117 mm diagonal, exceeding
the 0.95 mm minimum indicated hole tolerance. The implemented nominal hole
follows the manufacturer pattern, but finished-hole acceptance and the actual
terminal tolerance require process review before assembly release. This draft
review does not suppress that fit uncertainty.

Pin orientation is a **top-side PCB / header mating-face view**, with pin 1 at
upper left at zero footprint rotation; odd pins run down the left and even pins
down the right. This corresponds to the manufacturer's depicted mating face
rotated 90 degrees clockwise. The key opening is on the odd-pin side. A mating
receptacle viewed from its wire side can appear mirrored: connector keying alone
does not validate the wire assignment. Match the ribbon stripe/contact-1 mark
to PCB pad 1, then perform a powered-off end-to-end continuity check of all 16
wires before any later integration. This custom logic cable is **not** a direct
16-position segment of the Pi's 40-pin header. J6 carries logic/reference power
only, never motor current. The proposed signal mapping is in
[pin_map.md](pin_map.md).

Native `pcbnew` **10.0.6** `FootprintLoad` and assertions passed with exit 0:
exactly 16 unique pad numbers, all pad centers, every 1.80 mm pad and every
1.10 mm drill. The footprint's native model URI uses `${KIPRJMOD}`. The check
compares design geometry; it does not qualify drill tolerance or fabrication.

| Review file | SHA-256 |
|---|---|
| Inspected Würth PDF | `0df87add7e40d43c6154ff4d0b47710515a4fd9972b4fbe13c5d55295497b364` |
| Local J6 footprint, after project-relative model link | `31dc30244c3f308f30499065b31b9a5431770491345c80e98d89fa4e6a6286f8` |
