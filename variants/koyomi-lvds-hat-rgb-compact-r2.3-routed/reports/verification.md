# Koyomi RGB compact r2.3 routed verification

Date: 2026-08-11

## Geometry and interface

- Outline: 65.0000 × 28.2500 mm.
- Area: 1,836.25 mm², exactly 50% of the 65.0 × 56.5 mm donor.
- System connector: JFFC1, FH41-40S-0.5SH(05) / C596805.
- Cable mapping: straight-through contact `n` to contact `n`, documented in
  `../interface-pinout.csv`.
- Panel connector: J2, I-PEX 20374-R30E-31/20374-030E-31.
- Backlight connector: JBL1, keyed 12-contact Hirose FH12 horizontal FFC,
  carrying the complete former J5/J6 interface in legacy pin order. See
  `../backlight-interface-pinout.csv`.
- No physical J3-J8 donor test/header connectors are present on the board.
  Their schematic symbols are DNP and excluded from board, BOM, and placement
  files; JBL1 is the fitted replacement for J5/J6.
- Assembly sides: 21 SMD footprints on front, 0 SMD footprints on back.
- Total placed footprints: 29 front, 0 back (including mounting and
  unspecified footprints).
- RN1-RN6 were recreated on the front through KiCad's official netlist import,
  then positioned through the official IPC API.

## Routed PCB

- Copper stack: four layers (`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`).
- Ground reference: continuous named GND zone on `In1.Cu`, with local ground
  islands explicitly escaped and joined through checked vias/tracks.
- Assembly: 21 fitted SMD footprints on front, 0 on back.
- Connectivity: 0 unconnected PCB items.
- Via process: no via smaller than the board rule of 0.45 mm diameter;
  residual-route vias use 0.20 mm drills.
- Waivers/exclusions: none added.

The constrained IC1 fanout was completed without disturbing the established
RGB topology. D14, D15, D18, and D8 received local lane corrections; the
remaining signal routes were retained from the clean imported route. The
power and ground zones were refilled after every finishing pass.

## Fresh KiCad checks

All checks use the repository's bundled KiCad 10.99 nightly dated 2026-07-22.

- PCB DRC, error-only: **0 violations, 0 unconnected items**.
- PCB DRC, all-severity: 13 inherited `lib_footprint_mismatch` warnings and
  nothing else.
- Schematic ERC, error-only: three inherited `power_pin_not_driven` errors
  on +5 V, +3.3 V, and GND.
- Schematic ERC, all-severity: 85 findings total: 3 power errors, 61 off-grid
  endpoint warnings, 16 library-copy mismatches, 1 unavailable-library
  warning, and 4 intentionally unconnected-pin warnings.

Authoritative reports are `drc-errors.rpt`, `drc-all.rpt`, `erc-errors.rpt`,
and `erc-all.rpt` in this directory.

## Gate

PCB routing is complete and DRC-clean. Fabrication remains blocked only on the
schematic release decision: add proper power-source declarations/PWR_FLAGs or
formally accept the three inherited ERC errors in an electrical review. Do
not generate Gerbers, assembly files, or a shopping-cart upload from R2.3
until that decision is recorded.
