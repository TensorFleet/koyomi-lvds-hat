#!/usr/bin/env python3
"""Apply the final compact R2.4 revision silkscreen through KiCad IPC."""

from __future__ import annotations

import argparse
from pathlib import Path

from kipy import KiCad
from kipy.geometry import Vector2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("--kicad-cli", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with KiCad(
        headless=True,
        kicad_cli_path=args.kicad_cli,
        file_path=str(args.board.resolve()),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        matches = [
            item for item in board.get_text()
            if item.value in {
                "R2.4 DIRECT SIDEBANDS", "R2.4 SIDEBANDS", "R2.4 SIDE IO"
            }
        ]
        if len(matches) != 1:
            raise RuntimeError(f"expected one R2.4 revision label, found {len(matches)}")
        label = matches[0]
        print(
            f"revision silk: {label.value!r} at "
            f"({label.position.x / 1e6:.2f}, {label.position.y / 1e6:.2f}) "
            "-> 'R2.4 SIDE IO' at (146.00, 37.00)"
        )
        if args.apply:
            label.value = "R2.4 SIDE IO"
            label.position = Vector2.from_xy_mm(146.0, 37.0)
            commit = board.begin_commit()
            try:
                board.update_items(label)
                board.push_commit(commit, "Shorten R2.4 revision silkscreen")
            except Exception:
                board.drop_commit(commit)
                raise
            board.save()


if __name__ == "__main__":
    main()
