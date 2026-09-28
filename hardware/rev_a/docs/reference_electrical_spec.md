# Reference electrical specification — 12 V redesign

**Provisional 12 V electrical design — actual robot compatibility remains unconfirmed.**

Prepared 2026-09-28. Fabrication: **DEFERRED**. Assembly: **NOT ASSEMBLED**. Physical validation: **NOT TESTED**. The previous 6 V design is preserved in [the immutable archive](../../rev_a_6v_archive/docs/reference_electrical_spec.md). Its incompatibility was found before fabrication; no hardware failure is claimed.

## Scope and status of assumptions

This specification supersedes the earlier 6 V assumptions for the active redesign. The original accepted 6 V exercise remains archived as engineering history. The new limits below are selected for a bounded 12 V-class reference design; they are not measurements of the purchased motors, packs, chassis or harness.

| Parameter | Reference requirement | Status / consequence |
| --- | --- | --- |
| Board input |9–15 V continuous at J1, positive polarity | Provisional engineering envelope; actual pack nominal/min/max and chemistry unconfirmed |
| Pi power | Independent Pi supply; no VM-to-Pi power connection; common GND | Direct Pi control is confirmed; actual power/harness details remain to be checked |
| Logic rail | PI_3V3=3.2–3.4 V at this board | Derived requirement, not a Pi measurement |
| Normal input allocation |≤2.0 A continuous, including board overhead | Distinct from the approximately 2.98 A overload limiter |
| Individual motor regulation |0.791 A nominal; 0.708–0.888 A static screen | Hardware chopping; dynamic overshoot, required starting torque and motor heating unconfirmed |
| Thermal allocation |≤1 A RMS screening point per bridge; 0.90 W/driver; 3.60 W total; junction target <125 °C | A thermal design screen, not permission for four unrestricted 1 A loads or 3.2 A stalls |
| Simultaneous loads | Four bridges may operate together, subject to aggregate limiting | Simultaneous startup may trip the input protection |
| Ambient / PCB | Maximum 40 °C; provisional 100×100 mm; two layers; nominal 1 oz copper | Mounting, enclosure airflow and achieved thermal resistance unverified |
| Motor outputs | U20 FrontLeft; U21 FrontRight; U22 BackLeft; U23 BackRight | Four separate output bridges; actual wheel polarity remains a bench item |
| Logical grouping | FrontLeft/BackLeft share left PWM/direction; FrontRight/BackRight share right commands | Paired control does not parallel outputs or provide independent four-wheel commands |
| PWM | External PWM ≤20 kHz; switching/chopping allowance in driver thermal review | Actual waveform and current ripple must be verified |
| GPIO at J6 | High ≥2.8 V; low ≤0.4 V; driven-edge requirement ≤10 ns/V; short common-ground harness | Interface requirements, not measured Pi behavior; no hot-plug assumption |
| VM/source transients | VM ≤32 V; upstream protected path ≤45 V | Validation targets including temperature and layout overshoot |
| Returned energy |≤0.1 J total to VM/event, ≤0.1 Hz, initiallyVM ≤15 V; recover before next event | Actual motor/robot braking energy unknown; continuous back-driving excluded |
| Discharge | Remove source, stop mechanical input, wait ≥15 s and measureVM <0.3 V | Stored VM persists after physical disable |

Packs listed as 12 V and 2500 mAh do not establish 3S chemistry or 12.6 V charge maximum. Seller claims of <4 A continuous,<10 A startup and 48 W are not validated BMS characteristics. The two-pack inventory does not establish series, parallel, independent or spare usage. MG513P30_12V and its 0.36 A/3.2 A data remain candidate evidence only.

## Control and fault behavior

`FEED_ENABLE = LOGIC_GOOD AND PHYS_OK` drives eFuse SHDN and all four driver nSLEEP pins. Drivers therefore wake when physical and logic permission are valid, before ARM. Power-good, VM monitor and driver faults qualify the external arm latch; commands remain blocked until qualification and a fresh ARM edge. This avoids feeding the normal driver wake fault pulse back into the very signal that wakes it.

The PWM-mode command decoder produces:

| Motion permission | PWM | Direction | Driver inputs | Result while awake |
| --- | --- | --- | --- | --- |
|0|Any|Any|00|Coast / high impedance|
|1|0|Any|11|Brake / low-side slow decay|
|1|1|0|01|Reverse|
|1|1|1|10|Forward|

Thus **armed PWM=0 brakes; disarmed commands coast**. Physical INHIBIT also sleeps the bridges and removes the source feed. A fault, RUN low or watchdog expiry clears motion permission; recovery alone does not create ARM. Fixed-off-time current chopping does not itself report a fault and is not a stall detector.

Keep PWM low before arming or changing direction. Allow logic settling and a motor-specific deceleration/reversal interval before applying PWM. The combinational decoder contains no reversal timer, and GPIO software for this hardware remains unimplemented. Existing software tests use mocks only.

## Supply, current and thermal requirements

U13 provides controlled startup, aggregate limiting and an overload latch. The nominal 2.980 A input setting has a separate conservative 2.656–3.311 A static screen; it is not an instantaneous hard limit. Per-driver current regulation does not prove safe sustained motor stall or adequate starting torque. Prohibit sustained stalls until motor-specific limits/timeouts are validated.

During physical enable but disarm, allocate up to 28 mA VM quiescent current for the four awake drivers, plus bleed and power-path overhead. Cold-start capacitor current screens at 0.101 A, or 0.126 A with an additional 20% timing-capacitance allowance. Including awake loads gives approximately 0.18 A as a conservative input screen. Warm fault recovery may bypass the slow ramp when retained VM is already above PGTH's falling threshold; it must be validated separately.

The driver screen targets effective thermal resistance ≤80 °C/W including adjacent heat. Begin with at least 4 cm² ground-copper spreading per bridge, both copper layers and reviewed thermal vias. Do not assign the datasheet's JEDEC thermal resistance to this board without evidence. Routing, copper, airflow and physical temperatures remain release conditions.

The normal source maximum precedes TVS selection. 50 V VM capacitors provide margin over the 32 V transient target. Minimum storage 2304 µF takes 0.1 J from 15 V to 17.658 V; this is a mathematical bound for the selected capacitors, not a robot braking measurement. The detailed topology, tolerance assumptions, fuse and clamp coordination are in [power_circuit_spec.md](power_circuit_spec.md) and [power_path_review_12v.md](power_path_review_12v.md).

## Compatibility and validation gates

Confirm the actual motor label, pack minimum/maximum, BMS/source fault behavior, wiring, encoder interface and required torque before asserting real-robot compatibility. The existing TB6612 breakout boards remain prototype hardware; their regulator function and rail wiring are not established by the word “regulated.” The new custom board is a different driver implementation.

Physical enable, disarm and input disconnection have different effects. Input disconnection does not instantly remove stored VM, and coast is not a measured mechanical stopping guarantee. The DRV8874 single-VM architecture removes the old TB6612 separate-VCC dependency, but Pi brownout and arbitrary wiring faults still require validation.

Fabrication, assembly and powered validation remain deferred. Native ERC/DRC/parity and routed-width evidence must be reported from the new artifacts; old 6 V checks and the preserved mock test reports do not qualify this redesign. Primary electrical sources and document revisions are consolidated in the [power-path review](power_path_review_12v.md); the [driver review](driver_margin_review.md) supplies the detailed current and thermal analysis.
