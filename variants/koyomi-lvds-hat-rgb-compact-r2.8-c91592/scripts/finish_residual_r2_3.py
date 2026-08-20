#!/usr/bin/env python3
"""Route the final R2.3 signal and ground opens through KiCad IPC.

This pass operates on the clean checkpoint produced by ``finalize_r2_3.py``.
It uses the collision-aware router maintained with the CM5 carrier and saves
after every completed net so an unsuccessful candidate never corrupts a
previously verified route.
"""

from __future__ import annotations

import sys
from pathlib import Path

from kipy import KiCad
from kipy.geometry import Vector2
from kipy.util import from_mm


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "koyomi-lvds-hat.kicad_pcb"
KICAD_CLI = Path(
    "/Users/hyper/projects/tensorfleet/vaio_p_modding/tools/"
    "kicad11-nightly-20260722/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from finalize_r2_3 import (  # noqa: E402
    B_CU,
    BOARD_BOUNDS,
    F_CU,
    IN1_CU,
    IN2_CU,
    add_track,
    add_via,
    create_and_renet,
    deduplicate_copper,
    remove_net_copper,
)

ROUTER_HELPERS = Path("/Users/hyper/projects/tensorfleet/vaio_cm5_carrier/scripts")
sys.path.insert(0, str(ROUTER_HELPERS))
from configure_a3_3_right_io import _astar_multilayer  # noqa: E402


SIGNALS = (
    ("VSYNC", (100.90, 30.20), (114.75, 22.71)),
)

# The ground locations are the endpoints reported by the clean-checkpoint DRC.
# Each is escaped to the continuous In1.Cu ground reference plane.
GROUND_STARTS = (
    (118.75, 39.96),
    (120.25, 39.96),
    (120.25, 32.70),
    (121.75, 32.70),
    (122.75, 32.70),
    (124.25, 32.70),
    (126.75, 33.3401),
    (128.25, 32.70),
    (129.75, 32.70),
    (127.25, 39.96),
    (128.75, 39.96),
    (143.25, 42.15),
)


def create_path(board, net, path, message):
    items = []
    for start, end in zip(path, path[1:]):
        if start[2] != end[2]:
            add_via(items, net, start[:2], 0.45, 0.20)
        else:
            add_track(items, net, start[2], start[:2], end[:2], 0.15)
    create_and_renet(board, items, message)
    return len(items)


def route_signal(board, nets, net_name, start, goal, *, clearance_mm=0.18):
    remove_net_copper(board, {net_name})
    # Try progressively richer layer sets.  Completed copper remains an
    # obstacle, so these paths cannot silently disturb the verified fanout.
    attempts = (
        (IN2_CU,),
        (B_CU,),
        (IN1_CU, IN2_CU, B_CU),
    )
    failures = []
    for inner_layers in attempts:
        try:
            path = _astar_multilayer(
                board,
                net_name,
                start,
                goal,
                layers=(F_CU, *inner_layers),
                width_mm=0.15,
                via_diameter_mm=0.45,
                step=0.10,
                goal_layer=F_CU,
                clearance_mm=clearance_mm,
                start_layer=F_CU,
                board_bounds=BOARD_BOUNDS,
            )
            count = create_path(board, nets[net_name], path, f"Route R2.3 residual {net_name}")
            board.save()
            print(f"{net_name}: {len(path)} vertices / {count} items")
            return
        except RuntimeError as exc:
            failures.append(str(exc))
    raise RuntimeError(f"all residual route attempts failed for {net_name}: {failures[-1]}")


def route_d18(board, nets):
    """Escape both dense endpoints before crossing the board on In2.Cu."""
    remove_net_copper(board, {"D18"})
    source_pad = (138.10, 27.80)
    goal_pad = (121.25, 32.70)
    selected = None
    last_error = None
    for layer in (IN2_CU, B_CU, IN1_CU):
        for source_via in (
            (137.20, 27.80), (136.80, 27.80), (137.20, 26.80),
        ):
            for goal_via in (
                (120.90, 31.60), (120.95, 31.55),
                (120.85, 31.60), (121.00, 31.50),
            ):
                try:
                    path = _astar_multilayer(
                        board,
                        "D18",
                        source_via,
                        goal_via,
                        layers=(layer,),
                        width_mm=0.15,
                        via_diameter_mm=0.45,
                        step=0.10,
                        goal_layer=layer,
                        clearance_mm=0.15,
                        start_layer=layer,
                        board_bounds=BOARD_BOUNDS,
                    )
                    selected = (layer, source_via, goal_via, path)
                    break
                except RuntimeError as exc:
                    last_error = exc
            if selected:
                break
        if selected:
            break
    if not selected:
        raise RuntimeError(f"no escaped D18 route: {last_error}")
    layer, source_via, goal_via, path = selected
    items = []
    add_track(items, nets["D18"], F_CU, source_pad, source_via, 0.15)
    add_via(items, nets["D18"], source_via, 0.45, 0.20)
    for start, end in zip(path, path[1:]):
        add_track(items, nets["D18"], layer, start[:2], end[:2], 0.15)
    add_via(items, nets["D18"], goal_via, 0.45, 0.20)
    escape_corner = (goal_pad[0], goal_via[1])
    add_track(items, nets["D18"], F_CU, goal_via, escape_corner, 0.15)
    add_track(items, nets["D18"], F_CU, escape_corner, goal_pad, 0.15)
    create_and_renet(board, items, "Route R2.3 residual D18")
    board.save()
    print(f"D18: {len(path)} vertices / {len(items)} items")


def rework_d15_front_escape(board, nets):
    """Move D15's IC-side approach to In1 so D18 gets a front escape lane."""
    threshold = from_mm(118.40)
    stale = []
    for track in board.get_tracks():
        if track.net.name != "D15":
            continue
        if track.layer == IN1_CU or (
            track.layer == F_CU and max(track.start.x, track.end.x) >= threshold
        ):
            stale.append(track)
    stale.extend(
        via
        for via in board.get_vias()
        if via.net.name == "D15" and via.position.x > from_mm(118.60)
    )
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, "Open D18 lane beside D15")
        except Exception:
            board.drop_commit(commit)
            raise
    start = (118.50, 30.65)
    goal_via = (123.25, 31.50)
    path = _astar_multilayer(
        board,
        "D15",
        start,
        goal_via,
        layers=(IN1_CU,),
        width_mm=0.15,
        via_diameter_mm=0.45,
        step=0.10,
        goal_layer=IN1_CU,
        clearance_mm=0.15,
        start_layer=IN1_CU,
        board_bounds=BOARD_BOUNDS,
    )
    items = []
    for path_start, path_end in zip(path, path[1:]):
        add_track(items, nets["D15"], IN1_CU, path_start[:2], path_end[:2], 0.15)
    add_via(items, nets["D15"], goal_via, 0.45, 0.20)
    add_track(items, nets["D15"], F_CU, goal_via, (123.25, 32.70), 0.15)
    create_and_renet(board, items, "Rework R2.3 D15 IC escape")
    board.save()
    print(
        f"D15 front escape: removed {len(stale)} / "
        f"added {len(items)} items ({len(path)} vertices)"
    )


def rework_d14_front_escape(board, nets):
    """Move D14's short F.Cu tail left to open the adjacent GND lane."""
    stale = [
        track
        for track in board.get_tracks()
        if track.net.name == "D14"
        and track.layer == F_CU
        and max(track.start.x, track.end.x) >= from_mm(123.70)
    ]
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, "Open IC1 pad 13 ground escape beside D14")
        except Exception:
            board.drop_commit(commit)
            raise
    items = []
    points = ((124.40, 29.50), (123.75, 30.15), (123.75, 32.70))
    for point_a, point_b in zip(points, points[1:]):
        add_track(items, nets["D14"], F_CU, point_a, point_b, 0.15)
    create_and_renet(board, items, "Rework R2.3 D14 IC escape")
    board.save()
    print(f"D14 front escape: removed {len(stale)} / added {len(items)} items")


def rework_d8_front_escape(board, nets):
    """Move D8's short F.Cu approach left to open IC1 pad 5 GND."""
    x0, x1 = from_mm(127.74), from_mm(129.71)
    y0, y1 = from_mm(29.79), from_mm(32.71)
    stale = []
    for track in board.get_tracks():
        if track.net.name != "D8" or track.layer != F_CU:
            continue
        if all(
            x0 <= point.x <= x1 and y0 <= point.y <= y1
            for point in (track.start, track.end)
        ):
            stale.append(track)
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, "Open IC1 pad 5 ground escape beside D8")
        except Exception:
            board.drop_commit(commit)
            raise
    points = (
        (127.75, 32.70),
        (127.75, 32.20),
        (127.90, 32.05),
        (127.90, 29.80),
        (129.705, 29.80),
        (129.705, 30.2001),
    )
    items = []
    for point_a, point_b in zip(points, points[1:]):
        add_track(items, nets["D8"], F_CU, point_a, point_b, 0.15)
    create_and_renet(board, items, "Rework R2.3 D8 IC escape")
    board.save()
    print(f"D8 front escape: removed {len(stale)} / added {len(items)} items")


def rework_3v3_d18_bypass(board, nets):
    """Replace the two overlapping B.Cu diagonals with one clear branch."""
    target_pairs = {
        frozenset(((from_mm(120.00), from_mm(33.00)), (from_mm(122.30), from_mm(30.70)))),
        frozenset(((from_mm(120.20), from_mm(33.00)), (from_mm(122.50), from_mm(30.70)))),
    }
    stale = []
    for track in board.get_tracks():
        if track.net.name != "+3V3" or track.layer != B_CU:
            continue
        endpoints = frozenset(
            ((track.start.x, track.start.y), (track.end.x, track.end.y))
        )
        if endpoints in target_pairs:
            stale.append(track)
    if not stale:
        print("+3V3 D18 bypass: original diagonals already absent")
        return
    commit = board.begin_commit()
    try:
        board.remove_items(stale)
        board.push_commit(commit, "Open D18 via clearance in +3V3 branch")
    except Exception:
        board.drop_commit(commit)
        raise
    path = _astar_multilayer(
        board,
        "+3V3",
        (120.00, 33.00),
        (122.30, 30.70),
        layers=(B_CU,),
        width_mm=0.15,
        via_diameter_mm=0.45,
        step=0.10,
        goal_layer=B_CU,
        clearance_mm=0.15,
        start_layer=B_CU,
        board_bounds=BOARD_BOUNDS,
    )
    items = []
    for start, end in zip(path, path[1:]):
        add_track(items, nets["+3V3"], B_CU, start[:2], end[:2], 0.15)
    create_and_renet(board, items, "Route +3V3 around D18 escape")
    board.save()
    print(
        f"+3V3 D18 bypass: removed {len(stale)} / "
        f"added {len(items)} items ({len(path)} vertices)"
    )


def route_vsync(board, nets):
    """Use the known-clear RN1 escape and move the second via off B0."""
    remove_net_copper(board, {"VSYNC"})
    source_pad = (100.90, 30.20)
    source_via = (101.709, 30.20)
    goal_pad = (114.75, 22.71)
    selected = None
    last_error = None
    attempts = (
        ((IN2_CU,), IN2_CU, IN2_CU),
        ((B_CU,), B_CU, B_CU),
        ((IN1_CU,), IN1_CU, IN1_CU),
        ((IN1_CU, IN2_CU, B_CU), IN2_CU, B_CU),
        ((IN1_CU, IN2_CU, B_CU), B_CU, IN1_CU),
    )
    for layers, start_layer, goal_layer in attempts:
        for goal_via in ((114.75, 24.20), (114.75, 24.60), (115.00, 24.40)):
            try:
                path = _astar_multilayer(
                    board,
                    "VSYNC",
                    source_via,
                    goal_via,
                    layers=layers,
                    width_mm=0.15,
                    via_diameter_mm=0.45,
                    step=0.10,
                    goal_layer=goal_layer,
                    clearance_mm=0.15,
                    start_layer=start_layer,
                    board_bounds=BOARD_BOUNDS,
                )
                selected = (goal_via, path)
                break
            except RuntimeError as exc:
                last_error = exc
        if selected:
            break
    if not selected:
        raise RuntimeError(f"no VSYNC inner route: {last_error}")
    goal_via, path = selected
    items = []
    add_track(items, nets["VSYNC"], F_CU, source_pad, source_via, 0.15)
    add_via(items, nets["VSYNC"], source_via, 0.45, 0.20)
    for start, end in zip(path, path[1:]):
        if start[2] != end[2]:
            add_via(items, nets["VSYNC"], start[:2], 0.45, 0.20)
        else:
            add_track(items, nets["VSYNC"], start[2], start[:2], end[:2], 0.15)
    add_via(items, nets["VSYNC"], goal_via, 0.45, 0.20)
    add_track(items, nets["VSYNC"], F_CU, goal_via, goal_pad, 0.15)
    create_and_renet(board, items, "Route R2.3 residual VSYNC")
    board.save()
    print(f"VSYNC: {len(path)} vertices / {len(items)} items")


def route_b0_manual(board, nets):
    """Escape B0 at both ends and cross below the crowded front layer."""
    remove_net_copper(board, {"B0"})
    source_pad = (100.90, 28.60)
    goal_pad = (116.75, 22.71)
    selected = None
    last_error = None
    attempts = (
        ((IN2_CU,), IN2_CU, IN2_CU),
        ((B_CU,), B_CU, B_CU),
        ((IN1_CU,), IN1_CU, IN1_CU),
        ((IN1_CU, IN2_CU, B_CU), IN2_CU, B_CU),
    )
    for layers, start_layer, goal_layer in attempts:
        for source_via in ((99.80, 26.80), (100.00, 26.50), (101.50, 27.00)):
            for goal_via in ((116.75, 23.50), (116.75, 24.00), (117.20, 24.00)):
                try:
                    path = _astar_multilayer(
                        board,
                        "B0",
                        source_via,
                        goal_via,
                        layers=layers,
                        width_mm=0.15,
                        via_diameter_mm=0.45,
                        step=0.10,
                        goal_layer=goal_layer,
                        clearance_mm=0.16,
                        start_layer=start_layer,
                        board_bounds=BOARD_BOUNDS,
                    )
                    selected = (source_via, goal_via, path)
                    break
                except RuntimeError as exc:
                    last_error = exc
            if selected:
                break
        if selected:
            break
    if not selected:
        raise RuntimeError(f"no escaped B0 route: {last_error}")
    source_via, goal_via, path = selected
    items = []
    add_track(items, nets["B0"], F_CU, source_pad, source_via, 0.15)
    add_via(items, nets["B0"], source_via, 0.45, 0.20)
    for start, end in zip(path, path[1:]):
        if start[2] != end[2]:
            add_via(items, nets["B0"], start[:2], 0.45, 0.20)
        else:
            add_track(items, nets["B0"], start[2], start[:2], end[:2], 0.15)
    add_via(items, nets["B0"], goal_via, 0.45, 0.20)
    add_track(items, nets["B0"], F_CU, goal_via, goal_pad, 0.15)
    create_and_renet(board, items, "Route R2.3 B0 around VSYNC")
    board.save()
    print(f"B0: {len(items)} front-layer items")


def ground_goals(start):
    x, y = start
    outward = -1.40 if y < 36.0 else 1.40
    # Spread candidates sideways so densely packed TSSOP pads can fan out
    # without stacking their through vias.
    for dx in (
        0.0, -0.50, 0.50, -0.90, 0.90, -1.30, 1.30, -1.80, 1.80, -2.30, 2.30
    ):
        for extra_y in (0.0, -0.40 if outward < 0 else 0.40):
            yield (x + dx, y + outward + extra_y)


def route_ground_drop(board, nets, start, index, clearance_mm=0.25):
    failures = []
    for goal in ground_goals(start):
        try:
            path = _astar_multilayer(
                board,
                "GND",
                start,
                goal,
                layers=(F_CU, IN1_CU),
                width_mm=0.15,
                via_diameter_mm=0.45,
                step=0.10,
                goal_layer=IN1_CU,
                clearance_mm=clearance_mm,
                start_layer=F_CU,
                board_bounds=BOARD_BOUNDS,
            )
            count = create_path(board, nets["GND"], path, f"Route R2.3 ground escape {index}")
            board.save()
            print(f"GND {index}: {start} -> {goal}; {len(path)} vertices / {count} items")
            print(f"GND {index} path: {path}")
            return
        except RuntimeError as exc:
            failures.append(str(exc))
    raise RuntimeError(f"no ground escape from {start}: {failures[-1]}")


def route_ground_dogbone(board, nets, start, via_point, index, *waypoints):
    """Connect one local GND island to the In1 plane with a fixed dogbone."""
    points = (start, *waypoints, via_point)
    wanted_pairs = {
        frozenset(
            (
                (from_mm(a[0]), from_mm(a[1])),
                (from_mm(b[0]), from_mm(b[1])),
            )
        )
        for a, b in zip(points, points[1:])
    }
    stale = []
    for track in board.get_tracks():
        if track.net.name != "GND" or track.layer != F_CU:
            continue
        endpoints = frozenset(
            ((track.start.x, track.start.y), (track.end.x, track.end.y))
        )
        if endpoints in wanted_pairs:
            stale.append(track)
    stale.extend(
        via
        for via in board.get_vias()
        if via.net.name == "GND"
        and via.position.x == from_mm(via_point[0])
        and via.position.y == from_mm(via_point[1])
    )
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, f"Refresh R2.3 ground dogbone {index}")
        except Exception:
            board.drop_commit(commit)
            raise
    items = []
    for point_a, point_b in zip(points, points[1:]):
        add_track(items, nets["GND"], F_CU, point_a, point_b, 0.15)
    add_via(items, nets["GND"], via_point, 0.45, 0.20)
    create_and_renet(board, items, f"Route R2.3 ground dogbone {index}")
    print(f"GND {index}: {start} -> {via_point}; {len(items)} items")


def route_ground_bridge(board, nets, start, goal, index):
    """Join adjacent local GND islands on F.Cu without another through via."""
    path = _astar_multilayer(
        board,
        "GND",
        start,
        goal,
        layers=(F_CU,),
        width_mm=0.15,
        via_diameter_mm=0.45,
        step=0.10,
        goal_layer=F_CU,
        clearance_mm=0.15,
        start_layer=F_CU,
        board_bounds=BOARD_BOUNDS,
    )
    items = []
    for point_a, point_b in zip(path, path[1:]):
        add_track(items, nets["GND"], F_CU, point_a[:2], point_b[:2], 0.15)
    create_and_renet(board, items, f"Bridge R2.3 ground islands {index}")
    board.save()
    print(f"GND bridge {index}: {len(path)} vertices / {len(items)} items")
    print(f"GND bridge {index} path: {path}")


def route_ground_inner_bridge(board, nets, start, goal, index):
    """Join two GND vias on In1 when a local plane neck is interrupted."""
    path = _astar_multilayer(
        board,
        "GND",
        start,
        goal,
        layers=(IN1_CU, IN2_CU, B_CU),
        width_mm=0.15,
        via_diameter_mm=0.45,
        step=0.10,
        goal_layer=IN1_CU,
        clearance_mm=0.15,
        start_layer=IN1_CU,
        board_bounds=BOARD_BOUNDS,
    )
    items = []
    for point_a, point_b in zip(path, path[1:]):
        if point_a[2] != point_b[2]:
            add_via(items, nets["GND"], point_a[:2], 0.45, 0.20)
        else:
            add_track(
                items, nets["GND"], point_a[2], point_a[:2], point_b[:2], 0.15
            )
    create_and_renet(board, items, f"Bridge R2.3 inner GND islands {index}")
    board.save()
    print(f"GND inner bridge {index}: {len(path)} vertices / {len(items)} items")


def remove_ground_trial(board, start, via_point, *waypoints):
    """Remove one exact earlier dogbone before trying a clearer location."""
    points = (start, *waypoints, via_point)
    wanted_pairs = {
        frozenset(
            (
                (from_mm(point_a[0]), from_mm(point_a[1])),
                (from_mm(point_b[0]), from_mm(point_b[1])),
            )
        )
        for point_a, point_b in zip(points, points[1:])
    }
    stale = [
        track
        for track in board.get_tracks()
        if track.net.name == "GND"
        and track.layer == F_CU
        and frozenset(
            ((track.start.x, track.start.y), (track.end.x, track.end.y))
        ) in wanted_pairs
    ]
    stale.extend(
        via
        for via in board.get_vias()
        if via.net.name == "GND"
        and via.position.x == from_mm(via_point[0])
        and via.position.y == from_mm(via_point[1])
    )
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, "Remove rejected R2.3 ground dogbone")
        except Exception:
            board.drop_commit(commit)
            raise


def remove_ground_bbox(board, x_min, x_max, y_min, y_max):
    """Remove one isolated autogenerated GND path contained in a small box."""
    x0, x1 = from_mm(x_min), from_mm(x_max)
    y0, y1 = from_mm(y_min), from_mm(y_max)
    stale = []
    for track in board.get_tracks():
        if track.net.name != "GND":
            continue
        if all(
            x0 <= point.x <= x1 and y0 <= point.y <= y1
            for point in (track.start, track.end)
        ):
            stale.append(track)
    stale.extend(
        via
        for via in board.get_vias()
        if via.net.name == "GND"
        and x0 <= via.position.x <= x1
        and y0 <= via.position.y <= y1
    )
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, "Remove boxed-in autogenerated GND path")
        except Exception:
            board.drop_commit(commit)
            raise
    print(f"removed {len(stale)} GND items from retry box")


def resize_ground_vias(board, points, diameter_mm=0.40):
    """Apply the established 0.40/0.20 process to selected tight GND vias."""
    wanted = {(from_mm(x), from_mm(y)) for x, y in points}
    updates = []
    for via in board.get_vias():
        if via.net.name == "GND" and (via.position.x, via.position.y) in wanted:
            via.diameter = from_mm(diameter_mm)
            updates.append(via)
    if updates:
        commit = board.begin_commit()
        try:
            board.update_items(updates)
            board.push_commit(commit, "Resize tight R2.3 GND transition vias")
        except Exception:
            board.drop_commit(commit)
            raise
    print(f"resized {len(updates)} GND vias to {diameter_mm:.2f} mm")


def move_ground_via(board, old_point, new_point):
    """Move a GND transition and every attached GND track endpoint together."""
    old_x, old_y = from_mm(old_point[0]), from_mm(old_point[1])
    new_vector = Vector2.from_xy_mm(*new_point)
    updates = []
    for via in board.get_vias():
        if (
            via.net.name == "GND"
            and via.position.x == old_x
            and via.position.y == old_y
        ):
            via.position = new_vector
            via.diameter = from_mm(0.45)
            updates.append(via)
    for track in board.get_tracks():
        if track.net.name != "GND":
            continue
        changed = False
        if track.start.x == old_x and track.start.y == old_y:
            track.start = new_vector
            changed = True
        if track.end.x == old_x and track.end.y == old_y:
            track.end = new_vector
            changed = True
        if changed:
            updates.append(track)
    if updates:
        commit = board.begin_commit()
        try:
            board.update_items(updates)
            board.push_commit(commit, "Nudge tight R2.3 GND transition via")
        except Exception:
            board.drop_commit(commit)
            raise
    print(f"moved GND via {old_point} -> {new_point}; {len(updates)} items")


def main():
    with KiCad(
        headless=True,
        kicad_cli_path=str(KICAD_CLI),
        file_path=str(BOARD),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        nets = {net.name: net for net in board.get_nets()}
        move_ground_via(board, (128.50, 31.35), (128.50, 31.40))
        print(f"removed {deduplicate_copper(board)} duplicate items")
        board.refill_zones(block=True, max_poll_seconds=60.0)
        board.save()
        print(f"saved {board.name}")


if __name__ == "__main__":
    main()
