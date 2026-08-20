# R2.9 fabrication status

Updated: 2026-08-21

R2.9 is **board-source ready but fabrication-blocked**. No R2.9 Gerber, drill,
BOM, CPL, or vendor-upload package has been released. The intended output path
after the system gate clears is
`../../fab/r2.9-compact-rgb-production-jlc-c91592/`.

## Release gates

- Native KiCad errors-only DRC: **0 violations, 0 unconnected pads**.
- Native KiCad all-severity DRC: 14 footprint-library mismatch warnings and
  50 non-blocking silkscreen-clearance warnings inside connector footprints;
  **0 silkscreen-over-copper errors**, **0 board-edge clipping errors**,
  0 unconnected pads, and no electrical/clearance errors.
- J2-area references `C2`, `C3`, `C4`, `C5`, `FL2`, and other labels found by
  the stricter whole-board audit are hidden from production silkscreen.
- The release builder explicitly plots Gerbers with solder mask subtracted
  from silkscreen once the system gate passes.
- Errors-only schematic ERC: **0 errors, 0 warnings**.
- Routed board interface audit: **PASS** for all eleven named cross-connector
  nets.
- System interconnect gate:
  `python3 scripts/check_interconnect_release.py --board lcd`: **BLOCKED** by
  `gpio-breakout-lcd`; the proposed ES&S FH41-compatible cable lacks verified
  shield/ground-plate construction. This gate must not be bypassed.
- Exact connector X/Y, rotation, F.Cu side, assigned edge, and outward-opening
  audit for `JFFC1`, `J2`, and `JBL1`: **PASS**.
- Fitted assembly: **23 top, 0 bottom**.
- Stack: four copper layers; board minimum finished drill: 0.20 mm.
- Package checksum manifest: not generated while the system gate is blocked.

The reproducible release command is:

```sh
python3 scripts/build_r2_9_jlc_candidate.py
```

from the repository root. The builder runs fail-closed and invokes the
external LCD interconnect gate before producing any output. Its 2026-08-21
run stopped at that gate as intended.

## Mechanical and visual evidence

- Actual outline area: 1297.6 mm², 29.33% below R2.6.
- Print mock-up validation: 58.0000 × 22.7000 × 4.0950 mm, 896 facets.
- Fresh actual KiCad top, bottom, side, and perspective renders were generated
  from the R2.9 PCB source and reviewed. The top face contains all fitted parts,
  the bottom face contains none, and all three cable openings face outward.
- Render hashes are recorded in `reports/verification.md`.

## PCBA procurement boundary

After the system interconnect gate clears, procurement still has this boundary
from the 2026-08-20 live inventory check:

- `J2`, I-PEX `20374-R30E-31`, `C5311655`: stock 0; pre-order minimum 442.
- `FL1`/`FL2`, Murata `DLP2ADN900HL4L`, `C91592`: stock 3874; minimum 1.

`C91592` is an approved same-series, same-footprint 90-ohm substitution and was
actually fitted on the previous five-board JLCPCB batch. `J2` mates with the
panel cable and remains exact. PCBA may proceed after the J2 pre-order is
received; do not silently substitute that connector.
