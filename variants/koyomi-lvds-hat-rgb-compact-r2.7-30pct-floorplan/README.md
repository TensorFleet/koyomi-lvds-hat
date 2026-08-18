# Koyomi RGB/DPI LVDS — compact R2.7 30%-area study

R2.7 forks the electrically complete R2.6 production candidate to test a
smaller mechanical envelope without altering R2.6. It retains the same
schematic, connector identities, pin maps, and fitted component set.

## Mechanical target

- R2.6 outline: **65.0 × 28.25 mm = 1836.25 mm²**.
- R2.7 outline: **58.0 × 22.2 mm = 1287.6 mm²**.
- Area reduction: **29.88%**.
- Copper: four layers (`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`).
- Assembly: **23 fitted parts, all on the top side**.
- Four mounting holes retained.

The three production cable connectors remain at board edges: `JFFC1` for the
system harness, `J2` for the panel, and `JBL1` for backlight/sideband support.

## Status

This is a **placement and mechanical study**, not a fabrication revision. The
R2.6 routing and zones were deliberately removed because they are invalid after
moving components. Do not generate or upload fabrication files from R2.7 until
native routing, DRC/ERC, interface, signal-integrity, and assembly audits are
complete.

`scripts/make_r2_7_floorplan.py` records the layout mutation through KiCad's
official IPC API. Major-phase renders and fresh reports live in `renders/` and
`reports/` after regeneration.
