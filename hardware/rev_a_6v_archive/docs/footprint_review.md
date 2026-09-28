# Project footprint and pin-to-pad review

Status: **PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT**.
This review establishes the stated source dimensions, numbering, and native-file
geometry. It does not establish assembler acceptance, solder-joint reliability,
electrical operation, or physical fit. Fabrication and assembly remain deferred.

## TB6612FNG source contract

Primary sources inspected on 2026-09-28:

- [Toshiba TB6612FNG datasheet](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660), served revision **2026-05-13**, p2 pin functions and p8 package drawing.
- [Toshiba SSOP24-P-300-0.65A package drawing](https://toshiba.semicon-storage.com/info/docget.jsp?did=30079), drawing identifier `SSOP24-P-300-0p65A_04_01`, package outline only.
- The [manufacturer land-pattern link](https://toshiba.semicon-storage.com/info/docget.jsp?did=29382&displang=en) exposes an agreement page; its downloadable land pattern was **not inspected**. The project footprint is a documented geometric derivation, not a claimed Toshiba recommended land pattern.
- [KiCad footprint format](https://dev-docs.kicad.org/en/file-formats/sexpr-footprint/) and the footprint shipped in the official **KiCad 10.0.6** package establish the native file syntax used.

The datasheet page was visually inspected from its rendered PDF. Relevant package
limits, in mm: nominal body **5.6 × 7.8**, both dimensions ±0.2; longitudinal
outline maximum **8.3**; lead span **7.6±0.3**; pitch **0.65**; lead width
**0.22±0.1**; terminal foot length **0.45±0.2**; lead-width position control
**0.13 at maximum material condition**; overall height maximum **1.6**.

The stock symbol `Driver_Motor:TB6612FNG` links to
`Package_SO:SSOP-24_5.3x8.2mm_P0.65mm`. That footprint has a different nominal
body and uses 1.9 × 0.4 mm pads at x=±3.5 mm. Its default assignment alone does
not verify this Toshiba outline. The project uses
[`AI_Robot:TB6612FNG_SSOP24_5.6x7.8_P0.65`](../libraries/AI_Robot.pretty/TB6612FNG_SSOP24_5.6x7.8_P0.65.kicad_mod).
The project file was authored for these dimensions; the stock library served as
a native-syntax/numbering comparison, not as a substitute package drawing.

## Pad geometry and tolerances

| Feature | Implemented value | Derivation or design assumption |
|---|---|---|
| Pad size | 1.60 × 0.45 mm rounded rectangles | Length derived below; width includes maximum lead width plus the indicated position-zone width |
| Row centerlines | x=−3.50 and +3.50 mm | Midpoint of the selected 2.70–4.30 mm radial land interval |
| Pitch and end-pad centers | 0.65 mm; y=±3.575 mm | Twelve leads per row: `(12−1)×0.65/2` |
| Outer land edge | 4.30 mm from center | Maximum lead tip `7.9/2=3.95` plus proposed 0.35 mm toe allowance |
| Inner land edge | 2.70 mm from center | Earliest foot heel `7.3/2−0.65=3.00` minus proposed 0.30 mm heel allowance |
| Land length | 4.30−2.70 = 1.60 mm | Geometric toe/heel allowances are project choices, not manufacturer/IPC certification |
| Land width | 0.32+0.13 = 0.45 mm | Maximum-material lead width plus width-direction position zone before PCB registration and placement errors |
| Adjacent copper gap | 0.65−0.45 = 0.20 mm | Explicit reference design-rule assumption; no track routed between these pads |
| Solder-mask expansion | 0.03 mm per pad side | Footprint specifies the expansion; nominal mask web is `0.65−0.45−2×0.03=0.14 mm` |
| Paste aperture | Same rounded rectangle as copper by default | No stencil reduction specified; thickness/aperture changes await assembly-process review |
| Fab body | 5.6 × 7.8 mm with pin-1 chamfer | Nominal package planform, not maximum tolerance envelope |
| Courtyard | 9.10 × 8.90 mm, rectangular | x: outer copper 4.30+0.25=4.55; y: outline max 8.3/2+0.25=4.40, rounded outward to 4.45 |
| Silkscreen | Top/bottom lines and pin-1 triangle | 0.12 mm lines; marker is clear of pads/mask and outside the nominal body |
| Board-edge clearance | At least 0.50 mm from copper, checked at board level | Layout requirement; not inferred from the courtyard alone |

The 0.45 mm width contains the stated maximum-material lead/position envelope
at nominal component registration. It leaves no additional guaranteed side
coverage for PCB fabrication registration, solder-mask registration, placement
error or component rotation. Narrower leads' positional bonus tolerance and
actual joint criteria need assembly-process review. The toe/heel figures above
likewise are geometric before process errors. They must not be described as a
full IPC-7351 tolerance-stack calculation or an IPC solder-joint classification.
The 0.14 mm mask web exceeds the current provisional 0.10 mm mask-web target,
but a chosen manufacturer must confirm its mask process and tolerances later.
This is a documented draft-design exception to unqualified assembly readiness,
not an exception hidden to obtain a passing DRC.

The 0.20 mm copper gap is deliberate, not a silent relaxation of the earlier
0.25 mm provisional clearance worksheet. The board's final rules must record
0.20 mm clearance and still size motor-power copper separately. Refer to the
actual PCB DRC report for the board-level result.

## All 24 pin numbers versus Toshiba

Native `Driver_Motor:TB6612FNG` pin names/numbers were extracted from the official
KiCad 10.0.6 symbol and compared with Toshiba p2. Every mapping agrees; Toshiba's
`Vcc` versus library `VCC` is a capitalization difference. Stacked/hidden symbol
pins still represent separate physical pads and must be present in the netlist.

| Pin/pad | Toshiba/library function | Pad x (mm) | Pad y (mm) |
|---|---|---:|---:|
| 1 | AO1 | -3.500 | -3.575 |
| 2 | AO1 | -3.500 | -2.925 |
| 3 | PGND1 | -3.500 | -2.275 |
| 4 | PGND1 | -3.500 | -1.625 |
| 5 | AO2 | -3.500 | -0.975 |
| 6 | AO2 | -3.500 | -0.325 |
| 7 | BO2 | -3.500 | 0.325 |
| 8 | BO2 | -3.500 | 0.975 |
| 9 | PGND2 | -3.500 | 1.625 |
| 10 | PGND2 | -3.500 | 2.275 |
| 11 | BO1 | -3.500 | 2.925 |
| 12 | BO1 | -3.500 | 3.575 |
| 13 | VM2 | 3.500 | 3.575 |
| 14 | VM3 | 3.500 | 2.925 |
| 15 | PWMB | 3.500 | 2.275 |
| 16 | BIN2 | 3.500 | 1.625 |
| 17 | BIN1 | 3.500 | 0.975 |
| 18 | GND | 3.500 | 0.325 |
| 19 | STBY | 3.500 | -0.325 |
| 20 | VCC | 3.500 | -0.975 |
| 21 | AIN1 | 3.500 | -1.625 |
| 22 | AIN2 | 3.500 | -2.275 |
| 23 | PWMA | 3.500 | -2.925 |
| 24 | VM1 | 3.500 | -3.575 |

Coordinates are top-side PCB coordinates at zero footprint rotation, with pin 1
at upper left, counting down the left row and up the right row. This is the
manufacturer marked-face drawing rotated 90 degrees clockwise; it is not a
bottom view. Pin-1 silkscreen and Fab chamfer agree. Pads 1/2, 3/4, 5/6, 7/8, 9/10
and 11/12 are package duplicates of one terminal, not permission to parallel
separate bridges. All VM pins 13/14/24 need their specified supply connection.
No exposed/thermal pad is invented.

## Project 3D visualization model

[`TB6612FNG_nominal.wrl`](../libraries/3dmodels/TB6612FNG_nominal.wrl) is a
project-authored approximate model. It uses nominal 5.6 × 7.8 mm planform,
7.6 mm lead span, 0.65 mm pitch and 0.22 mm lead width. Body height/standoff and
pin-1 marker are arranged within a conservative 1.6 mm total envelope. Leads use
simple extruded polygon bends rather than a manufacturer-certified formed-lead
surface. It is suitable for checking visual occupancy and orientation, not
coplanarity, tolerances, solder joints or mechanical approval.

The model is bound as `${KIPRJMOD}/libraries/3dmodels/TB6612FNG_nominal.wrl`, assuming
the project lives in `hardware/rev_a`. All VRML coordinates are millimetres divided
by 2.54, with unit footprint scale. This matches the external-model convention
in [KiCad 10.0 source, exporter_vrml.cpp](https://gitlab.com/kicad/code/kicad/-/blob/10.0/pcbnew/exporters/exporter_vrml.cpp).
Model +Y is opposite PCB +Y, so the model's pin-1 marker is at negative X/positive
Y and aligns with pad 1. No unrelated stock 5.3 × 8.2 model is attached.

## Checks actually performed

| Check, 2026-09-28 | Tool/result | Limit |
|---|---|---|
| Primary package/pin review | Datasheet p2 text plus rendered p8 visually inspected | Document review, not measurement |
| Native load | Bundled Python `pcbnew` **10.0.6**, `FootprintLoad`; exit 0 | KiCad accepted the saved footprint syntax |
| Pad geometry and pin mapping | Assertions for exactly 24 unique pads, all centers, 1.60 × 0.45 sizes, pitch/gap/mask calculations, and all 24 symbol names/numbers; exit 0 | Checks this footprint, not the complete schematic/PCB netlist |
| Scratch 3D render | Actual `kicad-cli pcb render`, exit 0; 1000 × 800 PNG | A temporary single-footprint preview, not the robot PCB |
| Visual model inspection | Preview inspected: both 12-lead rows sit on matching pad rows, body/lead span is proportionate, pin-1 dot matches the footprint triangle | Approximate render, not a photograph or assembly evidence |

Native validation used the task-local official app's
`Contents/Frameworks/Python.framework/Versions/3.9/bin/python3` and `import pcbnew`.
The temporary board and preview are under task `work/footprint_review/`, not the
manufacturing/release package. The render command used the actual CLI help:

```sh
kicad-cli pcb render --width 1000 --height 800 --side top \
  --background opaque --rotate 25,0,15 --zoom 1.6 \
  --output footprint_preview.png footprint_preview.kicad_pcb
```

An earlier render attempt using `--rotate=-25,0,15` failed with exit 1 and
`Unknown argument: -25,0,15`; the separated positive-angle form above succeeded.
An initial bare-Python scratch-board save emitted a wx application-context
assertion warning. It did save the scratch board, which the CLI then read and
rendered. The final footprint-only native validation ran separately with exit 0
and no such warning. These attempts are not concealed as first-pass success.
No ERC, complete-board DRC, fabrication, assembly or physical validation is
claimed by the footprint checks; those statuses have separate reports.

SHA-256 review fingerprints:

| File | SHA-256 |
|---|---|
| Inspected Toshiba PDF | `fdea3a0bdfc09d4f09639affac8a56395dc066662641ecab31e1df83e450b966` |
| Official stock footprint | `120d739ab88ed463342f2154d6a4b447768755d164154f3706bb0af7bade9a07` |
| Official `Driver_Motor.kicad_sym` library | `23f23bdbdd5f3ebd6143802827d5df8a4209b643e7614c837d6ff3cd8a459c26` |
| Project footprint with local-model link | `3d96ddc59fac4837d00c9ce8c3fc60073b3949aa23ab5bef115f089b5f9c2316` |
| Project nominal VRML model | `5c77ada67766aad07d1feca1d0acb3a3e594a30d95b452f57ff564ba41181ec5` |


## J6 — exact 16-pin shrouded header selection

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
| Contact arrangement | Two rows, 2.54 mm apart; eight positions at 2.54 mm pitch | Pad 1 is at (0,0); odd pads at x=0, even pads at x=2.54; y=0 through 17.78 mm |
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
