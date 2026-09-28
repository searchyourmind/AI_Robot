# Draft fabrication notes

**DRAFT — NOT RELEASED FOR FABRICATION.** Fabrication: **DEFERRED / NOT BUILT**. No manufacturer was contacted, no quote obtained and no order placed. The following specification is for design review only.

| Parameter | Draft requirement / status |
| --- | --- |
| Board outline | 100×80 mm rectangle in native Edge.Cuts; user-accepted reference envelope, not verified robot mounting geometry |
| Layers | Two copper layers: F.Cu/B.Cu; accepted reference assumption |
| Copper | Nominal 1 oz/35 µm external copper; finished copper and etch tolerance require later manufacturer confirmation |
| Thickness | 1.6 mm in the native board; tolerance and laminate construction are provisional, not user-measured |
| Material | FR-4 suitable for the later chosen soldering process; exact laminate/Tg and stack-up not selected |
| Clearance | 0.20 mm copper design target; 0.50 mm minimum copper-to-edge target |
| Routing targets | 1.00 mm motor-input/VM trunks; 0.60 mm motor outputs; 0.40 mm individual VM branches, PI_3V3 and ground connections; 0.25 mm nominal signals with 0.20 mm routing permitted. VM branches may extend 27.09 mm; they are reviewed at 0.50 A RMS/package in routing_rationale.md. Local pad fanout geometry is reviewed separately. |
| Vias | Nominal 0.80 mm pad/0.30 mm finished hole; >=25 µm barrel plating is an electrical calculation assumption awaiting fabrication confirmation |
| Mounting | Four 3.2 mm non-plated holes; no plated connection or fastener bill implied |
| Solder mask | Top/bottom; reference green color, no functional reliance on color. TB6612 local pad expansion 0.03 mm; its nominal mask web 0.14 mm is a review target. Other openings follow the native files. |
| Silkscreen | Top-side identification, connector function and polarity; nominal white. Do not cover exposed pads or omit input/logic distinctions. |
| Finish | Not selected. Finish/thickness must be reviewed for the fine-pitch SSOP and assembler process before release. |
| Panel/stencil | Not selected. No panel rails, tooling holes, fiducials or stencil thickness are assumed approved. |

The source of truth is the native board and its actual generated exports. When draft Gerber/drill files are present, compare copper, mask, outline, drill count, plated/non-plated classification and origin to that board. A plotted PDF or render is not a fabrication layer. Keep plated and non-plated drill files distinguishable; do not convert the 3.2 mm mounting holes into plated pads. Do not mirror the fabrication files manually.

The local TB6612 footprint uses geometric pad derivation rather than an inspected manufacturer land pattern. Its lateral tolerance/placement margin, paste apertures and assembly process remain explicit review items in [footprint_review.md](footprint_review.md). Native ERC/DRC reports belong in the design validation package. A passing result checks configured rules; it does not establish electrical safety, solder-joint quality, thermal capability or compatibility with the existing robot.

Fabrication exports, BOM and placement data must remain under `exports/draft/`. They are not approved for uploading to a manufacturer's order workflow. Any future release needs resolved electrical/source/harness requirements, a selected fabrication/assembly process, final source/footprint checks and separate authorization for physical work.
