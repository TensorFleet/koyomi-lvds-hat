#!/usr/bin/env python3
"""Assign three redundant FFC contacts to the panel sideband nets via IPC."""

from __future__ import annotations

import argparse
from pathlib import Path

from kipy import KiCad
from kipy.geometry import Vector2
from kipy.proto.schematic import schematic_types_pb2
from kipy.schematic_types import GlobalLabel


PIN_NETS = {"17": "PANEL_ID0", "34": "PANEL_ID1", "39": "LCD_INS"}


def pin_positions(symbol) -> dict[str, Vector2]:
    result = {}
    for child in symbol.proto.definition.items:
        if not child.item.type_url.endswith("SchematicPin"):
            continue
        pin = schematic_types_pb2.SchematicPin()
        if not child.item.Unpack(pin):
            raise RuntimeError("failed to unpack schematic pin")
        result[pin.number] = Vector2(pin.position)
    return result


def same_point(a: Vector2, b: Vector2) -> bool:
    return a.x == b.x and a.y == b.y


def point_key(point: Vector2) -> tuple[int, int]:
    return point.x, point.y


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
        jffc = next(
            symbol for symbol in schematic.get_symbols()
            if symbol.reference_field.text.value == "JFFC1"
        )
        pins = pin_positions(jffc)
        labels = list(schematic.get_labels())
        lines = list(schematic.get_lines())
        replacements = []
        stale = []
        fallback = next(label for label in labels if isinstance(label, GlobalLabel))

        for number, net_name in PIN_NETS.items():
            position = pins[number]
            visited = {point_key(position)}
            component_lines = []
            changed = True
            while changed:
                changed = False
                for line in lines:
                    if line in component_lines:
                        continue
                    a = point_key(line.start)
                    b = point_key(line.end)
                    if a in visited or b in visited:
                        component_lines.append(line)
                        if a not in visited or b not in visited:
                            visited.update((a, b))
                            changed = True
            old = [label for label in labels if point_key(label.position) in visited]
            direct_lines = [
                line for line in component_lines
                if same_point(line.start, position) or same_point(line.end, position)
            ]
            print(
                f"JFFC1.{number} @ ({position.x / 1e6:.2f}, "
                f"{position.y / 1e6:.2f}) old={[label.text.value for label in old]} "
                f"lines={len(component_lines)} direct={len(direct_lines)} "
                f"new={net_name}"
            )
            template = next(
                (label for label in old if isinstance(label, GlobalLabel)), fallback
            )
            stale.extend(direct_lines)
            replacement = GlobalLabel(proto=template.proto)
            replacement.proto.id.value = ""
            replacement.position = position
            replacement.text.position = position
            replacement.text.value = net_name
            replacements.append(replacement)

        if not args.apply:
            return
        if stale:
            schematic.remove_items(stale)
        schematic.create_items(replacements)
        schematic.save()


if __name__ == "__main__":
    main()
