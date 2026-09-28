# Reference power circuit and native-CAD contract

**6 V REFERENCE ONLY — DIRECT 12 V INPUT INCOMPATIBLE.** The 2026-09-28 purchase-record update establishes listed 12 V motors and packs. This document retains the existing 5.5–6.5 V design; its calculations, parts and checks have not been qualified for that system. See the [12 V impact review](12v_design_impact.md) and [current hardware evidence](actual_hardware_evidence.md).

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
**DRAFT — NOT RELEASED FOR FABRICATION.** Prepared 2026-09-28. All physical work is deferred. Reference operating bounds are in [reference_electrical_spec.md](reference_electrical_spec.md).

## Exact topology

`J1.1 MOTOR_IN → F1 → FUSED_IN → D1 anode/cathode → REV_PROTECTED → Q1 source/drain → VM`.

J1.2, Pi interface grounds, both drivers' logic/PGND pins, all capacitor returns, TVS anode and monitor ground share GND. No motor output connects to GND or to another bridge output. Pi power remains independent; no VM-to-Pi regulator or Pi 5 V connection is fitted.

Q1 is a P-channel AO3401A, source pin2 on REV_PROTECTED and drain pin3 on VM. Its gate pin1 has R1=22k to source. Gate also connects through R2=4.7k to Q2 collector. Q2 is an MMBT3904LT1G: emitter pin2 GND, collector pin3 to R2, base pin1 driven through R3=10k from LOGIC_GOOD, with R4=100k base-to-GND. Thus the motor feed defaults off without valid Pi logic. LOGIC_GOOD must be a qualified push-pull 3.3 V signal able to source approximately 0.3 mA; it is supplied by the enable/supervisor circuit. Q1 permission deliberately does not depend on VM_OK or ARM, because the VM monitor must see power before it can permit arming.

Q1's divider makes gate drive approximately `−0.824×REV_PROTECTED` when Q2 is saturated. Use the 85 milliohm resistance limit at −2.5 V gate drive for screening. At 13.5 V on VM, a conservatively equal source voltage gives |VGS|≈11.1 V, below the ±12 V gate limit. Q1's body diode conducts VM toward REV_PROTECTED; D1 blocks further recharge into the external source. Reverse leakage is finite, so this is not galvanic isolation. The 25 V capacitors and 30/40 V semiconductors have voltage headroom; TB6612's 13.5 V operating/15 V absolute VM limits remain the tighter constraints.

D2 is a unidirectional SMBJ7.0A, cathode/banded pad1 to VM and anode pad2 GND. It is placed after the reverse blocker and Q1, beside the bulk capacitors and power return. C1/C2 are each 1000 µF/25 V, positive pad1 VM. R5=330 ohm/2 W discharges VM continuously. At each driver place 47 µF/25 V plus 100 nF/50 V on VM and separately on VCC. The electrolytic nominal exceeds Toshiba's 10 µF example without relying on MLCC DC-bias capacitance. Place ceramic connections at the IC pins, not at the distant input connector.

The reference PWM rate is 1 kHz. The Panasonic FR-A frequency table gives a 0.85 multiplier for 47 µF at 1 kHz, making the 280 mA/100 kHz ripple rating a 238 mA single-frequency screening limit. The 1000 µF parts use a 0.90 multiplier, or 1.962 A each at 1 kHz. Actual C3/C7 ripple is not the same as motor current: the local and bulk capacitors share pulsed current through frequency-dependent trace, lead and capacitor impedances. A harmonic-weighted ripple-current/temperature check is still required before fabrication release; do not assert compliance merely from capacitance or sum parallel ripple ratings without a sharing model. This is a documented analysis gap, not a failed physical test or a reason to change the accepted motor envelope without evidence. Source: Panasonic FR-A, 01-Sep-2025, pp1–2 frequency and case-size tables, accessed 2026-09-28.

## VM window monitor

U11 TPS3700DDCR uses the DDC SOT-23-6 pinout below. OUTA and OUTB are open-drain outputs wired together and pulled to PI_3V3 through R10=10k, producing VM_OK_RAW. The enable circuit Schmitt-buffers this as VM_OK. UV: R6=110k from VM to INA+, R7=10k to ground. OV: R8=169k from VM to INB−, R9=10k to ground. All divider resistors are 0.1%, 25 ppm/K. C11=100 nF from VDD to GND. No RC input filter is fitted; use short quiet sense routing taken from the local VM/bulk node. False trips safely require rearming; they must not be masked by an unreviewed delay.

`V_UV,rise = 0.400×(1+110/10) = 4.800 V` and `V_OV,rise = 0.400×(1+169/10) = 7.160 V`. Including the 396–404 mV reference and initial 0.1% resistor limits gives approximately 4.743–4.857 V UV rising and 7.075–7.245 V OV rising. UV falling uses the separately specified 387–400 mV range: approximately 4.635–4.809 V before input leakage and temperature drift. The 25 nA maximum INA+ leakage adds about 2.75 mV input-referred uncertainty. The minimum UV trip remains above the 4.5 V boundary with useful margin under the reference conditions. It is not an exact 4.8 V cutoff.

The monitor's input operating range is specified independently of VDD, permitting its divided VM input while the Pi rail is absent. VM=13.5 V gives only 1.125 V at INA+ and 0.754 V at INB−. Its output pullup connects only to PI_3V3. Outputs are not guaranteed below the monitor's power-on threshold; the separate LOGIC_GOOD qualification and arm latch must ignore them during invalid logic power. Startup maximum 450 µs is shorter than the supervisor qualification interval. This monitor is an enable interlock; it does not disconnect an erroneous high external voltage or enforce channel current.

## Pin / footprint table

References in this specification are functional identifiers; the integrated CAD/BOM may renumber them while preserving the nets. The generation handoff is the machine-readable `work/power_circuit.json`. Final deliverables must use the actual integrated reference designators.

| Part / candidate MPN | Native footprint | Exact pin-to-net contract |
| --- | --- | --- |
| F1 Littelfuse 0451002.MRL | Local Fuse_Littelfuse_451 | 1 MOTOR_IN; 2 FUSED_IN; nonpolar |
| D1 Vishay SSC54-E3/57T | Diode_SMD:D_SMC | 1 K REV_PROTECTED; 2 A FUSED_IN; body band at K |
| Q1 AOS AO3401A | Package_TO_SOT_SMD:SOT-23 | 1 G VM_GATE; 2 S REV_PROTECTED; 3 D VM |
| Q2 onsemi MMBT3904LT1G | Package_TO_SOT_SMD:SOT-23 | 1 B VM_EN_BASE; 2 E GND; 3 C VM_EN_COL |
| D2 Littelfuse SMBJ7.0A | Diode_SMD:D_SMB | 1 K VM; 2 A GND |
| U11 TI TPS3700DDCR | Package_TO_SOT_SMD:SOT-23-6 | 1 OUTA VM_OK_RAW; 2 GND; 3 INA+ VM_UV_SENSE; 4 INB− VM_OV_SENSE; 5 VDD PI_3V3; 6 OUTB VM_OK_RAW |
| C1/C2 Panasonic EEUFR1E102 | Capacitor_THT:CP_Radial_D10.0mm_P5.00mm | 1 positive VM; 2 negative GND; 10 mm nominal diameter, 20 mm length, 5 mm lead pitch |
| C3/C5/C7/C9 Panasonic EEUFR1E470 | Capacitor_THT:CP_Radial_D5.0mm_P2.00mm | 1 positive rail; 2 negative GND; 5 mm nominal diameter, 11 mm length, 2 mm lead pitch. C3/C5 at U1 VM/VCC; C7/C9 at U2 VM/VCC. |
| C4/C6/C8/C10/C11 KEMET C0805C104K5RACTU | Capacitor_SMD:C_0805_2012Metric | 1 rail; 2 GND; 100 nF, 50 V, X7R, nonpolar. C4/C6 at U1 VM/VCC; C8/C10 at U2; C11 monitor. |
| R1–R4/R6–R10 Vishay TNPW0805…BEEA | Resistor_SMD:R_0805_2012Metric | Nonpolar. 0.1%, 25 ppm/K; full MPNs and nets below. |
| R5 Vishay PR02000203300JA100 | Resistor_THT:R_Axial_DIN0414_L11.9mm_D4.5mm_P15.24mm_Horizontal | 1 VM; 2 GND. 330 ohm, 5%, Cu leads, 2 W. Larger library body clearance is intentional; actual body max10×3.9 mm, meniscus length max12 mm, leads0.78±0.05 mm; library holes1.2 mm. |
| J1–J5 Phoenix Contact 1757242 | Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_2-G-5,08_1x02_P5.08mm_Horizontal | J1:1 MOTOR_IN,2 GND. J2:1 FL_OUT1,2 FL_OUT2. J3 FR pair; J4 BL pair; J5 BR pair. Nominal12 A, pitch5.08 mm, drill1.4 mm. Mating cable plug1757019 is off-board. |

| Ref | Full resistor MPN | Value | Net1 / net2 |
| --- | --- | --- | --- |
| R1 | TNPW080522K0BEEA | 22k | REV_PROTECTED / VM_GATE |
| R2 | TNPW08054K70BEEA | 4.7k | VM_GATE / VM_EN_COL |
| R3 | TNPW080510K0BEEA | 10k | LOGIC_GOOD / VM_EN_BASE |
| R4 | TNPW0805100KBEEA | 100k | VM_EN_BASE / GND |
| R6 | TNPW0805110KBEEA | 110k | VM / VM_UV_SENSE |
| R7 | TNPW080510K0BEEA | 10k | VM_UV_SENSE / GND |
| R8 | TNPW0805169KBEEA | 169k | VM / VM_OV_SENSE |
| R9 | TNPW080510K0BEEA | 10k | VM_OV_SENSE / GND |
| R10 | TNPW080510K0BEEA | 10k | PI_3V3 / VM_OK_RAW |

F1 needs a local footprint: two approximately 1.96×3.15 mm pads on 4.90 mm centers, matching the manufacturer's recommended 6.86 mm total pad span and 2.95 mm inner gap (rounding accounts for 0.01 mm). The local footprint uses the 1.96 mm recommended pad length. Body is 6.10±0.20 by 2.69±0.25 mm, height2.69±0.25 mm. Pin numbering is arbitrary because F1 is nonpolar. Connector polarity on the silk is a board convention and must be checked against the cable drawing; identical motor/power plugs are not intrinsically protected against cross-connection.

TB6612 pin mapping is: 1/2 AO1, 3/4 PGND1, 5/6 AO2, 7/8 BO2, 9/10 PGND2, 11/12 BO1, 13 VM2, 14 VM3, 15 PWMB, 16 BIN2, 17 BIN1, 18 GND, 19 STBY, 20 VCC, 21 AIN1, 22 AIN2, 23 PWMA, 24 VM1. Join duplicate output pads belonging to one output; never join AO1 to AO2, A to B, or outputs of different ICs. All VM pins go to VM and all GND/PGND pins to the common ground plane. VCC goes directly to PI_3V3. The Toshiba package is SSOP24-P-300-0.65A; its detailed local footprint review is separate from the generic SOT/SMB pad assignments here.

## Protection coordination and remaining limitations

F1 is a 2 A fuse with a stated maximum opening time of 5 seconds at twice rated current. Therefore it is wiring backup, not a motor-current limiter or semiconductor protector. Its nominal melting I²t is 0.530 A²s; a simultaneous 2.4 A/20 ms event gives0.115 A²s. That comparison is only a first screen: repetitive fatigue, ambient rerating, initial temperature and inrush remain relevant. Keep the external source current-limited and time-limited as specified. Q1 has no controlled inrush limiter: the initial 0.10 A source charging setting is mandatory, with STBY inhibited, before increasing the source ceiling for motor operation. A 3 A ceiling by itself does not establish Q1 linear-mode startup SOA. No direct arbitrary-battery fault interrupt test has been performed.

D2 has 7.0 V stand-off, 7.78–8.60 V breakdown at10 mA and a 12.0 V maximum clamping test point at50 A, 25 C. This gives nominal room below TB6612 VM limits, but the breakdown temperature coefficient is not a guaranteed clamp-voltage coefficient. Reserve hot-state clamp, lead-inductance and capacitor-current checks for physical validation. Normal <=3 mJ regeneration is handled by the capacitor/bleed budget without invoking avalanche. An abnormal brief pulse target of <=2.4 A, <=100 µs and <=1/s corresponds to <=2.9 mJ at12 V and0.01% duty; this is an engineering test envelope, not a demonstrated surge qualification. Sustained source overvoltage, downhill braking or external back-driving are outside the reference envelope.

At normal maximum6.5 V, R5 dissipates <=0.135 W including its −5% tolerance. Even13.5 V gives <=0.582 W. After motor input removal and with no further mechanical energy, maximum VM capacitance including the two local47 µF caps is approximately2.513 mF. With R5 at346.5 ohm, time constant <=0.871 s; 5 s ideally reduces6.5 V below0.021 V. Actual discharge must be measured; shorts, capacitor faults or back-driving invalidate the simple exponential.

The controlled sequence is: Pi logic on → supervisor qualifies logic → Q1 may charge VM under an initial 0.10 A source current limit → VM_OK stable → raise the source current ceiling to <=3.0 A → deliberate arm edge may enable drivers. Shutdown is: disarm → stop mechanical motion → switch off motor source upstream → wait at least5 s and verify VM<0.3 V while Pi logic stays on → turn off Pi. Phoenix specifies these connectors have no switching power; do not use plug removal under voltage/load as the motor-power switch.

On abrupt Pi power loss, Q1 turns off after logic qualification is lost, but charged VM capacitors and spinning motors can leave VM above VCC. Toshiba does not guarantee the output state or injection current for this condition. Neither its internal pull-downs nor the external STBY pull-down proves safety with VCC absent. This reference is suitable only with the stated controlled sequencing; abrupt Pi-loss behavior is an explicit review/physical-validation exception. It is not a safety-rated emergency-stop system.

## Source register

All links accessed 2026-09-28; source revisions below are from the documents, not search-engine publication dates. No availability, price, assembler acceptance or purchase claim is made.

| Source | Revision / sections used |
| --- | --- |
| [Toshiba TB6612FNG](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660) | Served revision2026-05-13, pp2–8: pins, powered modes/ranges, thermal/test conditions, application decoupling and package. Filename's20141001 is not the served footer date. |
| [AOS AO3401A](https://www.aosmd.com/pdfs/datasheet/AO3401A.pdf) | Rev3.1 December2023, pp1–2 ratings/pin-position drawing/electrical limits; pp3–4 typical curves and SOA. Pin-position drawing visually inspected; numbered standardSOT23 mapping checked against native pad positions. |
| [Vishay SSC54](https://www.vishay.com/docs/88885/ssc53l.pdf), [orderable suffix table](https://www.vishay.com/en/product/88885/tab/quality/) | Document88885 Rev23-Apr-2020, pp1–4 polarity/rating/VF conditions/body; appended disclaimer is newer and does not change datasheet revision. |
| [onsemi MMBT3904L](https://www.onsemi.com/pdf/datasheet/mmbt3904lt1-d.pdf) | August2021 Rev14, pp1–2 ratings/ordercode; SOT23CASE318STYLE6 drawing establishes1B/2E/3C. |
| [TI TPS3700](https://www.ti.com/lit/ds/symlink/tps3700.pdf), [TPS3700DDCR](https://www.ti.com/product/TPS3700/part-details/TPS3700DDCR) | SBVS187G February2019, pp4–6 pins/ranges/thresholds; §7.3.1 input range independent ofVDD; §§7.3.2/7.4 outputs/startup; DDC drawing/land pattern in package appendix. |
| [Littelfuse451/453](https://www.littelfuse.com/assetdocs/fuse-451-and-453-datasheet?assetguid=533cd5cc-956c-4243-867f-6ab5a62f6ba1) | RevisedGD12/01/25, pp1–4 time/current, resistance/I²t, rerating, part number and pad layout. |
| [LittelfuseSMBJ](https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet?assetguid=ba555e99-a12d-4f72-a0b6-86b06c67171e) | RevisedJC07/04/25v4, pp1–2 pulse conditions andSMBJ7.0A row; pp4–6 derating,SMB andordering. Supersedes earlier2025v2 copy considered during research. |
| [Panasonic FR-A](https://industrial.panasonic.com/cdbs/www-data/pdf/RDF0000/ABA0000C1259.pdf), [EEUFR1E102](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1E102), [EEUFR1E470](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1E470) | Datasheet01-Sep-2025, p1 tolerance/lead dimensions/ripple frequency factors; p2 impedance/ripple by size;25 V part table. Bulk nominal1000 µF±20%,2180 mArms at100 kHz,20 milliohm impedance at100 kHz. Do not interpret the website's inconsistent impedance unit label as0.02 milliohm. |
| [KEMET C0805C104K5RACTU](https://search.kemet.com/download/specsheet/C0805C104K5RACTU) | Generated2024-10-18, p1 values, dimensions, dielectric/temperature; EIA0805 nonpolar. |
| [Vishay TNPWe3](https://www.vishay.com/docs/28758/tnpw_e3.pdf) | Document28758 Rev10-Apr-2026, pp1–4 ratings/tolerance/range and full ordering-code construction. Values are valid E-series order codes, not inventory assertions. |
| [Vishay PR01/02/03](https://www.vishay.com/docs/28729/pr010203.pdf) | Document28729 Rev08-Jul-2025, pp1–3 power and ordering; p16 PR02 dimensions. |
| [Phoenix1757242](https://www.phoenixcontact.com/en-de/products/pcb-header-mstba-25-2-g-508-1757242?type=pdf), [mating1757019](https://www.phoenixcontact.com/en-us/products/pcb-plug-mstb-25-2-st-508-1757019) | Header catalog PDF generated2026-09-25, pp1–3 rating/pitch/body/drill; plug product page compatibility and no-switching-power note. NativeKiCad10 footprint names1757242 in its description. |

The custom fuse footprint was actually loaded with KiCad 10.0.6 pcbnew.FootprintLoad on 2026-09-28. The check confirmed two native pads, each 1.96×3.15 mm, at X=−2.45/+2.45 mm. All 32 power-stage/connector footprints were also loaded from the handoff JSON using KiCad 10.0.6, and each complete pad-number set matched its assigned pin map. These are parser/geometry checks, not assembly validation.

The circuit topology and pad mappings are an electrical design contract. Successful native-CAD opening, exported connectivity, ERC/DRC and layout review must be reported separately by the integrated project checks. No source inspection here constitutes a physical assembly or operating result.
