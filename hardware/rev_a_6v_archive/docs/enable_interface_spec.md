# Rev A enable, inhibit and independent watchdog interface

Status: **DESIGN REVIEW ONLY — NOT RELEASED FOR FABRICATION OR MOTOR OPERATION.** Date: 2026-09-28. This is a proposed reference circuit, not a measurement of the existing robot. No physical tests or new software work accompany this specification. The existing mock-only software does not implement this new electrical interface.

The accepted reference envelope is 6 V nominal motor input, 5.5–6.5 V input range, four motors each at most 0.25 A RMS and 0.6 A for 20 ms at at most 10% duty, ambient at most 40 °C, a separately powered Pi 5, and a common ground. The power specification adds assumptions concerning source current, stored energy and regenerative energy; these are design restrictions, not established motor characteristics. Actual motor ratings, stall current, inertia, wiring and polarity remain unverified.

The proposed circuit makes missing heartbeat, physical inhibit, absent run request, logic undervoltage and VM outside the monitored window clear a hardware arm latch. Clearing the condition alone cannot re-enable the motors. This circuit is a functional inhibit, not a certified emergency stop, personnel-protection circuit, electrical isolator or mechanical brake. Abrupt loss of Pi logic power while VM remains charged is an explicit unresolved restriction.

## Control architecture and external signals

Both TB6612 ICs receive the same A-side logic and the same B-side logic. Each H-bridge drives its own motor; **motor outputs are never connected in parallel**. User-confirmed placement is U1/A front-left, U1/B front-right, U2/A back-left and U2/B back-right. This reference therefore supports paired left/right control of four separate power channels, not four independent direction/speed commands.

The seven original BCM numbers below are confirmed only by legacy code. Reuse in this reference is **ASSUMED**, and does not establish the existing robot's physical connections. ARM and heartbeat assignments are new proposals. Pi physical pin numbers follow the official [Raspberry Pi GPIO header documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html).

| Pi BCM / physical pin | Reference signal | Default and meaning |
|---|---|---|
| GPIO18 / 12 | PWM_A | Low; paired left PWM, reference 1 kHz |
| GPIO23 / 16 | AIN1 | Low; paired left direction input 1 |
| GPIO24 / 18 | AIN2 | Low; paired left direction input 2 |
| GPIO13 / 33 | PWM_B | Low; paired right PWM, reference 1 kHz |
| GPIO5 / 29 | BIN1 | Low; paired right direction input 1 |
| GPIO6 / 31 | BIN2 | Low; paired right direction input 2 |
| GPIO25 / 22 | RUN_RAW → RUN_REQ | Low inhibits and clears arm; high requests permission only |
| GPIO17 / 11 | ARM_RAW → ARM_PULSE | Low normally; a new positive edge arms only while ALL_OK is high |
| GPIO27 / 13 | HB_RAW → HB | Falling-edge heartbeat; at most 50 ms between falling edges |
| Pi 3.3 V / 1 or 17 | PI_3V3 | Driver VCC and all interface IC supplies; assumed normal 3.2–3.4 V |
| Pi GND | GND | Common with driver logic, driver power ground and motor-source negative |

No motor current may return through the Pi cable. Connector pin allocation is defined in the native schematic/connector drawing and must not be inferred from this BCM table. There is no 5 V GPIO interface, no MCU and no direct connection from GPIO25 to TB6612 STBY.

The logic equations are:

```text
RAILS_OK = LOGIC_GOOD AND PHYS_OK AND VM_OK
ALL_OK   = RAILS_OK AND WD_OK AND RUN_REQ
ARM_Q    = 0 asynchronously whenever ALL_OK = 0
ARM_Q    = 1 on a positive ARM_PULSE edge while ALL_OK = 1
STBY_EN  = ARM_Q AND ALL_OK
STBY     = noninverting open-drain-buffer output, pulled up to driver VCC
```

The final AND also gates the output directly, so a fault does not wait for software or for a subsequent ARM clock. STBY low selects the TB6612 high-impedance standby state. It does not remove VM or guarantee zero motor speed. The [Toshiba TB6612FNG truth table and electrical specification](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660), pages 4–5, are the basis for this interpretation.

## IC pin and footprint contract

References U3–U10 and U12 below are the enable-circuit references; the separate VM monitor is assigned a unique reference by the complete schematic. Unused outputs have explicit no-connect flags. All supply pins have a local 100 nF bypass to GND. Open-drain pins must be represented as open collector/drain electrical types, not push-pull outputs, in the schematic.

| Ref / exact MPN | Pin-to-net connections | Native footprint |
|---|---|---|
| U3 SN74LVC07APWR | 1 PWM_A_RAW → 2 PWM_A; 3 AIN1_RAW → 4 AIN1; 5 AIN2_RAW → 6 AIN2; 9 PWM_B_RAW → 8 PWM_B; 11 BIN1_RAW → 10 BIN1; 13 BIN2_RAW → 12 BIN2; 7 GND; 14 PI_3V3 | Package_SO:TSSOP-14_4.4x5mm_P0.65mm |
| U4 TPS3431SDRBR | 1 VDD=PI_3V3; 2 CWD=WD_SELECT; 3 EN=LOGIC_GOOD; 4 GND; 5 SET1=PI_3V3; 6 WDI=HB; 7 WDO_n and 8 ENOUT tied to WD_RAW; exposed pad 9 GND | AI_Robot:TPS3431_DRB8_3x3_P0.65 |
| U5 SN74LVC1G74DCUR | 1 CLK=ARM_PULSE; 2 D=PI_3V3; 3 inverted Q=NC; 4 GND; 5 Q=ARM_Q; 6 CLR_n=ALL_OK; 7 PRE_n=PI_3V3; 8 VCC=PI_3V3 | AI_Robot:TI_DCU0008A |
| U6 SN74LVC11APWR | 1 LOGIC_GOOD, 2 PHYS_OK, 13 VM_OK → 12 RAILS_OK; 3 RAILS_OK, 4 WD_OK, 5 RUN_REQ → 6 ALL_OK; 9 ARM_Q, 10 ALL_OK, 11 PI_3V3 → 8 STBY_EN; 7 GND; 14 PI_3V3 | Package_SO:TSSOP-14_4.4x5mm_P0.65mm |
| U7 TPS3839G33DBZR | 1 GND; 2 RESET_n=LOGIC_GOOD; 3 VDD=PI_3V3 | Package_TO_SOT_SMD:SOT-23 |
| U8 SN74LVC2G17DBVR | 1 PHYS_RAW → 6 PHYS_OK; 3 WD_RAW → 4 WD_OK; 2 GND; 5 PI_3V3 | Package_TO_SOT_SMD:SOT-23-6 |
| U9 SN74LVC2G17DBVR | 1 VM_OK_RAW → 6 VM_OK; 3 HB_RAW → 4 HB; 2 GND; 5 PI_3V3 | Package_TO_SOT_SMD:SOT-23-6 |
| U10 SN74LVC1G07DBVR | 1 NC; 2 A=STBY_EN; 3 GND; 4 Y=STBY; 5 VCC=PI_3V3 | Package_TO_SOT_SMD:SOT-23-5 |
| U12 SN74LVC2G17DBVR | 1 RUN_RAW → 6 RUN_REQ; 3 ARM_RAW → 4 ARM_PULSE; 2 GND; 5 PI_3V3 | Package_TO_SOT_SMD:SOT-23-6 |

The single-buffer and dual-buffer SOT-23 variants have different pin maps; their footprints are not interchangeable. In particular the dual Schmitt part is six pins, with supply on pin 5 and ground on pin 2. U5 is DCU VSSOP, not the larger DCT package.

U3 is noninverting with open-drain outputs: low input sinks its output, high input releases it. This references the high logic level to the same PI_3V3 rail as TB6612 VCC. The LVC devices provide Ioff behavior at VCC=0, reducing back-powering from a still-driven Pi GPIO. This does not establish complete power-off behavior of the TB6612 itself. See the manufacturer [SN74LVC07A](https://www.ti.com/lit/ds/symlink/sn74lvc07a.pdf), [SN74LVC1G07](https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf), [SN74LVC2G17](https://www.ti.com/lit/ds/symlink/sn74lvc2g17.pdf), [SN74LVC1G74](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf) and [SN74LVC11A](https://www.ti.com/lit/gpn/sn74lvc11a) pin tables and package drawings.

## Passive connectivity, physical inhibit and component values

All interface resistors are Yageo RC0603, 1%, 0.1 W; do not substitute larger tolerances without updating the level calculations.

| Ref(s) | Value / exact MPN | Connectivity |
|---|---|---|
| R100,104,108,112,116,120 | 330 Ω / RC0603FR-07330RL | GPIO18,23,24,13,5,6 respectively to corresponding U3 RAW input |
| R101,105,109,113,117,121 | 10 kΩ / RC0603FR-0710KL | Each corresponding U3 RAW input to GND |
| R102,106,110,114,118,122 | 1 kΩ / RC0603FR-071KL | PI_3V3 to each U3 output |
| R103,107,111,115,119,123 | 10 kΩ / RC0603FR-0710KL | Each shared U3 output net to GND |
| R124,126,128 | 330 Ω / RC0603FR-07330RL | GPIO25→RUN_RAW; GPIO17→ARM_RAW; GPIO27→HB_RAW |
| R125,127,129 | 10 kΩ / RC0603FR-0710KL | RUN_RAW, ARM_RAW, HB_RAW respectively to GND |
| R130 | 10 kΩ / RC0603FR-0710KL | PI_3V3 to WD_SELECT, close to U4 pin 2 |
| R131 | 10 kΩ / RC0603FR-0710KL | PI_3V3 to WD_RAW |
| R132 | 100 kΩ / RC0603FR-07100KL | HB to GND |
| R133 | 1 kΩ / RC0603FR-071KL | PI_3V3 to PHYS_SUPPLY |
| R134 | 10 kΩ / RC0603FR-0710KL | PHYS_RAW to GND |
| R135 | 1 kΩ / RC0603FR-071KL | PI_3V3 to common STBY |
| R136,137 | 10 kΩ / RC0603FR-0710KL | STBY to GND, one physically at each driver pin 19 |
| R138 | 100 kΩ / RC0603FR-07100KL | LOGIC_GOOD to GND |
| R139,140,141 | 10 kΩ / RC0603FR-0710KL | ARM_Q, ALL_OK, STBY_EN respectively to GND |
| C100 | 1 nF, 5%, 50 V C0G / GRM1885C1H102JA01D | PHYS_RAW to GND |
| C101–C109 | 100 nF, 10%, 50 V X7R / CC0603KRX7R9BB104 | Local supply bypass for U3–U10 and U12 respectively |

Resistor and capacitor footprints are `Resistor_SMD:R_0603_1608Metric` and `Capacitor_SMD:C_0603_1608Metric`. Manufacturer specifications: [330 Ω](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-07330RL), [1 kΩ](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-071KL), [10 kΩ](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-0710KL), [100 kΩ](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-07100KL), [100 nF](https://yageogroup.com/component-documentation/download/specsheet/CC0603KRX7R9BB104). The [Murata-authored 1 nF product sheet](https://datasheet.octopart.com/GRM1885C1H102JA01D-Murata-datasheet-140695818.pdf) was retrieved from an archive because the manufacturer's direct file returned HTTP 403; its 2020 revision must be refreshed before procurement. No procurement is authorized in this phase.

SW1 is C&K **JS102011SAQN**, nonshorting SPDT, in `Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN`. Pin 2 common goes to PHYS_RAW; pin 1 goes to PHYS_SUPPLY; pin 3 goes to GND. The mechanical mounting pads have no electrical net. Use the pin-1 mark and the [manufacturer JS drawing](https://www.ckswitches.com/media/1422/js.pdf), JS102011SAQN page, to establish actuator position; label the actual two positions **MOTOR INHIBIT** and **ENABLE** on the board. Locate the actuator at an accessible board edge.

In INHIBIT, SW1 grounds only a logic-input node. It never shorts an actively driven Pi output. In ENABLE, the 1 kΩ/10 kΩ divider yields about 0.909×PI_3V3 at PHYS_RAW. An open contact or missing switch connection decays low through R134. C100 filters brief contact noise; this is not a certified debounce or fault-detection network. Its nominal enable time constant is 0.91 µs and open-contact decay constant 10 µs, with approximately ±6% R/C initial tolerance. The switch's silver contacts carry only about 0.3 mA in ENABLE; minimum-load/contact reliability remains a later physical qualification item.

U8/U9/U12 use Schmitt inputs for slow physical, open-drain and ARM/RUN/HB signals. Six U3 motor inputs still require fast actively driven GPIO edges within the LVC07 input-transition limit; the reference assumes a short logic harness and PCB traces, not arbitrary cable length. Connect/disconnect only with physical inhibit selected and motor power removed. This is not a hot-plug interface.

## Watchdog, arm timing and recovery

U4 uses the factory 200 ms option, selected by SET1 high and CWD connected to VDD through R130=10 kΩ ±1% (9.9–10.1 kΩ, inside the specified 9–11 kΩ selection range). No external timing capacitor is fitted. The guaranteed timeout and reset-low interval are each 170–230 ms. A missing WDI falling edge asserts WDO low. ENOUT is also tied to WD_RAW so deasserting EN cannot appear healthy merely because WDO is released. The [TPS3431 datasheet](https://www.ti.com/lit/ds/symlink/tps3431.pdf), pin table, timing table and sections 7.3/8.1, support this configuration.

The following behavior is a **future firmware contract**, not implemented or physically tested here:

1. Keep RUN_RAW, ARM_RAW and both PWM GPIOs low throughout initialization. Direction inputs start low.
2. Start heartbeat under the same command-arbitration health decision that owns movement. Provide high and low intervals of at least 1 ms, and a falling edge at least once every 50 ms. Do not use a free-running peripheral or an independent heartbeat worker that survives failure of the motion arbiter.
3. Wait at least 1 s after stable supplies and at least three correctly scheduled heartbeat cycles before accepting an explicit operator arm request. ARM remains low. Establish zero PWM/direction before setting RUN_RAW high.
4. After RUN_REQ and all fault conditions have been stable high for at least 1 ms, issue one ARM high pulse of at least 1 ms and return it low. Software must not automatically repeat arm on reconnect, boot or fault recovery.
5. Any stop/fault sets RUN_RAW low, PWM low and ARM_RAW low. Recover only after checking the cause and accepting a new explicit operator arm request.

The board has no proof that a valid heartbeat occurred before the first arm; during the watchdog's initial grace interval, an erroneous ARM command can still enable briefly. The startup rule above reduces that exposure but is not a hardware guarantee. Holding ARM high through a fault does not re-arm when the fault clears. A fresh rising edge is required. Keep ARM away from the asynchronous-clear release boundary; the 1 ms qualification rule greatly exceeds the DFF's nanosecond timing requirements but needs a future implementation review.

Missing or stuck-high/low heartbeat leads to watchdog assertion within 230 ms of the last accepted falling edge, followed by logic/driver propagation. This is not a measured maximum mechanical stopping time or a complete system reaction-time certification. WD_RAW can later return high after its reset interval even if heartbeat remains absent, but ARM_Q remains zero; no automatic restart results. A software fault that continues valid heartbeat can evade this monitor.

| Event, with logic rail operating | ARM_Q / STBY result | Recovery |
|---|---|---|
| Startup; RUN low | Cleared / low | Explicit initialization and arm |
| SW1 moves to INHIBIT or PHYS contact opens | Cleared / low | ENABLE alone does not restart |
| RUN_REQ low | Cleared / low | RUN high alone does not restart |
| Missing/stuck HB reaches timeout | Cleared / low | Restored HB alone does not restart |
| VM under/overvoltage | Cleared / low | VM return alone does not restart |
| Logic undervoltage recognized | Cleared while logic remains operating; VM input switch opens | Reinitialize and arm after recovery |
| ARM held high while ALL_OK returns | Remains cleared / low | ARM must first return low, then new positive edge |
| All conditions valid and explicit ARM rising edge | Set / high | PWM/direction may command movement within reference bounds |

## Logic levels and power-sequence audit

U7's 3.08 V threshold option has a 3.003–3.126 V falling threshold and 120–350 ms reset-release delay. Its 20 µs falling response is typical, not a guaranteed maximum. The proposed normal 3.2–3.4 V PI_3V3 range provides threshold margin; it must be verified at the board before later operation. Refer to the [TPS3839 electrical table](https://www.ti.com/lit/ds/symlink/tps3839.pdf).

LOGIC_GOOD drives two CMOS inputs, R138=100 kΩ and the power circuit's 10 kΩ NPN base resistor. Even treating the base path as a short to ground, at 3.4 V this is below 0.39 mA including a 10 µA input allowance, below the supervisor's 0.5 mA VOH test load. Its specified VOH of at least VDD−0.4 V meets both LVC's 2.0 V input-high requirement and watchdog EN's 0.8×VDD requirement over the reference range.

The 330 Ω/10 kΩ input divider requires the Pi high level to exceed approximately 2.07 V for U3's 2.0 V input-high threshold; nominal 3.3 V is not itself a worst-case Pi VOH guarantee. Future harness qualification must include high/low levels and edge rate. A high GPIO supplies about 0.33 mA per input pulldown.

At PI_3V3=3.2 V, a 1.01 kΩ pullup, 9.9 kΩ output pulldown and 60 µA aggregate sink allowance give a U3 output of about 2.85 V. The two STBY pulldowns in parallel give about 2.61 V. Both exceed TB6612's 0.7×VCC=2.24 V requirement. This allowance includes two published 25 µA input-current maxima at the datasheet's 3 V test point and 10 µA buffer leakage; it is a review calculation, not a full temperature/supply qualification of input current. The buffer's conservative 0.55 V low-level limit is below 0.3×3.2 V=0.96 V. Use 1 kΩ pullups, not weak 10 kΩ substitutions.

Seven 1 kΩ output pullups draw at most about 24.1 mA total at 3.4 V when low, before other logic loads. Allow at least 50 mA of board-interface load in the Pi 3.3 V power budget and separately include driver VCC and all other peripherals. This allocation is not a statement of the Pi rail's measured spare capacity. Each pullup dissipates less than 12 mW versus its 100 mW rating. At an assumed output-net capacitance of 100 pF, 1 kΩ gives a nominal 0.1 µs RC constant, small relative to a 1 ms PWM period; actual capacitance and waveform remain unmeasured.

The power circuit drives AO3401A Q1 from LOGIC_GOOD through MMBT3904 Q2. Q1 source is REV_PROTECTED, drain is VM and gate has 22 kΩ to source; Q2 pulls the gate through 4.7 kΩ. Q2 emitter is GND, base is fed through 10 kΩ with 100 kΩ base pulldown. The gate network yields approximately −0.824×REV_PROTECTED VGS, around −4.0 to −5.4 V in the reference range, inside Q1's ±12 V rating. Use its −2.5 V RDS(on) limit for conservative loss calculations; a −4.5 V-only number does not cover every low-voltage corner. Sources: [AO3401A](https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf) and [MMBT3904](https://www.onsemi.com/pdf/datasheet/mmbt3904lt1-d.pdf).

Q1 enable depends on LOGIC_GOOD alone. Making it depend on VM_OK would create a startup deadlock because VM cannot become good while its own supply switch is off. The TPS3700 monitor instead qualifies ALL_OK: OUTA pin 1 and OUTB pin 6 form VM_OK_RAW with a 10 kΩ PI_3V3 pullup; pin 2 GND, pin 5 PI_3V3, pin 3 UV divider 110 kΩ/10 kΩ, pin 4 OV divider 169 kΩ/10 kΩ. All divider resistors are 0.1%. Nominal rising thresholds are 4.80 V UV release and 7.16 V OV assertion; hysteresis/tolerance calculations belong to the power specification. The [TPS3700 datasheet](https://www.ti.com/lit/ds/symlink/tps3700.pdf) permits tying the two open-drain outputs and requires accounting for its power-on state.

| Supply condition | Intended behavior and remaining limitation |
|---|---|
| Both rails absent | External pulldowns define low nodes; no energized motor source |
| Pi logic valid, motor source absent | VM_OK low clears arm; Pi GPIO may be initialized safely |
| Motor source present before Pi | Q1 gate-source pullup keeps the VM feed off; this assumes no external VM injection or previous charge |
| Pi rising with motor source present | Supervisor holds inhibit, then enables VM feed; arm stays cleared until explicit command |
| Normal controlled shutdown | Inhibit and RUN low first; remove motor source while retaining Pi3V3; wait until VM is below 0.3 V; only then remove Pi power |
| Abrupt Pi loss while VM charged or motors regenerate | Q1 eventually disconnects feed, but stored VM and motor energy remain; TB6612 VCC=0 behavior is not guaranteed. **Unrestricted use remains blocked.** |
| GPIO cable loses 3.3 V but signal pins remain driven | LVC Ioff limits interface back-powering at VCC=0; no claim of whole-board safe operation during partial supply or broken ground |
| Ground opens, GPIO overvoltage, shorted gate/latch or welded switch | Not detected/redundantly controlled by this circuit; outside the reference safety claim |

The 330 Ω bleed and 2×1000 µF plus 2×47 µF VM capacitance have nominal RC≈0.691 s. With +5% resistor and +20% capacitance, RC≈0.871 s; from 6.5 V to 0.3 V takes about 2.68 s with source disconnected and no regeneration. **Use the measured voltage, not a timer alone**, for a later controlled shutdown procedure. Q1 has a body diode and is not a bidirectional isolator. The input Schottky blocks source backfeed but does not absorb all regenerated energy. VM overvoltage inhibition does not clamp VM, enforce motor current, or establish a safe energy limit; refer to the separate power calculations.

## Watchdog footprint and digital review evidence

U5 uses the custom [TI_DCU0008A.kicad_mod](../libraries/AI_Robot.pretty/TI_DCU0008A.kicad_mod), matching TI example land pattern 4225266/A, 09/2014, on SN74LVC1G74 datasheet page 23: 0.85×0.30 mm pads at 0.50 mm pitch, row centers x=±1.55 mm, nominal corner radius 0.05 mm. The 0.20 mm copper gap meets the project minimum without a 0.15 mm clearance exception. The footprint sets 0.04 mm NSMD expansion, leaving 0.12 mm nominal mask web, within TI's maximum 0.05 mm expansion recommendation. The generic VSSOP 3D body is retained.

The custom footprint [TPS3431_DRB8_3x3_P0.65.kicad_mod](../libraries/AI_Robot.pretty/TPS3431_DRB8_3x3_P0.65.kicad_mod) uses TI DRB0008A drawing 4218875/A, 01/2018, in TPS3431 datasheet pages 28–30. Signal pad centers are x=±1.4 mm and y=±0.975/±0.325 mm; pads are 0.60×0.31 mm. Pad 9 includes the 1.50×1.75 mm center land and four manufacturer's exposed-pad extensions. Its matching paste windows are retained. All pad-9 shapes are one GND electrical pad.

Optional through-pad thermal vias and the stock footprint's bottom EP land were removed. There are **no drilled holes, buried vias or open via-in-pad** in this footprint. Connect the exposed-pad extensions to top copper GND and connect that copper to the ground plane with ordinary vias outside the solder/paste land. The generic DFN 3D model has the correct nominal 3×3 mm body and 0.65 mm pitch, but its underside exposed-pad geometry is approximate; the 3D image is not land-pattern evidence.

SW1 uses a project-authored nominal VRML model because the installed official KiCad bundle lacks the referenced switch STEP file. The model depicts a 9×3.6×3.5 mm nominal housing, simplified terminals/locating pegs and one actuator position; standoff, pin bends and actuator details are approximate. It does not prove contact position or mechanical fit. U4/U5 use the declared generic package models. All three model bindings use project-relative `${KIPRJMOD}/libraries/3dmodels/` paths. A library audit resolved all 22 model references to included files; model parsing/rendering of the assembled board is reported separately.

Digital work completed for this interface: primary IC pin/behavior/package checks, SW1 drawing review, resistor/level/timing calculations, custom-footprint inspection and successful load with KiCad 10.0.6's `pcbnew.FootprintLoad`. Loaded logical pad numbers are 1–9 and every footprint pad has zero drill size. A separate Boolean desk review checked the manifest's U5/U6 pin connections and all 64 combinations of the five qualifiers and prior arm state; only the all-true, armed combination permits STBY. A held-high ARM fault/recovery sequence stays disarmed. This is a logic-equation check without analog timing or metastability simulation. These checks do not claim a routed-board DRC result, electrical simulation, bench waveform, thermal validation or motor-stop test. The complete project reports ERC/DRC separately. The 62 interface parts in the source connectivity description were compared against the integrated manifest, with matching pins and footprints after the accepted U5/U12 changes. No software test counts were changed by this design-only work.

Before fabrication release, the full schematic/PCB review must resolve or explicitly retain the following restrictions: actual motor/wire/polarity mapping; current and regenerative-energy envelope; abrupt PI_3V3 loss with energized VM; input supply/inrush and fuse coordination; header/harness orientation and levels; IC land-pattern/paste review; and a future firmware implementation that honors this interface. Physical tests, including heartbeat loss, switch operation, stuck ARM, rail sequencing, reversal current and loaded stopping behavior, remain deferred to a separately authorized phase.

Review records: [native footprint geometry](../validation/design/enable_footprints.json), [included model paths](../validation/design/model_paths.json), and [Boolean hardware logic desk review](../validation/design/hardware_logic_desk_review.json). Each record states its limited scope and hashes the reviewed source snapshot.
