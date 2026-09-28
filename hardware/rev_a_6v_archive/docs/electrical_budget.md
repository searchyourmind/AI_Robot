# Electrical budget — current reference and retained screening history

**Evidence update — 2026-09-28:** Earlier unknown motor voltage/ratio and encoder presence are superseded by the [purchase-record evidence](actual_hardware_evidence.md): listed 12 V, 30:1, 500-line GMR motors. The remaining text records earlier reviews, not current hardware verification. The preserved 6 V PCB is [incompatible with direct 12 V input](12v_design_impact.md); actual currents, battery voltage bounds/topology and GPIO wiring remain unresolved.

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
Current reference calculation: 2026-09-28. The native schematic/layout milestone
is complete; the physical motor/source qualification remains unresolved.

[reference_electrical_spec.md](reference_electrical_spec.md) is the governing
numerical budget; [power_circuit_spec.md](power_circuit_spec.md) supplies the
selected protection/monitor circuit, and [routing_rationale.md](routing_rationale.md)
records routed widths and resistance calculations. The old larger-current
examples below are preserved to show the original screening method. They are
not the accepted motor envelope and must not be used as the board's rating.

| Quantity | Current reference / evidence boundary |
|---|---|
| Input / four-channel load | 6 V nominal, 5.5–6.5 V; each motor <=0.25 A RMS, <=0.60 A for <=20 ms and <=10% duty; peaks count within RMS |
| Aggregate screening | <=1.0 A summed motor RMS, approximately 1.05 A input-path screening with overhead; <=2.4 A coincident motor peak |
| Logic / ambient | PI_3V3 3.2–3.4 V at PCB; <=40 C ambient; reference requirements, not measured robot conditions |
| Driver package model | Two channels ×(0.25 A)²×1.4 Ω plus 50 mW =0.225 W/package; 40 C +160 C/W×0.225 W =76 C screening estimate, not measured or guaranteed hot-state performance |
| Source / Q1 inrush | Charge at <=0.10 A with STBY inhibited, then operating source ceiling <=3 A after VM_OK stable; persistent overload must be externally interrupted within 100 ms |
| VM qualification | Approximately >=4.85 V required for initial arm; nominal UV/OV rising thresholds 4.80/7.16 V; low-input simultaneous peaks may disable, rather than guarantee full torque |
| Returned energy | <=3 mJ/event, <=1 event/s, starting VM <=6.5 V; minimum 1.6 mF bulk gives calculated 6.782 V plus <=0.20 V overshoot allowance |
| Planned routing | 1.00 mm input/VM trunks, 0.60 mm motor outputs; individual 0.40 mm VM branches up to 27.09 mm including fanout/link segments at <=0.50 A RMS/package; local pad geometry and actual lengths reviewed separately |
| Signal / rail routing | 0.25 mm nominal signals with >=0.20 mm actual routes permitted, including about 10 mm sections; 0.40 mm nominal PI_3V3/GND plus ground zones and reviewed local fanout |
| Pi budget | Reserve 60 mA for board logic/driver VCC; not a claim of measured spare Pi capacity |

The narrower signal/branch routes supersede the preliminary worksheet defaults.
Final routing uses individual 0.80 mm pad /0.30 mm hole vias on REV_PROTECTED,
VM and some outputs, superseding the earlier paired-via preference. With assumed
25 µm plating, the calculated single-via resistance is approximately 1.35 mΩ at
60 C; the input-path 1.05 A RMS loss is approximately 1.49 mW. This is a
resistance/loss screen, not physical via-ampacity validation.
The actual [native DRC](../validation/design/drc_final.json) has zero violations,
unconnected items and schematic-parity findings under its recorded rules. Width
and connectivity checks do not establish trace temperature, load sharing,
regenerative behavior or EMC. Manufacturer/process tolerances and the actual
robot load still need review before any later fabrication release.

Pi logic must precede motor input and remain until motor input is removed,
mechanics stop, at least 5 s has elapsed and VM is measured below 0.3 V. A timer
alone does not establish discharge. Unrestricted battery hot-plug, an unknown
BMS, sustained motor stall or abrupt Pi loss with charged VM are outside the
qualified reference assumptions. The PCB provides neither per-channel current
regulation nor a certified emergency stop.

Fabrication and assembly are **DEFERRED / NOT BUILT / NOT ASSEMBLED**.
Physical current, voltage, temperature, stopping behavior and PCB integration
are **NOT TESTED**. Real motor/source/harness values in the historical input
worksheet remain unresolved, rather than being replaced by the accepted
reference assumptions.

## Historical pre-CAD evaluation — preserved

The material below records the earlier requirements/audit gate. Statements such
as “no native CAD,” “not run,” “TBD circuit,” or “before schematic capture” refer
to that earlier stage and are superseded by the current section above and its
linked design records. The earlier calculations remain examples, not the
accepted reference operating specification. Real-robot unknowns remain unknown.

### Preliminary current, power and thermal budget

**PROPOSED / NOT APPROVED.** USER-CONFIRMED HARDWARE: Pi 5 directly controls both drivers through GPIO; no Arduino is in the motor loop. Driver board A channel A drives FrontLeft, A channel B drives FrontRight, board B channel A drives BackLeft, and B channel B drives BackRight. Four geared DC motors share one motor battery through the two VM inputs; Pi is separately supplied and Pi/driver/battery-negative grounds are common. Exact GPIO allocation, polarity, module components, existing VCC source, motor/source ratings and mounting data remain UNKNOWN. This worksheet gives acceptance calculations, not a selected current rating. Sources T1–T4/R1/R2/A1–A5 are in [design_sources.md](design_sources.md).

#### Required inputs

| Quantity | Value | Evidence needed |
| --- | --- | --- |
| M1–M4 rated voltage, permitted PWM behavior | TBD for each | Manufacturer model/datasheet |
| Continuous operating current under intended load | TBD for each | Manufacturer information and approved controlled-load measurement |
| Startup/stall current and duration envelope | TBD for each | Manufacturer data or a reviewed current-limited characterization; no uncontrolled stall test |
| Battery/source minimum, nominal, full-charge maximum | TBD | Model/cell configuration and source/BMS documentation |
| Source sink/recharge capability; behavior when protection disconnects | TBD | Source/BMS documentation |
| Harness length, wire gauge, connector contact resistance | TBD | Actual harness and manufacturer ratings |
| Simultaneous starts/reversals and loading of each IC | Board A: front pair; board B: rear pair; current/profile TBD | User-confirmed channel assignment; operating profile and measurements still required |
| Enclosure ambient, copper geometry, nearby heat | TBD | Mounting/environment constraints |
| Pi supply and logic rail headroom | Separate Pi supply retained; model and VCC source TBD | Pi supply label, Pi Camera/USB mic/speaker load, actual VCC wiring |

#### TB6612FNG screening envelope

T1 p3 is the controlling reference; these are distinct limits:

| Parameter | Operating range / condition | Absolute maximum or other limitation |
| --- | --- | --- |
| VM | 2.5–13.5 V | 15 V |
| VCC | 2.7–5.5 V | 6 V |
| Output current | 1.0 A at VM >=4.5 V; 0.4 A at 2.5<=VM<4.5 V, latter row specifies without PWM | 1.2 A per channel |
| Pulsed output | Must also satisfy thermal/current waveform review | 2 A, tw=20 ms, repetitive duty <=20%; 3.2 A, tw=10 ms, single pulse |
| PWM frequency | <=100 kHz | Not a proposed software setting |
| Ambient | -20 to +85 C | Application temperature/rating margins still needed |

The absolute limits are not design targets or four-motor continuous capability. A startup lasting hundreds of milliseconds cannot be justified by the single-pulse number. A fuse is generally too slow to enforce an IC's peak-current envelope. Reject these drivers for this application if any intended motor/voltage/transient/thermal requirement cannot be met with margin; document the replacement decision before CAD.

#### Budget equations

For motor k, establish measured/modelled `i_k(t)` at full-charge voltage, load, acceleration, stop and reversal. Calculate `I_rms,k = sqrt(mean(i_k(t)^2))`; average current is insufficient for copper and bridge heating.

- Conservative input screening at continuous full drive: `I_input = sum(I_motor,k) + I_VM,IC + I_aux`. Evaluate all four starts separately. PWM input current and motor recirculation current differ; do not size a channel from battery average current.
- Board input power: `P_input = V_input * I_input`; connector/wire loss: `I_rms^2 * R_path`; round-trip drop: `I * (R_supply + R_return + R_contacts + R_protection)`.
- Per IC: `P_package ~= sum(mean(i_channel(t)^2 * R_bridge(state,T,V))) + P_switch + P_logic`. Off-time braking/freewheel loss remains; multiplying full-drive loss by PWM duty alone can underestimate it.
- `T_j ~= T_ambient + theta_JA,effective * P_package`. Effective thermal resistance depends on the final copper, airflow, enclosure and the other IC's heat. Iterate resistance with temperature and retain margin below allowed limits.
- Rail burst hold-up: `C >= I_step * dt / allowed_droop`, with additional ESR/ESL step and capacitance derating. This cannot replace continuous source capability.
- Regenerative energy estimate: `E_L = 0.5*L*I^2`; include mechanical kinetic energy returned through the motor. If all absorbed by a capacitor, `V_final = sqrt(V_initial^2 + 2*E_return/C)`. Validate clamp and source behavior when disconnected/full.

#### Illustrative thermal screening only

**The following currents are invented examples for calculation, not motor specifications or approved limits.** At T1 p5's test point (VM=VCC=5 V, 25 C), the 1 A combined bridge drop is 0.5 V typical / 0.7 V maximum. A `0.7 ohm` effective resistance is used below only as a simple sensitivity model; it is not a guaranteed resistance at 3.3 V logic, hot junctions, every current or PWM state.

| Example: both channels of one IC equally loaded | Conduction estimate, 2 × I² × 0.7 | Rise using 160 C/W IC-only reference |
| --- | --- | --- |
| 0.50 A RMS per channel | 0.350 W | 56 C |
| 0.75 A RMS per channel | 0.788 W | 126 C |
| 1.00 A RMS per channel | 1.400 W | 224 C |

These omit switching/logic losses. The 1 A example already exceeds T1's 25 C dissipation entries: 0.78 W IC-only, 0.89 W for its 50×50 mm board example, and 1.36 W for its larger board example. The listed boards are not our layout. From those curves, a linear screening derating to 50 C gives approximately `0.8 × PD(25 C)` (0.624/0.712/1.088 W); this is a reading of the reference curves, not a certified junction limit for a new PCB. Never substitute the 175 C thermal-shutdown design target for an allowed operating junction temperature. Any uncertainty in junction limits/thermal characterization must be resolved before approval.

Both ICs heat the same board; two acceptable isolated-package calculations do not prove acceptable simultaneous four-motor operation. Thermal shutdown is not a current regulator or a valid normal operating mode. Final calculations need actual hot-state losses and board thermal evidence; physical measurements remain NOT TESTED.

#### Logic load and supply

Direct Pi GPIO control is user-confirmed. Proposed Rev A logic rail: 3.3 V from the Pi logic supply, subject to rail-headroom and sequencing review; the existing driver VCC wiring is still UNKNOWN. For each IC, T1 p5 gives ICC maximum 1.8 mA at VCC=3 V and 2.2 mA at 5.5 V; these are specified test points, not a published 3.3 V worst-case bound. Budget conservatively after selecting the interface/enable logic and verifying all rail tolerances. Add input bias, external pull resistors, enable gate/watchdog, LEDs and any justified sensors explicitly. Do not connect an external regulator output to the Pi 3.3 V rail or motor VM to either Pi supply pin.

At nominal 3.3 V, the driver's threshold formulas imply VIH>=2.31 V and VIL<=0.99 V. Check worst-case loaded controller VOH/VOL against worst-case VCC thresholds, ground bounce and harness drop. VCC=5 V would require VIH>=3.5 V, so nominal Pi 3.3 V drive is not guaranteed sufficient.

#### Provisional copper and via assumptions

These are worksheet defaults to review, **not KiCad net classes or proven ampacities**:

- Two-layer, 1.6 mm FR-4, nominal 35 um external copper; final finished copper and etch tolerance from selected fabricator. Ambient 40 C, desired trace rise <=10 C and motor supply/return drop <=2% of minimum VM are proposed targets requiring review.
- Example only: a 50 mm long, 1 mm wide, 35 um copper trace has `R ~= rho*L/(w*t) ~= 24.6 milliohm` at 20 C using `rho=1.724e-8 ohm*m`. A 100 mm supply+return path therefore drops about 49 mV at 1 A before connectors, vias or heating. `R(T) ~= R20*[1+0.00393*(T-20)]`.
- Final width/clearance must satisfy current, allowable temperature rise, drop, neck-downs, pad fanout and manufacturing tolerances. Use an identified thermal/current method plus measurement; this resistance example provides no trace-temperature guarantee.
- Keep motor paths on an outer layer where practical. A hypothetical 0.30 mm finished-hole / 0.80 mm pad via with 25 um barrel plating and 1.6 mm length has roughly `R ~= rho*length/(pi*diameter*plating) ~= 1.17 milliohm` at 20 C. Plating is an assumption, not a verified fabrication minimum. Use parallel vias with balanced feeds only after current/thermal review; never assign a generic amps-per-via rating. Check solder wicking and keep ordinary open vias off IC solder pads.
- Move to four layers if the real outline/pin count cannot preserve short current loops, continuous signal return and adequate thermal copper. Four layers alone do not fix an undersized driver or power connector.

#### Protection coordination worksheet

`Fuse/limiter -> reverse-polarity protection -> protected VM distribution`, with local caps/clamp and an intentional return path, is a proposed topology only. Exact order depends on the chosen reverse-protection/clamp circuit and failure analysis. Select no ratings until source and motor data exist.

| Item | Required coordination |
| --- | --- |
| Input fuse/limiter | Voltage, DC breaking capacity, source fault current, harness/contact ampacity, ambient derating, startup I²t and fuse clearing curve; semiconductor protection may require a faster limiter |
| Reverse protection | Allowed conduction drop/heating, fault orientation, MOSFET body diode and whether regeneration can reach the source |
| TVS / energy clamp | Stand-off above full-charge maximum; worst-case clamp including tolerance/current/inductance below all affected limits with margin; repeated pulse energy and thermal recovery |
| Connectors / switch | RMS and transient current, DC inductive breaking rating, wire acceptance, retention, polarity and accessible termination |
| Capacitors | VM/VCC transient voltage including fault conditions, temperature, ESR/ripple, ceramic DC-bias derating and life; capacitance marking alone is insufficient |

A reverse blocker or opened motor switch can trap returned energy on VM. A battery/BMS or bench supply must not be assumed to sink it. Coordinate the energy path, clamp and switching sequence; a generic TVS part number cannot be selected from nominal battery voltage alone.
