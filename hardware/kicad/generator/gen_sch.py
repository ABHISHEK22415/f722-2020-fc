"""Generate the F722-2020 Rev B KiCad 7 schematic from design.py (net-label style, one A0 sheet)."""
import re, sys, uuid, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sexp, design

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'out'
OUT.mkdir(parents=True, exist_ok=True)
PROJECT = 'f722-2020-fc'
sexp._cache['fc'] = (HERE / 'fc.kicad_sym').read_text()
G = 1.27
def snap(v): return round(v / G) * G
def U(): return str(uuid.uuid4())
ROOT = U()

def symbol_text(lib_id):
    lib, name = lib_id.split(':')
    if lib == 'fc':
        t = sexp._cache['fc']
        s = sexp.block(t, t.index(f'(symbol "{name}"'))
        return s.replace(f'(symbol "{name}"', f'(symbol "fc:{name}"', 1)
    return sexp.flat_symbol(lib, name)

def graphic_bbox(sym, pins):
    xs, ys = [], []
    body = re.sub(r'\(property .*?\n', '', sym)
    for m in re.finditer(r'\((?:start|end|xy|center) ([-\d.]+) ([-\d.]+)\)', body):
        xs.append(float(m.group(1))); ys.append(float(m.group(2)))
    for p in pins:
        xs.append(p[3]); ys.append(p[4])
    if not xs: xs, ys = [0], [0]
    return min(xs), max(xs), min(ys), max(ys)

LABEL_W = lambda net: 1.0 * len(net) + 2.0

lib_used = {}
items = []           # placed symbol records
for part in design.parts:
    lib_id = part['lib']
    if lib_id not in lib_used: lib_used[lib_id] = symbol_text(lib_id)
    sym = lib_used[lib_id]
    pins = [p for p in sexp.pins(sym) if p[7] in (0, 1)]
    x0, x1, y0, y1 = graphic_bbox(sym, pins)
    # extents including labels (symbol coords: y up)
    lx0, lx1, ly0, ly1 = x0, x1, y0, y1
    for p in pins:
        net = part['pins'].get(p[0], None)
        w = LABEL_W(net) if net else 2.0
        if p[5] == 0: lx0 = min(lx0, p[3] - w)
        elif p[5] == 180: lx1 = max(lx1, p[3] + w)
        elif p[5] == 90: ly0 = min(ly0, p[4] - w)
        elif p[5] == 270: ly1 = max(ly1, p[4] + w)
    items.append(dict(part=part, sym=sym, pins=pins, ext=(lx0, lx1, ly0 - 3, ly1 + 3)))

# PWR_FLAGs
flag_sym = sexp.flat_symbol('power', 'PWR_FLAG')
lib_used['power:PWR_FLAG'] = flag_sym
for i, net in enumerate(design.PWR_FLAGS, start=1):
    part = dict(ref=f'#FLG{i:02d}', lib='power:PWR_FLAG', value='PWR_FLAG', fp='', pins={'1': net}, group='Power flags', place=None)
    pins = sexp.pins(flag_sym)
    items.append(dict(part=part, sym=flag_sym, pins=pins, ext=(-1.5, 1.5 + LABEL_W(net) * 0, -LABEL_W(net) - 2, 4)))

# ---------- pack: blocks of groups, shelf packing inside each block ----------
groups = design.GROUP_ORDER + ['Power flags']
SHEET_W, SHEET_H = 1189.0, 841.0
MARGIN = 20.0
GAP = 6.0
placements = {}
block_boxes = []
bx, by, row_h = MARGIN, MARGIN + 18, 0.0
BLOCK_W = {'MCU': 230, 'Edge pads': 300, 'Connectors': 260, 'Motor outputs': 200}
for g in groups:
    members = [it for it in items if it['part']['group'] == g]
    if not members: continue
    bw = BLOCK_W.get(g, 210)
    cx, cy, shelf_h, maxx = 0.0, 12.0, 0.0, 0.0
    local = []
    for it in members:
        lx0, lx1, ly0, ly1 = it['ext']
        w, h = lx1 - lx0, ly1 - ly0
        if cx > 0 and cx + w > bw:
            cx, cy, shelf_h = 0.0, cy + shelf_h + GAP, 0.0
        # symbol origin so that its extent's top-left lands at (cx, cy); schematic y down = -symbol y
        ox, oy = cx - lx0, cy + ly1
        local.append((it, ox, oy))
        cx += w + GAP; shelf_h = max(shelf_h, h); maxx = max(maxx, cx)
    bh = cy + shelf_h + 4
    bwr = max(maxx, 60)
    if bx > MARGIN and bx + bwr > SHEET_W - MARGIN:
        bx, by, row_h = MARGIN, by + row_h + 14, 0.0
    for it, ox, oy in local:
        placements[it['part']['ref']] = (snap(bx + ox), snap(by + oy))
    block_boxes.append((g, bx, by, bwr, bh))
    bx += bwr + 14; row_h = max(row_h, bh)
total_h = by + row_h + MARGIN
assert total_h < SHEET_H, f'sheet too small: {total_h:.0f} mm'

# ---------- emit ----------
def eff(size=1.27, hide=False, justify=None, bold=False):
    j = f' (justify {justify})' if justify else ''
    b = ' bold' if bold else ''
    return f'(effects (font (size {size} {size}){b}){j}{" hide" if hide else ""})'

out = []
out.append(f'(kicad_sch (version 20230121) (generator eeschema)\n  (uuid {ROOT})\n  (paper "A0")')
out.append('  (title_block (title "F722-2020 Flight Controller") (date "2026-10-27") (rev "B") (company "Abhishek")'
           ' (comment 1 "20x20 mm, STM32F722RET6 + MPU6000, 6 UARTs, 8 motor outputs")'
           ' (comment 2 "Rev B: noise-review fixes applied. Net-label schematic; see docs/noise-review.md"))')
out.append('  (lib_symbols')
for lib_id, sym in lib_used.items():
    out.append('    ' + sym.replace('\n', '\n  '))
out.append('  )')

labels, ncs, conns = [], [], []
LABEL_ANGLE = {0: 180, 180: 0, 90: 270, 270: 90}
JUST = {0: 'left bottom', 180: 'right bottom', 90: 'left bottom', 270: 'right bottom'}
for it in items:
    part = it['part']; ref = part['ref']
    X, Y = placements[ref]
    lx0, lx1, ly0, ly1 = it['ext']
    is_flag = ref.startswith('#')
    is_mech = part['lib'].startswith('Mechanical')
    in_bom = 'no' if is_flag or is_mech else 'yes'
    on_board = 'no' if is_flag else 'yes'
    s = [f'  (symbol (lib_id "{part["lib"]}") (at {X:.2f} {Y:.2f} 0) (unit 1)',
         f'    (in_bom {in_bom}) (on_board {on_board}) (dnp no)',
         f'    (uuid {U()})',
         f'    (property "Reference" "{ref}" (at {X + (it["ext"][0] + it["ext"][1]) / 2:.2f} {Y - it["ext"][3] + 1.5:.2f} 0) {eff(hide=is_flag)})',
         f'    (property "Value" "{part["value"]}" (at {X + (it["ext"][0] + it["ext"][1]) / 2:.2f} {Y - it["ext"][2] - 1.0:.2f} 0) {eff(hide=is_flag)})',
         f'    (property "Footprint" "{part["fp"]}" (at {X:.2f} {Y:.2f} 0) {eff(hide=True)})',
         f'    (property "Datasheet" "~" (at {X:.2f} {Y:.2f} 0) {eff(hide=True)})']
    for p in it['pins']:
        s.append(f'    (pin "{p[0]}" (uuid {U()}))')
    s.append(f'    (instances (project "{PROJECT}" (path "/{ROOT}" (reference "{ref}") (unit 1))))')
    s.append('  )')
    out.append('\n'.join(s))
    # labels / no-connects at every pin end
    for p in it['pins']:
        num, name, etype, px, py, ang = p[0], p[1], p[2], p[3], p[4], p[5]
        ax, ay = round(X + px, 2), round(Y - py, 2)
        if num in part['pins'] and part['pins'][num]:
            net = part['pins'][num]
            labels.append(f'  (label "{net}" (at {ax:.2f} {ay:.2f} {LABEL_ANGLE[ang]}) (fields_autoplaced) {eff(justify=JUST[ang])} (uuid {U()}))')
            conns.append((ref, num, net))
        elif etype != 'no_connect' or True:
            if part['lib'].startswith('Mechanical'): continue
            ncs.append(f'  (no_connect (at {ax:.2f} {ay:.2f}) (uuid {U()}))')
out.extend(labels); out.extend(ncs)
# block titles and frames
for g, x, y, w, h in block_boxes:
    out.append(f'  (text "{g}" (at {x:.2f} {y + 4:.2f} 0) {eff(size=2.54, bold=True, justify="left bottom")} (uuid {U()}))')
    out.append(f'  (rectangle (start {x - 4:.2f} {y - 1:.2f}) (end {x + w + 2:.2f} {y + h + 2:.2f}) (stroke (width 0.2) (type dash)) (fill (type none)) (uuid {U()}))')
out.append(f'  (text "F722-2020 flight controller, Rev B. Connections are made with net labels: pins with the same label are connected." (at {MARGIN:.2f} {MARGIN + 6:.2f} 0) {eff(size=2.54, justify="left bottom")} (uuid {U()}))')
out.append('  (sheet_instances (path "/" (page "1")))\n)')
(OUT / f'{PROJECT}.kicad_sch').write_text('\n'.join(out) + '\n')

# project files
(OUT / f'{PROJECT}.kicad_pro').write_text('{\n  "meta": {"filename": "%s.kicad_pro", "version": 1},\n  "board": {"design_settings": {"defaults": {}, "rules": {"min_clearance": 0.1, "min_track_width": 0.1, "min_via_diameter": 0.45, "min_through_hole_diameter": 0.2}}},\n  "schematic": {}\n}\n' % PROJECT)
(OUT / 'sym-lib-table').write_text('(sym_lib_table\n  (lib (name "fc")(type "KiCad")(uri "${KIPRJMOD}/fc.kicad_sym")(options "")(descr "F722-2020 custom symbols"))\n)\n')
(OUT / 'fc.kicad_sym').write_text(sexp._cache['fc'])
import json
(OUT / 'intended_connections.json').write_text(json.dumps(conns))
print(f'symbols: {len(items)}  labels: {len(labels)}  no-connects: {len(ncs)}  sheet height used: {total_h:.0f} mm')
