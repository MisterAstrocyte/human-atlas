import json, re, sys, io, contextlib
sys.path.insert(0,'translate')
m=json.load(open('data43/concepts43.json')); done=json.load(open('data43/de43_done.json'))
todo=[x for x in open('data43/de43_todo.txt').read().split('\n') if x]
# fallback: keep English, flag it
for n in todo: done[n]=(n, '')
parts=[{'id':e['id'],'conceptId':e['conceptId'],'english':e['name'],
        'german':done[e['name']][0],'latin':done[e['name']][1]} for e in m['elements'] if e['name'] in done]
cons=[{'id':c['id'],'english':c['name'],'german':done[c['name']][0],'latin':done[c['name']][1]}
      for c in m['concepts'] if c['name'] in done]
json.dump({'language':'de','source':'BodyParts3D 4.3 (CC BY-SA 2.1 JP)','parts':parts,'concepts':cons},
          open('data43/atlas-de.json','w'), ensure_ascii=False, separators=(',',':'))
print('de parts',len(parts),'concepts',len(cons),'english-fallback',len(todo))

# ---- info-de for 4.3 ----
ns={'__name__':'x'}; src=open('translate/build_info.py').read()
src=src.replace("atlas = json.load(open('public/models/atlas.json'))","atlas = json.load(open('data43/atlas43_stub.json'))")
src=src.replace("tr = json.load(open('public/models/atlas-de.json'))","tr = json.load(open('data43/atlas-de.json'))")
src=src.replace("open('public/models/info-de.json', 'w')","open('data43/info-de.json', 'w')")
stub={'parts':[{'id':p['id'],'conceptId':p['conceptId'],'name':p['english'],
                'system':json.load(open('data43/systems43.json'))['systems'].get(p['id'],'connective')} for p in parts],
      'concepts':[{'id':c['id'],'name':c['english'],'elements':[]} for c in cons]}
json.dump(stub, open('data43/atlas43_stub.json','w'))
with contextlib.redirect_stdout(io.StringIO()) as o: exec(src, ns)
print(o.getvalue().split('\n')[0])
