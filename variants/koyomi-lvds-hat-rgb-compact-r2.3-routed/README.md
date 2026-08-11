# Koyomi RGB/DPI LVDS — compact r2.3 routed

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

r2.3 retains the r2.2 `JBL1`, a keyed horizontal Hirose
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

R2.3 remains exactly **65.0 × 28.25 mm**, or 1,836.25 mm²: half the donor
area. It is now fully routed on four copper layers (`F.Cu`, `In1.Cu`,
`In2.Cu`, and `B.Cu`) with an internal ground reference plane. Every signal,
power, and ground island is connected.

Fresh error-only DRC reports **0 violations and 0 unconnected items**. The
all-severity report contains only 13 inherited footprint/library-copy
warnings; there are no shorts, clearance errors, invalid via sizes, or DRC
exclusions. The final routed board uses the existing minimum 0.45/0.20 mm via
process.

Schematic ERC remains unchanged from the donor: three inherited
`power_pin_not_driven` errors on +5 V, +3.3 V, and GND, plus library/off-grid
warnings. Routing is complete, but fabrication release remains closed until
those schematic power-source declarations are fixed or explicitly accepted
in a documented electrical review. No Gerbers or shopping-cart upload are
authorized from this folder yet.

All PCB and schematic mutations in this fork are performed by the scripts in
`scripts/` through KiCad's official `kicad-python` IPC API. The scripts do not
rewrite KiCad project internals. `scripts/finalize_r2_3.py` and
`scripts/finish_residual_r2_3.py` record the official-API routing workflow;
`scripts/polish_r2_3.py` applies the final silkscreen spacing. Current major-
phase board views are in `renders/top.png`, `renders/bottom.png`, and
`renders/side.png`.
