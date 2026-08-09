# Koyomi FFC r1.2 verification

Date: 2026-08-09

## Interface

- `J1` is absent from the schematic and PCB.
- `JFFC1` is present in both with 40 signal contacts.
- Netlist export contains exactly 40 `JFFC1` nodes.
- FFC pin number equals Raspberry Pi physical header pin number for all 1-40.
- PCB shield/retention pads 41-50 are all assigned to GND.
- Connector instance: x = 123.500 mm, y = 25.200 mm, rotation = 0 degrees.
- The system contract is carrier contact `n` -> LCD contact `n` -> Pi physical
  pin `n`.  Cable marketing type is not accepted as proof; verify `1 -> 1` and
  `40 -> 40` in the installed geometry before power-on.

## Mechanical/source checks

- Board outline: 65.0000 x 56.5000 mm.
- Stackup: 1.6000 mm, two copper layers.
- Minimum drill: 0.4000 mm.
- The exact shared FH41 STEP model appears in the top and side renders.
- Top, bottom, and side renders were generated from the `.kicad_pcb` source.

## ERC

Command:

```text
kicad-cli sch erc --severity-all --format report ...
```

Result: 77 findings = 3 errors + 74 warnings.  The donor baseline was 76
findings with the same 3 `power_pin_not_driven` errors.  The one added warning
is an explicit `lib_symbol_mismatch` because the embedded connector symbol keeps
the donor header's pin placement/names while pointing to the shared FH41 library
symbol.  There are no new ERC errors.

## PCB DRC gate

The bundled KiCad 10.99 CLI aborts with status 134 while starting PCB DRC on
the inherited project.  Nightly GUI DRC is therefore the current gate.

Stable KiCad reports 301 pads, 112 vias, 608 track segments, 96 nets, and **0
unrouted** on the post-order donor.  The previous "96 unrouted" statement was
a status-bar misread.  Nightly GUI DRC on the checked-in r1.2 floorplan reports
122 violations and 37 unconnected items; see `drc-floorplan-gui.rpt`.

Rejected routing experiments (none of their copper is checked in):

| Placement/mapping | Violations | Opens | Decision |
| --- | ---: | ---: | --- |
| Front/outward, contact `n = Pi n` | 395 | 14 | crossing/shorting fanout |
| Front/outward, reverse mapped | 296 | 1 | violates carrier contract without proven 1-to-40 cable |
| Bottom/mirrored/outward, contact `n = Pi n` | 445+ | 7 | dense B.Cu donor fanout still crosses |

The required successor is r1.3: exact FH41 bottom/mirrored at the top edge,
four copper layers, In1.GND, In2 power/slow routing, and a native interactive
fanout.  Contact `n = Pi n` remains mandatory.

The donor source is `hardware/koyomi-lvds-hat/` and includes commit `2119f6a`'s
FL1/FL2 solder-mask fix.  The exact five-board fabrication Gerbers remain in
`hardware/koyomi-lvds-hat/gerbers/` and predate that source fix.  Source-level
findings above must not be retroactively attributed to that Gerber package.

## Release status

Closed.  Do not generate or upload fabrication files from r1.2 until:

1. The r1.3 JFFC1 fanout is natively routed with contact `n = Pi n`.
2. PCB DRC runs to completion in a compatible KiCad build and has no unwaived
   violations.
3. The final installed board orientation and cable are mechanically verified,
   including continuity checks `1 -> 1` and `40 -> 40`.
4. The carrier port is used for either the LCD board or GPIO breakout, not both.
