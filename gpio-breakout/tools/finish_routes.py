#!/usr/bin/env python3
"""Close the four router-abandoned nets with collision-checked manual copper.

Run with KiCad's bundled python3. Adds:
  * +5V stub completion to J2 pad 2;
  * +5V_FFC and +3V3_FFC runs along the free band above the FFC signal row;
  * GND stitch vias (to the In1 plane) for the FFC's six mid-row ground pads.
Every segment/via is clearance-checked against existing copper before it is
added; the script aborts rather than place a colliding item.
"""
import sys
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

PCB = '/private/tmp/claude-501/-Users-hyper-projects-tensorfleet-vaio-p-modding/2f5c30d3-28a2-4e2f-a4f0-197163398436/scratchpad/bo2/gpio-breakout/kicad/gpio_breakout.kicad_pcb'
CLR = 0.2
W = 0.3          # manual track width (power + stubs)
VIA_D, VIA_DR = 0.6, 0.3

board = pcbnew.LoadBoard(PCB)
nets = {n: board.FindNet(n) for n in ('+5V', '+5V_FFC', '+3V3_FFC', 'GND')}

def seg_pt_dist(a, b, p):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx-ax, by-ay
    L2 = dx*dx + dy*dy
    if L2 == 0: return ((px-ax)**2 + (py-ay)**2) ** 0.5
    t = max(0, min(1, ((px-ax)*dx + (py-ay)*dy) / L2))
    cx, cy = ax + t*dx, ay + t*dy
    return ((px-cx)**2 + (py-cy)**2) ** 0.5

def seg_seg_dist(a, b, c, d):
    return min(seg_pt_dist(a, b, c), seg_pt_dist(a, b, d),
               seg_pt_dist(c, d, a), seg_pt_dist(c, d, b))

def copper_items(layer_id):
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_TRACK' and t.GetLayer() == layer_id:
            s, e = t.GetStart(), t.GetEnd()
            yield ('trk', (ToMM(s.x), ToMM(s.y)), (ToMM(e.x), ToMM(e.y)),
                   ToMM(t.GetWidth())/2, t.GetNetname())
        elif t.GetClass() == 'PCB_VIA':
            p = t.GetPosition()
            yield ('via', (ToMM(p.x), ToMM(p.y)), None, ToMM(t.GetWidth())/2, t.GetNetname())
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if not pad.IsOnLayer(layer_id): continue
            p = pad.GetPosition(); sz = pad.GetSize()
            r = max(ToMM(sz.x), ToMM(sz.y))/2
            yield ('pad', (ToMM(p.x), ToMM(p.y)), None, r, pad.GetNetname())

def check_seg(a, b, layer_id, net, halfw, trust_pitch=False):
    for kind, p1, p2, r, iname in copper_items(layer_id):
        if iname == net: continue
        if trust_pitch and kind == 'pad' and abs(p1[1] - 56.79) < 0.01 and abs(p1[0] - a[0]) <= 0.6:
            continue  # J1 signal-row neighbor: 0.25 riser on own pad x has 0.225 edge gap
        d = seg_seg_dist(a, b, p1, p2) if p2 else seg_pt_dist(a, b, p1)
        if d < halfw + r + CLR - 1e-3:
            return (kind, p1, iname, round(d, 3))
    return None

def add_track(pts, layer_id, netname, w=W, trust_pitch=False):
    net = nets[netname]
    for a, b in zip(pts, pts[1:]):
        hit = check_seg(a, b, layer_id, netname, w/2, trust_pitch)
        if hit:
            print('ABORT %s seg %s-%s hits %s' % (netname, a, b, hit)); sys.exit(1)
    for a, b in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(VECTOR2I(FromMM(a[0]), FromMM(a[1])))
        t.SetEnd(VECTOR2I(FromMM(b[0]), FromMM(b[1])))
        t.SetLayer(layer_id)
        t.SetWidth(FromMM(w))
        t.SetNet(net)
        t.SetLocked(True)
        board.Add(t)
    print('added %s: %d segs' % (netname, len(pts)-1))

def add_via(x, y, netname):
    for lay in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        hit = check_seg((x, y), (x, y), lay, netname, VIA_D/2)
        if hit:
            return hit
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
    v.SetWidth(FromMM(VIA_D)); v.SetDrill(FromMM(VIA_DR))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(nets[netname])
    v.SetLocked(True)
    board.Add(v)
    return None

F = pcbnew.F_Cu

# 1. +5V stub -> J2 pad 2 at (56.9, 66.66); stub end at (56.9, 62.45)
add_track([(56.9, 62.45), (56.9, 66.66)], F, '+5V')

# 2+3. power runs: F band above the FFC row, drop to B.Cu for the left descent
B = pcbnew.B_Cu
def must_via(x, y, netname):
    hit = add_via(x, y, netname)
    if hit:
        print('ABORT via %s at (%.1f,%.1f) hits %s' % (netname, x, y, hit)); sys.exit(1)

# +5V_FFC
add_track([(90.25, 56.79), (90.25, 55.2)], F, '+5V_FFC', w=0.25, trust_pitch=True)
add_track([(89.25, 56.79), (89.25, 55.2)], F, '+5V_FFC', w=0.25, trust_pitch=True)
add_track([(90.25, 55.2), (89.25, 55.2)], F, '+5V_FFC', w=0.25, trust_pitch=True)
add_track([(89.25, 55.2), (89.25, 52.7)], F, '+5V_FFC', w=0.25, trust_pitch=True)
add_track([(89.25, 52.7), (55.2, 52.7), (55.2, 53.4)], F, '+5V_FFC')
must_via(55.2, 53.4, '+5V_FFC')
add_track([(55.2, 53.4), (55.6, 53.8), (55.6, 60.6)], B, '+5V_FFC')
must_via(55.6, 60.6, '+5V_FFC')
add_track([(55.6, 60.6), (54.9, 61.2), (53.9, 61.2)], F, '+5V_FFC')

# +3V3_FFC
add_track([(90.75, 56.79), (90.75, 53.5)], F, '+3V3_FFC', w=0.25, trust_pitch=True)
add_track([(90.75, 53.5), (56.0, 53.5), (56.4, 53.9)], F, '+3V3_FFC')
must_via(56.4, 53.9, '+3V3_FFC')
add_track([(56.4, 53.9), (56.25, 54.4), (56.25, 63.2)], B, '+3V3_FFC')
must_via(56.25, 63.2, "+3V3_FFC")
add_track([(56.25, 63.2), (53.9, 66.35)], F, '+3V3_FFC')

# 4. GND stitch vias for J1 pads 6,9,14,20,25,30
gnd_x = {'6': 88.25, '9': 86.75, '14': 84.25, '20': 81.25, '25': 78.75, '30': 76.25}
for padnum, x in gnd_x.items():
    placed = False
    for y in (55.6, 55.2, 55.9, 58.4, 58.8):
        for dx in (0.0, 0.4, -0.4, 0.8, -0.8):
            hit_v = add_via(x + dx, y, 'GND')
            if hit_v is None:
                stub = [(x, 56.79), (x + dx, y)] if dx == 0 else [(x, 56.79), (x, y + (0.5 if y < 56.79 else -0.5)), (x + dx, y)]
                ok = all(not check_seg(a, b, F, 'GND', 0.125, trust_pitch=True) for a, b in zip(stub, stub[1:]))
                if ok:
                    add_track(stub, F, 'GND', w=0.25, trust_pitch=True)
                    placed = True
                else:
                    # remove the via we just placed? simplest: keep via only if stub ok; else abort attempt
                    for t in list(board.GetTracks()):
                        if t.GetClass() == 'PCB_VIA' and abs(ToMM(t.GetPosition().x)-(x+dx)) < 0.01 and abs(ToMM(t.GetPosition().y)-y) < 0.01:
                            board.Remove(t)
            if placed: break
        if placed: break
    if not placed:
        print('ABORT: no via spot for GND pad', padnum); sys.exit(1)
    print('GND pad %s stitched' % padnum)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(PCB)
print('saved')
