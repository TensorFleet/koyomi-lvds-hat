#!/usr/bin/env python3
"""Declare the three incoming harness rails as power sources via KiCad IPC."""

from __future__ import annotations

import argparse
from pathlib import Path

from kipy import KiCad
from kipy.proto.common.types.base_types_pb2 import ElectricalPinType
from kipy.proto.schematic import schematic_types_pb2


SOURCE_PINS = {"1": "+3V3", "2": "+5V", "6": "GND"}
PASSIVE_PINS = {"3": "VSYNC"}


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
        found = set()
        for child in jffc.proto.definition.items:
            if not child.item.type_url.endswith("SchematicPin"):
                continue
            pin = schematic_types_pb2.SchematicPin()
            if not child.item.Unpack(pin):
                continue
            if pin.number in SOURCE_PINS:
                print(
                    f"JFFC1.{pin.number} {SOURCE_PINS[pin.number]}: "
                    f"{pin.electrical_type} -> "
                    f"{ElectricalPinType.EPT_POWER_OUTPUT}"
                )
                pin.electrical_type = ElectricalPinType.EPT_POWER_OUTPUT
                found.add(pin.number)
            elif pin.number in PASSIVE_PINS:
                print(
                    f"JFFC1.{pin.number} {PASSIVE_PINS[pin.number]}: "
                    f"{pin.electrical_type} -> {ElectricalPinType.EPT_PASSIVE}"
                )
                pin.electrical_type = ElectricalPinType.EPT_PASSIVE
            else:
                continue
            child.item.Pack(pin)
        if found != set(SOURCE_PINS):
            raise RuntimeError(f"missing JFFC1 power pins: {set(SOURCE_PINS) - found}")
        if not args.apply:
            return
        commit = schematic.begin_commit()
        try:
            schematic.update_items(jffc)
            schematic.push_commit(commit, "Declare JFFC1 harness power sources")
        except Exception:
            schematic.drop_commit(commit)
            raise
        schematic.save()


if __name__ == "__main__":
    main()
