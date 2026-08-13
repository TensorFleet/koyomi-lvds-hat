#!/usr/bin/env python3
"""Apply final R2.3 silkscreen spacing through KiCad's IPC API."""

from pathlib import Path

from kipy import KiCad
from kipy.geometry import Vector2

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "koyomi-lvds-hat.kicad_pcb"
KICAD_CLI = Path(
    "/Users/hyper/projects/tensorfleet/vaio_p_modding/tools/"
    "kicad11-nightly-20260722/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)


def main():
    with KiCad(
        headless=True,
        kicad_cli_path=str(KICAD_CLI),
        file_path=str(BOARD),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        updates = []
        for item in board.get_text():
            if item.value == "R2.3 ROUTED":
                item.position = Vector2.from_xy_mm(151.8, 37.5)
                updates.append(item)
        if len(updates) != 1:
            raise RuntimeError(f"expected one R2.3 label, found {len(updates)}")
        commit = board.begin_commit()
        try:
            board.update_items(updates)
            board.push_commit(commit, "Separate R2.3 and backlight silkscreen labels")
        except Exception:
            board.drop_commit(commit)
            raise
        board.save()
        print("moved R2.3 ROUTED silkscreen to (151.8, 37.5)")


if __name__ == "__main__":
    main()
