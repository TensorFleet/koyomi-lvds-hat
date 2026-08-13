#!/usr/bin/env python3
"""Print placement data through KiCad's official headless IPC API."""

from __future__ import annotations

import argparse
from pathlib import Path

from kipy import KiCad
from kipy.proto.board.board_types_pb2 import BoardLayer


def mm(value_nm: int) -> float:
    return value_nm / 1_000_000


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
        print(f"KiCad {kicad.get_version()}", flush=True)
        for fp in sorted(
            board.get_footprints(), key=lambda item: item.reference_field.text.value
        ):
            side = "front" if fp.layer == BoardLayer.BL_F_Cu else "back"
            print(
                f"{fp.reference_field.text.value:5s} "
                f"side={side:5s} "
                f"x={mm(fp.position.x):8.3f} y={mm(fp.position.y):8.3f} "
                f"rot={fp.orientation.degrees:7.2f} "
                f"value={fp.value_field.text.value}",
                flush=True,
            )


if __name__ == "__main__":
    main()
