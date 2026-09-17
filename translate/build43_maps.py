"""Build concepts43.json + systems43.json for scripts/convert-anatomy.py from the
official BodyParts3D 4.3 metadata (FMA2Obj.txt + obj2FMA.html + MANIFEST.csv)."""
import csv, json, re, sys, html
from pathlib import Path

src = Path(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/bp43')
out = Path(sys.argv[2] if len(sys.argv) > 2 else '/home/claude/human-atlas/data43')
out.mkdir(parents=True, exist_ok=True)

# ---- FJ -> mesh name, primary FMA ----
rows = list(csv.DictReader(open(src / 'MANIFEST.csv')))
mesh = {}
for r in rows:
    mesh.setdefault(r['fj_id'], {'name': r['name'].strip(), 'fma': r['fma_id']})
print('meshes', len(mesh))

# ---- FMA -> English name (from obj2FMA.html) ----
page = open(src / 'metadata/obj2FMA.html', encoding='utf-8', errors='replace').read()
fma_name = {}
fj_name = {}
for tr in re.findall(r'<tr>(.*?)</tr>', page, re.S):
    tds = [html.unescape(re.sub(r'<.*?>', '', t)).strip()
           for t in re.findall(r'<td class="[^"]*">(.*?)</td>', tr, re.S)]
    if len(tds) < 5: continue
    fj, fma, name = tds[1], tds[3], tds[4]
    if fma and name: fma_name.setdefault('FMA' + fma.replace('FMA', ''), name)
    if fj and name: fj_name.setdefault(fj, name)
# merge FMA names already curated in the shipped 4.0 atlas
try:
    old = json.load(open(Path(__file__).resolve().parents[1] / 'public/models/atlas.json'))
    for c in old['concepts']: fma_name.setdefault(c['id'], c['name'])
    for pt in old['parts']: fj_name.setdefault(pt['id'], pt['name'])
except Exception as e: print('no 4.0 atlas to merge:', e)
print('FMA names', len(fma_name))

# ---- FMA -> components (the authoritative 4.3 object set) ----
concepts = {}
for line in open(src / 'metadata/FMA2Obj.txt', encoding='utf-8', errors='replace'):
    line = line.strip().replace('\r', '')
    if not line or line.startswith('#'): continue
    parts = line.split('\t')
    if len(parts) < 3: continue
    fma, _, comps = parts[0], parts[1], parts[2]
    els = [c for c in comps.split('+') if c in mesh]
    if els: concepts[fma] = els
print('FMA concepts with geometry', len(concepts))

# ---- systems: classify each mesh by name ----
RULES = [
 ('skeletal', r'\b(bone|skull|cranium|vertebra|rib\b|ribs|sternum|manubrium|xiphoid|sacrum|coccyx|clavicle|scapula|humerus|radius|ulna|femur|patella|tibia|fibula|talus|calcaneus|navicular|cuboid|cuneiform|hamate|capitate|lunate|pisiform|scaphoid|trapezium|trapezoid|triquetral|phalanx|metacarpal|metatarsal|maxilla|mandible|vomer|ethmoid|sphenoid|hyoid|atlas|axis|sesamoid|tooth|incisor|canine|molar|premolar|gingiva|intervertebral disk)'),
 ('muscular', r'\b(muscle|musculus|belly of|head of .*(muscle|biceps|triceps)|biceps|triceps|deltoid|trapezius|pectoralis|latissimus|rhomboid|serratus|oblique(?!.*artery)|transversus|rectus abdominis|psoas|iliacus|gluteus|piriformis|gemellus|obturator (internus|externus)|quadratus|sartorius|gracilis|adductor|vastus|semitendinosus|semimembranosus|gastrocnemius|soleus|plantaris|popliteus|tibialis|fibularis|peroneus|extensor|flexor|abductor|opponens|lumbrical|interosseous (muscle)?|supinator|pronator|brachialis|brachioradialis|anconeus|coracobrachialis|supraspinatus|infraspinatus|teres (major|minor)|subscapularis|sternocleidomastoid|scalenus|digastric|mylohyoid|geniohyoid|stylohyoid|omohyoid|sternohyoid|sternothyroid|thyrohyoid|genioglossus|hyoglossus|masseter|temporalis|pterygoid|orbicularis|zygomaticus|levator|depressor|risorius|buccinator|platysma|occipitofrontalis|splenius|longissimus|iliocostalis|spinalis|semispinalis|multifidus|rotator|interspinal|intertransvers|constrictor|cricothyroid|arytenoid|vocalis|thyroarytenoid|diaphragm|intercostal|coccygeus|puborectalis|pubococcygeus|iliococcygeus|sphincter|perineal muscle)'),
 ('arterial', r'\b(artery|arterial|arteries|aorta|aortic arch|truncus|trunk of .*artery|arcus palmaris|palmar arch|plantar arch|brachiocephalic trunk|celiac|coeliac trunk|costocervical|thyrocervical)'),
 ('venous',   r'\b(vein|venous|vena|sinus (sagittalis|rectus|transversus|sigmoideus|cavernosus)|coronary sinus|dural (venous )?sinus|jugular)'),
 ('nervous',  r'\b(nerve|nervous|ganglion|plexus|brain|cerebr|cerebell|cortex|gyrus|sulcus|thalamus|hypothalamus|hippocamp|amygdala|putamen|pallidus|caudate|corpus callosum|commissure|fornix|pons|medulla oblongata|midbrain|colliculus|peduncle|spinal cord|ventricle of brain|lateral ventricle|third ventricle|fourth ventricle|choroid plexus|dura|arachnoid|pia mater|tract|lemniscus|capsule (interna|externa)|insula|claustrum|septum pellucidum|mammillary|habenula|pineal|infundibulum|chiasm|optic|olfactory)'),
 ('respiratory', r'\b(bronch|trachea|lung|pulmonary segment|bronchopulmonary|larynx|laryngeal|epiglottis|nasal cavity|nose|concha|sinus (maxillaris|frontalis|sphenoidalis|ethmoidalis)|pharyn|alveol)'),
 ('digestive', r'\b(stomach|gaster|esophag|oesophag|duoden|jejun|ileum|ileal|cecum|caec|colon|rectum|anal canal|appendix|liver|hepat|biliary|bile|gallbladder|cystic duct|pancrea|tongue|lingual|salivary|parotid|submandibular gland|sublingual|palate|uvula|mesenter|mesocolon|omentum|peritone|taenia)'),
 ('urinary',  r'\b(kidney|renal(?!.* (artery|vein))|ureter|bladder|urethra|urinary)'),
 ('reproductive', r'\b(testis|testic|epididym|deferent|seminal|prostat|penis|cavernosum|spongiosum|scrotum|spermatic)'),
 ('endocrine', r'\b(adrenal|suprarenal(?!.* (artery|vein))|pituitary|hypophys|pineal body|thyroid gland|parathyroid)'),
 ('lymphatic', r'\b(spleen|splen(?!.* (artery|vein))|thymus|lymph|tonsil|thoracic duct)'),
 ('sensory',  r'\b(eye|eyeball|cornea|sclera|choroid(?!.* (artery|plexus))|iris|lens|retina|vitreous|ciliary|lacrimal|eyelid|palpebra|tarsal plate|ear|tympan|cochlea|vestibul|ossicle|malleus|incus|stapes|labyrinth)'),
 ('cardiac',  r'\b(heart|cardiac|atrium|atrial|ventricle of heart|myocard|endocard|pericard|valve|cusp|leaflet|papillary muscle|chordae|septum (interatriale|interventriculare))'),
 ('integumentary', r'\b(skin|cutis|epidermis|hair|nail|eyebrow|eyelash|lip\b|areola|nipple|integument)'),
 ('connective', r'\b(ligament|tendon|aponeurosis|fascia|membrane|cartilage|raphe|retinaculum|meniscus|labrum|capsule of joint|bursa|septum(?! pellucidum)|disc|disk)'),
]
def system(name):
    n = name.lower()
    for sys_id, pat in RULES:
        if re.search(pat, n): return sys_id
    return 'connective'

systems = {fj: system(m['name']) for fj, m in mesh.items()}
import collections
print(collections.Counter(systems.values()).most_common())

# ---- assemble ----
elements = [{'id': fj, 'name': fj_name.get(fj, m['name']), 'conceptId': 'FMA' + m['fma'].replace('FMA','')}
            for fj, m in sorted(mesh.items())]
concept_list = [{'id': f, 'name': fma_name.get(f, f), 'elements': els}
                for f, els in sorted(concepts.items()) if fma_name.get(f)]
named = sum(1 for c in concept_list)
json.dump({'version': 'BodyParts3D 4.3', 'elements': elements, 'concepts': concept_list},
          open(out / 'concepts43.json', 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump({'systems': systems}, open(out / 'systems43.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('elements', len(elements), 'concepts', named)
print('wrote', out / 'concepts43.json', out / 'systems43.json')
