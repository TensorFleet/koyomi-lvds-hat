"""Load symbols from KiCad 10 standard libraries, resolve inheritance, list pins."""
import os
import sexpr

SYMDIR = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols'
FPDIR = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'

_lib_cache = {}


def _load_lib(lib):
    if lib not in _lib_cache:
        with open(os.path.join(SYMDIR, lib + '.kicad_sym')) as f:
            _lib_cache[lib] = sexpr.loads(f.read())
    return _lib_cache[lib]


def get_symbol(lib, name):
    """Return the (symbol "name" ...) node, with 'extends' resolved (flattened)."""
    root = _load_lib(lib)
    for node in sexpr.find_all(root, 'symbol'):
        if node[1] == name:
            ext = sexpr.find(node, 'extends')
            if ext:
                parent = get_symbol(lib, ext[1])
                return _merge_extends(parent, node)
            return node
    raise KeyError('%s:%s' % (lib, name))


def _merge_extends(parent, child):
    """Flatten: take parent's drawing/pins + child's properties."""
    import copy
    out = copy.deepcopy(parent)
    out[1] = child[1]
    # replace properties defined by child
    child_props = {p[1]: p for p in sexpr.find_all(child, 'property')}
    newout = [out[0], out[1]]
    for x in out[2:]:
        if isinstance(x, list) and x and x[0] == 'property' and x[1] in child_props:
            newout.append(copy.deepcopy(child_props[x[1]]))
            del child_props[x[1]]
        elif isinstance(x, list) and x and x[0] == 'symbol':
            y = copy.deepcopy(x)
            # rename subsymbol prefix
            y[1] = y[1].replace(parent[1] + '_', child[1] + '_', 1)
            newout.append(y)
        else:
            newout.append(copy.deepcopy(x))
    for p in child_props.values():
        import copy as c
        newout.append(c.deepcopy(p))
    return newout


def pins(symnode):
    """List of dicts: number, name, type, x, y, angle, length (symbol coords)."""
    out = []
    for sub in sexpr.find_all(symnode, 'symbol'):
        for p in sexpr.find_all(sub, 'pin'):
            at = sexpr.find(p, 'at')
            out.append({
                'number': sexpr.find(p, 'number')[1],
                'name': sexpr.find(p, 'name')[1],
                'type': str(p[1]),
                'x': float(at[1]), 'y': float(at[2]), 'angle': float(at[3]),
                'length': float(sexpr.find(p, 'length')[1]),
            })
    return out


def prop(symnode, name, default=''):
    for p in sexpr.find_all(symnode, 'property'):
        if p[1] == name:
            return p[2]
    return default


if __name__ == '__main__':
    import sys
    node = get_symbol(sys.argv[1], sys.argv[2])
    print('Footprint:', prop(node, 'Footprint'))
    for p in sorted(pins(node), key=lambda q: (len(q['number']), q['number'])):
        print('%4s %-14s %-12s at %7.2f %7.2f ang %3.0f len %.2f' % (
            p['number'], p['name'], p['type'], p['x'], p['y'], p['angle'], p['length']))
