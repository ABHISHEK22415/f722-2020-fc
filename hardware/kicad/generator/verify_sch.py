import json, sys, xml.etree.ElementTree as ET
from collections import defaultdict
d = sys.argv[1]
intended = json.load(open(f'{d}/intended_connections.json'))
want = defaultdict(set)
for ref, pin, net in intended:
    if not ref.startswith('#'): want[net].add((ref, pin))  # power flags are not exported to netlists
root = ET.parse(f'{d}/net.xml').getroot()
got = {}
for n in root.iter('net'):
    name = n.get('name').lstrip('/')
    got[name] = {(x.get('ref'), x.get('pin')) for x in n.iter('node')}
bad = 0
for net, nodes in want.items():
    g = got.get(net, set())
    real = g
    if real != nodes:
        bad += 1; print('MISMATCH', net, 'missing', nodes - real, 'extra', real - nodes)
sys.path.insert(0, '.')
import design
nc_intended = {(p['ref'], n) for p in design.parts for n, v in p['pins'].items() if v is None}
stray = [k for k in got if k not in want]
nc_seen = set()
for k in stray:
    if k.startswith('unconnected-') and len(got[k]) == 1 and next(iter(got[k])) in nc_intended:
        nc_seen |= got[k]; continue
    print('UNINTENDED NET', k, sorted(got[k])[:6])
print('no-connect pins confirmed:', len(nc_seen), 'of', len(nc_intended))
stray = [k for k in stray if not got[k] <= nc_seen]
pin_count = sum(len(v) for v in want.values())
comps = {c.get('ref') for c in root.iter('comp')}
print(f'nets intended: {len(want)}  nets in KiCad: {len(got)}  connections checked: {pin_count}  mismatches: {bad}  stray nets: {len(stray)}  components: {len(comps)}')
