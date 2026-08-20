#!/usr/bin/env python3
"""Finalize R2.6 revision identification through KiCad IPC."""

from __future__ import annotations

from pathlib import Path

from kipy import KiCad


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "koyomi-lvds-hat.kicad_pcb"
KICAD_CLI = Path(
    "/Users/hyper/projects/tensorfleet/vaio_p_modding/tools/"
    "kicad11-nightly-20260722/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)


def main() -> None:
    with KiCad(
        headless=True,
        kicad_cli_path=str(KICAD_CLI),
        file_path=str(BOARD),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        texts = [text for text in board.get_text() if text.value == "R2.4 SIDE IO"]
        if len(texts) != 1:
            raise RuntimeError(f"expected one R2.4 revision label, found {len(texts)}")
        texts[0].value = "R2.6 PRODUCTION"
        commit = board.begin_commit()
        try:
            board.update_items(texts)
            board.push_commit(commit, "Set R2.6 production silkscreen")
        except Exception:
            board.drop_commit(commit)
            raise
        board.save()


if __name__ == "__main__":
    main()
