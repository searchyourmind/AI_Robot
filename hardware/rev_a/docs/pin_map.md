# Wheel mapping and proposed 12 V interface

**DRAFT — PROPOSED NEW HARNESS; EXISTING GPIO WIRES UNVERIFIED.**
The current redesign uses four DRV8874PWPR devices. It preserves the user-reported wheel assignment while replacing the old six-command TB6612 interface with two PWM/direction groups. The earlier 6 V pin map is retained in [the frozen archive](../../rev_a_6v_archive/docs/pin_map.md).

## Existing mapping versus new design

| Wheel | Existing user-reported board/channel | New driver | New motor connector | Pin 1 / pin 2 nets | Command group |
|---|---|---|---|---|---|
| Front-left | Board A, A | U20 DRV8874 | J2 | FL_OUT1 / FL_OUT2 | Left |
| Front-right | Board A, B | U21 DRV8874 | J3 | FR_OUT1 / FR_OUT2 | Right |
| Back-left | Board B, A | U22 DRV8874 | J4 | BL_OUT1 / BL_OUT2 | Left |
| Back-right | Board B, B | U23 DRV8874 | J5 | BR_OUT1 / BR_OUT2 | Right |

The first two columns are a user report, not physical continuity evidence. The remaining columns describe new CAD. Each connector carries a separate two-terminal H-bridge output. Motor terminal numbers do not establish actual wheel-forward polarity. Motor outputs are not paralleled and neither output is a permanent ground return.

Four motors and encoder hardware are purchase-confirmed; exact motor identity and current, encoder electrical levels/count convention and installed encoder integration remain unknown. No encoder connection is added to this board.

## Proposed Pi-to-J6 wire table

J6 is Würth 61201621621, a custom 2×8 logic cable, **not** the Pi's 40-pin HAT connector. At zero footprint rotation, the native top/mating view has pin 1 at the top of the left row, pin 2 at the top of the right row, odd/even numbers increasing down the rows. A cable's opposite face can appear mirrored; identify contacts using the keyed drawing and native pin 1 mark. BCM numbers and Pi physical pin numbers are different systems. The [official Pi GPIO reference](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header) supplies the Pi positions.

| J6 pin | New PCB net / function | Proposed Pi BCM or rail | Pi physical pin | Direction at PCB |
|---:|---|---|---:|---|
| 1 | PI_3V3 logic power | 3.3 V | 1 | Power input |
| 2 | GND | Ground | 6 | Common reference |
| 3 | GPIO18, left PWM | BCM18 | 12 | Pi → PCB |
| 4 | GND | Ground | 9 | Common reference |
| 5 | GPIO23, left DIR | BCM23 | 16 | Pi → PCB |
| 6 | Reserved NC | **No connection** | — | Unconnected; not GND |
| 7 | GPIO13, right PWM | BCM13 | 33 | Pi → PCB |
| 8 | GND | Ground | 14 | Common reference |
| 9 | GPIO5, right DIR | BCM5 | 29 | Pi → PCB |
| 10 | Reserved NC | **No connection** | — | Unconnected; not GND |
| 11 | GPIO25, RUN request | BCM25 | 22 | Pi → PCB |
| 12 | GPIO17, deliberate ARM edge | BCM17 | 11 | Pi → PCB |
| 13 | GPIO27, supervised heartbeat | BCM27 | 13 | Pi → PCB |
| 14 | GND | Ground | 20 | Common reference |
| 15 | GND; no enable feedback | Ground | 30 | Common reference |
| 16 | GND | Ground | 25 | Common reference |

BCM24 and BCM6/Pi physical 18 and 31 are not allocated by this redesign. In particular, the former J6.6/J6.10 signals are now NC reserves; they are not new ground positions. GPIO22 is not assigned. There is no direct Pi-to-driver-enable or Pi fault-feedback wire. ALL_OK has no return connection to the Pi, so future firmware cannot claim to observe hardware qualification through this harness; the hardware gates reject an unqualified ARM edge.

Six proposed ground wires share one reference. Pi physical 17 is another 3.3 V pin, but this table chooses physical 1. Pi 5 V pins 2/4 have no connection to this board. The PCB does not supply Pi power or generate its 3.3 V rail. Actual ground and supply routing in the existing two-pack robot still need evidence.

Electrical interface requirements are PI_3V3=3.2–3.4 V, command high≥2.8 V and low≤0.4 V at J6, with the input-edge/harness constraints in [enable_interface_spec.md](enable_interface_spec.md). These are proposed requirements, not measured Pi performance. Native connector continuity and actual GPIO conflicts/alternate functions are not physically validated.

## Decode, permission and sleep

U15 SN74LVC2G14 inverts each DIR. U16 SN74LVC132A generates the NAND terms; U3 SN74LVC08A AND-gates each term with A=DRIVE_ENABLE_CMD:

`IN1 = A AND NOT(PWM AND NOT(DIR))`
`IN2 = A AND NOT(PWM AND DIR)`

LEFT_IN1/2 feed U20/U22. RIGHT_IN1/2 feed U21/U23. PMODE is high for PWM-input mode. IMODE is intentionally open for fixed-off-time current chopping and latched OCP.

| Permission A | PWM | DIR | IN1/IN2 | Awake-driver state |
|---:|---:|---:|---|---|
| 0 | Any | Any | 00 | Coast / high impedance |
| 1 | 0 | Any | 11 | Low-side brake |
| 1 | 1 | 0 | 01 | Electrical reverse |
| 1 | 1 | 1 | 10 | Electrical forward |

These states follow [TI DRV8874 Table 4](https://www.ti.com/lit/ds/symlink/drv8874.pdf); physical wheel direction still depends on motor wiring. PWM-low while armed is a brake request. Disarming forces coast. Direction-change timing/deceleration belongs to a future backend; the combinational decode is not a reversal timer.

FEED_ENABLE=LOGIC_GOOD AND PHYS_OK drives all nSLEEP inputs and the eFuse SHDN network independently of ARM, RUN, fault and PGOOD. This allows rail startup and normal driver wake fault pulses while motion commands remain blocked. A physically enabled, disarmed driver can remain awake. SW1 inhibit lowers FEED_ENABLE and clears permission; VM energy remains in capacitors.

RUN low, watchdog timeout or fault clears the external arm latch and forces inputs 00. Restored qualification alone does not rearm. A fresh ARM edge is required; an internal driver OCP latch additionally requires deliberate physical-enable/power cycling. Hardware recognizes an edge, not human intent. No physical GPIO implementation of this protocol is present in the current mock-only software.

## IC and testpoint references

All U20–U23 use this pin-exact mapping:

| Pin | Function | Pin | Function |
|---:|---|---:|---|
| 1 | IN1 | 9 | PGND |
| 2 | IN2 | 10 | OUT2 |
| 3 | nSLEEP = FEED_ENABLE | 11 | VM |
| 4 | nFAULT = FAULT_OK_RAW | 12 | VCP |
| 5 | Individual VREF | 13 | CPH |
| 6 | Individual IPROPI | 14 | CPL |
| 7 | IMODE: NC/open by design | 15 | GND |
| 8 | OUT1 | 16 | PMODE = PI_3V3 |
| 17 | CAD exposed pad: GND | | |

J1.1 is MOTOR_IN, J1.2 GND. The provisional source envelope is 9–15 V; its applicability to the purchased packs is unresolved.

| Testpoint | Current net |
|---|---|
| TP1 / TP2 / TP3 | VM / PI_3V3 / GND |
| TP4 / TP5 | LOGIC_GOOD / FAULT_OK |
| TP6 / TP7 | WD_RAW / HB |
| TP8 / TP9 / TP10 | ARM_Q / ALL_OK / DRIVE_ENABLE_CMD |
| TP20 / TP21 / TP22 / TP23 | FL_IPROPI / FR_IPROPI / BL_IPROPI / BR_IPROPI |

TP10 no longer denotes TB6612 STBY. Current-indication nodes are separate analog signals, not Pi GPIO inputs or an implemented stall detector.

## Historical code evidence

At baseline 034882c, code defined PWMA 18, AIN1 23, AIN2 24, PWMB 13, BIN1 5, BIN2 6 and STBY 25. That was one logical A/B set, not an observed map of either carrier. The new proposal retains selected BCM numbers but changes GPIO25 to RUN, adds ARM/HB, and leaves old IN2 positions unconnected. It cannot be operated by simply applying the old constants.

The [hardware evidence record](actual_hardware_evidence.md) retains actual-wire fields as unknown. The original 132 offline mock cases remain software-only evidence. New native schematic/PCB checks are separate from this mapping and from physical integration, which remains **NOT TESTED**.
