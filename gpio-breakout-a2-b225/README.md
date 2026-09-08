# GPIO LCD bench adapter A2 — B2.25 numbered interface

This is the Raspberry Pi 40-pin GPIO addon that drives a separately updated LCD
board. It preserves the original A1 in `../gpio-breakout` and does not edit any
LCD driver or combined-peripheral revision. It is **not a carrier-to-carrier
adapter**, and it is not compatible with the old Hirose LCD board.

J1 is **Samtec ZF5S-40-01-T-WT-K-TR (C3169111)**. Its numbered contacts follow
the corrected B2.25 interface: LCD power and GPIO use pins 9–40; ground contacts
5 and 8 also connect to ground. The new USB-C input J3 connects USB supply
1–4, D−6 and D+7. Connect a normal USB-A-to-C cable from the Pi USB host
port to J3; the Pi GPIO header itself does not carry USB. This is a passive
USB2 pass-through with protection, not a USB hub or controller.

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

## USB input and power isolation

J3 is Molex 1054500101/C134092. Its A6/B6 contacts join D+, A7/B7 join D−;
SuperSpeed and SBU contacts are unused. Each CC contact has its own 5.1kΩ
pulldown. U2 and U3 are TPD2EUSB30DRTR/C97502 arrays for D± and CC1/CC2.
The shell and grounds connect to the common ground plane. No whole-board ESD
compliance claim is made.

USB VBUS passes through F2 (SMD1206P050TF/15/C106264, 0.5 A PTC), then
U1 (LM66100DCKR/C2869734). CE is tied to VOUT for reverse-current blocking;
unused ST is grounded as directed by TI. USB_VBUS never joins LCD5V or
Pi3V3. Local bypass is 1µF before U1 and 100nF after it; total downstream
capacitance, USB enumeration/inrush and the LCD peer load still need review.

The [PTTC fuse datasheet](https://www.pttc.com.tw/files/Products/OCP/PPTC/SMD/file/Data%20Sheet%20for%20SMD1206%20Series%20(Rev.%20L).pdf)
gives Rmin 0.150 Ω and R1max 0.750 Ω at 23°C one hour after reflow/trip; R1max
is not a hot maximum. At 500mA that upper post-reflow resistance drops 375mV,
or 75mV at 100mA, before U1, cable and copper losses. This is not a promise
of 500mA usable at the FFC, nor authorization to draw 500mA before enumeration.
See [TI LM66100](https://www.ti.com/lit/ds/symlink/lm66100.pdf) and
[TI TPD2EUSB30](https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf).

## Verification and release state

The 63.5×32mm four-layer source is fully routed. Native KiCad DRC reports
**0 errors and 0 opens**, with six visible library-snapshot mismatch warnings.
The native pin-map audit matches all 40 connected FFC contacts and every new
USB component pad. ERC has 0 active errors and 21 warnings (17 embedded
library snapshot differences and four intentionally unused Pi GPIO labels).
One precise ST-to-GND/PWR_FLAG finding is excluded with the TI datasheet
rationale; its raw finding remains in `reports/usb2-erc-before-targeted-exclusion.json`.
No global electrical-rule matrix setting was weakened. Independent XML review checked 42 USB pins and preserved
all 82 prior connected pins. The native preservation comparison confirms all
nine original footprint geometries/placements and 1,137 original tracks/vias;
only J1's six previously-unused USB contacts gain assignments. Native child
item IDs and session parent IDs are normalized in this comparison.

The main D± pair follows a shared centreline at 0.2774mm width/0.20mm gap,
opening briefly around the ESD ground pad. Connector A-contact paths are
22.441/21.139mm (1.302mm planar skew), with no layer transitions. The B-contact
joins are 28.090/29.885mm (1.795mm planar skew), with two regular through-vias
on each line and short In2.Cu sections. Every data transition has a ground
return via within 1.65mm. All 698 F.Cu reference samples lie over In1.Cu ground, and all 102 In2.Cu
samples lie over B.Cu ground, outside measured data-via antipads (0.500mm
radius plus 0.001mm polygon tolerance). These are geometric measurements, not USB compliance
or impedance certification; see [USB path audit](reports/usb2-path-audit.json).

Tracks remain at least 0.20mm; regular through-vias use 0.50mm copper/0.30mm
drills. There are no via-in-pad requirements and no fabrication files here.

**Native stackup update is pending.** The saved PCB still contains the inherited
generic 0.48/0.48/0.48mm dielectric stack. The selected future manufacturing
stack is **JLC04161H-7628**, four layers, nominal
1.6mm: outer 35 µm/inner 15.2 µm copper, 0.2104 mm outer dielectrics (Er 4.4),
1.065mm central core (Er 4.6). The official JLC coplanar differential calculator
returns 0.2774mm width for 90Ω with 0.20mm pair gap and 0.25mm side-ground gap.
See [calculator inputs and limits](reports/usb2-impedance-calculator.md).
Actual same-layer ground is present at 283/337 sampled locations beside the
main pair; connector breakouts and bends interrupt it. The short ESD/contact
escapes remain 0.20mm wide. The 0.2774mm geometry was selected for that future stack; it does not make
the currently saved generic stack 90Ω. The calculator is process-reference
evidence only, not a claim of uniform 90Ω or a qualified assembled USB link.
The pinned native IPC stackup setter is unimplemented, and the available
GUI selector could not isolate this addon from an unrelated unsaved board.
That other board was not modified. Apply the selected stack in a supported
native editor and rerun source/model/reference audits before fabrication.

**Not fabrication released.** The `gpio-breakout-a2` interconnect entry in
[contract PR34](https://github.com/TensorFleet/vaio_p_modding/pull/34) remains
blocked until the native stackup is updated, C1 routing/release checks close, and the catalog cable assembly and mechanical/model qualification are verified.

The user selected **Combined peripheral C1 J401** as the endpoint on 2026-09-09. Fresh schematic exports confirm the same Samtec ZF5S-40-01-T-WT-K-TR connector value and all 40 numbered functions match GPIO A2 without repinning. A further native C1 PCB load timed out; no fresh two-board PCB pass is claimed. The inherited cable candidate is [Samtec FJH-40-R-03.00-4](https://www.samtec.com/products/fjh-40-r-03.00-4), 76.2 mm. Installed length, contact-face/fold arrangement and clearance remain to be verified.
Physical cable continuity is a TODO after the cable choice; it is not the sole
release blocker. A clean PCB DRC is not proof of assembled LCD compatibility.

## Manufacturing findings follow-up

The selected scope is **low-power USB2 bench use**. F2 remains 0.5 A; the combined board's full downstream USB-A load is outside this scope. Hold current is not a precise current limit, and assembled current/voltage drop and inrush remain unqualified.

J1's missing paste layer is repaired on all 42 pads in the board and local library, and its description now names Samtec. Copper and all numbered connections are unchanged; DRC remains zero errors/zero opens with six existing library warnings. See [the eight-finding review](reports/manufacturing-findings-review.md) for the source evidence, stencil-thickness discrepancy, shared-footprint propagation work, and remaining power, termination, USB and stackup issues. These repairs do not authorize fabrication.

## Renders and model limits

[Top](renders/top.png), [USB-entry side](renders/right.png) and [FFC-entry side](renders/back.png) come from the authoritative
KiCad PCB. **J1 is only the inherited conservative envelope, not a detailed
Samtec model.** F2 has no 3D body in these renders; its pads and placement are present in the PCB. U1/U2/U3 use standard package models. J1’s intended cable-entry edge is the top board edge, Y50 mm,
with the tail row at Y55.23 mm and footprint rotation 180°. The envelope cannot
prove latch, contact, cable or housing alignment. See
[edge-connector-orientations.json](edge-connector-orientations.json).

On 2026-09-08 the [official exact-part page](https://www.samtec.com/products/zf5s-40-01-t-wt-k-tr)
required an email address and privacy-consent submission for instant model
downloads. No contact details were submitted, so vendor CAD remains pending.
The official page identifies FJH as the mating cable family; this does not select
a length, contact-side configuration or particular assembly for the new LCD.

J3 uses the unmodified official Molex STEP, SHA-256
`c70f02e35f4d3711f1b93e4e19d07a87fd4d6e9f06c242bb5558372dcba5b0ad`.
The native feature audit checks 26 solder feet against 24 pads and all four shell
legs against their slots. The right-facing mouth is at X113.55mm against the
board edge X113.50mm: only 0.05mm overhang. Plug-shroud/enclosure clearance
needs separate mechanical review; the carrier board overhang claim does not
apply to this addon. See [model audit](reports/usb2-model-audit.json).

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

The USB extension scripts under `tools/` are recorded native revision steps.
The netlist importer duplicated three custom footprints; the original native
footprints were restored from commit 07f30a4 and all nine originals compared.
Do not rerun the import or historical routing steps on a finished board.
