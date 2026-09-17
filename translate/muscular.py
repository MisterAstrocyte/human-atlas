import json, csv, re

atlas = json.load(open('public/models/atlas.json'))
terms = sorted(set(p['name'].lower() for p in atlas['parts'] if p['system'] == 'muscular'))

DE_SIDE = {'m':('Linker','Rechter'),'f':('Linke','Rechte'),'n':('Linkes','Rechtes')}
LA_SIDE = {'m':('sinister','dexter'),'f':('sinistra','dextra'),'n':('sinistrum','dextrum')}
ORD_DE = {'first':'Erster','second':'Zweiter','third':'Dritter','fourth':'Vierter'}
ORD_LA = {'first':'primus','second':'secundus','third':'tertius','fourth':'quartus'}

ADJ={'Kurzer','Langer','Großer','Kleiner','Kleinster','Unterer','Oberer','Äußerer','Innerer','Innerster','Tiefer','Oberflächlicher','Mittlerer','Seitlicher','Vorderer','Hinterer','Schräger','Gerader','Querer','Längster','Zweibäuchiger','Schlanker','Birnenförmiger','Viereckiger','Speichenseitiger','Ellenseitiger','Medialer','Runder'}
def lc(s):
    w=s.split(' ',1)
    return (w[0].lower()+(' '+w[1] if len(w)>1 else '')) if w[0] in ADJ else s
def cap(s): return s[0].upper()+s[1:]

# base -> (german, de_gender, latin, la_gender)
M = {
 'abductor hallucis':('Großzehenabzieher','m','Musculus abductor hallucis','m'),
 'abductor pollicis brevis':('Kurzer Daumenabzieher','m','Musculus abductor pollicis brevis','m'),
 'abductor pollicis longus':('Langer Daumenabzieher','m','Musculus abductor pollicis longus','m'),
 'adductor brevis':('Kurzer Schenkelanzieher','m','Musculus adductor brevis','m'),
 'adductor longus':('Langer Schenkelanzieher','m','Musculus adductor longus','m'),
 'adductor magnus':('Großer Schenkelanzieher','m','Musculus adductor magnus','m'),
 'adductor minimus':('Kleinster Schenkelanzieher','m','Musculus adductor minimus','m'),
 'anconeus':('Knorrenmuskel','m','Musculus anconeus','m'),
 'aryepiglotticus':('Stellknorpel-Kehldeckel-Muskel','m','Musculus aryepiglotticus','m'),
 'brachialis':('Armbeuger','m','Musculus brachialis','m'),
 'brachioradialis':('Oberarm-Speichen-Muskel','m','Musculus brachioradialis','m'),
 'cervical rotator':('Halsdrehmuskel','m','Musculus rotator cervicis','m'),
 'coccygeus':('Steißbeinmuskel','m','Musculus coccygeus','m'),
 'coracobrachialis':('Hakenarmmuskel','m','Musculus coracobrachialis','m'),
 'diaphragm':('Zwerchfell','n','Diaphragma','n'),
 'digastric':('Zweibäuchiger Muskel','m','Musculus digastricus','m'),
 'extensor carpi radialis brevis':('Kurzer speichenseitiger Handstrecker','m','Musculus extensor carpi radialis brevis','m'),
 'extensor carpi radialis longus':('Langer speichenseitiger Handstrecker','m','Musculus extensor carpi radialis longus','m'),
 'extensor carpi ulnaris':('Ellenseitiger Handstrecker','m','Musculus extensor carpi ulnaris','m'),
 'extensor digiti minimi':('Kleinfingerstrecker','m','Musculus extensor digiti minimi','m'),
 'extensor digitorum':('Fingerstrecker','m','Musculus extensor digitorum','m'),
 'extensor digitorum longus':('Langer Zehenstrecker','m','Musculus extensor digitorum longus','m'),
 'extensor hallucis brevis':('Kurzer Großzehenstrecker','m','Musculus extensor hallucis brevis','m'),
 'extensor hallucis longus':('Langer Großzehenstrecker','m','Musculus extensor hallucis longus','m'),
 'extensor indicis':('Zeigefingerstrecker','m','Musculus extensor indicis','m'),
 'extensor pollicis brevis':('Kurzer Daumenstrecker','m','Musculus extensor pollicis brevis','m'),
 'extensor pollicis longus':('Langer Daumenstrecker','m','Musculus extensor pollicis longus','m'),
 'external anal sphincter':('Äußerer Afterschließmuskel','m','Musculus sphincter ani externus','m'),
 'external intercostal muscle':('Äußerer Zwischenrippenmuskel','m','Musculus intercostalis externus','m'),
 'external oblique':('Äußerer schräger Bauchmuskel','m','Musculus obliquus externus abdominis','m'),
 'flexor accessorius':('Viereckiger Sohlenmuskel','m','Musculus quadratus plantae','m'),
 'flexor carpi radialis':('Speichenseitiger Handbeuger','m','Musculus flexor carpi radialis','m'),
 'flexor digitorum brevis':('Kurzer Zehenbeuger','m','Musculus flexor digitorum brevis','m'),
 'flexor digitorum longus':('Langer Zehenbeuger','m','Musculus flexor digitorum longus','m'),
 'flexor digitorum profundus':('Tiefer Fingerbeuger','m','Musculus flexor digitorum profundus','m'),
 'flexor digitorum superficialis':('Oberflächlicher Fingerbeuger','m','Musculus flexor digitorum superficialis','m'),
 'flexor hallucis longus':('Langer Großzehenbeuger','m','Musculus flexor hallucis longus','m'),
 'flexor pollicis brevis':('Kurzer Daumenbeuger','m','Musculus flexor pollicis brevis','m'),
 'flexor pollicis longus':('Langer Daumenbeuger','m','Musculus flexor pollicis longus','m'),
 'gemellus inferior':('Unterer Zwillingsmuskel','m','Musculus gemellus inferior','m'),
 'gemellus superior':('Oberer Zwillingsmuskel','m','Musculus gemellus superior','m'),
 'genioglossus':('Kinn-Zungen-Muskel','m','Musculus genioglossus','m'),
 'geniohyoid':('Kinn-Zungenbein-Muskel','m','Musculus geniohyoideus','m'),
 'gluteus maximus':('Großer Gesäßmuskel','m','Musculus gluteus maximus','m'),
 'gluteus medius':('Mittlerer Gesäßmuskel','m','Musculus gluteus medius','m'),
 'gluteus minimus':('Kleiner Gesäßmuskel','m','Musculus gluteus minimus','m'),
 'gracilis':('Schlanker Muskel','m','Musculus gracilis','m'),
 'hyoglossus':('Zungenbein-Zungen-Muskel','m','Musculus hyoglossus','m'),
 'iliacus':('Darmbeinmuskel','m','Musculus iliacus','m'),
 'iliococcygeus':('Darmbein-Steißbein-Muskel','m','Musculus iliococcygeus','m'),
 'iliocostalis cervicis':('Darmbein-Rippen-Muskel des Halses','m','Musculus iliocostalis cervicis','m'),
 'iliocostalis lumborum':('Darmbein-Rippen-Muskel der Lende','m','Musculus iliocostalis lumborum','m'),
 'iliocostalis thoracis':('Darmbein-Rippen-Muskel des Brustkorbs','m','Musculus iliocostalis thoracis','m'),
 'inferior oblique':('Unterer schräger Augenmuskel','m','Musculus obliquus inferior','m'),
 'inferior rectus':('Unterer gerader Augenmuskel','m','Musculus rectus inferior','m'),
 'infraspinatus muscle':('Untergrätenmuskel','m','Musculus infraspinatus','m'),
 'innermost intercostal muscle':('Innerster Zwischenrippenmuskel','m','Musculus intercostalis intimus','m'),
 'internal intercostal muscle':('Innerer Zwischenrippenmuskel','m','Musculus intercostalis internus','m'),
 'interspinalis thoracis':('Zwischendornmuskel des Brustkorbs','m','Musculus interspinalis thoracis','m'),
 'lateral crico-arytenoid':('Seitlicher Ringknorpel-Stellknorpel-Muskel','m','Musculus cricoarytenoideus lateralis','m'),
 'lateral lumbar intertransversarius':('Seitlicher Zwischenquerfortsatzmuskel der Lende','m','Musculus intertransversarius lateralis lumborum','m'),
 'lateral rectus':('Seitlicher gerader Augenmuskel','m','Musculus rectus lateralis','m'),
 'levator palpebrae superioris':('Oberlidheber','m','Musculus levator palpebrae superioris','m'),
 'levator veli palatini':('Gaumensegelheber','m','Musculus levator veli palatini','m'),
 'longissimus capitis':('Längster Muskel des Kopfes','m','Musculus longissimus capitis','m'),
 'longissimus cervicis':('Längster Muskel des Halses','m','Musculus longissimus cervicis','m'),
 'longissimus thoracis':('Längster Muskel des Brustkorbs','m','Musculus longissimus thoracis','m'),
 'longus capitis':('Langer Kopfmuskel','m','Musculus longus capitis','m'),
 'lumbar rotator':('Lendendrehmuskel','m','Musculus rotator lumborum','m'),
 'medial lumbar intertransversarius':('Medialer Zwischenquerfortsatzmuskel der Lende','m','Musculus intertransversarius medialis lumborum','m'),
 'medial rectus':('Innerer gerader Augenmuskel','m','Musculus rectus medialis','m'),
 'mylohyoid':('Kiefer-Zungenbein-Muskel','m','Musculus mylohyoideus','m'),
 'oblique arytenoid':('Schräger Stellknorpelmuskel','m','Musculus arytenoideus obliquus','m'),
 'obliquus capitis inferior':('Unterer schräger Kopfmuskel','m','Musculus obliquus capitis inferior','m'),
 'obliquus capitis superior':('Oberer schräger Kopfmuskel','m','Musculus obliquus capitis superior','m'),
 'obturator externus':('Äußerer Hüftlochmuskel','m','Musculus obturatorius externus','m'),
 'obturator internus':('Innerer Hüftlochmuskel','m','Musculus obturatorius internus','m'),
 'omohyoid':('Schulterblatt-Zungenbein-Muskel','m','Musculus omohyoideus','m'),
 'opponens pollicis':('Daumengegensteller','m','Musculus opponens pollicis','m'),
 'palmaris longus':('Langer Hohlhandmuskel','m','Musculus palmaris longus','m'),
 'pectineus':('Kammmuskel','m','Musculus pectineus','m'),
 'pectoralis minor':('Kleiner Brustmuskel','m','Musculus pectoralis minor','m'),
 'piriformis':('Birnenförmiger Muskel','m','Musculus piriformis','m'),
 'plantaris':('Langer Sohlenmuskel','m','Musculus plantaris','m'),
 'platysma':('Hautmuskel des Halses','m','Platysma','n'),
 'popliteus':('Kniekehlenmuskel','m','Musculus popliteus','m'),
 'posterior crico-arytenoid':('Hinterer Ringknorpel-Stellknorpel-Muskel','m','Musculus cricoarytenoideus posterior','m'),
 'pronator quadratus':('Viereckiger Einwärtsdreher','m','Musculus pronator quadratus','m'),
 'psoas major':('Großer Lendenmuskel','m','Musculus psoas major','m'),
 'pubococcygeus':('Schambein-Steißbein-Muskel','m','Musculus pubococcygeus','m'),
 'puborectalis':('Schambein-Mastdarm-Muskel','m','Musculus puborectalis','m'),
 'quadratus femoris':('Viereckiger Schenkelmuskel','m','Musculus quadratus femoris','m'),
 'rectus capitis anterior':('Vorderer gerader Kopfmuskel','m','Musculus rectus capitis anterior','m'),
 'rectus capitis lateralis':('Seitlicher gerader Kopfmuskel','m','Musculus rectus capitis lateralis','m'),
 'rectus capitis posterior major':('Großer hinterer gerader Kopfmuskel','m','Musculus rectus capitis posterior major','m'),
 'rectus capitis posterior minor':('Kleiner hinterer gerader Kopfmuskel','m','Musculus rectus capitis posterior minor','m'),
 'rectus femoris':('Gerader Schenkelmuskel','m','Musculus rectus femoris','m'),
 'rhomboid major':('Großer Rautenmuskel','m','Musculus rhomboideus major','m'),
 'rhomboid minor':('Kleiner Rautenmuskel','m','Musculus rhomboideus minor','m'),
 'sartorius':('Schneidermuskel','m','Musculus sartorius','m'),
 'scalenus anterior':('Vorderer Treppenmuskel','m','Musculus scalenus anterior','m'),
 'scalenus medius':('Mittlerer Treppenmuskel','m','Musculus scalenus medius','m'),
 'scalenus posterior':('Hinterer Treppenmuskel','m','Musculus scalenus posterior','m'),
 'semimembranosus':('Plattsehnenmuskel','m','Musculus semimembranosus','m'),
 'semispinalis capitis':('Halbdornmuskel des Kopfes','m','Musculus semispinalis capitis','m'),
 'semispinalis cervicis':('Halbdornmuskel des Halses','m','Musculus semispinalis cervicis','m'),
 'semispinalis thoracis':('Halbdornmuskel des Brustkorbs','m','Musculus semispinalis thoracis','m'),
 'semitendinosus':('Halbsehnenmuskel','m','Musculus semitendinosus','m'),
 'serratus anterior':('Vorderer Sägemuskel','m','Musculus serratus anterior','m'),
 'serratus posterior inferior':('Hinterer unterer Sägemuskel','m','Musculus serratus posterior inferior','m'),
 'serratus posterior superior':('Hinterer oberer Sägemuskel','m','Musculus serratus posterior superior','m'),
 'soleus':('Schollenmuskel','m','Musculus soleus','m'),
 'spinalis':('Dornmuskel','m','Musculus spinalis','m'),
 'spinalis thoracis':('Dornmuskel des Brustkorbs','m','Musculus spinalis thoracis','m'),
 'splenius capitis':('Riemenmuskel des Kopfes','m','Musculus splenius capitis','m'),
 'splenius cervicis':('Riemenmuskel des Halses','m','Musculus splenius cervicis','m'),
 'sternocleidomastoid':('Kopfwender','m','Musculus sternocleidomastoideus','m'),
 'sternohyoid':('Brustbein-Zungenbein-Muskel','m','Musculus sternohyoideus','m'),
 'sternothyroid':('Brustbein-Schildknorpel-Muskel','m','Musculus sternothyroideus','m'),
 'stylohyoid':('Griffel-Zungenbein-Muskel','m','Musculus stylohyoideus','m'),
 'subclavius':('Unterschlüsselbeinmuskel','m','Musculus subclavius','m'),
 'superficial perineal muscle':('Oberflächlicher querer Dammmuskel','m','Musculus transversus perinei superficialis','m'),
 'superior oblique':('Oberer schräger Augenmuskel','m','Musculus obliquus superior','m'),
 'superior rectus':('Oberer gerader Augenmuskel','m','Musculus rectus superior','m'),
 'supinator':('Auswärtsdreher','m','Musculus supinator','m'),
 'supraspinatus':('Obergrätenmuskel','m','Musculus supraspinatus','m'),
 'tensor veli palatini':('Gaumensegelspanner','m','Musculus tensor veli palatini','m'),
 'teres major':('Großer Rundmuskel','m','Musculus teres major','m'),
 'teres minor':('Kleiner Rundmuskel','m','Musculus teres minor','m'),
 'thoracic rotator':('Brustdrehmuskel','m','Musculus rotator thoracis','m'),
 'thyro-arytenoid':('Schildknorpel-Stellknorpel-Muskel','m','Musculus thyroarytenoideus','m'),
 'thyrohyoid':('Schildknorpel-Zungenbein-Muskel','m','Musculus thyrohyoideus','m'),
 'transverse arytenoid':('Querer Stellknorpelmuskel','m','Musculus arytenoideus transversus','m'),
 'transversus thoracis':('Querer Brustkorbmuskel','m','Musculus transversus thoracis','m'),
 'uvular muscle':('Zäpfchenmuskel','m','Musculus uvulae','m'),
 'vastus intermedius':('Mittlerer breiter Schenkelmuskel','m','Musculus vastus intermedius','m'),
 'vastus lateralis':('Äußerer breiter Schenkelmuskel','m','Musculus vastus lateralis','m'),
 'vastus medialis':('Innerer breiter Schenkelmuskel','m','Musculus vastus medialis','m'),
 'vocalis':('Stimmmuskel','m','Musculus vocalis','m'),
}
# muscles that appear as owners of parts/heads: base -> (de_gen after "des linken", la_gen after "musculi")
OWN = {
 'pectoralis major':('großen Brustmuskels','pectoralis majoris'),
 'deltoid':('Deltamuskels','deltoidei'),
 'trapezius':('Trapezmuskels','trapezii'),
 'flexor carpi ulnaris':('ellenseitigen Handbeugers','flexoris carpi ulnaris'),
 'pronator teres':('runden Einwärtsdrehers','pronatoris teretis'),
 'longus colli':('langen Halsmuskels','longi colli'),
 'flexor hallucis brevis':('kurzen Großzehenbeugers','flexoris hallucis brevis'),
 'gastrocnemius':('Zwillingswadenmuskels','gastrocnemii'),
 'triceps brachii':('dreiköpfigen Oberarmmuskels','tricipitis brachii'),
 'biceps brachii':('zweiköpfigen Oberarmmuskels','bicipitis brachii'),
 'biceps femoris':('zweiköpfigen Schenkelmuskels','bicipitis femoris'),
 'adductor hallucis':('Großzehenanziehers','adductoris hallucis'),
 'adductor pollicis':('Daumenanziehers','adductoris pollicis'),
 'cricothyroid':('Ringknorpel-Schildknorpel-Muskels','cricothyroidei'),
 'flexor pollicis brevis':('kurzen Daumenbeugers','flexoris pollicis brevis'),
}
PART = {
 'abdominal':('Bauchanteil','Pars abdominalis'), 'acromial':('Schulterhöhenanteil','Pars acromialis'),
 'clavicular':('Schlüsselbeinanteil','Pars clavicularis'), 'spinal':('Grätenanteil','Pars spinalis'),
 'sternocostal':('Brustbein-Rippen-Anteil','Pars sternocostalis'), 'ascending':('Aufsteigender Anteil','Pars ascendens'),
 'descending':('Absteigender Anteil','Pars descendens'), 'transverse':('Querer Anteil','Pars transversa'),
 'oblique':('Schräger Anteil','Pars obliqua'), 'straight':('Gerader Anteil','Pars recta'),
 'inferior oblique':('Unterer schräger Anteil','Pars obliqua inferior'),
 'superior oblique':('Oberer schräger Anteil','Pars obliqua superior'),
 'vertical intermediate':('Senkrechter mittlerer Anteil','Pars verticalis intermedia'),
}
HEAD = {
 'humeral':('Oberarmkopf','Caput humerale'), 'ulnar':('Ellenkopf','Caput ulnare'),
 'lateral':('Seitlicher Kopf','Caput laterale'), 'medial':('Medialer Kopf','Caput mediale'),
 'long':('Langer Kopf','Caput longum'), 'short':('Kurzer Kopf','Caput breve'),
 'oblique':('Schräger Kopf','Caput obliquum'), 'transverse':('Querer Kopf','Caput transversum'),
 'superficial':('Oberflächlicher Kopf','Caput superficiale'),
}
# hand/foot muscles: base -> ((de foot, de hand), la base)
HF = {
 'abductor digiti minimi':(('Kleinzehenabzieher','Kleinfingerabzieher'),'Musculus abductor digiti minimi'),
 'flexor digiti minimi brevis':(('Kurzer Kleinzehenbeuger','Kurzer Kleinfingerbeuger'),'Musculus flexor digiti minimi brevis'),
 'opponens digiti minimi':(('Kleinzehengegensteller','Kleinfingergegensteller'),'Musculus opponens digiti minimi'),
}
SETS = {
 'set of anterior cervical intertransversarii':('Vordere Zwischenquerfortsatzmuskeln des Halses','Musculi intertransversarii anteriores cervicis'),
 'set of posterior cervical intertransversarii':('Hintere Zwischenquerfortsatzmuskeln des Halses','Musculi intertransversarii posteriores cervicis'),
 'set of interspinales cervicis':('Zwischendornmuskeln des Halses','Musculi interspinales cervicis'),
 'set of interspinales lumborum':('Zwischendornmuskeln der Lende','Musculi interspinales lumborum'),
}
SETS_HAND = {
 'dorsal interossei':('Rückseitige Zwischenknochenmuskeln','Musculi interossei dorsales'),
 'palmar interossei':('Hohlhandseitige Zwischenknochenmuskeln','Musculi interossei palmares'),
 'lumbricals':('Spulmuskeln','Musculi lumbricales'),
}
CARDIAC = {
 'anterior papillary muscle of right ventricle':('Vorderer Papillarmuskel der rechten Herzkammer','Musculus papillaris anterior ventriculi dextri'),
 'posterior papillary muscle of right ventricle':('Hinterer Papillarmuskel der rechten Herzkammer','Musculus papillaris posterior ventriculi dextri'),
 'septal papillary muscle of right ventricle':('Septaler Papillarmuskel der rechten Herzkammer','Musculus papillaris septalis ventriculi dextri'),
 'lateral papillary muscle of left ventricle':('Seitlicher Papillarmuskel der linken Herzkammer','Musculus papillaris lateralis ventriculi sinistri'),
 'anterolateral head of lateral papillary muscle of left ventricle':('Vorderer seitlicher Kopf des seitlichen Papillarmuskels der linken Herzkammer','Caput anterolaterale musculi papillaris lateralis ventriculi sinistri'),
}

def side_idx(w): return 0 if w=='left' else 1
DEG = ('linken','rechten'); LAG = ('sinistri','dextri'); LAGF = ('sinistrae','dextrae')

def translate(t):
    if t in CARDIAC: return CARDIAC[t]
    if t in SETS: return SETS[t]
    if t in M:
        de,dg,la,lg = M[t]; return (de, la)
    m = re.match(r'^(left|right) (.+)$', t)
    if m and m.group(2) in M:
        s = side_idx(m.group(1)); de,dg,la,lg = M[m.group(2)]
        return (f'{DE_SIDE[dg][s]} {lc(de)}', f'{la} {LA_SIDE[lg][s]}')
    m = re.match(r'^(.+) part of (left|right) (.+)$', t)
    if m and m.group(1) in PART and m.group(3) in OWN:
        s = side_idx(m.group(2)); pde,pla = PART[m.group(1)]; ode,ola = OWN[m.group(3)]
        return (f'{pde} des {DEG[s]} {ode}', f'{pla} musculi {ola} {LAG[s]}')
    m = re.match(r'^(.+) head of (left|right) (.+)$', t)
    if m and m.group(1) in HEAD and m.group(3) in OWN:
        s = side_idx(m.group(2)); hde,hla = HEAD[m.group(1)]; ode,ola = OWN[m.group(3)]
        return (f'{hde} des {DEG[s]} {ode}', f'{hla} musculi {ola} {LAG[s]}')
    m = re.match(r'^(.+) of (left|right) (foot|hand)$', t)
    if m:
        s = side_idx(m.group(2)); foot = m.group(3)=='foot'
        de_loc = f'des {DEG[s]} Fußes' if foot else f'der {DEG[s]} Hand'
        la_loc = f'pedis {LAG[s]}' if foot else f'manus {LAGF[s]}'
        base = m.group(1)
        if base in HF:
            (df,dh),la = HF[base]; return (f'{df if foot else dh} {de_loc}', f'{la} {la_loc}')
        m2 = re.match(r'^(first|second|third|fourth) lumbrical$', base)
        if m2: return (f'{ORD_DE[m2.group(1)]} Spulmuskel {de_loc}', f'Musculus lumbricalis {ORD_LA[m2.group(1)]} {la_loc}')
        m2 = re.match(r'^(first|second|third|fourth) plantar interosseous$', base)
        if m2: return (f'{ORD_DE[m2.group(1)]} Sohlenzwischenknochenmuskel {de_loc}', f'Musculus interosseus plantaris {ORD_LA[m2.group(1)]} {la_loc}')
        m2 = re.match(r'^set of (.+)$', base)
        if m2 and m2.group(1) in SETS_HAND:
            de,la = SETS_HAND[m2.group(1)]; return (f'{de} {de_loc}', f'{la} {la_loc}')
    m = re.match(r'^set of (left|right) levatores costarum (breves|longi)$', t)
    if m:
        s = side_idx(m.group(1)); short = m.group(2)=='breves'
        return (f'{("Linke","Rechte")[s]} {"kurze" if short else "lange"} Rippenheber', f'Musculi levatores costarum {m.group(2)} {LAG[s]}')
    return None

rows, missing = [], []
for t in terms:
    r = translate(t)
    if r is None: missing.append(t); continue
    rows.append({'english': t, 'german': r[0], 'latin': r[1], 'system': 'muscular'})
print(len(rows), 'translated;', len(missing), 'missing', missing)
with open('translate/atlas-de-muscular.csv','w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=['english','german','latin','system']); w.writeheader(); w.writerows(rows)
json.dump(rows, open('translate/atlas-de-muscular.json','w'), ensure_ascii=False, indent=1)
with open('translate/atlas-de-muscular.md','w') as f:
    f.write('# Human Atlas – Muskelsystem (Deutsch / Latein)\n\n| English | Deutsch (Latein) |\n|---|---|\n')
    for r in rows: f.write(f"| {r['english']} | {r['german']} ({r['latin']}) |\n")
