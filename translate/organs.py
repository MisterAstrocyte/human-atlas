import json, csv, re
atlas = json.load(open('public/models/atlas.json'))
DE_SIDE = {'m':('Linker','Rechter'),'f':('Linke','Rechte'),'n':('Linkes','Rechtes')}
LA_SIDE = {'m':('sinister','dexter'),'f':('sinistra','dextra'),'n':('sinistrum','dextrum')}
ADJ = {'Vorderer','Hinterer','Oberer','Unterer','Mittlerer','Seitlicher','Medialer','Langer','Kurzer','Innerer','Äußerer','Vordere','Hintere','Obere','Untere','Mittlere','Seitliche','Mediale','Innere','Vorderes','Hinteres','Oberes','Unteres','Mittleres','Seitliches','Mediales','Inneres','Gemeinsamer','Gemeinsame','Gemeinsames','Aufsteigender','Absteigender','Querer','Freie','Glasige','Glasiger','Glasiges','Vierter','Dritter','Zwischen'}
def lc(s):
    w = s.split(' ',1); return (w[0].lower()+(' '+w[1] if len(w)>1 else '')) if w[0] in ADJ else s
S = (('left','linken','sinistri','sinistrae','sinister','sinistra','sinistrum'),('right','rechten','dextri','dextrae','dexter','dextra','dextrum'))

D = {}   # english -> (german, de_gender, latin, la_gender)
# ---------- digestive ----------
D.update({
 'appendix':('Wurmfortsatz','m','Appendix vermiformis','f'),
 'mesoappendix':('Wurmfortsatzgekröse','n','Mesoappendix','f'),
 'ascending colon':('Aufsteigender Dickdarm','m','Colon ascendens','n'),
 'transverse colon':('Querer Dickdarm','m','Colon transversum','n'),
 'descending colon':('Absteigender Dickdarm','m','Colon descendens','n'),
 'transverse mesocolon':('Gekröse des queren Dickdarms','n','Mesocolon transversum','n'),
 'taenia libera':('Freie Tänie','f','Taenia libera','f'),
 'taenia mesocolica':('Mesokolische Tänie','f','Taenia mesocolica','f'),
 'taenia omentalis':('Omentale Tänie','f','Taenia omentalis','f'),
 'ileocecal junction':('Ileozäkalübergang','m','Junctio ileocaecalis','f'),
 'rectum':('Mastdarm','m','Rectum','n'),
 'stomach':('Magen','m','Gaster','f'),
 'esophagus':('Speiseröhre','f','Oesophagus','m'),
 'duodenum':('Zwölffingerdarm','m','Duodenum','n'),
 'proximal part of jejunum':('Proximaler Teil des Leerdarms','m','Pars proximalis jejuni','f'),
 'middle part of jejunum':('Mittlerer Teil des Leerdarms','m','Pars media jejuni','f'),
 'distal part of jejunum':('Distaler Teil des Leerdarms','m','Pars distalis jejuni','f'),
 'proximal part of ileum':('Proximaler Teil des Krummdarms','m','Pars proximalis ilei','f'),
 'middle part of ileum':('Mittlerer Teil des Krummdarms','m','Pars media ilei','f'),
 'distal part of ileum':('Distaler Teil des Krummdarms','m','Pars distalis ilei','f'),
 'mesentery of small intestine':('Dünndarmgekröse','n','Mesenterium','n'),
 'pancreas':('Bauchspeicheldrüse','f','Pancreas','n'),
 'parenchyma of pancreas':('Parenchym der Bauchspeicheldrüse','n','Parenchyma pancreatis','n'),
 'pancreatic duct':('Bauchspeicheldrüsengang','m','Ductus pancreaticus','m'),
 'pancreatic duct tree':('Bauchspeicheldrüsen-Gangsystem','n','Arbor ductuum pancreaticorum','f'),
 'tongue':('Zunge','f','Lingua','f'),
 'sublingual gland':('Unterzungendrüse','f','Glandula sublingualis','f'),
 'submandibular gland':('Unterkieferdrüse','f','Glandula submandibularis','f'),
 'gallbladder':('Gallenblase','f','Vesica biliaris','f'),
 'cystic duct':('Gallenblasengang','m','Ductus cysticus','m'),
 'common hepatic duct':('Gemeinsamer Lebergang','m','Ductus hepaticus communis','m'),
 'hepatic duct':('Lebergang','m','Ductus hepaticus','m'),
 'caudate lobe of liver':('Schwanzlappen der Leber','m','Lobus caudatus hepatis','m'),
 'duct of caudate lobe of liver':('Gang des Schwanzlappens der Leber','m','Ductus lobi caudati hepatis','m'),
})
for sd,de,la,_,_,_,_ in S:
    D[f'{sd} duct of caudate lobe of liver'] = (f'{DE_SIDE["m"][sd=="right"]} Gang des Schwanzlappens der Leber','m',f'Ductus lobi caudati hepatis {la[:-1] if False else ("sinister" if sd=="left" else "dexter")}','m')
    D[f'caudate lobe tributary of {sd} hepatic biliary tree'] = (f'Schwanzlappenzufluss des {de} Gallengangsystems','m',f'Ramus lobi caudati arboris biliaris {la}','m')
    for en,dd,ll in (('anterior inferior','Vorderer unterer','anterior inferior'),('anterior superior','Vorderer oberer','anterior superior'),
                     ('lateral inferior','Seitlicher unterer','lateralis inferior'),('lateral superior','Seitlicher oberer','lateralis superior'),
                     ('medial inferior','Medialer unterer','medialis inferior'),('medial superior','Medialer oberer','medialis superior'),
                     ('posterior inferior','Hinterer unterer','posterior inferior'),('posterior superior','Hinterer oberer','posterior superior')):
        D[f'{en} tributary of {sd} hepatic biliary tree'] = (f'{dd} Segmentzufluss des {de} Gallengangsystems','m',f'Ramus segmentalis {ll} arboris biliaris {la}','m')
# ---------- sensory ----------
D.update({
 'choroid':('Aderhaut','f','Choroidea','f'),
 'choroid plexus of cerebral hemisphere':('Adergeflecht der Großhirnhemisphäre','n','Plexus choroideus hemispherii cerebri','m'),
 'common tendinous ring':('Gemeinsamer Sehnenring','m','Anulus tendineus communis','m'),
 'cornea':('Hornhaut','f','Cornea','f'),
 'corona ciliaris':('Ziliarkranz','m','Corona ciliaris','f'),
 'external ear':('Äußeres Ohr','n','Auris externa','f'),
 'iris':('Regenbogenhaut','f','Iris','f'),
 'lacrimal bone':('Tränenbein','n','Os lacrimale','n'),
 'lacrimal canaliculus':('Tränenkanälchen','n','Canaliculus lacrimalis','m'),
 'lacrimal gland':('Tränendrüse','f','Glandula lacrimalis','f'),
 'lacrimal lake':('Tränensee','m','Lacus lacrimalis','m'),
 'lacrimal sac':('Tränensack','m','Saccus lacrimalis','m'),
 'lens':('Linse','f','Lens','f'),
 'nasolacrimal duct':('Tränen-Nasen-Gang','m','Ductus nasolacrimalis','m'),
 'sclera':('Lederhaut','f','Sclera','f'),
 'vitreous body':('Glaskörper','m','Corpus vitreum','n'),
})
for sd,de,lg,lgf,lm,lf,ln in S:
    D[f'anterior chamber of {sd} eyeball'] = (f'Vordere Augenkammer des {de} Augapfels','f',f'Camera anterior bulbi oculi {lg}','f')
    D[f'flexor retinaculum of {sd} wrist'] = (f'Beugesehnen-Halteband des {de} Handgelenks','n',f'Retinaculum musculorum flexorum carpi {lg}','n')
    D[f'optic part of {sd} retina'] = (f'Optischer Teil der {de} Netzhaut','m',f'Pars optica retinae {lgf}','f')
    D[f'suspensory ligament of {sd} lens'] = (f'Aufhängeband der {de} Linse','n',f'Zonula ciliaris lentis {lgf}','f')
    D[f'tarsal plate of {sd} lower eyelid'] = (f'Lidplatte des {de} Unterlids','f',f'Tarsus inferior palpebrae {lgf}','m')
    D[f'tarsal plate of {sd} upper eyelid'] = (f'Lidplatte des {de} Oberlids','f',f'Tarsus superior palpebrae {lgf}','m')
# ---------- connective ----------
D.update({
 'calcaneal tendon':('Achillessehne','f','Tendo calcaneus','m'),
 'conus elasticus':('Conus elasticus','m','Conus elasticus','m'),
 'hyo-epiglottic ligament':('Zungenbein-Kehldeckel-Band','n','Ligamentum hyoepiglotticum','n'),
 'thyro-epiglottic ligament':('Schildknorpel-Kehldeckel-Band','n','Ligamentum thyroepiglotticum','n'),
 'intermediate tendon':('Zwischensehne','f','Tendo intermedius','m'),
 'lateral thyrohyoid ligament':('Seitliches Schildknorpel-Zungenbein-Band','n','Ligamentum thyrohyoideum laterale','n'),
 'median thyrohyoid ligament':('Mittleres Schildknorpel-Zungenbein-Band','n','Ligamentum thyrohyoideum medianum','n'),
 'thyrohyoid membrane':('Schildknorpel-Zungenbein-Membran','f','Membrana thyrohyoidea','f'),
 'median cricothyroid ligament':('Mittleres Ringknorpel-Schildknorpel-Band','n','Ligamentum cricothyroideum medianum','n'),
 'vocal ligament':('Stimmband','n','Ligamentum vocale','n'),
 'linea alba':('Weiße Linie','f','Linea alba','f'),
 'long plantar ligament':('Langes Fußsohlenband','n','Ligamentum plantare longum','n'),
 'pharyngeal raphe':('Rachennaht','f','Raphe pharyngis','f'),
 'pterygomandibular raphe':('Flügel-Unterkiefer-Naht','f','Raphe pterygomandibularis','f'),
 'stylohyoid ligament':('Griffel-Zungenbein-Band','n','Ligamentum stylohyoideum','n'),
 'tendinous arch of levator ani':('Sehnenbogen des Afterhebers','m','Arcus tendineus musculi levatoris ani','m'),
 'tensor fasciae latae':('Schenkelbindenspanner','m','Musculus tensor fasciae latae','m'),
})
D['left long plantar ligament'] = ('Linkes langes Fußsohlenband','n','Ligamentum plantare longum sinistrum','n')
D['right long plantar ligament'] = ('Rechtes langes Fußsohlenband','n','Ligamentum plantare longum dextrum','n')
for sd,de,lg,lgf,lm,lf,ln in S:
    D[f'check ligament of {sd} lateral rectus'] = (f'Hemmungsband des {de} seitlichen geraden Augenmuskels','n',f'Lacertus musculi recti lateralis {lg}','m')
    D[f'check ligament of {sd} medial rectus'] = (f'Hemmungsband des {de} inneren geraden Augenmuskels','n',f'Lacertus musculi recti medialis {lg}','m')
    D[f'interosseous membrane of {sd} forearm'] = (f'Zwischenknochenmembran des {de} Unterarms','f',f'Membrana interossea antebrachii {lg}','f')
    D[f'interosseous membrane of {sd} leg'] = (f'Zwischenknochenmembran des {de} Unterschenkels','f',f'Membrana interossea cruris {lg}','f')
    D[f'tendon of {sd} levator palpebrae superioris'] = (f'Sehne des {de} Oberlidhebers','f',f'Tendo musculi levatoris palpebrae superioris {lg}','m')
    D[f'trochlea of {sd} superior oblique'] = (f'Rolle des {de} oberen schrägen Augenmuskels','f',f'Trochlea musculi obliqui superioris {lg}','f')
# ---------- cardiac (+ brain ventricles filed under cardiac in the data) ----------
D.update({
 'anterior cusp of aortic valve':('Vordere Tasche der Aortenklappe','f','Valvula semilunaris anterior valvae aortae','f'),
 'posterior cusp of aortic valve':('Hintere Tasche der Aortenklappe','f','Valvula semilunaris posterior valvae aortae','f'),
 'anterior cusp of pulmonary valve':('Vordere Tasche der Pulmonalklappe','f','Valvula semilunaris anterior valvae trunci pulmonalis','f'),
 'posterior cusp of pulmonary valve':('Hintere Tasche der Pulmonalklappe','f','Valvula semilunaris posterior valvae trunci pulmonalis','f'),
 'anterior leaflet of mitral valve':('Vorderes Segel der Mitralklappe','n','Cuspis anterior valvae mitralis','f'),
 'posterior leaflet of mitral valve':('Hinteres Segel der Mitralklappe','n','Cuspis posterior valvae mitralis','f'),
 'anterior leaflet of tricuspid valve':('Vorderes Segel der Trikuspidalklappe','n','Cuspis anterior valvae tricuspidalis','f'),
 'posterior leaflet of tricuspid valve':('Hinteres Segel der Trikuspidalklappe','n','Cuspis posterior valvae tricuspidalis','f'),
 'septal leaflet of tricuspid valve':('Septales Segel der Trikuspidalklappe','n','Cuspis septalis valvae tricuspidalis','f'),
 'third ventricle':('Dritter Hirnventrikel','m','Ventriculus tertius','m'),
 'fourth ventricle':('Vierter Hirnventrikel','m','Ventriculus quartus','m'),
 'lateral ventricle':('Seitenventrikel','m','Ventriculus lateralis','m'),
 'interventricular foramen':('Zwischenkammerloch','n','Foramen interventriculare','n'),
 'wall of ventricle':('Wand der Herzkammer','f','Paries ventriculi','m'),
})
for sd,de,lg,lgf,lm,lf,ln in S:
    D[f'cavity of {sd} atrium'] = (f'Höhle des {de} Vorhofs','f',f'Cavitas atrii {lg}','f')
    D[f'cavity of {sd} ventricle'] = (f'Höhle der {de} Herzkammer','f',f'Cavitas ventriculi {lg}','f')
    D[f'wall of {sd} atrium'] = (f'Wand des {de} Vorhofs','f',f'Paries atrii {lg}','m')
    D[f'{sd} anterior cusp of pulmonary valve'] = (f'{DE_SIDE["f"][sd=="right"]} vordere Tasche der Pulmonalklappe','f',f'Valvula semilunaris anterior {lf} valvae trunci pulmonalis','f')
    D[f'{sd} posterior cusp of aortic valve'] = (f'{DE_SIDE["f"][sd=="right"]} hintere Tasche der Aortenklappe','f',f'Valvula semilunaris posterior {lf} valvae aortae','f')

def run(system):
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
for sy in ('digestive','sensory','connective','cardiac'): run(sy)
