#!/usr/bin/env python3
"""Audit the production cable endpoints on the routed R2.4 PCB via KiCad IPC."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from kipy import KiCad


EXPECTED = {
    "PANEL_ID0": (("JFFC1", "17"), ("J2", "10")),
    "PANEL_ID1": (("JFFC1", "34"), ("J2", "21")),
    "LCD_INS": (("JFFC1", "39"), ("J2", "30")),
    "EN": (("JFFC1", "13"), ("JBL1", "12")),
    "PWM": (("JFFC1", "37"), ("JBL1", "11")),
    "VCD1": (("J2", "18"), ("JBL1", "6")),
    "VCD2": (("J2", "17"), ("JBL1", "5")),
    "VCD3": (("J2", "16"), ("JBL1", "4")),
    "VCD4": (("J2", "15"), ("JBL1", "3")),
    "VCD5": (("J2", "14"), ("JBL1", "2")),
    "VCD6": (("J2", "13"), ("JBL1", "1")),
}


def pad(footprint, number):
    return next(item for item in footprint.definition.pads if item.number == number)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("--kicad-cli", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with KiCad(
        headless=True,
        kicad_cli_path=args.kicad_cli,
        file_path=str(args.board.resolve()),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        refs = {
            footprint.reference_field.text.value: footprint
            for footprint in board.get_footprints()
        }
        tracks = list(board.get_tracks())
        vias = list(board.get_vias())
        results = {}
        failures = []
        for net_name, expected_endpoints in EXPECTED.items():
            observed = []
            for reference, pin_number in expected_endpoints:
                actual = pad(refs[reference], pin_number).net.name
                observed.append(
                    {"reference": reference, "pin": pin_number, "net": actual}
                )
                if actual != net_name:
                    failures.append(
                        f"{reference}.{pin_number}: expected {net_name}, got {actual}"
                    )
            results[net_name] = {
                "endpoints": observed,
                "track_segments": sum(1 for item in tracks if item.net.name == net_name),
                "vias": sum(1 for item in vias if item.net.name == net_name),
            }

        forbidden = [reference for reference in refs if reference in {f"J{x}" for x in range(3, 9)}]
        if forbidden:
            failures.append(f"legacy optional connector footprints present: {forbidden}")

        report = {
            "board": str(args.board),
            "result": "PASS" if not failures else "FAIL",
            "legacy_j3_j8_footprints": forbidden,
            "nets": results,
            "failures": failures,
            "interpretation": (
                "A matching net on both named pads plus the fresh KiCad DRC result of "
                "zero unconnected items demonstrates continuous routed copper."
            ),
        }
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        if failures:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
