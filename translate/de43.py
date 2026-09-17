import json, re, sys, io, contextlib
sys.path.insert(0,'translate')
m=json.load(open('data43/concepts43.json'))
names=sorted({e['name'] for e in m['elements']} | {c['name'] for c in m['concepts']})
old={}
for f in ('atlas-de-all.csv',):
    import csv
    for r in csv.DictReader(open('/mnt/user-data/outputs/'+f)): old[r['english'].lower()]=(r['german'],r['latin'])
def load(path, argv=None):
    ns={'__name__':'x'}; o=sys.argv; sys.argv=argv or [path]
    with contextlib.redirect_stdout(io.StringIO()): exec(open(path).read(), ns)
    sys.argv=o; return ns
sk=load('translate/skeletal.py'); mu=load('translate/muscular.py'); ve=load('translate/vessels.py',['v','venous'])
nr=load('translate/nerv_resp.py'); org=load('translate/organs.py'); sm=load('translate/small.py')['T']
def lk(D,t,ns):
    mm=re.match(r'^(left|right) (.+)$',t)
    if t in D: de,dg,la,lg=D[t]; return (de,la)
    if mm and mm.group(2) in D:
        s=0 if mm.group(1)=='left' else 1; de,dg,la,lg=D[mm.group(2)]
        return (f"{ns['DE_SIDE'][dg][s]} {ns['lc'](de)}", f"{la} {ns['LA_SIDE'][lg][s]}")
def tr(t):
    if t in old: return old[t]
    for f in (sk['translate'],mu['translate']):
        try:
            r=f(t)
            if r: return r
        except Exception: pass
    try:
        r=ve['translate'](t)
        if r: return r
    except Exception: pass
    for D,ns in ((nr['N'],nr),(nr['R'],nr),(org['D'],org)):
        r=lk(D,t,ns)
        if r: return r
    if t in sm: return sm[t]
    return None
done={}; todo=[]
for n in names:
    r=tr(n.lower())
    if r: done[n]=r
    else: todo.append(n)
print(len(names),'names;',len(done),'translated;',len(todo),'missing')
json.dump(done, open('data43/de43_done.json','w'), ensure_ascii=False)
open('data43/de43_todo.txt','w').write('\n'.join(todo))
