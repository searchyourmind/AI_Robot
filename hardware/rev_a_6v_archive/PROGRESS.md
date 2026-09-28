# Rev A design-only milestone — current checkpoint

## Purchase-record update — 2026-09-28

**6 V REFERENCE ONLY — DIRECT 12 V INPUT INCOMPATIBLE.** The latest purchase records describe two WHEELTEC R3 sets: four listed 12 V / 30:1 / 500-line GMR motors, two regulated TB6612 boards, two listed 12 V / 2500 mAh protected lithium packs, and a Pi 5 4 GB camera kit. These are user-reported purchase records, not inspected motor labels or physical measurements. They supersede earlier unknown-voltage/encoder-presence statements below.

The [impact review](docs/12v_design_impact.md) identifies D2 SMBJ7.0A, the nominal 7.16 V VM monitor and the lack of a step-down regulator as direct-input conflicts. The monitor/STBY path does not remove source power from the TVS. Exact MG513 identity, motor currents, pack min/nominal/max/topology, module regulator/VCC circuit, actual GPIO harness, Pi supply and switch/E-stop remain unresolved. Candidate MG513P30_12V ratings are conditional manufacturer evidence only.

Updated files: hardware evidence/requirements, wiring and decision guides, current README/export/release notices, project development notes, revision log, source and 12 V impact reviews, and purchase-update integrity records. Native schematic/PCB, BOM and CAD-derived exports remain the existing 6 V design. No 12 V redesign, real backend or encoder interface is claimed. Previous ERC/DRC and 132-mock-test evidence remain historical checks for their original inputs. Documentation links, preserved-file hashes and archive readback are checked in [purchase-update verification](validation/design/purchase_update_verification.json); CAD/software tests are not rerun for this documentation-only update.

Fabrication: **DEFERRED / NOT BUILT**. Assembly: **DEFERRED / NOT ASSEMBLED**. Physical validation: **NOT TESTED**. Integration: **NOT TESTED**. No vendor contact, order, push, publication or live actuation. The next design step is an actual-hardware specification and 12 V architecture decision after the remaining electrical inputs are resolved. Earlier checkpoints below are retained as history.

---

**AI Robot — Four-Motor PCB Design, Pre-Fabrication.** Local work based on commit `034882cb2ce8106982508cf1a8309b4fa69673ff`; no commit, push or publication was performed in this phase.

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
**DRAFT — NOT RELEASED FOR FABRICATION.**

The user accepted the bounded 6 V / 0.25 A RMS per motor reference assumptions. Circuit and routed PCB design for that reference, with the explicit derived supply/energy/sequence restrictions, are complete as a design-only milestone. Compatibility with the existing motors, battery, harness and chassis remains unverified. Historical “KiCad unavailable / native CAD not created” entries below are superseded by this checkpoint.

Files delivered: native KiCad 10 project, five schematic sheets, 100 × 80 mm two-layer PCB, local symbols/footprints/models, pin and channel maps, 97-component/33-MPN candidate BOM, power/thermal/routing and enable-circuit reviews, PDFs, top/bottom layout images, actual KiCad 3D render, and draft Gerber/drill/placement files. See the [design index](README.md) and [draft package](exports/draft/README.md).

Checks actually performed: native schematic ERC; PCB DRC with schematic parity and all severities; full numbered-pad/net/footprint comparison; source/geometry review; BOM/placement reconciliation; export/PDF/image QA and file hashing. Final native results: **0 ERC violations; 0 DRC violations; 0 unconnected items; 0 schematic parity issues**. [The check report](validation/design/design_check_report.md) records scope, tool versions, exceptions and limitations. ERC omits SPICE-model issues because no simulation is performed; no DRC class is ignored and no marker exclusion hides a finding.

The prior 132 mock-test report and JUnit file remain byte-for-byte unchanged. They provide software-only evidence. No extra software tests or unrelated features were added during this CAD completion phase.

Remaining assumptions: actual motor/stall ratings, battery/source/protection and returned energy, real GPIO harness/polarity, mechanical fit, instrument and assembly/vendor choices. Abrupt loss of Pi logic while charged VM remains outside the verified reference sequence. The proposed hardware RUN/ARM/heartbeat protocol has not been integrated into a physical GPIO backend. These prevent a verified replacement or fabrication release; they do not require physical work to complete this design-only milestone.

Fabrication: **DEFERRED / NOT BUILT**. Assembly: **DEFERRED / NOT ASSEMBLED**. Physical validation: **NOT TESTED**. Integration with the proposed PCB: **NOT TESTED**. Blank records and procedures are retained. Nothing was ordered or sent to a vendor.

A future session should first obtain the actual motor/source/wiring/mechanical data and compare them with `docs/reference_electrical_spec.md`, then revise the design or conduct a separate release review. Do not infer real-hardware suitability from clean CAD checks.

---

# Historical progress record

Session began 2026-09-27 America/New_York; continued 2026-09-28. Baseline `034882cb2ce8106982508cf1a8309b4fa69673ff`. Work is local, uncommitted, and not deployed. No push, purchases, fabrication release or live actuation authorized/performed.

## Current stage

- Existing repository and all tracked source/README/requirements files audited.
- Four geared motors/two drivers and exact driver-channel-to-wheel map are user-confirmed; direct Pi 5 GPIO, no Arduino in loop, separate Pi supply/common ground are confirmed. Actual GPIO fanout, polarity and ratings remain TBD.
- Requirements, conditional architecture, source checks, calculations and blank validation package drafted.
- Mock-first software safety changes complete for this stage. Final combined offline suite: 132 passed, exit 0; compileall and diff checks passed. Evidence: `validation/software_test_report.md` and `validation/mock_tests.junit.xml`.
- Native CAD: NOT CREATED. KiCad not found in inspected locations; architecture/electrical review and dimensions also pending.
- Fabricated: NO EVIDENCE. Assembled: NO EVIDENCE. Physically tested: NOT TESTED.

## Resume sequence

1. Read `docs/existing_system_audit.md`, `docs/requirements.md`, `docs/architecture_review.md` and latest test report; inspect `git status` and preserve all uncommitted work.
2. Obtain the single outstanding hardware information batch recorded in requirements. No need to reconfirm motor/driver counts.
3. Conduct the requested architecture/electrical review using confirmed direct Pi/channel mapping and unresolved GPIO fanout, A/B logic, IC current/thermal suitability, supply/protection/disable, outline and assembly route. Record reviewer/date and conclusions before schematic/layout freeze.
4. Resolve KiCad version and selected assembler rules; follow `docs/cad_workflow.md`. Keep drafts separate from `manufacturing/release/`.
5. Add a real backend only after wiring/provider/timing and disable behavior are verified; preserve the mock suite and expand with measured acceptance criteria.
6. Stop before purchases, fabrication release, deployment or live actuation until explicit user approval.

## Review request status

The user has been asked for motor/source/wiring/mechanical/assembly/instrument details in one batch. Response received 2026-09-28 and incorporated in requirements/pin map; electrical ratings, exact GPIO fanout and mechanical/assembly inputs remain TBD. One architecture/electrical pre-review request has been sent for the conditional direct-IC, paired-logic, independently disabled/timed design. Response is pending; this is not schematic freeze or manufacturing authorization. Electrical ratings must still be supplied and reviewed. Elapsed time is not approval. Continue independent source/mock/documentation work only.

## Important limits

Neither passing mock tests nor ERC/DRC would establish physical electrical safety. Motor ratings, Pi GPIO provider and exact GPIO fanout/polarity remain unknown; direct Pi control is user-confirmed. AI is advisory with stop-only authority. Software timeout cannot guarantee motor disable during OS/process/peripheral failure. Physical record measurements remain blank.

## Session close-out

Files changed: the four existing robot scripts and both README files; new motor configuration/backend/state machine and pure vision validator; hardware requirements/audit/source/circuit/calculation/CAD-workflow/risk documents; draft candidate BOM; validation plans/blank records/test reports; offline mock tests and project development notes. See `validation/changed_files.txt` for the exact list.

Checks actually run: baseline pure-parser reproduction; 132 combined mock tests (70 motor, 58 vision/clients, 4 cross-service); Python compilation; git whitespace check; document links; candidate BOM and 17 blank physical records. No physical devices, live model calls, browser execution, CAD checks or manufacturing outputs.

Risks still open: motor/current/source/protection ratings, exact GPIO/VCC wiring and polarity, GPIO provider/timing, sensor exposure age, physical disable/watchdog circuit, mechanical/assembly limits and absent KiCad/native design.

Next specific decision: review the conditional paired-left/right direct-IC architecture and collect exact motor/source specifications plus both boards' control-pin wires. Do not freeze the driver/protection or layout while these remain TBD.

## Current stage — design-only scope update, 2026-09-28

This appended checkpoint supersedes the physical-completion requirement and the
prior session's resume priorities above. Earlier entries and the actual
132-case test report are preserved as history, not rewritten as new evidence.
The current milestone is **AI Robot — Four-Motor PCB Design, Pre-Fabrication**.
Authoritative scope: [scope_design_only.md](docs/scope_design_only.md).

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.** The user
has authorized continuation of circuit and PCB work under visible assumptions,
not silent substitution of proposed numbers for real motor/battery ratings.
Requirements and reviewable assumptions now appear in
[requirements_assumptions.md](docs/requirements_assumptions.md).

Current checkpoint:

- The four-motor/two-driver count, direct Pi 5 control, no Arduino in the loop,
  driver-channel-to-wheel positions, separate Pi supply and common ground remain
  user-confirmed. Do not request these again.
- Minimum real-system electrical gaps: motor voltage/running/startup/stall
  envelopes; battery voltage/protection/returned-energy bounds; exact GPIO
  fanout, motor polarity and VCC/power sequencing.
- A bounded reference supply/load/logic/ambient specification is proposed for
  review. Provisional mechanics and fabrication rules are assumptions; vendor
  selection and assembly arrangements are deferred.
- Native CAD completion remains pending actual permitted KiCad setup, circuit
  review, native design work and recorded checks. Tool installation is being
  evaluated in the task workspace; this checkpoint does not claim installation,
  a schematic/PCB opening, ERC/DRC, connectivity checks, exports or 3D rendering
  succeeded. The main design work will append its actual outcomes.
- Existing software is unchanged for this scope-only checkpoint. No new tests
  were added or run. Historical evidence remains **132 mock cases passed** in
  `validation/software_test_report.md` and `validation/mock_tests.junit.xml`;
  this is not PCB, physical disable or robot validation.
- Fabrication: **DEFERRED / NOT BUILT**. Assembly: **DEFERRED / NOT ASSEMBLED**.
  Physical validation: **NOT TESTED**. Integration with the proposed PCB:
  **NOT TESTED**. Keep physical procedures and measurement templates blank.

Files changed at this scope checkpoint: `docs/scope_design_only.md`,
`docs/requirements_assumptions.md`, this progress record, and
`../../docs/project_development.md`. No existing software, tests,
132-case reports, or historical progress entries were rewritten for this scope
update.

Checks performed: read the latest scope instruction, previous hardware answers,
requirements/mapping/architecture/electrical worksheets, project development notes and
actual software report; verified the report/JUnit file SHA-256 fingerprints
before and after the documentation edits. These are documentation-integrity
checks, not electrical, CAD, fabrication or physical tests.

Historical report fingerprints retained:

- `validation/software_test_report.md`: `ba52e1a29b1bbdef4f2432df6b0ea7b43c350fd1529ff60e16fccd07312ffaf3`
- `validation/mock_tests.junit.xml`: `db5a70a947769df63656d36b0bc726911738cb661d2122e831d8d5e0c567b473`

Next specific decision: accept/correct the bounded reference electrical
specification, or supply the real motor/source/wire details needed to replace
its assumptions. In parallel, establish the permitted, version-identified KiCad
execution path and continue unblocked draft circuit/layout work. Record actual
results before updating design-completion claims. Draft manufacturing exports,
if later generated, remain **DRAFT — NOT RELEASED FOR FABRICATION** under
`exports/draft/`; no order, vendor contact, physical work, push or publication.

### Reference-scope acceptance update — 2026-09-28

The user has now explicitly accepted the principal reference bounds: 6.0 V nominal,
5.5–6.5 V raw motor input; 0.25 A RMS and 0.60 A peak per motor with peaks at most
20 ms/10% duty; ambient at most 40 C; separate Pi supply with 3.3 V logic; and a
100 × 80 mm two-layer, 1 oz reference board. These are **ACCEPTED REFERENCE
ASSUMPTIONS**, not confirmed real-robot motor/battery/wiring ratings. Do not ask
the user to accept them again. The table records derived limits and still-open
details separately. Electrical suitability and actual CAD/check outcomes remain
pending; the work remains **PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE
EXISTING ROBOT**.

KiCad execution path: the main task is downloading the official KiCad 10.0.6 DMG
into the task workspace for local use, without a global installation. Download,
extraction, CLI execution, CAD creation and checks must each be reported from
actual results; no completion is asserted here. Next action is to continue the
circuit/net/pin review and native schematic/layout under the accepted bounds,
resolve the remaining protection/energy/sequence assumptions, and append the
actual tool/check results. All four physical-work statuses above are unchanged.

## Follow-up: hardware evidence and design explanation — 2026-09-28

The user requested actual-hardware matching, wiring diagrams, explanations of eleven design decisions and a critical account of the 97-part BOM. Added `docs/actual_hardware_evidence.md`, `docs/wiring_guide.md`, `docs/design_decisions.md`, and `docs/component_count_review.md`, with machine-readable part-count evidence. Existing and proposed wiring are explicitly separate. Current native pin/net records and baseline/current code were read without operating hardware. A single consolidated request asks only for missing motor/source/module/GPIO/VCC/protection information; no real hardware facts were invented while it is pending.

Key findings: the original code has one logical A/B pin set, which does not establish two-module fanout; Rev A pairing is hardwired; SW1 clears permission but does not cut VM; 62 of 97 fitted components belong to conditioning and supervision, so a minimum-component implementation has not been established. Simplification candidates are documented without deleting circuitry or retaining unsupported fault-coverage claims.

Native CAD, BOM, all manufacturing exports, previous ERC/DRC inputs/results and the 132-case mock reports remain unchanged. No CAD rerun or new software test was necessary for these explanation-only additions; preservation was checked by SHA-256 against the preceding artifact manifest. Local document links and the BOM reference partition were checked. Documentation/package hashes were refreshed separately from historical design evidence. Actual robot compatibility remains UNKNOWN, and physical validation/integration remain NOT TESTED. No vendor contact, order, deployment, push or actuation occurred.
