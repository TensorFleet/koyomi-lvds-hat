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

## JLCPCB quote audit — 2026-08-10

The package was uploaded as a five-board, two-layer, 1.6 mm, ENIG, two-sided
Standard PCBA quote with ordinary tented vias and **Confirm Production File**
enabled.  JLC's Standard PCBA workflow added edge rails, so its quote view
shows a 75 x 70.5 mm manufacturing panel around the actual 65 x 56.5 mm board.

JLC matched 10 of 12 BOM groups.  The matched parts total USD 19.23 for five
boards.  The pre-BOM PCB/assembly estimate was USD 20.14, so the incomplete
quote is at least USD 39.37 before the two shortages and shipping.

The two unresolved groups block the placement/final-quote stages:

- FL1/FL2: `DLP2ADN121HL4L`, JLC `C710576`, 10 pieces required, zero stock.
  This is an obsolete four-line common-mode choke array; do not substitute a
  superficially similar four-pad/two-line choke without an electrical and
  footprint revision.
- J2: `20374-R30E-31`, JLC `C5311655`, 5 pieces required, zero stock.

This upload is a sourcing/price probe only.  It is not in the shopping cart and
must not be purchased until both shortages are resolved and JLC's component
placement view has been checked.
