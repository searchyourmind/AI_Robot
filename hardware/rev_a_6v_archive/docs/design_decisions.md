# Design decisions and interview explanation

**6 V REFERENCE ONLY — DIRECT 12 V INPUT INCOMPATIBLE.** The 2026-09-28 purchase-record update establishes listed 12 V motors and packs. This document retains the existing 5.5–6.5 V design; its calculations, parts and checks have not been qualified for that system. See the [12 V impact review](12v_design_impact.md) and [current hardware evidence](actual_hardware_evidence.md).

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
This explains the actual reference design and its tradeoffs. It does not retroactively turn assumed ratings into actual robot specifications. See [wiring_guide.md](wiring_guide.md), [actual_hardware_evidence.md](actual_hardware_evidence.md), and the critical [component-count review](component_count_review.md).

## 1. Why two TB6612FNG devices?

Each device provides two full H-bridge channels. Four motors with one bridge per motor therefore use two devices, matching the existing two-module/four-motor architecture. The part is a conditional continuity choice, not a proven best driver for the actual motors. The purchased motors are listed as 12 V; exact loaded RMS current, startup/stall profiles, full-charge/transient VM and simultaneous two-channel package heating must still support the choice. Two TB6612 boards being included in the kits does not qualify this different custom circuit. The datasheet's absolute peak headline is not a continuous design rating. The 0.25 A RMS and 0.60 A/20 ms reference limits were accepted assumptions, not observed motor demand.

## 2. Why four separate H-bridge outputs?

Each motor gets its own OUT1/OUT2 pair, keeping its switching/current path separate from the other motors. Sharing commands does not justify tying H-bridge outputs together: switches have timing and voltage differences, so separate bridges must not be hard-paralleled in this design. Four channels mean eight motor terminals. VM and GND remain common; there is no galvanic isolation, and a power-supply fault can affect all channels. A channel does not have independent measured current regulation on this board.

## 3. Why left/right paired commands?

The existing differential-drive API commands a left side and a right side. Rev A fans out PWMA/AIN1/AIN2 to both A channels (left wheels), and PWMB/BIN1/BIN2 to both B channels (right wheels), reducing the command-pin requirement. This is a hardware connection in the delivered board. The benefits are simpler control and correspondence with the current API; the cost is no independent front/rear command within a side. Equal PWM does not ensure equal wheel speed, especially without encoder feedback. Four-wheel independent control requires new signal allocation, not just different HTTP commands.

## 4. Why independent Pi power?

This preserves the confirmed existing supply arrangement and avoids placing motor startup demand on a new shared Pi regulator. It reduces one path for motor-supply droop to reset the Pi. The board still uses a common ground reference and receives its 3.3 V logic from the Pi; supply separation is not noise isolation or an unconditional power-loss guarantee. Capacitor charging on the Pi rail, harness ground impedance and loss of Pi logic while VM retains energy remain review items.

## 5. Why two copper layers?

Two layers were accepted as a reference fabrication choice for this low-current motor/control board, with no new high-speed camera or USB routing. The completed layout routes within the stated dimensions and has ground fill on both sides. This avoids adding a four-layer stackup requirement before the mechanical and vendor requirements are known. Passing routing/DRC demonstrates geometric feasibility only. A four-layer revision could improve a dedicated ground reference, current-return continuity and routing density; EMI, signal-return and thermal validation could still motivate it. No cost quote or production optimization was performed.

## 6. Why 100 × 80 mm?

It was a user-accepted provisional envelope, chosen to provide room for six connectors, two drivers, through-hole bulk capacitors, discrete supervision, test points and four mounting holes. It is not derived from measured chassis dimensions and is not a minimum-area result. Both exact mounting compatibility and height clearance remain unknown. A smaller outline or a board shaped for the real robot could be appropriate after requirements and component simplification are decided. Do not say “100 × 80 mm was required for current capacity.”

## 7. Why these current-trace widths?

The board carries more current in the common supply than in each motor channel. Nominal widths are 1.00 mm input/main VM trunks, 0.60 mm motor outputs, 0.40 mm individual two-channel VM branches, and 0.20–0.25 mm signals, with explicitly reviewed short fanouts. Using nominal 35 µm copper, `R=rho*L/(w*t)` and `P=I_RMS^2*R` provides a voltage-drop/loss screen. A 50 mm, 0.60 mm motor trace is about 47.5 mΩ at an assumed 60 C conductor temperature: about 2.97 mW at 0.25 A RMS and 28.5 mV at 0.60 A peak. A 27.09 mm, 0.40 mm branch is about 38.6 mΩ: 9.65 mW at 0.50 A RMS and 46.3 mV at a 1.20 A peak.

These are calculations for the accepted current envelope, not an ampacity or temperature certification. Add both motor conductors, return copper, vias, connector contacts and protection-device drops. Final copper thickness, fault duration and actual motor demand may require wider copper or a different architecture. A net-class preferred width is not automatically a DRC-enforced minimum for that net. The [routing rationale](routing_rationale.md) and native width inventory document actual geometry rather than inferring correctness from “DRC 0.”

## 8. How is ground return handled?

Pi reference, driver logic grounds, power grounds and battery negative share a common GND net. Placement aims to keep driver/capacitor/motor switching loops near the motor-power region and their return to the source, with filled GND areas on both copper layers. The intent is to avoid routing motor current through a thin logic return or the Pi cable. Ground is not an ideal zero-impedance node: high-frequency return depends on local loop inductance, while lower-frequency division also depends on resistance. Plane slots, necks and shared segments matter. Two filled zones do not prove a continuous low-impedance return everywhere or zero Pi-cable noise; no field solver or EMC test was performed. Arbitrary split analog/digital grounds are not used as a cure.

## 9. Why these capacitor locations and values?

The 100 nF ceramics near each supply pin provide a short high-frequency current loop. Local electrolytics next to each driver support lower-frequency supply changes; distant bulk cannot replace close ceramics because trace/lead inductance matters. The two 1000 µF VM capacitors and the TVS are grouped near the motor-power region to buffer a specifically bounded returned-energy event. With 1.6 mF minimum effective initial bulk and a 3 mJ event starting at 6.5 V, the ideal energy calculation reaches about 6.782 V before the separate overshoot allowance.

Capacitance is not free: it adds inrush, stored energy, size and cost. The 47 µF local values and 2×1000 µF bulk are selected reference candidates, not proven minimums or measured optimums. Motor inductance and braking energy are unknown. Local/bulk ripple sharing still needs analysis before fabrication release. The VCC bulk also adds about 115 µF to the Pi logic rail. These are explicit simplification/requalification candidates in the component review.

## 10. Why default-disabled?

Pi booting, software initialization, missing commands and restoration after a fault should not automatically produce motor drive. The design uses pulldowns, rail qualification, a hardware watchdog and an arm latch so valid conditions alone do not set enable: a fresh ARM edge is needed. This makes restart behavior deliberate at the interface level. It does not make the circuit fail-safe against every component, ground or power failure, and it does not prove that a human approved an ARM edge. Abrupt Pi logic loss while VM remains charged is unresolved. The new handshake is not implemented in the current mock-only backend.

## 11. Physical disable versus software stop

Software stop requests a state through a software/backend execution path. SW1 acts on the permission circuit without HTTP/Python execution: it clears the latch and lowers STBY while the relevant hardware has valid power. These paths have different dependencies. SW1 does not disconnect VM or remove capacitor energy, and STBY low is high-impedance standby, not active braking or an instant physical stop. The board does not contain a safety-rated power-disconnecting E-stop. An external E-stop's actual existence/type is still unknown.

For the chosen watchdog configuration, 170–230 ms is a device timeout range, not a measured full robot stopping time. Normal-looking heartbeats from faulty software can avoid the watchdog. It is useful fault coverage, not proof of application correctness.

## What 97 components means

The fitted BOM contains 52 resistors, 21 capacitors, 12 ICs, six board connectors, two diodes, two transistors, one fuse and one switch. It excludes ten copper test pads, four mounting holes and off-board mating plugs. The count is not 97 ICs or 97 unique purchased part types: there are 33 distinct MPNs. Detailed block totals and references are in [component_count_review.md](component_count_review.md).

The signal-conditioning and permission/supervision circuits account for 62 of 97 placements. They implement behavior beyond consolidating jumper wires. The accurate conclusion is that this is a feature-rich discrete reference board, not an established minimum-component implementation. Some choices can plausibly be simplified or consolidated; deleting them without changing the fault-behavior claims would be misleading. No native circuit or BOM was changed during this explanatory review.

## How to explain ERC/DRC without overstating them

ERC checks electrical-rule relationships represented in the schematic, such as conflicting pin types or unconnected power inputs. DRC checks the configured board geometry/connectivity rules and, here, schematic parity. The actual delivered reports have zero violations, zero unconnected items and zero parity items. No DRC class was ignored; the ERC SPICE-model check was outside scope.

Neither checker proves the motor's stall current, suitability of a battery/BMS, thermal resistance, capacitor ripple, powered-off IC behavior, harness polarity or actual stopping distance. A perfectly consistent schematic and PCB can implement the wrong circuit. Datasheet/pin checks, load/energy calculations, failure-mode review and later authorized physical measurements are separate evidence. The 132 mock tests similarly establish only software behavior under their mocks.

## A short, honest interview narrative

> This AI-assisted reference design consolidates a Pi robot's four motor connections into two dual H-bridge ICs. Each motor has its own power-output pair, while the front/rear motors on each side share commands. The Pi remains separately powered with a common logic reference. The design separates software motion requests from a discrete hardware inhibit, watchdog and re-arm latch. Native schematic/layout checks and BOM reconciliation passed. Later purchase records identified 12 V motors and packs, exposing a direct-input mismatch with my 6 V reference protection and monitor. I documented the mismatch and retained the original CAD/check evidence without claiming a completed 12 V redesign. The exact motor current, pack topology/full-charge voltage and harness still need confirmation. This proposed PCB has not been fabricated, assembled or physically tested.

Only use first-person claims for engineering work you personally understand and can explain. The project explicitly records AI assistance; CAD generation by itself does not establish practical hardware experience.

## Primary sources and project evidence

- [Toshiba TB6612FNG datasheet](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660), served 2026-05-13: two channels, pinout, operating/absolute limits, powered truth table and local decoupling example. Rechecked 2026-09-28.
- [Raspberry Pi GPIO documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header): 3.3 V GPIO and physical-header context. Rechecked 2026-09-28; does not establish actual wires.
- [TI TPS3431](https://www.ti.com/lit/ds/symlink/tps3431.pdf) and [SN74LVC1G74](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf): watchdog and latch behavior.
- [KiCad 10 PCB rule checking](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#design_rule_checking): configured rules and preferred-versus-enforced track widths. Rechecked 2026-09-28.
- [Actual final check report](../validation/design/design_check_report.md), [reference electrical limits](reference_electrical_spec.md), [power topology](power_circuit_spec.md), [enable logic](enable_interface_spec.md), [routing/thermal calculation](routing_rationale.md). Numerical results in this guide are project calculation screens, not manufacturer guarantees or physical measurements.
