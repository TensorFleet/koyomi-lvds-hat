#!/usr/bin/env python3
"""Generate the compact Koyomi r2.3 populated 3D-print fit gauge.

Run with FreeCAD's command-line Python. The KiCad source is read-only. Vendor
STEP assemblies are reduced to closed external occupancy envelopes so the STL
is deterministic and manifold instead of a collection of overlapping shells.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import FreeCAD as App
import Import
import Mesh
import MeshPart
import Part


VARIANT = Path(__file__).resolve().parents[1]
PCB = VARIANT / "koyomi-lvds-hat.kicad_pcb"
OUT = VARIANT / "mechanical/print-models"
WORK = OUT / ".work"
RAW_STEP = WORK / "koyomi-rgb-compact-r2.3-populated.step"
NAME = "koyomi-rgb-compact-r2.3-print-mockup"

MESH_LINEAR_DEFLECTION = 0.05
MESH_ANGULAR_DEFLECTION = 0.35


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_kicad_cli() -> Path:
    candidates = []
    if os.environ.get("KICAD_CLI"):
        candidates.append(Path(os.environ["KICAD_CLI"]))
    candidates.extend(
        [
            Path.home()
            / "projects/tensorfleet/vaio_p_modding/tools/"
            "kicad11-nightly-20260722/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
            Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"),
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("no compatible kicad-cli found; set KICAD_CLI")


def top_group_label(obj) -> str:
    chain, current, seen = [], obj, set()
    while True:
        parents = [
            parent
            for parent in current.InList
            if parent.TypeId == "App::Part" or hasattr(parent, "Group")
        ]
        if not parents or parents[0].Name in seen:
            break
        seen.add(parents[0].Name)
        current = parents[0]
        chain.append(current.Label)
    return chain[-2] if len(chain) >= 2 else obj.Label


def placed_solids(doc):
    for obj in doc.Objects:
        if obj.TypeId != "Part::Feature":
            continue
        if not (obj.Shape and obj.Shape.Solids) or obj.OutList:
            continue
        shape = obj.Shape.copy()
        shape.Placement = obj.getGlobalPlacement()
        yield obj.Label, top_group_label(obj), shape


def bounds_box(bounds) -> Part.Shape:
    x0, x1, y0, y1, z0, z1 = bounds
    return Part.makeBox(
        x1 - x0, y1 - y0, z1 - z0, App.Vector(x0, y0, z0)
    )


def merge_bounds(old, incoming):
    if old is None:
        return incoming
    return (
        min(old[0], incoming[0]),
        max(old[1], incoming[1]),
        min(old[2], incoming[2]),
        max(old[3], incoming[3]),
        min(old[4], incoming[4]),
        max(old[5], incoming[5]),
    )


OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)

kicad_cli = locate_kicad_cli()
subprocess.run(
    [
        str(kicad_cli),
        "pcb",
        "export",
        "step",
        "--force",
        "--subst-models",
        "--no-dnp",
        "-o",
        str(RAW_STEP),
        str(PCB),
    ],
    check=True,
)

doc = App.newDocument("koyomi_r23_source")
Import.insert(str(RAW_STEP), doc.Name)

board_shape = None
group_bounds = {}
for _label, group, shape in placed_solids(doc):
    bb = shape.BoundBox
    if group.endswith("_PCB"):
        board_shape = shape
        continue
    bounds = (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax)
    group_bounds[group] = merge_bounds(group_bounds.get(group), bounds)

if board_shape is None:
    raise RuntimeError("could not identify KiCad board slab")

board_top_z = board_shape.BoundBox.ZMax

# FL1/FL2 source model is unresolved in the KiCad project. The referenced
# package filename and footprint define a 2.0 x 1.0 x 0.5 mm body.
missing_model_proxies = {
    "FL1": Part.makeBox(
        2.0, 1.0, 0.5, App.Vector(127.6, -44.0, board_top_z)
    ),
    "FL2": Part.makeBox(
        2.0, 1.0, 0.5, App.Vector(124.8, -44.0, board_top_z)
    ),
}

labelled_shapes = [("PCB", board_shape)]
for group, bounds in sorted(group_bounds.items()):
    labelled_shapes.append((group, bounds_box(bounds)))
labelled_shapes.extend(sorted(missing_model_proxies.items()))

combined = Mesh.Mesh()
for _label, shape in labelled_shapes:
    combined.addMesh(
        MeshPart.meshFromShape(
            Shape=shape,
            LinearDeflection=MESH_LINEAR_DEFLECTION,
            AngularDeflection=MESH_ANGULAR_DEFLECTION,
            Relative=False,
        )
    )

stl_path = OUT / f"{NAME}.stl"
step_path = OUT / f"{NAME}.step"
report_path = OUT / "print-mockup-report.json"
checksums_path = OUT / "CHECKSUMS.sha256"

combined.write(str(stl_path))
if not combined.isSolid():
    raise RuntimeError("generated STL is not a closed solid")

Part.Compound([shape for _label, shape in labelled_shapes]).exportStep(
    str(step_path)
)

# Reloading catches serialization failures that an in-memory mesh can hide.
reloaded = Mesh.Mesh(str(stl_path))
if not reloaded.isSolid():
    raise RuntimeError("serialized STL does not reload as a closed solid")

bb = reloaded.BoundBox
report = {
    "units": "mm",
    "revision": "Koyomi RGB compact r2.3 routed",
    "source_board": str(PCB.relative_to(VARIANT)),
    "source_board_sha256": sha256(PCB),
    "source_step_warning": [
        "FL1 and FL2 source STEP paths are unresolved; conservative "
        "2.0 x 1.0 x 0.5 mm package proxies are included"
    ],
    "model_method": (
        "exact KiCad PCB slab plus closed external occupancy envelopes for "
        "fitted component STEP groups"
    ),
    "board_slab_mm": {
        "x": round(board_shape.BoundBox.XLength, 4),
        "y": round(board_shape.BoundBox.YLength, 4),
        "z": round(board_shape.BoundBox.ZLength, 4),
    },
    "populated_envelope_mm": {
        "x": round(bb.XLength, 4),
        "y": round(bb.YLength, 4),
        "z": round(bb.ZLength, 4),
        "z_min": round(bb.ZMin, 4),
        "z_max": round(bb.ZMax, 4),
    },
    "modeled_component_groups": [
        {
            "name": group,
            "bounds": [round(value, 4) for value in bounds],
        }
        for group, bounds in sorted(group_bounds.items())
    ],
    "missing_model_proxies": {
        "FL1": {"body_mm": [2.0, 1.0, 0.5], "center_xy_mm": [128.6, -43.5]},
        "FL2": {"body_mm": [2.0, 1.0, 0.5], "center_xy_mm": [125.8, -43.5]},
    },
    "mesh": {
        "facets": reloaded.CountFacets,
        "points": reloaded.CountPoints,
        "solid": True,
    },
    "limitations": [
        "occupancy/fit gauge, not a cosmetic component rendering",
        "does not prove cable bend radius, latch access, or chassis retention",
    ],
}
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

deliverables = (stl_path, step_path, report_path)
checksums_path.write_text(
    "".join(f"{sha256(path)}  {path.name}\n" for path in deliverables),
    encoding="utf-8",
)

print(
    f"{stl_path.name}: {bb.XLength:.4f} x {bb.YLength:.4f} x "
    f"{bb.ZLength:.4f} mm; {reloaded.CountFacets} facets; solid=True"
)
