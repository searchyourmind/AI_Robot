# Rev A circuit review — completed reference CAD

**Evidence update — 2026-09-28:** Earlier unknown motor voltage/ratio and encoder presence are superseded by the [purchase-record evidence](actual_hardware_evidence.md): listed 12 V, 30:1, 500-line GMR motors. The remaining text records earlier reviews, not current hardware verification. The preserved 6 V PCB is [incompatible with direct 12 V input](12v_design_impact.md); actual currents, battery voltage bounds/topology and GPIO wiring remain unresolved.

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
**DRAFT — NOT RELEASED FOR FABRICATION.** Current review: 2026-09-28.

The design-only milestone now has an editable five-sheet KiCad schematic and a
routed 100 × 80 mm, two-layer reference PCB. The schematic contains 107
instances: 97 planned fitted components and ten copper test points excluded
from the BOM. Four mounting holes are PCB-only mechanical features. “Fitted”
here is the intended BOM population, not evidence of an assembled board.

The current circuit directly integrates U1/U2 TB6612FNG devices, with U1 A/B
assigned to front-left/right and U2 A/B to back-left/right. The six buffered
PWM/direction nets fan out for paired left/right commands; each motor has its
own electrically separate output pair. J6 is the custom 16-way logic interface
in [pin_map.md](pin_map.md), with GPIO25 RUN, GPIO17 deliberate ARM and GPIO27
heartbeat. J6 pin 15 is ground; STBY is available at TP10, not a Pi GPIO.

The selected input circuit uses F1, D1 reverse blocking, Q1/Q2 logic-qualified
VM feed, 2×1000 µF bulk, 330 Ω bleed, SMBJ7.0A and a TPS3700 VM window monitor.
Each driver's VM and VCC has 47 µF plus 100 nF local decoupling. The independent
TPS3431 watchdog, logic supervisor, Schmitt conditioning and deliberate-arm
latch qualify STBY; SW1 inhibits a logic input without shorting a GPIO output.
A restored rail, heartbeat or switch alone does not re-arm the latch. These
are reviewed circuit behaviors, not measured results.

The governing circuit/value/pin sources are
[reference_electrical_spec.md](reference_electrical_spec.md),
[power_circuit_spec.md](power_circuit_spec.md),
[enable_interface_spec.md](enable_interface_spec.md), and
[schematic_review.md](schematic_review.md). The custom TB6612, watchdog, latch,
fuse and IDC footprints and their source/assembly limitations are recorded in
those reviews and [footprint_review.md](footprint_review.md). The original
pin/mode tables below remain useful manufacturer review history, but their
“not compared” and unselected-footprint statements are no longer current.

## Actual checks and retained limitations

Native KiCad 10.0.6 [ERC](../validation/design/erc_final.json) reports zero
violations. Native [DRC](../validation/design/drc_final.json) reports zero
violations, zero unconnected items and zero schematic-parity findings under
the recorded rule configuration. [Netlist comparison](../validation/design/schematic_parity.json)
matches all 107 instances, 322 package pins, 60 connected nets and two isolated
NC nets. Source hashes and check configuration are retained; passing these
checks does not certify electrical safety, component assembly or motor function.

The accepted reference input is 5.5–6.5 V with 0.25 A RMS per motor and 0.60 A
peaks limited to 20 ms and 10% duty at <=40 C ambient. Additional derived
constraints include PI_3V3 of 3.2–3.4 V, initial source charging <=0.10 A,
operating ceiling <=3 A, external persistent-overload interruption <=100 ms,
and returned energy <=3 mJ/event at <=1 Hz. Establish Pi logic first; remove
motor input and verify VM <0.3 V after at least 5 s with mechanics stopped
before removing Pi logic. Abrupt Pi loss with stored VM remains unvalidated.
Actual motor/battery/VCC/harness ratings and polarity remain unknown, and the
physical ARM/RUN/heartbeat backend is not implemented by the existing mocks.

Fabrication: **DEFERRED / NOT BUILT**. Assembly: **DEFERRED / NOT ASSEMBLED**.
Physical validation and proposed-PCB integration: **NOT TESTED**. Draft exports
are design-review artifacts, not authorization to fabricate or connect the robot.

## Historical pre-CAD evaluation — preserved

The material below records the earlier requirements/audit gate. Statements such
as “no native CAD,” “not run,” “TBD circuit,” or “before schematic capture” refer
to that earlier stage and are superseded by the current section above and its
linked design records. The earlier calculations remain examples, not the
accepted reference operating specification. Real-robot unknowns remain unknown.

### Rev A circuit review — conditional architecture

**Status: preliminary, NOT electrically approved, NOT CAD checked, NOT physically tested.** USER-CONFIRMED HARDWARE: Pi 5 directly controls both driver boards through GPIO; Arduino is not in the motor loop. Board A channel A -> FrontLeft, A channel B -> FrontRight, board B channel A -> BackLeft, and B channel B -> BackRight. The four geared DC motors share one battery feeding both VM inputs. Pi is separately supplied; Pi ground, both driver grounds and battery negative are common. GPIO allocation, lead polarity, driver-board parts, VCC wiring, motor/source ratings and mechanical constraints remain UNKNOWN. Use [electrical_budget.md](electrical_budget.md) and [design_sources.md](design_sources.md). This file defines a reviewable circuit contract, not a fabricated board or a frozen netlist.

#### Gate before schematic capture/freeze

Accept direct integration of two TB6612FNG ICs only after the four channel current/voltage/thermal envelopes pass review. Inspect the existing driver-board model/schematic, VCC wiring and any pull-ups/regulators before reusing its interface. Retain the user-confirmed direct Pi control path; verify each GPIO-to-input wire before choosing the connector or freezing the pin map. Do not add an Arduino or other motor controller without a new verified requirement. Capture mounting/outline, assembler route and budget before placement.

Reject or revise this architecture if a motor exceeds the accepted driver envelope, source transients cannot be contained, or unpowered interface behavior cannot be made controlled. A custom carrier remains an explicit alternative, requiring its own module schematic/pinout and assembly review.

#### Verified device pin contract

T1 p2 establishes the following for **each** tentative IC U1/U2. Prefix signal/output names with the IC identifier so channels remain electrically separate. `AO1` uses the letter O, not the digit zero.

| Physical pin(s) | Toshiba name | Proposed connection contract |
| --- | --- | --- |
| 1, 2 | AO1 | This IC's channel-A motor terminal 1; connect both pins |
| 3, 4 | PGND1 | Low-impedance power return; connect both |
| 5, 6 | AO2 | This IC's channel-A motor terminal 2; connect both |
| 7, 8 | BO2 | This IC's channel-B motor terminal 2; connect both |
| 9, 10 | PGND2 | Low-impedance power return; connect both |
| 11, 12 | BO1 | This IC's channel-B motor terminal 1; connect both |
| 13, 14, 24 | VM2, VM3, VM1 | Protected motor rail; connect all three with local supply path |
| 15 | PWMB | Pi channel-B PWM; actual GPIO pin TBD |
| 16, 17 | BIN2, BIN1 | Pi channel-B direction; actual GPIO pins TBD |
| 18 | GND | Logic reference tied to common return with controlled current routing |
| 19 | STBY | Hardware-qualified enable, default low |
| 20 | VCC | Logic rail to be verified; nominal 3.3 V proposed, existing VCC unknown |
| 21, 22 | AIN1, AIN2 | Pi channel-A direction; actual GPIO pins TBD |
| 23 | PWMA | Pi channel-A PWM; actual GPIO pin TBD |

This table is a schematic-review reference. It has not been compared with a saved KiCad symbol, footprint or netlist. Duplicate power/output pins must not be left unconnected merely because a library symbol visually groups them. One motor per H-bridge channel; never parallel A/B or U1/U2 outputs. Paired left/right commands may share validated logic inputs or software commands, never output copper.

#### Package and assembly review

T1 p8 and T3 identify **SSOP24-P-300-0.65A**, 0.65 mm pitch, body 7.8±0.2 by 5.6±0.2 mm, overall lead span 7.6±0.3 mm and maximum height 1.6 mm. In the marked-face drawing, the index is next to pin 1 at lower left; pins 12/13/24 are lower right/upper right/upper left. A CAD orientation rotated relative to this drawing is acceptable only if pin numbering, centroid rotation and pin-1 mark remain consistent.

No footprint identifier is approved yet. Compare all 24 pad numbers, pitch, body/lead dimensions, toe/heel/side allowances, courtyard and soldermask/paste against the manufacturer drawing and selected assembly process. Verify no invented exposed pad; this package uses leaded pins for electrical/thermal paths. Place clear pin-1 marks outside soldermask and retain access for inspection and rework. Check the assembler's actual zero-degree library orientation against the top-view assembly drawing, not merely the numeric KiCad rotation. Use one documented placement origin, in mm, consistently across board, drawings and CPL.

Single-sided SMT assembly of the fine-pitch drivers and local passives, with separately reviewed hand assembly of suitable through-hole connectors, is a provisional route. JLCPCB A1 is a capabilities comparison, not a chosen supplier or quotation. Final reflow limits, moisture handling and library land pattern must be reviewed for the actual orderable suffix. A user with suitable magnification, flux and rework tools may hand assemble SSOP; available equipment/experience is unknown.

#### Output modes and stop semantics

T1 p4; H=logic high, L=logic low, X=either. These describe bridge behavior, not guaranteed mechanical stopping distance.

| STBY | IN1 | IN2 | PWM | OUT1 / OUT2 | Meaning |
| --- | --- | --- | --- | --- | --- |
| L | X | X | X | High impedance | Standby, both channels of that IC disabled |
| H | H | L | H | H / L | One direction |
| H | L | H | H | L / H | Opposite direction |
| H | H | L | L | L / L | Short brake during PWM off-time |
| H | L | H | L | L / L | Short brake during PWM off-time |
| H | H | H | X | L / L | Short brake |
| H | L | L | H | High impedance | Stop/coast mode |

`IN1=IN2=L, PWM=L, STBY=H` is not explicitly listed as a separate row in the manufacturer's table. Do not depend on this combination to claim a specific coast/brake mode. For an unambiguous disabled condition, assert STBY low. Duty=0 on an otherwise directional channel is short braking, not the same as removing motor power. Direction reversal needs a reviewed ramp/dead interval and load-dependent current control; internal bridge shoot-through dead time does not prevent mechanical reversal overcurrent. A mock delay is a software behavior proposal until motor data and physical verification justify it.

- **Software stop:** application policy ends the command, latches/disarms as documented and requests the defined bridge state. It depends on the process/OS/backend.
- **STBY disable:** local logic takes both bridges on an IC to high impedance. The motor may continue rotating; diode/regen paths and supply remain present.
- **Short brake:** motor terminals are driven to the same low potential. Mechanical energy becomes heat; braking current requires review.
- **Physical power interruption:** a rated circuit opens the motor supply. Stored energy remains and the Pi can remain powered. Switching rating, returned-energy path and discharge must be designed; it is not necessarily an immediate mechanical stop.

#### Default-off enable and watchdog proposal

Use a locally defined enable function such as `ENABLE = ARM_REQUEST AND PHYSICAL_ENABLE AND WATCHDOG_OK AND LOGIC_GOOD`, driving both STBY inputs or separately qualified enables. The components, thresholds, timeout, pull values and supply domains are TBD. Each condition must default inactive on open/disconnected inputs and startup. A physical enable switch should operate a gate input with a defined pull-down or open a rated supply circuit; **do not short a push-pull GPIO/STBY output to ground with a switch**.

A normally-open enable path into a pulled-low logic input is a possible prototype arrangement, with disconnect interpreted as disable. Pick real gate/buffer/watchdog parts only after checking voltage, input current, power-off isolation and fault behavior. Prevent accidental auto-rearm after a physical disable or watchdog event; use feedback and a latched recovery requirement if needed. Feedback wiring/pins remain TBD and software alone cannot prove switch state.

The TB6612 inputs include nominal 200 kohm pull-downs (T1 pp2–3). They help establish inactive inputs but do not replace a reviewed external enable network. Size any external pull and series impedance from leakage, gate thresholds, GPIO loading, wiring noise and RC rise/fall time, including a controller configured incorrectly at boot. A 200 kohm pull-down cannot override an actively high output.

A Python watchdog handles only failures where its thread executes and can reach the backend. OS freeze, SIGSTOP, deadlock, killed process, stuck output or an independently repeating PWM engine can defeat it. If unattended motion or such failure coverage is required, qualify STBY with an **independent hardware timeout** on the confirmed direct Pi GPIO path. Its heartbeat must track a healthy control loop with a still-valid command; a separate endless heartbeat must not keep expired AI intent alive. This does not justify adding a new MCU by default. Until a validated independent mechanism exists, document the uncovered failures and restrict physical tests to supervised staged bring-up. The prototype disable is not a certified emergency stop.

#### Supply, power sequence and back-power checks

Keep the Pi on its existing appropriate supply. The existing common ground is user-confirmed. The proposed interface carries that reference and verified logic only; no tying of independent supply outputs. Existing driver VCC wiring remains to be traced. Any selected logic source must power all relevant input-protection paths coherently. T1's input equivalent circuit shows a VCC-related protection path; it supplies no quantified `Ioff` guarantee permitting high inputs when VCC=0. Its powered input-high range extends only to VCC+0.2 V. The 6 V absolute input limit is not permission for arbitrary unpowered drive.

RP1 §3.1.3 describes very little pin current below 3.63 V when its IO supply is zero. This limited pad statement does not cover TB6612 power-off tolerance, external interface components, 5 V GPIO signaling, all Pi header circuitry or every power sequence. Use nominal 3.3 V signaling; close the actual interface's powered/unpowered requirements rather than assuming a generic Pi rule.

| State to analyze and later measure | Required behavior / unresolved evidence |
| --- | --- |
| Pi off, motor source on | Both STBY inactive; no unintended logic rail rise/back-power; driver VM-on/VCC-off behavior and gate behavior need closure |
| Pi on, VM off | Motors inactive; GPIO may reach powered VCC only; no unintended VM charging through selected circuit |
| Driver VCC off but Pi output high | Prevent through shared sequencing or specified isolation; series resistors alone do not establish acceptable injection current |
| Boot, halt, brownout, USB reconnect | Enable remains low until fresh deliberate arm; observe actual pins and supply ramps |
| Interface disconnected | Local disable; no floating enable or return-dependent assertion |
| Physical disable with spinning motor | Review energy disposal and VM excursion; no reliance on a source sink capability that is unverified |

A common ground is necessary for direct non-isolated signaling; motor-current routing must not make the controller's logic reference a shared high-current neck. A logic-rail presence indicator is not proof of correct sequencing. Board design must document rail rise/fall order and any allowed partial-power states before freeze.

#### Decoupling, protection and return paths

As a starting topology per IC, place **10 uF plus 0.1 uF on VM and 10 uF plus 0.1 uF on VCC** close to the relevant pins, following T1 p7 and T4. These are reference capacitances, not selected MPNs or proof that bulk energy requirements are met. Verify effective capacitance under bias, voltage margin, temperature, ripple/ESR, polarity and inrush; additional input bulk is TBD from the energy/current worksheet. Do not replace the local capacitors with a distant single shared electrolytic.

High-current paths to show during layout review:

1. Local VM capacitor -> high-side bridge -> motor connector/harness -> low-side bridge -> PGND -> capacitor return.
2. Brake/freewheel loops through the bridge/motor and the relevant diode paths.
3. Returned motor energy -> VM network -> capacitor/clamp/permitted source path.
4. Input source/fuse/protection -> both drivers, sized for simultaneous demand.

Use short, wide power paths and a continuous ground return with placement controlling where currents flow. Connect signal return without forcing motor current through a narrow logic/Pi ground path. Do not arbitrarily split a ground plane or route signals across a return gap. Keep switching output copper/harness away from sensitive interfaces; consider paired motor wires and local suppression only after measured emissions/transients justify component values. Place protection where its loop inductance is low; clamp overshoot at the IC matters more than nominal clamp voltage at a distant connector.

Expose labeled test points for protected VM, VCC, nearby GND, qualified STBY, each PWM/direction signal and accessible motor terminals. Avoid inviting a grounded oscilloscope probe onto a switching motor terminal without the reviewed measurement method. Encoders are user-confirmed as not integrated. Pi Camera and USB microphone/speaker remain on the existing Pi interfaces. Additional sensor/encoder connectors remain unpopulated/unselected until a concrete sensor model, voltage, cable and use are verified. Do not claim HAT compliance.

#### Review record

| Check | Current evidence | Status |
| --- | --- | --- |
| Manufacturer pin/mode/package reference | T1 inspected; tables above | DOCUMENT REVIEW ONLY |
| Motor voltage/current and both-channel thermal suitability | Required inputs absent | BLOCKED |
| Controller path and motor assignment | Direct Pi GPIO and board/channel-to-wheel assignment user-confirmed; no bench verification | USER-CONFIRMED HARDWARE |
| GPIO allocation, polarity and VCC/module details | Each physical control wire and module circuit still needs tracing | BLOCKED |
| Power-off/enable/protection component design | Contract and scenarios above; no selected circuit | BLOCKED |
| Footprint, netlist, placement, route and connector access | No native CAD created at this gate | NOT RUN |
| ERC/DRC, unconnected nets and schematic/PCB consistency | No native CAD created at this gate | NOT RUN |
| BOM/CPL/assembly origin/rotations | Candidate list only | NOT RUN |
| Physical electrical/thermal/disable checks | No robot/PCB bench testing | NOT TESTED |

Next gate: one user architecture/electrical review after the compact requirements batch is answered; then select parts and capture editable native KiCad files. No fake CAD, manufacturing outputs, assembly evidence or release approval is implied by this document.
