# Koyomi GPIO/DPI r1.1 — JLCPCB quote package

This package is the tested GPIO/DPI Koyomi LCD controller with TensorFleet's
FL1/FL2 solder-mask correction regenerated from the authoritative KiCad
source.  It is the conservative board to quote while the FFC and HDMI variants
remain development-only.

## Upload settings

- 65.0 x 56.5 mm, 2 copper layers, 1.6 mm FR-4
- ordinary 0.40 mm vias; no plugged, filled, blind, or buried vias
- assemble both sides
- upload `koyomi-gpio-r1.1-gerbers.zip`, then the tracked BOM and CPL
- enable **Confirm Production File** before adding the PCBA to the cart
- J2 (`20374-R30E-31`) has no LCSC code in the inherited BOM and may require
  global sourcing, consignment, or manual fitting

## Verification disposition

- The source is the previously manufactured and working upstream controller.
- The only copper-adjacent change is adding the missing F.Mask openings to all
  16 FL1/FL2 pads.  The regenerated front mask contains those openings.
- KiCad's nightly CLI successfully regenerated Gerbers, drill data, and board
  statistics from the current source.
- The nightly PCB DRC command aborts in this local build, so **Confirm
  Production File** and JLC's production-file review remain mandatory.
- ERC reports three inherited `power_pin_not_driven` errors for +5V, +3V3, and
  GND because the legacy schematic has no PWR_FLAG symbols.  These are
  annotation defects, not new opens; the board is physically tested.  They are
  retained in `reports/erc-errors.rpt` instead of being silently excluded.

The FFC r1.2 and HDMI r0.1 folders are not alternate release packages and must
not be uploaded.

