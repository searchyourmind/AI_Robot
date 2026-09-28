# Physical mapping and proposed interfaces

**6 V REFERENCE ONLY — DIRECT 12 V INPUT INCOMPATIBLE.** The 2026-09-28 purchase-record update establishes listed 12 V motors and packs. This document retains the existing 5.5–6.5 V design; its calculations, parts and checks have not been qualified for that system. See the [12 V impact review](12v_design_impact.md) and [current hardware evidence](actual_hardware_evidence.md).

## Current Rev A reference connector — 2026-09-28

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
The current native schematic assigns J6, Würth **61201621621**, as a custom
2×8 logic cable. The following is a **proposed new harness**, not a report of
existing wires. Number J6 from its top/mating face, with the footprint's pin-1
marker: odd pins down the left row, even pins down the right at zero rotation.
See [the connector drawing review](footprint_review.md#j6--exact-16-pin-shrouded-header-selection).
The proposed Pi assignments use the official [40-pin GPIO reference](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header).
BCM/GPIO numbers and physical header positions are separate numbering systems.

| J6 pin | PCB net | Proposed Pi BCM / role | Pi 40-pin physical position | Direction at PCB |
|---:|---|---|---:|---|
| 1 | PI_3V3 | 3.3 V reference supply from Pi | 1 | Power input; no motor power |
| 2 | GND | Signal/power reference | 6 | Common ground |
| 3 | GPIO18 | BCM18, A-channel PWM to both drivers | 12 | Pi → PCB |
| 4 | GND | Signal reference | 9 | Common ground |
| 5 | GPIO23 | BCM23, AIN1 to both drivers | 16 | Pi → PCB |
| 6 | GPIO24 | BCM24, AIN2 to both drivers | 18 | Pi → PCB |
| 7 | GPIO13 | BCM13, B-channel PWM to both drivers | 33 | Pi → PCB |
| 8 | GND | Signal reference | 14 | Common ground |
| 9 | GPIO5 | BCM5, BIN1 to both drivers | 29 | Pi → PCB |
| 10 | GPIO6 | BCM6, BIN2 to both drivers | 31 | Pi → PCB |
| 11 | GPIO25 | BCM25, RUN request through conditioning | 22 | Pi → PCB; no direct STBY drive |
| 12 | GPIO17 | BCM17, deliberate ARM pulse through conditioning | 11 | Pi → PCB |
| 13 | GPIO27 | BCM27, supervised heartbeat | 13 | Pi → PCB |
| 14 | GND | Signal reference | 20 | Common ground |
| 15 | GND | Signal reference; no STBY feedback on this connector | 30 | Common ground |
| 16 | GND | Signal reference | 25 | Common ground |

The six ground wires above are proposed separate returns to six Pi ground
positions; all connect to the same reference. Other Pi ground pins remain
available, but changing cable assignments requires a revised wire table. Pi
physical pin 17 is also a 3.3 V pin; this harness chooses physical pin 1. Never
use Pi 5 V pins 2/4 for J6 pin 1. No power is fed into a Pi rail from this PCB.
STBY is available at TP10 for a later controlled bench measurement. It is not
exposed to any Pi GPIO: that avoids a misconfigured GPIO fighting the hardware
disable sink. J6 pin 15 is ground, and GPIO22 is not assigned by this design.

The proposed ARM/heartbeat/RUN handshake is **not
implemented by the current mock motor backend**. The historical GPIO25 direct
STBY meaning below is superseded for this new PCB: GPIO25 is now a RUN request,
while the independent enable circuit owns STBY. A future physical backend must
configure the input/output directions, meet the watchdog timing contract,
require a fresh deliberate ARM edge after disable, and handle faults according to the hardware contract. The 132 historical mock tests are not evidence of that physical handshake.

The six command signals fan out to corresponding inputs on U1 and U2 for paired
left/right operation; the four motor-output pairs remain separate. Connector
polarity, actual GPIO allocation conflicts, alternate-function configuration and
continuity are NOT TESTED. The source/power sequencing restrictions in
[reference_electrical_spec.md](reference_electrical_spec.md) remain mandatory for
the reference design. Do not connect this draft cable to the existing robot
based solely on the old software pin constants.

## Historical system record and earlier proposal

The sections below preserve the baseline audit. Their unassigned-connector
statements describe that earlier stage; the current native connector allocation
above supersedes them only for the proposed reference PCB.

**USER-CONFIRMED HARDWARE, 2026-09-28:** Board A channel A drives front-left, channel B front-right; Board B channel A drives back-left, channel B back-right. Both boards are controlled directly by Pi 5 GPIO; no Arduino is in the motor-control loop. This is user-supplied mapping, not a continuity test. Exact GPIO wiring and lead polarity remain TBD.

| Motor position | Driver 1/2 | Channel A/B | Control pins / origin | Polarity | Encoder, if present |
|---|---|---|---|---|---|
| Front-left (motor_1) | 1 / existing Board A | A | Direct Pi 5 GPIO; exact wires TBD | TBD | Not integrated; presence TBD |
| Back-left (motor_2) | 2 / existing Board B | A | Direct Pi 5 GPIO; exact wires TBD | TBD | Not integrated; presence TBD |
| Front-right (motor_3) | 1 / existing Board A | B | Direct Pi 5 GPIO; exact wires TBD | TBD | Not integrated; presence TBD |
| Back-right (motor_4) | 2 / existing Board B | B | Direct Pi 5 GPIO; exact wires TBD | TBD | Not integrated; presence TBD |

Assign stable wire labels before measuring: motor M1–M4 and driver U1/U2, channel A/B. Use the user-confirmed positions above and verify labels physically before actuation. One motor per H-bridge channel; never join H-bridge outputs. Two physically separate output pins with the same Toshiba channel-output name are package duplicates that must be connected as the datasheet requires; that is not paralleling two bridges.

## Baseline code mapping (confirmed in code, not four-channel wiring)

| Logical signal | BCM | Pi 40-pin header position (documented mapping) | Purpose |
|---|---:|---:|---|
| PWMA | 18 | 12 | A PWM, code requests 1 kHz |
| AIN1 | 23 | 16 | A direction 1 |
| AIN2 | 24 | 18 | A direction 2 |
| PWMB | 13 | 33 | B PWM, code requests 1 kHz |
| BIN1 | 5 | 29 | B direction 1 |
| BIN2 | 6 | 31 | B direction 2 |
| STBY | 25 | 22 | Shared enable intent |

Both READMEs match these constants. A HIGH/LOW pair in `forward()` is software intent only; motor leads/gearboxes determine actual forward. The remaining IC's connections cannot be inferred. Header names are not permission to wire a new board before checking actual signal fanout, Pi pin functions and supply sequencing.

## Proposed connector/net inventory (no assigned footprint/pins yet)

| Interface | Nets / labels | Decision still needed |
|---|---|---|
| J_PWR | Motor input positive, power return | Current/voltage/keying/rating; input fuse/protection topology |
| J_M1…J_M4 | Separate channel OUT1, OUT2 | Verified wheel labels/polarity; keyed or unambiguous connectors |
| J_CTRL | Logic reference, signal ground, PWM/direction signals, enable request; optional heartbeat | Direct Pi 5 confirmed; actual GPIO fanout, A/B option, logic rail and unpowered isolation TBD |
| Physical disable | Gate-enable inhibit, accessible labeled switch | Fail-low gating, no GPIO short; mechanical power interruption separately reviewed |
| Test points | Raw/protected VM, VCC, GND, each STBY, each PWM; accessible output measurement | Safe probe spacing/current loops, count by layout |

No generic sensor headers are added. A Pi Camera is user-confirmed; retain the existing camera path. Code opens OpenCV device index 0; exact camera model/driver/exposure timing remains unverified. USB microphone and speaker remain existing peripherals, with no new audio circuit proposed. Encoder, battery ADC and current measurement interfaces require a concrete sensor/electrical requirement first.

For IC pad numbers use the verified Toshiba table in `circuit_review.md`; this document must not be used as a released netlist.
