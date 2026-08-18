#!/usr/bin/env python3
"""Finish R2.3 routing through KiCad's official headless IPC API.

The broad signal fanout was imported from a tracked Specctra session.  This
pass removes exact duplicate session items, repairs the remaining constrained
nets, and adds the ground reference planes.  It never rewrites KiCad project
S-expressions.
"""

from __future__ import annotations

import sys
from pathlib import Path

from kipy import KiCad
from kipy.board_types import Track, Via, Zone, ZoneConnectionStyle
from kipy.common_types import PolygonWithHoles
from kipy.geometry import PolyLine, PolyLineNode, Vector2
from kipy.util import from_mm
from kipy.util.board_layer import layer_from_canonical_name


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "koyomi-lvds-hat.kicad_pcb"
KICAD_CLI = Path(
    "/Users/hyper/projects/tensorfleet/vaio_p_modding/tools/"
    "kicad11-nightly-20260722/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
)

# Reuse the collision-aware IPC router maintained beside the CM5 carrier.
# The resulting copper is persisted in this repository; this import is only
# needed if the one-time finishing pass is intentionally replayed.
ROUTER_HELPERS = Path(
    "/Users/hyper/projects/tensorfleet/vaio_cm5_carrier/scripts"
)
sys.path.insert(0, str(ROUTER_HELPERS))
from configure_a3_3_right_io import _astar_multilayer  # noqa: E402


F_CU = layer_from_canonical_name("F.Cu")
IN1_CU = layer_from_canonical_name("In1.Cu")
IN2_CU = layer_from_canonical_name("In2.Cu")
B_CU = layer_from_canonical_name("B.Cu")
BOARD_BOUNDS = (91.35, 155.65, 22.35, 49.90)
ZONE_NAME = "R2.3 GND REFERENCE"


def add_track(items, net, layer, start, end, width_mm):
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


def create_and_renet(board, items, message):
    intended = [item.net for item in items]
    commit = board.begin_commit()
    try:
        created = board.create_items(items)
        board.push_commit(commit, message)
    except Exception:
        board.drop_commit(commit)
        raise
    live = {item.id.value: item for item in [*board.get_tracks(), *board.get_vias()]}
    updates = []
    for created_item, net in zip(created, intended, strict=True):
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


def deduplicate_copper(board):
    duplicates = []
    seen_tracks = set()
    for track in board.get_tracks():
        endpoints = sorted(
            ((track.start.x, track.start.y), (track.end.x, track.end.y))
        )
        key = (
            track.net.name,
            track.layer,
            endpoints[0],
            endpoints[1],
            track.width,
        )
        if key in seen_tracks:
            duplicates.append(track)
        else:
            seen_tracks.add(key)
    seen_vias = set()
    for via in board.get_vias():
        key = (
            via.net.name,
            via.position.x,
            via.position.y,
            via.diameter,
            via.drill_diameter,
        )
        if key in seen_vias:
            duplicates.append(via)
        else:
            seen_vias.add(key)
    if duplicates:
        commit = board.begin_commit()
        try:
            board.remove_items(duplicates)
            board.push_commit(commit, "Remove duplicate Specctra session copper")
        except Exception:
            board.drop_commit(commit)
            raise
    return len(duplicates)


def remove_net_copper(board, net_names):
    targets = set(net_names)
    stale = [
        item
        for item in [*board.get_tracks(), *board.get_vias()]
        if item.net.name in targets
    ]
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, f"Replace routes: {', '.join(sorted(targets))}")
        except Exception:
            board.drop_commit(commit)
            raise


def add_path(board, nets, net_name, start, goal, *, width_mm, layers):
    path = _astar_multilayer(
        board,
        net_name,
        start,
        goal,
        layers=layers,
        width_mm=width_mm,
        via_diameter_mm=0.50,
        step=0.10,
        goal_layer=F_CU,
        clearance_mm=0.15,
        start_layer=F_CU,
        board_bounds=BOARD_BOUNDS,
    )
    items = []
    for a, b in zip(path, path[1:]):
        if a[2] != b[2]:
            add_via(items, nets[net_name], a[:2])
        else:
            add_track(items, nets[net_name], a[2], a[:2], b[:2], width_mm)
    create_and_renet(board, items, f"Finish R2.3 {net_name}")
    print(f"{net_name}: {len(path)} vertices / {len(items)} items")


def route_clock_pair(board, nets):
    remove_net_copper(board, {"RXCLK+", "RXCLK-", "RX2+", "RX2-"})
    # FL2 and J2 are close enough for direct, monotonic fanout. The four
    # straight routes stay ordered, avoid stubs/vias, and keep both LVDS pairs
    # matched to better than 0.06 mm.
    pairs = {
        "RXCLK+": [(125.0499, 43.975), (125.0499, 44.30), (126.10, 44.95), (126.10, 45.63)],
        "RXCLK-": [(125.5501, 43.975), (125.5501, 44.30), (126.50, 44.95), (126.50, 45.63)],
        "RX2+": [(126.0499, 43.975), (126.0499, 44.30), (126.90, 44.95), (126.90, 45.63)],
        "RX2-": [(126.5501, 43.975), (126.5501, 44.30), (127.30, 44.95), (127.30, 45.63)],
    }
    items = []
    for net_name, points in pairs.items():
        for start, end in zip(points, points[1:]):
            add_track(items, nets[net_name], F_CU, start, end, 0.09)
    create_and_renet(board, items, "Route matched R2.3 FL2 LVDS output pairs")


def route_d14_d15(board, nets):
    """Restore D14; leave adjacent D15 for the final global route pass."""
    remove_net_copper(board, {"D14", "D15"})
    routes = (
        (
            "D14",
            (103.10, 30.20),
            (103.621, 31.009),
            (124.40, 29.50),
            ((124.40, 29.50), (124.40, 31.40), (123.75, 32.05), (123.75, 32.70)),
            IN2_CU,
        ),
    )
    for net_name, source_pad, source_via, goal_via, goal_escape, route_layer in routes:
        path = _astar_multilayer(
            board,
            net_name,
            source_via,
            goal_via,
            layers=(route_layer,),
            width_mm=0.15,
            via_diameter_mm=0.45,
            step=0.10,
            goal_layer=route_layer,
            clearance_mm=0.15,
            start_layer=route_layer,
            board_bounds=BOARD_BOUNDS,
        )
        items = []
        add_track(items, nets[net_name], F_CU, source_pad, source_via, 0.15)
        add_via(items, nets[net_name], source_via, 0.45, 0.20)
        for a, b in zip(path, path[1:]):
            add_track(items, nets[net_name], route_layer, a[:2], b[:2], 0.15)
        add_via(items, nets[net_name], goal_via, 0.45, 0.20)
        for start, end in zip(goal_escape, goal_escape[1:]):
            add_track(items, nets[net_name], F_CU, start, end, 0.15)
        create_and_renet(board, items, f"Finish R2.3 {net_name}")
        print(f"{net_name}: {len(path)} inner-layer vertices / {len(items)} items")


def route_5v(board, nets):
    """Neck out of the FFC/backlight pads and carry +5 V on B.Cu."""
    remove_net_copper(board, {"+5V"})
    source_a = (114.25, 22.81)
    source_b = (115.25, 22.81)
    merge = (114.75, 23.35)
    load_via = (143.75, 43.70)
    path = _astar_multilayer(
        board,
        "+5V",
        merge,
        load_via,
        layers=(B_CU,),
        width_mm=0.40,
        via_diameter_mm=0.45,
        step=0.10,
        goal_layer=B_CU,
        clearance_mm=0.15,
        start_layer=B_CU,
        board_bounds=BOARD_BOUNDS,
    )
    items = []
    # Two minimum-rule vias provide parallel current paths without crossing
    # the interleaved VSYNC/HSYNC FFC pads.
    add_track(items, nets["+5V"], F_CU, (114.25, 22.71), source_a, 0.15)
    add_track(items, nets["+5V"], F_CU, (115.25, 22.71), source_b, 0.15)
    add_via(items, nets["+5V"], source_a, 0.45, 0.20)
    add_via(items, nets["+5V"], source_b, 0.45, 0.20)
    add_track(items, nets["+5V"], B_CU, source_a, merge, 0.15)
    add_track(items, nets["+5V"], B_CU, source_b, merge, 0.15)
    for a, b in zip(path, path[1:]):
        add_track(items, nets["+5V"], B_CU, a[:2], b[:2], 0.40)
    add_via(items, nets["+5V"], load_via, 0.45, 0.20)
    add_track(items, nets["+5V"], F_CU, load_via, (143.75, 42.15), 0.15)
    create_and_renet(board, items, "Route R2.3 +5V distribution")
    print(f"+5V: {len(path)} inner-layer vertices / {len(items)} items")


def route_ic_3v3(board, nets):
    """Replace the repeated autorouter detour with a short B.Cu IC feed."""
    stale = []
    for item in [*board.get_tracks(), *board.get_vias()]:
        if item.net.name != "+3V3":
            continue
        if isinstance(item, Track):
            points = (item.start, item.end)
        else:
            points = (item.position,)
        explicit_old = {
            frozenset(((113.338, 33.000), (113.800, 31.800))),
            frozenset(((113.800, 31.800), (117.750, 31.800))),
            frozenset(((117.750, 31.800), (117.750, 32.700))),
            frozenset(((117.750, 31.450), (117.750, 32.700))),
            frozenset(((117.250, 32.650), (117.250, 32.850))),
        }
        endpoints = frozenset(
            (
                round(point.x / 1e6, 3),
                round(point.y / 1e6, 3),
            )
            for point in points
        )
        old_via = (
            not isinstance(item, Track)
            and round(item.position.x / 1e6, 3) == 117.750
            and round(item.position.y / 1e6, 3) == 31.450
        )
        local_fine_route = all(
            112.00 <= point.x / 1e6 <= 118.00
            and 31.00 <= point.y / 1e6 <= 35.80
            for point in points
        ) and (
            not isinstance(item, Track) or item.width <= from_mm(0.20)
        )
        if old_via or endpoints in explicit_old or local_fine_route:
            stale.append(item)
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, "Replace R2.3 IC +3V3 detour")
        except Exception:
            board.drop_commit(commit)
            raise
    source_via = (112.60, 35.50)
    goal_via = (117.75, 32.00)
    path = _astar_multilayer(
        board,
        "+3V3",
        source_via,
        goal_via,
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
    add_track(items, nets["+3V3"], F_CU, (113.338, 33.00), source_via, 0.15)
    add_via(items, nets["+3V3"], source_via, 0.45, 0.20)
    for start, end in zip(path, path[1:]):
        add_track(items, nets["+3V3"], B_CU, start[:2], end[:2], 0.15)
    add_via(items, nets["+3V3"], goal_via, 0.45, 0.20)
    add_track(items, nets["+3V3"], F_CU, goal_via, (117.75, 32.70), 0.15)
    create_and_renet(board, items, "Route short R2.3 IC +3V3 feed")


def reroute_ffc_3v3(board, nets):
    """Move the FFC +3V3 branch around the two +5 V escape vias."""
    old_segments = {
        frozenset(((114.170, 26.789), (114.170, 23.747))),
        frozenset(((114.170, 23.747), (115.149, 22.768))),
        frozenset(((114.170, 23.747), (113.133, 22.710))),
        frozenset(((115.149, 22.768), (121.037, 22.768))),
    }
    stale = []
    for track in board.get_tracks():
        if track.net.name != "+3V3" or track.layer != IN1_CU:
            continue
        endpoints = frozenset(
            (
                round(point.x / 1e6, 3),
                round(point.y / 1e6, 3),
            )
            for point in (track.start, track.end)
        )
        if endpoints in old_segments:
            stale.append(track)
    old_escape_points = {(113.133, 22.710), (112.900, 23.000)}
    for via in board.get_vias():
        point = (
            round(via.position.x / 1e6, 3),
            round(via.position.y / 1e6, 3),
        )
        if via.net.name == "+3V3" and point in old_escape_points:
            stale.append(via)
    for track in board.get_tracks():
        if track.net.name != "+3V3" or track.layer != F_CU:
            continue
        points = {
            (
                round(point.x / 1e6, 3),
                round(point.y / 1e6, 3),
            )
            for point in (track.start, track.end)
        }
        if points & old_escape_points:
            stale.append(track)
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, "Clear R2.3 FFC +3V3 escape")
        except Exception:
            board.drop_commit(commit)
            raise

    escape_items = []
    add_track(escape_items, nets["+3V3"], F_CU, (113.75, 22.71), (113.40, 23.00), 0.15)
    add_track(escape_items, nets["+3V3"], F_CU, (113.40, 23.00), (112.90, 23.00), 0.15)
    add_via(escape_items, nets["+3V3"], (112.90, 23.00), 0.45, 0.20)
    create_and_renet(board, escape_items, "Move R2.3 FFC +3V3 escape")

    waypoints = ((112.900, 23.000), (114.170, 26.789), (121.037, 22.768))
    for start, goal in zip(waypoints, waypoints[1:]):
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
        for a, b in zip(path, path[1:]):
            add_track(items, nets["+3V3"], IN1_CU, a[:2], b[:2], 0.30)
        create_and_renet(board, items, "Reroute R2.3 FFC +3V3 branch")


def reroute_vsync_escape(board, nets):
    """Move VSYNC off F.Cu so it does not cross the FFC power escapes."""
    stale = []
    target = frozenset(((105.975, 23.364), (114.648, 23.364)))
    for track in board.get_tracks():
        if track.net.name != "VSYNC" or track.layer != F_CU:
            continue
        endpoints = frozenset((
            (round(track.start.x / 1e6, 3), round(track.start.y / 1e6, 3)),
            (round(track.end.x / 1e6, 3), round(track.end.y / 1e6, 3)),
        ))
        if endpoints == target:
            stale.append(track)
    new_via_point = (114.75, 23.80)
    for via in board.get_vias():
        if via.net.name == "VSYNC" and (
            round(via.position.x / 1e6, 3),
            round(via.position.y / 1e6, 3),
        ) == new_via_point:
            stale.append(via)
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, "Clear R2.3 VSYNC FFC crossing")
        except Exception:
            board.drop_commit(commit)
            raise
    path = _astar_multilayer(
        board,
        "VSYNC",
        new_via_point,
        (105.975, 23.3639),
        layers=(IN2_CU,),
        width_mm=0.15,
        via_diameter_mm=0.50,
        step=0.10,
        goal_layer=IN2_CU,
        clearance_mm=0.15,
        start_layer=IN2_CU,
        board_bounds=BOARD_BOUNDS,
    )
    items = []
    add_track(items, nets["VSYNC"], F_CU, (114.648, 23.3639), new_via_point, 0.15)
    add_via(items, nets["VSYNC"], new_via_point, 0.50, 0.25)
    for a, b in zip(path, path[1:]):
        add_track(items, nets["VSYNC"], IN2_CU, a[:2], b[:2], 0.15)
    create_and_renet(board, items, "Reroute R2.3 VSYNC escape")


def cleanup_known_router_artifacts(board, nets):
    stale = []
    for via in board.get_vias():
        point = (
            round(via.position.x / 1e6, 3),
            round(via.position.y / 1e6, 3),
        )
        if (via.net.name, point) in {
            ("D9", (127.000, 31.700)),
            ("D21", (119.000, 31.700)),
        }:
            stale.append(via)
    for track in board.get_tracks():
        if track.net.name != "+3V3" or track.layer != B_CU:
            continue
        endpoints = {
            (round(track.start.x / 1e6, 3), round(track.start.y / 1e6, 3)),
            (round(track.end.x / 1e6, 3), round(track.end.y / 1e6, 3)),
        }
        if (116.600, 35.500) in endpoints:
            stale.append(track)
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, "Remove dangling router vias")
        except Exception:
            board.drop_commit(commit)
            raise

    # Restore the short FFC pad escape that the broad router stopped 1.07 mm
    # below pad 27.
    existing = False
    for track in board.get_tracks():
        if track.net.name != "CLKIN" or track.layer != F_CU:
            continue
        endpoints = {
            (round(track.start.x / 1e6, 4), round(track.start.y / 1e6, 4)),
            (round(track.end.x / 1e6, 4), round(track.end.y / 1e6, 4)),
        }
        if endpoints == {(126.7500, 22.7100), (126.7500, 23.7779)}:
            existing = True
            break
    if not existing:
        items = []
        add_track(
            items, nets["CLKIN"], F_CU,
            (126.7500, 22.7100), (126.7500, 23.7779), 0.15,
        )
        create_and_renet(board, items, "Join R2.3 CLKIN FFC escape")


def route_ground_returns(board, nets):
    """Remove the unsafe trial ground drops before the dedicated route pass."""
    drops = (
        # IC1 top edge: vias sit under the package body.
        ((120.25, 32.70), (120.25, 34.20)),
        ((121.75, 32.70), (121.75, 34.20)),
        ((122.75, 32.70), (122.75, 34.20)),
        ((124.25, 32.70), (124.25, 34.20)),
        ((126.75, 33.3401), (126.75, 34.20)),
        ((128.25, 32.70), (128.25, 34.20)),
        ((129.75, 32.70), (129.75, 34.20)),
        # IC1 bottom edge.
        ((118.75, 39.960), (118.75, 38.60)),
        ((120.25, 39.960), (120.25, 38.60)),
        ((127.25, 39.960), (127.25, 38.60)),
        ((128.75, 39.960), (128.75, 38.60)),
        # Backlight harness return.
        ((143.25, 42.15), (143.25, 44.50)),
    )
    via_points = {
        (round(end[0], 3), round(end[1], 3)) for _, end in drops
    }
    drop_segments = {
        frozenset((
            (round(start[0], 3), round(start[1], 3)),
            (round(end[0], 3), round(end[1], 3)),
        ))
        for start, end in drops
    }
    stale = []
    for via in board.get_vias():
        if via.net.name != "GND":
            continue
        point = (
            round(via.position.x / 1e6, 3),
            round(via.position.y / 1e6, 3),
        )
        if point in via_points:
            stale.append(via)
    for track in board.get_tracks():
        if track.net.name != "GND" or track.layer != F_CU:
            continue
        endpoints = frozenset((
            (round(track.start.x / 1e6, 3), round(track.start.y / 1e6, 3)),
            (round(track.end.x / 1e6, 3), round(track.end.y / 1e6, 3)),
        ))
        if endpoints in drop_segments:
            stale.append(track)
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, "Remove unsafe trial ground drops")
        except Exception:
            board.drop_commit(commit)
            raise


def add_ground_zone(board, net):
    existing = [
        zone for zone in board.get_zones()
        if zone.name == ZONE_NAME or zone.name.startswith(f"{ZONE_NAME} ")
    ]
    if existing:
        commit = board.begin_commit()
        try:
            board.remove_items(existing)
            board.push_commit(commit, "Replace R2.3 ground reference zone")
        except Exception:
            board.drop_commit(commit)
            raise
    outline = PolyLine()
    for x, y in (
        (91.40, 22.40),
        (155.60, 22.40),
        (155.60, 49.85),
        (91.40, 49.85),
        (91.40, 22.40),
    ):
        outline.append(PolyLineNode.from_xy(from_mm(x), from_mm(y)))
    polygon = PolygonWithHoles()
    polygon.outline = outline
    zones = []
    for layer, suffix in ((IN1_CU, "IN1"),):
        zone = Zone()
        zone.name = f"{ZONE_NAME} {suffix}"
        zone.layers = [layer]
        zone.outline = polygon
        zone.net = net
        assert zone.connection is not None
        zone.connection.zone_connection = ZoneConnectionStyle.ZCS_FULL
        zones.append(zone)
    commit = board.begin_commit()
    try:
        board.create_items(zones)
        board.push_commit(commit, "Add R2.3 ground reference planes")
    except Exception:
        board.drop_commit(commit)
        raise


def add_ground_stitching(board, net):
    points = (
        (96.0, 24.0), (105.0, 24.0), (112.0, 24.0), (122.0, 24.0),
        (134.0, 24.0), (144.0, 24.0), (153.0, 24.0),
        (96.0, 48.0), (106.0, 48.0), (116.0, 48.0), (126.0, 48.0),
        (136.0, 48.0), (146.0, 48.0), (153.0, 48.0),
        (119.0, 31.7), (127.0, 31.7), (119.0, 40.8), (127.0, 40.8),
        (124.0, 44.2), (131.0, 44.2),
    )
    point_set = {(round(x, 3), round(y, 3)) for x, y in points}
    # The first audit proved a regular grid is unsafe on this already-routed
    # compact board. Remove those trial sites; purpose-placed return vias are
    # added only after the final DRC/transition audit.
    stale = [
        via for via in board.get_vias()
        if via.net.name == "GND"
        and (
            round(via.position.x / 1e6, 3),
            round(via.position.y / 1e6, 3),
        ) in point_set
    ]
    if stale:
        commit = board.begin_commit()
        try:
            board.remove_items(stale)
            board.push_commit(commit, "Remove unsafe trial return-via grid")
        except Exception:
            board.drop_commit(commit)
            raise


def update_silkscreen(board):
    updates = []
    for item in board.get_text():
        if item.value == "R2.2":
            item.value = "R2.3 ROUTED"
        if item.value in {"R2.3 ROUTED", "JBL1 BACKLIGHT"}:
            item.attributes.size = Vector2.from_xy_mm(1.0, 1.0)
            item.attributes.stroke_width = from_mm(0.15)
            updates.append(item)
    if updates:
        commit = board.begin_commit()
        try:
            board.update_items(updates)
            board.push_commit(commit, "Update R2.3 routed silkscreen")
        except Exception:
            board.drop_commit(commit)
            raise


def main():
    with KiCad(
        headless=True,
        kicad_cli_path=str(KICAD_CLI),
        file_path=str(BOARD),
        timeout_ms=60_000,
    ) as kicad:
        board = kicad.get_board()
        nets = {net.name: net for net in board.get_nets()}
        print(f"removed {deduplicate_copper(board)} exact duplicate items")

        route_clock_pair(board, nets)
        route_d14_d15(board, nets)
        # These nets need the remaining global channels. Leave them open for
        # the dedicated final Specctra pass together with GND.
        remove_net_copper(board, {"D15", "D18", "VSYNC"})

        # Join the split +3V3 layer transition and the isolated IC1 supply pad.
        has_transition_via = any(
            via.net.name == "+3V3"
            and round(via.position.x / 1e6, 3) == 114.163
            and round(via.position.y / 1e6, 3) == 40.161
            for via in board.get_vias()
        )
        if not has_transition_via:
            via_items = []
            add_via(via_items, nets["+3V3"], (114.163, 40.1612))
            create_and_renet(board, via_items, "Join R2.3 +3V3 layer transition")
        route_ic_3v3(board, nets)

        route_5v(board, nets)
        reroute_ffc_3v3(board, nets)

        cleanup_known_router_artifacts(board, nets)
        route_ground_returns(board, nets)
        add_ground_zone(board, nets["GND"])
        add_ground_stitching(board, nets["GND"])
        update_silkscreen(board)
        print(f"removed {deduplicate_copper(board)} late duplicate items")
        board.save()
        print(f"saved {board.name}")


if __name__ == "__main__":
    main()
