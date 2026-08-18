# Koyomi RGB compact R2.7 floorplan verification

Date: 2026-08-18

## Mechanical result

- Source revision: R2.6 production candidate.
- R2.6 outline: 65.0 × 28.25 mm = 1836.25 mm².
- R2.7 outline: 58.0 × 22.2 mm = 1287.6 mm².
- Area reduction: 29.88%.
- Fitted parts: 23 front, 0 back.
- Mechanical/configuration footprints: H1–H4 and JP1–JP2 remain front-side
  bare features and are excluded from the fitted count.
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
