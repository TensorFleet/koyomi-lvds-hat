# Koyomi RGB compact R2.7 floorplan verification

Date: 2026-08-18

## Mechanical result

- Source revision: R2.6 production candidate.
- R2.6 outline: 65.0 × 28.25 mm = 1836.25 mm².
- R2.7 base rectangle: 58.0 × 22.2 mm = 1287.6 mm².
- JFFC1 support tab: 20.0 × 0.5 mm = 10.0 mm².
- Actual R2.7 area: 1297.6 mm²; area reduction: 29.33%.
- Fitted parts: 23 front, 0 back.
- Mechanical/configuration footprints: H1–H4 and JP1–JP2 remain front-side
  bare features and are excluded from the fitted count.

## Edge connector orientation

- Hirose's FH41 drawing places the cable opening opposite the 40 signal solder
  pads. At `JFFC1` rotation 180°, that opening faces the top `Edge.Cuts` tab.
- `J2` and `JBL1` open toward the bottom `Edge.Cuts` boundary.
- The B2.2 carrier-to-LCD audit rechecked contacts 1 through 40 after the
  rotation: all 40 pad numbers and assigned nets still match the straight-
  through interface contract. Its only five reported failures are the expected
  unrouted `PANEL_ID0`, `PANEL_ID1`, `LCD_INS`, `EN`, and `PWM` copper paths in
  this floorplan phase.
- System, panel, and backlight connector identities are unchanged.

## Fresh KiCad checks

Checks use the repository-pinned KiCad 10.99 nightly dated 2026-07-22.

- PCB placement/clearance violations: **0**.
- Expected unrouted connections: **138**.
- Schematic ERC errors: **0**.
- DRC exclusions: **0**.
- Visual review: top-side components are on the board, the bottom assembly
  face is empty, and all four mounting holes remain inside the outline.

The DRC report is `drc-errors.rpt`; it intentionally records the 138 opens.
This floorplan is not a release candidate and has no fabrication package.

## Next gate

R2.7 needs native four-layer routing, plane/return-path review, refreshed
interface audits, all-severity DRC/ERC, assembly/CPL review, and a new carrier
interconnect check before any fabrication artifacts can be generated.
