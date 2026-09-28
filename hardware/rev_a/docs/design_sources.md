# Design sources and evidence limits

The 12 V redesign uses primary manufacturer documentation. Retrieved source details, equations and assumptions are in the [power review](power_path_review_12v.md), [driver review](driver_margin_review.md), [interface review](enable_interface_spec.md), [footprint review](footprint_review.md) and [BOM source registry](../validation/design/bom_source_registry.json). Sources establish component specifications, not the identity or performance of the installed robot.

| Source | Use |
|---|---|
| [Toshiba TB6612FNG datasheet](https://toshiba.semicon-storage.com/info/datasheet_en_20141001.pdf?did=10660), served 2026-05-13 | Rejected branch: distinguish operating/average output, absolute peak pulse and package thermal constraints. The older date in the URL is not the served revision. |
| [TI DRV8874 datasheet](https://www.ti.com/lit/ds/symlink/drv8874.pdf), SLVSF66A | Selected driver: voltage/current/thermal screening, IPROPI/VREF, PWM truth table, fixed-off regulation, wake nFAULT behavior and PWP0016J package. |
| [TI TPS2663 datasheet](https://www.ti.com/lit/ds/symlink/tps2663.pdf), SLVSE94G | TPS26630 eFuse, external reverse-block FET circuit, soft start and recovery, PGOOD, shutdown and RGE0024H pad pattern. |
| [TI CSD19537Q3](https://www.ti.com/lit/ds/symlink/csd19537q3.pdf) | Reverse-FET electrical and exact asymmetric Texas Q3 terminal/EP geometry. |
| [TI TPS3700](https://www.ti.com/lit/ds/symlink/tps3700.pdf) | VM window monitor and open-drain outputs. |
| [TI SN74LVC132A](https://www.ti.com/lit/ds/symlink/sn74lvc132a.pdf), [SN74LVC2G14](https://www.ti.com/lit/ds/symlink/sn74lvc2g14.pdf), [SN74LVC08A](https://www.ti.com/lit/ds/symlink/sn74lvc08a.pdf) | Schmitt decode and final AND command gating. The LVC132 input-transition requirement is retained despite the broader slow-input description. |
| [Littelfuse SMBJ series](https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet?assetguid=ba555e99-a12d-4f72-a0b6-86b06c67171e) | Standoff, breakdown, clamp conditions and pulse/temperature limits. TVS nominal standoff is not its clamp voltage. |
| [WHEELTEC MG513 family](https://www.wheeltec.net/product/html/?163.html) | Candidate MG513P30_12V rated/stall data only; the [source review](wheeltec_source_review.md) distinguishes the model's published data from purchase evidence. |
| [Raspberry Pi documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html), [RP1 peripherals](https://datasheets.raspberrypi.com/rp1/rp1-peripherals.pdf) | Pi 3.3 V interface and separate-supply context; installed PSU/provider and harness remain unknown. |
| [Würth 61201621621 drawing](https://www.we-online.com/components/products/datasheet/61201621621.pdf) | Custom 16-pin IDC footprint geometry; not a Pi HAT connector. |
| [KiCad 10 CLI manual](https://docs.kicad.org/10.0/en/cli/cli.html), actual 10.0.6 CLI help | Real native checks/exports and editable source parsing. |
| [Freerouting 2.4.1 release](https://github.com/freerouting/freerouting/releases/tag/v2.4.1) | Local routing candidates; final native KiCad results control the check verdict. |

The complete earlier 6 V source audit is in the [archive](../../rev_a_6v_archive/docs/design_sources.md). Those part choices are historical. Manufacturer PDFs are linked rather than redistributed. Project-local library/model files have separate [provenance and limits](../libraries/README.md). A nominal 3D mesh is not manufacturer mechanical certification.

Purchase records were supplied as a user transcription; receipts, unit labels and actual wiring were not physically inspected. No pack chemistry, cell count or maximum voltage is inferred from the 12 V listing. Stock, price, assembler acceptance, physical measurements and fabrication readiness are not established. The final packet must identify native check inputs and outputs by hash; the [check report](../validation/design/design_check_report.md) tracks current evidence and pending work.
