# 3D model provenance and limits

Models copied from the KiCad 10.0.6 official library retain their package geometry. Custom VRML meshes are nominal visualizations for manufacturer package envelopes or parts without an available stock model, including the DRV8874PWP, TPS26630RGE, CSD19537Q3, fuse and slide switch. They are not manufacturer-certified mechanical CAD.

The new bulk capacitors use 50 V package footprints: C1/C2 diameter 16 mm, nominal height 25 mm, pitch 7.5 mm; C20/C25/C30/C35 diameter 10 mm, nominal height 16 mm, pitch 5 mm. Verify actual supplier drawings, lead forming, tolerance and installed height before any enclosure decision. The provisional 100×100 mm board has no verified chassis fit or height envelope.

KiCad resolves model paths via `${KIPRJMOD}/libraries/3dmodels/`. The export consistency record checks that fitted-component bindings exist. A successful render does not verify solder-pad geometry, thermal holes, collision clearance under worst tolerance, terminal access or physical assembly. Fabrication DEFERRED; assembly NOT ASSEMBLED; physical validation NOT TESTED.
