import json, csv, re
atlas = json.load(open('public/models/atlas.json'))
DE_SIDE = {'m':('Linker','Rechter'),'f':('Linke','Rechte'),'n':('Linkes','Rechtes')}
LA_SIDE = {'m':('sinister','dexter'),'f':('sinistra','dextra'),'n':('sinistrum','dextrum')}
ADJ = {'Vorderer','Hinterer','Oberer','Unterer','Mittlerer','Seitlicher','Medialer','Langer','Kurzer','Innerer','Äußerer','Weiße','Vordere','Hintere','Obere','Untere','Mittlere','Seitliche','Mediale','Innere','Vorderes','Hinteres','Oberes','Unteres','Mittleres','Seitliches','Mediales','Inneres','Apikaler','Basaler','Spindelförmiger','Graue','Grauer','Graues','Eigentlicher'}
def lc(s):
    w = s.split(' ',1); return (w[0].lower()+(' '+w[1] if len(w)>1 else '')) if w[0] in ADJ else s
def cap(s): return s[0].upper()+s[1:]

# english -> (german, de_gender, latin, la_gender)
N = {
 'amygdala':('Mandelkern','m','Corpus amygdaloideum','n'),
 'angular gyrus':('Gyrus angularis','m','Gyrus angularis','m'),
 'anterior commissure':('Vordere Kommissur','f','Commissura anterior','f'),
 'posterior commissure':('Hintere Kommissur','f','Commissura posterior','f'),
 'anterior ethmoidal nerve':('Vorderer Siebbeinnerv','m','Nervus ethmoidalis anterior','m'),
 'posterior ethmoidal nerve':('Hinterer Siebbeinnerv','m','Nervus ethmoidalis posterior','m'),
 'anterior part of superior temporal gyrus':('Vorderer Teil des Gyrus temporalis superior','m','Pars anterior gyri temporalis superioris','f'),
 'posterior part of superior temporal gyrus':('Hinterer Teil des Gyrus temporalis superior','m','Pars posterior gyri temporalis superioris','f'),
 'brachium of inferior colliculus':('Arm des unteren Hügels','m','Brachium colliculi inferioris','n'),
 'brachium of superior colliculus':('Arm des oberen Hügels','m','Brachium colliculi superioris','n'),
 'caudate nucleus':('Schweifkern','m','Nucleus caudatus','m'),
 'central canal of spinal cord':('Zentralkanal des Rückenmarks','m','Canalis centralis medullae spinalis','m'),
 'cerebellum':('Kleinhirn','n','Cerebellum','n'),
 'cerebral aqueduct':('Hirnwasserleitung','f','Aqueductus mesencephali','m'),
 'ciliary ganglion':('Ziliarganglion','n','Ganglion ciliare','n'),
 'cingulate gyrus':('Gürtelwindung','f','Gyrus cinguli','m'),
 'commissure of fornix of forebrain':('Kommissur des Fornix','f','Commissura fornicis','f'),
 'communicating branch of nasociliary nerve with ciliary ganglion':('Verbindungsast des Nasoziliarnervs zum Ziliarganglion','m','Ramus communicans nervi nasociliaris cum ganglio ciliari','m'),
 'corpus callosum':('Balken','m','Corpus callosum','n'),
 'fornix of forebrain':('Fornix','m','Fornix','m'),
 'frontal nerve':('Stirnnerv','m','Nervus frontalis','m'),
 'fusiform gyrus':('Spindelförmige Windung','f','Gyrus fusiformis','m'),
 'globus pallidus':('Pallidum','n','Globus pallidus','m'),
 'habenula':('Habenula','f','Habenula','f'),
 'hippocampus':('Hippocampus','m','Hippocampus','m'),
 'hypothalamus':('Hypothalamus','m','Hypothalamus','m'),
 'inferior branch of oculomotor nerve':('Unterer Ast des Augenbewegungsnervs','m','Ramus inferior nervi oculomotorii','m'),
 'superior branch of oculomotor nerve':('Oberer Ast des Augenbewegungsnervs','m','Ramus superior nervi oculomotorii','m'),
 'inferior colliculus':('Unterer Hügel','m','Colliculus inferior','m'),
 'superior colliculus':('Oberer Hügel','m','Colliculus superior','m'),
 'inferior frontal gyrus':('Untere Stirnwindung','f','Gyrus frontalis inferior','m'),
 'middle frontal gyrus':('Mittlere Stirnwindung','f','Gyrus frontalis medius','m'),
 'superior frontal gyrus':('Obere Stirnwindung','f','Gyrus frontalis superior','m'),
 'inferior temporal gyrus':('Untere Schläfenwindung','f','Gyrus temporalis inferior','m'),
 'middle temporal gyrus':('Mittlere Schläfenwindung','f','Gyrus temporalis medius','m'),
 'infratrochlear nerve':('Nervus infratrochlearis','m','Nervus infratrochlearis','m'),
 'supratrochlear nerve':('Nervus supratrochlearis','m','Nervus supratrochlearis','m'),
 'supra-orbital nerve':('Oberer Augenhöhlennerv','m','Nervus supraorbitalis','m'),
 'insula':('Inselrinde','f','Insula','f'),
 'internal capsule':('Innere Kapsel','f','Capsula interna','f'),
 'interpeduncular fossa':('Interpedunkuläre Grube','f','Fossa interpeduncularis','f'),
 'lacrimal nerve':('Tränennerv','m','Nervus lacrimalis','m'),
 'lamina terminalis':('Lamina terminalis','f','Lamina terminalis','f'),
 'lateral geniculate body':('Seitlicher Kniehöcker','m','Corpus geniculatum laterale','n'),
 'medial geniculate body':('Medialer Kniehöcker','m','Corpus geniculatum mediale','n'),
 'long ciliary nerve':('Langer Ziliarnerv','m','Nervus ciliaris longus','m'),
 'short ciliary nerve':('Kurzer Ziliarnerv','m','Nervus ciliaris brevis','m'),
 'mammillary body':('Brustwarzenkörper','m','Corpus mamillare','n'),
 'medulla oblongata':('Verlängertes Mark','n','Medulla oblongata','f'),
 'midbrain':('Mittelhirn','n','Mesencephalon','n'),
 'nasociliary nerve':('Nasoziliarnerv','m','Nervus nasociliaris','m'),
 'occipital lobe':('Hinterhauptslappen','m','Lobus occipitalis','m'),
 'ophthalmic nerve':('Augennerv','m','Nervus ophthalmicus','m'),
 'optic chiasm':('Sehnervenkreuzung','f','Chiasma opticum','n'),
 'optic nerve':('Sehnerv','m','Nervus opticus','m'),
 'optic tract':('Sehbahn','f','Tractus opticus','m'),
 'orbital gyrus':('Orbitale Windung','f','Gyrus orbitalis','m'),
 'parahippocampal gyrus':('Parahippocampale Windung','f','Gyrus parahippocampalis','m'),
 'peduncle of midbrain':('Hirnschenkel','m','Pedunculus cerebri','m'),
 'pons':('Brücke','f','Pons','m'),
 'postcentral gyrus':('Hintere Zentralwindung','f','Gyrus postcentralis','m'),
 'precentral gyrus':('Vordere Zentralwindung','f','Gyrus precentralis','m'),
 'putamen':('Putamen','n','Putamen','n'),
 'septum of telencephalon':('Septum des Endhirns','n','Septum telencephali','n'),
 'stria medullaris of thalamus':('Markstreifen des Thalamus','m','Stria medullaris thalami','f'),
 'stria terminalis':('Stria terminalis','f','Stria terminalis','f'),
 'superior parietal lobule':('Oberes Scheitelläppchen','n','Lobulus parietalis superior','m'),
 'supramarginal gyrus':('Gyrus supramarginalis','m','Gyrus supramarginalis','m'),
 'tentorium cerebelli':('Kleinhirnzelt','n','Tentorium cerebelli','n'),
 'thalamus':('Thalamus','m','Thalamus','m'),
 'trochlear nerve':('Rollnerv','m','Nervus trochlearis','m'),
 'tuber cinereum':('Tuber cinereum','n','Tuber cinereum','n'),
 'white matter of cerebral hemisphere':('Weiße Substanz der Großhirnhemisphäre','f','Substantia alba hemispherii cerebri','f'),
}

for sd,de,la in (('left','linken','sinistri'),('right','rechten','dextri')):
    N[f'anterior part of {sd} superior temporal gyrus'] = (f'Vorderer Teil des {de} Gyrus temporalis superior','m',f'Pars anterior gyri temporalis superioris {la}','f')
    N[f'posterior part of {sd} superior temporal gyrus'] = (f'Hinterer Teil des {de} Gyrus temporalis superior','m',f'Pars posterior gyri temporalis superioris {la}','f')
    N[f'brachium of {sd} inferior colliculus'] = (f'Arm des {de} unteren Hügels','m',f'Brachium colliculi inferioris {la}','n')
    N[f'brachium of {sd} superior colliculus'] = (f'Arm des {de} oberen Hügels','m',f'Brachium colliculi superioris {la}','n')
    N[f'inferior branch of {sd} oculomotor nerve'] = (f'Unterer Ast des {de} Augenbewegungsnervs','m',f'Ramus inferior nervi oculomotorii {la}','m')
    N[f'superior branch of {sd} oculomotor nerve'] = (f'Oberer Ast des {de} Augenbewegungsnervs','m',f'Ramus superior nervi oculomotorii {la}','m')
    N[f'communicating branch of {sd} nasociliary nerve with {sd} ciliary ganglion'] = (f'Verbindungsast des {de} Nasoziliarnervs zum {de} Ziliarganglion','m',f'Ramus communicans nervi nasociliaris {la} cum ganglio ciliari {"sinistro" if sd=="left" else "dextro"}','m')
    N[f'white matter of {sd} cerebral hemisphere'] = (f'Weiße Substanz der {de} Großhirnhemisphäre','f',f'Substantia alba hemispherii cerebri {la}','f')

SEG = {'anterior basal':('vorderer basaler','basalis anterior'),'posterior basal':('hinterer basaler','basalis posterior'),
       'lateral basal':('seitlicher basaler','basalis lateralis'),'medial basal':('medialer basaler','basalis medialis'),
       'anterior':('vorderer','anterior'),'posterior':('hinterer','posterior'),'apical':('apikaler','apicalis'),
       'superior':('oberer','superior'),'lateral':('seitlicher','lateralis'),'medial':('medialer','medialis')}
R = {
 'epiglottis':('Kehldeckel','m','Epiglottis','f'),
 'trachea':('Luftröhre','f','Trachea','f'),
 'main bronchus':('Hauptbronchus','m','Bronchus principalis','m'),
 'main bronchus proper':('Eigentlicher Hauptbronchus','m','Bronchus principalis proprius','m'),
 'superior lingular bronchial tree':('Oberer Lingula-Bronchialbaum','m','Arbor bronchialis lingularis superior','f'),
 'inferior lingular bronchial tree':('Unterer Lingula-Bronchialbaum','m','Arbor bronchialis lingularis inferior','f'),
 'inferior nasal concha':('Untere Nasenmuschel','f','Concha nasalis inferior','f'),
 'lateral nasal cartilage':('Seitlicher Nasenknorpel','m','Cartilago nasi lateralis','f'),
 'septal nasal cartilage':('Nasenscheidewandknorpel','m','Cartilago septi nasi','f'),
 'superior pharyngeal constrictor':('Oberer Schlundschnürer','m','Musculus constrictor pharyngis superior','m'),
 'middle pharyngeal constrictor':('Mittlerer Schlundschnürer','m','Musculus constrictor pharyngis medius','m'),
 'inferior pharyngeal constrictor':('Unterer Schlundschnürer','m','Musculus constrictor pharyngis inferior','m'),
 'palatopharyngeus':('Gaumen-Rachen-Muskel','m','Musculus palatopharyngeus','m'),
 'salpingopharyngeus':('Tuben-Rachen-Muskel','m','Musculus salpingopharyngeus','m'),
 'stylopharyngeus':('Griffel-Rachen-Muskel','m','Musculus stylopharyngeus','m'),
}
for k,(de,la) in SEG.items():
    R[f'{k} segmental bronchial tree'] = (cap(f'{de} Segmentbronchialbaum'),'m',f'Arbor bronchialis segmentalis {la}','f')

def run(system, D):
    terms = sorted(set(p['name'].lower() for p in atlas['parts'] if p['system']==system))
    rows, missing = [], []
    for t in terms:
        m = re.match(r'^(left|right) (.+)$', t)
        if t in D:
            de,dg,la,lg = D[t]; rows.append((t,de,la))
        elif m and m.group(2) in D:
            s = 0 if m.group(1)=='left' else 1; de,dg,la,lg = D[m.group(2)]
            rows.append((t, f'{DE_SIDE[dg][s]} {lc(de)}', f'{la} {LA_SIDE[lg][s]}'))
        else: missing.append(t)
    print(system, len(rows), 'translated;', len(missing), 'missing', missing)
    rs = [{'english':e,'german':d,'latin':l,'system':system} for e,d,l in rows]
    with open(f'translate/atlas-de-{system}.csv','w',newline='') as f:
        w = csv.DictWriter(f, fieldnames=['english','german','latin','system']); w.writeheader(); w.writerows(rs)
    json.dump(rs, open(f'translate/atlas-de-{system}.json','w'), ensure_ascii=False, indent=1)
    with open(f'translate/atlas-de-{system}.md','w') as f:
        f.write(f'# Human Atlas – {system} (Deutsch / Latein)\n\n| English | Deutsch (Latein) |\n|---|---|\n')
        for r in rs: f.write(f"| {r['english']} | {r['german']} ({r['latin']}) |\n")
run('nervous', N); run('respiratory', R)
