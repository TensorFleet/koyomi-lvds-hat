#!/usr/bin/env python3
"""Route a board: DSN export -> freerouting -> SES import -> save.

Two DSN edits happen before routing:
  * boundary inset 0.5 mm so copper respects the board-edge clearance rule;
  * power nets split into their own Specctra class with a 0.60 mm width rule.

The second addresses review finding P0-1: KiCad's Specctra export drops every
net into `kicad_default`, so project netclasses never reach the router and
power distribution came out at signal width. Widening afterwards just collides
with neighbouring copper, so the width has to be set up front.

DSN resolution is `um 10` with 1 unit == 1 um, so 600 == 0.60 mm.

Usage: route_board.py <pcb> <workdir>
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pcbnew

JAR = os.environ.get(
    "FREEROUTING_JAR",
    "/private/tmp/claude-501/-Users-hyper-projects-tensorfleet-vaio-p-modding/"
    "8ec5c2b1-bd4c-4d05-97f9-92a0ac5f71cb/scratchpad/freerouting-2.2.4.jar",
)
JAVA = "/opt/homebrew/opt/openjdk@25/bin/java"

POWER_NET = re.compile(r'^"?(VBUS[A-Z0-9_]*|\+3V3|SD_VDD|AU_VBUS|AU_VDD|HDMI_5V)"?$')
POWER_WIDTH_UM = 600
POWER_CLEARANCE_UM = 200


def inset_boundary(dsn: str, margin_um: int = 500) -> str:
    m = re.search(r"\(boundary\s*\(path pcb 0((?:\s+-?\d+)+)\s*\)", dsn)
    if not m:
        return dsn
    nums = [int(v) for v in m.group(1).split()]
    xs, ys = nums[0::2], nums[1::2]
    x0, x1 = min(xs) + margin_um, max(xs) - margin_um
    y0, y1 = min(ys) + margin_um, max(ys) - margin_um
    pts = f"{x1} {y0}  {x0} {y0}  {x0} {y1}  {x1} {y1}\n            {x1} {y0}"
    return dsn[:m.start()] + f"(boundary\n      (path pcb 0  {pts})" + dsn[m.end():]


def _balanced(text: str, start: int) -> int:
    """Index just past the ')' that closes the '(' at `start`."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError("unbalanced DSN")


def split_power_class(dsn: str) -> tuple[str, int]:
    """Move power nets out of kicad_default into their own wide class.

    The class body is `NET NET ... (circuit ...) (rule ...)`; both sub-blocks
    must be preserved verbatim in the remaining class and mirrored (with a
    wider width) into the new one. A naive regex flattens them and produces
    malformed DSN that the router silently ignores.
    """
    key = "(class kicad_default"
    i = dsn.find(key)
    if i < 0:
        return dsn, 0
    j = _balanced(dsn, i)
    block = dsn[i:j]
    body = block[len(key):-1]
    # first '(' that is NOT inside a quoted net name (names look like
    # "unconnected-(U1-DM3-Pad6)" and would otherwise fool the split)
    sub_at, in_q = -1, False
    for k, ch in enumerate(body):
        if ch == '"':
            in_q = not in_q
        elif ch == "(" and not in_q:
            sub_at = k
            break
    names_part = body[:sub_at] if sub_at >= 0 else body
    subs = body[sub_at:] if sub_at >= 0 else ""
    names = re.findall(r'"[^"]+"|[^\s()]+', names_part)
    power = [n for n in names if POWER_NET.match(n)]
    if not power:
        return dsn, 0
    keep = [n for n in names if n not in power]

    # mirror the sub-blocks, overriding width/clearance in the power copy
    psubs = re.sub(r"\(width\s+\d+\)", f"(width {POWER_WIDTH_UM})", subs)
    psubs = re.sub(r"\(clearance\s+\d+\)", f"(clearance {POWER_CLEARANCE_UM})", psubs)

    ind = "    "
    rebuilt = (f"{key} {' '.join(keep)}\n{ind}{subs.strip()}\n{ind})"
               f"\n{ind}(class power {' '.join(power)}\n{ind}{psubs.strip()}\n{ind})")
    return dsn[:i] + rebuilt + dsn[j:], len(power)


def drop_nets_from_network(dsn: str, nets: set[str]) -> tuple[str, int]:
    """Remove already-routed nets from (network ...) so the router skips them.

    Their wires stay in (wiring ...) as obstacles. Leaving the nets listed made
    freerouting try to re-route around its own fixed wires, which collapsed the
    score from ~987 to ~684 with most nets unrouted.
    """
    n = 0
    for net in nets:
        m = re.search(r"\n(\s*)\(net " + re.escape(net) + r"\b", dsn)
        if not m:
            continue
        start = m.start() + 1
        depth, i = 0, dsn.index("(", start)
        while i < len(dsn):
            if dsn[i] == "(":
                depth += 1
            elif dsn[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        dsn = dsn[:start] + dsn[i + 1:]
        n += 1
    return dsn, n


def main() -> int:
    pcb, work = sys.argv[1], Path(sys.argv[2])
    work.mkdir(parents=True, exist_ok=True)
    dsn_path, ses_path = work / "board.dsn", work / "board.ses"

    board = pcbnew.LoadBoard(pcb)
    if not pcbnew.ExportSpecctraDSN(board, str(dsn_path)):
        raise SystemExit("DSN export failed")

    dsn = dsn_path.read_text()
    dsn = inset_boundary(dsn)
    dsn, n_power = split_power_class(dsn)
    keep = {x for x in os.environ.get("ROUTE_KEEP_NETS", "").split(",") if x}
    if keep:
        dsn, n_dropped = drop_nets_from_network(dsn, keep)
        print(f"DSN: {n_dropped} pre-routed nets excluded from routing")
    # In1 stays a solid GND plane; the router may still use In2.
    dsn = dsn.replace("(layer In1.Cu\n      (type signal)",
                      "(layer In1.Cu\n      (type power)")
    dsn_path.write_text(dsn)
    print(f"DSN: boundary inset 0.5 mm; {n_power} power nets at "
          f"{POWER_WIDTH_UM/1000:.2f} mm; In1 reserved as plane")

    max_passes = os.environ.get("ROUTE_PASSES", "20")
    proc = subprocess.run([JAVA, "-jar", JAR, "-de", str(dsn_path),
                           "-do", str(ses_path), "-mp", max_passes, "-da"],
                          capture_output=True, text=True, timeout=900)
    done = [ln for ln in proc.stdout.splitlines() if "session completed" in ln]
    print(done[-1][-90:] if done else proc.stdout[-200:])
    if not ses_path.exists():
        raise SystemExit("freerouting produced no SES")

    # The SES import REPLACES all routing, so anything pre-routed (the matched
    # USB pairs) would be silently lost. Snapshot those nets first and put them
    # back afterwards; freerouting saw them as fixed obstacles in the DSN, so
    # its own routes were planned around them.
    keep_nets = {n for n in (os.environ.get("ROUTE_KEEP_NETS", "").split(","))
                 if n}
    saved = []
    if keep_nets:
        pre = pcbnew.LoadBoard(pcb)
        for t in pre.GetTracks():
            if t.GetNetname() not in keep_nets:
                continue
            if isinstance(t, pcbnew.PCB_VIA):
                saved.append(("via", t.GetPosition(), t.GetWidth(),
                              t.GetDrill(), t.GetNetname()))
            else:
                saved.append(("trk", t.GetStart(), t.GetEnd(), t.GetWidth(),
                              t.GetLayer(), t.GetNetname()))

    board = pcbnew.LoadBoard(pcb)
    if not pcbnew.ImportSpecctraSES(board, str(ses_path)):
        raise SystemExit("SES import failed")

    if saved:
        for t in list(board.GetTracks()):
            if t.GetNetname() in keep_nets:
                board.Remove(t)
        for item in saved:
            if item[0] == "via":
                _, pos, w, d, net = item
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pos); v.SetWidth(w); v.SetDrill(d)
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNet(board.FindNet(net)); v.SetLocked(True)
                board.Add(v)
            else:
                _, a, b, w, ly, net = item
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(a); t.SetEnd(b); t.SetWidth(w); t.SetLayer(ly)
                t.SetNet(board.FindNet(net)); t.SetLocked(True)
                board.Add(t)
        print(f"restored {len(saved)} pre-routed items on {len(keep_nets)} nets")

    pcbnew.SaveBoard(pcb, board)
    print(f"routed: {len(board.GetTracks())} track items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
