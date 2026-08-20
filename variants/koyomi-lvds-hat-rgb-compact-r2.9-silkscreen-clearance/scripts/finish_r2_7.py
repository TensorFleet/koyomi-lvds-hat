#!/usr/bin/env python3
"""Close the final R2.7 routes through KiCad's official IPC API."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kipy import KiCad


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from finalize_r2_3 import (  # noqa: E402
    B_CU,
    F_CU,
    IN1_CU,
    IN2_CU,
    add_track,
    add_via,
    create_and_renet,
)

ROUTER_HELPERS = Path(
    "/Users/hyper/projects/tensorfleet/vaio_cm5_carrier/scripts"
)
sys.path.insert(0, str(ROUTER_HELPERS))
from configure_a3_3_right_io import _astar_multilayer  # noqa: E402


BOARD_BOUNDS = (91.0, 149.0, 21.5, 44.2)
TOP_ROUTE_BOUNDS = (91.3, 148.7, 22.4, 43.9)


def add_path(board, net, path, message: str) -> None:
    items = []
    for start, end in zip(path, path[1:]):
        if start[2] != end[2]:
            add_via(items, net, start[:2], 0.45, 0.20)
        else:
            add_track(items, net, start[2], start[:2], end[:2], 0.15)
    create_and_renet(board, items, message)


def remove_exact_track(board, net_name: str, point_a, point_b) -> None:
    wanted = {point_a, point_b}
    matches = []
    for track in board.get_tracks():
        if track.net.name != net_name:
            continue
        endpoints = {
            (round(track.start.x / 1e6, 4), round(track.start.y / 1e6, 4)),
            (round(track.end.x / 1e6, 4), round(track.end.y / 1e6, 4)),
        }
        if endpoints == wanted:
            matches.append(track)
    if len(matches) != 1:
        raise RuntimeError(f"expected one {net_name} track {wanted}, got {len(matches)}")
    commit = board.begin_commit()
    try:
        board.remove_items(matches)
        board.push_commit(commit, f"Open R2.7 {net_name} path for G1 escape")
    except Exception:
        board.drop_commit(commit)
        raise


def remove_exact_via(board, net_name: str, point) -> None:
    matches = [
        via
        for via in board.get_vias()
        if via.net.name == net_name
        and (round(via.position.x / 1e6, 4), round(via.position.y / 1e6, 4))
        == point
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {net_name} via {point}, got {len(matches)}")
    commit = board.begin_commit()
    try:
        board.remove_items(matches)
        board.push_commit(commit, f"Remove obsolete R2.7 {net_name} transition")
    except Exception:
        board.drop_commit(commit)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("--kicad-cli", required=True)
    args = parser.parse_args()

    with KiCad(
        headless=True,
        kicad_cli_path=args.kicad_cli,
        file_path=str(args.board.resolve()),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        nets = {net.name: net for net in board.get_nets()}

        # The +2V5 tree already terminates on a via beside C5.  Route the local
        # branch around the adjacent C4 ground pad and panel connector fanout.
        power_path = _astar_multilayer(
            board,
            "+2V5",
            (121.8375, 38.1000),
            (119.3441, 38.7641),
            layers=(F_CU,),
            width_mm=0.15,
            step=0.025,
            goal_layer=F_CU,
            clearance_mm=0.15,
            start_layer=F_CU,
            board_bounds=BOARD_BOUNDS,
            max_states=500_000,
        )
        add_path(
            board,
            nets["+2V5"],
            power_path,
            "Close R2.7 C5 +2V5 branch",
        )
        board.save()

        # Four top-layer spans cross the only all-layer-clear through-via
        # corridor for G1.  Bridge the three signal paths on other layers; the
        # short GND span is redundant once the ground zones are refilled.
        remove_exact_track(board, "R2", (123.3359, 25.4375), (108.3892, 25.4375))
        remove_exact_track(board, "G3", (123.1580, 25.9338), (114.5051, 25.9338))
        remove_exact_track(board, "CLKIN", (122.8637, 26.3138), (117.5559, 26.3138))
        remove_exact_track(board, "CLKIN", (123.1627, 26.6128), (122.8637, 26.3138))
        remove_exact_track(board, "CLKIN", (123.8355, 26.6128), (123.1627, 26.6128))
        remove_exact_via(board, "CLKIN", (123.8355, 26.6128))
        remove_exact_track(board, "GND", (120.1279, 26.6196), (118.2949, 26.6196))

        escape = (118.7500, 24.1000)
        escape_items = []
        add_track(
            escape_items,
            nets["G1"],
            F_CU,
            (118.7500, 28.1900),
            (118.7300, 27.9500),
            0.15,
        )
        add_track(
            escape_items,
            nets["G1"],
            F_CU,
            (118.7300, 27.9500),
            (118.7300, 24.3000),
            0.15,
        )
        add_track(
            escape_items,
            nets["G1"],
            F_CU,
            (118.7300, 24.3000),
            escape,
            0.15,
        )
        add_via(escape_items, nets["G1"], escape, 0.45, 0.20)
        create_and_renet(board, escape_items, "Escape R2.7 JFFC1 G1")
        board.save()

        restored_paths = {
            "R2": (
                (108.3892, 25.4375, F_CU),
                (114.8000, 25.4375, F_CU),
                (115.7500, 24.1000, F_CU),
                (115.7500, 24.1000, B_CU),
                (115.7500, 22.5000, B_CU),
                (120.7500, 22.5000, B_CU),
                (120.7500, 24.1000, B_CU),
                (120.7500, 24.1000, F_CU),
                (122.0000, 25.4375, F_CU),
                (123.3359, 25.4375, F_CU),
            ),
            "G3": (
                (114.5051, 25.9338, F_CU),
                (115.0000, 25.9338, F_CU),
                (116.7500, 24.1000, F_CU),
                (116.7500, 24.1000, B_CU),
                (116.7500, 23.3000, B_CU),
                (119.7500, 23.3000, B_CU),
                (119.7500, 24.1000, B_CU),
                (119.7500, 24.1000, F_CU),
                (121.6000, 25.9338, F_CU),
                (123.1580, 25.9338, F_CU),
            ),
        }
        for net_name, restored in restored_paths.items():
            add_path(
                board,
                nets[net_name],
                restored,
                f"Restore R2.7 {net_name} around G1",
            )
            board.save()
            print(f"{net_name} path: {restored}")

        clkin_escape = (117.7500, 24.1000)
        clkin_items = []
        add_track(
            clkin_items,
            nets["CLKIN"],
            F_CU,
            (117.5559, 26.3138),
            clkin_escape,
            0.15,
        )
        add_via(clkin_items, nets["CLKIN"], clkin_escape, 0.45, 0.20)
        create_and_renet(board, clkin_items, "Escape R2.7 CLKIN around G1")
        board.save()
        clkin_path = _astar_multilayer(
            board,
            "CLKIN",
            clkin_escape,
            (123.8355, 26.6129),
            layers=(B_CU,),
            width_mm=0.15,
            step=0.025,
            goal_layer=B_CU,
            clearance_mm=0.15,
            start_layer=B_CU,
            board_bounds=BOARD_BOUNDS,
            max_states=500_000,
        )
        add_path(board, nets["CLKIN"], clkin_path, "Bridge R2.7 CLKIN around G1")
        board.save()
        print(f"CLKIN path: {clkin_path}")

        path = _astar_multilayer(
            board,
            "G1",
            escape,
            (128.5886, 34.5000),
            layers=(B_CU,),
            width_mm=0.15,
            via_diameter_mm=0.45,
            step=0.025,
            goal_layer=B_CU,
            clearance_mm=0.15,
            start_layer=B_CU,
            board_bounds=BOARD_BOUNDS,
            max_states=1_000_000,
            surface_step_cost=1.5,
            via_clearance_mm=0.15,
        )
        add_path(board, nets["G1"], path, "Route R2.7 residual G1")
        board.save()
        print(f"G1 path: {path}")

        # Route the split ground span explicitly on F.Cu. Plane-only ties are
        # not sufficient here: the narrow support strip isolates candidate
        # stitching vias after the zones are refilled.
        ground_path = _astar_multilayer(
            board,
            "GND",
            (118.2949, 26.6196),
            (120.1279, 26.6196),
            layers=(F_CU,),
            width_mm=0.15,
            step=0.05,
            goal_layer=F_CU,
            clearance_mm=0.15,
            start_layer=F_CU,
            board_bounds=BOARD_BOUNDS,
            max_states=1_000_000,
        )
        add_path(board, nets["GND"], ground_path, "Bridge R2.7 GND around G1")
        board.save()
        print(f"GND path: {ground_path}")


if __name__ == "__main__":
    main()
