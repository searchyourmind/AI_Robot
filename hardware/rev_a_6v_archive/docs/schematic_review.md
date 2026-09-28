# Native schematic review — Rev A reference design

**PROVISIONAL REFERENCE DESIGN — NOT VERIFIED FOR THE EXISTING ROBOT.**
**DRAFT — NOT RELEASED FOR FABRICATION.** Review date: 2026-09-28.

The native project contains all 107 reviewed electrical parts on five A3 sheets:
Power (23), Interface (27), Safety (28), Latch (13) and Drivers (16). These counts
include ten copper test points and exclude the PCB-only mounting holes.
TP1–TP10 remain on-board copper features but have `in_bom no` in both the
project library and placed instances, so they are not purchased BOM items. The root
is [`ai_robot_interface.kicad_sch`](../ai_robot_interface.kicad_sch); its four
child sheets, project-local symbol library and library table are included.

Every custom symbol has the physical pin numbers, electrical types and MPN from
the reviewed circuit manifest. The symbols are pin-exact schematic blocks;
rectangular IC/transistor/diode blocks are not behavioral simulation models.
D1/D2 explicitly display cathode K/anode A and pin numbers. Polarized capacitors
show the positive terminal. No-connect markers explicitly mark U5 pin 3 and
U10 pin 1. Global labels provide the intersheet nets. Each physical package pin,
including the duplicate TB6612 terminals, is represented separately. J6 pin 15
is GND; STBY is not connected to a Pi GPIO and can be probed at TP10.

Four power-output flags mark MOTOR_IN, PI_3V3, GND and the conditionally supplied
VM rail. These encode the external-source / switched-source connectivity
assumption for ERC. They do not prove rail voltage, source impedance, power
sequencing or immunity to abrupt Pi power loss. Refer to the
[power circuit review](power_circuit_spec.md) and
[reference operating constraints](reference_electrical_spec.md).

## Checks performed on the saved native files

The task-local official **KiCad 10.0.6** CLI read the files and produced the actual
reports below. The validation directory preserves the exact manifest and symbol
paths used in the comparison, along with source/evidence SHA-256 fingerprints.

| Check | Actual result | Evidence / limitation |
|---|---|---|
| Native ERC, all severities and violation exit status enabled | Exit 0; **zero violations** on all five sheets | [schematic_erc.json](../validation/design/schematic_erc.json); only `simulation_model_issue` remains ignored because no SPICE model is part of this scope |
| Native PDF export | Exit 0; five A3 pages | Native CLI PDF, rendered and visually inspected page by page; export packaging is recorded separately in the CAD workflow |
| Native KiCad XML netlist export | Exit 0 | [schematic_netlist.xml](../validation/design/schematic_netlist.xml), not a hand-written netlist |
| Full manifest-to-native-netlist comparison | **PASS**: 107 parts, 322 package pins, 60 connected nets and 2 isolated NC nets | [schematic_parity.json](../validation/design/schematic_parity.json); reference set, value, MPN, footprint, UUID, every pin number/type/net and whole-net membership matched |
| Visual readability/polarity | All five final PDF pages inspected | References, values, pin names/numbers, global labels, diode K/A, capacitor positive marks, J6 pin 15 GND and sheet/title blocks checked; no overlapping labels found at the inspected scale |
| Physical operation | **NOT TESTED** | ERC/netlist/PDF do not prove timing, supply thresholds, motor current/thermal behavior or real wiring |

Exact command forms, exit results, the runtime warning and fingerprints are in
[schematic_checks.json](../validation/design/schematic_checks.json). The normalized
comparison input is [schematic_manifest.json](../validation/design/schematic_manifest.json),
and [schematic_paths.json](../validation/design/schematic_paths.json) supplies stable
sheet and symbol UUID paths for PCB association. This report checks schematic
consistency, not complete schematic-to-PCB parity or board DRC; use the separate
board-validation records for those checks.

## Corrections and evidence limits

The first native ERC run reported 431 off-grid endpoint warnings. Component
centers and power-flag coordinates were corrected to the 1.27 mm connection
grid, and the final native run has none. Right-hand global-label justification
was corrected after visual inspection. The diode blocks originally hid their
K/A terminal names; the final symbols display both names and numbers. An early
proposal connected J6 pin 15 to STBY feedback; it was removed so a misconfigured
Pi output cannot fight the hardware disable sink through that connection.

Earlier default checks ignored single global labels, four-way junctions and
footprint filters; those check classes were enabled as warnings before the final
zero-violation run. No exclusion markers or electrical-connectivity waivers
were introduced. SPICE model checking remains out of scope and is disclosed in
the actual report. Native CLI commands emitted `Fontconfig error: Cannot load
default config file: File not found` but returned exit 0 and produced inspectable
PDF/netlist/JSON outputs; this warning is recorded rather than suppressed.

After native PCB parity review, all ten test-point BOM flags were corrected
and U4 received its manufacturer datasheet field in both library and placed
symbol. The native netlist explicitly confirms those metadata values. ERC,
netlist and PDF were regenerated; all five rendered PDF pages were byte-equal
to the previously visually inspected page images because the changes are
hidden metadata. Updated source/evidence fingerprints are recorded.

The historical software test evidence was not rerun or modified for this
milestone. It does not implement or validate the proposed physical ARM/RUN/
heartbeat interface. Fabrication remains **DEFERRED / NOT BUILT**; assembly
**DEFERRED / NOT ASSEMBLED**; physical validation and PCB integration **NOT TESTED**.
