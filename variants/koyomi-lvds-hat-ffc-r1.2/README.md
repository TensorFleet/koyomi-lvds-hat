# Koyomi LVDS HAT — 40-pin FFC r1.2

This is an incremental fork of the manufactured Project Koyomi LVDS HAT.  The
LVDS, backlight, DPI, and software-I2C circuitry is unchanged.  Revision r1.2
replaces the tall Raspberry Pi 2x20 header with one compact 40-position FFC
connector.  The donor is the current post-order source in
`hardware/koyomi-lvds-hat/`, including commit `2119f6a`'s FL1/FL2 solder-mask
fix.  The exact Gerbers used for the earlier five-board fabrication remain in
`hardware/koyomi-lvds-hat/gerbers/`; those Gerbers predate that mask fix.

## Interface decision

- Connector: Hirose `FH41-40S-0.5SH(05)`
- JLCPCB/LCSC: `C596805`
- Contacts: 40, 0.5 mm pitch, bottom contact
- Mated height above PCB: 2.5 mm nominal
- Board reference: `JFFC1`
- Footprint: `B2_INTERCONNECT:FPC-SMD_FH41-40S-0.5SH`
- Board outline: 65.0 x 56.5 mm, unchanged from the donor HAT

This is the same connector, footprint, and 3D model used for the B2 carrier
interface.  JLCPCB showed 2,096 pieces in stock on 2026-08-09.  Treat that as a
dated snapshot, not a purchase guarantee.

The FFC contact number equals the Raspberry Pi physical header pin number:
FFC 1 -> Pi physical pin 1 through FFC 40 -> Pi physical pin 40.  The complete
map is tracked in `interface-pinout.csv`.  That preserves the current LCD/DPI
use and allows a future generic GPIO breakout to use the same carrier socket.

The LCD board and a generic GPIO breakout are alternative attachments.  They
must not be connected in parallel unless a purpose-built splitter addresses
signal ownership, power, and stubs.

## Cable contract

The electrical contract is exact and must not be inferred from the cable's
marketing name: carrier contact `n` must reach LCD contact `n`.  Verify at
minimum `1 -> 1` and `40 -> 40` with a continuity meter in the final installed
board orientation before applying power.  "Type A" and "Type B" describe
which face exposes the contacts, but do not by themselves prove the effective
pin order after either PCB is flipped or mirrored in the chassis.

## Display configuration

The display path still uses the TI `SN75LVDS83B` and the Raspberry Pi DPI
signals.  Software I2C remains GPIO23/SDA and GPIO24/SCL.

```text
dtparam=i2c_arm=off
dtparam=spi=off
display_auto_detect=0
dtoverlay=vc4-kms-dpi-generic
dtparam=hactive=1600,hfp=32,hsync=65,hbp=97
dtparam=vactive=768,vfp=1,vsync=1,vbp=8
dtparam=width-mm=182,height-mm=87
dtparam=clock-frequency=83600000,rgb666
framebuffer_width=1600
framebuffer_height=768
dtoverlay=i2c-gpio,i2c_gpio_sda=23,i2c_gpio_scl=24
disable_overscan=1
```

## Status and fabrication gate

The donor circuit is the manufactured Koyomi design.  Stable KiCad's status
bar reports **96 nets and 0 unrouted connections** for that donor; the earlier
"96 opens" statement confused those adjacent counters.  The r1.2 **FFC
conversion is an interface/floorplan revision**, not fabrication-ready:

- authoritative nightly GUI DRC on the checked-in r1.2 floorplan reports 122
  violations and 37 unconnected items;
- replacing J1 therefore still requires a native fanout/routing pass;
- the KiCad nightly CLI aborts with status 134 on this inherited project, so
  GUI DRC is the gate until that tooling issue is resolved;
- baseline ERC has three inherited `power_pin_not_driven` errors and 76 total
  findings; r1.2 must not add new electrical errors.

Three deterministic fanout experiments were rejected rather than promoted:

1. front/outward, contact `n = Pi n`: 395 violations, 14 opens;
2. front/outward with reversed contact assignment: 296 violations, 1 open,
   but it breaks the carrier's `n = Pi n` contract without a proven 1-to-40
   crossover interconnect;
3. bottom/mirrored/outward, contact `n = Pi n`: 445+ violations, 7 opens.

The safe successor is **r1.3**, using the exact FH41 bottom/mirrored at the top
edge, four copper layers, and a native interactive reroute.  It must preserve
contact `n = Pi n`; recommended planes are In1.GND and In2 power/slow signals.
No scripted direct-fanout copper from the experiments is retained.

No Gerbers, CPL, BOM, fab archive, or shopping-cart upload is authorized from
this folder until those gates are closed.  The shield and retention pads 41-50
are tied to GND on the PCB; signal contacts 1-40 are the documented interface.

## Reproduction

The two scripts in `scripts/` use KiCad's official IPC API rather than editing
project internals:

- `scripts/koyomi_ffc_r12_schematic.py`
- `scripts/koyomi_ffc_r12_board.py`

The board script imports an Eeschema netlist by reference, places `JFFC1`, ties
its shield pads to GND, and updates the revision silkscreen.

The donor project originated with Exentio's Project Koyomi and is the circuit
manufactured for the earlier five-board run.  Only this new FFC conversion is
being treated as an interface-only, unrouted revision.
