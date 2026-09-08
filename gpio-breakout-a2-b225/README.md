# GPIO LCD bench adapter A2 — B2.25 numbered interface

This is the Raspberry Pi 40-pin GPIO addon that drives a separately updated LCD
board. It preserves the original A1 in `../gpio-breakout` and does not edit any
LCD driver or combined-peripheral revision. It is **not a carrier-to-carrier
adapter**, and it is not compatible with the old Hirose LCD board.

J1 is **Samtec ZF5S-40-01-T-WT-K-TR (C3169111)**. Its numbered contacts follow
the corrected B2.25 interface: LCD power and GPIO use pins 9–40; ground contacts
5 and 8 also connect to ground. USB supply 1–4 and data 6/7 are deliberately
unconnected. No USB cable input or USB supply is needed for this LCD-only use.

Use [interface-pinout.csv](interface-pinout.csv) as the exact handoff for the
separate LCD update. It lists **physical Pi header pin numbers**, not BCM numbers.
GPIO identity is preserved: FFC13→Pi16/GPIO23,14→Pi18/GPIO24,
15→Pi28/ID_SC,16→Pi3/GPIO2,17→Pi5/GPIO3,19→Pi27/ID_SD.
The remaining RGB lines use GPIO4–21 as listed in the CSV. Configure the Pi
software for the matching display timing and GPIO alternate functions; no
firmware or display-channel performance claim is made by the PCB checks.

## Power and assembly

- **JP4 (5V) and JP5 (3V3) are OPEN by default.** Close them only when the Pi
  is the sole source powering the LCD chain. Keep them open for independently
  powered LCD electronics. The jumpers isolate power when open; they are not
  automatic reverse-current protection when closed. Never connect two powered
  sources through closed links.
- JP4 feeds F1, the retained 0.5 A PTC, then FFC9/10. JP5 feeds FFC11.
  Backlight power and load qualification remain outside this adapter.
- J2 remains a hand-fit Pi 2×20 header/stacking socket. The rendered pin header
  is an existing library visualization, not a qualification of a particular
  stacking socket or Pi mechanical fit. Pin1 is marked.
- A1's ID0/ID1/INS jumpers and test points were removed because those functions
  are not assigned to these B2.25 contacts. TP4/GND and TP5/Pi3V3 remain.

## Verification and release state

The 63.5 ×32 mm four-layer source is fully routed. Native KiCad DRC reports
**0 violations and 0 opens**, including the refilled ground planes. ERC reports
**0 errors, 7 warnings**: four intentionally unused Pi GPIO labels and three
embedded symbol/library snapshot differences. No warning was newly waived.
The independent native netlist/PCB audit matches all 40 contacts (34 connected,
6 explicitly unused), verifies the Pi and power paths, and binds source hashes.
Tracks are at least 0.20 mm; regular through vias have 0.50 mm copper and 0.30 mm
drills. There are no via-in-pad requirements and no fabrication files here.

**Not fabrication released.** The `gpio-breakout-a2` interconnect entry in
[contract PR34](https://github.com/TensorFleet/vaio_p_modding/pull/34) remains
blocked until the separate LCD endpoint exists, an exact catalog cable assembly
and one-to-one pin order are audited, and mechanical/model qualification closes.
Physical cable continuity is a TODO after the cable choice; it is not the sole
release blocker. A clean PCB DRC is not proof of assembled LCD compatibility.

## Renders and model limits

[Top](renders/top.png) and [cable-entry side](renders/back.png) come from the authoritative
KiCad PCB. **J1 is only the inherited conservative envelope, not a detailed
Samtec model.** Its intended cable-entry edge is the top board edge, Y50 mm,
with the tail row at Y55.23 mm and footprint rotation180°. The envelope cannot
prove latch, contact, cable or housing alignment. See
[edge-connector-orientations.json](edge-connector-orientations.json).

On 2026-09-08 the [official exact-part page](https://www.samtec.com/products/zf5s-40-01-t-wt-k-tr)
required an email address and privacy-consent submission for instant model
downloads. No contact details were submitted, so vendor CAD remains pending.
The official page identifies FJH as the mating cable family; this does not select
a length, contact-side configuration or particular assembly for the new LCD.

## Reproducibility

All PCB/schematic edits used native KiCad IPC; the schematic title was updated
in KiCad Page Settings. `tools/update_addon_ipc.py` migrates an untouched A1
copy using the corrected B2.25 donor named by `B225_SOURCE`; subsequent scripts
record the routed candidate, remaining-via closures, cleanup and audits.
These are audited revision steps, not a fabrication generator or a single
idempotent rebuild command. Failed route attempts were rejected by native DRC.
`reports/telemetry` records the successful and failed phases and final hashes.

Runtime recovery used an **isolated** copy of KiCad Python bindings, generated
from the existing `/private/tmp/b225-native-proto` with its pinned protoc.
The Sept5 schematic server needed that matching protocol; the parity PCB CLI
used restored local protobuf/Abseil libraries. No shared installation or system
package was modified. See `reports/runtime-and-review.md` for exact paths.
