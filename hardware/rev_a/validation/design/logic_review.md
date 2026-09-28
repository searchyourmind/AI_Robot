# Independent 12 V logic and power-control desk review

2026-09-28. Read-only review of `build_manifest12v.py`, `power_parts.json` and generated `design_manifest.json`. No CAD was changed by this reviewer. This is source/netlist analysis, not SPICE, physical validation, timing measurement or fabrication approval.

**Final reviewed manifest SHA-256:** `71b76047da224433f414b0c205fbe67ba003c064f2e59530479020ec6d2da83c`.

`work/venv/bin/python work/redesign12v/check_logic_manifest.py` passed all **32 combinations of ARM/PWM-left/DIR-left/PWM-right/DIR-right**, checking **128 driver input pairs**, plus sleep, fault, PMODE, PGTH and latch connection assertions. Machine-readable evidence: `work/redesign12v/logic_truth_review.json`. This verifies Boolean connectivity only; gate races, electrical waveforms and analog behavior remain outside that test.

## Review findings and their resolution

1. **Normal wake-up fault pulse:** The original direct nFAULT→arm-clear→nSLEEP chain could cancel every ARM. TI DRV8874 Figure 28 on page 26 visibly shows nFAULT low briefly when nSLEEP rises. Resolved in the reviewed manifest: driver nSLEEP follows FEED_ENABLE, independently of ARM/fault, while separate logic blocks motor commands. No fault-masking timer is used. The waveform was rendered directly from the primary PDF to `work/redesign12v/drv_startup.png`.
2. **PGTH output sensing:** The proposed use of input-side EFUSE_UV for PGTH could bypass the intended dV/dt recovery when the input is high but the output empty. Resolved: U13.15 senses VM through R45=60.4 kΩ / R46=10 kΩ; U13.16 PGOOD joins FAULT_OK_RAW. It qualifies both output voltage and internal FET enhancement. C40 is now 2.2 µF.
3. **Passive tri-state fall into ordinary logic:** The intermediate U3 /OE gating with 10 kΩ output pull-downs could violate following ordinary LVC input transition limits. Resolved: U3 is a quad AND with actively driven outputs. The raw input decode uses Schmitt U15/U16. Removed U10, C108 and R135 are not part of the final gating path.
4. **PWM off-time decay:** The intermediate AND direction decode would coast every PWM off interval, changing diode conduction and regeneration from the original thermal calculation. Resolved: NAND decode gives low-side braking while armed PWM is low, and coast only when disarmed. The driver thermal screen can retain its stated brake-recirculation basis.
5. **Powered-off specification wording:** The initial SN74LVC125A did not have the claimed Ioff specification. It is no longer used. Do not generalize Ioff to the entire board; U3 SN74LVC08A is an ordinary logic gate. Pi-off inhibition rests on the separate FEED_ENABLE/nSLEEP path and its pull-downs, with no powered source on command inputs.

## Final command and fault logic

U15 **SN74LVC2G14DBVR** dual Schmitt inverter: pin 1 DIR_L, pin 6 /DIR_L; pin 3 DIR_R, pin 4 /DIR_R; pin 2 GND, pin 5 PI_3V3.

U16 **SN74LVC132APWR** quad Schmitt NAND: left PRE1=NOT(PWM_L AND /DIR_L), PRE2=NOT(PWM_L AND DIR_L); right analogous. Gate pin sets are (1,2→3), (4,5→6), (9,10→8), (12,13→11); pin 7 GND and pin 14 PI_3V3.

U3 **SN74LVC08APWR** quad AND gates each PRE term with DRIVE_ENABLE_CMD. Its pin sets and supplies match U16's standard TSSOP-14 layout. These actively driven outputs connect directly to driver IN1/IN2. The two left bridges share command signals; the two right bridges share the other pair. Their power outputs remain separate.

| Motion permission | PWM | Direction | IN1/IN2 | Awake driver result |
|---|---|---|---|---|
| 0 | Any | Any | 00 | Coast |
| 1 | 0 | Any | 11 | Brake / low-side slow decay |
| 1 | 1 | 0 | 01 | Reverse |
| 1 | 1 | 1 | 10 | Forward |

All four driver PMODE pins connect to PI_3V3. IMODE remains intentionally floating for fixed-off-time current chopping and latched OCP. Fixed-off-time chopping itself does not assert nFAULT.

U5 uses D=high, positive-edge clock=ARM_PULSE, asynchronous active-low clear=ALL_OK and preset=high. Physical disable, RUN low, watchdog expiry or a qualified fault clears ARM_Q. ALL_OK rising later is not a clock edge and cannot restore ARM_Q. Held-high ARM across a fault likewise does not create a new edge. Actual ARM pulses must respect flip-flop recovery/setup timing and be issued after stable qualification.

FEED_ENABLE=LOGIC_GOOD AND PHYS_OK supplies all nSLEEP inputs and the eFuse SHDN network. It is independent of ARM, fault and PGOOD, avoiding both startup feedback and power-good deadlock. The normal driver wake pulse occurs with command permission blocked. An OCP latch remains set until deliberate physical disable/re-enable or motor power cycle; that action resets the internal driver but still does not supply an external ARM edge. UVLO/thermal auto-recovery also leaves external motion permission cleared.

Keep PWM low before arming or changing direction; leave a settling interval and motor-specific deceleration/reversal interval before raising PWM. Propagation skew can briefly alter the two decoded states if direction changes while PWM is high. The decoder is not a reversal-current limiter or interlock timer. Native gate timing and physical direction-change waveforms require subsequent validation.

## Logic-level margins

At PI_3V3=3.2–3.4 V, the LVC132A table gives VT+ maximum 2.0 V at its bracketing 3.0/3.6 V entries. For LVC2G14, TI explicitly recommends linear interpolation between table supply points: VT+ maximum is 2.32–2.44 V, and VT− minimum is 0.667–0.733 V. Use the conservative lower 3.0 V endpoint of 0.6 V for the input-low screen.

With 330 Ω series / 10 kΩ pull-down resistors at 1% and up to 10 µA combined input leakage, require **GPIO high ≥2.8 V and low ≤0.4 V at J6**. Those values yield ≥2.705 V high and ≤0.391 V low at raw logic nodes, retaining margin. They are interface requirements, not measured Pi output values. Schmitt outputs drive U3 with low load and meet its 2.0 V high / 0.8 V low thresholds; U3 drives DRV8874's 1.5 V high / 0.8 V low inputs.

The SN74LVC132A publication describes slow-input tolerance but also lists a 10 ns/V recommended input-transition limit. Retain that stricter active driven-edge requirement, short harness and no hot-plug assumption; do not claim unlimited slow transitions. Its Schmitt structure handles hysteresis, not arbitrary analog input levels or noise immunity certification.

## Driver and current-limit connections

U20–U23 **DRV8874PWPR**: 1 IN1, 2 IN2, 3 nSLEEP, 4 nFAULT, 5 VREF, 6 IPROPI, 7 IMODE, 8 OUT1, 9 PGND, 10 OUT2, 11 VM, 12 VCP, 13 CPH, 14 CPL, 15 GND, 16 PMODE; CAD pad 17 grounded exposed pad. The generated manifest matches this pin map. Per driver: 100 nF VCP–VM, 22 nF CPH–CPL, VM bypass and 220 µF local bulk are correctly connected. Each motor output and IPROPI measurement node remains separate. J6 pins 6 and 10 are reserved NC.

VREF uses 20.0 kΩ/10.0 kΩ; IPROPI uses 3.09 kΩ. The nominal 0.791 A and documented 0.708–0.888 A static range are unchanged by the control correction. Sensing delay, overshoot and motor stall heating are not covered by that static range. See the deliverable `driver_margin_review.md` for assumptions and thermal allocation.

## Power path and Pi-off review

U13 **TPS26630RGER** pin map matches the RGE table: 1/2 IN, 3 B_GATE, 4 DRV, 5 IN_SYS, 6 UVLO, 7 OVP, 8 GND, 9 dVdT, 10 ILIM, 11 MODE, 12 SHDN, 13 IMON, 14 FLT, 15 PGTH, 16 PGOOD, 17/18 OUT, 19–24 NC, exposed pad GND. MODE open selects latch-off. FLT and PGOOD are open drain and share the 3.3 V fault pull-up with the rail monitor and four driver fault outputs.

Q1 **CSD19537Q3** source=FUSED_IN, drain=EFUSE_IN, gate=EFUSE_BGATE; Q2 **BSS138** gate=EFUSE_DRV, source=FUSED_IN, drain=EFUSE_BGATE match TPS2663 Figure 8-7. Q2 source deliberately is not ground. Q1 exposed drain is EFUSE_IN, not ground. UVLO/OVP dividers sense EFUSE_IN, keeping negative raw-input polarity away from those limited-negative-voltage pins.

The 1 kΩ series / 10 kΩ pull-down at SHDN satisfies the ≥10 µA pull-down capability requirement. With logic absent, its internally sourced shutdown node remains around 0.1 V under that current, below the 0.8 V disable threshold. The enabled gate/divider has margin over SHDN's 2 V turn-on threshold. U14 drives the driver sleep pull-down load directly; the removed 330 Ω enable pull-up is not used.

Pi absence removes command and fault pull-up power. FEED_ENABLE/nSLEEP and SHDN fall through their defined pull-down paths. Remaining VM is a normal supply condition for the DRV8874 single-VM architecture, unlike the prior separate VCC/VM driver concern. Still, abrupt brownout waveforms, connector intermittency and arbitrary component failures are not physically validated.

Physical disable opens the input feed and sleeps the bridges; it does not galvanically isolate motor wiring or instantly discharge VM. The 680 Ω bleed and bulk capacitors leave stored energy for seconds. While physically enabled, drivers remain awake even when disarmed: retain up to 4×7 mA VM quiescent-current allocation.

Reverse current opens Q1 after the controller/FET response; it does not absorb returned motor energy. Energy remains on VM, so the separate capacitor/TVS event-energy and repetition limits remain necessary. eFuse reverse-current fault reporting may clear the arm latch as a safe nuisance trip. Overload latch reset by SHDN/UVLO/power cycling does not create ARM. No automatic motion recovery is credited.

## Primary sources

- DRV8874, SLVSF66A, December 2019: https://www.ti.com/lit/ds/symlink/drv8874.pdf
- TI direct sleep-state answer: https://e2e.ti.com/support/motor-drivers-group/motor-drivers/f/motor-drivers-forum/932996/drv8874-nfault-state-during-sleep-mode
- TPS2663, SLVSE94G, June 2024: https://www.ti.com/lit/ds/symlink/tps2663.pdf
- SN74LVC132A, SCLSA12, May 2024: https://www.ti.com/lit/ds/symlink/sn74lvc132a.pdf
- SN74LVC2G14, SCES200O, August 2015: https://www.ti.com/lit/ds/symlink/sn74lvc2g14.pdf
- TI exact-part threshold interpolation guidance: https://e2e.ti.com/support/logic-group/logic/f/logic-forum/773128/sn74lvc2g14-threshold-voltage
- SN74LVC08A, SCAS283W, July 2024: https://www.ti.com/lit/gpn/sn74lvc08a
- SN74LVC1G08: https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf

No unresolved Boolean/pin-map defect was found in the final reviewed manifest. Native schematic/PCB parity, ERC/DRC, thermal copper, physical waveforms and actual robot compatibility are separate checks and remain subject to their own evidence.
