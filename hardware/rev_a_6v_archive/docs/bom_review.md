# Candidate BOM review

**6 V REFERENCE ONLY — DIRECT 12 V INPUT INCOMPATIBLE.** The 2026-09-28 purchase-record update establishes listed 12 V motors and packs. This document retains the existing 5.5–6.5 V design; its calculations, parts and checks have not been qualified for that system. See the [12 V impact review](12v_design_impact.md) and [current hardware evidence](actual_hardware_evidence.md).

**DRAFT — NOT RELEASED FOR FABRICATION.** This is the candidate bill for the bounded reference design, not a purchasing authorization or verified replacement for the existing robot. Fabrication and assembly are deferred.

The integrated component manifest produces [bom_reference.tsv](../exports/draft/bom_reference.tsv), grouped by manufacturer part number, footprint and value, and [bom_per_reference.tsv](../exports/draft/bom_per_reference.tsv), with one row per fitted part. There are **97 board components and 33 distinct MPNs** in this revision. The [machine check](../validation/bom_manifest_check.json) records the manifest SHA-256, reference-set equality, duplicate check and quantity check. Regenerate both TSV files and that report if the manifest changes.

TP1–TP10 are exposed PCB copper features, not purchased test-point components. H1–H4 are 3.2 mm non-plated mounting holes in the PCB, not purchased hardware. Neither is included in the board BOM. Standoffs, screws, motor leads, Pi interface cable, source and motors remain outside the assembled-PCB BOM; no complete harness or mounting kit is invented.

The [separate off-board candidate list](../exports/draft/bom_offboard_candidates.tsv) contains five Phoenix 1757019 mating plugs for J1–J5. It does not count them as board-mounted connectors and does not imply that cables are complete. J6 requires a separately specified keyed 16-way cable assembly with the exact project pin map. It must never be plugged directly into a Pi 40-pin header.

## Ordering and footprint consistency

| Item | Design decision / review boundary |
| --- | --- |
| U1/U2 | MPN is `TB6612FNG(O,C,8,EL`, exactly the current Toshiba orderable-example string, including its unusual open parenthesis. Toshiba notes that delivery suffixes/configurations may need confirmation. No inventory or complete-order-code acceptance is claimed. |
| U5 | `SN74LVC1G74DCUR` uses project footprint `AI_Robot:TI_DCU0008A`; a generic VSSOP body label is insufficient because the required pad span differs. |
| U4 | `TPS3431SDRBR` uses the local DRB8 footprint, including exposed pad 9 tied to GND. The watchdog timing option is part-specific. |
| U11 | `TPS3700DDCR` uses the DDC six-pin arrangement. Do not substitute the DSE package without remapping. This is the monitor called U3 in the initial power-only handoff; integrated references govern assembly. |
| C101–C109 | `CC0603KRX7R9BB104`, YAGEO, 100 nF/50 V/X7R/10%, 0603. These are not the superseded 0805 or other dielectric parts. C4/C6/C8/C10/C11 remain KEMET 0805. |
| C100 | `GRM1885C1H102JA01D`, 1 nF/C0G/50 V/5%, 0603. The reviewed sheet is manufacturer-authored but retrieved from an archive because direct manufacturer retrieval was unavailable. Refresh the current manufacturer record before any later procurement. |
| R1–R4/R6–R10 | Vishay TNPW0805, 0.1%,25 ppm/K; preserve precision at the VM divider. Do not substitute the ordinary 1% 0603 pull resistors. |
| R100–R141 | YAGEO RC0603, 1%, 0.1 W at 70 C, with distinct 330 ohm/1k/10k/100k values as listed. |
| R5 | Cu-lead PR02, 330 ohm/5%/2 W. The larger axial library body clearance is intentional. Lead forming and stand-off remain assembly-process decisions. |
| SW1 | C&K JS102011SAQN, non-shorting SPDT with silver contacts. This is a logic enable/inhibit switch, not a motor disconnect; minimum-load reliability is a documented physical-validation item. |
| F1 | Littelfuse 0451002.MRL. The native custom footprint uses 1.96×3.15 mm pads on 4.90 mm centers; the superseded 2.00 mm draft note has been removed from the manifest. |

No alternate parts are pre-approved. A substitution must preserve polarity, exact pin mapping, package and land pattern, electrical ranges, threshold/timing behavior, thermal requirements and power-off behavior. Distributor names, estimated prices, stock, minimum order quantity and assembler library numbers are intentionally absent because no purchasing or manufacturer-selection step occurred.

## Sources

Accessed 2026-09-28. The TSV Source_URL column supplies a source for each candidate; electrical source revisions are recorded in [power_circuit_spec.md](power_circuit_spec.md) and [enable_interface_spec.md](enable_interface_spec.md). Added integrated-BOM references are:

- [Toshiba TB6612 product page](https://toshiba.semicon-storage.com/eu/semiconductor/product/motor-driver-ics/brushed-dc-motor-driver-ics/detail.TB6612FNG.html), current Orderable part number and Notes sections.
- [YAGEO CC0603KRX7R9BB104](https://yageogroup.com/download/specsheet/CC0603KRX7R9BB104), generated 2026-05-08, p1.
- YAGEO exact-part sheets: [1k](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-071KL) and [100k](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-07100KL), generated 2026-09-27; [330 ohm](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-07330RL), generated 2026-09-28; [10k](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-0710KL), retrieved generated 2026-01-16. All p1 values/package/rating tables.
- [Würth 61201621621](https://www.we-online.com/components/products/datasheet/61201621621.pdf), revision 002.000,2022-08-30, mechanical/PCB drawing and pin1 orientation. The project header footprint is reviewed separately.
- [C&K JS series](https://www.ckswitches.com/media/1422/js.pdf), revision VL01/14/26, ordering options and JS102011SAQN drawing.

The BOM check establishes consistency with the design manifest. It does not establish solderability, physical operation, genuine supply-chain provenance, component availability or manufacturer acceptance.
