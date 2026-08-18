# R2.7 fabrication status

Updated: 2026-08-18

R2.7 is **not fabrication-ready**. Do not generate or upload Gerbers, drill
files, BOM, or CPL files from this directory until the two remaining copper
opens are fixed and every release gate is rerun.

## Completed

- The print mock-up was regenerated after correcting the outward-facing
  JFFC1 orientation.
- The checked STL is
  `mechanical/print-models/koyomi-rgb-compact-r2.7-print-mockup.stl`.
- The print validation reports a 58.0000 x 22.7000 x 4.0950 mm solid with
  896 facets; checksums are recorded beside the model.
- KiCad ERC, errors only: 0 violations.
- The repository interconnect release gate passes for `lcd`.
- JFFC1 and JBL1 edge openings face out of the board.
- The board-level `R2.7` and `JBL1` silkscreen text now meets the 1.0 mm
  height and 0.15 mm stroke rules.

## Blocking PCB result

The native KiCad DRC report is `reports/drc-routed-working.rpt`:

- 0 DRC copper/clearance violations,
- 14 reviewed warnings,
- 2 unconnected items,
- 0 exclusions.

The two opens are:

1. `G1`: JFFC1 pad 23 to the existing G1 via at 128.5886, 34.5000 mm.
2. `+2V5`: C5 pad 1 to the existing +2V5 branch near
   119.3441, 38.7641 mm.

The 14 warnings are one dangling G1 via plus 13 inherited/local footprint
library mismatches. The earlier four silkscreen dimension warnings are fixed.

Several isolated routing experiments reached zero opens but failed native
KiCad clearance checks, so none were retained. The saved board remains the
clean two-open result; reports produced by a routing experiment must never be
used as release evidence.

## Required next gate

Route both opens natively, refill zones, and rerun:

1. all-severity PCB DRC with 0 violations, 0 unconnected items, and 0
   exclusions;
2. errors-only ERC;
3. the LCD/carrier pin-order audit;
4. `python3 scripts/check_interconnect_release.py --board lcd` from the
   `vaio_p_modding` repository;
5. the fabrication-package checksum and assembly-file checks.

Only after all five pass may a fabrication package be created or uploaded.
