# Koyomi RGB compact r2.0 floorplan verification

Date: 2026-08-11

## Geometry and interface

- Outline: 65.0000 × 28.2500 mm.
- Area: 1,836.25 mm², exactly 50% of the 65.0 × 56.5 mm donor.
- System connector: JFFC1, FH41-40S-0.5SH(05) / C596805.
- Cable mapping: straight-through contact `n` to contact `n`, documented in
  `../interface-pinout.csv`.
- Panel connector: J2, I-PEX 20374-R30E-31/20374-030E-31.
- No physical J3-J8 test/header connectors are present on the board. Their
  schematic symbols are DNP and excluded from board, BOM, and placement files.

## Fresh KiCad checks

All checks use the repository's bundled KiCad 10.99 nightly.

- DRC all-severity: 19 violations, all inherited footprint-library mismatch or
  unavailable-library warnings.
- DRC physical placement: 0 courtyard overlaps, 0 copper-to-edge violations,
  0 shorts, and 0 other placement violations.
- DRC opens: 137, expected because donor routing and zones were deliberately
  removed before compact placement.
- ERC all-severity: 84 findings, including the same three inherited
  `power_pin_not_driven` errors. The remaining findings are warnings.

Authoritative reports are `drc-floorplan.rpt`, `erc-floorplan.rpt`, and
`board-stats.json` in this directory.

## Gate

Fabrication is blocked. The next revision must select the final layer stack,
route every connection, restore ground/power zones and return paths, and pass
fresh DRC/ERC before any release package or shopping-cart upload is created.
