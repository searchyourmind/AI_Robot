# 12 V purchase evidence: impact on the preserved 6 V design

**DIRECT 12 V INPUT IS INCOMPATIBLE WITH THE CURRENT REFERENCE BOARD.** This is a read-only design-impact review dated 2026-09-28. The native CAD, BOM and historical validation reports have not been changed. The existing design remains a 5.5–6.5 V reference; its ERC/DRC results do not establish 12 V operation. The [machine-readable assessment](../validation/design/12v_design_impact.json) records source hashes, checks and unresolved requirements.

## What the new evidence establishes

The user-provided purchase information describes two WHEELTEC R3 two-wheel chassis kits, each with 12 V, 30:1 geared GMR motors advertised with 500-line encoders and a TB6612 regulated dual-channel board. This accounts for four motors and two driver boards. It also describes two lithium packs listed as 12 V and 2500 mAh, with listing claims of built-in protection, continuous current below 4 A, startup current below 10 A and maximum power of 48 W.

These are purchase/listing facts, not measured electrical limits. The exact motor identity remains unconfirmed; **MG513P30_12V is only a candidate identification**. Actual nominal/minimum/maximum pack voltage, chemistry, cell count, full-charge voltage, discharge limits, BMS thresholds/delay and actual pack connections are unknown. The inventory does not show whether the two packs are used independently, one is spare, or another arrangement exists. No series or parallel topology is selected by this review.

Do not infer 3S chemistry or a 12.6 V maximum from the “12 V lithium” label. Capacity in mAh is not motor current. The listed battery current/power figures neither specify each motor's running/stall current nor demonstrate a regulated current limiter. Dividing the battery current by four would not bound an individual stalled motor.

## Definite conflicts in the current native circuit

| Item | Existing design | Direct 12 V consequence |
| --- | --- | --- |
| D2 TVS | SMBJ7.0A from VM to GND, cathode at VM | Its 7.0 V stand-off and 7.78–8.60 V breakdown range are unsuitable across a normally energized 12 V-class rail. It enters avalanche; sustained heating/current depends on the source and protection. Its 600 W rating is a specified transient pulse rating, not continuous absorption capacity. |
| VM overvoltage monitor | U11 TPS3700, R8=169 kΩ and R9=10 kΩ | `0.400×(1+169/10)=7.160 V` nominal OV threshold. Initial reference/resistor tolerances give approximately 7.075–7.245 V before temperature/leakage effects. A normal 12 V-class VM rail is rejected. |
| Input power topology | J1 → F1 → D1 → Q1 → VM | There is no 12 V-to-6 V regulator. Diode/MOSFET voltage drops do not convert this design into a 6 V supply. |

The TVS values come from the [Littelfuse SMBJ table, p2](https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet?assetguid=ba555e99-a12d-4f72-a0b6-86b06c67171e). The threshold calculation uses the preserved divider values and the [TPS3700 reference specification, §6.5](https://www.ti.com/lit/ds/symlink/tps3700.pdf).

**The OV monitor does not remove power from D2.** In the native netlist, LOGIC_GOOD drives Q2/Q1 through R3/R2; VM_OK instead qualifies U6 and the arm/STBY path. Once valid Pi logic turns Q1 on, selecting INHIBIT or receiving an OV fault can leave the input source connected to the TVS. Q1's turn-on architecture was deliberately independent of VM_OK to avoid the original startup deadlock. It is therefore incorrect to assume that the 7.16 V monitor makes a 12 V connection harmless.

Neither raising only the monitor threshold nor removing only D2 resolves the design. The first leaves the wrong TVS energized; the second removes the selected transient clamp while leaving incompatible supervision and unreviewed power/current conditions. Do not power the current board directly from these packs as a compatibility experiment.

## TB6612 eligibility is conditional

The bare TB6612FNG lists VM operation from 2.5 to 13.5 V and a 15 V absolute maximum. Thus nominal 12 V alone does not disqualify the IC, but it leaves limited voltage margin. Its VCC operating range is 2.7–5.5 V. The operating current entry is 1 A/channel for VM≥4.5 V without PWM operation; 1.2 A/channel is an absolute rating. Higher absolute pulse entries are 2 A for 20 ms at ≤20% duty and 3.2 A for a single 10 ms pulse. These are not continuous ratings or a motor-start guarantee. [Toshiba, p3](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660).

Suitability requires the actual charged-source voltage and transients, each motor's startup/stall/reversal/braking profile, and simultaneous two-channel package heating. The previous 0.25 A RMS/0.60 A reference envelope remains a historical assumption; the purchase information does not show that these motors satisfy it. Thermal shutdown is not a current-regulation strategy. The datasheet also warns that back-EMF can raise VM when the supply cannot absorb returned energy. [Toshiba, pp6 and 10](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660).

The [WHEELTEC MG513 product page](https://www.wheeltec.net/product/html/?163.html) provides a [manufacturer parameter image](https://www.wheeltec.net/kindeditor/attached/image/202410/23/20241023091819_60412.jpg) whose **MG513P30_12V** row lists 12 V rated voltage, **0.36 A rated current** and **3.2 A stall current**. I inspected that row directly. It is candidate evidence, not confirmation of the installed motor model; the purchase listing supplies the 30:1 description. No formal revision is visible in the image, and its URL date is not treated as a datasheet revision.

If this candidate is confirmed, its rated-current point is 1.44× the reference 0.25 A/channel limit, and its stall current is 5.33× the 0.60 A reference peak. A purely illustrative equal-resistance conduction-loss comparison gives `(0.36/0.25)²=2.07×`; this is not a new thermal calculation or an assertion that every duty cycle has 0.36 A RMS. The candidate’s sustained stall is not authorized by the TB6612’s 3.2 A **single 10 ms absolute** entry. Startup/stall duration and an effective current-protection strategy remain required before driver eligibility can be established. Four motor currents also need not divide evenly or peak together.

The purchased “regulated TB6612 board” is a separate assembly from this native two-IC design. Its regulator may supply logic, motor power or another output; the listing name does not establish which. Obtain its exact schematic/pinout and regulator behavior before applying the reference wiring. A 5 V driver logic rail would require a guaranteed input-high level of 3.5 V under Toshiba's 0.7×VCC rule, so a nominal 3.3 V Pi signal alone would not meet that stated threshold. The reference PCB instead supplies driver VCC from PI_3V3. [Toshiba, p5](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660).

## Protection cannot be updated by the voltage label alone

For example, **SMBJ12A is not an approved substitute**. Its published stand-off is 12 V, breakdown range is 13.3–14.7 V, and maximum clamp is 19.9 V at the specified 30.2 A pulse test. That does not establish a clamp below the driver's absolute limit. It does not predict the voltage at this robot's unknown fault current either. Normal source maximum, temperature, pulse current, dynamic clamp voltage and layout overshoot must be coordinated together. [Littelfuse SMBJ table, p2](https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet?assetguid=ba555e99-a12d-4f72-a0b6-86b06c67171e).

The existing reverse blocker prevents energy returning to the source, so bulk storage, a clamp or another deliberate energy-dissipation path must handle regeneration. A different BMS does not automatically fix this; charge acceptance can depend on its state. The eventual architecture may require a controlled clamp, regulated motor rail, a different driver with more voltage/current margin, or a verified existing carrier interface. None is selected by this assessment.

Q1 has a ±12 V gate-source absolute limit. The current divider gives approximately `|VGS|=0.824×V_REV_PROTECTED`; at an illustrative exact 12 V source node this is about 9.9 V. That is not a nominal-12 V incompatibility by itself, but maximum input, regeneration, overshoot, gate protection and MOSFET safe operating area still require recalculation. Its −30 V drain rating does not override its separate gate limit. [AO3401A, pp1–3](https://www.aosmd.com/pdfs/datasheet/AO3401A.pdf).

## Calculations that must change

The table below evaluates a hypothetical **exact 12.0 V protected rail after a future redesign**. It is not the pack's maximum voltage and does not describe what happens when the present 7 V TVS is connected to 12 V.

| Screening quantity using the current component values | At 6.5 V | At exactly 12 V | Interpretation |
| --- | ---: | ---: | --- |
| Stored energy in nominal 2×1000 µF + 2×47 µF VM capacitors | 44.2 mJ | 150.8 mJ | Approximately 3.41× the stored energy; startup and fault/discharge energy must be revisited |
| R5 dissipation at 330 Ω minus 5% tolerance | 0.135 W | 0.459 W | The earlier recommendation to consider a smaller bleed resistor must not be carried over unchanged |
| Initial pass-switch `V×I` screen at 0.10 A charging current | 0.65 W | 1.20 W | Not an SOA approval; the old charging restriction is not a verified 12 V startup design |
| Ideal discharge to 0.3 V, R +5%, C +20%, source removed and no regeneration | 2.68 s | 3.21 s | A calculated decay only; actual VM must still be verified, particularly with a back-driven motor |

These follow `E=½CV²`, `P=V²/R`, and `t=RC ln(Vstart/Vend)`. Returned motor energy is separate from initially stored capacitor energy. The old 3 mJ/event limit is not a newly established capability or requirement for the purchased motors.

The required redesign review covers:

- Exact pack voltage range, actual connection topology, BMS/source behavior and Pi supply arrangement.
- Per-motor current waveforms and simultaneous loads; new driver thermal calculations and real per-channel protection requirements. The existing board has no electronic per-channel current limiter or current measurement.
- UV/OV thresholds and tolerances, actual power disconnection, clamp coordination, regeneration and startup/inrush control.
- F1's rating/time-current/interrupt coordination with the source, D1/Q1 losses, R5 heating, wire/connector limits, and actual trace/via currents. The battery listing does not enforce the board's earlier 3 A ceiling or 100 ms external cutoff requirement.
- Capacitor voltage/ripple/ESR limits and energy, including local/bulk current sharing. The existing 25 V capacitors alone do not qualify the complete board.
- Logic rail levels and sequencing. Abrupt Pi/VCC loss while VM remains charged is still unresolved; a higher motor voltage does not repair this limitation.
- Encoder requirements if they are to be integrated. “500-line GMR” does not establish encoder voltage, push-pull/open-collector/differential outputs, pinout, phase timing or counts per output-shaft revolution. Do not multiply 500 by four and by 30 without confirming the manufacturer's count/shaft convention. The current PCB does not provide a reviewed encoder interface.

## Evidence and disposition

The critical D2, monitor-divider and Q1-permission facts were checked against both the preserved manifest and native schematic netlist. Hashes of the native schematic/PCB/project, both BOM forms and selected historical reports are retained in the JSON assessment; those files were not modified. No motor, battery or driver board was powered or measured, and no purchase or manufacturer contact occurred.

This new evidence changes the **applicability** of the 6 V reference. It does not invalidate its historical digital checks or turn them into 12 V checks. A 12 V-compatible implementation needs a separately reviewed specification and electrical redesign before fabrication or connection to the purchased system. This document provides the impact assessment, not that redesign.

Primary sources accessed 2026-09-28: Toshiba TB6612FNG served revision 2026-05-13, pp3/5–7/10; Littelfuse SMBJ JC.07/04/25 v4, pp1–2; TI TPS3700 SBVS187G, February 2019, §6.5 and §7.3; Alpha & Omega AO3401A Rev.3.1, December 2023, pp1–3. WHEELTEC MG513 product page and parameter image, MG513P30_12V row, no formal revision visible. Exact links are provided beside the findings and in the JSON source register.
