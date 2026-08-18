# Koyomi RGB/DPI LVDS — compact R2.7 30%-area study

R2.7 forks the electrically complete R2.6 production candidate to test a
smaller mechanical envelope without altering R2.6. It retains the same
schematic, connector identities, pin maps, and fitted component set.

## Mechanical target

- R2.6 outline: **65.0 × 28.25 mm = 1836.25 mm²**.
- R2.7 base rectangle: **58.0 × 22.2 mm = 1287.6 mm²**.
- `JFFC1` support tab: **20.0 × 0.5 mm = 10.0 mm²**.
- Actual board area: **1297.6 mm²**, a **29.33% reduction**.
- Copper: four layers (`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`).
- Assembly: **23 fitted parts, all on the top side**.
- Four mounting holes retained.

The three production cable connectors remain at board edges: `JFFC1` for the
system harness, `J2` for the panel, and `JBL1` for backlight/sideband support.
All three cable openings face their assigned board edge. `JFFC1` is rotated
180° from the first floorplan and sits behind a shallow local support tab so
its shield pads retain edge clearance. Their authoritative
edge and rotation record is `edge-connector-orientations.json`; a connector
opening toward the board interior blocks routing and fabrication.

## Status

This is a **routed work in progress**, not a fabrication revision. The first
full route is clean for copper clearance but still has two open connections.
Do not generate or upload fabrication files from R2.7 until native routing,
DRC/ERC, interface, signal-integrity, and assembly audits are complete. The
current fail-closed gate and exact open-net list are in
`FABRICATION_STATUS.md`.

`scripts/make_r2_7_floorplan.py` records the layout mutation through KiCad's
official IPC API. Major-phase renders and fresh reports live in `renders/` and
`reports/` after regeneration.
