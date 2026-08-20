"""Generate kicad/io_breakout.kicad_sch from netlist_def.py.

Style: every pin gets a global label at its connection point (no wires).
Validated afterwards with kicad-cli sch erc.
"""
import uuid

import sexpr
from sexpr import Sym as S
import kicad_libs
import netlist_def_bo as netlist_def
import os as _os
_here = _os.path.dirname(_os.path.abspath(__file__))
kicad_libs._lib_cache['B2_INTERCONNECT'] = sexpr.loads(
    open(_os.path.join(_here, '..', 'B2_INTERCONNECT.kicad_sym')).read())


OUT = '/private/tmp/claude-501/-Users-hyper-projects-tensorfleet-vaio-p-modding/2f5c30d3-28a2-4e2f-a4f0-197163398436/scratchpad/bo2/gpio-breakout/kicad/gpio_breakout.kicad_sch'
PROJECT = 'gpio_breakout'

# Stable UUIDs: derive from a fixed namespace so regeneration is deterministic.
NS = uuid.UUID('9c1f0f6e-2a54-4bb0-9d3e-1f60a55d0001')


def uid(*key):
    return str(uuid.uuid5(NS, '/'.join(str(k) for k in key)))


ROOT_UUID = uid('root')

# ---------------------------------------------------------------- layout ----
# grid positions (mm) for each ref; symbols are large, keep generous spacing
POS = {
    'J1': (70, 80), 'J2': (200, 80),
    'JP1': (300, 50), 'JP2': (300, 80), 'JP3': (300, 110),
    'TP1': (340, 50), 'TP2': (340, 80), 'TP3': (340, 110),
    'TP4': (340, 140), 'TP5': (300, 140),
    'H1': (60, 200), 'H2': (90, 200),
    'F1': (240, 140), 'JP4': (200, 140), 'JP5': (200, 170),
}
FLAG_X0, FLAG_Y = 40, 380  # PWR_FLAG row


def snap(v):
    """snap to 1.27mm grid"""
    return round(round(v / 1.27) * 1.27, 4)


def effects(hide=False, size=1.27):
    e = [S('effects'), [S('font'), [S('size'), size, size]]]
    if hide:
        e.append([S('hide'), S('yes')])
    return e


def prop(name, val, x, y, hide=False):
    return [S('property'), name, val, [S('at'), x, y, 0], effects(hide)]


def main():
    used_syms = {}   # "Lib:Name" -> embedded node
    body = []
    label_points = set()

    def embed(libname, symname):
        key = '%s:%s' % (libname, symname)
        if key not in used_syms:
            node = kicad_libs.get_symbol(libname, symname)
            import copy
            n = copy.deepcopy(node)
            n[1] = key
            used_syms[key] = n
        return used_syms[key]

    def place(ref, libsym, value, footprint, pinmap, flags, x, y):
        libname, symname = libsym.split(':')
        node = embed(libname, symname)
        pins = kicad_libs.pins(node)
        su = uid('sym', ref)
        inst = [S('symbol'), [S('lib_id'), libsym], [S('at'), x, y, 0],
                [S('unit'), 1],
                [S('exclude_from_sim'), S('no')], [S('in_bom'), S('yes')],
                [S('on_board'), S('yes')],
                [S('dnp'), S('yes' if flags.get('dnp') else 'no')],
                [S('uuid'), su],
                prop('Reference', ref, x, y - 2.54 * 3, ref.startswith('#')),
                prop('Value', value, x, y + 2.54 * 3, ref.startswith('#')),
                prop('Footprint', footprint, x, y, True),
                prop('Datasheet', '', x, y, True),
                prop('Description', flags.get('desc', ''), x, y, True),
                ]
        if flags.get('lcsc'):
            inst.append(prop('LCSC', flags['lcsc'], x, y, True))
        seen_pins = set()
        for p in pins:
            if p['number'] in seen_pins:
                continue
            seen_pins.add(p['number'])
            inst.append([S('pin'), p['number'], [S('uuid'), uid('pin', ref, p['number'])]])
        inst.append([S('instances'),
                     [S('project'), PROJECT,
                      [S('path'), '/' + ROOT_UUID,
                       [S('reference'), ref], [S('unit'), 1]]]])
        body.append(inst)

        # labels / no-connects
        if pinmap is not None:
            bypos = {}
            for p in pins:
                px, py = snap(x + p['x']), snap(y - p['y'])
                net = pinmap.get(p['number'], '__MISSING__')
                if net == '__MISSING__':
                    raise SystemExit('%s pin %s (%s) has no net assignment'
                                     % (ref, p['number'], p['name']))
                bypos.setdefault((px, py), []).append((p, net))
            for (px, py), plist in sorted(bypos.items()):
                nets = {n for _, n in plist}
                if len(nets) > 1:
                    raise SystemExit('%s: stacked pins at %s,%s map to different nets %s'
                                     % (ref, px, py, nets))
                net = nets.pop()
                p0 = plist[0][0]
                if net == netlist_def.NC:
                    for p, _ in plist:
                        body.append([S('no_connect'), [S('at'), px, py],
                                     [S('uuid'), uid('nc', ref, p['number'])]])
                    continue
                if (px, py) in label_points:
                    raise SystemExit('label point collision at %s,%s (%s)' % (px, py, ref))
                label_points.add((px, py))
                ang = int((p0['angle'] + 180) % 360)
                body.append([S('global_label'), net, [S('shape'), S('passive')],
                             [S('at'), px, py, ang], effects(),
                             [S('uuid'), uid('lbl', ref, p0['number'])],
                             [S('property'), 'Intersheetrefs', '${INTERSHEET_REFS}',
                              [S('at'), px, py, 0], effects(True)]])

    for ref, libsym, value, footprint, pinmap, flags in netlist_def.COMPONENTS:
        x, y = POS[ref]
        place(ref, libsym, value, footprint, pinmap, flags, snap(x), snap(y))

    for i, (ref, net) in enumerate(netlist_def.PWR_FLAGS):
        x, y = snap(FLAG_X0 + 30 * i), snap(FLAG_Y)
        place(ref, 'power:PWR_FLAG', 'PWR_FLAG', '', {'1': net}, {}, x, y)

    doc = [S('kicad_sch'),
           [S('version'), 20250114],
           [S('generator'), 'gen_sch'],
           [S('generator_version'), '10.0'],
           [S('uuid'), ROOT_UUID],
           [S('paper'), 'A2'],
           [S('title_block'),
            [S('title'), 'koyomi gpio-breakout A1'],
            [S('date'), '2026-08-02'],
            [S('rev'), 'A1'],
            [S('comment'), 1, 'FH41 40P FFC to Pi GPIO bench adapter']],
           [S('lib_symbols')] + list(used_syms.values()),
           ]
    doc += body
    doc.append([S('sheet_instances'), [S('path'), '/', [S('page'), '1']]])
    doc.append([S('embedded_fonts'), S('no')])

    with open(OUT, 'w') as f:
        f.write(sexpr.dumps(doc) + '\n')
    print('wrote', OUT, '-', len(netlist_def.COMPONENTS), 'components,',
          len(label_points), 'label points')


if __name__ == '__main__':
    main()
