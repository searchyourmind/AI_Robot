# 12 V power-path review and component decisions

**Provisional 12 V electrical design — actual robot compatibility remains unconfirmed.**

Prepared 2026-09-28. Fabrication: **DEFERRED**. Assembly: **NOT ASSEMBLED**. Physical validation: **NOT TESTED**. The previous 6 V design is preserved in [the immutable archive](../../rev_a_6v_archive/docs/reference_electrical_spec.md). Its incompatibility was found before fabrication; no hardware failure is claimed.

## Selected architecture and evidence boundary

The new circuit uses four DRV8874 bridges and a TPS26630 eFuse with an external reverse-current blocker. It addresses the old board's incompatible TVS, voltage monitor, uncontrolled inrush and lack of adjustable motor current regulation. The driver choice is explained in [driver_margin_review.md](driver_margin_review.md); this document covers the entire power path.

The packs are **listed as 12 V**. Their actual chemistry, series count, nominal/minimum/maximum voltage, BMS behavior and connections remain unknown. The selected **9–15 V continuous input** is a design envelope, not a statement about those packs. No 3S or 12.6 V assumption is used. The candidate MG513P30_12V motor is still unconfirmed; its published 0.36 A rated and 3.2 A stall figures remain conditional. Battery current claims are neither motor specifications nor validated protection thresholds.

The working board size is **100×100 mm, two layers, nominal 1 oz copper**, expanded for two 16 mm bulk capacitors and four exposed-pad drivers. Mounting compatibility remains unverified. The component/net review used the 135-item manifest (121 fitted parts plus 14 copper test points; four PCB-only mounting holes are outside the manifest count); final routed dimensions and check results must come from the final native artifacts.

## Voltage and protection coordination

The sequence is `J1 → F1 → FUSED_IN → Q1 → EFUSE_IN → U13 → VM`. D1 is now an input **bidirectional TVS**, and D2 is the VM clamp. Q1/Q2 with U13 block reverse input/current and control startup. Pi power stays independent, with a common ground reference.

The source envelope is 9–15 V. Source-side overvoltage cutoff is about 16.08 V; the separate VM monitor trips near 18.08 V. D2 SMBJ18A has 18 V stand-off, 20.0–22.1 V breakdown at 1 mA and 29.2 V clamp at the specified 20.6 A pulse point. The VM design target is **≤32 V including overshoot**, leaving 5 V to the driver's 37 V operating ceiling. D1 SMBJ24CA has 24 V stand-off and 38.9 V clamp at 15.5 A; the upstream target is **≤45 V**, below the eFuse's 60 V operating limit. These values follow the [Littelfuse table](https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet?assetguid=ba555e99-a12d-4f72-a0b6-86b06c67171e).

The 32 V and 45 V ceilings are validation requirements, not guaranteed hot-clamp predictions. The TVS breakdown temperature coefficient must not be treated as a guaranteed clamp coefficient. Layout, pulse current, temperature and source impedance still matter. Input and VM TVS loops need short returns to the power ground region.

A restricted abnormal-pulse qualification target is ≤2 A peak, ≤1 ms duration, ≤0.05 J dissipated per TVS, ≤0.1 Hz and initial TVS temperature ≤60 °C. All limits apply together. This is not IEC surge qualification or continuous overvoltage protection. Sustained wrong-supply connection or arbitrary charger operation remains outside the design envelope.

## Complete power-component matrix

The left column identifies the archived design; new references are stated where they changed. Voltage margins compare the component rating with the selected transient target, not merely the 12 V label. Component current ratings do not establish board ampacity.

| Component | Archived rating or implementation | New requirement / selection | Margin, keep/change decision and reason |
| --- | --- | --- | --- |
| F1 | 0451002.MRL, 2 A /125 V | 0451003.MRL, 3 A; ≤2 A normal input allocation | **Change.**  Conservatively credit 300 A interrupt at 32 VDC from the manufacturer table. Actual prospective pack fault current must be confirmed; the <10 A startup claim does not bound a short circuit. |
| D1 | Series SSC54, 40 V /5 A | SMBJ24CA across FUSED_IN/GND | **Replace topology.**  Reverse blocking moves to Q1/U13. 24 V stand-off exceeds 15 V normal; 45 V upstream target fits 60 V eFuse. |
| Q1 | AO3401A, −30 V /±12 V gate; uncontrolled startup | CSD19537Q3, 100 V /±20 V gate | **Replace.**  BGATE 8.3–14 V fits the gate rating; the 100 V drain rating adds reverse-input/charged-output margin. Exposed drain metal connects EFUSE_IN. |
| Q2 | MMBT3904 NPN | BSS138, 50 V /±20 V | **Replace function.**  Fast gate discharge is referenced to FUSED_IN, not ground; its voltage stress is the gate-drive span. |
| R1–R4 | Discrete gate bias network | Removed | **Remove.**  Replaced by the eFuse and separately defined physical/logic permission. |
| D2 | SMBJ7.0A | SMBJ18A | **Change.** 18 V stand-off fits the defined source/energy envelope; 29.2 V table clamp fits the higher-voltage driver with explicit overshoot validation. |
| C1,C2 | Each 1000 µF /25 V | Each EEUFR1H102, 1000 µF /50 V; D16×25 mm, pitch 7.5 mm | **Change.** 50/32=1.56 rating ratio; larger footprints. Each rated 3.32 A ripple at 100 kHz. |
| C3,C7 local VM capacitors | Each 47 µF /25 V, two packages | C20,C25,C30,C35: each EEUFR1H221, 220 µF /50 V; D10×16 mm, pitch 5 mm | **Change and expand.** 50/32=1.56; each rated 1.65 A ripple at 100 kHz. Added storage supports the stated energy limit. |
| C4,C8 VM ceramics |100 nF /50 V | C21,C26,C31,C36: C0805C104K5RACTU | **Keep specification, expand to four.** 50/32=1.56; connect directly at VM/PGND. |
| U1,U2 VM and output pins | Dual TB6612: 13.5 V operating /15 V absolute | U20–U23: DRV8874PWPR, 37 V operating /40 V absolute | **Replace.** 5 V operating margin at the 32 V target; hardware current chopping. The 6 A peak headline is not a continuous board rating. |
| R5 bleed |330 Ω /2 W | PR02000206800JA100, 680 Ω /2 W | **Change.** 0.348 W at 15 V and 1.585 W at 32 V, including −5% resistance; longer discharge procedure. |
| U11 monitor | TPS3700, 4.8/7.16 V thresholds | Same IC, 8.4/18.08 V thresholds | **Keep IC, change settings.**  At VM 32 V, highest divided input is 1.524 V. It inhibits motion but does not absorb energy. |
| R6,R7 |110k/10k, 0.1% |200k/10k, 0.1% | **Change R6.**  Motor-rail UV threshold becomes 8.4 V. |
| R8,R9 |169k/10k, 0.1% |442k/10k, 0.1% | **Change R8.**  VM OV threshold becomes 18.08 V. |
| R10,C11 |10k logic pull-up; 100 nF monitor bypass | Retain; pull up FAULT_OK_RAW to PI_3V3 | **Keep.**  No VM pull-up is connected to a Pi signal. |
| J1, J2–J5 | Phoenix 1757242, 12 A /320 V (III/2), 5.08 mm | Same board headers with reviewed 1757019 cable plugs | **Keep.**  Input static current-rating ratio 12/3.31≈3.63; wire, contact and temperature checks remain. These are not load switches. |
| TP1 and exposed VM copper | Copper test feature | Labeled VM test point | **Keep/relabel.**  Accessible stored-energy node, not a purchased component. |
| Trunks, branches, vias and ground | Old 1 mm trunks/0.4 mm VM branches | Larger routing targets below | **Reroute and recalculate.**  The old 0.25 A/channel current assumptions do not transfer. |
| C5,C9 old logic bulk |47 µF on TB6612 VCC | Removed from the motor-driver supply topology | **Remove legacy role.**  DRV8874 has no separate VCC pin; logic-rail bypass is separately defined. |

The fuse is wiring backup; it is not a per-channel current regulator. A 3 A fuse needs ambient/load derating, inrush fatigue and source interruption review. No battery short-circuit test has been performed. The selected 300 A/32 V interrupt credit is a restriction to verify, not a measured pack property. [Littelfuse 451/453, pp 1–4](https://www.littelfuse.com/assetdocs/fuse-451-and-453-datasheet?assetguid=533cd5cc-956c-4243-867f-6ab5a62f6ba1).

| New support component | Selected rating/value | Purpose and margin |
| --- | --- | --- |
| U13 | TPS26630RGER, 4.5–60 V | Aggregate current limiting, controllable feed, inrush and reverse-block control; 45 V upstream target leaves 15 V operating headroom |
| R40–R43 |53.6k/10k UV, 124k/10k OV; 0.1% TNPW0805 | Protected-input dividers; 150 V rated family, low dissipation |
| R44 | RC0603FR-076K04L, 6.04k, 1% |2.980 A nominal aggregate limit; not a hard instantaneous ceiling |
| R45,R46 |60.4k/10k, 0.1% | Dedicated **output** PGTH divider; necessary for correct recovery ramp selection |
| C40 | C1206C225K5RACTU, 2.2 µF /50 V | dV/dt timing; low differential voltage, with capacitance tolerance/aging allowance |
| C41,C42 | C1206C105K1RACTU, 1 µF /100 V | Raw and post-blocker bypass; 100/45=2.22 rating ratio; upstream charging is not limited by the output ramp |
| U14,R11,R12 | SN74LVC1G08, 1k series, 10k pull-down | FEED_ENABLE drives SHDN; pull-down must sink the eFuse's internal source current |
| C22,C27,C32,C37 |100 nF /50 V, VCP–VM | Differential charge-pump reservoir; never substitute VCP–GND wiring |
| C23,C28,C33,C38 |22 nF /50 V, CPH–CPL | VM-rated flying capacitors; 50 V gives margin against the 32 V target |
| R20–R35 and C24,C29,C34,C39 | Per-driver reference/sense/sleep bias and 100 nF VREF bypass | Keep each sense node separate; these do not carry motor current or provide an automatic stall timer |

## Current, startup and thermal screens

R44 gives `18/6.04=2.980 A` nominal. A conservative ±10% IC allowance plus 1% resistor screen is **2.656–3.311 A**. This is a design allowance around the manufacturer's specified test points, not a new guaranteed accuracy specification at every condition. Fast faults can overshoot; the eFuse does not enforce an instantaneous 3 A ceiling. MODE is open for latch-off.

Per-channel regulation is 0.791 A nominal, with a 0.708–0.888 A static tolerance screen from the driver review. Dynamic overshoot remains unmeasured. Four simultaneous starts can exceed the input limiter's lower bound. Startup failure or a nuisance trip must be resolved through motor/torque validation rather than quietly increasing protection settings.

C40 gives about 0.686 s nominal ramp at 15 V. With maximum VM capacitance, maximum charge current/gain and C40−10%, capacitive charging screens at 0.101 A. Another 20% effective-capacitance loss gives 0.126 A. **The drivers are awake during the ramp:** nSLEEP follows FEED_ENABLE independently of ARM. Add up to 28 mA driver quiescent current, about 23.2 mA bleed and 1.7 mA eFuse input overhead: a conservative cold-start input screen is about **0.18 A**. Simultaneously applying 15 V across the pass element and all downstream allocations gives about **2.66 W** as a conservative instantaneous screen. These are calculations, not measured startup limits.

PGOOD and the arm latch block commands while the feed ramps. A warm fault recovery with VM above PGTH's falling threshold can use fast slew instead of C40; the cold-start current screen does not apply universally. At an illustrative 15 V source and retained 8 V output, pass-path capacitor charging energy is approximately `½×3.456 mF×(15−8)²=0.085 J`. Validate this case separately.

The four-driver design allocates 0.90 W per driver, 3.60 W total, with effective thermal resistance ≤80 °C/W and junction target <125 °C at 40 °C ambient. This depends on adequate copper and functioning regulation. For the input eFuse, 3 A through 53 mΩ gives 0.477 W. Q1's 6 V gate test limit is 16.6 mΩ at 25 °C; applying a separate 2× hot-resistance allowance gives 0.299 W at 3 A. The multiplier is a sensitivity assumption, not a guaranteed hot specification. Add fuse, resistor and copper heating. See [driver_margin_review.md](driver_margin_review.md) for the motor-driver loss model.

## Returned energy and discharge

C1/C2 plus four local capacitors total 2880 µF nominal, 2304 µF minimum and 3456 µF maximum using ±20%. Ignoring ceramic storage, 0.1 J returned from an initial 15 V produces **17.658 V**. The minimum-capacitance capacity from 15 to 18 V is 0.114 J. Require ≤0.1 J/event, ≤0.1 Hz, and VM returned to its source-defined level before the next event. The 14 mJ storage margin must not be spent twice on motor energy and layout overshoot. Against the conservative 17.766 V lowest VM overvoltage threshold, storage headroom above the 0.1 J allowance is only about **4.4 mJ**. Verify effective capacitance remains at least 2304 µF over the intended temperature and service interval; nominal initial tolerance alone does not establish an end-of-life guarantee. An early monitor trip is a possible nuisance inhibit, not clamp failure.

The reverse blocker prevents relying on the battery as the energy sink. TVS protection is backup for brief transients; this design is not approved for continuous downhill braking or externally driven motors. The actual robot's inertial/inductive returned energy is unknown.

R5 is 680 Ω/2 W. Worst initial resistance gives 0.348 W at 15 V and 1.585 W at 32 V. Maximum R/C predicts 9.65 s for 15→0.3 V and 11.52 s for 32→0.3 V, with the source removed and no mechanical input. Require **at least 15 s and measured VM <0.3 V** before handling. An active source or back-driven motor invalidates the exponential discharge model.

## Routing requirements and remaining checks

The prepared power paths use 3 mm MOTOR_IN/main VM copper, 2/1 mm FUSED_IN sections, a 1.5 mm EFUSE_IN trunk, 1 mm individual VM branches and 0.8 mm motor conductors. Short package escapes are 0.40 mm at Q1/DRV leads and two 0.30 mm paths at eFuse input/output pairs. The output expands through 1.2 mm copper and paired 0.80/0.30 mm vias into the main VM bus. Use continuous power ground and at least two parallel vias at main-current layer changes. The [final saved-geometry inventory](../validation/design/routing_geometry.md) supplies actual lengths, bottlenecks and via counts; it distinguishes current-carrying trunks from low-current sense branches. These widths are not an ampacity or thermal certification.

At 35 µm copper and resistivity 1.724×10⁻⁸ Ωm, using a 1.24 hot-resistance multiplier, a 3 mm×100 mm trunk is 0.0204 Ω: at 3.31 A this is 67 mV/0.223 W. A 1 mm×30 mm branch is 0.0183 Ω: at 1 A it is 18 mV/18 mW per conductor. For a 1.6 mm board with 0.30 mm drill and 25 µm barrel plating, one via is approximately 1.17 mΩ at 20 °C or 1.45 mΩ at 80 °C. These are resistance/loss screens, not certified ampacity.

Under the same copper assumptions, a 0.8 mm×30 mm motor conductor screens at 22.9 mΩ and 22.9 mW at 1 A. A pair of 0.30 mm×2 mm escapes carrying 3.31 A total equally dissipates about 11 mW per escape. Treat 2 mm as the provisional maximum short-fanout length; verify actual path lengths and current sharing. A 1 mm aggregate-current segment dissipates about 67 mW per 10 mm at 3.31 A, so it must not be reviewed as a 1 A branch. Transient fault heating and fuse/eFuse response need separate validation.

Use manufacturer thermal-pad geometry, useful copper on both layers and a defined via-in-pad/paste process. Keep motor return out of the Pi harness. Check the actual routed lengths, bottlenecks, shared ground paths and current-bearing vias after routing. Capacitor ripple requires PWM/harmonic frequency derating and an impedance/current-sharing model; adding nameplate ripple ratings is insufficient.

Before release, confirm pack voltage/topology and fault current, motor identity and starting torque, current-limit waveforms, regen energy/clamp overshoot, simultaneous-load temperatures, reverse/reconnect behavior, Pi brownout and fault/rearm timing, capacitor ripple and assembly process. ERC/DRC/parity are separate digital checks. Historical mock-software results are preserved and do not validate any of these physical behaviors.

## Primary source register

All sources accessed 2026-09-28. Dates identify the served document revision, not a search-engine publication date.

| Primary source | Revision and material used |
| --- | --- |
| [TI TPS2663](https://www.ti.com/lit/ds/symlink/tps2663.pdf) | SLVSE94G, June 2024; pp 3–9 pins/limits; §§8.3.1–8.3.2 ramp/PGOOD, 8.3.5–8.3.7 reverse/current protection, 8.3.13/8.4 shutdown/latch; RGE0024H drawing 4219016/A, August 2017 |
| [TI CSD19537Q3](https://www.ti.com/lit/ds/symlink/csd19537q3.pdf) | SLPS549B, November 2022; pp 1–3 ratings/pins; pp 5–6 curves; package drawing |
| [onsemi BSS138](https://www.onsemi.com/pdf/datasheet/bss138-d.pdf) | BSS138/D, April 2024 Rev 7; pp 1–3 pin numbering, voltage ratings and capacitance |
| [TI DRV8874](https://www.ti.com/lit/ds/symlink/drv8874.pdf) | SLVSF66A, December 2019; pp 3–7 electrical limits; Table 4 modes; Figure 28 wake-up behavior; package PWP0016J |
| [TI TPS3700](https://www.ti.com/lit/ds/symlink/tps3700.pdf) | SBVS187G, February 2019; pin map, §6.5 thresholds and §7.3 input range independent of VDD |
| [TI SN74LVC1G08](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf) | SCES217AA, August 2026; p6 loaded output-high margin for U14/SHDN |
| [Littelfuse SMBJ](https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet?assetguid=ba555e99-a12d-4f72-a0b6-86b06c67171e) | JC.07/04/25 v4; pp 1–4 pulse conditions, SMBJ18A/24CA rows and derating |
| [Littelfuse 451/453](https://www.littelfuse.com/assetdocs/fuse-451-and-453-datasheet?assetguid=533cd5cc-956c-4243-867f-6ab5a62f6ba1) | GD12/01/25; pp 1–4 time/current, interrupt ratings, derating and ordering code |
| [Panasonic EEUFR1H102](https://industrial.panasonic.com/sa/products/pt/aluminum-cap-lead/models/EEUFR1H102), [EEUFR1H221](https://na.industrial.panasonic.com/products/capacitors/aluminum-electrolytic-capacitors/lineup/aluminum-electrolytic-capacitors-radial-lead-type/series/83367/model/83746), [FR series sheet](https://industrial.panasonic.com/cdbs/www-data/pdf/RDF0000/ABA0000C1259.pdf) | Live part pages, no formal page revision; FR-A sheet dated 01-Sep-2025, physical and ripple tables. Use the series table's 0.030 Ω for the 220 µF part; one web table has inconsistent impedance units. |
| [KEMET C1206C105K1RACTU](https://search.kemet.com/component-documentation/download/specsheet/C1206C105K1RACTU), [C1206C225K5RACTU](https://search.kemet.com/component-documentation/download/specsheet/C1206C225K5RACTU) | Generated 25-Mar-2026 and 26-Sep-2026; ratings, dimensions, capacitance tolerance/TCC/aging |
| [Vishay TNPW e3](https://www.vishay.com/docs/28758/tnpw_e3.pdf) | Document 28758, revision 10-Apr-2026; ratings and ordering pattern for precision dividers |
| [Vishay PR01/02/03](https://www.vishay.com/docs/28729/pr010203.pdf) | Document 28729, revision 08-Jul-2025; PR02 copper-lead rating, ordering and dimensions |
| [Yageo R44](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-076K04L) | Generated 11-Sep-2026; 6.04 kΩ, 1%, 0.1 W, 0603 |
| [Phoenix 1757242](https://www.phoenixcontact.com/en-us/products/pcb-header-mstba-25-2-g-508-1757242) | Live product page, no formal revision; 12 A, 320 V (III/2), 5.08 mm pitch and connector conditions |
| [WHEELTEC motor page](https://www.wheeltec.net/product/html/?163.html) and [manufacturer parameter image](https://www.wheeltec.net/kindeditor/attached/image/202410/23/20241023091819_60412.jpg) | Undated live page/image; MG513P30_12V row gives 12 V, 0.36 A rated and 3.2 A stall. Installed motor identity remains unconfirmed. |

No availability, price, assembler acceptance or procurement claim is made. Exact order-code and manufacturing-process checks remain part of release review.
