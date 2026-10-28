"""Tiny KiCad S-expression helpers: extract symbol blocks (flattening `extends`) and pin lists."""
import re
LIB = '/usr/share/kicad/symbols'
_cache = {}
def lib_text(lib):
    if lib not in _cache: _cache[lib] = open(f'{LIB}/{lib}.kicad_sym').read()
    return _cache[lib]
def block(txt, start):
    depth = 0; j = start; instr = False
    while True:
        c = txt[j]
        if c == '"' and txt[j-1] != '\\': instr = not instr
        elif not instr:
            if c == '(': depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0: return txt[start:j+1]
        j += 1
def raw_symbol(lib, name):
    t = lib_text(lib)
    i = t.index(f'\n  (symbol "{name}"') + 3
    return block(t, i)
def flat_symbol(lib, name):
    """Return the symbol S-expr with any `extends` resolved, named lib:name."""
    s = raw_symbol(lib, name)
    m = re.match(r'\(symbol "[^"]+" \(extends "([^"]+)"\)', s)
    if m:
        parent = flat_symbol(lib, m.group(1)).split('\n', 1)  # already renamed
        pname = m.group(1)
        pbody = flat_symbol_body(lib, pname)
        child_props = re.findall(r'\n    \(property .*?(?=\n    \(|\n  \)$|\)$)', s, re.S)
        # take child's header lines (properties) and parent's sub-symbols/pins
        head = s[:s.index('\n')]
        props = ''.join(child_props)
        subs = [b for b in sub_blocks(pbody) if b.startswith('(symbol ')]
        subs = [b.replace(f'(symbol "{pname}_', f'(symbol "{name}_', 1) for b in subs]
        flags = re.findall(r'\n    \((?:pin_numbers|pin_names|in_bom|on_board|exclude_from_sim)[^\n]*', pbody)
        s = f'(symbol "{name}"' + ''.join(flags) + props + ''.join('\n    ' + b for b in subs) + '\n  )'
    return s.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)
def flat_symbol_body(lib, name):
    s = raw_symbol(lib, name)
    m = re.match(r'\(symbol "[^"]+" \(extends "([^"]+)"\)', s)
    if m:
        return flat_symbol(lib, name).replace(f'(symbol "{lib}:{name}"', f'(symbol "{name}"', 1)
    return s
def sub_blocks(s):
    out = []; i = s.index('\n') if '\n' in s else 1
    while True:
        k = s.find('(', i)
        if k < 0 or k >= len(s) - 1: break
        b = block(s, k); out.append(b); i = k + len(b)
    return out
def pins(sym):
    """[(number, name, etype, x, y, angle, length, unit)] from a flattened symbol."""
    res = []
    for sub in re.finditer(r'\(symbol "[^"]*_(\d+)_(\d+)"', sym):
        unit = int(sub.group(1))
        b = block(sym, sub.start())
        for p in re.finditer(r'\(pin (\w+) \w+\s+\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s+\(length ([\d.]+)\)(?:\s+hide)?\s+\(name "([^"]*)".*?\(number "([^"]*)"', b, re.S):
            res.append((p.group(7), p.group(6), p.group(1), float(p.group(2)), float(p.group(3)), int(p.group(4)), float(p.group(5)), unit))
    return res
