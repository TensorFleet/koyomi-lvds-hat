# Koyomi RGB/DPI LVDS — compact r2.1 single-side

This is a mechanical and routing fork of the tested TensorFleet/Exentio
Koyomi RGB/DPI LVDS HAT. It deliberately excludes the experimental HDMI input
path and starts from the post-order source with the FL1/FL2 solder-mask fix.

## Size target

- Donor outline: 65.0 × 56.5 mm = 3,672.5 mm².
- Compact target: no more than 65.0 × 28.25 mm = 1,836.25 mm².
- Objective: approximately half the donor area while retaining the RGB/DPI to
  SN75LVDS83B path, LVDS display connector, required power conditioning, and
  backlight-control signals.

The 2×20 Raspberry Pi header has been replaced by the same Hirose
`FH41-40S-0.5SH(05)` / JLCPCB `C596805` used on the compact CM5 carrier. The
system interface is one straight-through 40-contact FFC harness. Contact `n`
maps to Raspberry Pi physical pin `n`; the authoritative mapping is
`interface-pinout.csv`.

The single system harness carries RGB/DPI, power, ground, software I²C,
enable, PWM, and the retained control signals. J3 through J8 remain visible in
the schematic only to document the donor test connections, but they are DNP,
excluded from the PCB, excluded from the BOM, and excluded from placement
files. Physically, the compact board has only:

1. `JFFC1` — system/CM5-carrier FFC harness;
2. `J2` — 30-position I-PEX micro-coax cable to the LCD panel.

The two solder jumpers remain local configuration items and do not require a
cable.

## Single-side assembly

All 20 fitted SMD footprints are now on the front side. The six resistor
arrays that were on the back in r2.0 were removed and re-imported from the
schematic so KiCad recreated them natively on `F.Cu`; they were not mirrored
by editing footprint internals. The bottom render is intentionally bare.

This should allow a single SMT placement/stencil/reflow pass when the routed
board is eventually quoted. It does not require a one-layer PCB: routing may
still use both outer copper faces and the expected four-layer stack.

## Status

The r2.1 floorplan reaches exactly **65.0 × 28.25 mm**, or 1,836.25 mm²: half
the donor area. Fresh all-severity DRC has no courtyard, edge-clearance,
shorting, or other physical-placement violations. It reports 13 inherited
library warnings and 127 expected opens because donor routing was deliberately
removed before compaction. ERC has the same three inherited power-pin errors;
the additional findings are warnings only.

This revision remains fabrication-closed until the compact board is natively
routed, zones are restored, and fresh KiCad ERC/DRC gates pass. A four-layer
stack is the expected routing direction because it preserves ground reference
under the 40-contact RGB fanout without expanding the board. No Gerbers,
assembly files, or JLCPCB upload are authorized from this folder yet.

All PCB and schematic mutations in this fork are performed by the scripts in
`scripts/` through KiCad's official `kicad-python` IPC API. The scripts do not
rewrite KiCad project internals.
