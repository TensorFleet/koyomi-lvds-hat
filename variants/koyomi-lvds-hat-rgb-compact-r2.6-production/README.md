# Koyomi RGB/DPI LVDS — compact R2.6 production candidate

R2.6 is the fabrication-ready successor to the compact R2.4 routing fork of
the tested TensorFleet/Exentio Koyomi RGB/DPI LVDS HAT. It retains only the
RGB/DPI-to-SN75LVDS83B path and fixes the schematic power declarations that
previously kept the compact board out of fabrication.

## Mechanical and assembly target

- Outline: **65.0 × 28.25 mm**, exactly half the donor board area.
- Copper: four layers (`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`).
- Assembly: **23 fitted parts, all on the top side**.
- Board-to-system cable: Hirose `FH41-40S-0.5SH(05)` / JLCPCB `C596805`.
- Panel cable: I-PEX `20374-R30E-31` / JLCPCB `C5311655`.
- Backlight cable: Hirose `FH12-12S-0.5SH(55)` / JLCPCB `C88360`.

The bottom face is intentionally free of fitted parts. H1–H4 and JP1–JP2 are
bare mechanical/configuration features and are excluded from BOM and CPL.

## Consolidated interfaces

The 40-contact `JFFC1` harness carries RGB/DPI, power, ground, software I2C,
enable, PWM, and the panel-sideband signals. Its authoritative contact map is
`interface-pinout.csv`. The three repaired sidebands are:

| Contact | LCD net | Endpoint |
| ---: | --- | --- |
| 17 | `PANEL_ID0` | J2.10 |
| 34 | `PANEL_ID1` | J2.21 |
| 39 | `LCD_INS` | J2.30 |

`JBL1` consolidates the former J5/J6 backlight harness: VCD1–VCD6, VAD, 5 V,
ground, PWM, and enable. Its map is `backlight-interface-pinout.csv`. The old
J3–J8 symbols remain in the schematic as DNP documentation, but no J3–J8
footprints exist and no required production endpoint depends on them.

## Release gates

- PCB DRC: **0 errors, 0 unconnected pads, 0 exclusions**.
- Schematic ERC: **0 errors**.
- Routed interface audit: **PASS** for all eleven retained interface nets.
- All-severity DRC: 13 inherited `lib_footprint_mismatch` warnings only.
- Minimum drill: **0.20 mm**; the JLC quote must include the fine-hole process.
- Fabrication package: `../../fab/r2.6-compact-rgb-production-jlc-candidate/`.

The production package is fail-closed and checksumed. Use the Gerber ZIP,
`assembly/bom.csv`, and `assembly/positions.csv`; select four layers, 1.6 mm,
ENIG, ordinary tented vias, and top-side Economic PCBA. **Confirm Production
File** and manual placement confirmation are mandatory.

## System-level constraints

R2.6 must be paired with carrier **B2.2** using a straight-through 40-contact
FFC. Earlier carrier pinouts can drive the three sideband contacts incorrectly
and are incompatible.

`PANEL_ID0`, `PANEL_ID1`, and `LCD_INS` are sensed inputs, not driven outputs.
The external backlight/interlock circuit must provide the documented 100 kΩ
pull-up and Schmitt/hardware interlock for active-low `LCD_INS`. That circuit,
live JLC inventory, placement review, and measured chassis fit remain external
system gates; this folder authorizes a fabrication prototype, not checkout.

All schematic and PCB mutations are recorded in `scripts/` and use KiCad's
official IPC API. Current major-phase views are in `renders/`.
