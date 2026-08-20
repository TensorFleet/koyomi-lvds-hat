"""Generate kicad/io_breakout.kicad_pcb from the exported schematic netlist.

Run with KiCad's bundled python3 (pcbnew module).
Phases: placement -> routing -> zones -> save. Validated with kicad-cli pcb drc.
"""
import os
import sys

import pcbnew
from pcbnew import VECTOR2I, FromMM

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sexpr  # noqa: E402

REPO = os.path.dirname(os.path.abspath(__file__)) + '/..'
NETFILE = os.path.join(REPO, 'kicad', 'gpio_breakout.net')
OUT = os.path.join(REPO, 'kicad', 'gpio_breakout.kicad_pcb')
FPBASE = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'

# Board origin (page coords) and size
OX, OY = 50.0, 50.0
BW, BH = 63.5, 30.0


def mm(x, y):
    return VECTOR2I(FromMM(OX + x), FromMM(OY + y))


# ref: (x, y, rot_deg, side)
PLACEMENT = {
    'J1':  (31.0, 3.9, 180, 'F'),
    'J2':  (6.9, 19.2, 90, 'F'),
    'JP1': (46.0, 24.5, 0, 'F'),
    'JP2': (51.0, 24.5, 0, 'F'),
    'JP3': (56.0, 24.5, 0, 'F'),
    'TP1': (46.0, 28.0, 0, 'F'),
    'TP2': (51.0, 28.0, 0, 'F'),
    'TP3': (56.0, 28.0, 0, 'F'),
    'TP4': (61.0, 28.0, 0, 'F'),
    'TP5': (61.0, 24.5, 0, 'F'),
    'H1':  (3.0, 8.5, 0, 'F'),
    'H2':  (60.3, 3.2, 0, 'F'),
}


# refs whose silk designators collide with the readable labels
HIDE_REFS = {'J1', 'J2'}

# visual 3D-model substitutes for footprints whose exact model isn't in the
# shipped library (render cosmetics only; copper/footprint unchanged)
MODEL_SUBS = {}

# human-readable silkscreen labels: (text, x, y, layer)
SILK_LABELS = [
    ('FFC to carrier / LCD', 31.0, 8.3, 'F'),
    ('Pi GPIO', 30.0, 22.3, 'F'),
    ('ID0', 42.8, 24.5, 'F'),
    ('ID1', 48.4, 24.5, 'F'),
    ('INS', 53.4, 24.5, 'F'),
    ('jumpers open = safe', 15.0, 24.5, 'F'),
    ('GND', 61.0, 26.2, 'F'),
    ('3V3', 58.6, 23.2, 'F'),
    ('koyomi gpio-breakout A0', 26.0, 13.5, 'B'),
]


def parse_netlist():
    doc = sexpr.loads(open(NETFILE).read())
    comps = {}
    for c in sexpr.find_all(sexpr.find(doc, 'components'), 'comp'):
        ref = sexpr.find(c, 'ref')[1]
        fp = sexpr.find(c, 'footprint')[1]
        val = sexpr.find(c, 'value')[1]
        ts = sexpr.find(c, 'tstamps')[1]
        props = {p[1]: p[2] for p in []}
        dnp = any(str(f[1]) == 'dnp' for f in sexpr.find_all(c, 'property'))
        comps[ref] = {'fp': fp, 'value': val, 'tstamps': ts, 'dnp': dnp}
    nets = {}
    for n in sexpr.find_all(sexpr.find(doc, 'nets'), 'net'):
        name = sexpr.find(n, 'name')[1]
        nodes = [(sexpr.find(x, 'ref')[1], sexpr.find(x, 'pin')[1])
                 for x in sexpr.find_all(n, 'node')]
        nets[name] = nodes
    return comps, nets


def build():
    comps, nets = parse_netlist()
    board = pcbnew.CreateEmptyBoard()

    # --- board outline ---
    def edge_line(x1, y1, x2, y2):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(mm(x1, y1))
        seg.SetEnd(mm(x2, y2))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(FromMM(0.1))
        board.Add(seg)
    edge_line(0, 0, BW, 0)
    edge_line(BW, 0, BW, BH)
    edge_line(BW, BH, 0, BH)
    edge_line(0, BH, 0, 0)

    # --- nets ---
    netmap = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netmap[name] = ni

    pad_net = {}
    for name, nodes in nets.items():
        for ref, pin in nodes:
            pad_net[(ref, pin)] = name

    # --- footprints ---
    fps = {}
    for ref, info in comps.items():
        lib, fpname = info['fp'].split(':')
        local = os.path.join(REPO, lib + '.pretty')
        fp = (pcbnew.FootprintLoad(local, fpname) if os.path.isdir(local)
              else pcbnew.FootprintLoad(FPBASE + '/' + lib + '.pretty', fpname))
        assert fp, 'footprint not found: %s' % info['fp']
        fp.SetReference(ref)
        fp.SetValue(info['value'])
        fp.SetPath(pcbnew.KIID_PATH(info['tstamps']))
        if info['dnp']:
            try:
                fp.SetDNP(True)
            except AttributeError:
                pass
        board.Add(fp)
        x, y, rot, side = PLACEMENT[ref]
        fp.SetPosition(mm(x, y))
        fp.SetOrientationDegrees(rot)
        if side == 'B':
            fp.Flip(mm(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        for pad in fp.Pads():
            key = (ref, str(pad.GetNumber()))
            if key in pad_net:
                pad.SetNet(netmap[pad_net[key]])
        if ref in HIDE_REFS:
            fp.Reference().SetVisible(False)
        if ref in MODEL_SUBS:
            fp.Models().clear()
            model = pcbnew.FP_3DMODEL()
            model.m_Filename = MODEL_SUBS[ref]
            fp.Models().push_back(model)
        fps[ref] = fp

    # --- silkscreen labels ---
    for text, x, y, layer in SILK_LABELS:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(mm(x, y))
        t.SetLayer(pcbnew.F_SilkS if layer == 'F' else pcbnew.B_SilkS)
        t.SetTextSize(VECTOR2I(FromMM(1.0), FromMM(1.0)))
        t.SetTextThickness(FromMM(0.15))
        if layer == 'B':
            t.SetMirrored(True)
        board.Add(t)
    return board, fps, netmap, comps, nets


def report(board, fps):
    from pcbnew import ToMM
    print('--- pad world coordinates (board-local mm) ---')
    for ref in sorted(fps):
        fp = fps[ref]
        for pad in fp.Pads():
            p = pad.GetPosition()
            print('%-4s %-4s %7.2f %7.2f  net=%s' % (
                ref, pad.GetNumber(), ToMM(p.x) - OX, ToMM(p.y) - OY,
                pad.GetNetname()))
    print('--- courtyard bboxes ---')
    boxes = {}
    for ref in sorted(fps):
        fp = fps[ref]
        side = PLACEMENT[ref][3]
        cy = fp.GetCourtyard(pcbnew.B_CrtYd if side == 'B' else pcbnew.F_CrtYd)
        if cy.OutlineCount() == 0:
            bb = fp.GetBoundingBox(False)
        else:
            bb = cy.BBox()
        boxes[ref] = (ToMM(bb.GetLeft()) - OX, ToMM(bb.GetTop()) - OY,
                      ToMM(bb.GetRight()) - OX, ToMM(bb.GetBottom()) - OY, side)
        print('%-4s %s  %6.2f..%6.2f  %6.2f..%6.2f' % ((ref, side) + boxes[ref][:4]))
    print('--- courtyard overlaps ---')
    refs = sorted(boxes)
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            A, B = boxes[a], boxes[b]
            if A[4] != B[4]:
                continue
            if A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3]:
                print('OVERLAP %s %s' % (a, b))
    print('--- outside board ---')
    for ref, B in boxes.items():
        if B[0] < -3 or B[1] < -3 or B[2] > BW + 3 or B[3] > BH + 3:
            print('WAY OUT', ref, B)


if __name__ == '__main__':
    board, fps, netmap, comps, nets = build()
    report(board, fps)
    board.Save(OUT)
    print('saved', OUT)
