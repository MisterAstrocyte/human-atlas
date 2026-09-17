import json, csv, re, sys

atlas = json.load(open('public/models/atlas.json'))
SYSTEM = sys.argv[1] if len(sys.argv) > 1 else 'arterial'
terms = sorted(set(p['name'].lower() for p in atlas['parts'] if p['system'] == SYSTEM))

# ---------------- grammar helpers ----------------
NOM_END = {'m':'er','f':'e','n':'es','p':'e'}
ART_GEN = {'m':'des','f':'der','n':'des','p':'der'}
LA_SIDE = {'m':('sinister','dexter'),'f':('sinistra','dextra'),'n':('sinistrum','dextrum'),'p':('sinistrae','dextrae')}
NOUN_GEN = {'Zufluss':'Zuflusses','Venennetz':'Venennetzes','Venenbogen':'Venenbogens','Sinus':'Sinus','Ast':'Astes','Stamm':'Stammes','Bogen':'Bogens','Teil':'Teils','Abschnitt':'Abschnitts',
            'Aortenbogen':'Aortenbogens','Hohlhandbogen':'Hohlhandbogens','Fußsohlenbogen':'Fußsohlenbogens',
            'Eingeweidestamm':'Eingeweidestamms','Lungenstamm':'Lungenstamms','Rippen-Hals-Stamm':'Rippen-Hals-Stamms',
            'Schilddrüsen-Hals-Stamm':'Schilddrüsen-Hals-Stamms','Arm-Kopf-Stamm':'Arm-Kopf-Stamms'}

def de_adj(stems, gender, genitive=False):
    return ' '.join(s + ('en' if genitive else NOM_END[gender]) for s in stems.split() if s)

def de_noun_gen(noun, gender):
    if gender in ('f','p'): return noun
    if noun in NOUN_GEN: return NOUN_GEN[noun]
    for k,v in NOUN_GEN.items():
        if noun.endswith(k): return noun[:-len(k)] + v
        if noun.endswith(k.lower()): return noun[:-len(k)] + v.lower()
    return noun + 's'

LA_HEAD_GEN = {'Vena':'venae','Venae':'venarum','Sinus':'sinus','Rete':'retis','Arteria':'arteriae','Arteriae':'arteriarum','Ramus':'rami','Rami':'ramorum','Truncus':'trunci',
               'Pars':'partis','Aorta':'aortae','Arcus':'arcus'}
LA_FIXED = {'princeps':'principis','dexter':'dextri','sinister':'sinistri'}
def la_word_gen(w, gender):
    if w in LA_FIXED: return LA_FIXED[w]
    if w in LA_HEAD_GEN: return LA_HEAD_GEN[w]
    if w.endswith('um') and gender=='n': return w[:-2]+'i'
    if w.endswith(('ae','i','is','um')) and not w.endswith('us'): return w
    if w.endswith('ior'): return w + 'is'
    if w.endswith('ns'): return w[:-2] + 'ntis'
    if w.endswith('us'):
        return w[:-2] + 'i' if gender in ('m',) else w   # genus, arcus… unchanged in fem context
    if w.endswith('a'): return w + 'e'
    if w.endswith('e'): return w[:-1] + 'is'
    return w
def la_gen(phrase, gender):
    return ' '.join(la_word_gen(w, gender) for w in phrase.split())

def cap(s): return s[0].upper()+s[1:]

# ---------------- base arteries ----------------
# english -> (german adj stems, german noun, gender, latin nominative)
A = {
 'abdominal aorta':('','Bauchaorta','f','Aorta abdominalis'),
 'ascending aorta':('aufsteigend','Aorta','f','Aorta ascendens'),
 'descending aorta':('absteigend','Aorta','f','Aorta descendens'),
 'descending thoracic aorta':('absteigend','Brustaorta','f','Aorta thoracica descendens'),
 'thoracic aorta':('','Brustaorta','f','Aorta thoracica'),
 'arch of aorta':('','Aortenbogen','m','Arcus aortae'),
 'anterior basal segmental artery':('vorder basal','Segmentarterie','f','Arteria segmentalis basalis anterior'),
 'posterior basal segmental artery':('hinter basal','Segmentarterie','f','Arteria segmentalis basalis posterior'),
 'lateral basal segmental artery':('seitlich basal','Segmentarterie','f','Arteria segmentalis basalis lateralis'),
 'medial basal segmental artery':('medial basal','Segmentarterie','f','Arteria segmentalis basalis medialis'),
 'anterior segmental artery':('vorder','Segmentarterie','f','Arteria segmentalis anterior'),
 'posterior segmental artery':('hinter','Segmentarterie','f','Arteria segmentalis posterior'),
 'apical segmental artery':('apikal','Segmentarterie','f','Arteria segmentalis apicalis'),
 'superior segmental artery':('ober','Segmentarterie','f','Arteria segmentalis superior'),
 'lateral segmental artery':('seitlich','Segmentarterie','f','Arteria segmentalis lateralis'),
 'medial segmental artery':('medial','Segmentarterie','f','Arteria segmentalis medialis'),
 'superior lingular artery':('ober','Lingula-Arterie','f','Arteria lingularis superior'),
 'inferior lingular artery':('unter','Lingula-Arterie','f','Arteria lingularis inferior'),
 'upper lobar artery':('ober','Lappenarterie','f','Arteria lobaris superior'),
 'anterior cecal artery':('vorder','Blinddarmarterie','f','Arteria caecalis anterior'),
 'posterior cecal artery':('hinter','Blinddarmarterie','f','Arteria caecalis posterior'),
 'anterior cerebral artery':('vorder','Hirnarterie','f','Arteria cerebri anterior'),
 'middle cerebral artery':('mittler','Hirnarterie','f','Arteria cerebri media'),
 'posterior cerebral artery':('hinter','Hirnarterie','f','Arteria cerebri posterior'),
 'anterior choroidal artery':('vorder','Aderhautarterie','f','Arteria choroidea anterior'),
 'posterior medial choroidal artery':('hinter medial','Aderhautarterie','f','Arteria choroidea posterior medialis'),
 'anterior circumflex humeral artery':('vorder','Oberarm-Zirkumflexarterie','f','Arteria circumflexa humeri anterior'),
 'posterior circumflex humeral artery':('hinter','Oberarm-Zirkumflexarterie','f','Arteria circumflexa humeri posterior'),
 'circumflex scapular artery':('','Schulterblatt-Zirkumflexarterie','f','Arteria circumflexa scapulae'),
 'lateral circumflex femoral artery':('seitlich','Oberschenkel-Zirkumflexarterie','f','Arteria circumflexa femoris lateralis'),
 'anterior communicating artery':('vorder','Verbindungsarterie','f','Arteria communicans anterior'),
 'posterior communicating artery':('hinter','Verbindungsarterie','f','Arteria communicans posterior'),
 'anterior inferior cerebellar artery':('vorder unter','Kleinhirnarterie','f','Arteria inferior anterior cerebelli'),
 'posterior inferior cerebellar artery':('hinter unter','Kleinhirnarterie','f','Arteria inferior posterior cerebelli'),
 'superior cerebellar artery':('ober','Kleinhirnarterie','f','Arteria superior cerebelli'),
 'anterior inferior pancreaticoduodenal artery':('vorder unter','Pankreas-Duodenal-Arterie','f','Arteria pancreaticoduodenalis inferior anterior'),
 'anterior superior pancreaticoduodenal artery':('vorder ober','Pankreas-Duodenal-Arterie','f','Arteria pancreaticoduodenalis superior anterior'),
 'posterior inferior pancreaticoduodenal artery':('hinter unter','Pankreas-Duodenal-Arterie','f','Arteria pancreaticoduodenalis inferior posterior'),
 'posterior superior pancreaticoduodenal artery':('hinter ober','Pankreas-Duodenal-Arterie','f','Arteria pancreaticoduodenalis superior posterior'),
 'inferior pancreaticoduodenal artery':('unter','Pankreas-Duodenal-Arterie','f','Arteria pancreaticoduodenalis inferior'),
 'anterior inferior segmental hepatic artery':('vorder unter','Lebersegmentarterie','f','Arteria segmentalis hepatica anterior inferior'),
 'anterior superior segmental hepatic artery':('vorder ober','Lebersegmentarterie','f','Arteria segmentalis hepatica anterior superior'),
 'lateral inferior segmental hepatic artery':('seitlich unter','Lebersegmentarterie','f','Arteria segmentalis hepatica lateralis inferior'),
 'lateral superior segmental hepatic artery':('seitlich ober','Lebersegmentarterie','f','Arteria segmentalis hepatica lateralis superior'),
 'medial inferior segmental hepatic artery':('medial unter','Lebersegmentarterie','f','Arteria segmentalis hepatica medialis inferior'),
 'medial superior segmental hepatic artery':('medial ober','Lebersegmentarterie','f','Arteria segmentalis hepatica medialis superior'),
 'posterior inferior segmental hepatic artery':('hinter unter','Lebersegmentarterie','f','Arteria segmentalis hepatica posterior inferior'),
 'posterior superior segmental hepatic artery':('hinter ober','Lebersegmentarterie','f','Arteria segmentalis hepatica posterior superior'),
 'anterior interosseous artery':('vorder','Zwischenknochenarterie','f','Arteria interossea anterior'),
 'common interosseous artery':('gemeinsam','Zwischenknochenarterie','f','Arteria interossea communis'),
 'recurrent interosseous artery':('rückläufig','Zwischenknochenarterie','f','Arteria interossea recurrens'),
 'anterior parietal artery':('vorder','Scheitellappenarterie','f','Arteria parietalis anterior'),
 'posterior parietal artery':('hinter','Scheitellappenarterie','f','Arteria parietalis posterior'),
 'anterior spinal artery':('vorder','Rückenmarksarterie','f','Arteria spinalis anterior'),
 'anterior temporal artery':('vorder','Schläfenlappenarterie','f','Arteria temporalis anterior'),
 'polar temporal artery':('polar','Schläfenlappenarterie','f','Arteria polaris temporalis'),
 'anterior tibial artery':('vorder','Schienbeinarterie','f','Arteria tibialis anterior'),
 'posterior tibial artery':('hinter','Schienbeinarterie','f','Arteria tibialis posterior'),
 'anterior tibial recurrent artery':('vorder rückläufig','Schienbeinarterie','f','Arteria recurrens tibialis anterior'),
 'anterior ulnar recurrent artery':('vorder rückläufig','Ellenarterie','f','Arteria recurrens ulnaris anterior'),
 'posterior ulnar recurrent artery':('hinter rückläufig','Ellenarterie','f','Arteria recurrens ulnaris posterior'),
 'radial recurrent artery':('rückläufig','Speichenarterie','f','Arteria recurrens radialis'),
 'radial artery':('','Speichenarterie','f','Arteria radialis'),
 'ulnar artery':('','Ellenarterie','f','Arteria ulnaris'),
 'appendicular artery':('','Wurmfortsatzarterie','f','Arteria appendicularis'),
 'arcuate artery':('','Bogenarterie','f','Arteria arcuata'),
 'arteria princeps pollicis':('','Hauptdaumenarterie','f','Arteria princeps pollicis'),
 'arteria radialis indicis':('speichenseitig','Zeigefingerarterie','f','Arteria radialis indicis'),
 'axillary artery':('','Achselarterie','f','Arteria axillaris'),
 'basilar artery':('','Basilararterie','f','Arteria basilaris'),
 'brachial artery':('','Oberarmarterie','f','Arteria brachialis'),
 'deep brachial artery':('tief','Oberarmarterie','f','Arteria profunda brachii'),
 'brachiocephalic artery':('','Arm-Kopf-Stamm','m','Truncus brachiocephalicus'),
 'bronchial artery':('','Bronchialarterie','f','Arteria bronchialis'),
 'callosomarginal artery':('','Callosomarginalarterie','f','Arteria callosomarginalis'),
 'caudal pancreatic artery':('','Pankreasschwanzarterie','f','Arteria caudae pancreatis'),
 'dorsal pancreatic artery':('dorsal','Pankreasarterie','f','Arteria pancreatica dorsalis'),
 'great pancreatic artery':('groß','Pankreasarterie','f','Arteria pancreatica magna'),
 'inferior pancreatic artery':('unter','Pankreasarterie','f','Arteria pancreatica inferior'),
 'celiac artery':('','Eingeweidearterie','f','Arteria coeliaca'),
 'celiac trunk':('','Eingeweidestamm','m','Truncus coeliacus'),
 'colic artery':('','Dickdarmarterie','f','Arteria colica'),
 'middle colic artery':('mittler','Dickdarmarterie','f','Arteria colica media'),
 'marginal colic artery':('','Dickdarmrandarterie','f','Arteria marginalis coli'),
 'marginal artery of colon':('','Dickdarmrandarterie','f','Arteria marginalis coli'),
 'common carotid artery':('gemeinsam','Halsschlagader','f','Arteria carotis communis'),
 'internal carotid artery':('inner','Halsschlagader','f','Arteria carotis interna'),
 'common hepatic artery':('gemeinsam','Leberarterie','f','Arteria hepatica communis'),
 'hepatic artery':('','Leberarterie','f','Arteria hepatica'),
 'hepatic artery proper':('eigentlich','Leberarterie','f','Arteria hepatica propria'),
 'common iliac artery':('gemeinsam','Beckenarterie','f','Arteria iliaca communis'),
 'external iliac artery':('äußer','Beckenarterie','f','Arteria iliaca externa'),
 'internal iliac artery':('inner','Beckenarterie','f','Arteria iliaca interna'),
 'conus artery':('','Konusarterie','f','Arteria coni arteriosi'),
 'coronary artery':('','Koronararterie','f','Arteria coronaria'),
 'anterior interventricular artery':('vorder','Zwischenkammerarterie','f','Arteria interventricularis anterior'),
 'posterior interventricular artery':('hinter','Zwischenkammerarterie','f','Arteria interventricularis posterior'),
 'costocervical trunk':('','Rippen-Hals-Stamm','m','Truncus costocervicalis'),
 'thyrocervical trunk':('','Schilddrüsen-Hals-Stamm','m','Truncus thyrocervicalis'),
 'deep cervical artery':('tief','Halsarterie','f','Arteria cervicalis profunda'),
 'superficial cervical artery':('oberflächlich','Halsarterie','f','Arteria cervicalis superficialis'),
 'transverse cervical artery':('quer','Halsarterie','f','Arteria transversa cervicis'),
 'deep palmar arch':('tief','Hohlhandbogen','m','Arcus palmaris profundus'),
 'superficial palmar arterial arch':('oberflächlich','Hohlhandbogen','m','Arcus palmaris superficialis'),
 'plantar arch':('','Fußsohlenbogen','m','Arcus plantaris'),
 'deep plantar artery':('tief','Fußsohlenarterie','f','Arteria plantaris profunda'),
 'lateral plantar artery':('seitlich','Fußsohlenarterie','f','Arteria plantaris lateralis'),
 'medial plantar artery':('medial','Fußsohlenarterie','f','Arteria plantaris medialis'),
 'superficial medial plantar artery':('oberflächlich medial','Fußsohlenarterie','f','Arteria plantaris medialis superficialis'),
 'plantar metatarsal artery':('','Fußsohlen-Mittelfußarterie','f','Arteria metatarsalis plantaris'),
 'descending genicular artery':('absteigend','Kniearterie','f','Arteria descendens genus'),
 'inferior lateral genicular artery':('unter seitlich','Kniearterie','f','Arteria inferior lateralis genus'),
 'inferior medial genicular artery':('unter medial','Kniearterie','f','Arteria inferior medialis genus'),
 'lateral superior genicular artery':('ober seitlich','Kniearterie','f','Arteria superior lateralis genus'),
 'medial superior genicular artery':('ober medial','Kniearterie','f','Arteria superior medialis genus'),
 'middle genicular artery':('mittler','Kniearterie','f','Arteria media genus'),
 'distal perforating artery':('distal','Perforansarterie','f','Arteria perforans distalis'),
 'dorsal artery of penis':('dorsal','Penisarterie','f','Arteria dorsalis penis'),
 'dorsal digital artery of foot':('dorsal','Zehenarterie','f','Arteria digitalis dorsalis pedis'),
 'dorsal scapular artery':('dorsal','Schulterblattarterie','f','Arteria dorsalis scapulae'),
 'dorsalis pedis artery':('','Fußrückenarterie','f','Arteria dorsalis pedis'),
 'esophageal artery':('','Speiseröhrenarterie','f','Arteria oesophagea'),
 'femoral artery':('','Oberschenkelarterie','f','Arteria femoralis'),
 'first common palmar digital artery':('erst gemeinsam','Hohlhand-Fingerarterie','f','Arteria digitalis palmaris communis prima'),
 'second common palmar digital artery':('zweit gemeinsam','Hohlhand-Fingerarterie','f','Arteria digitalis palmaris communis secunda'),
 'third common palmar digital artery':('dritt gemeinsam','Hohlhand-Fingerarterie','f','Arteria digitalis palmaris communis tertia'),
 'fourth common palmar digital artery':('viert gemeinsam','Hohlhand-Fingerarterie','f','Arteria digitalis palmaris communis quarta'),
 'first posterior intercostal artery':('erst hinter','Zwischenrippenarterie','f','Arteria intercostalis posterior prima'),
 'second posterior intercostal artery':('zweit hinter','Zwischenrippenarterie','f','Arteria intercostalis posterior secunda'),
 'posterior intercostal arteries':('hinter','Zwischenrippenarterien','p','Arteriae intercostales posteriores'),
 'superior intercostal artery':('oberst','Zwischenrippenarterie','f','Arteria intercostalis suprema'),
 'gastric artery':('','Magenarterie','f','Arteria gastrica'),
 'gastro-epiploic artery':('','Magen-Netz-Arterie','f','Arteria gastroomentalis'),
 'gastroduodenal artery':('','Magen-Duodenal-Arterie','f','Arteria gastroduodenalis'),
 'ileal artery':('','Krummdarmarterie','f','Arteria ilealis'),
 'ileocolic artery':('','Ileokolikarterie','f','Arteria ileocolica'),
 'inferior epigastric artery':('unter','Bauchdeckenarterie','f','Arteria epigastrica inferior'),
 'superior epigastric artery':('ober','Bauchdeckenarterie','f','Arteria epigastrica superior'),
 'superficial epigastric artery':('oberflächlich','Bauchdeckenarterie','f','Arteria epigastrica superficialis'),
 'inferior mesenteric artery':('unter','Gekrösearterie','f','Arteria mesenterica inferior'),
 'superior mesenteric artery':('ober','Gekrösearterie','f','Arteria mesenterica superior'),
 'inferior phrenic artery':('unter','Zwerchfellarterie','f','Arteria phrenica inferior'),
 'inferior suprarenal artery':('unter','Nebennierenarterie','f','Arteria suprarenalis inferior'),
 'middle suprarenal artery':('mittler','Nebennierenarterie','f','Arteria suprarenalis media'),
 'inferior thyroid artery':('unter','Schilddrüsenarterie','f','Arteria thyroidea inferior'),
 'inferior ulnar collateral artery':('unter','Ellen-Kollateralarterie','f','Arteria collateralis ulnaris inferior'),
 'superior ulnar collateral artery':('ober','Ellen-Kollateralarterie','f','Arteria collateralis ulnaris superior'),
 'internal thoracic artery':('inner','Brustwandarterie','f','Arteria thoracica interna'),
 'lateral thoracic artery':('seitlich','Brustwandarterie','f','Arteria thoracica lateralis'),
 'lateral frontobasal artery':('seitlich','Frontobasalarterie','f','Arteria frontobasalis lateralis'),
 'medial frontobasal artery':('medial','Frontobasalarterie','f','Arteria frontobasalis medialis'),
 'lateral occipital artery':('seitlich','Hinterhauptarterie','f','Arteria occipitalis lateralis'),
 'medial occipital artery':('medial','Hinterhauptarterie','f','Arteria occipitalis medialis'),
 'lateral tarsal artery':('seitlich','Fußwurzelarterie','f','Arteria tarsalis lateralis'),
 'lumbar artery':('','Lendenarterie','f','Arteria lumbalis'),
 'musculophrenic artery':('','Muskel-Zwerchfell-Arterie','f','Arteria musculophrenica'),
 'ophthalmic artery':('','Augenarterie','f','Arteria ophthalmica'),
 'palmar metacarpal artery':('','Hohlhand-Mittelhandarterie','f','Arteria metacarpalis palmaris'),
 'pericallosal artery':('','Perikallosalarterie','f','Arteria pericallosa'),
 'pontine artery':('','Brückenarterie','f','Arteria pontis'),
 'popliteal artery':('','Kniekehlenarterie','f','Arteria poplitea'),
 'prefrontal artery':('','Präfrontalarterie','f','Arteria prefrontalis'),
 'pulmonary artery':('','Lungenarterie','f','Arteria pulmonalis'),
 'pulmonary trunk':('','Lungenstamm','m','Truncus pulmonalis'),
 'renal artery':('','Nierenarterie','f','Arteria renalis'),
 'sigmoid artery':('','Sigmaarterie','f','Arteria sigmoidea'),
 'splenial artery':('','Spleniumarterie','f','Arteria splenialis'),
 'splenic artery':('','Milzarterie','f','Arteria splenica'),
 'subclavian artery':('','Unterschlüsselbeinarterie','f','Arteria subclavia'),
 'subcostal artery':('','Unterrippenarterie','f','Arteria subcostalis'),
 'subscapular artery':('','Unterschulterblattarterie','f','Arteria subscapularis'),
 'suprascapular artery':('','Oberschulterblattarterie','f','Arteria suprascapularis'),
 'superior rectal artery':('ober','Mastdarmarterie','f','Arteria rectalis superior'),
 'testicular artery':('','Hodenarterie','f','Arteria testicularis'),
 'thalamogeniculate artery':('','Thalamogenikulararterie','f','Arteria thalamogeniculata'),
 'thalamoperforating artery':('','Thalamoperforansarterie','f','Arteria thalamoperforans'),
 'thoracodorsal artery':('','Brust-Rücken-Arterie','f','Arteria thoracodorsalis'),
 'thoraco-acromial artery':('','Brust-Schulterhöhen-Arterie','f','Arteria thoracoacromialis'),
 'vertebral artery':('','Wirbelarterie','f','Arteria vertebralis'),
}
# branch modifiers: english -> (german adj stems, german noun prefix, latin masc adjectives)
BR = {
 'accessory subsuperior':('akzessorisch subsuperior','','subsuperior accessorius'),
 'acromial':('','Schulterhöhen','acromialis'), 'anterior':('vorder','','anterior'), 'posterior':('hinter','','posterior'),
 'anterior temporal':('vorder','Schläfen','temporalis anterior'), 'middle temporal':('mittler','Schläfen','temporalis medius'),
 'posterior temporal':('hinter','Schläfen','temporalis posterior'),
 'anterolateral central':('anterolateral zentral','','centralis anterolateralis'),
 'posteromedial central':('posteromedial zentral','','centralis posteromedialis'),
 'ascending':('aufsteigend','','ascendens'), 'descending':('absteigend','','descendens'),
 'basal':('basal','','basalis'), 'laterobasal':('laterobasal','','laterobasalis'), 'mediobasal':('mediobasal','','mediobasalis'),
 'bronchial':('','Bronchial','bronchialis'), 'caudate lobe':('','Schwanzlappen','lobi caudati'), 'lobe':('','Lappen','lobi'),
 'circumflex':('','Zirkumflex','circumflexus'), 'left lobe':('','Linkslappen','lobi sinistri'), 'right lobe':('','Rechtslappen','lobi dextri'), 'conus':('','Konus','coni arteriosi'), 'deltoid':('','Delta','deltoideus'),
 'diagonal':('diagonal','','diagonalis'), 'dorsal carpal':('dorsal','Handwurzel','carpalis dorsalis'),
 'first anterior ventricular':('erst vorder','Kammer','ventricularis anterior primus'),
 'first posterior ventricular':('erst hinter','Kammer','ventricularis posterior primus'),
 'first septal':('erst','Septum','septalis primus'), 'second septal':('zweit','Septum','septalis secundus'), 'septal':('','Septum','septalis'),
 'first right anterior':('erst recht vorder','','anterior dexter primus'),
 'second right anterior':('zweit recht vorder','','anterior dexter secundus'),
 'third right anterior':('dritt recht vorder','','anterior dexter tertius'),
 'hypothalamic':('','Hypothalamus','hypothalamicus'), 'ileal':('','Krummdarm','ilealis'),
 'inferior':('unter','','inferior'), 'superior':('ober','','superior'), 'lateral':('seitlich','','lateralis'), 'medial':('medial','','medialis'),
 'inferior segmental':('unter','Segment','segmentalis inferior'), 'superior segmental':('ober','Segment','segmentalis superior'),
 'posterior segmental':('hinter','Segment','segmentalis posterior'),
 'intermediomedial':('intermediomedial','','intermediomedialis'), 'paracentral':('parazentral','','paracentralis'),
 'posteromedial':('posteromedial','','posteromedialis'), 'precuneal':('','Precuneus','precunealis'),
 'marginal':('','Rand','marginalis'), 'middle collateral':('mittler','Kollateral','collateralis medius'),
 'radial collateral':('speichenseitig','Kollateral','collateralis radialis'), 'pectoral':('','Brust','pectoralis'),
 'posterior interventricular':('hinter','Zwischenkammer','interventricularis posterior'),
 'anterior interventricular':('vorder','Zwischenkammer','interventricularis anterior'),
 'anterior descending':('vorder absteigend','','interventricularis anterior'),
 'superior vermian':('ober','Wurm','vermis superior'), 'temporo-occipital':('','Schläfen-Hinterhaupt-','temporooccipitalis'),
 'inferior terminal':('unter terminal','','terminalis inferior'),
}
PARTS = {
 'insular':('insulär','insularis'), 'sphenoid':('sphenoidal','sphenoidalis'),
 'postcommunicating':('postkommunikal','postcommunicalis'), 'precommunicating':('präkommunikal','precommunicalis'),
 'anterior':('vorder','anterior'), 'posterior':('hinter','posterior'), 'apical':('apikal','apicalis'),
}
DIGIT = {'index finger':('Zeigefingers','indicis'),'middle finger':('Mittelfingers','digiti medii'),
         'ring finger':('Ringfingers','digiti anularis'),'little finger':('Kleinfingers','digiti minimi')}
FIXED = {
 'artery of central sulcus':('Arterie des Sulcus centralis','Arteria sulci centralis'),
 'artery of left postcentral sulcus':('Arterie des linken Sulcus postcentralis','Arteria sulci postcentralis sinistri'),
 'artery of right postcentral sulcus':('Arterie des rechten Sulcus postcentralis','Arteria sulci postcentralis dextri'),
 'artery of left precentral sulcus':('Arterie des linken Sulcus precentralis','Arteria sulci precentralis sinistri'),
 'artery of right precentral sulcus':('Arterie des rechten Sulcus precentralis','Arteria sulci precentralis dextri'),
 'branch of left middle cerebral artery to left angular gyrus':('Ast der linken mittleren Hirnarterie zum linken Gyrus angularis','Ramus arteriae cerebri mediae sinistrae ad gyrum angularem sinistrum'),
 'branch of right middle cerebral artery to right angular gyrus':('Ast der rechten mittleren Hirnarterie zum rechten Gyrus angularis','Ramus arteriae cerebri mediae dextrae ad gyrum angularem dextrum'),
 'branch of left anterior choroidal artery to posterior limb of left internal capsule':('Ast der linken vorderen Aderhautarterie zum hinteren Schenkel der linken inneren Kapsel','Ramus arteriae choroideae anterioris sinistrae ad crus posterius capsulae internae sinistrae'),
 'branch of right anterior choroidal artery to posterior limb of right internal capsule':('Ast der rechten vorderen Aderhautarterie zum hinteren Schenkel der rechten inneren Kapsel','Ramus arteriae choroideae anterioris dextrae ad crus posterius capsulae internae dextrae'),
 'set of calcaneal branches of posterior tibial artery':('Fersenbeinäste der hinteren Schienbeinarterie','Rami calcanei arteriae tibialis posterioris'),
 'set of common plantar digital arteries':('Gemeinsame Fußsohlen-Zehenarterien','Arteriae digitales plantares communes'),
 'set of dorsal digital arteries':('Rückseitige Fingerarterien','Arteriae digitales dorsales'),
 'set of dorsal metacarpal arteries':('Rückseitige Mittelhandarterien','Arteriae metacarpales dorsales'),
 'set of oesophageal branches of thoracic aorta':('Speiseröhrenäste der Brustaorta','Rami oesophageales aortae thoracicae'),
 'set of perforating arteries':('Perforansarterien','Arteriae perforantes'),
 'set of plantar digital arteries proper':('Eigentliche Fußsohlen-Zehenarterien','Arteriae digitales plantares propriae'),
 'set of posterior temporal branches of lateral occipital artery':('Hintere Schläfenäste der seitlichen Hinterhauptarterie','Rami temporales posteriores arteriae occipitalis lateralis'),
}

try:
    sys.path.insert(0,'translate'); from vocab43 import A43, BR43
    A.update(A43); BR.update(BR43)
except Exception: pass
if SYSTEM == 'venous':
    sys.path.insert(0,'translate'); from veins_vocab import V, VBR, VPARTS, VFIXED
    A.update(V); BR.update(VBR); PARTS.update(VPARTS); FIXED.update(VFIXED)

class NP:
    def __init__(s, de_nom, de_gen, la_nom, la_gen): s.de_nom, s.de_gen, s.la_nom, s.la_gen = de_nom, de_gen, la_nom, la_gen

def build(stems, noun, gender, la, side=None):
    """Build a noun phrase; side = 0 left / 1 right / None."""
    st = (('link','recht')[side] + ' ' + stems).strip() if side is not None else stems
    la_n = la + (' ' + LA_SIDE[gender][side] if side is not None else '')
    h = la.split()[0]
    la_gender = 'm' if h in ('Ramus','Truncus','Arcus','Sinus') else ('n' if h=='Rete' else ('p' if h in ('Arteriae','Rami','Venae') else 'f'))
    de_nom = cap((de_adj(st, gender) + ' ' + noun).strip())
    de_gen = ART_GEN[gender] + ' ' + (de_adj(st, gender, True) + ' ' + de_noun_gen(noun, gender)).strip()
    return NP(de_nom, de_gen, la_n, la_gen(la_n, la_gender))

def parse(t):
    m = re.match(r'^(left|right) (.+)$', t)
    side = None
    if m and m.group(2) in A: side = 0 if m.group(1)=='left' else 1; t = m.group(2)
    if t in A:
        stems, noun, g, la = A[t]; return build(stems, noun, g, la, side)
    m = re.match(r'^(lateral|medial) proper palmar digital artery of (left|right) (.+)$', t)
    if m:
        s = 0 if m.group(2)=='left' else 1; dde, dla = DIGIT[m.group(3)]
        st = 'seitlich' if m.group(1)=='lateral' else 'medial'
        base = build(st + ' eigentlich', 'Hohlhand-Fingerarterie', 'f', f'Arteria digitalis palmaris propria {"lateralis" if st=="seitlich" else "medialis"}')
        tail_de = f' des {("linken","rechten")[s]} {dde}'; tail_la = f' {dla} {("sinistri","dextri")[s]}'
        return NP(base.de_nom + tail_de, base.de_gen + tail_de, base.la_nom + tail_la, base.la_gen + tail_la)
    m = re.match(r'^(.+) of (left|right) (foot|hand)$', t)
    if m and f'{m.group(1)} of {m.group(3)}' in A:
        sidx = 0 if m.group(2)=='left' else 1
        stems, noun, g, la = A[f'{m.group(1)} of {m.group(3)}']
        base = build(stems, noun, g, la)
        st = ('link','recht')[sidx] + ' ' + stems
        de_nom = cap((de_adj(st, g) + ' ' + noun).strip())
        de_gen = ART_GEN[g] + ' ' + (de_adj(st, g, True) + ' ' + de_noun_gen(noun, g)).strip()
        la_n = la.replace(' pedis', f' pedis {("sinistri","dextri")[sidx]}').replace(' manus', f' manus {("sinistrae","dextrae")[sidx]}')
        return NP(de_nom, de_gen, la_n, base.la_gen.replace(' pedis', f' pedis {("sinistri","dextri")[sidx]}').replace(' manus', f' manus {("sinistrae","dextrae")[sidx]}'))
    m = re.match(r'^proper palmar digital vein of (left|right) (.+)$', t)
    if m:
        sidx = 0 if m.group(1)=='left' else 1; dde, dla = DIGIT[m.group(2)]
        base = build('eigentlich', 'Hohlhand-Fingervene', 'f', 'Vena digitalis palmaris propria')
        tail_de = f' des {("linken","rechten")[sidx]} {dde}'; tail_la = f' {dla} {("sinistri","dextri")[sidx]}'
        return NP(base.de_nom + tail_de, base.de_gen + tail_de, base.la_nom + tail_la, base.la_gen + tail_la)
    m = re.match(r'^trunk of (.+)$', t)
    if m:
        p = parse(m.group(1))
        return NP(f'Stamm {p.de_gen}', f'des Stammes {p.de_gen}', f'Truncus {p.la_gen}', f'trunci {p.la_gen}')
    m = re.match(r'^ureteric segment of (.+)$', t)
    if m:
        p = parse(m.group(1))
        return NP(f'Harnleiterabschnitt {p.de_gen}', f'des Harnleiterabschnitts {p.de_gen}', f'Pars ureterica {p.la_gen}', f'partis uretericae {p.la_gen}')
    m = re.match(r'^tributary of (.+)$', t)
    if m:
        p = parse(m.group(1))
        return NP(f'Zufluss {p.de_gen}', f'des Zuflusses {p.de_gen}', f'Ramus {p.la_gen}', f'rami {p.la_gen}')
    m = re.match(r'^(.+?) (branch|division|tributary) of (.+)$', t)
    if m and m.group(2)=='tributary' and m.group(1) in BR:
        st, pre, la = BR[m.group(1)]; p = parse(m.group(3))
        noun = pre + 'zufluss' if pre else 'Zufluss'
        de_nom = cap((de_adj(st,'m') + ' ' + noun).strip()) + ' ' + p.de_gen
        de_gen = 'des ' + (de_adj(st,'m',True) + ' ' + de_noun_gen(noun,'m')).strip() + ' ' + p.de_gen
        return NP(de_nom, de_gen, f'Ramus {la} {p.la_gen}', f'rami {la_gen(la,"m")} {p.la_gen}')
    if m and m.group(1) not in BR and m.group(1).startswith(('left ','right ')) and m.group(1).split(' ',1)[1] in BR:
        sd, mod = m.group(1).split(' ',1); st, pre, la = BR[mod]; p = parse(m.group(3))
        sidx = 0 if sd=='left' else 1
        st = ('link','recht')[sidx] + ' ' + st; la = la + ' ' + LA_SIDE['m'][sidx]
        noun = (pre + 'Ast') if pre.endswith('-') else (pre + ('ast' if pre else 'Ast'))
        de_nom = cap((de_adj(st,'m') + ' ' + noun).strip()) + ' ' + p.de_gen
        de_gen = 'des ' + (de_adj(st,'m',True) + ' ' + de_noun_gen(noun,'m')).strip() + ' ' + p.de_gen
        return NP(de_nom, de_gen, f'Ramus {la} {p.la_gen}', f'rami {la_gen(la,"m")} {p.la_gen}')
    if m and m.group(1) in BR:
        st, pre, la = BR[m.group(1)]; p = parse(m.group(3))
        noun = (pre + 'Ast') if pre.endswith('-') else (pre + ('ast' if pre else 'Ast'))
        de_nom = cap((de_adj(st,'m') + ' ' + noun).strip()) + ' ' + p.de_gen
        de_gen = 'des ' + (de_adj(st,'m',True) + ' ' + de_noun_gen(noun,'m')).strip() + ' ' + p.de_gen
        return NP(de_nom, de_gen, f'Ramus {la} {p.la_gen}', f'rami {la_gen(la,"m")} {p.la_gen}')
    m = re.match(r'^(.+?) part of (.+)$', t)
    if m and m.group(1) in PARTS:
        st, la = PARTS[m.group(1)]; p = parse(m.group(2))
        return NP(f'{cap(de_adj(st,"m"))} Teil {p.de_gen}', f'des {de_adj(st,"m",True)} Teils {p.de_gen}',
                  f'Pars {la} {p.la_gen}', f'partis {la_gen(la,"f")} {p.la_gen}')
    raise KeyError(t)

def translate(t):
    if t in FIXED: return FIXED[t]
    p = parse(t); return (p.de_nom, p.la_nom)

rows, missing = [], []
for t in terms:
    try:
        r = translate(t); rows.append({'english': t, 'german': r[0], 'latin': r[1], 'system': SYSTEM})
    except KeyError as e: missing.append(str(e))
print(len(rows), 'translated;', len(missing), 'missing', missing[:20])
with open(f'translate/atlas-de-{SYSTEM}.csv','w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=['english','german','latin','system']); w.writeheader(); w.writerows(rows)
json.dump(rows, open(f'translate/atlas-de-{SYSTEM}.json','w'), ensure_ascii=False, indent=1)
with open(f'translate/atlas-de-{SYSTEM}.md','w') as f:
    f.write(f'# Human Atlas – {SYSTEM} (Deutsch / Latein)\n\n| English | Deutsch (Latein) |\n|---|---|\n')
    for r in rows: f.write(f"| {r['english']} | {r['german']} ({r['latin']}) |\n")
