# Motor-driver margin review — provisional 12 V redesign

**2026-09-28 — Select Branch B: four DRV8874PWPR drivers. Do not retain dual TB6612FNG as the recommended custom-board architecture.**

Fabrication: **DEFERRED**. Assembly: **NOT ASSEMBLED**. Physical validation: **NOT TESTED**. This is a pre-fabrication design review, not a report of a hardware failure.

## Scope and evidence

The user reports four motors, two WHEELTEC R3 chassis, two TB6612 carrier boards and two lithium packs sold as 12 V. **MG513P30_12V remains unconfirmed.** Its published 0.36 A rated / 3.2 A stall values are conditional analysis inputs only; see [primary-source review](wheeltec_source_review.md). The carrier boards' regulators, logic supplies and protection remain undocumented. Battery listing claims are not verified BMS trip characteristics.

The proposed electrical case is **9–15 V source operation**, with a coordinated VM transient ceiling of **32 V**, ambient at most **40°C**, and an independently supplied Pi. This is a selected design envelope, not a claim about the purchased packs. In particular, **12.6 V and 3S chemistry are not established**. The power-path review supplies the detailed clamp, eFuse and capacitor conditions.

## Branch A — TB6612FNG: reject for this envelope

[Toshiba's current datasheet](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660), served revision **2026-05-13**, specifies:

| Item | Published condition |
|---|---|
| VM operating / absolute maximum | 2.5–13.5 V / 15 V |
| Operating output current | 1 A/channel, VM ≥4.5 V, without PWM |
| Absolute average current | 1.2 A/channel |
| Absolute pulse entries | 2 A, 20 ms, duty ≤20%; 3.2 A, single 10 ms |
| Package dissipation at 25°C | 0.78 W bare; 0.89 W / 1.36 W on specified test boards |
| Bridge voltage drop | 0.5 V typical / 0.7 V maximum at 1 A under the stated 25°C test conditions |

The candidate's rated-current point is modest, but **3.2 A stall has no margin against a single-pulse absolute limit**. Startup duration is unknown. A sustained or repeated stall is not that pulse condition. There is no adjustable per-channel current regulator, and thermal shutdown is not the operating protection strategy. Moreover, 15 V normal source operation already exceeds the recommended VM maximum; a 32 V transient ceiling is incompatible.

For an illustrative conduction-only screen, assume both channels carry equal RMS current and use `Ppackage = 2 × I² × 0.7 Ω`. This extrapolates the stated voltage-drop test point; it is not a guaranteed hot resistance or transient model.

| Conditional current per motor | One dual-channel package | Two packages / four motors |
|---|---:|---:|
| 0.36 A running example | 0.181 W | 0.363 W |
| 0.80 A hypothetical constrained load | 0.896 W | 1.792 W |
| 3.20 A unregulated startup/stall screen | 14.336 W | 28.672 W |

The last row is a rejection screen, not an allowable operating point. At 40°C, linear reading of Toshiba's dissipation curves gives approximately 0.686/0.783/1.197 W for its three stated mounting cases. Actual board performance can differ. A separate 1 Ω hot-path allowance would increase the 0.36 A example to 0.259 W/package before switching and supply losses. Normal running can therefore look reasonable while startup/stall remains unacceptable. Neither the 3.2 A headline nor low average PWM duty proves safe winding-current peaks; current also circulates during PWM off intervals.

Branch A would require a different, verified low-current motor envelope, a suitably constrained rail and effective individual current protection. It is not an approved fallback for the purchased hardware.

## Branch B — selected replacement and alternatives

| Architecture | Practical assessment |
|---|---|
| Two TB6612FNG | Closest to the prototype, but rejected above; simultaneous package heating and narrow voltage margin dominate. |
| Four DRV8876PWPR | Hardware current regulation, current feedback, fault reporting and 3.3 V control are available. Its typical bridge resistance is 0.7 Ω: 3.5 times DRV8874's at the same current. Additional heat and lower transient headroom make it the secondary choice. |
| **Four DRV8874PWPR** | **Selected.** One bridge per motor, lower conduction loss, hardware current chopping and a hardware fault output. More ICs and charge-pump components, but manageable without an added MCU. |

The [DRV8874 product specification](https://www.ti.com/product/DRV8874) gives 4.5–37 V operation, 3.3 V logic support, 0.2 Ω typical bridge resistance and integrated current sensing/regulation. The [DRV8876 specification](https://www.ti.com/product/DRV8876) supports the alternative comparison. The choice is based on bounded current, loss and protection behavior; **6 A peak is not a 6 A continuous board rating**. TI's [evaluation-module guide](https://www.ti.com/lit/ug/slvubg7c/slvubg7c.pdf), SLVUBG7C, separately limits extended operation according to its own PCB and temperature conditions; those EVM limits are not transferred to this board.

Keep **four separate output bridges but two logical left/right command groups**. Front-left and back-left share a decoded PWM/direction command; front-right and back-right share the other command. Pairing control signals does not parallel motor outputs or create four independent wheel commands. Retaining this behavior preserves the prototype's steering concept while changing the physical driver interface.

## Current-limit selection

Per driver, select a 20.0 kΩ upper / 10.0 kΩ lower VREF divider from PI_3V3, and **3.09 kΩ from IPROPI to GND**. All three resistors: **0.1%, ≤25 ppm/°C**. PI_3V3 remains a **3.2–3.4 V** design requirement.

Using `ITRIP = VREF / (450 µA/A × RIPROPI)` and the applicable ±7.5% current-sense error:

| Calculation | Result |
|---|---:|
| Nominal VREF / ITRIP | 1.100 V / 0.7911 A |
| VREF with supply and initial resistor tolerance | 1.0652–1.1348 V |
| Static ITRIP, initial tolerances | 0.7119–0.8832 A |
| Static ITRIP with ±0.35% total resistor allowance | **0.7078–0.8884 A** |
| Four-channel sum of that upper static threshold | **3.5535 A** |

The ±0.35% allowance combines initial tolerance with a conservative 100°C excursion at the specified TCR. These are static threshold calculations; sensing delay, blanking, switching overshoot, noise and component faults are not included. The physical peak waveform must be measured. Do not use the application example's 455 µA/A value in place of the electrical-table value used here.

The coordinated input eFuse is approximately **2.98 A nominal**, with a separate provisional **2.66–3.31 A** tolerance screen and latch-off. It does not guarantee that four simultaneous starts succeed: 3.5535 A of instantaneous phase-current demand can exceed its lower limit. PWM recirculation means phase current and battery average current differ; local capacitors also affect the waveform. Normal 4×0.36 A demand is 1.44 A before overhead, but motor acceleration, synchronous PWM pulses and supply collapse remain validation cases. A safe nuisance trip is preferable to quietly increasing either limiter.

## Four-driver thermal screen

This is a calculated design allocation, **not thermal simulation or qualification**. Follow the loss categories in TI's [H-bridge power-dissipation application report](https://www.ti.com/lit/an/slva504/slva504.pdf), SLVA504A: conduction, switching, dead time and supply consumption.

For a conservative provisional screen use 15 V, 7 mA active supply current, **0.4 Ω hot bridge allowance**, 600 ns combined rise/fall allowance, 0.4 µs combined dead time, 1 V diode drop and **80 kHz switching-cycle allowance**. The latter includes external PWM capped at 20 kHz and additional fixed-off-time current chopping; it is an engineering allowance to verify, not a guaranteed oscillator maximum.

`Pdriver ≈ 0.4 I_RMS² + 0.392 I_RMS + 0.105 W`

| Conditional load | Each driver | Four drivers | Estimated junction at 40°C and effective 80°C/W |
|---|---:|---:|---:|
| 0.36 A running example | 0.298 W | 1.192 W | 63.8°C |
| 0.7911 A nominal limiting | 0.665 W | 2.662 W | 93.2°C |
| 0.8884 A upper static threshold | 0.769 W | 3.076 W | 101.5°C |
| 1.00 A RMS design allocation | 0.897 W | 3.588 W | 111.8°C |

Allocate **0.90 W per driver / 3.60 W total**, target junction below **125°C**, and require effective junction-to-ambient resistance at most **80°C/W**, including board heating from adjacent drivers and power-path components. Begin layout with at least **4 cm² of ground copper spreading per driver**, connections to both copper layers and thermal vias. Do not simply assign the package's 36°C/W JEDEC figure to this two-layer PCB. Copper area, via arrangement, airflow and enclosure temperature need subsequent verification. [TI motor-driver layout guidance](https://www.ti.com/lit/pdf/slva959) explains the associated layout considerations.

At the hypothetical unregulated 3.2 A point, this same screen becomes 5.46 W/device, far outside the allocation. Thus the design depends on functioning current regulation; the replacement is not approved for unrestricted 3.2 A continuous stall. Startup duration does not need to be assumed short to pass the **driver's** bounded-current thermal screen. Startup torque and **motor** temperature are separate unresolved requirements.

## Control, fault response and implementation details

Use **PWM-input mode, PMODE=PI_3V3**, with IMODE intentionally floating for fixed-off-time chopping and latched overcurrent response. The Pi harness still supplies one PWM and one direction signal per side. U15 SN74LVC2G14DBVR creates inverted direction, U16 SN74LVC132APWR generates the two NAND terms, and U3 SN74LVC08APWR gates each resulting driver input with the latched motion permission A:

`IN1 = A AND NOT(PWM AND NOT(DIR))`

`IN2 = A AND NOT(PWM AND DIR)`

| Permission A | PWM | DIR | Driver inputs IN1/IN2 | Result while awake |
|---|---|---|---|---|
| 0 | Any | Any | 0/0 | Coast/high impedance |
| 1 | 0 | Any | 1/1 | Brake/low-side slow decay |
| 1 | 1 | 0 | 0/1 | Reverse |
| 1 | 1 | 1 | 1/0 | Forward |

This preserves brake recirculation during armed PWM off-time, which is the basis of the loss screen above, while disarm coasts. [TI's driver truth table](https://www.ti.com/lit/ds/symlink/drv8874.pdf), Table 4, defines these states. Direction polarity at each wheel remains a wiring/bench item.

**Driver wake and motion permission are separate.** nSLEEP follows FEED_ENABLE=LOGIC_GOOD AND PHYS_OK, independent of ARM and nFAULT. The drivers wake as the supply ramps, with commands blocked. This avoids the normal nFAULT wake pulse in TI Figure 28 immediately clearing the very latch that woke the drivers. Power-good, rail monitor and driver faults qualify the external arm latch; a fresh ARM edge is required after the rail and driver have settled. RUN low, watchdog expiry or a reported fault clears the arm latch and makes both driver inputs low. They do not automatically put the drivers to sleep.

Physical disable lowers FEED_ENABLE, lowers driver nSLEEP and shuts the eFuse input feed; the bridge becomes high impedance after its sleep transition. It does not instantly discharge VM. Latched driver overcurrent now requires a deliberate physical-disable/re-enable or motor-power cycle to reset the driver, followed by a fresh ARM edge. Clearing a thermal or undervoltage fault does not restore the external arm latch. Keep PWM low before ARM; change direction only with PWM already low, then allow logic settling and a motor-specific deceleration/reversal interval before raising PWM. The decoder has no reversal timer and gate propagation delays are not a motor-current safety guarantee.

The raw command input stages use Schmitt inputs; final gating actively drives low rather than relying on a slow passive pull-down to cross an ordinary logic threshold. At the specified 3.2–3.4 V logic rail, require command GPIO levels of **at least 2.8 V high and at most 0.4 V low at J6**, with a short common-ground harness. These are interface requirements, not measured Pi performance. SN74LVC2G14 threshold interpolation gives a worst rising threshold of 2.44 V; TI [explicitly recommends this interpolation method](https://e2e.ti.com/support/logic-group/logic/f/logic-forum/773128/sn74lvc2g14-threshold-voltage). Including the 330 Ω/10 kΩ input network tolerances and 10 µA total input leakage, those GPIO levels give at least 2.705 V high and at most 0.391 V low at the receiving inputs. Retain the active-edge requirement of at most 10 ns/V and no hot-plug: the SN74LVC132A datasheet lists that limit despite also describing slow-input tolerance.

Fixed-off-time chopping itself does **not** assert nFAULT. An analog current indication is not an integrated stall timer, and Pi GPIO has no analog-input function. Preserve each IPROPI as an individual test/measurement node; do not join these outputs. No extra filtered-current timer is required for the provisional driver heat allocation, but **motor stall protection is not thereby established**. Prohibit sustained stalls; require bounded commands and subsequent motor-specific timeout validation. A heartbeat watchdog detects missing heartbeat, not a stalled motor while valid heartbeats continue. Do not populate a large IPROPI filter capacitor casually: it can delay regulation.

Exact selected MPN: **DRV8874PWPR**, HTSSOP-16 PowerPAD, package drawing **PWP0016J**. The [datasheet](https://www.ti.com/lit/ds/symlink/drv8874.pdf), SLVSF66A (December 2019), supplies this pin map:

| Pin | Function | Pin | Function |
|---:|---|---:|---|
| 1 | EN/IN1 | 9 | PGND |
| 2 | PH/IN2 | 10 | OUT2 |
| 3 | nSLEEP | 11 | VM |
| 4 | nFAULT | 12 | VCP |
| 5 | VREF | 13 | CPH |
| 6 | IPROPI | 14 | CPL |
| 7 | IMODE | 15 | GND |
| 8 | OUT1 | 16 | PMODE |
| Exposed pad | GND; use CAD pad 17 | | |

IN1/IN2/nSLEEP need at least 1.5 V high. U3 actively drives the four decoded command nets. U14 actively drives the shared FEED_ENABLE/nSLEEP net, with four local 10 kΩ pull-downs plus the internal driver pull-downs; no shared 330 Ω enable pull-up is used. Each driver needs local VM bypass/bulk capacitance, 22 nF CPH–CPL and 100 nF VCP–VM charge-pump capacitance. Use the reviewed voltage ratings; VCP–VM is a differential connection, not VCP–GND.

Use a project footprint matched to TI drawing **4223595/B, December 2023**, rather than an unverified generic exposed-pad option: body 4.4×5 mm, 0.65 mm lead pitch; lead lands 1.50×0.45 mm, row centers ±2.90 mm; grounded thermal copper 3.4×5.0 mm, mask opening 2.46×3.55 mm. Its stencil example uses a 2.46×3.55 mm opening at 0.125 mm thickness. Exposed-pad soldering and heat removal are essential. The final [selective process map](../exports/draft/drills/selective_via_fill_map.csv) identifies 13 holes under paste that require filled, capped and planarized treatment. Ordinary tenting is not a substitute. The sixteen DRV thermal holes remain outside paste and require the separately specified tented process; supplier acceptance is unqualified. [TI PowerPAD guidance](https://www.ti.com/lit/pdf/slma002) supports the assembly review.

## Release conditions

The replacement architecture is selected for the provisional CAD redesign, not cleared for the actual robot. Before powered validation or fabrication release, establish motor identity, pack voltage/topology, required starting torque, encoder/interface levels and actual wiring. Verify limiter peaks, simultaneous starts, source fault recovery, regeneration, four-driver thermal coupling, sleep/coast behavior and absence of automatic restart. CAD ERC/DRC results are reported separately and do not satisfy these physical checks. No software GPIO backend or real-motor compatibility claim is introduced by this review.
