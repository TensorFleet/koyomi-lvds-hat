# Koyomi RGB/DPI LVDS — compact r2.2 backlight FFC

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

The system harness carries RGB/DPI, power, ground, software I²C, enable, PWM,
and the retained control signals. The legacy J3 through J8 symbols remain in
the schematic only to document the donor test connections; they are DNP and
excluded from the PCB, BOM, and placement files.

r2.2 adds `JBL1`, a keyed horizontal Hirose
`FH12-12S-0.5SH(55)` 12-contact, 0.5 mm FFC connector. It consolidates every
old J5/J6 LCD-backlight contact into one cable without changing their order:
new pins 1–6 are J5.1–J5.6, and new pins 7–12 are J6.1–J6.6. The old unused
J6.2 position remains an explicit no-connect on JBL1 pin 8. The authoritative
map is `backlight-interface-pinout.csv`.

Physically, the compact board now has three cable connectors:

1. `JFFC1` — system/CM5-carrier FFC harness;
2. `J2` — 30-position I-PEX micro-coax cable to the LCD panel;
3. `JBL1` — 12-position FFC for VCD1–VCD6, VAD, 5 V, ground,
   backlight PWM, and backlight enable.

The two solder jumpers remain local configuration items and do not require a
cable.

## Single-side assembly

All 21 fitted SMD footprints are on the front side. The six resistor
arrays that were on the back in r2.0 were removed and re-imported from the
schematic so KiCad recreated them natively on `F.Cu`; they were not mirrored
by editing footprint internals. JBL1 is also on the front. The bottom render
is intentionally bare.

This should allow a single SMT placement/stencil/reflow pass when the routed
board is eventually quoted. It does not require a one-layer PCB: routing may
still use both outer copper faces and the expected four-layer stack.

## Status

The r2.2 floorplan remains exactly **65.0 × 28.25 mm**, or 1,836.25 mm²: half
the donor area. Fresh all-severity DRC has no courtyard, edge-clearance,
shorting, or other physical-placement violations. It reports 13 inherited
library warnings and 138 expected opens because donor routing was deliberately
removed before compaction and JBL1 is not routed yet. ERC has the same three
inherited power-pin errors; the additional findings are warnings only. The two
new connector-specific warnings are imported-library-symbol parity and one
off-grid endpoint inherited from the native connector template.

This revision remains fabrication-closed until the compact board is natively
routed, zones are restored, and fresh KiCad ERC/DRC gates pass. A four-layer
stack is the expected routing direction because it preserves ground reference
under the 40-contact RGB fanout without expanding the board. No Gerbers,
assembly files, or JLCPCB upload are authorized from this folder yet.

All PCB and schematic mutations in this fork are performed by the scripts in
`scripts/` through KiCad's official `kicad-python` IPC API. The scripts do not
rewrite KiCad project internals. `scripts/add_backlight_harness.py` preserves
the old J5/J6 ordering exactly and `scripts/make_compact_floorplan.py` places
and labels the resulting connector.
