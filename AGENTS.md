# PCB edge-connector orientation policy

Every connector placed at a board edge must face outward: its cable-entry,
latch-opening, or external-port aperture must point toward the nearest intended
`Edge.Cuts` boundary, never into the board interior.

Before generating a print model, fabrication package, BOM/CPL, or release
candidate:

1. Record each edge connector's reference, intended edge, and board rotation in
   the revision's `edge-connector-orientations.json`.
2. Render the authoritative `.kicad_pcb` from the top and an applicable side
   using a KiCad version at least as new as the board generator.
3. Visually confirm the real 3D model's cable/port opening faces outward.
4. Re-run the mating-interface and straight-through pin-order audit after any
   connector rotation. Rotation must never be treated as permission to use a
   crossover or custom harness.

An inward-facing edge connector blocks routing and fabrication. Any unavoidable
exception requires an explicit mechanical justification in the revision README.
