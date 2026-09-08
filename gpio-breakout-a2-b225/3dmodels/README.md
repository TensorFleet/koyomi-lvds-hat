# Model provenance

- `Molex_1054500101_official.stp`: unmodified Molex manufacturer STEP supplied
  with the USB-C part drawing. SHA-256 and fitted feet/shell/mouth evidence are
  in `../reports/usb2-model-audit.json`.
- `ZF5S-40-01-nominal-envelope.wrl`: existing conservative Samtec envelope;
  not vendor CAD and not proof of mating, latch or cable clearance.
- `standard/*.step`: unmodified KiCad standard 3D library models for SC-70-6,
  DRT-3 and 0603 passive bodies. Exact source-library names and file hashes are
  in `../reports/usb2-standard-models.json`. These are visualizations, not
  manufacturer metrology. KiCad libraries are distributed under CC BY-SA4.0
  with the KiCad libraries exception; see https://www.kicad.org/libraries/license/.

Native top/USB-side views show the saved model placements. J3 has only0.05mm
mouth overhang; the separate enclosure/plug-shroud fit still needs review.
