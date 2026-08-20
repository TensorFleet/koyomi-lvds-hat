# Compact RGB LCD R2.9 JLCPCB fabrication candidate

Upload the Gerber ZIP, `assembly/bom.csv`, and `assembly/positions.csv`. Select **four layers**, 1.6 mm, ENIG, a **0.20 mm minimum via-hole process**, the JLC-selected plugged-via process, and **top-side Economic PCBA**. Enable **Confirm Production File** and manual parts-placement confirmation.

The board is electrically gated for fabrication: zero DRC errors, zero unconnected pads, zero exclusions, zero ERC errors, and the eleven-net routed-interface audit passes. The all-severity DRC warnings are retained in the report; none are silkscreen-over-copper or board-edge clipping violations.

This is a fabrication-ready prototype, not final system approval. The mating B2.2 carrier and a straight-through 40-contact, 0.5 mm-pitch cable are required. Cable length can be selected after mechanical fit-up and is not a fabrication gate. The external backlight circuit must implement the documented LCD_INS# pull-up and hardware interlock.

The verified JLCPCB cart candidate is **Y47-13044587A**, five boards, with top-side Economic PCBA. JLC matched 11 of 12 BOM lines. `J2` / C5311655 had a five-piece inventory shortfall and is intentionally not placed; hand-solder the pre-ordered I-PEX 20374-R30E-31 after assembly. FL1/FL2 use the approved DLP2ADN900HL4L / C91592 substitution previously fitted on the five-board 2026-07-30 batch. The saved quote is $61.04 PCB plus $72.21 PCBA, $133.25 before shipping and tax.
