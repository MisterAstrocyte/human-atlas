import json, csv, re, sys

atlas = json.load(open('public/models/atlas.json'))
terms = sorted(set(p['name'].lower() for p in atlas['parts'] if p['system'] == 'skeletal'))

# ---------- vocab ----------
# German ordinal stems + endings, Latin ordinals (m/f/n) + fem genitive
ORD = {
 'first':('erst','primus','prima','primum','primae'), 'second':('zweit','secundus','secunda','secundum','secundae'),
 'third':('dritt','tertius','tertia','tertium','tertiae'), 'fourth':('viert','quartus','quarta','quartum','quartae'),
 'fifth':('fünft','quintus','quinta','quintum','quintae'), 'sixth':('sechst','sextus','sexta','sextum','sextae'),
 'seventh':('siebt','septimus','septima','septimum','septimae'), 'eighth':('acht','octavus','octava','octavum','octavae'),
 'ninth':('neunt','nonus','nona','nonum','nonae'), 'tenth':('zehnt','decimus','decima','decimum','decimae'),
 'eleventh':('elft','undecimus','undecima','undecimum','undecimae'), 'twelfth':('zwölft','duodecimus','duodecima','duodecimum','duodecimae'),
}
DE_END = {'m':'er','f':'e','n':'es'}
LA_SIDE = {'m':('sinister','dexter'),'f':('sinistra','dextra'),'n':('sinistrum','dextrum')}
DE_SIDE = {'m':('linker','rechter'),'f':('linke','rechte'),'n':('linkes','rechtes')}

# paired bones: english -> (german, de_gender, latin, la_gender)
PAIRED = {
 'arytenoid cartilage':('Stellknorpel','m','Cartilago arytenoidea','f'),
 'calcaneus':('Fersenbein','n','Calcaneus','m'),
 'capitate':('Kopfbein','n','Os capitatum','n'),
 'clavicle':('Schlüsselbein','n','Clavicula','f'),
 'corniculate cartilage':('Spitzenknorpel','m','Cartilago corniculata','f'),
 'cuboid bone':('Würfelbein','n','Os cuboideum','n'),
 'cuneiform cartilage':('Keilknorpel des Kehlkopfs','m','Cartilago cuneiformis','f'),
 'femur':('Oberschenkelknochen','m','Femur','n'),
 'fibula':('Wadenbein','n','Fibula','f'),
 'fibularis brevis':('Kurzer Wadenbeinmuskel','m','Musculus fibularis brevis','m'),
 'fibularis longus':('Langer Wadenbeinmuskel','m','Musculus fibularis longus','m'),
 'fibularis tertius':('Dritter Wadenbeinmuskel','m','Musculus fibularis tertius','m'),
 'hamate':('Hakenbein','n','Os hamatum','n'),
 'hip bone':('Hüftbein','n','Os coxae','n'),
 'humerus':('Oberarmknochen','m','Humerus','m'),
 'iliotibial tract':('Iliotibialtrakt','m','Tractus iliotibialis','m'),
 'intermediate cuneiform bone':('Mittleres Keilbein','n','Os cuneiforme intermedium','n'),
 'lateral cuneiform bone':('Äußeres Keilbein','n','Os cuneiforme laterale','n'),
 'medial cuneiform bone':('Inneres Keilbein','n','Os cuneiforme mediale','n'),
 'levator scapulae':('Schulterblattheber','m','Musculus levator scapulae','m'),
 'lunate':('Mondbein','n','Os lunatum','n'),
 'major alar cartilage':('Großer Flügelknorpel','m','Cartilago alaris major','f'),
 'maxilla':('Oberkiefer','m','Maxilla','f'),
 'nasal bone':('Nasenbein','n','Os nasale','n'),
 'palatine bone':('Gaumenbein','n','Os palatinum','n'),
 'parietal bone':('Scheitelbein','n','Os parietale','n'),
 'patella':('Kniescheibe','f','Patella','f'),
 'pisiform':('Erbsenbein','n','Os pisiforme','n'),
 'radius':('Speiche','f','Radius','m'),
 'scaphoid':('Kahnbein','n','Os scaphoideum','n'),
 'scapula':('Schulterblatt','n','Scapula','f'),
 'subscapularis':('Unterschulterblattmuskel','m','Musculus subscapularis','m'),
 'talus':('Sprungbein','n','Talus','m'),
 'temporal bone':('Schläfenbein','n','Os temporale','n'),
 'tibia':('Schienbein','n','Tibia','f'),
 'tibialis anterior':('Vorderer Schienbeinmuskel','m','Musculus tibialis anterior','m'),
 'tibialis posterior':('Hinterer Schienbeinmuskel','m','Musculus tibialis posterior','m'),
 'trapezium':('Großes Vieleckbein','n','Os trapezium','n'),
 'trapezoid':('Kleines Vieleckbein','n','Os trapezoideum','n'),
 'triquetral':('Dreiecksbein','n','Os triquetrum','n'),
 'ulna':('Elle','f','Ulna','f'),
 'zygomatic bone':('Jochbein','n','Os zygomaticum','n'),
}
SINGLE = {
 'atlas':('Atlas','Atlas'), 'axis':('Axis','Axis'),
 'body of sternum':('Brustbeinkörper','Corpus sterni'),
 'cricoid cartilage':('Ringknorpel','Cartilago cricoidea'),
 'ethmoid':('Siebbein','Os ethmoidale'), 'frontal bone':('Stirnbein','Os frontale'),
 'gingiva of lower jaw':('Zahnfleisch des Unterkiefers','Gingiva mandibularis'),
 'gingiva of upper jaw':('Zahnfleisch des Oberkiefers','Gingiva maxillaris'),
 'hyoid bone':('Zungenbein','Os hyoideum'),
 'intervertebral disk':('Bandscheibe','Discus intervertebralis'),
 'intervertebral disk of axis':('Bandscheibe des Axis','Discus intervertebralis axis'),
 'mandible':('Unterkiefer','Mandibula'), 'manubrium':('Brustbeingriff','Manubrium sterni'),
 'occipital bone':('Hinterhauptbein','Os occipitale'), 'sacrum':('Kreuzbein','Os sacrum'),
 'sphenoid bone':('Keilbein','Os sphenoidale'), 'thyroid cartilage':('Schildknorpel','Cartilago thyroidea'),
 'vomer':('Pflugscharbein','Vomer'), 'xiphoid process':('Schwertfortsatz','Processus xiphoideus'),
 'navicular bone of left foot':('Kahnbein des linken Fußes','Os naviculare pedis sinistri'),
 'navicular bone of right foot':('Kahnbein des rechten Fußes','Os naviculare pedis dextri'),
 'sesamoid bone of left foot':('Sesambein des linken Fußes','Os sesamoideum pedis sinistri'),
 'sesamoid bone of right foot':('Sesambein des rechten Fußes','Os sesamoideum pedis dextri'),
}
# ordinal-numbered paired items: (german noun, de_gender, latin noun, la_gender)
NUMBERED = {
 'rib':('Rippe','f','Costa','f'),
 'costal cartilage':('Rippenknorpel','m','Cartilago costalis','f'),
 'metacarpal bone':('Mittelhandknochen','m','Os metacarpale','n'),
 'metatarsal bone':('Mittelfußknochen','m','Os metatarsale','n'),
}
VERT = {'cervical':('Halswirbel','cervicalis'),'thoracic':('Brustwirbel','thoracica'),'lumbar':('Lendenwirbel','lumbalis')}
PHAL = {'distal':('Endphalanx','Phalanx distalis'),'middle':('Mittelphalanx','Phalanx media'),'proximal':('Grundphalanx','Phalanx proximalis')}
# digits: german genitive phrase after "des/der linken", german gender, latin genitive
DIGIT = {
 'thumb':('Daumens','m','pollicis'), 'index finger':('Zeigefingers','m','indicis'),
 'middle finger':('Mittelfingers','m','digiti medii'), 'ring finger':('Ringfingers','m','digiti anularis'),
 'little finger':('Kleinfingers','m','digiti minimi manus'),
 'big toe':('Großzehe','f','hallucis'), 'second toe':('zweiten Zehe','f','digiti secundi pedis'),
 'third toe':('dritten Zehe','f','digiti tertii pedis'), 'fourth toe':('vierten Zehe','f','digiti quarti pedis'),
 'little toe':('Kleinzehe','f','digiti minimi pedis'),
}
TOOTH = {
 'central secondary incisor':('mittlerer Schneidezahn','Dens incisivus medialis'),
 'lateral secondary incisor':('seitlicher Schneidezahn','Dens incisivus lateralis'),
 'secondary canine':('Eckzahn','Dens caninus'),
 'first secondary premolar':('erster Prämolar','Dens premolaris primus'),
 'second secondary premolar':('zweiter Prämolar','Dens premolaris secundus'),
 'first secondary molar':('erster Molar','Dens molaris primus'),
 'second secondary molar':('zweiter Molar','Dens molaris secundus'),
}

def cap(s): return s[0].upper()+s[1:]

def translate(t):
    if t in SINGLE: return SINGLE[t]
    m = re.match(r'^(left|right) (.+)$', t)
    if m:
        side = 0 if m.group(1)=='left' else 1
        rest = m.group(2)
        if rest in PAIRED:
            de,dg,la,lg = PAIRED[rest]
            return (f'{cap(DE_SIDE[dg][side])} {de[0].lower()+de[1:] if de.split()[0] in ("Großer","Kurzer","Langer","Dritter","Vorderer","Hinterer","Mittleres","Äußeres","Inneres","Großes","Kleines") else de}', f'{la} {LA_SIDE[lg][side]}')
        m2 = re.match(r'^(\w+) (.+)$', rest)
        if m2 and m2.group(1) in ORD and m2.group(2) in NUMBERED:
            o = ORD[m2.group(1)]; de,dg,la,lg = NUMBERED[m2.group(2)]
            la_ord = {'m':o[1],'f':o[2],'n':o[3]}[lg]
            return (f'{cap(DE_SIDE[dg][side])} {o[0]}{DE_END[dg]} {de}', f'{la} {la_ord} {LA_SIDE[lg][side]}')
        m3 = re.match(r'^(upper|lower) (.+) tooth$', rest)
        if m3 and m3.group(2) in TOOTH:
            de,la = TOOTH[m3.group(2)]
            pos_de = 'oberer' if m3.group(1)=='upper' else 'unterer'
            pos_la = 'superior' if m3.group(1)=='upper' else 'inferior'
            return (f'{cap(DE_SIDE["m"][side])} {pos_de} {de}', f'{la} {pos_la} {LA_SIDE["m"][side]}')
    m = re.match(r'^(distal|middle|proximal) phalanx of (left|right) (.+)$', t)
    if m:
        pde,pla = PHAL[m.group(1)]; side = 0 if m.group(2)=='left' else 1
        gde,gg,gla = DIGIT[m.group(3)]
        art = 'des' if gg=='m' else 'der'
        return (f'{pde} {art} {["linken","rechten"][side]} {gde}', f'{pla} {gla} {["sinistri","dextri"][side]}')
    m = re.match(r'^(\w+) (cervical|thoracic|lumbar) vertebra$', t)
    if m:
        o = ORD[m.group(1)]; de,la = VERT[m.group(2)]
        return (f'{cap(o[0])}er {de}', f'Vertebra {la} {o[2]}')
    m = re.match(r'^intervertebral disk of (\w+) (cervical|thoracic|lumbar) vertebra$', t)
    if m:
        o = ORD[m.group(1)]; de,la = VERT[m.group(2)]
        return (f'Bandscheibe des {o[0]}en {de}s', f'Discus intervertebralis vertebrae {la.replace("thoracica","thoracicae")} {o[4]}')
    return None

rows = []
missing = []
for t in terms:
    r = translate(t)
    if r is None: missing.append(t); continue
    rows.append({'english': t, 'german': r[0], 'latin': r[1], 'system': 'skeletal'})
print(len(rows), 'translated;', len(missing), 'missing', missing)
with open('translate/atlas-de-skeletal.csv','w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=['english','german','latin','system']); w.writeheader(); w.writerows(rows)
json.dump(rows, open('translate/atlas-de-skeletal.json','w'), ensure_ascii=False, indent=1)
with open('translate/atlas-de-skeletal.md','w') as f:
    f.write('# Human Atlas – Skelettsystem (Deutsch / Latein)\n\n| English | Deutsch (Latein) |\n|---|---|\n')
    for r in rows: f.write(f"| {r['english']} | {r['german']} ({r['latin']}) |\n")
