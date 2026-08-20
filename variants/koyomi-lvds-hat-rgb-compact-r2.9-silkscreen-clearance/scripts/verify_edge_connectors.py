#!/usr/bin/env python3
"""Fail closed if an R2.9 edge connector placement regresses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from kipy import KiCad
from kipy.proto.board.board_types_pb2 import BoardLayer


EXPECTED = {
    "JFFC1": {"x": 120.0, "y": 25.3, "rotation": 180.0, "edge": "top"},
    "J2": {"x": 118.5, "y": 41.2, "rotation": 0.0, "edge": "bottom"},
    "JBL1": {"x": 135.5, "y": 39.8, "rotation": 0.0, "edge": "bottom"},
}


def mm(value_nm: int) -> float:
    return value_nm / 1_000_000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("--kicad-cli", required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    record = json.loads(args.record.read_text(encoding="utf-8"))
    documented = {item["reference"]: item for item in record["connectors"]}
    if set(documented) != set(EXPECTED):
        raise SystemExit(f"edge record refs changed: {sorted(documented)}")

    with KiCad(
        headless=True,
        kicad_cli_path=args.kicad_cli,
        file_path=str(args.board.resolve()),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        footprints = {
            fp.reference_field.text.value: fp for fp in board.get_footprints()
        }
        result = {}
        for reference, expected in EXPECTED.items():
            fp = footprints[reference]
            required_record = {
                "reference": reference,
                "edge": expected["edge"],
                "x_mm": expected["x"],
                "y_mm": expected["y"],
                "layer": "F.Cu",
                "rotation_degrees": expected["rotation"],
                "opening": "outward",
            }
            if documented[reference] != required_record:
                raise SystemExit(
                    f"{reference} connector record regression: "
                    f"actual={documented[reference]}, required={required_record}"
                )
            actual = {
                "x": round(mm(fp.position.x), 4),
                "y": round(mm(fp.position.y), 4),
                "rotation": round(fp.orientation.degrees % 360.0, 2),
                "layer": "F.Cu" if fp.layer == BoardLayer.BL_F_Cu else "B.Cu",
                "edge": documented[reference]["edge"],
                "opening": documented[reference]["opening"],
            }
            required = {
                **expected,
                "layer": "F.Cu",
                "opening": "outward",
            }
            if actual != required:
                raise SystemExit(
                    f"{reference} edge placement regression: "
                    f"actual={actual}, required={required}"
                )
            result[reference] = actual

    payload = {
        "result": "PASS",
        "board": str(args.board),
        "connectors": result,
        "interpretation": (
            "Exact X/Y, rotation, F.Cu placement, assigned edge, and outward "
            "opening agree with the R2.9 record inherited from immutable R2.8."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
