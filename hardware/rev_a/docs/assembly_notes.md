# Assembly and inspection notes — 12 V redesign

**DRAFT — NOT RELEASED FOR FABRICATION.** Fabrication: **DEFERRED**. Assembly: **NOT ASSEMBLED**. Physical validation: **NOT TESTED**. Updated 2026-09-28 for the provisional 12 V redesign; the former 6 V files are preserved in `hardware/rev_a_6v_archive`.

These are requirements for a later authorized assembly phase, not records of completed work. Use the native PCB/Fab layers, current per-reference BOM, [footprint review](footprint_review.md), [power circuit](power_circuit_spec.md), [driver review](driver_margin_review.md) and [enable interface](enable_interface_spec.md) together.

## Part identity and orientation

| References | Required inspection |
| --- | --- |
| U20–U23 | **DRV8874PWPR**, PWP16. Pin 1 and all 16 lead pads must match; exposed pad 17 is GND. U20/U21/U22/U23 feed FL/FR/BL/BR respectively. Inspect the four separate bridges; outputs are never paralleled. |
| U13 | **TPS26630RGER**, RGE24; exposed pad 25 GND. Pins1/2 are the shared IN terminals and 17/18 shared OUT. MODE is deliberately floating; physical NC terminals remain unsoldered to unrelated nets. |
| Q1 | **CSD19537Q3**: pins 1–3 sources/FUSED_IN; pin 4 gate; pins 5–8 and the large exposed drain land **EFUSE_IN**. Do not use a generic grounded exposed-pad assumption. |
| Q2 | **BSS138**: pin 1 gate, pin 2 source/FUSED_IN, pin 3 drain/B_GATE. It replaces the old NPN; do not populate an MMBT3904. |
| U3,U6,U16 | Distinct TSSOP14 logic: SN74LVC08A, SN74LVC11A and SN74LVC132A respectively. Similar packages do not imply interchangeable functions. |
| U4,U5 | TPS3431 DRB8 plus grounded pad 9; SN74LVC1G74 DCU8 with the custom TI_DCU0008A footprint. Verify exact package suffixes and fine-pitch joints. |
| U7–U9,U11,U12,U14,U15 | Distinct SOT packages/pin functions. U14 is a five-pin AND gate; U15 is a six-pin inverter. Populate by exact reference/MPN. U10 is absent from this redesign. |
| D1 | **SMBJ24CA**, bidirectional input TVS across FUSED_IN/GND; it is no longer a series reverse-polarity diode. Verify CA suffix. |
| D2 | **SMBJ18A**, unidirectional VM TVS: cathode/banded pad 1 to VM; anode/pad 2 to GND. Verify A suffix and orientation. |
| C1,C2 | **EEUFR1H102, 1000 µF /50 V**; positive pad 1 to VM, negative stripe/pad 2 GND. Nominal can D16×25 mm, pitch 7.5 mm; allow actual tolerance and installed stand-off. |
| C20,C25,C30,C35 | **EEUFR1H221, 220 µF /50 V**; one per driver, positive VM/pad 1. Nominal D10×16 mm, pitch 5 mm. |
| C22,C27,C32,C37 | 100 nF reservoirs connect VCP to VM. They must not be moved to VCP-to-GND. Flying capacitors C23/C28/C33/C38 connect CPH-to-CPL. |
| F1,R5 | Nonpolar **0451003.MRL 3 A** fuse and **680 Ω /2 W** bleed resistor. Neither is the old 2 A/330 Ω item. Do not substitute a PTC or assume a 3 A fuse regulates motor current. |
| SW1 | Pin2 common PHYS_RAW; pin 1 ENABLE via PHYS_SUPPLY; pin 3 INHIBIT/GND. Verify actuator direction from the drawing and continuity before relying on silk. |
| J1–J5 | Phoenix 1757242 headers. J1.1 motor source positive, J1.2 GND. J2–J5 each carry two switched motor outputs; neither wire is a ground return. Matching connector bodies can be misplugged. |
| J6 | Würth 61201621621 custom IDC16 logic interface. Check key/notch and contact1; it is not a Pi HAT or a direct 16-pin segment of the Pi header. Pins6/10 are reserved NC and pin 15 is GND. |

## Soldering process and inspection

All SMD parts are intended on the top side; radial capacitors, axial R5 and through-hole connectors follow a separately reviewed soldering process. Do not assume those through-hole parts tolerate the selected SMD reflow profile. Exact solder alloy, stencil thickness, paste reduction, atmosphere and thermal profile remain unapproved.

U13's four thermal holes and **every routed via hole intersecting a paste aperture must be filled, capped and planarized**. Use the exact [selective process coordinate map](../exports/draft/drills/selective_via_fill_map.csv) and [polygon-intersection report](../validation/design/selective_via_fill_review.json) for the matching native PCB hash. This requirement includes affected discrete-component pads; it is not restricted to thermal lands. Confirm the mapped features were processed and are planar/solderable before stencil printing. Ordinary tenting alone is not the specified process.

U20–U23 retain their sixteen tented holes outside paste. Follow [fabrication_notes.md](fabrication_notes.md); changing hole treatment is a design/process change, not a routine assembler substitution. Fill material, cap/plating, finish, planarity, stencil/profile compatibility and inspection acceptance need explicit later vendor qualification. Added process complexity and cost are unquoted, and no fabrication or assembly is authorized by this note. Inspect hidden QFN/thermal-pad joints using an appropriate process, including X-ray where needed, against later agreed void/coverage criteria. No numeric void acceptance criterion is invented here. Inspect Q1's fine source/gate gap, drain solder land, lead bridges, solder-wicking defects and unsoldered common terminals.

Renders use generic KiCad or project-authored nominal models. The three new TI body models simplify lead/underside details; the switch and fuse are also approximations. The new radial-capacitor models use nominal D16×25 and D10×16 dimensions; actual height/tolerance and installation clearance still need verification. A visibly plausible render does not establish solder joints, enclosure fit, insertion room or actual part orientation.

Do not fit purchased components to TP1–TP10 and TP20–TP23: they are copper probe pads. H1–H4 are non-plated mounting features, not four purchased standoffs. Cable plugs, wires, strain relief, mounting hardware and external isolation equipment require their own integration choices. SW1's low-current contact reliability remains an environmental qualification item.

## Deferred first power-up and shutdown

Use the current [bring-up procedure](../validation/bring_up.md) after assembly is separately authorized. Initially disconnect motors and the Pi harness; establish the defined logic rail using a reviewed bench arrangement, keep physical INHIBIT, and verify polarity/continuity. The old 0.10 A VM charging instruction is superseded: the new capacitor-only screen can reach 0.126 A and awake/bleed loads bring the conservative startup input screen to about **0.18 A**. Select a controlled bench limit that permits the intended ramp while remaining protective; the present procedure and protection review govern the exact steps. Do not raise a source limit merely to defeat an unexplained latch trip.

Drivers wake when FEED_ENABLE is valid, independently of ARM; blocked inputs coast until qualified motion permission. Physical INHIBIT sleeps the bridges and removes the input feed, but stored VM remains. For handling, stop mechanical input, disconnect the motor source, wait **at least 15 s and measure VM <0.3 V**. A live source or back-driven motor invalidates the discharge calculation. No assembly inspection, continuity measurement, powered test or thermal observation was performed in preparing these notes.
