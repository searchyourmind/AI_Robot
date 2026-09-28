# Power circuit specification — 12 V redesign

**Provisional 12 V electrical design — actual robot compatibility remains unconfirmed.**

Prepared 2026-09-28. Fabrication: **DEFERRED**. Assembly: **NOT ASSEMBLED**. Physical validation: **NOT TESTED**. The previous 6 V design is preserved in [the immutable archive](../../rev_a_6v_archive/docs/reference_electrical_spec.md). Its incompatibility was found before fabrication; no hardware failure is claimed.

## Canonical circuit

This specification follows the current redesign manifest and [driver control review](driver_margin_review.md). It supersedes the earlier 6 V power specification for the active design; the archived 6 V files remain unchanged. Routed implementation checks are recorded separately after layout.

`J1.1 MOTOR_IN → F1 → FUSED_IN → Q1 → EFUSE_IN → U13 → VM`

J1.2, all driver PGND/GND/exposed pads, logic ground, capacitor returns and Pi reference grounds join the common ground system. Motor return current must use PCB power copper and the source return, not the Pi harness. No motor output is tied to ground or another bridge output.

D1 SMBJ24CA is bidirectional across FUSED_IN/GND. C41 bypasses the same node. Q1 CSD19537Q3 has sources 1/2/3 at FUSED_IN, gate 4 at EFUSE_BGATE and drains 5/6/7/8 plus exposed drain metal at EFUSE_IN. Q2 BSS138 has gate 1=EFUSE_DRV, source 2=FUSED_IN and drain 3=EFUSE_BGATE. Q2 source is not ground. C42 bypasses EFUSE_IN. This is the eFuse's external reverse-block topology; it replaces the old series diode and P-channel switch.

D2 SMBJ18A has cathode/banded pad 1 at VM and anode 2 at GND. C1/C2 and C20/C25/C30/C35 have positive pad 1 at VM. R5 continuously bleeds VM through 680 Ω. See the [component matrix and protection calculations](power_path_review_12v.md) for ratings and limitations.

## Power permission and fault connection

U14 produces FEED_ENABLE from LOGIC_GOOD and PHYS_OK. R11=1 kΩ connects it to EFUSE_SHDN; R12=10 kΩ pulls SHDN to GND. This ensures the pull-down can sink the documented 10 µA internal current while keeping the node below 0.8 V. A 100 kΩ substitute would not preserve that screen. The rail-level divider estimate is approximately 2.91 V at a 3.2 V source. More conservatively, U14's specified loaded output high of at least 2.4 V at a 3 V supply/16 mA load gives **at least 2.17 V** through worst-case 1% divider resistors, above the 2 V SHDN threshold. The actual static FEED_ENABLE load allocation is below 2 mA.

All four nSLEEP pins also connect FEED_ENABLE. **Drivers are awake during power ramp and recovery.**  Their inputs are actively held at 00 by U3 while motion permission is cleared; they are not held asleep by ARM or PGOOD. Physical disable lowers nSLEEP and SHDN, while software disarm/RUN/watchdog/fault clear commands without necessarily sleeping the drivers.

U13 FLT and PGOOD, U11 OUTA/OUTB, and U20–U23 nFAULT are open-drain outputs sharing FAULT_OK_RAW. R10 is the single 10 kΩ pull-up to PI_3V3. U9 Schmitt-buffers this node for qualification of the arm latch. No fault or arm feedback drives FEED_ENABLE, preventing startup deadlock. A return to healthy levels does not generate a new ARM edge. Reverse-current reporting can conservatively clear ARM during regeneration.

U13 MODE is intentionally open for overload latch-off. Cycling SHDN, UVLO or input power can reset the eFuse; driver OCP latch reset needs physical disable/re-enable or motor-power cycling. The separate external arm latch still requires a fresh edge. Normal driver wake fault behavior occurs with commands blocked.

## Voltage sensing and startup

R40/R41 and R42/R43 sense EFUSE_IN after Q1. This avoids negative raw-input voltage at UVLO/OVP pins, whose lower absolute limit is −0.3 V. Body-diode precharge permits startup; the 7.632 V input UV floor leaves margin at the 9 V minimum source. Because retained VM can feed the post-blocker node through the eFuse body diode, this is not a battery-state-of-charge monitor during reverse or power-removal conditions.

**PGTH uses a dedicated VM divider R45/R46.**  It must not sense EFUSE_IN: TI §8.3.2.1 uses the output-voltage information to choose fast or dV/dt recovery. PGOOD requires both the threshold and internal FET enhancement. The independent TPS3700 still checks downstream UV/OV.

| Function | Divider | Nominal rising threshold | Initial reference/resistor range |
| --- | --- | ---: | ---: |
| U13 input UV | R40=53.6k / R41=10k |7.632 V|7.467–7.798 V|
| U13 input OV | R42=124k / R43=10k |16.080 V|15.729–16.432 V|
| U13 output PGTH | R45=60.4k / R46=10k |8.448 V|8.265–8.632 V|
| U11 VM UV | R6=200k / R7=10k |8.400 V|8.300–8.500 V|
| U11 VM OV | R8=442k / R9=10k |18.080 V|17.864–18.297 V|

Dividers are 0.1%, 25 ppm/°C parts. These initial ranges exclude temperature and input leakage. With a ±0.35% resistor allowance and the documented input leakage, conservative rising screens rounded outward are 7.427–7.839 V input UV, 15.638–16.527 V input OV, 8.220–8.678 V PGTH, 8.255–8.546 V VM UV and 17.766–18.398 V VM OV. The resistor allowance uses a 100 °C excursion; these bounds are calculation assumptions, not measured trip levels. The calculation uses 1.176–1.224 V references and ±150 nA leakage for U13; 0.396–0.404 V and ±25 nA for U11. Each bound includes the divider ratio and a conservative leakage term of `|I_leak| × R_top,max`. Input UV is a circuit fault floor, not validated battery protection.

R44=6.04 kΩ sets 2.980 A nominal aggregate limit. C40=2.2 µF sets approximately 0.686 s nominal cold ramp at 15 V. The static 2.656–3.311 A current screen and cold-start/warm-recovery qualifications are in the power-path review. The 1 µF capacitors upstream of the pass element are not charged through the output dV/dt limiter.

## Exact IC and switch pin contract

The following tables use native reference designators. NC means intentional no-connect; floating configuration pins must not be silently tied to ground.

| U13 TPS26630RGER pin | Name | Net |
| ---: | --- | --- |
| 1 | IN | EFUSE_IN |
| 2 | IN | EFUSE_IN |
| 3 | B_GATE | EFUSE_BGATE |
| 4 | DRV | EFUSE_DRV |
| 5 | IN_SYS | FUSED_IN |
| 6 | UVLO | EFUSE_UV |
| 7 | OVP | EFUSE_OV |
| 8 | GND | GND |
| 9 | dVdT | EFUSE_DVDT |
| 10 | ILIM | EFUSE_ILIM |
| 11 | MODE | NC |
| 12 | SHDN | EFUSE_SHDN |
| 13 | IMON | NC |
| 14 | FLT | FAULT_OK_RAW |
| 15 | PGTH | EFUSE_PG_SENSE |
| 16 | PGOOD | FAULT_OK_RAW |
| 17 | OUT | VM |
| 18 | OUT | VM |
| 19 | NC | NC |
| 20 | NC | NC |
| 21 | NC | NC |
| 22 | NC | NC |
| 23 | NC | NC |
| 24 | NC | NC |
| 25 | EP | GND |

U13 uses `AI_Robot:TPS26630_RGE0024H_EP2.7x2.7`; its pad 25 is GND. Q1 uses `AI_Robot:CSD19537Q3_Texas_Q3`; its large exposed metal is drain/EFUSE_IN. Do not apply the eFuse's grounded-pad convention to Q1. Q2 uses the standard SOT-23 pin mapping stated above.

| U11 TPS3700DDCR pin | Name / net |
| ---: | --- |
|1|OUTA / FAULT_OK_RAW|
|2|GND|
|3|INA+ / VM_UV_SENSE|
|4|INB− / VM_OV_SENSE|
|5|VDD / PI_3V3|
|6|OUTB / FAULT_OK_RAW|

U20–U23 each use DRV8874PWPR with pins 1/2 IN1/IN2, 3 nSLEEP, 4 nFAULT, 5 VREF, 6 IPROPI, 7 IMODE, 8 OUT1, 9 PGND, 10 OUT2, 11 VM, 12 VCP, 13 CPH, 14 CPL, 15 GND, 16 PMODE and grounded CAD exposed pad 17. PMODE connects PI_3V3 for PWM mode; IMODE is intentionally floating. See the driver review for exact control states and current-setting values.

## Capacitor and connector implementation

| References | Value / exact MPN | Connection and mechanical requirement |
| --- | --- | --- |
| C1,C2 |1000 µF /50 V, EEUFR1H102 | VM/GND; D16×25 mm, pitch 7.5 mm |
| C20,C25,C30,C35 |220 µF /50 V, EEUFR1H221 | One local VM/GND capacitor per driver; D10×16 mm, pitch 5 mm |
| C21,C26,C31,C36 |100 nF /50 V, C0805C104K5RACTU | Local VM-to-PGND bypass |
| C22,C27,C32,C37 |100 nF /50 V, C0805C104K5RACTU | VCP-to-VM, never VCP-to-GND |
| C23,C28,C33,C38 |22 nF /50 V, C0805C223K5RACTU | CPH-to-CPL |
| C24,C29,C34,C39 |100 nF /50 V, C0805C104K5RACTU | Each VREF-to-GND; does not join the separate IPROPI outputs |
| C40 |2.2 µF /50 V, C1206C225K5RACTU | EFUSE_DVDT-to-GND; 1206 |
| C41,C42 |1 µF /100 V, C1206C105K1RACTU | FUSED_IN/GND and EFUSE_IN/GND; 1206 |

J1–J5 use Phoenix 1757242 board headers, with 1757019 cable plugs specified separately. J1 pin 1 is MOTOR_IN and pin 2 GND. J2/J3/J4/J5 are FL/FR/BL/BR respectively, pin 1 OUT1 and pin 2 OUT2. Their matching physical form does not prevent misconnection. Label and verify the harness; do not use energized connector removal as a power switch.

J6 is a logic-only IDC16 interface, not a Pi HAT connector. Its pin allocation and GPIO mapping are defined in the current pin/wiring documents. Reserved pins 6/10 are NC; pin 15 is GND. VM and Pi 5 V are not connected to this header.

## Shutdown and remaining evidence

Physical disable removes source permission and sleeps the bridges, but capacitors and motor back-EMF can retain VM. Stop mechanical input, disconnect the source upstream, wait at least 15 s and measure VM below 0.3 V before handling. A connector is not galvanic isolation while still connected, and semiconductor switches do not discharge the rail instantly.

No powered measurement, current-limit waveform, thermal test or actual-robot compatibility is claimed. Final layout widths, vias, ERC/DRC and schematic/PCB parity need the new native artifacts; they are not inferred from this pin contract. The primary source register is in [power_path_review_12v.md](power_path_review_12v.md).
