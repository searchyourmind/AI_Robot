# Bounded reference electrical specification

**6 V REFERENCE ONLY — DIRECT 12 V INPUT INCOMPATIBLE.** The 2026-09-28 purchase-record update establishes listed 12 V motors and packs. This document retains the existing 5.5–6.5 V design; its calculations, parts and checks have not been qualified for that system. See the [12 V impact review](12v_design_impact.md) and [current hardware evidence](actual_hardware_evidence.md).

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
**DRAFT — NOT RELEASED FOR FABRICATION.** Prepared 2026-09-28.

The user accepted the reference values below for completing the design-only milestone. They are not measurements or specifications of the existing motors, battery, harness or prototype. The prior [electrical budget](electrical_budget.md) remains the record of unresolved real-robot compatibility; this document supplies the separate reference calculation. Fabrication: DEFERRED / NOT BUILT. Assembly: DEFERRED / NOT ASSEMBLED. Physical validation and integration with this PCB: NOT TESTED.

## Accepted reference values and resulting constraints

| Parameter | Reference value | Status / consequence |
| --- | --- | --- |
| Motor input | 6 V nominal; 5.5–6.5 V at the board input | User accepted reference assumption. This is upstream of protection losses, not guaranteed motor-terminal voltage. |
| Each of four motor channels | 0.25 A RMS; 0.60 A maximum for <=20 ms at <=10% repetition duty | User accepted reference assumption. RMS includes the peaks and braking current; it is not 0.25 A plus an additional peak allowance. |
| Simultaneous loads | Both channels of both ICs may carry their reference profiles together | Design calculation; four outputs remain electrically separate. |
| Ambient / PCB | Maximum 40 C; 100×80 mm, two layers, nominal 1 oz copper | User accepted reference assumptions; enclosure, airflow and mounting compatibility remain unknown. |
| Controller / supply separation | Direct Pi 5 GPIO; independent existing Pi supply; shared ground; logic from Pi 3.3 V | Direct-Pi architecture is confirmed; the new rail arrangement is accepted for the reference design. Existing module VCC wiring is still unknown. |
| Mapping | U1A FrontLeft; U1B FrontRight; U2A BackLeft; U2B BackRight | User-confirmed mapping. Paired commands may fan out logic; never parallel bridge outputs. |
| Logic supply tolerance | PI_3V3 = 3.2–3.4 V at the PCB | Derived reference requirement, not a measured Pi rail. A low rail inhibits arming. No external regulator feeds this rail. |
| Protected VM | Initial arming requires approximately 4.85 V or more; undervoltage/overvoltage monitor nominal thresholds 4.80/7.16 V rising | Derived operating condition. Protection drop at low input and coincident peaks can cause a deliberate disable; full peak torque at 5.5 V input is not guaranteed. |
| Source behavior | Initial bulk charging with STBY inhibited and source limit <=0.10 A; after VM_OK is stable, operating current ceiling <=3.0 A; persistent overload above the normal pulse envelope must be externally disconnected within 100 ms | Derived source requirement. This PCB does not provide per-channel current regulation or timed electronic overcurrent shutdown. A battery with an unknown BMS is not qualified by this specification. |
| Returned energy | <=3 mJ total into VM per event, no more than one event/s; initial VM <=6.5 V | Derived reference operating bound for the selected bulk capacitors, not a measured robot braking capability. Include motor inductance and mechanical energy. |
| Rail sequencing | Pi logic established before motor input; Pi logic retained until motor input is removed, mechanics stop and VM <0.3 V | Required limitation. Abrupt Pi loss with residual VM is an unvalidated partial-power condition. |

Interpret the 0.25 A limit as a rolling 1 s RMS ceiling and also as a long-term ceiling. For example, 0.60 A for 10% of a cycle leaves only `sqrt((0.25² − 0.1×0.60²)/0.9) = 0.172 A` for the other 90%. The startup, stall, reversal and braking profiles of a compatible motor must satisfy all limits. A sustained stall above the envelope is outside this reference specification; the fuse does not enforce this envelope.

## Driver and logic margins

The manufacturer pin, operating-range and mode reviews are retained in [circuit_review.md](circuit_review.md) and [design_sources.md](design_sources.md). The reference peak is 60% of the 1 A operating-current entry for VM >=4.5 V and is below the 1.2 A/channel absolute-current entry. Toshiba's much higher pulse entries have explicit duration/duty conditions; they are not used to justify this design.

At maximum reference VCC, required driver VIH is `0.7×3.4 = 2.38 V`. At minimum VCC the VIL ceiling is `0.3×3.2 = 0.96 V`. The selected interface must preserve those limits at the IC pins after series resistors, pull resistors, fanout and ground noise. Inputs must never exceed `VCC+0.2 V`. PI_3V3 also supplies the local logic so no separately powered input source is intentionally present when the Pi rail is off. Do not apply external 5 V to the GPIO interface.

Use STBY low for unambiguous disabled/high-impedance outputs while VCC is valid. STBY high with opposite IN1/IN2 and PWM low produces short brake. IN1=IN2=0 with PWM high is the documented stop combination; all three low with STBY high is not an explicitly documented mode. The hardware enable circuit owns STBY, receives VM_OK and LOGIC_GOOD, and requires a new arm edge after a fault. Hardware timeout and mock-software timeout evidence remain separate.

## Shared-package thermal calculation

This is a deliberately conservative **screening model, not a guaranteed 3.3 V/hot-junction resistance specification**. Toshiba's 0.7 V maximum combined drop at 1 A is specified at VM=VCC=5 V, 25 C. Use twice its effective resistance, `R_bridge,model = 1.4 ohm`, plus 50 mW per package for switching/logic as an engineering allowance. The latter allowance must be verified at the selected PWM frequency and actual switching behavior.

For both channels of one IC:

`P_IC,model = 2 × (0.25 A)² × 1.4 ohm + 0.050 W = 0.225 W`.

Using Toshiba's IC-only reference thermal resistance, `Tj,model = 40 C + 160 C/W ×0.225 W = 76 C`. Two ICs dissipate 0.45 W together in this model. This does not establish the board's actual thermal resistance or the resistance of the switches at 3.3 V logic. The 0.60 A/20 ms coincident pulse adds a conduction-energy estimate of `2×0.60²×1.4×0.020 = 20.2 mJ` in each package; physical transient temperature remains unmeasured. Thermal shutdown is not a normal control mode.

Q1 has no controlled inrush circuit. Charge the bulk capacitance using a source limited to 0.10 A while STBY is inhibited, then raise the source current ceiling only after VM_OK is stable. This bounds initial Q1 dissipation by 6.5 V×0.10 A=0.65 W, although the manufacturer thermal/SOA board conditions still differ from this board. Automatic battery hot-plug is outside this reference design.

The design target for a later thermal review is junction temperature below 100 C at the accepted 40 C ambient with all four channels active. Reject or revise the driver choice if measured loss, transient heating or copper performance fails the reference target. The old higher-current illustrative examples are not the new current specification.

## Input, copper and energy calculations

An upper screening bound on aggregate normal RMS current is `sum(I_channel,RMS) = 1 A`, before approximately 20 mA VM bleed load and IC supply current. Allow 1.05 A RMS for input-path screening. Four simultaneous peaks can demand approximately 2.4 A plus small overhead. Input current under PWM can differ from motor current; this calculation does not estimate regenerative current by multiplying motor current by duty.

At a 1 A aggregate operating point, the nominal fuse resistance 0.0367 ohm, the diode's 0.49 V maximum test-point drop, and 0.085 ohm Q1 resistance yield `5.5−0.0367−0.49−0.085 = 4.888 V` before copper/harness loss. This is a screening point, not a temperature-wide voltage guarantee. At 2.4 A the same model gives 4.718 V; undervoltage may therefore latch the board disabled at the low input corner. Do not remove that behavior to make the specification appear wider.

At 1.05 A RMS, Q1 conduction is approximately 0.094 W using its 25 C resistance limit; a 1.5× hot-resistance sensitivity gives 0.141 W. D1 can dissipate approximately 0.51 W at that current using the 0.49 V test-point drop. Give D1 and Q1 useful copper area and separation from the driver ICs; their manufacturer thermal examples use different boards. These are heat-load calculations, not validated package temperatures.

The two 1000 µF capacitors have a combined initial minimum of 1600 µF. Ignoring the additional local capacitors gives conservative energy capacity:

`V_after = sqrt(6.5² + 2×0.003/0.0016) = 6.782 V`.

Reserve a further 0.20 V for ESR/ESL and layout overshoot; the resulting 6.982 V target remains below the 7.0 V TVS stand-off rating. That 0.20 V is a design requirement to verify, not a measured transient. The 330 ohm bleed dissipates at least about 0.12 W around the starting voltage, far above the 3 mW average returned-energy budget, allowing the capacitor voltage to return toward its source-defined operating level between isolated events. It cannot absorb sustained braking from an arbitrary robot.

The final routing targets supersede the earlier preliminary width proposal: 0.60 mm motor-output conductors, 1.00 mm input/VM trunks, 0.40 mm individual VM branches, 0.40 mm ground connections with broad continuous ground zones, 0.40 mm PI_3V3, and 0.25 mm nominal signal traces with 0.20 mm routing permitted. Individual VM branches may run 27.09 mm at up to 0.50 A RMS/package; they are not limited to short pad necks. A 50 mm × 1 mm × 35 µm copper track is approximately 24.6 milliohm at 20 C; a 0.60 mm track of the same length is 41.0 milliohm. Use actual routed lengths and hot resistivity for drop review. The 27.09 mm × 0.40 mm branch screens at 38.60 milliohm at 60 C, 9.65 mW at 0.50 A RMS. See [routing_rationale.md](routing_rationale.md) for branch and signal examples. These target values do not guarantee copper temperature. The final design uses individual 0.30 mm finished-hole / 0.80 mm pad vias, including on input, VM-branch and motor-output paths, superseding the preliminary paired-via preference. With assumed >=25 µm plating, one via screens at 1.35 milliohm at 60 C: 1.49 mW at the 1.05 A input-path RMS bound, 0.338 mW at 0.50 A branch RMS, or 0.084 mW at 0.25 A channel RMS. These calculations do not constitute an ampacity guarantee; series via drops must be added. Final fabricated copper/plating remain deferred assumptions.

## Sources and evidence boundaries

Accessed 2026-09-28. Toshiba [TB6612FNG datasheet](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660), served revision 2026-05-13, pp3–7, supplies the driver limits, test conditions, modes, thermal references and local decoupling example. The detailed new part sources and net table are in [power_circuit_spec.md](power_circuit_spec.md). Official [Pi documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html) and [RP1 peripheral specification](https://datasheets.raspberrypi.com/rp1/rp1-peripherals.pdf), build 2023-11-07 b9b6f74-clean §3.1.3, do not establish full-board powered-off tolerance. No mock test, ERC result, CAD render or calculation substitutes for the deferred electrical measurements.
