# Independent electrical audit of the 12 V redesign

**Subsequent completion note:** This is the earlier schematic/manifest desk-review record. Its then-pending native routing and geometry work is now completed in the [final check report](design_check_report.md) and [saved geometry audit](routing_geometry.md); the physical-release conditions below remain unresolved. The final process map requires all 13 mapped holes to be filled, capped and planarized, in addition to the separately tented DRV holes.

**2026-09-28 — desk review only.** Fabrication **DEFERRED**; assembly **NOT ASSEMBLED**; physical validation **NOT TESTED**. No CAD, manifest, purchased parts or hardware was changed by this audit. Native routing was still in progress; this is not a completed-board DRC or geometry approval.

**Conclusion:** no unambiguous must-fix schematic/net-contract defect was found within the stated provisional envelope. There are substantial physical-release conditions below. In particular, this conclusion does not approve the purchased batteries/motors, continuous stalls, a hot TVS clamp, or any unfinished copper route.

Reviewed manifest SHA-256: `71b76047da224433f414b0c205fbe67ba003c064f2e59530479020ec6d2da83c` — 135 items, including 121 fitted components. `final_electrical_audit.json` records input hashes, 45 passing connectivity/agreement assertions and recalculated values. The independent command evaluation used actual manifest gate nets for all 32 ARM/left-PWM/left-DIR/right-PWM/right-DIR combinations, checking 128 bridge input pairs; its result agrees with the separate supplied Boolean review. This verifies logic, not timing, analog simulation or hardware.

## Power and reverse-polarity contract

J1 → F1 → FUSED_IN → Q1 → EFUSE_IN → U13 → VM is consistent across the manifest and power proposal. Q1 sources 1–3 are raw input; drains 5–8 and the exposed drain land are EFUSE_IN. U13 has both physical IN terminals and both OUT terminals present. Only explicit NC declarations were normalized when comparing the proposal to the manifest; real nets were compared exactly.

The source-referenced **BSS138 is correctly connected**: gate=DRV, source=FUSED_IN, drain=B_GATE. Its 50 V drain-source rating must not be compared directly to the 45 V ground-referenced input target. In the intended controller operation, its drain-source stress is the gate-drive span, bounded by the eFuse B_GATE clamp up to 14 V; its gate-source drive is 3–5.2 V. Both fit the BSS138's 50 V/±20 V ratings. Q1's 100 V/±20 V ratings similarly cover the controller gate span. Opposing −45 V input and +32 V retained VM would place about 77 V across the blocking FET before parasitic overshoot, below 100 V. This is a stress screen inside a restricted transient test envelope, not reverse-surge qualification. [TPS2663, §§8.3.5–8.3.6 and Figure 9-2](https://www.ti.com/lit/ds/symlink/tps2663.pdf); [onsemi BSS138, Rev 7, pp 1–3](https://www.onsemi.com/pdf/datasheet/bss138-d.pdf).

One unresolved dynamic margin must remain visible: onsemi's 27 pF Ciss is **typical**, while TI requests ≤50 pF, and BSS138's specified on-resistance test uses 4.5 V gate drive while DRV's high minimum is 3 V. TI itself selects CSD19537Q3/BSS138 in its example, so this is not evidence of a wrong topology or a necessary part replacement. It does mean that no guaranteed reverse turn-off delay can be inferred from nominal capacitance or the driver's typical timing. Gate waveforms, delay and peak stress require qualification.

D1 SMBJ24CA is a bidirectional raw-input shunt. D2 SMBJ18A is a unidirectional VM shunt with cathode on VM. UVLO/OVP sense **EFUSE_IN after Q1**, keeping negative raw input off their restricted-negative pins. OVP sees approximately3.36 V at the 45 V upstream target, within its 4 V recommended input range. Retained output voltage can appear on EFUSE_IN through the internal body diode, so this sensor is not a battery-state monitor during input removal/reversal.

The chosen32 V VM and45 V upstream ceilings leave margin to DRV8874's 37 V and TPS26630's 60 V operating limits. The TVS table's 29.2 V/38.9 V clamp points are specified pulse conditions, **not guaranteed hot/layout clamp ceilings**. Keep the documented simultaneous restrictions: ≤2 A peak, ≤1 ms, ≤0.05 J per TVS, ≤0.1 Hz, initial TVS ≤60°C, and verify actual overshoot. Arbitrary charger, sustained overvoltage and IEC surge claims are excluded. [Littelfuse SMBJ, JC.07/04/25 v4](https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet?assetguid=ba555e99-a12d-4f72-a0b6-86b06c67171e).

## Startup, PGOOD and fault behavior

FEED_ENABLE derives only from LOGIC_GOOD and PHYS_OK. It drives eFuse SHDN and all four nSLEEP pins independently of ARM/fault/PGOOD. Drivers therefore wake during ramp/recovery; their inputs remain actively00/coast until qualification and a fresh ARM edge. This removes the earlier wake-fault feedback loop. The fault bus combines U13 FLT/PGOOD, both TPS3700 outputs and four nFAULT outputs through one 3.3 V pull-up and a Schmitt stage. Healthy recovery does not clock the arm latch.

PGTH senses **VM output** through its dedicated 60.4k/10k divider. It no longer uses the input UV node. PGOOD requires both threshold and internal FET enhancement. Warm fault recovery with retained VM above PGTH's falling threshold may ignore C40 and use fast slew/current limiting; the cold-ramp calculation does not apply to every recovery. [TPS2663, §§8.3.1–8.3.2.1](https://www.ti.com/lit/ds/symlink/tps2663.pdf).

SHDN's 1k/10k network retains margin: a conservative loaded U14 high of 2.4 V through worst 1% divider values gives 2.178 V against a 2 V threshold. The pull-down gives 0.101 V for the documented 10 µA internal source current. The actual resistors are 0.1%, so this 1% calculation is deliberately broader. The separate nSLEEP pull-downs remain connected. Pi loss removes external command/pull-up supply, but arbitrary brownout edges and component failures are not validated by this static result. [SN74LVC1G08, SCES217AA, p6](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf).

MODE remains floating for eFuse latch-off. The driver IMODE pins remain floating for fixed-off-time regulation/latched OCP, and PMODE is high. The evaluated truth table is disarmed00/coast; armed PWM0=11/brake; armed PWM1 selects01 or10 by direction. Four power outputs remain separate despite paired controls. There is no automatic reversal timer or stalled-motor detector. A continued heartbeat during stall does not establish motor safety.

## Recalculated energy, current and loss

| Item | Audit calculation | Limitation |
| --- | ---: | --- |
| Aggregate limit |2.980 A nominal; 2.656–3.311 A screening range | ±10% IC engineering allowance plus1% resistor; dynamic overshoot is not bounded |
| VM storage |2.880 mF nominal; 2.304/3.456 mF min/max | Initial±20% only; verify effective capacitance over temperature/life |
| 0.1 J returned at 15 V |17.658 V with minimum storage | Actual motor/robot energy unknown; ≤0.1 Hz and reset between events |
| Headroom to lowest VMOV screen |4.4 mJ above the 0.1 J event | Early nuisance inhibit is possible; this is not a failure of TVS protection |
| Cold-start input screen |0.179 A, rounded to 0.18 A | Includes0.126 A capacitor allowance, 28 mA awake drivers, 23.2 mA bleed, 1.7 mA eFuse overhead |
| Nominal cold ramp |0.686 s at 15 V | C40 tolerance/aging and warm-recovery behavior differ |
| eFuse conduction at 3 A |0.477 W using 53 mΩ hot maximum | Physical junction/copper temperature not measured |
| Q1 conduction at 3 A |0.299 W using 2×16.6 mΩ allowance | The2× hot factor is an assumption, not a guaranteed hot resistance |
| R5 at 15/32 V |0.348/1.585 W, including−5% resistance | 2 W rating still needs ambient/assembly review |
| 32→0.3 V discharge |11.52 s at maximum R/C | Require ≥15 s **and measuredVM <0.3 V**, with no source/back-drive |
| Paired0.30×2 mm escapes |11.2 mW each at 3.31 A shared equally | 35 µm copper/80°C resistance screen, not verified routing or pulse ampacity |
| 1 mm aggregate segment |66.9 mW per 10 mm at 3.31 A | Must use actual length; do not analyze it as a 1 A branch |

The four-driver 0.90 W/device allocation and80°C/W effective target remain conditional on functioning regulation and actual copper/airflow. They do not turn the 3.2 A candidate stall current into an allowable operating condition. The interface has no current telemetry ADC or automatic motor-specific stall timer.

## Required completion and release conditions

- Complete native routing/parity/ERC/DRC and the actual width/return-path inventory. Check both eFuse IN and OUT escapes independently, any shared narrow neck, main-current via pairs and all exposed-ground connections. Native thermal holes do not by themselves prove the required spreading area.
- Retain U13 filled/capped/planarized thermal holes under paste. DRV holes are outside paste and tented; confirm the selected fabrication process can implement both deliberately.
- Establish actual motor identity, pack voltage/topology/BMS and prospective fault current. The3 A fuse's credited 300 A/32 VDC interrupt capacity must exceed the actual source fault current; seller startup-current wording is not evidence of that.
- Measure limiter peaks, starting torque, simultaneous starts, warm recovery, gate reverse turn-off, clamp peaks, capacitor ripple, four-driver temperatures and Pi brownout/rearm behavior before physical compatibility claims.

The design-only milestone can proceed with these explicitly open conditions and the remaining native geometry checks. Fabrication/assembly/physical validation remain deferred. No circuit deletion, part substitution, source selection or physical authorization is implied by this audit.
