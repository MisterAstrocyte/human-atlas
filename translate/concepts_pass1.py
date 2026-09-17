import json, re, sys, io, contextlib
atlas = json.load(open('public/models/atlas.json'))
parts = set(p['name'].lower() for p in atlas['parts'])
con = sorted(set(c['name'].lower() for c in atlas['concepts']) - parts)

def load(path, argv=None):
    ns = {'__name__':'x'}; src = open(path).read()
    old = sys.argv; sys.argv = argv or [path]
    with contextlib.redirect_stdout(io.StringIO()): exec(src, ns)
    sys.argv = old; return ns

sk = load('translate/skeletal.py'); mu = load('translate/muscular.py')
ve = load('translate/vessels.py', ['vessels.py','venous'])   # venous merges artery+vein vocab
nr = load('translate/nerv_resp.py'); org = load('translate/organs.py')
small = load('translate/small.py')['T']

def lookup_dict(D, t, ns):
    m = re.match(r'^(left|right) (.+)$', t)
    if t in D: de,dg,la,lg = D[t]; return (de, la)
    if m and m.group(2) in D:
        s = 0 if m.group(1)=='left' else 1; de,dg,la,lg = D[m.group(2)]
        return (f"{ns['DE_SIDE'][dg][s]} {ns['lc'](de)}", f"{la} {ns['LA_SIDE'][lg][s]}")
    return None

def try_all(t):
    for f in (sk['translate'], mu['translate']):
        try:
            r = f(t)
            if r: return r
        except Exception: pass
    try:
        r = ve['translate'](t)
        if r: return r
    except Exception: pass
    for D, ns in ((nr['N'], nr), (nr['R'], nr), (org['D'], org)):
        r = lookup_dict(D, t, ns)
        if r: return r
    if t in small: return small[t]
    return None

done, todo = {}, []
for t in con:
    r = try_all(t)
    if r: done[t] = r
    else: todo.append(t)
print(len(done), 'covered by existing generators;', len(todo), 'remaining')
json.dump(done, open('translate/concepts_covered.json','w'), ensure_ascii=False, indent=1)
open('translate/concepts_todo.txt','w').write('\n'.join(todo))

# ---- pass 2: side-less variants of sided patterns ----
def strip_side(de, la):
    de = re.sub(r'^(Linker|Linke|Linkes) ', '', de)
    de = re.sub(r'\b(des|der) linken ', r'\1 ', de)
    de = re.sub(r' linken ', ' ', de)
    # re-capitalize a lowercased adjective that is now first
    de = de[0].upper() + de[1:]
    la = re.sub(r' (sinistri|sinistrae|sinister|sinistra|sinistrum)\b', '', la)
    return de, la

def variants(t):
    yield 'left ' + t
    idx = [m.end() for m in re.finditer(r' of ', t)]
    for i in idx: yield t[:i] + 'left ' + t[i:]
    for i in idx:
        for j in idx:
            if j > i: yield t[:i] + 'left ' + t[i:j] + 'left ' + t[j:]
    m = re.match(r'^(.+) (branch|part|division|head|tributary) of (.+)$', t)
    if m: yield f'{m.group(1)} {m.group(2)} of left {m.group(3)}'

todo2 = []
for t in todo:
    r = None
    for v in variants(t):
        r = try_all(v)
        if r: break
    if r: done[t] = strip_side(*r)
    else: todo2.append(t)
print(len(done), 'covered after pass 2;', len(todo2), 'remaining')
json.dump(done, open('translate/concepts_covered.json','w'), ensure_ascii=False, indent=1)
open('translate/concepts_todo.txt','w').write('\n'.join(todo2))
