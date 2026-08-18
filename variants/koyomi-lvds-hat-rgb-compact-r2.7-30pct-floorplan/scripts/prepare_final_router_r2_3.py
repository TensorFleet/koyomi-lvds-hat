#!/usr/bin/env python3
"""Restore the verified R2.3 checkpoint before the residual router pass."""

from __future__ import annotations

import sys
from pathlib import Path

from kipy import KiCad
from kipy.board_types import Track
from kipy.util import from_mm


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "koyomi-lvds-hat.kicad_pcb"
KICAD_CLI = Path(
    "/Users/hyper/projects/tensorfleet/vaio_p_modding/tools/"
    "kicad11-nightly-20260722/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from finalize_r2_3 import B_CU, deduplicate_copper  # noqa: E402


def main():
    with KiCad(
        headless=True,
        kicad_cli_path=str(KICAD_CLI),
        file_path=str(BOARD),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        stale = []
        for item in [*board.get_tracks(), *board.get_vias()]:
            if item.net.name in {"D15", "D18", "VSYNC"}:
                stale.append(item)
                continue
            if item.net.name == "GND":
                if isinstance(item, Track) and item.width == from_mm(0.15):
                    stale.append(item)
                    continue
                if (
                    not isinstance(item, Track)
                    and item.diameter == from_mm(0.45)
                    and item.drill_diameter == from_mm(0.20)
                ):
                    stale.append(item)
                    continue
            if item.net.name == "+3V3" and isinstance(item, Track) and item.layer == B_CU:
                points = (
                    (item.start.x / 1e6, item.start.y / 1e6),
                    (item.end.x / 1e6, item.end.y / 1e6),
                )
                if any(abs(x - 116.6) < 0.01 and 35.0 < y < 35.6 for x, y in points):
                    stale.append(item)
        if stale:
            commit = board.begin_commit()
            try:
                board.remove_items(stale)
                board.push_commit(commit, "Restore R2.3 residual-router checkpoint")
            except Exception:
                board.drop_commit(commit)
                raise
        print(f"removed {len(stale)} trial residual items")
        print(f"removed {deduplicate_copper(board)} duplicate items")
        board.refill_zones(block=True, max_poll_seconds=60.0)
        board.save()
        print(f"saved {board.name}")


if __name__ == "__main__":
    main()
