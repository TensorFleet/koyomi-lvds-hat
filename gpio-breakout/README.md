# koyomi gpio-breakout A1 — 40-pin FFC to Pi GPIO bench adapter

Bench adapter: the carrier/LCD system's 40-contact FFC (Hirose
FH41-40S-0.5SH(05), C596805 — the JDISP1/JFFC1 interconnect) broken out 1:1 to
a standard Raspberry Pi 40-pin 2.54 mm header, so a stock Pi can drive the
Koyomi LVDS chain over the production FFC, or probe a carrier's display FFC.

**A1 addresses the 2026-08-20 A0 design review**: 63.5 × 32 mm, **4-layer**
(F sig / In1 solid GND plane / In2 GND pour / B sig+pour), corrected FH41
land pattern (0.30 × 0.65 copper, 0.25 paste via paste-margin), fused and
cuttable power links, all connector pins connected (pads 41–50 shield → GND),
FH41 symbol pins retyped passive.

## Gates (this commit, reproducible)

- Errors-only ERC: 0. Errors-only DRC: **0 violations, 0 unconnected, 0
  footprint errors** (`kicad/drc-errors.rpt`).
- All-severity DRC: 30 cosmetic silkscreen warnings, **zero dangling copper**
  (`kicad/drc-all.rpt`). All-severity ERC: 31 library-snapshot notices
  (`kicad/erc-all.rpt`) — recorded, not waived.
- NOT fabrication-released: the interconnect contract entry (registered in
  vaio_p_modding) pins the cable question — FH41 is specified for shielded
  0.3 mm FFC with ground contacts; an exact shielded cable P/N (or a reviewed
  decision to accept unshielded AWM 20624 for bench-only use) is required
  before Gerber/BOM/CPL generation.

## Power (new in A1)

Pi → FFC power is **fused and severable**:

- `JP4` (5V LINK) and `JP5` (3V3 LINK): solder jumpers, **bridged by default**
  so the adapter works out of the box; **cut them when the LCD chain is
  powered externally** (backside silk says so) to prevent backfeeding the Pi.
- `F1`: 0.5 A PTC polyfuse (1206) in the 5 V path — matches the FH41 0.5 A
  contact rating. Budget: serializer ≈50 mA on 3V3; backlight loads belong on
  a separate supply, not through this adapter.

## The three special pins — jumpers OPEN by default

FFC 17/34/39 are PANEL_ID0/PANEL_ID1/LCD_INS in the FFC system but 3V3/GND/GND
on a real Pi. They are isolated behind default-OPEN solder jumpers JP1–JP3
with test pads TP1–TP3 (TP4 GND, TP5 3V3 alongside). Close JP1/JP2 to strap
IDs, JP3 to report "panel inserted". Open = safe, and correct for the
retrofit (straps ignored, WP-003e).

## Assembly definition

- **J1 (FH41, C596805): JLC SMT-placed** — the only machine-placed part
  besides F1/JP jumper pads.
- **J2: DNP for assembly — hand-fit.** For riding a Pi, solder a 2×20
  **stacking socket** from the BOTTOM face (exact P/N to be pinned at order
  time); for cable use, a plain 2×20 pin header on top. Pin 1 = square pad,
  marked `1` on silk.
- FFC contacts face DOWN (silk marked) — same bottom-contact convention and
  cable fold rules as the carrier↔LCD link.

Generated headlessly (tools/: netlist_def_bo, gen_sch_bo, gen_pcb_bo,
route_board + pre-lay scripts); Freerouting 2.2.4 jar SHA-256 verified. GND
mid-row pads are stitched to the In1 plane with dedicated vias; power runs are
hand-placed locked copper laid before autorouting.
