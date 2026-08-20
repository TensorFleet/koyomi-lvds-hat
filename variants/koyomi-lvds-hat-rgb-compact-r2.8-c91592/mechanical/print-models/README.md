# Koyomi RGB compact r2.8 print model

This bundle is generated from the single-side-assembly R2.8 compact LCD
controller floorplan in
`variants/koyomi-lvds-hat-rgb-compact-r2.8-c91592/`.

Use `koyomi-rgb-compact-r2.8-print-mockup.stl` at **100% scale in
millimetres**. The matching STEP is provided for CAD collision checks.

The file includes:

- the exact 58.0 x 22.2 mm base outline, including the 20.0 x 0.5 mm JFFC1
  support tab and four mounting holes;
- outward-facing system FFC `JFFC1`;
- outward-facing panel micro-coax connector `J2`;
- outward-facing backlight FFC `JBL1`;
- all currently fitted ICs, resistor arrays, capacitors, and filters.

Detailed vendor models are converted to closed external occupancy envelopes.
This makes the STL deterministic and printable, while deliberately sacrificing
cosmetic component detail. FL1 and FL2 use conservative 2.0 x 1.0 x 0.5 mm
proxies because their source STEP file is missing from the project.

Regenerate with:

`/Applications/FreeCAD.app/Contents/MacOS/FreeCAD -c variants/koyomi-lvds-hat-rgb-compact-r2.8-c91592/scripts/generate_print_model.py`

This is a mechanical floorplan gauge, not a fabrication release. The current
board has 0 geometric DRC violations but retains 138 intentional unconnected
items until native routing is complete.
