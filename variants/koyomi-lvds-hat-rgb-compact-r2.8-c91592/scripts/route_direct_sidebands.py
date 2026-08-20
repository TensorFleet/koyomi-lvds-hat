#!/usr/bin/env python3
"""Route the three direct panel-sideband FFC contacts using KiCad IPC."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kipy import KiCad
from kipy.board_types import Track, Via
from kipy.geometry import Vector2
from kipy.util import from_mm
from kipy.util.board_layer import layer_from_canonical_name


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "koyomi-lvds-hat.kicad_pcb"
KICAD_CLI = Path(
    "/Users/hyper/projects/tensorfleet/vaio_p_modding/tools/"
    "kicad11-nightly-20260722/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)
sys.path.insert(0, "/Users/hyper/projects/tensorfleet/vaio_cm5_carrier/scripts")
from configure_a3_3_right_io import (  # noqa: E402
    _astar_multilayer,
    _distance_to_segment,
    _layer_obstacles,
)


F_CU = layer_from_canonical_name("F.Cu")
IN1_CU = layer_from_canonical_name("In1.Cu")
IN2_CU = layer_from_canonical_name("In2.Cu")
B_CU = layer_from_canonical_name("B.Cu")
BOUNDS = (91.35, 155.65, 22.35, 49.90)
PIN_MAP = {
    # Each selected redundant power contact already has a short, legal F.Cu
    # fanout to a through-via.  Reusing that escape is substantially safer
    # than forcing a new 0.5 mm-pitch fanout through the dense RGB bundle.
    # Tuple: FFC pin, panel pin, inherited fanout via, candidate destination
    # vias.  Candidate order prefers the short upper-side escape, then the
    # connector's outer side, then the lower-side corridor.
    "PANEL_ID0": {
        "ffc_pin": "17", "panel_pin": "10",
        "anchor": (121.980, 23.7118),
        "stages": (), "auto_layers": None,
        "start_layer": B_CU, "final_layer": B_CU,
        "goal_candidates": (
            (122.10, 44.20), (122.40, 43.90), (121.80, 43.90),
            (121.30, 47.20), (122.00, 47.50),
        ),
    },
    "PANEL_ID1": {
        "ffc_pin": "34", "panel_pin": "21",
        "anchor": (130.401, 23.4886),
        "stages": ((B_CU, (130.40, 25.20)),
                   (IN2_CU, (130.90, 25.60)),
                   (B_CU, (130.40, 28.30)),
                   (IN2_CU, (128.80, 30.40))),
        "auto_layers": None, "start_layer": B_CU,
        "final_layer": B_CU,
        "goal_candidates": (
            (125.70, 48.90), (125.20, 48.90), (126.20, 48.90),
            (123.10, 44.00), (123.00, 43.80),
        ),
    },
    "LCD_INS": {
        "ffc_pin": "39", "panel_pin": "30",
        "anchor": (133.834, 23.3852),
        "stages": ((IN1_CU, (134.60, 23.30)),
                   (B_CU, (132.90, 29.60))),
        "auto_layers": (IN2_CU, B_CU),
        "start_layer": IN2_CU, "final_layer": B_CU,
        "goal_candidates": (
            (129.50, 45.60), (130.50, 44.00), (130.80, 43.70),
            (130.50, 45.00),
            (129.30, 47.20), (130.50, 47.50),
        ),
    },
}


def pad(footprint, number):
    return next(item for item in footprint.definition.pads if item.number == number)


def xy(item):
    return item.position.x / 1e6, item.position.y / 1e6


def add_track(items, net, layer, start, end, width_mm=0.15):
    if start == end:
        return
    track = Track()
    track.start = Vector2.from_xy_mm(*start)
    track.end = Vector2.from_xy_mm(*end)
    track.width = from_mm(width_mm)
    track.layer = layer
    track.net = net
    items.append(track)


def add_via(items, net, point, diameter_mm=0.50, drill_mm=0.25):
    via = Via()
    via.position = Vector2.from_xy_mm(*point)
    via.diameter = from_mm(diameter_mm)
    via.drill_diameter = from_mm(drill_mm)
    via.net = net
    items.append(via)


def create_and_renet(board, items, net, message):
    commit = board.begin_commit()
    try:
        created = board.create_items(items)
        board.push_commit(commit, message)
    except Exception:
        board.drop_commit(commit)
        raise
    live = {item.id.value: item for item in [*board.get_tracks(), *board.get_vias()]}
    updates = []
    for created_item in created:
        item = live[created_item.id.value]
        item.net = net
        updates.append(item)
    commit = board.begin_commit()
    try:
        board.update_items(updates)
        board.push_commit(commit, f"Re-net: {message}")
    except Exception:
        board.drop_commit(commit)
        raise


def point_key(point):
    return round(point[0], 4), round(point[1], 4)


def endpoints(track):
    return (
        point_key((track.start.x / 1e6, track.start.y / 1e6)),
        point_key((track.end.x / 1e6, track.end.y / 1e6)),
    )


def adopt_inherited_fanout(board, start, anchor, net, plan_only):
    """Re-net the old power fanout through its first via to the sideband."""
    start_key = point_key(start)
    anchor_key = point_key(anchor)
    tracks = list(board.get_tracks())
    vias = {point_key(xy(via)): via for via in board.get_vias()}
    first = [track for track in tracks if start_key in endpoints(track)]
    old_names = {track.net.name for track in first if track.net.name != net.name}
    if len(old_names) != 1:
        raise RuntimeError(
            f"expected one inherited net at {start_key}, found {sorted(old_names)}"
        )
    old_name = old_names.pop()
    pending = [start_key]
    visited = set()
    adopted = []
    while pending:
        node = pending.pop()
        if node in visited:
            continue
        visited.add(node)
        for track in tracks:
            if track.layer != F_CU or track.net.name != old_name:
                continue
            a, b = endpoints(track)
            if node not in (a, b) or track in adopted:
                continue
            adopted.append(track)
            other = b if node == a else a
            if other != anchor_key:
                pending.append(other)
    if anchor_key not in vias:
        raise RuntimeError(f"missing inherited fanout via at {anchor_key}")
    anchor_via = vias[anchor_key]
    if not any(anchor_key in endpoints(track) for track in adopted):
        raise RuntimeError(f"fanout from {start_key} did not reach {anchor_key}")
    stale = [
        track for track in tracks
        if track.layer != F_CU and track.net.name == old_name
        and anchor_key in endpoints(track)
    ]
    print(
        f"{net.name}: adopt {len(adopted)} F.Cu fanout segments and via "
        f"{anchor_key}; detach {len(stale)} inherited {old_name} branches"
    )
    # Apply this to the live headless document for dry-runs too; plan-only
    # sessions never save, but the router must see the adopted via as its net.
    commit = board.begin_commit()
    try:
        if stale:
            board.remove_items(stale)
        for item in [*adopted, anchor_via]:
            item.net = net
        board.update_items([*adopted, anchor_via])
        board.push_commit(commit, f"Adopt R2.4 {net.name} FFC fanout")
    except Exception:
        board.drop_commit(commit)
        raise


def restore_repurposed_power_bridge(board, net, plan_only):
    """Reconnect the +3V3 B.Cu/In1 branches formerly joined at pin 17."""
    back_start = (121.980, 27.8973)
    inner_start = (121.037, 22.7680)
    obstacles = via_obstacles(board, net.name)
    midpoint = (
        (back_start[0] + inner_start[0]) / 2,
        (back_start[1] + inner_start[1]) / 2,
    )
    candidates = []
    for ix in range(41):
        x = 119.0 + ix * 0.10
        for iy in range(51):
            y = 22.8 + iy * 0.10
            point = (round(x, 3), round(y, 3))
            if via_is_clear(obstacles, point):
                candidates.append(point)
    candidates.sort(key=lambda point: (
        (point[0] - midpoint[0]) ** 2 + (point[1] - midpoint[1]) ** 2,
        point,
    ))
    failures = []
    for candidate in candidates:
        try:
            back_path = _astar_multilayer(
                board, net.name, back_start, candidate,
                layers=(B_CU,), width_mm=0.30, step=0.10,
                goal_layer=B_CU, clearance_mm=0.15, start_layer=B_CU,
                board_bounds=BOUNDS,
            )
            inner_path = _astar_multilayer(
                board, net.name, inner_start, candidate,
                layers=(IN1_CU,), width_mm=0.30, step=0.10,
                goal_layer=IN1_CU, clearance_mm=0.15,
                start_layer=IN1_CU, board_bounds=BOUNDS,
            )
            break
        except RuntimeError as error:
            failures.append(str(error))
    else:
        raise RuntimeError(
            "unable to restore +3V3 bridge: " + "; ".join(failures[-3:])
        )
    print(f"+3V3 replacement bridge via: {candidate}")
    print(f"+3V3 B.Cu bridge: {back_path}")
    print(f"+3V3 In1 bridge: {inner_path}")
    if plan_only:
        return
    items = []
    for path in (back_path, inner_path):
        for a, b in zip(path, path[1:]):
            add_track(items, net, a[2], a[:2], b[:2], 0.30)
    add_via(items, net, candidate)
    create_and_renet(board, items, net, "Restore R2.4 +3V3 layer bridge")


def remove_abandoned_ground_spur(board):
    """Remove the now-dead GND trunk between repurposed pins 34 and 39."""
    targets = {
        frozenset(((128.1440, 23.4886), (128.7900, 22.8422))),
        frozenset(((128.7900, 22.8422), (133.2910, 22.8422))),
    }
    stale = [
        track for track in board.get_tracks()
        if track.layer == IN2_CU and track.net.name == "GND"
        and frozenset(endpoints(track)) in targets
    ]
    if len(stale) != 2:
        raise RuntimeError(f"expected two abandoned GND tracks, found {len(stale)}")
    commit = board.begin_commit()
    try:
        board.remove_items(stale)
        board.push_commit(commit, "Remove R2.4 abandoned GND FFC spur")
    except Exception:
        board.drop_commit(commit)
        raise


def via_obstacles(board, net_name):
    return [
        _layer_obstacles(board, layer, net_name, 0.50, 0.20)
        for layer in (F_CU, IN1_CU, IN2_CU, B_CU)
    ]


def via_is_clear(obstacles, point):
    for segments, circles, rectangles in obstacles:
        x, y = point
        if any(
            _distance_to_segment(x, y, ax, ay, bx, by) < limit
            for ax, ay, bx, by, limit in segments
        ):
            return False
        if any(
            ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 < limit
            for cx, cy, limit in circles
        ):
            return False
        if any(x0 < x < x1 and y0 < y < y1
               for x0, y0, x1, y1 in rectangles):
            return False
    return True


def route_one(
    board, net, start, goal, anchor, stages, auto_layers, start_layer,
    final_layer, goal_candidates, plan_only
):
    failures = []
    obstacles = via_obstacles(board, net.name)
    stage_paths = []
    main_start = anchor
    if stages is not None:
        for layer, stage_point in stages:
            if not via_is_clear(obstacles, stage_point):
                raise RuntimeError(f"stage via blocked at {stage_point}")
            stage_path = _astar_multilayer(
                board, net.name, main_start, stage_point,
                layers=(layer,), width_mm=0.15, step=0.10,
                goal_layer=layer, clearance_mm=0.15, start_layer=layer,
                board_bounds=BOUNDS,
            )
            stage_paths.append((stage_path, stage_point))
            main_start = stage_point
    for goal_escape in goal_candidates:
        if not via_is_clear(obstacles, goal_escape):
            failures.append(f"{goal_escape}: via blocked")
            continue
        try:
            goal_path = _astar_multilayer(
                board,
                net.name,
                goal,
                goal_escape,
                layers=(F_CU,),
                width_mm=0.10,
                step=0.05,
                goal_layer=F_CU,
                clearance_mm=0.15,
                start_layer=F_CU,
                board_bounds=BOUNDS,
            )
            route_layers = auto_layers or (final_layer,)
            route_start_layer = start_layer
            path = _astar_multilayer(
                board,
                net.name,
                main_start,
                goal_escape,
                layers=route_layers,
                width_mm=0.15,
                via_diameter_mm=0.50,
                step=0.10,
                goal_layer=final_layer,
                clearance_mm=0.15,
                start_layer=route_start_layer,
                board_bounds=BOUNDS,
            )
            break
        except RuntimeError as error:
            failures.append(f"{goal_escape}: {error}")
    else:
        raise RuntimeError("; ".join(failures))
    print(f"{net.name}: destination via {goal_escape}")
    for index, (stage_path, _) in enumerate(stage_paths, 1):
        print(f"{net.name} stage {index}: {stage_path}")
    print(f"{net.name} main: {path}")
    print(f"{net.name} panel fanout: {goal_path}")
    if plan_only:
        return
    items = []
    for stage_path, stage_point in stage_paths:
        for a, b in zip(stage_path, stage_path[1:]):
            add_track(items, net, a[2], a[:2], b[:2])
        add_via(items, net, stage_point)
    for a, b in zip(path, path[1:]):
        if a[2] != b[2]:
            add_via(items, net, a[:2], 0.45, 0.25)
        else:
            add_track(items, net, a[2], a[:2], b[:2])
    add_via(items, net, goal_escape)
    for a, b in zip(goal_path, goal_path[1:]):
        add_track(items, net, F_CU, a[:2], b[:2], 0.10)
    create_and_renet(board, items, net, f"Route R2.4 direct {net.name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--find-vias", action="store_true")
    args = parser.parse_args()
    with KiCad(
        headless=True,
        kicad_cli_path=str(KICAD_CLI),
        file_path=str(BOARD),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        refs = {fp.reference_field.text.value: fp for fp in board.get_footprints()}
        nets = {net.name: net for net in board.get_nets()}
        for net_name, config in PIN_MAP.items():
            if args.only and args.only != net_name:
                continue
            ffc_pin = config["ffc_pin"]
            panel_pin = config["panel_pin"]
            anchor = config["anchor"]
            goal_candidates = config["goal_candidates"]
            start = xy(pad(refs["JFFC1"], ffc_pin))
            goal = xy(pad(refs["J2"], panel_pin))
            adopt_inherited_fanout(
                board, start, anchor, nets[net_name], args.plan_only
            )
            if net_name == "PANEL_ID0":
                restore_repurposed_power_bridge(
                    board, nets["+3V3"], args.plan_only
                )
            elif net_name == "LCD_INS":
                remove_abandoned_ground_spur(board)
            if args.find_vias:
                candidates = []
                obstacles = via_obstacles(board, net_name)
                for ix in range(220):
                    x = 118.0 + ix * 0.10
                    for iy in range(275):
                        y = 22.4 + iy * 0.10
                        point = (round(x, 3), round(y, 3))
                        if via_is_clear(obstacles, point):
                            candidates.append(point)
                candidates.sort(
                    key=lambda point: (
                        (point[0] - goal[0]) ** 2 + (point[1] - goal[1]) ** 2,
                        point,
                    )
                )
                print(f"{net_name} nearest clear vias: {candidates[:40]}")
                by_anchor = sorted(
                    candidates,
                    key=lambda point: (
                        (point[0] - anchor[0]) ** 2
                        + (point[1] - anchor[1]) ** 2,
                        point,
                    ),
                )
                print(f"{net_name} nearest anchor vias: {by_anchor[:40]}")
                for probe in (
                    (130.3, 28.25), (132.9, 29.75),
                    (131.2, 31.45), (128.8, 30.45), (126.0, 36.5),
                ):
                    by_probe = sorted(
                        candidates,
                        key=lambda point: (
                            (point[0] - probe[0]) ** 2
                            + (point[1] - probe[1]) ** 2,
                            point,
                        ),
                    )
                    print(f"{net_name} clear vias near {probe}: {by_probe[:20]}")
                continue
            route_one(
                board, nets[net_name], start, goal,
                anchor, config["stages"], config["auto_layers"],
                config["start_layer"], config["final_layer"],
                goal_candidates, args.plan_only,
            )
        if not args.plan_only:
            for text in board.get_text():
                if text.value == "R2.3 ROUTED":
                    text.value = "R2.4 SIDE IO"
                    commit = board.begin_commit()
                    try:
                        board.update_items(text)
                    board.push_commit(commit, "Update R2.4 revision silkscreen")
                    except Exception:
                        board.drop_commit(commit)
                        raise
                    break
            board.save()


if __name__ == "__main__":
    main()
