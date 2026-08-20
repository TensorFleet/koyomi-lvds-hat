#!/usr/bin/env python3
"""Keep legacy test connectors documented but exclude them from hardware."""

from __future__ import annotations

import argparse
from pathlib import Path

from kipy import KiCad


SCHEMATIC_ONLY_REFERENCES = {"J3", "J4", "J5", "J6", "J7", "J8"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("schematic", type=Path)
    parser.add_argument("--kicad-cli", required=True)
    args = parser.parse_args()

    schematic_path = args.schematic.resolve()
    with KiCad(
        headless=True,
        kicad_cli_path=args.kicad_cli,
        file_path=str(schematic_path),
        timeout_ms=60_000,
    ) as kicad:
        schematic = kicad.get_schematic()
        updates = []
        for symbol in schematic.get_symbols():
            if symbol.reference_field.text.value not in SCHEMATIC_ONLY_REFERENCES:
                continue
            attributes = symbol.attributes
            attributes.exclude_from_bill_of_materials = True
            attributes.exclude_from_board = True
            attributes.exclude_from_position_files = True
            attributes.do_not_populate = True
            symbol.attributes = attributes
            updates.append(symbol)
        schematic.update_items(updates)
        schematic.save()


if __name__ == "__main__":
    main()
