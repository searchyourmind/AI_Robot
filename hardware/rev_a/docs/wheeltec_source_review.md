# WHEELTEC primary-source review

Review date: **2026-09-28**. Public document review only; no inspection or measurement of the purchased hardware.

## Purchase record versus manufacturer evidence

The user reports purchasing two WHEELTEC R3 two-wheel chassis sets, each with two **12 V, 30:1, 500-line GMR encoder motors** and one **regulated dual-channel TB6612 board**: four motors and two modules total. These are user-provided purchase details. An exact purchase URL, motor marking and driver-board model/revision have not been supplied. **MG513P30_12V remains an unconfirmed candidate.** The current custom reference uses four DRV8874 drivers and a provisional 9–15 V source envelope; it is a separate implementation, still unverified for these purchased units.

The [WHEELTEC manufacturer homepage](https://www.wheeltec.net/) identifies the company and links its [official store](https://wheeltec.tmall.com/) and [forum](http://bbs.wheeltec.net/). The store and forum could not be inspected successfully with the available tools. No accessible manufacturer source was found tying this particular purchase to an exact motor or board revision.

## Verified motor-family information

The [official MG513 page](https://www.wheeltec.net/product/html/?163.html) shows both [GMR and Hall encoder variants](https://www.wheeltec.net/kindeditor/attached/image/202410/23/20241023091819_69548.jpg). Its [manufacturer parameter table](https://www.wheeltec.net/kindeditor/attached/image/202410/23/20241023091819_60412.jpg) lists the following for **MG513P30_12V**:

| Parameter | Candidate model's published value |
|---|---:|
| Rated voltage | 12 V |
| Rated current | 0.36 A |
| Stall current | 3.2 A |
| Speed after reduction, unloaded | 366 ± 26 rpm |
| Speed after reduction, rated | 293 ± 21 rpm |
| Rated / stall torque | 1 / 4.5 kg·cm |
| Power | Approximately 4 W |

These values are **not confirmed ratings of the purchased motors**. If this candidate is confirmed, its published rated and stall currents exceed the archived 6 V reference's 0.25 A RMS and 0.6 A peak bounds. That historical comparison motivated redesign; the [6 V archive](../../rev_a_6v_archive/README.md) remains unqualified for direct 12 V input.

The current four-DRV8874 reference instead selects approximately **0.791 A nominal current regulation per motor** (0.708–0.888 A static screen) and a **2.980 A nominal aggregate eFuse limit**. The candidate's 0.36 A rated current is below that channel setting, but its 3.2 A stall figure is well above it. Current regulation will alter startup and stall torque; simultaneous startup can trip the aggregate protection. These comparisons do not establish dynamic peak control, successful starting, continuous thermal suitability or actual-robot compatibility. See the [driver margin review](driver_margin_review.md) and [reference electrical specification](reference_electrical_spec.md). The two purchased packs' maximum voltage, installed topology and BMS behavior remain unknown; “12 V” does not establish 3S chemistry or a 12.6 V full-charge maximum.

## Encoder convention and signal voltage

The separate [MG513X/MG513XL family page](https://www.wheeltec.net/product/html/?223.html) has a [motor table specifying 1:28 reduction](https://www.wheeltec.net/kindeditor/attached/image/20251121/20251121160211_37337.jpg); it is not the reported 30:1 configuration. Its [encoder table](https://www.wheeltec.net/kindeditor/attached/image/20251121/20251121160212_30101.jpg) explicitly labels GMR as **500ppr**, Hall as **13ppr**, and encoder supply as **3.3–5 V**. It also states that encoder outputs have pull-ups to encoder VCC.

This establishes terminology for that documented family, but not the purchased motor's count convention. The table does not explicitly resolve motor-shaft versus gearbox-output-shaft reference or the decoded-edge convention. Do not record **500 PPR, 2,000 decoded counts per revolution, or 60,000 counts per wheel revolution** as verified configuration. Confirm the exact encoder and counting method first. The documented pull-ups also mean that a 5 V encoder supply must not be assumed to produce Pi-compatible 3.3 V signals; the actual unit's output circuit and interface require verification.

## Regulated TB6612 module: unresolved

No exact manufacturer schematic or manual for the purchased regulated dual-channel TB6612 module was verified. Its regulator topology, output rails and capacities, motor-supply routing, TB6612 logic supply, encoder supply, and STBY accessibility remain unknown. **“Regulated” does not establish that a 12 V motor supply is reduced to 6 V**, or that the module can supply a Raspberry Pi 5. Reseller rail/current claims and anonymous technical blogs were not used as primary conclusions.

The next evidence needed is the purchase specification and readable motor/board markings, followed by the matching manufacturer's wiring diagram or schematic. Source values above must remain conditional until that identity match is established.
