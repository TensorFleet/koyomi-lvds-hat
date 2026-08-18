# Koyomi RGB compact R2.6 production verification

Date: 2026-08-13

## Defects closed

R2.6 retains R2.4's routed replacement for the functional endpoints that were
lost when legacy J3–J8 connector footprints were removed:

| Net | System FFC | Panel connector |
| --- | --- | --- |
| `PANEL_ID0` | JFFC1.17 | J2.10 |
| `PANEL_ID1` | JFFC1.34 | J2.21 |
| `LCD_INS` | JFFC1.39 | J2.30 |

The production-interface audit also verifies `EN` and `PWM` between JFFC1 and
JBL1 and VCD1–VCD6 between J2 and JBL1. Every named endpoint has routed copper;
none depends on an excluded legacy footprint.

R2.6 additionally marks the incoming JFFC1 power contacts with the correct
schematic power-output semantics. This closes the three inherited +5 V, +3.3 V,
and GND `power_pin_not_driven` ERC errors without an exclusion or waiver.

## Fresh KiCad gates

Checks use the repository's bundled KiCad 10.99 nightly dated 2026-07-22.

- PCB DRC, error-only: **0 violations, 0 unconnected pads**.
- PCB DRC, all-severity: **13 inherited `lib_footprint_mismatch` warnings**,
  no other findings, and 0 unconnected pads.
- Schematic ERC, error-only: **0 errors**.
- Schematic ERC, all-severity: **91 warnings, 0 errors**.
- Routed production-interface audit: **PASS**.
- DRC exclusions: **0**.
- Assembly population: **23 top, 0 bottom**.
- Minimum Excellon drill: **0.20 mm**.

Authoritative reports are `drc-errors.rpt`, `drc-all.rpt`, `erc-errors.rpt`,
`erc-all.rpt`, `r2.6.net`, and `interface-audit.json` in this directory. The
release builder regenerates fresh copies in the fabrication package and aborts
if any gated count or fitted reference changes.

## Paired-carrier and fabrication gate

The matching carrier is B2.2. Its cross-board audit verifies all 40 contacts,
including `PANEL_ID0` on contact 17, `PANEL_ID1` on contact 34, and `LCD_INS`
on contact 39. R2.6 must not be connected to the older R2.3/R2.4 carrier map.

The board is approved as a fabrication-ready prototype. The JLC quote must use
four layers, 1.6 mm, ENIG, ordinary tented vias, and the 0.20 mm fine-hole
process. Enable **Confirm Production File** and manual placement confirmation.
Purchase remains gated on live component inventory, placement review, measured
chassis fit, and completion of the external LCD_INS pull-up/Schmitt/interlock.
