#!/usr/bin/env python3
"""Remove the obsolete +3V3 trunk tail left by repurposing JFFC1 pin 17."""

from __future__ import annotations

import argparse
from pathlib import Path

from kipy import KiCad


TARGET = {(41_910_000, 30_480_000), (41_910_000, 50_800_000)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("schematic", type=Path)
    parser.add_argument("--kicad-cli", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with KiCad(
        headless=True,
        kicad_cli_path=args.kicad_cli,
        file_path=str(args.schematic.resolve()),
        timeout_ms=60_000,
    ) as kicad:
        schematic = kicad.get_schematic()
        matches = [
            line for line in schematic.get_lines()
            if {(line.start.x, line.start.y), (line.end.x, line.end.y)} == TARGET
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"expected one obsolete sideband wire, found {len(matches)}"
            )
        print("remove obsolete +3V3 trunk tail: (41.91,30.48)-(41.91,50.80)")
        if args.apply:
            schematic.remove_items(matches)
            schematic.save()


if __name__ == "__main__":
    main()
