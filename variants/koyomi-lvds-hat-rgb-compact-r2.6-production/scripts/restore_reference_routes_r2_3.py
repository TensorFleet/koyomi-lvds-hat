#!/usr/bin/env python3
"""Restore the known-good low-speed routes and move the +3V3 FFC escape."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from kipy import KiCad
from kipy.board_types import Track


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "koyomi-lvds-hat.kicad_pcb"
REFERENCE_DSN = ROOT / "router" / "koyomi-lvds-hat-r2.3-complete.dsn"
KICAD_CLI = Path(
    "/Users/hyper/projects/tensorfleet/vaio_p_modding/tools/"
    "kicad11-nightly-20260722/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from finalize_r2_3 import (  # noqa: E402
    BOARD_BOUNDS,
    F_CU,
    IN1_CU,
    add_track,
    add_via,
    create_and_renet,
    deduplicate_copper,
    remove_net_copper,
)

ROUTER_HELPERS = Path("/Users/hyper/projects/tensorfleet/vaio_cm5_carrier/scripts")
sys.path.insert(0, str(ROUTER_HELPERS))
from configure_a3_3_right_io import _astar_multilayer  # noqa: E402


TARGETS = {"B0", "G4", "R1", "VSYNC"}
LAYERS = {"F.Cu": 3, "In1.Cu": 4, "In2.Cu": 5, "B.Cu": 34}
WIRE_RE = re.compile(
    r"^\s*\(wire \(path (\S+) ([\d.]+)\s+(.+?)\)"
    r"\(net (.+?)\)\(type protect\)\)\s*$"
)
VIA_RE = re.compile(
    r'^\s*\(via "Via\[0-3\]_(\d+):(\d+)_um"\s+'
    r"(-?[\d.]+)\s+(-?[\d.]+)\s+\(net (.+?)\)"
    r"\(type protect\)\)\s*$"
)
NUMBER_RE = re.compile(r"-?[\d.]+")


def unquote(value):
    value = value.strip()
    return value[1:-1] if value.startswith('"') and value.endswith('"') else value


def restore_reference_routes(board, nets):
    remove_net_copper(board, TARGETS)
    items = []
    for line in REFERENCE_DSN.read_text(encoding="utf-8").splitlines():
        match = WIRE_RE.match(line)
        if match:
            layer_name, width_um, coordinates, raw_net = match.groups()
            net_name = unquote(raw_net)
            if net_name not in TARGETS:
                continue
            values = [float(value) for value in NUMBER_RE.findall(coordinates)]
            points = [
                (values[i] / 1000.0, -values[i + 1] / 1000.0)
                for i in range(0, len(values), 2)
            ]
            for start, end in zip(points, points[1:]):
                add_track(
                    items, nets[net_name], LAYERS[layer_name],
                    start, end, float(width_um) / 1000.0,
                )
            continue
        match = VIA_RE.match(line)
        if match:
            diameter_um, drill_um, x_um, y_um, raw_net = match.groups()
            net_name = unquote(raw_net)
            if net_name not in TARGETS:
                continue
            add_via(
                items,
                nets[net_name],
                (float(x_um) / 1000.0, -float(y_um) / 1000.0),
                float(diameter_um) / 1000.0,
                float(drill_um) / 1000.0,
            )
    create_and_renet(board, items, "Restore R2.3 reference low-speed routes")
    print(f"restored {len(items)} reference items")


def move_3v3_escape(board, nets):
    stale = []
    for item in [*board.get_tracks(), *board.get_vias()]:
        if item.net.name != "+3V3":
            continue
        points = (item.start, item.end) if isinstance(item, Track) else (item.position,)
        if all(
            112.50 <= point.x / 1e6 <= 114.40
            and 22.65 <= point.y / 1e6 <= 26.90
            for point in points
        ):
            stale.append(item)
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, "Move R2.3 +3V3 FFC escape above VSYNC")
        except Exception:
            board.drop_commit(commit)
            raise

    start = (112.90, 22.90)
    goal = (114.17, 26.789)
    path = _astar_multilayer(
        board,
        "+3V3",
        start,
        goal,
        layers=(IN1_CU,),
        width_mm=0.30,
        via_diameter_mm=0.45,
        step=0.10,
        goal_layer=IN1_CU,
        clearance_mm=0.15,
        start_layer=IN1_CU,
        board_bounds=BOARD_BOUNDS,
    )
    items = []
    add_track(items, nets["+3V3"], F_CU, (113.75, 22.71), start, 0.15)
    add_via(items, nets["+3V3"], start, 0.45, 0.20)
    for a, b in zip(path, path[1:]):
        add_track(items, nets["+3V3"], IN1_CU, a[:2], b[:2], 0.30)
    create_and_renet(board, items, "Route R2.3 +3V3 escape above VSYNC")
    print(f"+3V3 escape: {len(path)} vertices / {len(items)} items")


def main():
    with KiCad(
        headless=True,
        kicad_cli_path=str(KICAD_CLI),
        file_path=str(BOARD),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        nets = {net.name: net for net in board.get_nets()}
        restore_reference_routes(board, nets)
        move_3v3_escape(board, nets)
        print(f"removed {deduplicate_copper(board)} duplicate items")
        board.refill_zones(block=True, max_poll_seconds=60.0)
        board.save()
        print(f"saved {board.name}")


if __name__ == "__main__":
    main()
