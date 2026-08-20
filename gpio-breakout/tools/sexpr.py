"""Minimal S-expression reader/writer for KiCad files."""


class Sym(str):
    """A bare (unquoted) symbol token."""
    __slots__ = ()


def loads(text):
    i = 0
    n = len(text)

    def parse():
        nonlocal i
        while i < n and text[i].isspace():
            i += 1
        if text[i] == '(':
            i += 1
            out = []
            while True:
                while i < n and text[i].isspace():
                    i += 1
                if text[i] == ')':
                    i += 1
                    return out
                out.append(parse())
        elif text[i] == '"':
            i += 1
            buf = []
            while text[i] != '"':
                if text[i] == '\\':
                    buf.append(text[i:i + 2])
                    i += 2
                else:
                    buf.append(text[i])
                    i += 1
            i += 1
            return ''.join(buf)
        else:
            j = i
            while i < n and not text[i].isspace() and text[i] not in '()':
                i += 1
            return Sym(text[j:i])

    return parse()


def dumps(node, indent=0):
    pad = '\t' * indent
    if isinstance(node, list):
        if not node:
            return pad + '()'
        # decide inline vs block: inline if no sublists
        if not any(isinstance(x, list) for x in node):
            return pad + '(' + ' '.join(atom(x) for x in node) + ')'
        parts = [pad + '(' + atom(node[0])]
        k = 1
        # keep leading atoms on the same line
        while k < len(node) and not isinstance(node[k], list):
            parts[0] += ' ' + atom(node[k])
            k += 1
        lines = [parts[0]]
        for x in node[k:]:
            lines.append(dumps(x, indent + 1))
        lines.append(pad + ')')
        return '\n'.join(lines)
    return pad + atom(node)


def atom(x):
    if isinstance(x, Sym):
        return str(x)
    if isinstance(x, bool):
        return 'yes' if x else 'no'
    if isinstance(x, float):
        s = ('%.6f' % x).rstrip('0').rstrip('.')
        return s if s not in ('-0',) else '0'
    if isinstance(x, int):
        return str(x)
    # quoted string
    return '"' + str(x).replace('\\', '\\\\').replace('"', '\\"') + '"'


def find(node, key):
    """First child list whose head == key."""
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]
