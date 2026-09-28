# Rev A 12 V reference — enable, inhibit and watchdog interface

**2026-09-28. DESIGN REVIEW ONLY. Fabrication deferred; not assembled or physically tested.** This describes the revised custom board, not the purchased TB6612 carriers. The existing software remains mock-only and does not implement this GPIO interface. The prior 6 V design is preserved separately in `hardware/rev_a_6v_archive`.

The selected reference uses a **9–15 V source**, four DRV8874PWPR bridges, a separately supplied Pi 5, **3.2–3.4 V PI_3V3**, common ground, ambient at most 40°C and a provisional **100×100 mm, two-layer, 1 oz** PCB. Each bridge has approximately 0.791 A nominal hardware current regulation. These are design choices; motor identity, pack maximum voltage/BMS behavior, wiring, starting torque and regenerative energy remain unverified. See [driver margins](driver_margin_review.md) and [power specification](power_circuit_spec.md).

This circuit provides a functional inhibit and independent missing-heartbeat timeout. It is not a certified emergency stop, personnel-protection system, isolator or guaranteed mechanical stopping device.

## What each kind of stop does

- **Physical INHIBIT at SW1:** clears the arm latch, forces command inputs to the coast state, lowers all driver nSLEEP inputs and lowers eFuse SHDN to disconnect the input feed. Motor-rail capacitors and rotating motors can still hold or generate energy.
- **Software stop through RUN low:** clears the arm latch and forces both inputs of every bridge low, selecting coast. The drivers remain awake and the motor rail remains supplied while physical permission is present.
- **PWM low while still armed:** commands electrical braking during the PWM off interval. This is normal speed modulation, not a latched stop. Raising PWM again can immediately drive.
- **Watchdog, rail or reported driver fault:** clears the arm latch. Removing the fault alone cannot restore permission. A new explicit ARM edge is necessary after recovery.

There are four power bridges but **two logical command groups**: U20 front-left and U22 back-left share left commands; U21 front-right and U23 back-right share right commands. Outputs are never paralleled. This interface cannot independently control all four wheel speeds.

## Pi and harness contract

The legacy BCM assignments are code evidence only; reuse for this reference is **ASSUMED**, not verification of the robot's wires. ARM/HB are proposed assignments. Pi header numbering follows [official Raspberry Pi documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html). J6 is the board's separate **16-pin connector**, not a direct 40-pin Pi hat.

| J6 pin | Net / proposed Pi connection | Meaning |
|---:|---|---|
| 1 | PI_3V3; Pi 3.3 V physical 1 or 17 | Logic supply only; not 5 V or motor supply |
| 2, 4, 8, 14, 15, 16 | GND | Common logic reference; no motor return current through harness |
| 3 | GPIO18; Pi physical 12 | Left PWM, low initially; maximum reference PWM 20 kHz |
| 5 | GPIO23; Pi physical 16 | Left direction; high maps to OUT1→OUT2 |
| 6 | NC / reserved | Former GPIO24 position; no connection in this design |
| 7 | GPIO13; Pi physical 33 | Right PWM, low initially |
| 9 | GPIO5; Pi physical 29 | Right direction; high maps to OUT1→OUT2 |
| 10 | NC / reserved | Former GPIO6 position; no connection in this design |
| 11 | GPIO25; Pi physical 22 | RUN; low clears arm, high only requests permission |
| 12 | GPIO17; Pi physical 11 | ARM; new positive edge only, normally low |
| 13 | GPIO27; Pi physical 13 | Heartbeat; falling edges no more than 50 ms apart |

Actual wheel-forward polarity remains to be established from wiring. J6 MPN is **Würth 61201621621**, footprint `AI_Robot:IDC_Wurth_61201621621`. Its shroud/key and pin-1 marking do not make an arbitrary ribbon cable safe; use the explicit cavity map in [pin map](pin_map.md) and [wiring guide](wiring_guide.md). Do not infer connector numbering from a top/bottom mirror image. Connect or disconnect only with physical inhibit selected and motor power removed.

Require GPIO levels **≥2.8 V high and ≤0.4 V low at J6**, with short common-ground wiring. The 330 Ω/10 kΩ input networks draw approximately 0.3 mA per high input. These are interface requirements, not measured Pi capabilities. All motor PWM, RUN and ARM outputs start low; old prototype wiring does not establish the new harness.

## Logic equations and driver states

```text
FEED_ENABLE     = LOGIC_GOOD AND PHYS_OK
RAILS_OK        = LOGIC_GOOD AND PHYS_OK AND FAULT_OK
ALL_OK          = RAILS_OK AND WD_OK AND RUN_REQ
ARM_Q           = 0 asynchronously whenever ALL_OK = 0
ARM_Q           = 1 on a new ARM_PULSE rising edge while ALL_OK = 1
DRIVE_ENABLE_CMD = ARM_Q AND ALL_OK

For each side, with A = DRIVE_ENABLE_CMD:
PRE1 = NOT(PWM AND NOT(DIR))
PRE2 = NOT(PWM AND DIR)
IN1  = A AND PRE1
IN2  = A AND PRE2

All four driver nSLEEP inputs = FEED_ENABLE
All four driver PMODE inputs = PI_3V3
All four driver IMODE inputs = intentionally unconnected
```

| A | PWM | DIR | IN1/IN2 | Result with driver awake |
|---|---|---|---|---|
| 0 | Any | Any | 00 | Coast / high impedance |
| 1 | 0 | Any | 11 | Brake / low-side slow decay |
| 1 | 1 | 0 | 01 | Reverse |
| 1 | 1 | 1 | 10 | Forward |

PMODE high selects the driver's PWM-input truth table. The hardware decoder preserves the Pi's one-PWM/one-direction interface and preserves brake recirculation during armed PWM off-time. [DRV8874 Table 4](https://www.ti.com/lit/ds/symlink/drv8874.pdf) defines the output states. nSLEEP low independently places the driver into its low-power high-impedance state after the sleep transition.

**Wake is independent of ARM.** A normal driver wake can briefly assert nFAULT, as shown in TI Figure 28. Driving nSLEEP from ARM while feeding nFAULT back to arm-clear would cancel normal startup. Here FEED_ENABLE wakes the drivers as the motor rail ramps; the command gate stays closed until rail/fault qualification and a fresh ARM edge. No fault-blinding timer is used.

FAULT_OK_RAW is an open-drain wired-AND node pulled up by R10=10 kΩ: both U11 rail-monitor outputs, U13 eFuse FLT, U13 PGOOD and U20–U23 nFAULT may pull it low. U9 produces FAULT_OK. Fixed-off-time current chopping does not itself assert nFAULT. Internal overcurrent is latched because IMODE is floating; reset requires a deliberate physical-disable/re-enable or motor-power cycle, followed by a new external ARM. Thermal/undervoltage recovery does not re-arm either.

## Exact logic IC and footprint connections

All listed ICs use PI_3V3/GND with local 100 nF decoupling. These are final reference connections; unused pins have explicit no-connect markers in CAD.

| Ref / MPN | Pin contract | Footprint |
|---|---|---|
| U3 SN74LVC08APWR | 1 LEFT_PRE1,2 permission→3 LEFT_IN1;4 LEFT_PRE2,5 permission→6 LEFT_IN2;9 RIGHT_PRE1,10 permission→8 RIGHT_IN1;12 RIGHT_PRE2,13 permission→11 RIGHT_IN2;7 GND,14 VCC | `Package_SO:TSSOP-14_4.4x5mm_P0.65mm` |
| U4 TPS3431SDRBR | 1 VDD;2 WD_SELECT;3 LOGIC_GOOD;4 GND;5 SET1=VDD;6 HB;7 WDO and8 ENOUT tied WD_RAW;9 EP=GND | `AI_Robot:TPS3431_DRB8_3x3_P0.65` |
| U5 SN74LVC1G74DCUR | 1 CLK=ARM_PULSE;2 D=VDD;3 /Q NC;4 GND;5 Q=ARM_Q;6 /CLR=ALL_OK;7 /PRE=VDD;8 VCC | `AI_Robot:TI_DCU0008A` |
| U6 SN74LVC11APWR | 1 LOGIC_GOOD,2 PHYS_OK,13 FAULT_OK→12 RAILS_OK;3 RAILS_OK,4 WD_OK,5 RUN_REQ→6 ALL_OK;9 ARM_Q,10 ALL_OK,11 VDD→8 DRIVE_ENABLE_CMD;7 GND,14 VCC | TSSOP-14 above |
| U7 TPS3839G33DBZR | 1 GND;2 RESET=LOGIC_GOOD;3 VDD | `Package_TO_SOT_SMD:SOT-23` |
| U8 SN74LVC2G17DBVR | 1 PHYS_RAW→6 PHYS_OK;3 WD_RAW→4 WD_OK;2 GND,5 VCC | `Package_TO_SOT_SMD:SOT-23-6` |
| U9 SN74LVC2G17DBVR | 1 FAULT_OK_RAW→6 FAULT_OK;3 HB_RAW→4 HB;2 GND,5 VCC | SOT-23-6 above |
| U12 SN74LVC2G17DBVR | 1 RUN_RAW→6 RUN_REQ;3 ARM_RAW→4 ARM_PULSE;2 GND,5 VCC | SOT-23-6 above |
| U14 SN74LVC1G08DBVR | 1 LOGIC_GOOD,2 PHYS_OK→4 FEED_ENABLE;3 GND,5 VCC | `Package_TO_SOT_SMD:SOT-23-5` |
| U15 SN74LVC2G14DBVR | 1 AIN1_RAW→6 LEFT_PH_N;3 BIN1_RAW→4 RIGHT_PH_N;2 GND,5 VCC | SOT-23-6 above |
| U16 SN74LVC132APWR | 1 PWM_A_RAW,2 LEFT_PH_N→3 LEFT_PRE1;4 PWM_A_RAW,5 AIN1_RAW→6 LEFT_PRE2;9 PWM_B_RAW,10 RIGHT_PH_N→8 RIGHT_PRE1;12 PWM_B_RAW,13 BIN1_RAW→11 RIGHT_PRE2;7 GND,14 VCC | TSSOP-14 above |

U10, C108 and R135 from earlier candidates are removed. There is no shared STBY net or open-drain command buffer in this redesign. The U3 final AND outputs actively drive both driver inputs low on disarm.

Primary pin references: [LVC08A](https://www.ti.com/lit/gpn/sn74lvc08a), [LVC132A](https://www.ti.com/lit/ds/symlink/sn74lvc132a.pdf), [LVC2G14](https://www.ti.com/lit/ds/symlink/sn74lvc2g14.pdf), [LVC2G17](https://www.ti.com/lit/ds/symlink/sn74lvc2g17.pdf), [LVC1G74](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf), [LVC11A](https://www.ti.com/lit/gpn/sn74lvc11a) and [LVC1G08](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf).

## Passives and physical switch

Interface RC0603 resistors are 1%, 0.1 W in `Resistor_SMD:R_0603_1608Metric`.

| References | Value / MPN | Connections |
|---|---|---|
| R100,104,112,116 | 330 Ω / RC0603FR-07330RL | GPIO18,23,13,5 to PWM_A_RAW,AIN1_RAW,PWM_B_RAW,BIN1_RAW |
| R101,105,113,117 | 10 kΩ / RC0603FR-0710KL | Corresponding raw commands to GND |
| R124,126,128 | 330 Ω / RC0603FR-07330RL | GPIO25,17,27 to RUN_RAW,ARM_RAW,HB_RAW |
| R125,127,129 | 10 kΩ / RC0603FR-0710KL | Those three raw control signals to GND |
| R130,131 | 10 kΩ / RC0603FR-0710KL | VDD→WD_SELECT; VDD→WD_RAW |
| R132,138 | 100 kΩ / RC0603FR-07100KL | HB→GND; LOGIC_GOOD→GND |
| R133 | 1 kΩ / RC0603FR-071KL | VDD→PHYS_SUPPLY |
| R134,139,140,141 | 10 kΩ / RC0603FR-0710KL | PHYS_RAW,ARM_Q,ALL_OK,DRIVE_ENABLE_CMD to GND |
| C100 | 1 nF 5% C0G / GRM1885C1H102JA01D | PHYS_RAW→GND; 0603 |
| C101–107,C109 | 100 nF 50 V X7R / CC0603KRX7R9BB104 | Local logic bypass; 0603 |
| C12–14 | 100 nF 50 V X7R / C0805C104K5RACTU | U14–16 local bypass; 0805 |

Driver-local nSLEEP pull-downs are R23/R27/R31/R35=10 kΩ TNPW080510K0BEEA, one at each driver. They remain connected when the command latch is cleared. The complete driver/power passive list belongs to the BOM and power specification.

SW1 **C&K JS102011SAQN**, `Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN`, is nonshorting SPDT: pin2 common=PHYS_RAW, pin1=PHYS_SUPPLY, pin3=GND. Its mounting pads are electrically unconnected. The [manufacturer drawing](https://www.ckswitches.com/media/1422/js.pdf) controls actuator orientation; label the actual positions INHIBIT and ENABLE.

SW1 grounds a logic node, never an actively driven Pi output. ENABLE gives about 0.909×PI_3V3 through the 1 kΩ/10 kΩ divider. An open contact decays low through R134. C100's nominal enable/open decay constants are approximately 0.91/10 µs with about ±6% initial RC tolerance. This filters brief noise, but is not a certified debounce or switch-failure detector. Silver-contact reliability at approximately 0.3 mA and the mechanical actuator position still require physical qualification. Releasing physical inhibit permits a supply ramp; it cannot set ARM_Q.

## Watchdog and future firmware sequence

The [TPS3431](https://www.ti.com/lit/ds/symlink/tps3431.pdf) factory 200 ms option uses SET1 high and CWD pulled to VDD through R130=10 kΩ±1%, within its 9–11 kΩ selection band. No timing capacitor is used. Timeout and reset-low interval are each **170–230 ms**. Falling WDI edges service it. Tying ENOUT to WDO ensures watchdog disable also makes WD_RAW low.

The board cannot prove that a valid heartbeat preceded first ARM during the watchdog's initial grace interval. It also cannot detect a broken motion process that continues producing valid heartbeat. A later implementation must therefore follow this contract:

1. Initialize PWM, RUN and ARM low. Keep motion permission blocked while physical enable starts the motor-rail ramp and driver wake.
2. Generate heartbeat from the motion arbiter's health decision, with high/low intervals at least 1 ms and accepted falling edges no more than 50 ms apart. An unrelated free-running heartbeat is insufficient.
3. Wait for the motor rail and driver startup to settle, then allow at least 1 s and three valid heartbeat cycles before accepting explicit operator ARM. The present harness does not report ALL_OK to the Pi; absence of status must not be presented as measured fault clearance.
4. With PWM low, set RUN high. After qualification is stable for at least 1 ms, pulse ARM high for at least 1 ms and return low. A rejected arm stays rejected; do not retry automatically on reconnect or fault recovery.
5. A stop sets RUN, PWM and ARM low. Hold PWM low before changing direction and allow logic settling plus a validated motor deceleration/reversal interval before driving again. No hardware reversal timer is fitted.

Watchdog assertion occurs within 230 ms of its last accepted falling edge, plus subsequent logic/driver propagation. This is not a measured stopping-time bound. WD_RAW may later recover while heartbeat is still missing, but ARM_Q remains cleared. A held-high ARM cannot re-arm when ALL_OK returns.

## Power qualification and recovery

U7 [TPS3839G33](https://www.ti.com/lit/ds/symlink/tps3839.pdf) has a 3.003–3.126 V falling threshold and 120–350 ms release delay. Its 20 µs falling propagation is typical, not a guaranteed worst case. The 3.2–3.4 V normal rail is a required design range. LOGIC_GOOD drives CMOS loads and R138, without the old NPN base load; its specified high-level margin supports the watchdog EN and logic inputs.

U11 [TPS3700](https://www.ti.com/lit/ds/symlink/tps3700.pdf) has pin1 OUTA and pin6 OUTB tied to FAULT_OK_RAW; pin2 GND, pin5 PI_3V3; pin3 UV sense via 200 kΩ/10 kΩ and pin4 OV sense via 442 kΩ/10 kΩ. Nominal rising thresholds are 8.40 V UV and 18.08 V OV. Tolerance/hysteresis bounds are in the power review.

U13 [TPS26630](https://www.ti.com/lit/ds/symlink/tps2663.pdf) FLT pin14 and PGOOD pin16 also join the fault node. PGTH pin15 senses **VM output** through R45/R46=60.4 kΩ/10 kΩ, nominal rising 8.448 V; PGOOD additionally requires its internal FET to be enhanced. C40=2.2 µF controls the selected slow startup. Input-side sensing must not replace this output divider because PGTH also selects fault-recovery slew behavior.

FEED_ENABLE drives SHDN through R11=1 kΩ with R12=10 kΩ to GND. The pull-down meets the eFuse's 10 µA sinking requirement and keeps shutdown below 0.8 V when Pi logic is absent. FEED_ENABLE intentionally does not depend on FAULT_OK or PGOOD: otherwise the supply could never start. Q1 CSD19537Q3 and Q2 BSS138 provide the reviewed reverse-polarity/reverse-current path; Q2 source is FUSED_IN, not ground.

| Event | Motion result | Recovery |
|---|---|---|
| Startup or RUN low | Latch cleared, coast | Explicit initialization and ARM |
| Physical INHIBIT/contact opens | Coast, sleep, feed off | Re-enable, settle, fresh ARM |
| Missing/stuck heartbeat | Latch cleared, coast; feed may stay on | Restore health and fresh ARM |
| VM/eFuse/driver reported fault | Latch cleared, coast | Fix cause; OCP may require physical reset; fresh ARM |
| ARM remains high through fault | Latch stays cleared | Return ARM low, then deliberate new edge |
| Pi rail undervoltage/loss | Supervisor removes feed/sleep permission; pull-downs define off state | Reinitialize after restored power |
| PWM=0 while armed | Brake, not latched stop | PWM high can drive immediately |

DRV8874 uses VM as its supply and accepts separate low-voltage control; the old TB6612 separate-VCC partial-power limitation does not carry over unchanged. Nevertheless, abrupt rail-collapse waveforms, broken ground, externally driven wires, shorts and component failures remain untested. Do not attribute powered-off isolation to all logic ICs or promise redundant fault tolerance.

At physical enable, drivers remain awake even when disarmed; allow up to 4×7 mA VM quiescent current. PI_3V3 powers interface logic and VREF dividers, not motor current. Keep a conservative 50 mA interface allocation pending complete measured loading; no claim is made about Pi spare capacity.

The 680 Ω bleed and nominal 2.88 mF bulk/local capacitance give RC≈1.96 s; +5% resistance/+20% capacitance gives ≈2.47 s. From 15 V to 0.3 V that corner takes approximately 9.65 s with feed removed and no regeneration. **Measure VM before handling; elapsed time alone is insufficient.** Reverse-current blocking prevents intentional return to the source but does not absorb energy. The power review's bounded regeneration case remains essential; coast does not guarantee zero speed or zero returned energy.

## Footprints and evidence limits

U5's project `TI_DCU0008A` footprint matches TI's 0.50 mm pitch DCU land pattern, using 0.85×0.30 mm pads and 0.20 mm copper gap. U4's `TPS3431_DRB8_3x3_P0.65` uses the manufacturer 0.65 mm pitch pad arrangement and grounded exposed-pad extensions. Neither package name may be replaced with a visually similar larger variant. Their generic 3D underside details are approximate. SW1's local nominal model illustrates orientation only; it does not establish mechanical fit or contact position. DRV8874 exposed-pad land, stencil and thermal-via requirements are documented separately in the footprint/assembly review.

Final logic review checked the actual manifest's pin maps and all 32 combinations of permission and paired PWM/direction states, yielding 128 checked driver input pairs. It also checked independent wake, output-sensed power-good, fault-latch recovery and current-limit connections. These are Boolean/source checks, not SPICE, native ERC/DRC, physical waveforms, thermal qualification or motor-stop testing. Native CAD checks have their own reports. No GPIO backend was enabled and no software test result is presented as hardware validation.

Before release, resolve actual motor/pack identity, harness orientation and levels, current-limit peaks, simultaneous starting torque, regeneration, thermal coupling, brownout/stop behavior and a firmware implementation that honors the interface. Fabrication, assembly and physical validation remain deferred.
