#!/usr/bin/env python3
"""Print live copper geometry for selected R2.3 nets."""

from pathlib import Path
import sys

from kipy import KiCad
from kipy.util import to_mm
from kipy.util.board_layer import canonical_name

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "koyomi-lvds-hat.kicad_pcb"
KICAD_CLI = Path(
    "/Users/hyper/projects/tensorfleet/vaio_p_modding/tools/"
    "kicad11-nightly-20260722/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)


def point(vector):
    return (round(to_mm(vector.x), 4), round(to_mm(vector.y), 4))


def main():
    bbox = None
    if len(sys.argv) == 6 and sys.argv[1] == "--bbox":
        bbox = tuple(float(value) for value in sys.argv[2:])
        names = None
    else:
        names = set(sys.argv[1:] or ("D15", "D18"))
    with KiCad(
        headless=True,
        kicad_cli_path=str(KICAD_CLI),
        file_path=str(BOARD),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        for track in board.get_tracks():
            endpoints = (point(track.start), point(track.end))
            in_box = bbox and any(
                bbox[0] <= p[0] <= bbox[1] and bbox[2] <= p[1] <= bbox[3]
                for p in endpoints
            )
            if (names is not None and track.net.name in names) or in_box:
                print(
                    track.net.name,
                    canonical_name(track.layer),
                    point(track.start),
                    point(track.end),
                    "w", round(to_mm(track.width), 4),
                )
        for via in board.get_vias():
            via_point = point(via.position)
            in_box = bbox and (
                bbox[0] <= via_point[0] <= bbox[1]
                and bbox[2] <= via_point[1] <= bbox[3]
            )
            if (names is not None and via.net.name in names) or in_box:
                print(
                    via.net.name,
                    "VIA",
                    point(via.position),
                    "d", round(to_mm(via.diameter), 4),
                    "h", round(to_mm(via.drill_diameter), 4),
                )


if __name__ == "__main__":
    main()
