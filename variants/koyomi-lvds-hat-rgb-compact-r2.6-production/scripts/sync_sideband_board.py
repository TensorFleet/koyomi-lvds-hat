#!/usr/bin/env python3
"""Synchronize the direct-sideband R2.4 PCB from its exported netlist."""

from __future__ import annotations

import argparse
from pathlib import Path

from kipy import KiCad


KICAD_CLI = Path(
    "/Users/hyper/projects/tensorfleet/vaio_p_modding/tools/"
    "kicad11-nightly-20260722/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("netlist", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    with KiCad(
        headless=True,
        kicad_cli_path=str(KICAD_CLI),
        file_path=str(args.board.resolve()),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        result = board.import_netlist(
            str(args.netlist.resolve()),
            dry_run=args.dry_run,
            delete_extra_footprints=False,
            update_footprints=False,
            transfer_groups=True,
        )
        print(result)
        if result.report:
            print(result.report)
        if result.error_count:
            raise SystemExit(f"netlist import failed with {result.error_count} errors")
        if not args.dry_run:
            board.save()


if __name__ == "__main__":
    main()
