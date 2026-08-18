#!/usr/bin/env python3
"""Add the r2.2 consolidated 12-pin LCD backlight FFC through KiCad IPC.

The new connector preserves the legacy J5 pin order on pins 1-6 followed by
the legacy J6 pin order on pins 7-12.  J6 pin 2 was unused and remains marked
no-connect on new pin 8.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from kipy import KiCad
from kipy.geometry import Vector2
from kipy.proto.common.types.enums_pb2 import KiCadObjectType
from kipy.proto.schematic.schematic_types_pb2 import SchematicLabelSpinStyle
from kipy.schematic_types import GlobalLabel, NoConnectMarker, SchematicSymbolInstance


CONNECTOR_REFERENCE = "JBL1"
CONNECTOR_POSITION = (210.0, 115.0)
PIN_X_MM = 204.92
PIN_Y0_MM = 102.30
PIN_PITCH_MM = 2.54

# Keep the briefly tested grid-aligned coordinates so rerunning the script
# repairs any intermediate checkout.  KiCad IPC currently moves the symbol
# instance without moving this imported symbol's absolute pin geometry, so the
# original electrically connected placement remains authoritative.
PREVIOUS_CONNECTOR_POSITION = (210.82, 114.30)
PREVIOUS_PIN_X_MM = 205.74
PREVIOUS_PIN_Y0_MM = 101.60

# Exact legacy ordering: J5.1-J5.6, then J6.1-J6.6.
PIN_NETS = {
    1: "VCD6",
    2: "VCD5",
    3: "VCD4",
    4: "VCD3",
    5: "VCD2",
    6: "VCD1",
    7: "VAD",
    8: None,
    9: "GND",
    10: "+5V",
    11: "PWM",
    12: "EN",
}


def pin_position(pin: int) -> Vector2:
    return Vector2.from_xy_mm(PIN_X_MM, PIN_Y0_MM + (pin - 1) * PIN_PITCH_MM)


def previous_pin_position(pin: int) -> Vector2:
    return Vector2.from_xy_mm(
        PREVIOUS_PIN_X_MM,
        PREVIOUS_PIN_Y0_MM + (pin - 1) * PIN_PITCH_MM,
    )


def same_position(a: Vector2, b: Vector2) -> bool:
    return a.x == b.x and a.y == b.y


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("schematic", type=Path)
    parser.add_argument(
        "--symbol-source",
        type=Path,
        required=True,
        help="KiCad schematic containing a native Connector_Generic:Conn_01x12",
    )
    parser.add_argument("--kicad-cli", required=True)
    args = parser.parse_args()

    schematic_path = args.schematic.resolve()
    symbol_source_path = args.symbol_source.resolve()

    # KiCad returns the full embedded symbol definition.  Retain that native
    # definition rather than constructing a schematic symbol by hand.
    with KiCad(
        headless=True,
        kicad_cli_path=args.kicad_cli,
        file_path=str(symbol_source_path),
        timeout_ms=60_000,
    ) as kicad:
        source_schematic = kicad.get_schematic()
        source = next(
            symbol
            for symbol in source_schematic.get_symbols()
            if symbol.reference_field.text.value == "JSD1"
            and symbol.definition.id.name == "Conn_01x12"
        )
        connector_template = SchematicSymbolInstance(proto=source.proto)

    with KiCad(
        headless=True,
        kicad_cli_path=args.kicad_cli,
        file_path=str(schematic_path),
        timeout_ms=60_000,
    ) as kicad:
        schematic = kicad.get_schematic()
        symbols = list(schematic.get_symbols())
        connector = next(
            (
                symbol
                for symbol in symbols
                if symbol.reference_field.text.value == CONNECTOR_REFERENCE
            ),
            None,
        )

        if connector is None:
            root_path = next(
                symbol for symbol in symbols if symbol.reference_field.text.value == "J3"
            ).path
            connector_template.proto.id.value = ""
            connector_template.path = root_path
            connector_template.reference_field.text.value = CONNECTOR_REFERENCE
            connector_template.value_field.text.value = "BACKLIGHT FFC-12"
            connector_template.footprint_field.text.value = (
                "Connector_FFC-FPC:"
                "Hirose_FH12-12S-0.5SH_1x12-1MP_P0.50mm_Horizontal"
            )
            connector_template.description_field.text.value = (
                "12-position 0.5 mm FFC carrying the complete legacy J5/J6 "
                "LCD backlight interface"
            )
            attributes = connector_template.attributes
            attributes.exclude_from_bill_of_materials = False
            attributes.exclude_from_board = False
            attributes.exclude_from_position_files = False
            attributes.do_not_populate = False
            connector_template.attributes = attributes
            # The source symbol is already natively located here, including
            # its embedded pin geometry and fields.
            connector_template.position = Vector2.from_xy_mm(*CONNECTOR_POSITION)
            connector = schematic.create_items(connector_template)[0]
        else:
            connector.position = Vector2.from_xy_mm(*CONNECTOR_POSITION)
            schematic.update_items([connector])

        labels = list(schematic.get_labels())
        label_template = next(
            label
            for label in labels
            if isinstance(label, GlobalLabel) and label.text.value == "VCD6"
        )
        create = []
        update = []
        remove = []
        for pin, net in PIN_NETS.items():
            pos = pin_position(pin)
            previous_pos = previous_pin_position(pin)
            if net is None:
                existing_nc = schematic.get_items(KiCadObjectType.KOT_SCH_NO_CONNECT)
                current = next(
                    (item for item in existing_nc if same_position(item.position, pos)),
                    None,
                )
                previous = next(
                    (
                        item
                        for item in existing_nc
                        if same_position(item.position, previous_pos)
                    ),
                    None,
                )
                if current is None and previous is not None:
                    previous.position = pos
                    update.append(previous)
                elif current is not None and previous is not None:
                    remove.append(previous)
                elif current is None:
                    marker = NoConnectMarker()
                    marker.position = pos
                    marker.size = 1_270_000
                    create.append(marker)
                continue

            current = next(
                (
                    label
                    for label in labels
                    if isinstance(label, GlobalLabel)
                    and label.text.value == net
                    and same_position(label.position, pos)
                ),
                None,
            )
            previous = next(
                (
                    label
                    for label in labels
                    if isinstance(label, GlobalLabel)
                    and label.text.value == net
                    and same_position(label.position, previous_pos)
                ),
                None,
            )
            if current is not None:
                if previous is not None:
                    remove.append(previous)
                continue
            if previous is not None:
                previous.position = pos
                previous.text.position = pos
                update.append(previous)
                continue
            if any(
                isinstance(label, GlobalLabel)
                and label.text.value == net
                and same_position(label.position, pos)
                for label in labels
            ):
                continue
            label = GlobalLabel(proto=label_template.proto)
            label.proto.id.value = ""
            label.position = pos
            label.text.position = pos
            label.text.value = net
            label.spin_style = SchematicLabelSpinStyle.SLSS_LEFT
            create.append(label)

        schematic.create_items(create)
        schematic.update_items(update)
        # Moving this imported connector was only a short-lived experiment.
        # Delete any duplicate labels left at those abandoned coordinates;
        # the authoritative labels above remain attached to the real pins.
        for pin, net in PIN_NETS.items():
            if net is None:
                continue
            stale_pos = previous_pin_position(pin)
            remove.extend(
                label
                for label in labels
                if isinstance(label, GlobalLabel)
                and label.text.value == net
                and same_position(label.position, stale_pos)
                and label not in remove
            )
        schematic.remove_items(remove)
        schematic.save()


if __name__ == "__main__":
    main()
