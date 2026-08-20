# Koyomi RGB compact R2.8 production verification

Date: 2026-08-20

## Mechanical result

- Source revision: R2.8, derived from the immutable R2.7 production candidate.
- R2.6 outline: 65.0 × 28.25 mm = 1836.25 mm².
- R2.8 base rectangle: 58.0 × 22.2 mm = 1287.6 mm².
- JFFC1 support tab: 20.0 × 0.5 mm = 10.0 mm².
- Actual R2.8 area: 1297.6 mm²; area reduction: 29.33%.
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
- R2.7 versus R2.8 normalized manufacturing geometry: copper, mask, paste,
  outline, and drill outputs are **identical**. Only the intended top-silk
  revision text and the assembly BOM value/part number changed.

## Fresh KiCad render review

- `renders/top.png`: `1d18c20c2b5712d60422eb1e91a2d9183b2b71315fbc93c8109e14d42ac9fbcb`
- `renders/bottom.png`: `e7e91e1f037a7f44bc9df42f3e0fdde7bc64ed54e6abd0ff3d6f97cb228ac611`
- `renders/side.png`: `5031554716f1125c500719a8156c4bfaf3caf8a1589a699566b756cfacdf2102`
- `renders/perspective.png`: `16546691e80f93600cec825d4bd4731e75c4d3ea455e76bd6da36ab9b8a0fdd8`

The top render confirms that every fitted component is on F.Cu and all three
cable entries face their documented physical edges. The bottom render is free
of fitted parts. The side view confirms a single-sided assembly envelope.
KiCad cannot resolve the vendor STEP path attached to FL1/FL2, so those two
2.0 × 1.0 mm filter bodies are represented by conservative solid proxies in
the generated print mockup; their pads and placement remain visible in the
actual KiCad render.

## Release package

`scripts/build_r2_8_jlc_candidate.py` creates the checksum-locked package under
`fab/r2.8-compact-rgb-production-jlc-c91592/`. The PCB is approved for
prototype fabrication. FL1/FL2 use in-stock `C91592`; PCBA checkout remains
conditional only on receiving exact connector `C5311655` into the private
parts library.
