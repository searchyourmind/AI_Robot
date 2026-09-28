# Component count and simplification review

**6 V REFERENCE ONLY — DIRECT 12 V INPUT INCOMPATIBLE.** The 2026-09-28 purchase-record update establishes listed 12 V motors and packs. This document retains the existing 5.5–6.5 V design; its calculations, parts and checks have not been qualified for that system. See the [12 V impact review](12v_design_impact.md) and [current hardware evidence](actual_hardware_evidence.md).

**DESIGN REVIEW ONLY — NO CAD OR BOM CHANGES.** Reviewed 2026-09-28 against the integrated manifest and [per-reference BOM](../exports/draft/bom_per_reference.tsv). The [machine-readable review](../validation/design/component_count_review.json) records their hashes, exact reference sets and reconciliation checks.

**The 97 fitted parts are traceable, but 97 has not been established as a necessary or minimum count.** The user's core aim was to consolidate jumper-wire motor, power and control connections. This revision also adds independent timeout, deliberate re-arm, supply qualification and extensive signal conditioning. Those additional requirements explain much of its size; they need their own justification. The design should not be defended simply because every component has a describable function.

## What 97 counts

A fitted placement is one physical component, including a small resistor or capacitor. The bill contains **33 distinct MPNs**, **12 ICs**, and **73 resistors/capacitors**. Test-pad copper TP1–TP10 and mounting holes H1–H4 are excluded. Five off-board mating plugs, cable assemblies, the Pi, motors, source and mounting hardware are also excluded.

| Component category | Count | Exact references |
| --- | ---: | --- |
| Resistors | 52 | R1–R10; R100–R141 |
| Capacitors | 21 | C1–C11; C100–C109 |
| ICs | 12 | U1–U12 |
| Board connectors | 6 | J1–J6 |
| Diodes | 2 | D1, D2 |
| Transistors | 2 | Q1, Q2 |
| Fuse | 1 | F1 |
| Switch | 1 | SW1 |
| **Total** | **97** | Every fitted reference appears once |

The capacitor count is six electrolytics, fourteen 100 nF bypass capacitors and one 1 nF switch filter. The resistor count includes nine precision power-circuit resistors, one power bleed resistor and forty-two interface resistors. These distinctions matter more than the total alone.

## Functional accounting

The following partition also totals 97 with no duplicated references. References spanning several functions are allocated once for accounting; this does not imply electrical independence between blocks.

| Block | Count | Exact references | Relation to the goal |
| --- | ---: | --- | --- |
| Drivers and local VM/VCC decoupling | 10 | U1, U2; C3–C10 | Central motor-power function; local bypass is warranted, while capacitance values remain reviewable |
| Motor/source/Pi connections | 6 | J1–J6 | Directly serves wire consolidation |
| Input protection, feed switching, bulk and bleed | 12 | F1; D1, D2; Q1, Q2; R1–R5; C1, C2 | Supports power handling; exact topology/size is a design choice |
| VM window monitor | 7 | U11; R6–R10; C11 | Added supply-qualification requirement |
| Six motor GPIO buffer channels | 26 | U3; R100–R123; C101 | Added conditioning and powered-off interface behavior |
| RUN/ARM/HB and fault-signal conditioning | 13 | U8, U9, U12; R124–R129, R132; C106, C107, C109 | Supports the added supervisory architecture |
| Physical inhibit and filter | 4 | SW1; R133, R134; C100 | Independent physical control request |
| Watchdog | 4 | U4; R130, R131; C102 | Added independent missing-heartbeat timeout |
| Logic-rail supervisor | 3 | U7; R138; C105 | Added reset/rail qualification |
| Arm latch and permission gates | 7 | U5, U6; R139–R141; C103, C104 | Added deliberate re-arm and fault-latching behavior |
| STBY output stage/defaults | 5 | U10; R135–R137; C108 | Implements common driver inhibit |
| **Total** | **97** | | |

The broad totals are **16 motor/local-support/connection parts + 19 power/protection/VM-monitor parts + 39 conditioning parts + 23 hardware-supervision parts**. Conditioning plus supervision accounts for **62 placements, approximately 64% of the board**. Removing those 62 arithmetically leaves 35, but 35 is not a reviewed buildable alternative: STBY defaults, fault behavior and the Pi interface would need redesign.

The two drivers still have four separate motor outputs. Their input commands are shared by left/right pairs. There are no encoder interfaces, motor-current sensors or onboard control MCU hidden in the 97-part count.

## Simplifications worth reviewing

These are candidates for a subsequent revision, not authorized substitutions or removal instructions. Value/package rationalization and placement reduction are different objectives. No price or assembly quote was obtained.

| Candidate | Quantified effect | Critical assessment and required review |
| --- | --- | --- |
| Relax R1–R4 and R10 from 0.1% precision parts to ordinary 1% parts, keeping nominal values initially | **0 placements removed**; five parts no longer need precision grades | These are gate/base bias and a logic pullup, not threshold-setting dividers. Their current precision is difficult to justify. Recheck Q1 gate margin, Q2 drive and monitor-output edge rate. R6–R9 have the stronger precision case because they set UV/OV thresholds. Reusing existing 10 kΩ/100 kΩ types may reduce purchasing complexity; changing grades alone does not necessarily reduce MPN count. |
| Reconsider R5's 2 W through-hole package | **0 placements removed**; possible footprint/assembly improvement | At 6.5 V and −5% resistance tolerance, dissipation is about 0.135 W, only 6.7% of 2 W. A smaller 0.5–1 W implementation merits review. At 13.5 V the same resistor would initially dissipate about 0.581 W, so derating, pulse energy and abnormal-voltage behavior still matter. A 0.125 W part is not justified. |
| Reduce C5/C9 VCC bulk toward the manufacturer's 10 µF application example | **0 placements removed**; substantially less Pi-rail charging load | Two 47 µF parts were convenient/common with VM decoupling, but add 94 µF nominal. The complete logic rail is approximately 115 µF at initial upper tolerances. Two 10 µF/±20% candidates would reduce that estimate toward 26 µF; a hypothetical 3.3 V/1 ms ramp changes from about 0.38 A to 0.086 A. These are charging calculations, not measurements. Effective capacitance, rail transients and power sequencing must be checked; the new value could add an MPN. [Toshiba application circuit, p7](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660). |
| Reassess C1/C2 rather than assume two 1000 µF cans are mandatory | Potentially **1 fewer placement** if one suitable part replaces two | This pair contributes about 42 mJ stored energy at 6.5 V and is a major reason for controlled inrush and discharge requirements. With one 1000 µF part plus the existing local VM capacitors at −20%, a 3 mJ return starting at 6.5 V raises the idealized rail to about 7.01 V, versus 6.77 V with both cans. That changes the clamp/monitor margin. Reducing bulk needs a new ripple, transient, source-impedance and regeneration calculation; it is not a free deletion. |
| Standardize the fourteen 100 nF bypass capacitors | **0 placements removed**; potentially one fewer MPN/package family | C4/C6/C8/C10/C11 are 0805 KEMET while C101–C109 are 0603 YAGEO with the same nominal capacitance, voltage, dielectric and tolerance. A qualified common package can simplify stocking and placement. Retain a local bypass at each IC; sharing a rail does not make all local capacitors redundant. |
| Replace three dual Schmitt buffers with one six-channel noninverting Schmitt buffer | U8/U9/U12 plus three bypasses: **6 placements → 2**, conditionally saving **4** | A real candidate family is Nexperia 74LV17A, with a TSSOP14 type 74LV17APW and powered-off leakage specification. It is not yet a selected replacement. Thresholds, Pi levels, slow-input limits, Ioff conditions, layout and startup behavior need requalification. One larger package concentrates the six signal paths. [Nexperia, §§3–9](https://assets.nexperia.com/documents/data-sheet/74LV17A.pdf). |
| Replace U3's open-drain data-buffer topology with a suitable push-pull buffer on the same PI_3V3 rail | Could remove R102/R106/R110/R114/R118/R122: **up to 6 placements** | There is no rail translation or wired-OR function required on these six data outputs in the current topology. A suitable powered-off-tolerant push-pull family can avoid the six pullups and their roughly 20 mA worst low-state load. A 74LV17A-based option is worth comparing; its thresholds differ from the present LVC07. Recheck all levels, output loading and partial-power conditions. Simply deleting the pullups while retaining U3 would leave no active high drive. [Current LVC07 output type](https://www.ti.com/lit/ds/symlink/sn74lvc07a.pdf). |
| Package repeated input resistors as isolated resistor arrays | Nine 330 Ω series parts plus nine raw-input 10 kΩ pulldowns: **18 placements → 6 four-element arrays**, saving **12 packages** | This retains eighteen electrical resistors; it reduces placements, not functions. It can complicate routing, rework, parasitics and fault concentration, and may increase MPN variety. Unused elements need proper treatment. Array tolerance/power/package must be qualified; the Panasonic EXB family demonstrates the packaging concept, not a selected substitute. [EXB circuit/package data](https://industrial.panasonic.com/cdbs/www-data/pdf/AOC0000/AOC0000C14.pdf). |
| Review U10's separate STBY buffer and duplicated defaults | Potentially U10/C108/R135 and, after net merger, R141: **up to 4 placements** | U6 already produces the qualified permission signal on the same supply rail. Direct drive deserves a worst-case VOH/VOL and power-state comparison. U10 currently provides a defined open-drain interface, so it should not be deleted on Boolean equivalence alone. Preserve a reviewed low default at the drivers and every physical-disable/arm requirement. [U6 electrical table, p5](https://www.ti.com/lit/gpn/sn74lvc11a), [U10 specification](https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf). |

The Schmitt consolidation and data-buffer change alone illustrate **97 → 87** placements before detailed requalification. Adding the separate resistor-array packaging idea gives an arithmetic **75**, with the same eighteen input-resistor elements. These figures demonstrate optimization opportunity; they are not new BOMs, validated targets or a commitment that all candidates combine without additional support parts. Value changes such as a smaller R5 or VCC capacitance leave the placement count unchanged.

The 12 A, 5.08 mm connectors are also large relative to the reference 0.6 A motor peaks. A smaller connector family could reduce area, but insertion strength, wire gauge, retention and assembly access matter. The five common power/motor headers reduce MPN variety at the cost of making accidental cross-connection possible. Connector quantity alone does not capture that tradeoff.

## What should not be removed casually

The watchdog, arm latch, rail monitors and physical inhibit are not all duplicates: they respond to different conditions. Removing them is a change to the fault-response requirements, not simply cost reduction. A lean consolidation board is a reasonable architecture to compare if those added requirements are explicitly revised. The present software is still mock-only and does not implement the new ARM/heartbeat contract; extra hardware does not by itself complete integration.

Local decoupling, a defined STBY default, source polarity protection and a correctly coordinated power path deserve preservation of their functions. D1 and Q1 are not interchangeable protections: Q1's body diode permits reverse energy toward its input node; D1 blocks further source backfeed. Likewise, an integrated power-stage redesign might improve D1's approximately 0.5 W screening loss, but its reverse-energy, inrush and fault behavior must be designed rather than assumed.

Despite the 97 parts, this board has **no per-channel electronic current limiting or current measurement**. The 2 A fuse and required external source cutoff do not enforce 0.6 A on each motor. Abrupt Pi/VCC loss while VM is charged also remains an unresolved partial-power condition. The board is not a certified emergency stop or a complete fault-tolerant motor controller. Increasing part count has not closed those gaps.

A sensible next revision would first rationalize noncritical precision, capacitor values and package variety; then compare the buffer/array consolidation options; finally decide which independent supervisory behaviors are actually required for the user's wire-consolidation objective. Retain the current files as the reviewed reference until that requirement decision and the revised electrical/CAD checks are complete.

## Metadata erratum and source basis

The manifest's descriptive `role` text for **C109** says “next to U11.” The intended local bypass assignment is **C109 → U12**; **C11 → U11**. Both capacitors use PI_3V3/GND, so a net-name check cannot detect this prose error. This review records the erratum without changing the historical manifest, native CAD or BOM. The functional partition uses the intended assignment from the enable specification.

Primary sources consulted on 2026-09-28: Toshiba TB6612FNG, served revision 2026-05-13, pp4–5 electrical conditions and p7 application circuit; Nexperia 74LV17A Rev.2, 22 March 2024, pp1–4 functions/package/thresholds/Ioff; TI SN74LVC07A SCAS595W, October 2016, output type and electrical tables; TI SN74LVC11A SCLS993A, May 2024, p5; TI SN74LVC1G07 SCES296AG, October 2025, electrical/feature sections; Panasonic EXB array circuit/package tables; and the [Vishay PR01/02/03](https://www.vishay.com/docs/28729/pr010203.pdf) power/derating data. Current component values and topology come from the preserved manifest, rather than an inferred minimum circuit. No prices, purchases or physical tests support this review.
