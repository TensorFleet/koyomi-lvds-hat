#!/usr/bin/env python3
"""Build the R2.7 30%-area, top-assembly LCD-controller floorplan.

The source is the electrically complete R2.6 production candidate. This
script deliberately removes routing and zones after moving the footprints;
R2.7 remains fabrication-blocked until it has been routed and reverified.
All project mutations use KiCad's official IPC API.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from kipy import KiCad
from kipy.board_types import BoardSegment, BoardText
from kipy.geometry import Angle, Vector2
from kipy.proto.board.board_types_pb2 import BoardLayer


# The 58.0 x 22.2 mm base rectangle is 1287.6 mm^2.  A 20 x 0.5 mm
# connector-support tab adds 10 mm^2, for 1297.6 mm^2 total versus R2.6's
# 1836.25 mm^2.  This is a 29.33% area reduction.
OUTLINE = (91.0, 22.0, 149.0, 44.2)
JFFC_TAB = (110.0, 21.5, 130.0, 22.0)

# x, y, rotation in millimetres/degrees. All fitted parts remain on F.Cu.
PLACEMENT = {
    "H1": (94.5, 25.5, 0.0),
    "H2": (145.5, 25.5, 0.0),
    "H3": (94.5, 40.7, 0.0),
    "H4": (145.5, 40.7, 0.0),
    # Cable opening faces the top Edge.Cuts boundary.  Rotation 0 opened into
    # the board interior and is prohibited by the repository edge policy.
    "JFFC1": (120.0, 25.3, 180.0),
    "IC1": (118.5, 32.95, -90.0),
    "J2": (118.5, 41.2, 0.0),
    "JBL1": (135.5, 39.8, 0.0),
    "RN1": (100.5, 28.2, 0.0),
    "RN2": (104.5, 28.2, 0.0),
    "RN3": (109.5, 33.3, 0.0),
    "RN4": (128.5, 33.3, 0.0),
    "RN5": (135.5, 28.2, 0.0),
    "RN6": (139.5, 28.2, 0.0),
    "C1": (109.5, 38.1, 0.0),
    "C2": (112.8, 38.1, 0.0),
    "C3": (116.1, 38.1, 0.0),
    "C4": (119.4, 38.1, 0.0),
    "C5": (122.7, 38.1, 0.0),
    "C6": (132.5, 31.0, 0.0),
    "C7": (98.5, 37.0, 0.0),
    "C8": (102.5, 40.0, 0.0),
    "R1": (98.5, 31.2, 0.0),
    "R2": (98.5, 33.5, 0.0),
    "U1": (103.8, 34.7, -90.0),
    "FL1": (129.5, 38.0, 0.0),
    "FL2": (126.2, 38.0, 0.0),
    "JP1": (135.0, 34.0, -90.0),
    "JP2": (139.0, 34.0, -90.0),
}


def edge(start: tuple[float, float], end: tuple[float, float]) -> BoardSegment:
    item = BoardSegment()
    item.layer = BoardLayer.BL_Edge_Cuts
    item.start = Vector2.from_xy_mm(*start)
    item.end = Vector2.from_xy_mm(*end)
    item.attributes.stroke.width = 50_000
    return item


def label(value: str, position: tuple[float, float], size: float = 0.65) -> BoardText:
    item = BoardText()
    item.layer = BoardLayer.BL_F_SilkS
    item.position = Vector2.from_xy_mm(*position)
    item.value = value
    item.attributes.size = Vector2.from_xy_mm(size, size)
    item.attributes.stroke_width = 110_000
    return item


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("--kicad-cli", required=True)
    args = parser.parse_args()

    board_path = args.board.resolve()
    with KiCad(
        headless=True,
        kicad_cli_path=args.kicad_cli,
        file_path=str(board_path),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()

        # Existing copper cannot remain valid after a component move. Clear it
        # explicitly and make the floorplan fail closed until native rerouting.
        board.remove_items(
            list(board.get_tracks()) + list(board.get_vias()) + list(board.get_zones())
        )

        updates = []
        for fp in board.get_footprints():
            ref = fp.reference_field.text.value
            if ref not in PLACEMENT:
                continue
            models = list(fp.definition.models)
            x_mm, y_mm, rotation = PLACEMENT[ref]
            fp.position = Vector2.from_xy_mm(x_mm, y_mm)
            fp.orientation = Angle.from_degrees(rotation)
            # Current kicad-python setters rebuild the item list; carry the
            # official 3D model objects forward explicitly.
            fp.definition.items = list(fp.definition.items) + models
            updates.append(fp)
        board.update_items(updates)

        # Rebuild only the board-level outline and compact phase markings.
        board.remove_items(list(board.get_shapes()) + list(board.get_text()))
        x0, y0, x1, y1 = OUTLINE
        tab_x0, tab_y0, tab_x1, _ = JFFC_TAB
        board.create_items(
            [
                edge((x0, y0), (tab_x0, y0)),
                edge((tab_x0, y0), (tab_x0, tab_y0)),
                edge((tab_x0, tab_y0), (tab_x1, tab_y0)),
                edge((tab_x1, tab_y0), (tab_x1, y0)),
                edge((tab_x1, y0), (x1, y0)),
                edge((x1, y0), (x1, y1)),
                edge((x1, y1), (x0, y1)),
                edge((x0, y1), (x0, y0)),
                label("R2.7", (145.0, 33.0), 0.50),
                label("JBL1", (143.8, 36.3), 0.50),
            ]
        )
        board.save()


if __name__ == "__main__":
    main()
