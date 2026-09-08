"""Obstacle-aware native route search, adapted from TensorFleet carrier router.

Geometry is read through KiCad IPC. Caller creates the candidate through IPC
and must run native DRC; a found search path alone is not verification.
"""
import heapq
import math
F_CU, IN1_CU, IN2_CU, IN3_CU, IN4_CU, B_CU = 3, 4, 5, 6, 7, 34
def _distance_to_segment(px, py, ax, ay, bx, by) -> float:
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def _layer_obstacles(board, layer: int, routed_net: str, width_mm: float,
                     clearance=0.13, include_same_net_drills=False,
                     mate_net=None, mate_clearance=None):
    radius = width_mm / 2
    segments = []
    circles = []
    rectangles = []
    for track in board.get_tracks():
        if track.layer != layer or track.net.name == routed_net:
            continue
        item_clearance = (
            mate_clearance
            if mate_net and track.net.name == mate_net and mate_clearance is not None
            else clearance
        )
        segments.append((
            track.start.x / 1e6, track.start.y / 1e6,
            track.end.x / 1e6, track.end.y / 1e6,
            track.width / 2e6 + radius + item_clearance,
        ))
    copper_stack = (F_CU, IN1_CU, IN2_CU, IN3_CU, IN4_CU, B_CU)
    for via in board.get_vias():
        if via.net.name == routed_net:
            continue
        # A blind/microvia is only an obstacle on the copper layers it spans.
        # Treating every via as through-hole creates false collisions against
        # routes on layers where no via copper exists.
        start_layer = int(via.padstack.drill.start_layer)
        end_layer = int(via.padstack.drill.end_layer)
        try:
            start_index = copper_stack.index(start_layer)
            end_index = copper_stack.index(end_layer)
            low, high = sorted((start_index, end_index))
            if not low <= copper_stack.index(layer) <= high:
                continue
        except ValueError:
            # Preserve the conservative behavior for an unknown stack entry.
            pass
        item_clearance = (
            mate_clearance
            if mate_net and via.net.name == mate_net and mate_clearance is not None
            else clearance
        )
        circles.append((
            via.position.x / 1e6, via.position.y / 1e6,
            max(
                via.diameter / 2e6 + radius + item_clearance,
                via.drill_diameter / 2e6 + radius + 0.20,
            ),
        ))
    for footprint in board.get_footprints():
        for pad in footprint.definition.pads:
            if layer not in pad.padstack.layers:
                continue
            same_net = pad.net.name == routed_net
            item_clearance = (
                mate_clearance
                if mate_net and pad.net.name == mate_net and mate_clearance is not None
                else clearance
            )
            # NPTH alignment holes have no copper shape, but they are still
            # hard routing obstacles on every copper layer.  The earlier
            # router skipped them entirely and could generate traces inside
            # J701's locating holes after the socket moved.
            drill = pad.proto.pad_stack.drill
            drill_x = drill.diameter.x_nm / 1e6
            drill_y = drill.diameter.y_nm / 1e6
            if same_net:
                if include_same_net_drills and drill_x > 0 and drill_y > 0:
                    circles.append((
                        pad.position.x / 1e6,
                        pad.position.y / 1e6,
                        max(drill_x, drill_y) / 2 + radius
                        + max(clearance, 0.25),
                    ))
                continue
            if drill_x > 0 and drill_y > 0:
                circles.append((
                    pad.position.x / 1e6,
                    pad.position.y / 1e6,
                    max(drill_x, drill_y) / 2 + radius
                    + max(item_clearance, 0.20),
                ))
            if not pad.padstack.copper_layers and drill_x > 0 and drill_y > 0:
                continue
            if not pad.padstack.copper_layers:
                continue
            # Use the largest copper-layer shape and include both padstack and
            # footprint rotation.  The earlier proxy omitted the footprint
            # angle, so a 90-degree connector could expose copper outside the
            # obstacle rectangle.  A diagonal bounding circle was safe but too
            # pessimistic for fine-pitch escape routing.
            shapes = list(pad.padstack.copper_layers)
            width = max(shape.size.x for shape in shapes) / 1e6
            height = max(shape.size.y for shape in shapes) / 1e6
            if footprint.reference_field.text.value in {"JP4", "JP5"}:
                width, height = 1.0, 1.5  # full custom copper, not anchor rectangle
            # KiCad IPC reports padstack.angle in board coordinates, already
            # including the footprint rotation.  Adding footprint.orientation
            # a second time rotates connector pads twice.
            angle = pad.padstack.angle.degrees % 180
            if 45 < angle < 135:
                width, height = height, width
            margin = radius + item_clearance
            if all(shape.shape == 1 for shape in shapes) and abs(width - height) < 1e-6:
                circles.append((
                    pad.position.x / 1e6,
                    pad.position.y / 1e6,
                    width / 2 + margin,
                ))
            else:
                rectangles.append((
                    pad.position.x / 1e6 - width / 2 - margin,
                    pad.position.y / 1e6 - height / 2 - margin,
                    pad.position.x / 1e6 + width / 2 + margin,
                    pad.position.y / 1e6 + height / 2 + margin,
                ))
    return segments, circles, rectangles

def _astar_multilayer(board, net_name: str, start, goal,
                      layers=(B_CU, IN4_CU), width_mm=0.09,
                      via_diameter_mm=0.25, step=0.10,
                      goal_layer=None, clearance_mm=0.13,
                      start_layer=None,
                      board_bounds=(74.15, 164.80, 34.30, 85.70),
                      max_states=400_000,
                      surface_step_cost=1.0,
                      via_clearance_mm=None,
                      mate_net=None,
                      mate_clearance_mm=None,
                      span_aware_vias=False,
                      via_endpoint_keepout_mm=0.75):
    board_xmin, board_xmax, board_ymin, board_ymax = board_bounds
    # Dense carrier revisions can contain a complete copper barrier within the
    # old 6 x 8 mm search halo.  Keep the search bounded to the board, but give
    # long buses enough room to go around an occupied component/fanout band.
    xmin = max(board_xmin, min(start[0], goal[0]) - 12.0)
    xmax = min(board_xmax, max(start[0], goal[0]) + 12.0)
    ymin = max(board_ymin, min(start[1], goal[1]) - 12.0)
    ymax = min(board_ymax, max(start[1], goal[1]) + 12.0)
    layer_obstacles = {
        layer: _layer_obstacles(
            board, layer, net_name, width_mm, clearance_mm,
            mate_net=mate_net, mate_clearance=mate_clearance_mm,
        )
        for layer in layers
    }
    if via_clearance_mm is None:
        via_clearance_mm = max(clearance_mm, 0.20)
    via_obstacles = {
        # Model the actual requested via diameter.  The exact hole clearance
        # remains enforced by the KiCad DRC gate after routing.
        layer: _layer_obstacles(
            board, layer, net_name, via_diameter_mm,
            via_clearance_mm, include_same_net_drills=True,
            mate_net=mate_net, mate_clearance=mate_clearance_mm,
        )
        for layer in (F_CU, IN1_CU, IN2_CU, IN3_CU, IN4_CU, B_CU)
    }

    def make_index(obstacles):
        index = {}

        def add_to_cells(entry, x0, y0, x1, y1):
            for cell_x in range(math.floor(x0), math.floor(x1) + 1):
                for cell_y in range(math.floor(y0), math.floor(y1) + 1):
                    index.setdefault((cell_x, cell_y), []).append(entry)

        segments, circles, rectangles = obstacles
        for ax, ay, bx, by, limit in segments:
            entry = (0, (ax, ay, bx, by, limit))
            add_to_cells(entry, min(ax, bx) - limit, min(ay, by) - limit,
                         max(ax, bx) + limit, max(ay, by) + limit)
        for cx, cy, limit in circles:
            entry = (1, (cx, cy, limit))
            add_to_cells(entry, cx - limit, cy - limit, cx + limit, cy + limit)
        for rectangle in rectangles:
            entry = (2, rectangle)
            add_to_cells(entry, *rectangle)
        return index

    layer_indices = {layer: make_index(obstacles)
                     for layer, obstacles in layer_obstacles.items()}
    via_indices = {layer: make_index(obstacles)
                   for layer, obstacles in via_obstacles.items()}
    existing_via_holes = [
        (
            via.position.x / 1e6,
            via.position.y / 1e6,
            via.diameter / 2e6 + via_diameter_mm / 2
            + max(via_clearance_mm, 0.25),
        )
        for via in board.get_vias()
    ]

    def xy(node):
        return xmin + node[0] * step, ymin + node[1] * step

    def node(point):
        return round((point[0] - xmin) / step), round((point[1] - ymin) / step)

    blocked_cache = {}

    def blocked(point, index) -> bool:
        x, y = point
        if not (xmin <= x <= xmax and ymin <= y <= ymax):
            return True
        cache_key = (id(index), round(x, 3), round(y, 3))
        if cache_key in blocked_cache:
            return blocked_cache[cache_key]
        result = False
        for kind, data in index.get((math.floor(x), math.floor(y)), ()):
            if kind == 0:
                ax, ay, bx, by, limit = data
                result = _distance_to_segment(x, y, ax, ay, bx, by) < limit
            elif kind == 1:
                cx, cy, limit = data
                result = math.hypot(x - cx, y - cy) < limit
            else:
                x0, y0, x1, y1 = data
                result = x0 < x < x1 and y0 < y < y1
            if result:
                break
        blocked_cache[cache_key] = result
        return result

    copper_stack = (F_CU, IN1_CU, IN2_CU, IN3_CU, IN4_CU, B_CU)

    def via_blocked(point, start_via_layer=None, end_via_layer=None) -> bool:
        if span_aware_vias and start_via_layer is not None and end_via_layer is not None:
            start_index = copper_stack.index(start_via_layer)
            end_index = copper_stack.index(end_via_layer)
            low, high = sorted((start_index, end_index))
            checked_layers = copper_stack[low:high + 1]
        else:
            checked_layers = copper_stack
        if any(blocked(point, via_indices[layer]) for layer in checked_layers):
            return True
        x, y = point
        return any(
            math.hypot(x - cx, y - cy) < limit
            for cx, cy, limit in existing_via_holes
        )

    nx = round((xmax - xmin) / step)
    ny = round((ymax - ymin) / step)
    start_grid = node(start)
    goal_grid = node(goal)
    if start_layer is None:
        start_layer = layers[0]
    if start_layer not in layers:
        raise ValueError(f"start layer {start_layer} not in routing layers {layers}")
    start_state = (*start_grid, layers.index(start_layer))
    moves = ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
             (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)),
             (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2)))
    queue = [(0.0, 0.0, start_state)]
    parent = {start_state: None}
    cost = {start_state: 0.0}
    goal_state = None
    while queue:
        if len(parent) > max_states:
            raise RuntimeError(
                f"search cap reached for {net_name}: {len(parent)} states"
            )
        _, current_cost, current = heapq.heappop(queue)
        if current_cost != cost.get(current):
            continue
        ix, iy, layer_index = current
        if (ix, iy) == goal_grid and (
            goal_layer is None or layers[layer_index] == goal_layer
        ):
            goal_state = current
            break
        cx, cy = xy((ix, iy))
        obstacles = layer_indices[layers[layer_index]]
        for dx, dy, move_cost in moves:
            nix, niy = ix + dx, iy + dy
            if not (0 <= nix <= nx and 0 <= niy <= ny):
                continue
            point = xy((nix, niy))
            midpoint = ((cx + point[0]) / 2, (cy + point[1]) / 2)
            # The goal point itself is allowed because its same-net pad is not
            # an obstacle, but the final segment midpoint must still clear all
            # foreign copper.  The former combined condition skipped both
            # tests for the goal step and could cross an adjacent pad.
            if blocked(midpoint, obstacles) or (
                (nix, niy) != goal_grid and blocked(point, obstacles)
            ):
                continue
            nxt = (nix, niy, layer_index)
            layer = layers[layer_index]
            layer_cost = surface_step_cost if layer in (F_CU, B_CU) else 1.0
            new_cost = current_cost + move_cost * layer_cost
            if new_cost < cost.get(nxt, math.inf):
                cost[nxt] = new_cost
                parent[nxt] = current
                heuristic = math.hypot(nix - goal_grid[0], niy - goal_grid[1])
                heapq.heappush(queue, (new_cost + heuristic, new_cost, nxt))
        # Keep through-vias away from both endpoint pad drills.  This matters
        # for the optional PTH GPIO/UART landings and avoids hole-to-hole DRC
        # misses that a copper-only endpoint check cannot catch.
        if (
            math.hypot(cx - start[0], cy - start[1]) > via_endpoint_keepout_mm
            and math.hypot(cx - goal[0], cy - goal[1]) > via_endpoint_keepout_mm
        ):
            for next_layer in range(len(layers)):
                if next_layer == layer_index:
                    continue
                if via_blocked(
                    (cx, cy), layers[layer_index], layers[next_layer]
                ):
                    continue
                nxt = (ix, iy, next_layer)
                new_cost = current_cost + 8.0
                if new_cost < cost.get(nxt, math.inf):
                    cost[nxt] = new_cost
                    parent[nxt] = current
                    heuristic = math.hypot(ix - goal_grid[0], iy - goal_grid[1])
                    heapq.heappush(queue, (new_cost + heuristic, new_cost, nxt))
    if goal_state is None:
        reached_points = [xy((state[0], state[1])) for state in parent]
        via_sites = [
            point for point in reached_points
            if any(
                not via_blocked(point, first, second)
                for first in layers for second in layers if first != second
            )
        ]
        bounds = (
            min(p[0] for p in reached_points), max(p[0] for p in reached_points),
            min(p[1] for p in reached_points), max(p[1] for p in reached_points),
        )
        raise RuntimeError(
            f"no multilayer path for {net_name}; reached={len(parent)}; "
            f"bounds={bounds}; via_sites={via_sites[:8]}"
        )

    states = []
    current = goal_state
    while current is not None:
        states.append(current)
        current = parent[current]
    states.reverse()
    points = [(start[0], start[1], start_layer)]
    for state in states[1:-1]:
        px, py = xy(state[:2])
        points.append((px, py, layers[state[2]]))
    points.append((goal[0], goal[1], layers[goal_state[2]]))

    simplified = [points[0]]
    previous_direction = None
    for index in range(1, len(points)):
        a, b = points[index - 1], points[index]
        if a[2] != b[2]:
            if simplified[-1] != a:
                simplified.append(a)
            simplified.append(b)
            previous_direction = None
            continue
        dx, dy = round(b[0] - a[0], 4), round(b[1] - a[1], 4)
        direction = (0 if abs(dx) < 1e-6 else (1 if dx > 0 else -1),
                     0 if abs(dy) < 1e-6 else (1 if dy > 0 else -1), a[2])
        if previous_direction is not None and direction != previous_direction:
            simplified.append(a)
        previous_direction = direction
    if simplified[-1] != points[-1]:
        simplified.append(points[-1])
    return simplified
