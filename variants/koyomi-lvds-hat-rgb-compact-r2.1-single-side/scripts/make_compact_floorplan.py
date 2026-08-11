#!/usr/bin/env python3
"""Create the r2.1 single-side compact floorplan with KiCad's IPC API.

This script intentionally removes donor routing and zones.  It creates a
fabrication-closed floorplan that can be natively routed as the next step.
RN1-RN6 are removed and re-imported from the schematic so KiCad itself creates
them as front-side footprints; no footprint internals are hand-mirrored.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from kipy import KiCad
from kipy.board_types import BoardSegment, BoardText
from kipy.geometry import Angle, Vector2
from kipy.proto.board.board_types_pb2 import BoardLayer


OPTIONAL_CONNECTORS = {"J3", "J4", "J5", "J6", "J7", "J8"}

# x, y, rotation in millimetres/degrees.  The 65 x 28.25 mm outline is
# x=91..156 and y=22..50.25.
PLACEMENT = {
    "H1": (94.5, 25.5, 0.0),
    "H2": (152.5, 25.5, 0.0),
    "H3": (94.5, 46.5, 0.0),
    "H4": (152.5, 46.5, 0.0),
    "JFFC1": (123.5, 25.6, 0.0),
    "IC1": (123.5, 36.3, -90.0),
    "J2": (123.5, 47.0, 0.0),
    "RN1": (100.0, 29.0, 0.0),
    "RN2": (104.0, 29.0, 0.0),
    "RN3": (108.0, 29.0, 0.0),
    "RN4": (139.0, 29.0, 0.0),
    "RN5": (143.0, 29.0, 0.0),
    "RN6": (147.0, 29.0, 0.0),
    "C1": (114.2, 33.0, 0.0),
    "C2": (114.2, 36.2, 0.0),
    "C3": (114.2, 39.4, 0.0),
    "C4": (112.5, 42.2, 0.0),
    "C5": (116.0, 42.2, 0.0),
    "C6": (119.5, 42.2, 0.0),
    "C7": (100.5, 42.0, -90.0),
    "C8": (106.5, 45.0, 0.0),
    "R1": (99.5, 34.0, -90.0),
    "R2": (99.5, 37.5, -90.0),
    "U1": (106.0, 38.0, -90.0),
    "FL1": (128.6, 43.5, 0.0),
    "FL2": (125.8, 43.5, 0.0),
    "JP1": (145.0, 35.0, -90.0),
    "JP2": (149.0, 35.0, -90.0),
}


def edge_segment(start: tuple[float, float], end: tuple[float, float]) -> BoardSegment:
    item = BoardSegment()
    item.layer = BoardLayer.BL_Edge_Cuts
    item.start = Vector2.from_xy_mm(*start)
    item.end = Vector2.from_xy_mm(*end)
    item.attributes.stroke.width = 50_000
    return item


def board_label() -> BoardText:
    item = BoardText()
    item.layer = BoardLayer.BL_F_SilkS
    item.position = Vector2.from_xy_mm(145.5, 40.5)
    item.value = "RGB R2.1 SINGLE SIDE"
    item.attributes.size = Vector2.from_xy_mm(1.0, 1.0)
    item.attributes.stroke_width = 150_000
    item.attributes.angle = 90.0
    return item


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("--netlist", type=Path, required=True)
    parser.add_argument("--kicad-cli", required=True)
    args = parser.parse_args()

    board_path = args.board.resolve()
    netlist_path = args.netlist.resolve()
    with KiCad(
        headless=True,
        kicad_cli_path=args.kicad_cli,
        file_path=str(board_path),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()

        # A compact placement cannot reuse the original HAT routing.  Remove it
        # explicitly so every future connection is routed against this geometry.
        board.remove_items(
            list(board.get_tracks()) + list(board.get_vias()) + list(board.get_zones())
        )

        footprints = list(board.get_footprints())
        remove = [
            fp
            for fp in footprints
            if fp.reference_field.text.value in OPTIONAL_CONNECTORS
            or fp.reference_field.text.value == "REF**"
        ]
        board.remove_items(remove)

        # Reinstantiate all six arrays from the schematic.  Newly imported
        # footprints are front-side by construction, which makes this a true
        # single-side assembly without hand-authored footprint transformations.
        resistor_arrays = [
            fp
            for fp in footprints
            if fp.reference_field.text.value in {f"RN{i}" for i in range(1, 7)}
        ]
        board.remove_items(resistor_arrays)
        result = board.import_netlist(
            str(netlist_path),
            dry_run=False,
            delete_extra_footprints=False,
            update_footprints=False,
        )
        if result.error_count or result.new_footprint_count != 6:
            raise RuntimeError(
                "RN re-import failed: "
                f"errors={result.error_count}, new={result.new_footprint_count}\n"
                f"{result.report}"
            )

        footprints = list(board.get_footprints())
        updates = []
        for fp in footprints:
            ref = fp.reference_field.text.value
            if ref not in PLACEMENT:
                continue
            # kicad-python 0.8.0.dev0's position/orientation setters currently
            # rebuild the footprint item list without carrying 3D models.
            # Preserve and reattach those official API objects explicitly.
            models = list(fp.definition.models)
            x_mm, y_mm, rotation = PLACEMENT[ref]
            fp.position = Vector2.from_xy_mm(x_mm, y_mm)
            fp.orientation = Angle.from_degrees(rotation)
            fp.definition.items = list(fp.definition.items) + models
            updates.append(fp)
        board.update_items(updates)

        # Remove donor board graphics and rebuild a simple exact half-area outline.
        board.remove_items(list(board.get_shapes()) + list(board.get_text()))
        board.create_items(
            [
                edge_segment((91.0, 22.0), (156.0, 22.0)),
                edge_segment((156.0, 22.0), (156.0, 50.25)),
                edge_segment((156.0, 50.25), (91.0, 50.25)),
                edge_segment((91.0, 50.25), (91.0, 22.0)),
                board_label(),
            ]
        )
        board.save()


if __name__ == "__main__":
    main()
