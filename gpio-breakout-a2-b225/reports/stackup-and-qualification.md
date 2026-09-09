> Historical stackup-stage record. The [later qualification corrections](qualification-fixes.md) supersede its USB, startup, display-array and C1 paste status.

# GPIO A2 stackup correction and qualification

2026-09-09. **Stackup correction and power-width improvements verified; manufacturing qualification remains blocked.** Scope: low-power USB2 bench use, with C1 as the LCD/USB peer. No fabrication files or JLCPCB upload were produced.

Source PCB SHA-256: `6df373e8b229327e0325547ae18f7e711fa34f61f5d1cccadf840d49595d9113`.
Schematic SHA-256: `7d6f4f5814031e3394d59b90022250afa140a6cd729119d2978a34c2cbb0e7e7` (unchanged).

## Corrections verified

The editable PCB now uses JLC04161H-7628: 35/15.2/15.2/35 µm copper, 0.2104/1.065/0.2104 mm dielectric, and dielectric constants 4.4/4.6/4.4. The outer layers are prepreg and the middle layer is core. Impedance control is enabled. Values were rechecked against [JLC's published construction](https://jlcpcb.com/impedance) and read back through native KiCad.

Solder-mask permittivity is 3.8. KiCad's flat layer approximation uses the published 15.24 µm thickness above traces; JLC specifies 30.48 µm above substrate and between traces. The copper/dielectric sum is 1.5862 mm; adding the flat mask approximation gives 1.61668 mm. Order by **nominal 1.6 mm and named JLC stack**, not by requesting 1.61668 mm fabrication. The inherited loss tangent of 0.02 is not a measured material model. The native stack now matches the calculator inputs, but this alone cannot qualify the whole channel at 90 Ω.

293 existing power segments were widened to 0.25–0.50 mm according to available clearance; most unrestricted runs use 0.50 mm. Narrow fanouts remain, including roughly 10 mm FFC escapes on the 5 V and 3.3 V rails. No signal routes, connector placements, pad geometry, net assignments, or schematic connections changed. All 1,353 tracks, 74 vias, 18 footprints and four zone definitions remain. Three ground fills were regenerated for the new clearances.

KiCad converted the inherited thermal default on JP4/JP5's four custom pads from 45° to 90°. Native setter round-trip attempts did not restore it. The audit permits only these four exact changes after confirming none of their nets has a copper zone; no thermal connection exists there to change. The project file also gained native version metadata/default rule entries. No electrical rule was weakened.

See [native stack and preservation checks](stackup-qualification.json), [width changes](power-width-qualification.json) and [independent pin checks](qualification-interface.json).

## Check results

| Check | Result |
| --- | --- |
| Saved JLC copper/dielectrics/mask inputs | PASS |
| Expected changes only | PASS, including the explicitly checked thermal-default conversion and zone refills |
| Native DRC, pinned September 5 build | 0 errors, 0 opens; 6 library snapshot warnings |
| Native ERC, pinned build | 0 active errors; 21 existing warnings; the prior exact unused-ST exclusion is unchanged |
| Schematic/PCB parity | All 135 numbered board pads pass; all 40 FFC functions pass |
| J1 paste | All 42 GPIO connector pads have paste |
| USB reference ground | 698/698 F.Cu-to-In1 and 102/102 In2-to-B samples covered outside transition antipads |
| USB full channel | NOT QUALIFIED: branch length, discontinuities and complete peer/cable channel remain |
| Power | Positive-conductor DC model completed; full assembled budget and inrush NOT QUALIFIED |
| DPI | All 22 driven lines connected; source termination and receiver timing NOT QUALIFIED |
| Mechanical mating | USB opening remains outward; Samtec detailed model and installed catalog cable fit remain open |

The development-build cross-check also reported zero electrical/geometry errors, but 9 DRC and 43 ERC library/configuration warnings because its standard libraries were not enabled. Both raw reports are retained; the pinned results above use the established library environment.

## Remaining electrical work

**USB branches:** actual junction-to-contact planar branches are A6/A7 ≈1.03 mm, B6 **6.678 mm**, and B7 **9.776 mm**; each B branch also uses two through-vias. These are actual branch lengths, not A/B endpoint-length subtraction. They exceed the 200 mil (5.08 mm) stub recommendation in [TI's USB2 layout guide](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/171/USB-2.0-Board-Design-and-Layout-Guidelines.pdf). This is a design-screen failure, not a measured USB compliance failure. Rework the reversible-contact joins or select a qualified footprint/connector solution, then recheck clearance, pairing, ground return and total channel. No routing change to the data pair is claimed in this correction. Main-path skews remain 1.302 mm (A) and 1.795 mm (B). Coplanar ground is present at only 283/337 main-pair samples, so the calculator result is not a uniform impedance guarantee.

**Voltage drop:** the widened USB positive copper path has a conservative single-path estimate of 0.0627 Ω at 60 °C, assuming 20 µm via plating. Parallel copper is ignored. Including the review's 0.75 Ω PTC resistance screen gives about 0.081 V at 100 mA, 0.203 V at 250 mA, or 0.406 V at 500 mA, **before** ideal diode, connectors, cables, ground return and C1 losses. These are calculation scenarios, not supported current ratings. F2 remains 0.5 A hold and is not a regulated limiter. The actual host/load and minimum receiver voltage must close the budget. See [power-path calculation](power-path-qualification.json).

**Inrush:** C1's prior schematic audit identifies 120.2 µF directly on its downstream USB rail. The C1 schematics remain unchanged. Charging that nominal capacitance to 5 V requires 601 µC; a 1 ms rise implies 0.601 A average capacitor current, plus operating load. The [LM66100](https://www.ti.com/lit/ds/symlink/lm66100.pdf) provides reverse blocking, not an adjustable current-limited charging ramp. Add controlled inrush charging or qualify plug-in current and host droop with the actual assembled load. Low steady-state load does not eliminate this issue. No scope measurement was available.

**DPI:** all 22 driven paths were traced from J2 to J1. There are still no source-side series components; C1's 47 Ω arrays are at the receiver. The Pi model, drive settings and panel mode/pixel clock have been requested. Source-side resistor provisions and their fitted values still need implementation/verification against those assumptions; 0 Ω options alone would not establish termination. The [Raspberry Pi DPI guide](https://pip.raspberrypi.com/categories/685-app-notes-guides-pcns-whitepapers/documents/RP-003471-WP/Using-a-DPI-display.pdf) establishes the configurable interface, not this cable's timing margin. See [DPI qualification record](dpi-qualification.json). No resistor arrays were added by this correction.

## Peer and assembly limits

C1 advanced to commit `ce6f1d0d` during this review. Its current J401 footprint was read natively, and all 40 contacts still match the unchanged C1 schematic export and GPIO functions. **C1 J401 has zero paste-enabled pads**, so its copy of the Samtec footprint still needs the solder-paste repair. C1's prior full-board manufacturing status refers to an older PCB hash and is not a fresh approval of its latest board. C1 source files were not edited here.

J1 on GPIO remains a nominal envelope, not a detailed manufacturer model. The official Samtec FJH-40-R-03.00-4 catalog cable remains the candidate; installed contact faces, available length and fold clearance require confirmation. Physical continuity is a TODO after the cable choice and is not, by itself, a release blocker. Custom harnesses remain prohibited. Samtec's stencil drawing specifies 0.15 mm while its product specification says 0.13 mm; the assembler must resolve that process discrepancy. GPIO paste apertures themselves are 1:1.

[Current top view](../renders/qualification-top.png) and [USB entry view](../renders/qualification-right.png) are native KiCad renders. J3 opens outward. F1/F2 have no body model in the top view; J1 is only an envelope. Renders do not close Samtec latch/cable or chassis fit qualification.
