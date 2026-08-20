# Koyomi RGB compact R2.7 production verification

Date: 2026-08-20

## Mechanical result

- Source revision: R2.6 production candidate.
- R2.6 outline: 65.0 × 28.25 mm = 1836.25 mm².
- R2.7 base rectangle: 58.0 × 22.2 mm = 1287.6 mm².
- JFFC1 support tab: 20.0 × 0.5 mm = 10.0 mm².
- Actual R2.7 area: 1297.6 mm²; area reduction: 29.33%.
- Fitted parts: 23 front, 0 back.
- Mechanical/configuration footprints: H1–H4 and JP1–JP2 remain front-side
  bare features and are excluded from the fitted count.

## Edge connector orientation and interface

- Hirose's FH41 drawing places the cable opening opposite the 40 signal solder
  pads. At `JFFC1` rotation 180°, that opening faces the top `Edge.Cuts` tab.
- `J2` and `JBL1` open toward the bottom `Edge.Cuts` boundary.
- The B2.2 carrier-to-LCD audit rechecked contacts 1 through 40 after the
  rotation: all 40 pad numbers and assigned nets match the straight-through
  interface contract.
- The routed-interface audit passes all eleven named cross-connector nets,
  including `PANEL_ID0`, `PANEL_ID1`, `LCD_INS`, `EN`, and `PWM`.
- System, panel, and backlight connector identities are unchanged.

## Fresh KiCad checks

Checks use KiCad 10.99 nightly build `10.99.0-2630-ge98e17ed18`.

- PCB error-level violations: **0**.
- Unconnected pads: **0**.
- All-severity PCB findings: 13 inherited footprint-library mismatch warnings.
- Schematic ERC errors: **0**.
- DRC exclusions: **0**.
- External interconnect release gate: **PASS**.
- Edge-connector placement/orientation audit: **PASS**.
- Assembly audit: **23 top, 0 bottom**.

## Fresh KiCad render review

- `renders/top.png`: `fa46687dbbab8be16c698c153922f007af346c0a96db5a3edfbafe8346d8e1c5`
- `renders/bottom.png`: `6989b7be569368340e5461c2892fd35657ac89aad850ba26fdfbee5cefa69447`
- `renders/side.png`: `cfb10fd0ab40f05f77e22e5bbb01235e2911529792e345d51e8eef273db27f71`
- `renders/perspective.png`: `36f078f9469b306985c4ce3793d2cada49ba6e0b9e87c831101d5a005ab455e4`

The top render confirms that every fitted component is on F.Cu and all three
cable entries face their documented physical edges. The bottom render is free
of fitted parts. The side view confirms a single-sided assembly envelope.

## Release package

`scripts/build_r2_7_jlc_candidate.py` creates the checksum-locked package under
`fab/r2.7-compact-rgb-production-jlc-candidate/`. The PCB is approved for
prototype fabrication. PCBA checkout remains conditional on sourcing the two
zero-stock BOM identities documented in `FABRICATION_STATUS.md`.
