# GPIO LCD bench adapter A2 — B2.25 numbered interface

This Raspberry Pi GPIO addon drives the separately updated LCD/Combined
peripheral C1 board. It preserves A1 in `../gpio-breakout`. Its 40-contact Samtec
interface follows the corrected B2.25 allocation; historical Hirose LCD boards
are incompatible.

**Qualification corrections implemented; not fabrication released.** The saved
JLC stackup, power widths, J1 paste, USB contact routing and startup circuit are
corrected. Six Pi-side display resistor arrays provide tuning options. Native
DRC has **0 errors/0 opens** and ERC has **0 active errors**. Hardware USB/power,
display and installed cable qualification remain open. See the
[current review and exact source hashes](reports/qualification-fixes.md) and
[bench procedure](reports/bench-qualification-plan.md).

## Interface and use

J1 is **Samtec ZF5S-40-01-T-WT-K-TR/C3169111**. USB uses VBUS pins 1–4,
D−6 and D+7; grounds are 5/8. LCD power and GPIO use pins 9–40. All 40 numbered
functions are preserved. [Pinout](interface-pinout.csv) lists physical Pi header
pins and the updated power/series-element paths. The native comparison is in
[interface-audit.json](reports/interface-audit.json).

J3 is **Molex 1054500101/C134092**. Connect a normal USB-A-to-C cable from the Pi
host port; the GPIO header itself does not carry USB. This is USB2 pass-through
with protection, not a hub. Both CC contacts have independent 5.1 kΩ pulldowns.
TPD2EUSB30 arrays protect data and CC; no whole-board ESD compliance is claimed.

RN1–RN6 insert one isolated **0 Ω** element on each of GPIO0–21, with GPIO0/1
named ID_SD/ID_SC. Their six four-element arrays are `4D03WGJ0000T5E/C1952`.
Select nonzero source values only after confirming the Pi/display timing and
coordinating C1's receiver-side resistor banks. Software must select the
corresponding alternate functions and display mode.

## Power and assembly

- Scope is **low-power USB2 bench use**. Full downstream USB-A load capacity
  is not provided. The 0.5 A PTC is not a precise current limit.
- USB VBUS passes through F2, TPS22918DBVR/C131941 and the existing LM66100
  reverse blocker. A 10 nF CT capacitor targets a typical 26.55 ms 10–90% rise
  at 5 V. QOD is unconnected. Actual startup current, host droop and load voltage
  still require measurements; this circuit does not implement USB enumeration.
- **JP4 (5 V) and JP5 (3.3 V) default OPEN.** Close only when the Pi is the sole
  source of those LCD supplies. Keep open for independently powered LCD
  electronics; closed links are not automatic reverse-current protection.
  JP4 includes F1, the retained 0.5 A PTC. USB supply remains separate.
- J2 is a hand-fit 2×20 Pi header/stacking socket. No particular stacking socket
  or Pi mechanical fit has been qualified. Pin 1 is marked. TP4/GND and
  TP5/Pi3V3 remain.
- J1's 42 pads include paste. C1's latest J401 also has 42 paste-enabled pads;
  the earlier peer paste finding is closed. Stencil and exact-part sourcing
  belong in the eventual gated fabrication package.

## Verification and limits

The 63.5×32 mm board has 27 footprints. All 193 numbered pads match the native
schematic XML and all 40 interface functions match. Native DRC retains 13
library snapshot warnings; ERC retains 25 library snapshot differences and
four intentionally unused Pi GPIO label warnings. The previous exact
TI-documented ST-to-ground exclusion remains; no global rule was weakened.

The saved four-layer JLC04161H-7628 construction is verified. Main USB pair
width/gap remains 0.2774/0.20 mm; minimum track width is 0.20 mm, ordinary via
drills are 0.30 mm. B6/B7 planar branches shortened to 1.588/4.312 mm, but B7
has two transitions while B6 has none. Coplanar ground is interrupted. These
geometry results do not qualify uniform impedance or the assembled channel.

[Current top](renders/qualification-fixes-top.png),
[USB-entry side](renders/qualification-fixes-right.png) and
[native schematic](renders/schematic/gpio_breakout.svg) reflect the final sources.
J1 is still a nominal envelope, not detailed Samtec CAD. J2 has no chosen socket
model. J3 uses the unmodified official Molex STEP with its mouth facing outward
at X113.55 mm, 0.05 mm past the board edge; plug-shroud clearance needs checking.

The catalog cable candidate is
[Samtec FJH-40-R-03.00-4](https://www.samtec.com/products/fjh-40-r-03.00-4),
76.2 mm. Both connectors match its manufacturer mating family, but installed
contact faces, pin-one arrangement, length and latch/fold clearance remain
unverified. Custom harnesses and repinning are prohibited. Physical continuity
is a TODO after cable selection and is not the sole release blocker.

## Reproduction and release

All native edits and checks are instrumented. Sources, current reports and
renders are hash-bound in the telemetry artifact manifest. Tools under `tools/`
are audited sequential revision steps, not a single idempotent generator.
Do not rerun historical netlist import/routing on the completed board. Use the
pinned September 5 KiCad CLI through `KICAD_CLI`; see
[the runtime record](reports/runtime-and-review.md). No shared installation was
modified. Standard package models were copied into project-relative paths.

The authoritative `gpio-breakout-a2` contract in
[private interconnect PR34](https://github.com/TensorFleet/vaio_p_modding/pull/34)
retains the hardware and installed-cable qualification hold. No Gerbers, drill,
BOM, CPL or JLC upload were produced during these corrections. Before any
fabrication generation, run `scripts/check_interconnect_release.py --board
gpio-breakout-a2` in that repository; it must pass. Older reports are historical
when their source hashes differ from the current review.
