# Actual robot hardware evidence — repository audit

**Evidence assessment, 2026-09-28. No hardware was operated or newly tested.**
**CURRENT COMPATIBILITY STATUS: the completed 6 V reference design is NOT MATCHED
to the user's purchase-record 12 V system.** Rev A's 5.5–6.5 V input design must
not be treated as suitable for a 12 V battery connection. This is a design-range
mismatch, not a claim that a 12 V motor could never operate at a lower voltage;
that separate operating case has not been qualified. See
[12v_design_impact.md](12v_design_impact.md).

The latest user purchase records identify **two WHEELTEC R3 two-wheel chassis
sets**. Each listing includes two **12 V, 30:1, 500-line GMR encoder motors** and
one **TB6612 regulated dual-channel driver board**, giving four motors and two
boards in total. The records also identify **two 12 V, 2500 mAh lithium packs**
listed with a built-in protection board, continuous current <4 A, startup current
<10 A and maximum power 48 W, plus a **Raspberry Pi 5 4 GB camera kit**. These
are purchase/listing facts, not newly measured electrical characteristics or a
complete installed-system connection diagram. The evidence supplied here is the user's
transcription in chat; original receipts, unit labels and physical connections
were not independently inspected.

The user's earlier installed-system description remains: Pi 5 directly controls
both boards, no Arduino is in the motor loop; Board A A/B serves front-left/right
and Board B A/B serves back-left/right. Independent Pi power and common ground
remain the last reported arrangement, pending reconciliation with the battery
connection graph. The earlier statement “one battery feeds both VM inputs” is
retained as history below and is **superseded as a settled topology claim**:
purchasing two packs does not establish which pack is installed where, whether
one is spare, or whether any packs are connected together.

The [manufacturer-source review](wheeltec_source_review.md) records conditional
candidate-model ratings separately from these purchase facts.

Exact motor identification is still unresolved. **MG513P30_12V is a candidate
only**, not a confirmed MPN for the purchased motors. Existing two-board GPIO
endpoints, module VCC source, current profiles, full battery limits and protection
behavior remain unknown. No hardware was operated or newly tested for this
update.

## Evidence classes and sources

| Class | Meaning in this audit |
|---|---|
| USER-CONFIRMED | Explicit hardware answer recorded in the project; no new physical verification implied |
| PURCHASE-RECORD / LISTING CONFIRMED | Item/count/specification stated in the user-supplied purchase record; not proof of installed topology, exact unit markings or measured behavior |
| CODE / DOCUMENTATION ONLY | A source constant, function or README assertion; does not prove the code deployed on the Pi or the actual wire endpoint |
| PROPOSED / REFERENCE | An accepted design assumption or newly designed PCB interface; never an observed property of the existing robot |
| UNKNOWN | The available evidence does not settle this fact; absence from code is not proof that a physical component is absent |

| ID | Evidence inspected | Scope |
|---|---|---|
| U2 | Latest user-supplied purchase records: 2× WHEELTEC R3 sets, 2× listed 12 V/2500 mAh lithium packs and Pi 5 4 GB camera kit | Purchased item/count/listing information; supersedes earlier unknown purchase identity but does not establish the as-built battery or GPIO graph |
| U1 | Recorded hardware answers in [requirements.md](requirements.md), [pin_map.md](pin_map.md) and [existing_system_audit.md](existing_system_audit.md), dated 2026-09-28 | User-confirmed count, wheel/driver assignment, direct Pi path, supplies/common ground and peripherals |
| B1 | `git show 034882cb2ce8106982508cf1a8309b4fa69673ff:pi_robot/web_motor.py` | Original motor source, read without importing or running it |
| B2 | `git show` of `README.md` and `pi_robot/README.md` at the same baseline | Original high-level single-driver wiring example |
| B3 | Other baseline application scripts and requirements inspected for GPIO names | Camera/vision/CLI use the motor HTTP service; no second pin allocation was found |
| C1 | Current [motor_config.py](../../../pi_robot/motor_config.py), lines 5–24 | Four named channel records; `control_pins` and `polarity` remain `None` |
| C2 | Current [motor_backend.py](../../../pi_robot/motor_backend.py) and [web_motor.py](../../../pi_robot/web_motor.py) | Mock output backend; service rejects a non-mock backend setting |
| R1 | [requirements_assumptions.md](requirements_assumptions.md), [reference_electrical_spec.md](reference_electrical_spec.md) and [power_circuit_spec.md](power_circuit_spec.md) | New reference operating bounds and proposed power/protection architecture |
| R2 | Current [pin_map.md](pin_map.md) and [enable_interface_spec.md](enable_interface_spec.md) | New J6 allocation and proposed ARM/RUN/heartbeat contract |

## Facts requested for hardware compatibility

| Topic / fact | Available evidence | Class | What remains unresolved |
|---|---|---|---|
| Chassis / motor count | 2× WHEELTEC R3 two-wheel sets, each with two encoder motors; four motors total, U2; count also U1 | PURCHASE-RECORD / USER-CONFIRMED | Installed chassis arrangement, exact motor markings and whether supplied units match the listing |
| Motor listed specification | 12 V, 30:1, 500-line GMR encoder motors, U2 | PURCHASE-RECORD / LISTING CONFIRMED | Exact manufacturer MPN; MG513P30_12V is only a candidate, not an identified installed motor |
| Driver count/type | One TB6612 regulated dual-channel board per set; two total, U2/U1 | PURCHASE-RECORD / USER-CONFIRMED | Exact board revision, regulator topology, VCC routing, terminal pinout, IC marking and jumper configuration |
| Wheel assignment | Board A A→front-left, B→front-right; Board B A→back-left, B→back-right, U1 | USER-CONFIRMED | Actual terminal/lead identity and direction polarity |
| Running/current waveform | No per-motor applicable current record | UNKNOWN | Current versus source voltage, load, speed, RMS duty and simultaneous demand; 12 V/30:1 does not establish current |
| Startup/stall/reversal limits | Motor transient current and permitted duration absent from supplied record | UNKNOWN | Peak magnitude, duration, repetition and returned motor energy |
| Purchased batteries | 2× lithium packs listed as 12 V, 2500 mAh, U2 | PURCHASE-RECORD / LISTING CONFIRMED | Exact pack model/chemistry/series count, true nominal voltage, minimum and full-charge maximum |
| Pack advertised output | Continuous <4 A; startup <10 A; maximum 48 W, U2 | PURCHASE-RECORD / LISTING CONFIRMED | Rating conditions/durations and whether those figures describe capability, limits or cutoff behavior; not proof of regulated current limiting |
| Installed motor-source topology | Earlier U1 said one battery feeds both VM inputs; U2 now documents two packs purchased | HISTORICAL REPORT — NEEDS RECONCILIATION | Which pack powers each device, whether one is spare, connections between packs, branches/returns and intervening protection |
| Battery protection board | Each pack listing states built-in protection board, U2 | PURCHASE-RECORD / LISTING CONFIRMED | Exact circuit, over/undervoltage/current cutoffs, delay, recovery, short-circuit behavior, current limiting and charging/sink capability |
| Existing external fuse / reverse protection | Not established for the installed robot | UNKNOWN | Presence, parts, DC interruption and fault-current coordination; listed pack protection does not answer these |
| Regenerative-energy handling | No applicable source sink/absorption or motor-energy evidence | UNKNOWN | Pack/protection behavior during returned energy; protection-board presence does not prove regeneration compatibility |
| Pi identity | Pi 5 direct control reported U1; Pi 5 4 GB camera kit purchased U2 | USER-CONFIRMED / PURCHASE-RECORD CONFIRMED | Actual kit power components, provider/software configuration and available rail headroom |
| Pi power arrangement | Independent Pi power was last reported, U1 | USER-CONFIRMED PRIOR ARRANGEMENT; GRAPH PENDING | Actual supply source/adapter model and how the two purchased packs relate to Pi power |
| Common reference | Pi/driver/battery-negative common ground was last reported, U1 | USER-CONFIRMED PRIOR ARRANGEMENT; GRAPH PENDING | Complete ground topology for all installed packs and devices; no inferred series/parallel pack wiring |
| Existing driver VCC | Baseline README describes Pi 3.3 V, B2; purchased boards are listed as regulated, U2 | DOCUMENTATION ONLY / PURCHASE DESCRIPTION; ACTUAL UNKNOWN | Actual VCC source/voltage and regulator/jumper connections for each module; “regulated” does not settle the rail |
| Controller path | Pi 5 directly controls both boards; no Arduino, U1 | USER-CONFIRMED | Exact Pi header endpoints and fanout for **both** boards |
| GPIO numerical constants | PWMA18, AIN1 23, AIN2 24, PWMB13, BIN1 5, BIN2 6, STBY25, B1 | CODE ONLY | One logical set without board identifiers; neither first-board nor second-board actual wiring is proven |
| Existing PWM | B1 requests two `GPIO.PWM(..., 1000)` objects | CODE ONLY | Actual deployed provider, waveform, timing and fanout; not proof of hardware PWM |
| Existing STBY wiring/disable | One `STBY=25` constant and software writes, B1 | CODE ONLY | Either board's straps, shared/independent enable wire and extra components |
| Current mock channel map | Four records retain user wheel assignment; GPIO/polarity unset, C1/C2 | CODE ONLY | No GPIO backend or physical ARM/RUN/heartbeat implementation |
| Existing power sequence | No complete as-built partial-power/sequence record | UNKNOWN | VM-only/VCC-off behavior, back-power, stored energy and disconnected ground states |
| Reference operating bounds | Completed 5.5–6.5 V design, <=0.25 A RMS and <=0.60 A/20 ms/10% per motor, R1 | PROPOSED / ACCEPTED REFERENCE; NOT MATCHED TO 12 V PURCHASE SYSTEM | A 12 V source cannot be treated as compatible with this input design; lower-voltage motor operation has not been qualified |
| Reference protection/handshake | New F1/TVS/VM gating/monitor/watchdog/latch and GPIO25 RUN/17 ARM/27 HB, R1/R2 | PROPOSED / REFERENCE | Not evidence of existing-module features, battery protection behavior or actual wires |
| Encoder hardware | Four purchased motors are listed with 500-line GMR encoders, U2 | PURCHASE-RECORD / LISTING CONFIRMED | Supply/output voltage, output topology, pinout, count convention, shaft reference and current integration/wiring; do not infer 500 counts per wheel revolution |
| Other peripherals | Pi camera kit purchased U2; USB microphone/speaker previously reported U1 | PURCHASE-RECORD / USER-CONFIRMED | Exact peripheral models, installed connections and power budget |

The new design's F1, TVS, VM monitor and watchdog must not be entered as existing
robot protection. The user accepted reference bounds to complete design work;
that acceptance does not fill the remaining actual motor/battery fields above.

Historical reconciliation: before the purchase update, motor voltage/ratio and
encoder presence were recorded as unknown, one battery was reported to feed both
VM inputs, and encoder integration was reported absent. The purchase evidence
now establishes the listed 12 V/30:1 encoder-motor hardware and two purchased
packs. It does not establish current encoder integration or an installed
one-pack/two-pack topology. The old README example of 6–9 V is superseded as a
source for purchase identification and was never a battery measurement.

## Original GPIO evidence versus current configuration

The original source selects **BCM numbering** at B1 line 18. Its complete logical
motor pin set is below. The physical-header column is the annotation in B2,
not a record of an observed wire. No row may be assigned to Board A or Board B
without additional as-built evidence.

| Baseline logical signal | BCM constant, B1 | Physical-header annotation, B2 | Source-only behavior |
|---|---:|---:|---|
| PWMA | 18 | 12 | One A PWM object, requested 1 kHz |
| AIN1 | 23 | 16 | A direction input 1 |
| AIN2 | 24 | 18 | A direction input 2 |
| PWMB | 13 | 33 | One B PWM object, requested 1 kHz |
| BIN1 | 5 | 29 | B direction input 1 |
| BIN2 | 6 | 31 | B direction input 2 |
| STBY | 25 | 22 | One enable output |

B1 has **two PWM objects and four direction outputs**, not four independently
specified channels. It contains no Board A/Board B identifiers and no second
GPIO set. The user particularly highlights the second board, but the first
board is also represented only by code constants until actual endpoints are
provided. `left()` commands logical A backward and B forward; `right()` reverses
that pairing. This is consistent with paired-side intent and the user's channel
assignment, but does not prove the physical inputs are fanned out. Two READMEs
repeat the same example; repetition is not independent wiring evidence.

The historical `stop_all()` asserts `standby(True)`, drives the four direction
outputs low and requests zero PWM (B1 lines 38–44). Therefore the original word
“stop” is not evidence of an STBY-low physical disable. `forward()` sets IN1 high
and IN2 low for both logical channels (B1 lines 52–59); actual wheel direction
still depends on lead orientation and gearing.

Current C1 represents the confirmed positions explicitly:

| Mock channel | Simulation side | Recorded driver/channel | Recorded position | Actual GPIO tuple / polarity |
|---|---|---|---|---|
| motor_1 | left | board_a / A | front_left | `None` / `None` |
| motor_2 | left | board_b / A | back_left | `None` / `None` |
| motor_3 | right | board_a / B | front_right | `None` / `None` |
| motor_4 | right | board_b / B | back_right | `None` / `None` |

C2 records output requests in memory; it does not write GPIO. Its `standby` field
is simulated state, not a sensed voltage. The current 132-test record establishes
its stated mock behavior, not actual fanout, VCC, current, polarity or disable.
The new PCB's GPIO25 RUN role is distinct from B1's GPIO25 direct-STBY role;
GPIO17 ARM and GPIO27 heartbeat are new design assignments, not discovered wires.

## Expected as-built wire record — existing Board A

These tables define the **fields expected in an evidence-backed wire record**,
not instructions to connect hardware. “Expected role” follows the confirmed
channel assignment only. Terminal names are functional names; exact module
silkscreen, header order, jumpers and duplicate terminals remain to be identified.
`AO1/AO2/BO1/BO2` use the letter O; the baseline README's `A01/A02/B01/B02`
spellings do not prove physical module markings. Every **Actual wire endpoint**
and **Evidence ID** cell is intentionally blank because no endpoint evidence
has been supplied. A blank cell does not mean the terminal is unconnected.

| Board A terminal/function | Expected role / unresolved source | Actual wire endpoint, including BCM + physical Pi pin where applicable | Evidence ID |
|---|---|---|---|
| VM | Earlier common-feed report now needs two-pack reconciliation; actual source/branch/protection unknown | | |
| VCC | Existing logic-supply source and voltage unknown | | |
| GND / all return terminals | Last report is common Pi/battery/driver ground; complete two-pack ground graph unknown | | |
| PWMA | Front-left channel PWM; actual GPIO/fanout unknown | | |
| AIN1 | Front-left direction 1; actual GPIO/fanout unknown | | |
| AIN2 | Front-left direction 2; actual GPIO/fanout unknown | | |
| PWMB | Front-right channel PWM; actual GPIO/fanout unknown | | |
| BIN1 | Front-right direction 1; actual GPIO/fanout unknown | | |
| BIN2 | Front-right direction 2; actual GPIO/fanout unknown | | |
| STBY | Enable source, possible strap/jumper and sharing unknown | | |
| AO1 | Front-left motor, one terminal; lead identity/polarity unknown | | |
| AO2 | Front-left motor, other terminal; lead identity/polarity unknown | | |
| BO1 | Front-right motor, one terminal; lead identity/polarity unknown | | |
| BO2 | Front-right motor, other terminal; lead identity/polarity unknown | | |

## Expected as-built wire record — existing Board B

Do not copy Board A's GPIO numbers into Board B merely because the reference
PCB uses shared inputs. The original source does not identify either board.

| Board B terminal/function | Expected role / unresolved source | Actual wire endpoint, including BCM + physical Pi pin where applicable | Evidence ID |
|---|---|---|---|
| VM | Earlier common-feed report now needs two-pack reconciliation; actual source/branch/protection unknown | | |
| VCC | Existing logic-supply source and voltage unknown | | |
| GND / all return terminals | Last report is common Pi/battery/driver ground; complete two-pack ground graph unknown | | |
| PWMA | Back-left channel PWM; actual GPIO/fanout unknown | | |
| AIN1 | Back-left direction 1; actual GPIO/fanout unknown | | |
| AIN2 | Back-left direction 2; actual GPIO/fanout unknown | | |
| PWMB | Back-right channel PWM; actual GPIO/fanout unknown | | |
| BIN1 | Back-right direction 1; actual GPIO/fanout unknown | | |
| BIN2 | Back-right direction 2; actual GPIO/fanout unknown | | |
| STBY | Enable source, possible strap/jumper and sharing unknown | | |
| AO1 | Back-left motor, one terminal; lead identity/polarity unknown | | |
| AO2 | Back-left motor, other terminal; lead identity/polarity unknown | | |
| BO1 | Back-right motor, one terminal; lead identity/polarity unknown | | |
| BO2 | Back-right motor, other terminal; lead identity/polarity unknown | | |

An eventual evidence record must identify shared splices and straps explicitly,
rather than just listing identical GPIO numbers. Board and terminal photographs,
an existing labeled as-built drawing/wire list, module manufacturer documents
and existing measurement records are possible evidence sources; none is
invented or implied by this blank template.

## Evidence needed for a compatibility conclusion

A document-based compatibility assessment would require the following evidence
to agree with one another and with the current reference design:

- Exact motor identification tied to the purchased 12 V/30:1 encoder units,
  with applicable running, startup, stall/reversal and duty ratings for all four
  motors; candidate MG513P30_12V data cannot be substituted for identification. Existing
  controlled records, where available, need voltage/load/duration context.
- Identified battery/source and protection parts for the two purchased packs,
  a resolved installed connection graph, full voltage/current/fault limits,
  protection-board behavior and returned-energy handling. Evidence must address the
  reference design's source-limited inrush and overload/energy restrictions;
  a “12 V” pack listing and advertised output-current figures alone cannot
  establish those properties.
- A complete as-built endpoint record for both driver modules, including exact
  VCC origin, common-return branches, GPIO fanout/straps and motor lead identity,
  tied to the identified module revision and Pi header numbering.
- The actual deployed software/version and GPIO provider/pin configuration,
  including any other GPIO users. A repository import name or mock configuration
  is not a target-system inventory.
- If encoder integration is required, exact encoder pinout, supply and output
  electrical levels, and the meaning of the listed 500-line count and 30:1 ratio
  are required. Purchased encoder hardware alone is not a defined interface.
- Evidence of the actual Pi power budget and existing rail-sequence/partial-power
  behavior, or an explicit design change with reviewed limits. Existing evidence
  cannot be assumed to satisfy the new ARM/RUN/heartbeat contract.

The current direct 12 V-source connection is outside Rev A's input range; it
requires a separately reviewed design decision, as recorded in
[12v_design_impact.md](12v_design_impact.md). The additional evidence above could
support a **conditional compatibility review of a revised design or explicitly
qualified lower-voltage operating case**,
not a claim of fabricated-PCB integration, measured thermal performance or safe
mechanical stopping. Unknown or conflicting evidence requires a specific
unresolved finding or design revision, rather than filling in the proposed
values as actual facts. No new physical-test procedure or operation is requested
by this audit. Fabrication remains **DEFERRED / NOT BUILT**, assembly
**DEFERRED / NOT ASSEMBLED**, physical validation and PCB integration **NOT TESTED**.

## Reproducibility fingerprints

Baseline is fixed at `034882cb2ce8106982508cf1a8309b4fa69673ff`. Current hashes
identify the files read for this audit, not files observed on the user's Pi.

| File snapshot | SHA-256 |
|---|---|
| Baseline `pi_robot/web_motor.py` | `eb13aa85467ae59afce18b19635e6b0d1b750e8c7e2535095b1abce9f19e6940` |
| Baseline `README.md` | `862cced26575cfa951d6c1795447a16fe50b5f24876d39c1dd4dbbadff1062f1` |
| Baseline `pi_robot/README.md` | `0a6229cfcd2b74ef6a9c41b7976bb22fc6ca477820bcd42b82d3385b2dbb9ddf` |
| Current `pi_robot/motor_config.py` | `7274bf962b66e81c2965942f8df13f6ef1c6d8b3602aa8729f8ec3f1200d301d` |
| Current `pi_robot/motor_backend.py` | `1d5274c5e985f1d19c0e922848d6be671ec0e82888a3c473f70f3eda81adcb30` |
| Current `pi_robot/web_motor.py` | `9449f031a1c6e31120aca26e92293a9eeae8cc3e6fbfd4e036128ebd1318b10b` |
