# Koyomi RGB compact r2.3 print model

This bundle is generated from the routed, single-side-assembly compact LCD
controller in `variants/koyomi-lvds-hat-rgb-compact-r2.3-routed/`.

Use `koyomi-rgb-compact-r2.3-print-mockup.stl` at **100% scale in
millimetres**. The matching STEP is provided for CAD collision checks.

The file includes:

- the exact 65.0 × 28.25 mm KiCad PCB slab and mounting holes;
- system FFC `JFFC1`;
- panel micro-coax connector `J2`;
- backlight FFC `JBL1`;
- all fitted ICs, resistor arrays, capacitors, and filters.

Detailed vendor models are converted to closed external occupancy envelopes.
This makes the STL deterministic and printable, while deliberately sacrificing
cosmetic component detail. FL1 and FL2 use conservative 2.0 × 1.0 × 0.5 mm
proxies because their source STEP file is missing from the project.

Regenerate with:

`/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd variants/koyomi-lvds-hat-rgb-compact-r2.3-routed/scripts/generate_print_model.py`

The PCB has 0 DRC violations and 0 unconnected pads. Fabrication remains a
separate decision: the schematic still has three inherited power-source ERC
errors and this print artifact does not waive them.
