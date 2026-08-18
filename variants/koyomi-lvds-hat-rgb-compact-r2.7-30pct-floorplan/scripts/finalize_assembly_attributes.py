#!/usr/bin/env python3
"""Exclude non-placeable holes and copper jumpers from R2.6 assembly outputs."""

from pathlib import Path

from kipy import KiCad


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "koyomi-lvds-hat.kicad_pcb"
KICAD_CLI = Path(
    "/Users/hyper/projects/tensorfleet/vaio_p_modding/tools/"
    "kicad11-nightly-20260722/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)
EXCLUDED = {"H1", "H2", "H3", "H4", "JP1", "JP2"}


def main():
    with KiCad(
        headless=True,
        kicad_cli_path=str(KICAD_CLI),
        file_path=str(BOARD),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        footprints = {
            item.reference_field.text.value: item
            for item in board.get_footprints()
        }
        missing = EXCLUDED - set(footprints)
        if missing:
            raise RuntimeError(f"missing expected assembly exclusions: {sorted(missing)}")
        changed = []
        for reference in sorted(EXCLUDED):
            item = footprints[reference]
            item.attributes.exclude_from_bill_of_materials = True
            item.attributes.exclude_from_position_files = True
            changed.append(item)
        commit = board.begin_commit()
        try:
            board.update_items(changed)
            board.push_commit(commit, "Finalize R2.6 assembly exclusions")
        except Exception:
            board.drop_commit(commit)
            raise
        board.save()
        print("excluded from BOM/CPL: " + ", ".join(sorted(EXCLUDED)))


if __name__ == "__main__":
    main()
