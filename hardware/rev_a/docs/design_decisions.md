# Motor-interface design decisions

**2026-09-28 — Current 12 V-class reference redesign. DRAFT, NOT RELEASED.**

This document explains the four-DRV8874 motor interface developed for the Raspberry Pi robot. It covers driver selection, paired commands, power protection, layout, and hardware enable behavior. The earlier two-TB6612, 5.5–6.5 V design is retained in `hardware/rev_a_6v_archive`; the current design has its own routing and check results. The custom board has not yet been fabricated or tested on the robot.

The project hardware includes four motors, two WHEELTEC R3 chassis, two TB6612 carrier boards and two packs sold as 12 V. The exact motor identity, pack chemistry/full-charge voltage, installed harness and regulator circuit on the purchased carriers remain unconfirmed. The new design adopts a **provisional 9–15 V input envelope**, independently powered Pi, **3.2–3.4 V logic rail**, and ambient at most **40°C**. These are design conditions to verify against the actual robot. They are not measurements of the purchased hardware. See [actual hardware evidence](actual_hardware_evidence.md) and [source review](wheeltec_source_review.md).

## Why change from two TB6612 devices to four DRV8874 devices?

The historical choice followed the prototype: one TB6612 contains two bridges, so two packages could serve four motors. That continuity did not establish sufficient electrical margin for a new custom board. Toshiba lists a 13.5 V recommended VM maximum and 15 V absolute maximum. A 15 V normal input envelope has no suitable operating margin, and the new bounded VM transient case reaches beyond that part's limits. Its 3.2 A entry is a single 10 ms absolute pulse condition, not permission to sustain a candidate motor's 3.2 A stall. The bare chip also lacks the selected design's adjustable per-motor current regulation. [Toshiba datasheet](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660).

The new board selects **four DRV8874PWPR**, one per motor. The broader supply range, hardware current regulation, current indication and fault output allow a better bounded protection architecture. Four single-bridge packages spread heat and keep each current limit local. DRV8876 is a plausible lower-current alternative, but its greater typical bridge resistance increases conduction loss; DRV8874 was selected for margin. The advertised 6 A peak is **not this board's continuous rating**. [TI DRV8874](https://www.ti.com/lit/ds/symlink/drv8874.pdf), [TI DRV8876](https://www.ti.com/product/DRV8876).

The selected static per-channel threshold is approximately **0.791 A nominal**, with a **0.708–0.888 A** calculation range including the stated supply, resistor and sensing tolerances. This is a deliberate constrained-current design, not an attempt to deliver unrestricted 3.2 A stall. The conditional MG513P30_12V figures of 0.36 A rated and 3.2 A stall are comparison inputs only; the actual motor has not been identified. Current-limited starting torque, normal loaded current and winding temperature need physical evaluation. A driver surviving its bounded current does not prove that a stalled motor can remain energized indefinitely. The equations, thermal allowances and alternative comparison are in [driver margin review](driver_margin_review.md).

## Four separate outputs versus four independent commands

The board has four separate H-bridges and eight motor terminals. Front-left and back-left share one PWM/direction command; front-right and back-right share another. **The pairing is wired in hardware**, so the delivered interface supplies two independently commanded sides, not four independently commanded wheels.

Sharing control signals does not mean sharing power outputs. Each motor retains its own bridge, current-limit network, output connector and IPROPI test node. Do not connect output pairs from different bridges together. Their VM and GND are common, and their fault reports join a common inhibit, so this is neither galvanic isolation nor independent fault-containment for every failure.

This grouping preserves differential-drive behavior and requires four motion GPIO signals. The tradeoff is that unequal motor loads, gearing or friction can produce unequal wheel speeds even at equal duty cycle. Encoders are not integrated into this board or the active control loop. Front/rear independent speed control would need another signal allocation and a hardware revision; extra HTTP commands alone cannot change the wired pairing. [Pin map](pin_map.md).

## Why keep the Pi separately powered?

It preserves the confirmed supply arrangement and avoids feeding Pi startup/CPU/camera loads from a newly designed motor regulator. Motor inrush and braking energy are handled in the motor path; the Pi provides the board's 3.3 V logic rail. The Pi, interface and motor source still need a common ground reference.

Independent supplies reduce one path for motor-rail disturbance to reset the Pi, but they do not remove conducted noise, ground impedance or sequencing requirements. This board does not add USB, camera or audio power distribution. Motor current should return through the motor-power path rather than a thin Pi ground lead. GPIO and logic specifications remain requirements at the connector, with a short common-ground harness and no hot-plug assumption. [Wiring guide](wiring_guide.md), [Raspberry Pi hardware documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header).

## Why an eFuse, reverse-current control and substantial capacitance?

The input protection handles different events from the per-driver current limits. The **TPS26630** circuit supervises the common source, limits input current, controls charging and latches off after the selected overload conditions. Its external FET arrangement blocks reverse current after the specified response. Its approximately 2.98 A nominal aggregate limit is not a verified battery/BMS rating or an instantaneous current ceiling. The normal source limit is provisionally 2 A continuous. [TI TPS2663](https://www.ti.com/lit/ds/symlink/tps2663.pdf), [power circuit specification](power_circuit_spec.md).

Four upper-bound phase currents can total more than the lower aggregate eFuse threshold. Battery current and motor phase current also differ during PWM recirculation. Therefore four simultaneous starts may produce a protective trip; that is a case to measure, not a reason to assume the limit can be increased. Local capacitors and controlled inrush affect the transient.

Two 1000 µF bulk capacitors plus four 220 µF local capacitors provide **2.88 mF nominal / 2.304 mF minimum** under the stated tolerance model. A bounded 0.1 J returned-energy event starting at 15 V raises that minimum capacitance to approximately **17.66 V** in the ideal energy calculation. The separate transient/clamp ceiling is 32 V; capacitor voltage rating is 50 V. These numbers are coordinated design limits, not measured regenerative energy. The event repetition limit, capacitor ripple, TVS behavior and supply wiring still matter. Reverse blocking keeps energy on VM; it does not absorb it. [Reference electrical specification](reference_electrical_spec.md), [power circuit specification](power_circuit_spec.md).

Close ceramics support fast switching loops, local bulk supports slower changes, and the charge-pump capacitors serve a distinct driver function. Distant bulk cannot replace a short local bypass connection. Added capacitance has costs: inrush, area, stored energy and discharge time. The 680 Ω bleed is a discharge aid, not instantaneous removal of power.

## Why two layers and a provisional 100 × 100 mm outline?

The reference uses **two copper layers, nominal 1 oz copper and a 100 × 100 mm outline**. The larger envelope replaces the historical 100 × 80 mm board to accommodate four driver packages, their thermal spreading areas and additional local bulk. It is a provisional engineering envelope, not a measured fit to either chassis or an optimized minimum area. Mounting-hole locations, connector access, enclosure clearance and component height remain mechanical requirements to confirm.

Two layers keep the reference stackup simple and avoid inventing a production stackup before the fabricator and mechanics are known. There are no camera or USB high-speed traces on this board. The cost is limited room for uninterrupted ground return and heat spreading. A four-layer revision could help return continuity, thermal spreading and density; the present choice must still satisfy actual copper, temperature and EMC requirements. No supplier cost comparison or thermal qualification has been performed.

The driver screen allocates approximately **0.90 W per driver**, with an effective junction-to-ambient target no worse than **80°C/W**, including nearby heat sources. An initial layout objective is at least 4 cm² of spreading copper per driver with grounded exposed-pad connections and thermal vias. The [saved ground-area inventory](../validation/design/routing_geometry.md) reviews the final copper geometry. The local copper windows share and overlap ground regions, so the area screen does not establish thermal independence or satisfy the unresolved physical thermal qualification. A package's JEDEC thermal number cannot simply be assigned to this different two-layer board. [Driver margin review](driver_margin_review.md), [TI motor-driver layout guidance](https://www.ti.com/lit/pdf/slva959).

## How should trace widths and ground return be justified?

Common input/VM paths carry the aggregate load; motor output paths carry individual winding current, including recirculation. Logic nets carry far less current. Width choices should use the final copper thickness, path length, RMS current, allowed drop, temperature rise, via geometry, connector resistance and fault duration. Short package fanouts must be reviewed separately from wider trunks.

The [final routing audit](../validation/design/routing_geometry.md) records actual widths, lengths, narrow segments and vias. No width or current-capacity claim is inherited from the 6 V board. Preferred net-class widths are routing settings; they are not automatically enforced per-net minimums. DRC can check configured geometric limits, but it does not establish temperature rise or ampacity. [KiCad PCB rule checking](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#design_rule_checking).

The common GND connection aims to keep fast motor/bypass loops local and provide a continuous return to the power source. The Pi cable is a reference connection, not an intended motor-current return. Filled copper on two layers does not automatically prove low impedance: slots, narrow necks, thermal spokes and shared paths matter. The design does not claim field-solver analysis, EMC performance or a universal cure through split grounds.

## Why default-disable, a hardware watchdog and an arm latch?

A booting Pi, missing process, stale command or recovered fault should not restore drive automatically. Three functions address different dependencies:

- **Qualification:** supply-good, physical enable, driver/eFuse fault status, RUN and watchdog status must permit motion.
- **Independent timeout:** TPS3431 watches heartbeat transitions without depending on the Python ticker.
- **Restart latch:** a positive ARM edge sets permission only while qualification is valid; losing qualification clears it asynchronously.

Valid rails or restored heartbeat alone do not clock the latch. A held-high ARM signal also does not create a fresh edge after a fault. This is deliberate restart behavior, not proof that a person approved each edge, and not a safety-certified redundant system. A component short, ground fault or arbitrary wiring fault can lie outside the intended coverage. [Enable interface specification](enable_interface_spec.md), [TPS3431](https://www.ti.com/lit/ds/symlink/tps3431.pdf), [SN74LVC1G74](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf).

The selected watchdog configuration has a **170–230 ms device timeout range**. The proposed interface sends falling heartbeat edges at intervals no greater than 50 ms. That timeout is not measured stopping distance, total response latency or a motor stall timer. Faulty software that continues to produce acceptable heartbeats can evade this check. Hardware heartbeat handling for this board has not been implemented in the mock-only backend.

## Why separate waking the drivers from permitting motion?

A driver needs power and time to initialize before its fault output can qualify motion. DRV8874 has a normal nFAULT pulse during waking. If ARM also woke the driver and that pulse immediately cleared ARM and put it back to sleep, ordinary startup could defeat itself.

The final circuit instead uses **FEED_ENABLE = LOGIC_GOOD AND PHYS_OK** for driver nSLEEP and the eFuse shutdown network. Drivers wake and VM ramps with commands blocked. Fault and power-good qualification then allow a deliberate ARM edge. Command permission is separate and actively drives both motor inputs low when cleared. Output-sensed eFuse power-good prevents arming simply because input voltage is present before the output is ready. [Driver startup discussion](driver_margin_review.md), [enable circuit](enable_interface_spec.md).

The Pi still provides one PWM and one direction signal per side. Schmitt inverters/NAND gates decode those signals; a final AND stage applies the latched permission. This adds parts, but it preserves braking during armed PWM off-time while giving a defined coast state on disarm. It also avoids relying on a slowly falling tri-state output to cross a downstream ordinary logic threshold.

## Physical disable, software stop, braking and coasting

| Action/state | Board behavior | What it does not establish |
|---|---|---|
| Software requests a stop | The present software latches its mock controller stop. A future real backend must lower RUN according to the new interface contract. | No proof that current software operates this physical board. |
| RUN low, watchdog expiry or qualified fault | External ARM latch clears; command gating forces IN1/IN2 = 00. Awake bridges coast. | It does not turn off the common input feed or instantly stop wheel motion. |
| SW1 physical disable | Clears motion qualification, lowers nSLEEP and shuts off the eFuse input feed through hardware. | It does not galvanically isolate motor wiring or instantly discharge VM. |
| Armed, PWM low | IN1/IN2 = 11, giving braking/slow-decay recirculation. | PWM=0 is not equivalent to the disarmed coast state. |
| Fault clears or SW1 is re-enabled | Supply/driver qualification can recover; a new ARM edge is still needed. | No automatic restart is intended or credited. |

“Stop” is a requested control state; wheel speed can persist due to inertia or external force. The board's normal disarm behavior is **coast**, not active emergency braking. Physical disable is useful because it does not require HTTP/Python execution, but the board is not a safety-rated E-stop. An actual external isolator/E-stop arrangement remains a separate system decision.

Turning off the feed leaves stored charge and may still allow energy from a turning motor into VM. With no further source or regeneration, the selected bleed/bulk maximum-RC model takes approximately **9.65 seconds from 15 V to 0.3 V**. Measure the rail before handling; that calculation is not a guaranteed safe-to-touch interlock. Pi-off behavior is improved by the single-VM driver architecture and defined nSLEEP/SHDN pull-downs, but abrupt brownout waveforms and arbitrary partial-power conditions still require later validation. [Enable interface](enable_interface_spec.md), [power circuit](power_circuit_spec.md).

A driver OCP latch requires a deliberate physical-disable/re-enable or motor-power cycle, then fresh external ARM. Under-voltage or temperature may recover inside a driver, but the external latch remains cleared. A persistent motor stall might stay within current regulation without asserting nFAULT; neither the shared fault line nor the heartbeat proves a freely rotating motor.

## Why so many components and no added microcontroller?

The current manifest contains **135 electrical entries: 121 fitted components and 14 copper test features**, plus four mechanical mounting holes on the PCB. That count is not a count of ICs or unique purchased types. The four bridges each need supply/charge-pump capacitors and current-limit parts; the remaining circuits add rail supervision, input protection, waveform conditioning and explicit inhibit/re-arm behavior.

The circuit implements those functions without adding a firmware-bearing MCU to the motor-control loop. Discrete logic makes the intended signal dependencies visible, but consumes area and creates additional timing, supply and assembly considerations. It is a reviewed reference architecture, not a proven minimum-component or lowest-cost design. Simplification is possible only with a corresponding review of the behavior it removes or consolidates. Actual production optimization has not been performed.

The 14 test features help access current indication, supplies and permission signals during later authorized measurements. They do not add ADC acquisition or encoder closed-loop control. Current observation remains an analog board test point until additional interfaces are designed.

## What ERC, DRC and independent net checks can establish

ERC checks the relationships represented by symbol pin types and schematic connections. DRC checks configured board geometry/connectivity and schematic parity. Independent comparison additionally catches missing references, wrong footprint IDs, shifted pin maps, disconnected repeated power terminals, lost NC markers and disagreement between native schematic, PCB and the reviewed manifest. [KiCad ERC](https://docs.kicad.org/10.0/en/eeschema/eeschema.html#electrical_rules_check), [KiCad DRC](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#design_rule_checking).

The final read-only comparison of this design checked 135 electrical components, 434 logical pins, 459 physical numbered pads, 15 deliberate NCs and 135 native footprint instances. The command truth table matched separately in the manifest, freshly exported native netlist and PCB. The routed-stage comparison also passed native DRC, connectivity and schematic parity against the final saved board; exact hashes and limits appear in the [check report](../validation/design/design_check_report.md).

Even perfectly matching files can encode the same wrong circuit. Neither ERC nor DRC proves driver losses, winding temperature, battery/BMS behavior, regenerative energy, body-diode transients, gate races, harness polarity, enclosure fit or stopping distance. A zero count must be accompanied by the checked file identity, enabled rules and exclusions. Old reports cannot be carried forward after a circuit change. Existing mock software results likewise remain software-only evidence.
