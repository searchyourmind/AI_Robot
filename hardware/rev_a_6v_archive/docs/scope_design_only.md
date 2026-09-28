# AI Robot — Four-Motor PCB Design, Pre-Fabrication

Scope update: **2026-09-28, DESIGN-ONLY MILESTONE**. This document records the
user's latest instruction and supersedes the earlier requirement to fabricate,
assemble, and bring up the proposed PCB before completing this phase. It extends
the existing AI_Robot repository; the audited software, prior documentation,
original Git history, and actual 132-case mock-test evidence remain in place.

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.** This
label remains necessary because compatibility with the actual robot is
unverified. The user accepted the principal bounded reference specification on
2026-09-28; electrical suitability and native design checks remain pending. A reference specification is not a substitute for the
real motors, battery, GPIO wiring, or power-sequencing information.

## Work authorized in this phase

The target is a reviewable, editable circuit and PCB for the stated specification:
two conditionally suitable TB6612FNG ICs, four electrically separate motor
outputs, the confirmed direct Pi 5 control path, separate existing Pi supply,
defined logic interface, input protection, decoupling, default disable, physical
disable provision, useful test points, connector labels, and documented returns.
Paired left/right commands may share logic inputs after review; H-bridge outputs
must not be joined. No new MCU, charging circuit, custom Pi supply, or speculative
sensor interface is added without a recorded requirement.

Priority is actual schematic and PCB work. Existing software/test results are
retained; raising the test count or adding unrelated software is not a milestone
objective. Software timeouts and a proposed hardware timeout have different
failure modes and evidence. Passing a mock test does not validate a physical
motor-disable mechanism, a PCB, or the real robot.

KiCad may be installed only through an environment-permitted path without
unauthorized system changes. Inspect the actual version and supported commands,
use native formats and version-matched documentation, and record actual results.
Tool setup, CAD opening, ERC, DRC, connectivity checks, exports, and 3D rendering
must never be inferred from the existence of a file. If tool operation fails,
record the exact blocker and keep the corresponding completion state BLOCKED.

## Boundary of completion

| Deliverable | Evidence needed for a completed design-only claim |
|---|---|
| Requirements and assumptions | Parameter/value/source/status/consequence table; accepted specification and explicit remaining real-robot compatibility limits |
| Circuit and component selection | Complete native schematic; primary datasheet references; electrical/thermal/protection review; verified symbol-to-footprint/pad mapping |
| PCB | Native project and routed PCB; outline/mounting assumptions; placement, copper returns, labeling, and connector-access review |
| Design checks | Actual tool/version/command/exit-status records; ERC, DRC and connectivity results; resolved or explicitly reviewed findings |
| Visual review | Actual schematic PDF, top/bottom layout views, and KiCad-generated 3D render clearly labeled as a render; checked readability/orientation |
| BOM and draft outputs | Real candidate MPNs; design-consistent BOM, placement data, draft Gerbers/drills and fabrication/assembly notes where supported |
| Repository presentation | Accurate current-state descriptions, links only to existing evidence, limitations and ownership record |
| Deferred validation | Preserved staged procedures and blank records; no invented measurements or PASS results |

An electrically reviewed reference design can finish this phase without being
verified as a replacement for the existing robot. If the circuit/layout or actual
checks are incomplete, report that incomplete state rather than calling the
whole design-only phase complete. ERC/DRC checks are not evidence of electrical
safety or physical operation.

## Draft-only manufacturing boundary

All generated manufacturing candidates belong under `hardware/rev_a/exports/draft/`
and must carry **DRAFT — NOT RELEASED FOR FABRICATION**. Nothing from this phase
is released into `manufacturing/release/`. Manufacturer selection and assembly
arrangements may remain deferred; provisional stackup/design-rule assumptions
must not be represented as manufacturer acceptance.

No PCB order, quotation request, vendor contact, purchase, soldering, physical
board test, live actuation, deployment, push, or publication is authorized by this
scope update. Existing breakout-board robot footage is not evidence that the
proposed custom PCB works. Empty image files and placeholder CAD are not evidence.

## Physical work is deferred

| Activity | Required status |
|---|---|
| Fabrication | **DEFERRED / NOT BUILT** |
| Assembly | **DEFERRED / NOT ASSEMBLED** |
| Physical validation | **NOT TESTED** |
| Integration with the proposed PCB | **NOT TESTED** |

Keep the existing bring-up procedure and blank test records for a later separately
authorized phase. Do not populate instrument readings, dates, photographs,
oscilloscope captures, physical fault recovery, or Rev B improvements without
actual evidence.

## Current handoff and decision gate

At this scope-document checkpoint, the prior 132-case software report remains
historical evidence; it has not been rerun or expanded for this scope change.
The user accepted the principal reference electrical/mechanical envelope on
2026-09-28. The main design work is obtaining the official KiCad 10.0.6 DMG into
the task workspace for a local execution path, without a global installation.
Native CAD/tool operation and electrical suitability review remain in progress. No new tool/check/render success is claimed by this document.
The current design checkpoint and later actual CAD results belong in
[the progress record](../PROGRESS.md).

Review the bounded proposal in [requirements_assumptions.md](requirements_assumptions.md).
The minimum unanswered real-robot inputs are motor voltage/current envelope,
source voltage/protection bounds, actual GPIO fanout and motor polarity, and
VCC/power sequencing. The direct Pi controller path and driver-to-wheel mapping
have already been confirmed and must not be requested again. Draft schematic and
layout work may proceed under the accepted reference envelope; remaining detailed
assumptions stay visible until checked. Do not ask the user to reconfirm the
already accepted envelope. No schematic/layout freeze or compatibility claim
follows merely from elapsed time.
