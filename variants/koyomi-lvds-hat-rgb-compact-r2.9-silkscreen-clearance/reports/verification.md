# R2.9 source verification

Verified 2026-08-21 with the KiCad 10.99.0 nightly matching the board format.

- Errors-only PCB DRC: 0 violations, 0 unconnected pads.
- Errors-only schematic ERC: 0 errors, 0 warnings.
- Silkscreen clipped by solder-mask openings: 0.
- Silkscreen clipped by board edge: 0.
- Routed interface audit: PASS for all eleven named nets.
- Edge-connector placement/orientation audit: PASS for JFFC1, J2, and JBL1.
- Assembly geometry and electrical routing are unchanged from R2.8.
- Print-fit STL: 58.0000 x 22.7000 x 4.0950 mm, 896 facets, closed solid.
- System release gate: BLOCKED by the unverified `gpio-breakout-lcd` FH41
  cable shield/ground-plate construction. No fabrication output was released.

## Source and render hashes

```text
ddae61dc0f6302bba9859ffbd2c29ab5eda3464f14207622f222e93fbaf44c85  koyomi-lvds-hat.kicad_pcb
153467e2202b61ca545b943aacf0e0ba551110995907664860c0776f5a0ff370  renders/top.png
7e182db335fe40b212773cfabddd386bd9f65c455bd4dc8b067964f956644baf  renders/bottom.png
9a86171d0f4fd6fb570ab2842a05723856ed622df57958074e146ab84367fd60  renders/side.png
9393cdb7d02cabb5541174ecac93645958756306a59aa42e273fd5e010159f65  renders/perspective.png
03d07f8ac60688eb3e24a3259931d538953b660ae7965db6925a9f4c355647a8  mechanical/print-models/koyomi-rgb-compact-r2.9-print-mockup.stl
f34d3d0bb0fb1cbdf423e81c8bc4d57c3d9f8ff37be30df065f686219cb65a32  mechanical/print-models/koyomi-rgb-compact-r2.9-print-mockup.step
```
