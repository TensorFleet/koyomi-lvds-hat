# Compact RGB LCD R2.7 JLCPCB fabrication candidate

Upload the Gerber ZIP, `assembly/bom.csv`, and `assembly/positions.csv`. Select **four layers**, 1.6 mm, ENIG, a **0.20 mm minimum via-hole process**, ordinary tented vias, and **top-side Economic PCBA**. Enable **Confirm Production File** and manual parts-placement confirmation.

The board is electrically gated for fabrication: zero DRC errors, zero unconnected pads, zero exclusions, zero ERC errors, and the eleven-net routed-interface audit passes. The 13 all-severity DRC warnings are inherited library-copy mismatches and are retained in the report.

This is a fabrication-ready prototype, not final system approval. The mating B2.2 carrier and straight-through 40-contact cable are required. The external backlight circuit must implement the documented LCD_INS# pull-up and hardware interlock. Verify live JLC inventory, especially private-library connector C5311655, before checkout. The 2026-08-20 live check found C5311655 at stock 0 with a 442-piece pre-order minimum and C710576 at stock 0 with a 23-piece consignment minimum. The PCB is ready to fabricate; PCBA must wait until those exact parts are received.
