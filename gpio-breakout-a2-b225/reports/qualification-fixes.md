# GPIO A2 qualification corrections — 2026-09-09

The desktop design corrections are implemented. **This is not a fabrication
release or a record of completed hardware qualification.** Scope remains
low-power USB2 bench use with the user-selected Combined peripheral C1.

## Final sources and checks

- PCB SHA-256: `fc25e04aed25fc0094d64c32bc30104b626fe1165ffbb7e90a8c57916ff2e60d`.
- Schematic SHA-256: `318696ff14d9f45b238c8337d1508b61577e4c56837971118e5ead9886f4fc65`.
- Native DRC: **0 errors, 0 opens, 13 library snapshot warnings**.
- Native ERC: **0 active errors, 29 warnings**: 25 library snapshot differences
  and four intentionally unused Pi GPIO labels. The existing exact TI-documented
  ST-to-ground exclusion is retained; no electrical-rule matrix was weakened.
- Independent XML/native pad comparison: all **193 numbered pads** and all
  **40 FFC functions** match. J1 retains solder paste on all 42 pads.
- 27 unique footprints; 1,908 tracks and 124 vias. Nine parts were added.
- Native preservation comparison retains J1/J2/J3 geometry, all original
  component geometries except the intentionally moved bypass C1, and all 406
  original tracks outside the modified display/power/USB nets.
- The previously corrected JLC04161H-7628 construction is unchanged: outer
  copper 35 µm, inner 15.2 µm, outer dielectrics 0.2104 mm/Er 4.4, core
  1.065 mm/Er 4.6. New startup power routes have another 80 widened segments,
  up to 0.50 mm where clearance permits; three screened segments remain narrower.

Authoritative reports: [interface](qualification-interface.json),
[preservation](qualification-fixes-preservation.json),
[DRC](qualification-fixes-drc.json), [ERC](qualification-fixes-erc.json),
[native snapshot](qualification-native-snapshot.json),
[schematic XML](qualification-netlist.xml).

## USB B-contact routing

B6/B7 planar junction-to-contact branches are now **1.588/4.312 mm**, formerly
6.678/9.776 mm. The main 0.2774 mm / 0.20 mm pair is preserved. B6 stays on
F.Cu; B7 retains two through-vias and an In2.Cu segment. A-contact planar skew
is 1.302 mm; B-contact planar skew is 0.393 mm. **The B pair has unequal via
counts (0 versus 2), so planar skew alone is not electrical delay matching.**

At the saved F-to-In2 centre separation of 1.3157 mm, the two transitions add
about 2.6314 mm of vertical conductor on B7. Its full geometric branch is about
6.944 mm; this is not a claim that the whole branch meets TI's 200 mil stub
recommendation. The corresponding simple B-path length mismatch is about
3.024 mm before dielectric propagation and discontinuities are considered.

All 700 F.Cu-to-In1.Cu and 25 In2.Cu-to-B.Cu ground-reference samples pass
outside measured antipads. Return vias are 1.768 and 2.035 mm from the two data
vias. Coplanar ground remains interrupted at breakouts and bends. Thus the
routing is shorter, but uniform 90 ohm impedance and the assembled USB channel
remain unqualified. Test both plug orientations. [Native path audit](usb2-path-audit.json).

## Controlled USB startup

The USB supply path is now J3 → F2 0.5 A PTC → **U4 TPS22918DBVR/C131941** →
U1 LM66100 reverse blocker → FFC pins 1–4. U4 is before the existing reverse
blocker so its body path does not replace that protection. ON is tied to VIN;
QOD is unconnected. C3 is **10 nF C0G 50 V 5%, C76599** on CT. C4 adds 1 µF
on the switched rail. The LCD5V/3V3 links remain separate and default-open.

[TI's TPS22918 datasheet](https://www.ti.com/lit/ds/symlink/tps22918.pdf)
gives a typical 26.55 ms 10–90% rise at 5 V with this CT value. For the peer's
nominal 120.2 µF this implies about 18.1 mA mean capacitor charging current in
that interval, excluding operating load. It is not a guaranteed peak limit or
proof of USB host allocation compliance. Measure actual current, host droop,
reset/startup and externally powered peer behavior.

At 60°C the sampled positive copper path estimate is 0.0899 Ω. Including the
PTC's 0.75 Ω upper post-reflow value gives 84/210/420 mV at 100/250/500 mA,
**before** U4, U1, USB cable, FFC, contact, return and peer losses. F2 is not a
precision limiter. This update does not provide full downstream USB-A power.
[Power estimates and exclusions](power-path-qualification.json).

## Pi-side display provisions

RN1–RN6 are six isolated four-element 0603 arrays, initially **0 Ω**
(`4D03WGJ0000T5E`, C1952). Exactly 22 Pi outputs, GPIO0–21 (0/1 named
ID_SD/ID_SC), pass through one element each. Two unused elements remain NC.
The Pi header-to-resistor planar runs measure 3.066–10.872 mm. Total planar
header-to-FFC runs through the arrays measure 26.242–72.024 mm.

These are source-side tuning provisions, not qualified termination values.
The exact Pi, drive setting, panel and pixel clock still need confirmation.
Historical project settings suggest 83.6 MHz RGB666 1600×768, but are not
confirmed for this setup. Coordinate any nonzero source population with C1's
existing receiver-side 47 Ω arrays. Measure receiving setup/hold and ringing.
[DPI topology and path audit](dpi-qualification.json).

## C1 and mechanical status

C1 commit `00c6e73d` now enables paste on **all 42 J401 pads**. Its source-bound
preflight reports zero geometry errors, opens and schematic parity findings;
this closes the earlier missing-paste finding. The native connector read binds
PCB SHA-256 `1bbc9a6f8cb5cf28cb54341c03c1d5cdff20cfe000a83fd909f164c52de66f84`.
All 40 numbered functions still correspond to GPIO A2.
[C1 connector evidence](c1-paste-current.json). C1 was inspected, not edited.

Both ends specify Samtec ZF5S-40-01-T-WT-K-TR. Samtec lists FJH as the mating
family; the existing catalog candidate is FJH-40-R-03.00-4, 76.2 mm. Manufacturer
family compatibility does not prove installed contact-face orientation, length,
latch access or fold clearance. Verify these with the actual selected assembly.
Physical continuity is a TODO after cable selection, not the sole release
blocker. No custom harness or repinning is permitted.

[Native top](../renders/qualification-fixes-top.png) and
[USB-entry side](../renders/qualification-fixes-right.png) were inspected at the
final PCB hash. New components use standard package models. J1 remains a nominal
Samtec envelope and J2 has no selected stacking-socket model; neither proves fit.
J3's exact official Molex model and placement are unchanged. Its mouth overhang
is only 0.05 mm, requiring plug-shroud clearance in the intended installation.
[Native schematic preview](../renders/schematic/gpio_breakout.svg).

## Remaining qualification and artifact scope

Follow the [bench procedure](bench-qualification-plan.md) for the actual
host/display/peer/cable combination. Record measured USB startup and supply
behavior, both USB-C orientations, and display timing. Confirm the catalog
cable's installed geometry. These checks are not replaced by DRC or calculations.

The authoritative interconnect contract retains a manufacturing hold with these
current reasons. No fabrication files were generated and nothing was uploaded
to JLCPCB. Files named `qualification-route-pass`, `qualification-placement`,
`qualification-updated-netlist`, `qualification-board-import`, `startup-routing`,
`startup-width-qualification` and `usb2-short-joins` are intermediate revision
records; use final hashes/reports above for the current board. Earlier stackup
and USB reports are historical where their hashes differ.

All KiCad edits, failed retries, audits and renders are instrumented in the
`20260909T082142-4e01c546` telemetry run. These scripts are sequential revision
steps, not an idempotent whole-board generator; do not rerun the historical
netlist importer on the finished board. Native import duplicated three custom
footprints; their original geometries were restored and all 27 final references
and schematic paths were checked. Local symbol graphics and absolute pin
coordinates are handled separately in the final schematic cleanup.
