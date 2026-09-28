# Unresolved risks and release gates

- Exact motor identity, current-time profile, gearbox torque and required startup torque are unknown. Current chopping can prevent the motor from starting; it does not prevent all motor overheating or detect mechanical stall.
- Actual battery maximum, minimum, chemistry, installed topology, source impedance, available short-circuit current and BMS trip curves are unknown. Seller <4 A / <10 A /48 W claims are not validated protection curves. Never infer series/parallel wiring from two purchased packs.
- The eFuse may latch off on simultaneous starts. Warm recovery with retained VM charge can differ from cold soft start. Transient/TVS energy and clamp limits require waveform testing.
- Effective thermal resistance, driver switching loss, capacitors under DC bias, ground-return impedance and EMI remain unmeasured. Native copper widths alone do not prove thermal compliance.
- The physical inhibit is an electronic disable; VM retains energy and motor backdrive can recharge it. It is not a safety-certified emergency stop or isolation switch. Disarm coast does not guarantee the robot stops within a particular distance.
- Actual Pi/driver GPIO maps, wiring polarities, Pi supply, encoders, external switch/fuse/BMS arrangement and board mounting are unknown. The custom J6 pinout is a proposal, not an observed harness.
- The software is mock-only; the new hardware interface has no real backend, no fault-return GPIO and no four-wheel closed-loop encoder control.
- TPS26630 thermal-pad holes under paste require filled/capped/planarized fabrication. Vendor capability, assembly process, sourcing, cost and enclosure fit remain unqualified.

The [requirements](requirements_assumptions.md), [electrical specification](reference_electrical_spec.md), [driver review](driver_margin_review.md) and [bring-up plan](../validation/bring_up.md) define the work required before release. Fabrication DEFERRED; assembly NOT ASSEMBLED; physical validation NOT TESTED.
