# R2.8 fabrication status

Updated: 2026-08-20

R2.8 is **fabrication-ready as a prototype**. The Gerber, drill, BOM, CPL,
STEP, render, and checksum package is
`../../fab/r2.8-compact-rgb-production-jlc-c91592/`.

## Release gates

- Native KiCad errors-only DRC: **0 violations, 0 unconnected pads**.
- Native KiCad all-severity DRC: 13 inherited footprint-library mismatch
  warnings, 0 unconnected pads, and no electrical/clearance errors.
- Errors-only schematic ERC: **0 errors, 0 warnings**.
- Routed board interface audit: **PASS** for all eleven named cross-connector
  nets.
- System interconnect gate:
  `python3 scripts/check_interconnect_release.py --board lcd`: **PASS**.
- Exact connector X/Y, rotation, F.Cu side, assigned edge, and outward-opening
  audit for `JFFC1`, `J2`, and `JBL1`: **PASS**.
- Fitted assembly: **23 top, 0 bottom**.
- Stack: four copper layers; minimum finished drill in the package: 0.20 mm.
- Package checksum manifest: generated and self-consistent.

The reproducible release command is:

```sh
python3 scripts/build_r2_8_jlc_candidate.py
```

from the repository root. The builder runs fail-closed and invokes the
external LCD interconnect gate before producing any output.

## Mechanical and visual evidence

- Actual outline area: 1297.6 mm², 29.33% below R2.6.
- Print mock-up validation: 58.0000 × 22.7000 × 4.0950 mm, 896 facets.
- Fresh actual KiCad top, bottom, side, and perspective renders were generated
  from the released PCB and reviewed. The top face contains all fitted parts,
  the bottom face contains none, and all three cable openings face outward.
- Render hashes are recorded in `reports/verification.md` and the fabrication
  package `SHA256SUMS` file.

## PCBA procurement boundary

The PCB is ready to fabricate. As of the 2026-08-20 live inventory check:

- `J2`, I-PEX `20374-R30E-31`, `C5311655`: stock 0; pre-order minimum 442.
- `FL1`/`FL2`, Murata `DLP2ADN900HL4L`, `C91592`: stock 3874; minimum 1.

`C91592` is an approved same-series, same-footprint 90-ohm substitution and was
actually fitted on the previous five-board JLCPCB batch. `J2` mates with the
panel cable and remains exact. PCBA may proceed after the J2 pre-order is
received; do not silently substitute that connector.
