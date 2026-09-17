import json, re, sys
sys.path.insert(0, 'translate')
from info_classes import C

atlas = json.load(open('public/models/atlas.json'))
tr = json.load(open('public/models/atlas-de.json'))
DE = {c['id']: c['german'] for c in tr['concepts']}
SYS = {}
for p in atlas['parts']: SYS.setdefault(p['conceptId'], p['system'])
for c in atlas['concepts']:
    if c['id'] not in SYS:
        s = [SYS.get(e) for e in c['elements'] if SYS.get(e)]
        s = [SYS.get(p['conceptId']) for p in atlas['parts'] if p['id'] in set(c['elements'])] or s
        SYS[c['id']] = max(set(s), key=s.count) if s else None

# location hints from English name fragments
LOC = [
 (r'\b(hallucis|pedis|plantar|metatarsal|tarsal|calcaneal|toe|foot)\b','am Fuß'),(r'\b(pollicis|indicis|carpi|carpal|metacarpal|palmar|finger|thumb|hand|wrist)\b','an der Hand'),
 (r'\b(antebrachi|forearm|radial|ulnar|radius|ulna)','am Unterarm'),(r'\b(brachi|humer|arm|deltoid|biceps|triceps|anconeus)','am Oberarm'),
 (r'\b(scapul|clavic|shoulder|supraspinatus|infraspinatus|teres|subscapularis)','an der Schulter'),(r'\b(femor|thigh|vastus|gracilis|sartorius|adductor|pectineus|gluteus|gemellus|obturator|piriformis|quadratus femoris|iliac|hip|patell)','an Hüfte und Oberschenkel'),
 (r'\b(tibia|fibula|crur|leg|popliteal|gastrocnemius|soleus|plantaris|genicular|knee)','am Unterschenkel und Knie'),
 (r'\b(cervic|neck|hyoid|scalen|sternocleido|longus colli|thyroid|thyro|crico|aryten|laryn|vocal)','am Hals'),
 (r'\b(cranial|capitis|head|skull|facial|nasal|mandib|maxill|zygom|tempor|pariet|occipit|front|sphenoid|ethmoid|orbit|ocul|eye|palat|tongue|lingual|genio|hyo)','am Kopf'),
 (r'\b(thorac|intercostal|rib|costal|sternum|sternal|pectoral|serratus|chest|mediastin)','am Brustkorb'),
 (r'\b(abdomin|lumbar|lumborum|psoas|epigastric|mesenteric|colic|gastric|hepatic|splenic|renal|pancreat|ileal|celiac|coeliac)','im Bauchraum'),
 (r'\b(pelvi|sacral|pudend|perine|coccyg|levator ani|rectal|obturator|gluteal|prostat|penis|testic)','im Becken'),
 (r'\b(cerebr|cerebell|pontine|basilar|choroidal|callos|frontobasal|parietal artery|temporal artery|occipital artery|thalam|striate)','im Gehirn'),
 (r'\b(pulmon|bronch|lung|lobar|segmental|lingular)','in der Lunge'),(r'\b(coronary|cardiac|ventricular|interventricular|atrium|atrial|conus|marginal branch|diagonal)','am Herzen'),
]
def loc(en):
    for pat, l in LOC:
        if re.search(pat, en): return ' ' + l
    return ''

def classify(en, sysid):
    e = en.lower()
    if re.search(r'\b(anatomical|entity|cluster|organ part|organ region|organ component|organ zone|organ segment|organ chamber|continuity|heterogeneous|cardinal|physical|material|immaterial|set of|subdivision|portion of|tissue|organs$|organ$|solid organ|cavitated|parenchymatous|hollow tree|tree organ|conduit|boundary|junction$|anatomical line|anatomical lobe|anatomical space)\b', e): return 'abstract'
    if re.search(r'^(back|front|side) of|girdle|bony pelvis|rib cage|^skull$|skeleton|^(head|neck|trunk|thorax|chest|abdomen|pelvis|perineum|arm|forearm|hand|thigh|leg|foot|limb|face|cheek|hip|knee|wrist|shoulder|finger|thumb|toe|big toe|little toe|mediastinum|body wall|thoracic wall|chest wall|abdominal wall|pelvic wall)( proper)?$|^(left|right|upper|lower|free|anterior|posterior|superior|inferior|middle|lateral|medial) (head|neck|thorax|chest|abdomen|pelvis|arm|forearm|hand|thigh|leg|foot|limb|cheek|hip|knee|wrist|shoulder|finger|thumb|toe|mediastinum|chest wall|thoracic wall|abdominal wall|upper limb|lower limb|free upper limb|free lower limb|index finger|middle finger|ring finger|little finger|big toe|second toe|third toe|fourth toe|little toe|parietal part of head|pectoral part of chest|lateral chest wall|lateral superficial chest wall)$|segment of trunk|part of head|part of pelvis|part of chest|hairs$', e): return 'region'
    if 'bronchopulmonary' in e or 'pulmopleural' in e or re.search(r'\blung\b|lobe of lung|hemiliver', e) and 'liver' not in e: return 'lung'
    if 'tooth' in e or 'incisor' in e or 'canine' in e or 'molar' in e or 'gingiva' in e: return 'tooth'
    if 'intervertebral' in e and ('disk' in e or 'symphysis' in e): return 'disk'
    if 'vertebra' in e or e in ('atlas','axis','sacrum') or 'vertebral column' in e: return 'vertebra'
    if re.search(r'\brib\b|ribs|costal cartilage|rib cage', e): return 'rib'
    if 'cartilage' in e or 'conus elasticus' in e: return 'cartilage'
    if re.search(r'compartment', e): return 'compartment'
    if re.search(r'ligament|raphe|retinaculum|tendinous ring|linea alba|tendinous arch|symphysis|articular disk', e): return 'ligament'
    if re.search(r'tendon|iliotibial|fasciae latae', e): return 'tendon'
    if re.search(r'fascia|membrane|interosseous membrane', e) and 'muscle' not in e: return 'fascia'
    if re.search(r'coronary|conus artery|interventricular (branch|artery)|diagonal branch|marginal branch|ventricular branch|septal branch', e): return 'coronary'
    if 'aorta' in e and 'artery' not in e and 'branch' not in e: return 'aorta'
    if 'pulmonary artery' in e or 'pulmonary arterial' in e or ('segmental artery' in e and 'renal' not in e and 'hepatic' not in e) or 'lobar artery' in e or 'lingular artery' in e: return 'pulmonary_artery'
    if re.search(r'cerebr|cerebell|basilar|pontine|choroidal|callos|frontobasal|pericallosal|precuneal|paracentral|thalamo|communicating artery|carotid|vertebral artery|sulcus|temporal artery|occipital artery|parietal artery|prefrontal artery|splenial|angular gyrus', e) and ('arter' in e or 'branch' in e or 'part of' in e): return 'cerebral_artery'
    if re.search(r'arter|arch$|palmar arch|plantar arch|trunk$|brachiocephalic|costocervical|thyrocervical', e) and 'vein' not in e and 'venous' not in e and 'muscle' not in e and 'nerve' not in e and 'brain' not in e: return 'artery'
    if 'portal' in e or 'hepatovenous' in e or 'hepatic vein' in e and 'tributary' in e: return 'portal_vein'
    if 'pulmonary vein' in e or 'pulmonary venous' in e or 'segmental vein' in e or 'lobar vein' in e or 'lingular vein' in e or 'basal vein' in e: return 'pulmonary_vein'
    if 'cardiac vein' in e or 'coronary sinus' in e or 'interventricular vein' in e or 'vein of left ventricle' in e or 'vein of right ventricle' in e: return 'cardiac_vein'
    if re.search(r'femoral vein|popliteal vein|tibial vein|fibular vein|iliac vein|vena cava|brachial vein|axillary vein|subclavian vein|jugular vein', e): return 'deep_vein'
    if re.search(r'vein|venous|vena', e): return 'vein'
    if re.search(r'caudate nucleus|putamen|globus pallidus|basal gangli|striatum|amygdala', e): return 'basal_ganglia' if 'amygdala' not in e else 'limbic'
    if re.search(r'hippocamp|cingulate|parahippocampal|fornix|limbic|mammillary|septum of telencephalon|stria terminalis|archicortex', e): return 'limbic'
    if re.search(r'cerebellum|cerebellar|vermis|tentorium', e) and 'artery' not in e: return 'cerebellum'
    if re.search(r'pons|medulla oblongata|midbrain|brainstem|colliculus|tectum|peduncle of midbrain|interpeduncular|aqueduct|metencephalon|hindbrain|mesencephalon', e): return 'brainstem'
    if re.search(r'thalam|hypothalam|habenula|geniculate|tuber cinereum|diencephalon|epithalamus|lamina terminalis|stria medullaris', e): return 'diencephalon'
    if re.search(r'ventricle|foramen|choroid plexus|ventricular system|central canal', e) and 'heart' not in e and 'cardiac' not in e and 'wall of' not in e and 'cavity of' not in e and 'myocardium' not in e: return 'ventricle_brain'
    if re.search(r'dura|subarachnoid|meninx', e): return 'meninges'
    if re.search(r'optic|chiasm', e): return 'optic'
    if re.search(r'gyrus|cortex|lobe$|lobule|insula|corpus callosum|commissure|internal capsule|white matter|gray matter|telencephalon|forebrain|cerebral hemisphere|brain|neuraxis|nervous system|nucleus|decussation|neural|spinal cord|septum|hemisphere', e) and 'liver' not in e and 'thymus' not in e and 'lung' not in e and 'nasal' not in e: return 'brain'
    if re.search(r'nerve|ganglion|plexus', e): return 'nerve'
    if re.search(r'retina', e): return 'retina'
    if re.search(r'lacrimal|nasolacrimal', e) and 'bone' not in e: return 'lacrimal'
    if re.search(r'eyelid|tarsal plate|palpebra', e): return 'eyelid'
    if re.search(r'\bear\b', e): return 'ear'
    if re.search(r'cornea|sclera|choroid|iris|lens|vitreous|eyeball|ciliar|eye\b|orbit|corona ciliaris|rectus$|oblique$|extra-ocular|check ligament|trochlea of', e) and sysid in ('sensory','connective','muscular','nervous') and 'artery' not in e: return 'eye' if not re.search(r'rectus$|oblique$', e) else 'muscle'
    if re.search(r'bronch|trachea|respiratory tract|airway', e): return 'airway'
    if re.search(r'bronchopulmonary|lung|pulmopleural|lobe of lung|upper lobe|lower lobe|middle lobe', e): return 'lung'
    if re.search(r'laryn|epiglottis|vocal|arytenoid|crico|thyro-|thyrohyoid|thyroid cartilage|aryepiglot', e): return 'larynx'
    if re.search(r'nasal|nose|concha|septum of nose', e): return 'nose'
    if re.search(r'pharyn|constrictor|uvul|palat|faucial|tonsil', e): return 'pharynx' if 'pharyn' in e or 'constrictor' in e else 'mouth'
    if re.search(r'tongue|lingua|genioglossus|hyoglossus|\bmouth\b|\blip\b|\bjaw\b|\boral\b', e) and 'bone' not in e: return 'mouth'
    if re.search(r'salivary|sublingual|submandibular|parotid', e): return 'salivary'
    if re.search(r'esophag|oesophag', e): return 'esophagus'
    if 'stomach' in e or 'gastric' in e or 'gaster' in e: return 'stomach'
    if re.search(r'duoden|jejun|ileum|ileal|small intestine|ileocecal', e): return 'small_intestine'
    if re.search(r'colon|cecum|caec|taenia|large intestine|sigmoid|colic', e): return 'colon'
    if 'rect' in e or 'anal' in e: return 'rectum'
    if 'appendi' in e: return 'appendix'
    if re.search(r'liver|hepat|hemiliver', e): return 'liver' if 'bil' not in e and 'duct' not in e else 'biliary'
    if re.search(r'bile|biliar|gallbladder|cystic duct', e): return 'biliary'
    if 'pancrea' in e: return 'pancreas'
    if re.search(r'peritone|mesenter|mesocolon|mesoappendix|omentum', e): return 'peritoneum'
    if 'kidney' in e or 'renal' in e: return 'kidney'
    if 'ureter' in e: return 'ureter'
    if 'bladder' in e: return 'bladder'
    if 'urethra' in e or 'urinary' in e: return 'urethra'
    if 'testis' in e or 'testic' in e: return 'testis'
    if 'epididym' in e: return 'epididymis'
    if re.search(r'deferent|seminal|genital|spermatic', e): return 'genital_duct'
    if 'prostat' in e: return 'prostate'
    if 'penis' in e or 'cavernos' in e or 'spongios' in e: return 'penis'
    if 'adrenal' in e or 'suprarenal' in e: return 'adrenal'
    if 'pituitary' in e or 'hypophys' in e: return 'pituitary'
    if 'pineal' in e: return 'pineal'
    if 'spleen' in e or 'splen' in e: return 'spleen'
    if 'thymus' in e: return 'thymus'
    if re.search(r'valve|cusp|leaflet|fibrous ring|tendinous cord|papillary muscle|chordae', e): return 'valve'
    if re.search(r'heart|atrium|atrial|ventricle|ventricular|myocard|endocard|pericard|septum of heart|cardiac', e): return 'heart_chamber'
    if re.search(r'skin|epidermis|integument|cutis', e): return 'skin'
    if 'hair' in e or 'eyebrow' in e or 'pubic' in e: return 'hair'
    if 'lip' == e or e.endswith(' lip'): return 'lip'
    if re.search(r'bone|skeleton|skull|cranium|sternum|manubrium|xiphoid|scapula|clavicle|humerus|radius|ulna|femur|patella|tibia|fibula|talus|calcaneus|navicular|cuboid|cuneiform|hamate|capitate|lunate|pisiform|scaphoid|trapezium|trapezoid|triquetral|phalanx|metacarpal|metatarsal|maxilla|mandible|vomer|ethmoid|sphenoid|hyoid|pelvis|girdle|carpal|tarsal', e): return 'bone'
    if re.search(r'muscl|musculature|head of|part of (left |right )?(pectoralis|deltoid|trapezius|flexor|pronator|longus colli|cricothyroid)|belly', e) or sysid == 'muscular': return 'muscle'
    if sysid == 'skeletal': return 'bone'
    if sysid == 'arterial': return 'artery'
    if sysid == 'venous': return 'vein'
    if sysid == 'nervous': return 'brain'
    if sysid == 'respiratory': return 'airway'
    if sysid == 'digestive': return 'small_intestine'
    if sysid == 'connective': return 'ligament'
    return 'region'

# curated descriptions for major structures (english name -> German description); class inherits from classifier
CUR = {
 'heart':'Das Herz ist ein faustgroßer Hohlmuskel im Brustkorb. Die rechte Hälfte pumpt sauerstoffarmes Blut in die Lunge, die linke Hälfte sauerstoffreiches Blut in den Körper – rund 100 000 Schläge pro Tag.',
 'brain':'Das Gehirn ist das Steuerorgan des Körpers. Großhirn, Kleinhirn und Hirnstamm verarbeiten Sinneseindrücke, steuern Bewegung, Sprache, Gedächtnis, Gefühle und lebenswichtige Funktionen wie Atmung und Herzschlag.',
 'liver':'Die Leber ist mit etwa 1,5 kg das größte innere Organ. Sie verstoffwechselt Nährstoffe, entgiftet Blut, bildet Galle, Gerinnungsfaktoren und Bluteiweiße und speichert Glykogen, Eisen und Vitamine.',
 'stomach':'Der Magen ist ein dehnbarer Muskelsack zwischen Speiseröhre und Zwölffingerdarm. Magensäure und Enzyme beginnen die Eiweißverdauung und töten Keime ab.',
 'spleen':'Die Milz liegt im linken Oberbauch unter dem Zwerchfell. Sie filtert das Blut, baut alte rote Blutkörperchen ab und ist eine wichtige Station der Immunabwehr.',
 'pancreas':'Die Bauchspeicheldrüse liegt quer hinter dem Magen. Sie liefert täglich etwa 1,5 Liter Verdauungssekret in den Zwölffingerdarm und bildet die Blutzuckerhormone Insulin und Glukagon.',
 'urinary bladder':'Die Harnblase ist ein muskulöser Speicher im kleinen Becken für etwa 300–500 ml Harn. Ihre Dehnung löst den Harndrang aus.',
 'trachea':'Die Luftröhre ist ein etwa 12 cm langes, von Knorpelspangen offen gehaltenes Rohr zwischen Kehlkopf und Hauptbronchien. Flimmerhärchen befördern Schleim und Staub nach oben.',
 'diaphragm':'Das Zwerchfell ist der wichtigste Atemmuskel. Die Kuppel trennt Brust- und Bauchraum; zieht sie sich zusammen, strömt Luft in die Lunge.',
 'left kidney':'Die linke Niere liegt etwas höher als die rechte hinter dem Bauchfell. Jede Niere filtert täglich rund 180 Liter Primärharn und regelt Wasser-, Salz- und Säure-Basen-Haushalt.',
 'right kidney':'Die rechte Niere liegt unter der Leber und daher etwas tiefer als die linke. Jede Niere filtert täglich rund 180 Liter Primärharn und regelt Wasser-, Salz- und Säure-Basen-Haushalt.',
 'esophagus':'Die Speiseröhre ist ein etwa 25 cm langer Muskelschlauch. Wellenförmige Kontraktionen befördern den Bissen in wenigen Sekunden in den Magen; der untere Schließmuskel verhindert Rückfluss.',
 'duodenum':'Der Zwölffingerdarm ist der C-förmige erste Dünndarmabschnitt. Hier münden Galle und Bauchspeichel und neutralisieren den sauren Magenbrei.',
 'rectum':'Der Mastdarm ist der letzte, etwa 15 cm lange Darmabschnitt. Er speichert den Stuhl; Schließmuskeln steuern die Entleerung.',
 'appendix':'Der Wurmfortsatz ist ein fingerförmiger Anhang des Blinddarms mit viel lymphatischem Gewebe – ein Reservoir für nützliche Darmbakterien.',
 'gallbladder':'Die Gallenblase speichert und konzentriert Galle aus der Leber und gibt sie nach fettreichen Mahlzeiten in den Zwölffingerdarm ab.',
 'tongue':'Die Zunge ist ein beweglicher Muskelkörper mit Geschmacksknospen. Sie formt den Bissen, leitet das Schlucken ein und ist für die Sprache unverzichtbar.',
 'prostate':'Die Prostata ist eine kastaniengroße Drüse unter der Harnblase, die die Harnröhre umschließt. Ihr Sekret macht etwa ein Drittel der Samenflüssigkeit aus.',
 'pituitary gland':'Die Hirnanhangsdrüse ist die erbsengroße Zentrale des Hormonsystems an der Schädelbasis. Sie steuert Schilddrüse, Nebennieren, Keimdrüsen, Wachstum und Wasserhaushalt.',
 'pineal body':'Die Zirbeldrüse im Zwischenhirn bildet nachts das Schlafhormon Melatonin und stimmt den Körper auf den Tag-Nacht-Rhythmus ab.',
 'left adrenal gland':'Die linke Nebenniere sitzt wie eine Kappe auf der Niere. Ihre Rinde bildet Cortisol, Aldosteron und Androgene, das Mark Adrenalin und Noradrenalin.',
 'right adrenal gland':'Die rechte Nebenniere sitzt wie eine Kappe auf der Niere. Ihre Rinde bildet Cortisol, Aldosteron und Androgene, das Mark Adrenalin und Noradrenalin.',
 'left lung':'Die linke Lunge hat zwei Lappen und ist wegen des Herzens etwas kleiner als die rechte. In ihren Lungenbläschen findet der Gasaustausch statt.',
 'right lung':'Die rechte Lunge hat drei Lappen und ist die größere der beiden Lungen. In etwa 300 Millionen Lungenbläschen findet der Gasaustausch statt.',
 'left testis':'Der linke Hoden hängt meist etwas tiefer als der rechte. Die Hoden bilden Spermien und Testosteron; ihre Lage außerhalb des Körpers hält sie kühler.',
 'right testis':'Der rechte Hoden liegt im Hodensack. Die Hoden bilden Spermien und Testosteron; ihre Lage außerhalb des Körpers hält sie kühler.',
 'cerebellum':'Das Kleinhirn liegt unter dem Hinterhauptslappen. Es enthält mehr Nervenzellen als das Großhirn und feinsteuert Bewegung, Gleichgewicht und Koordination.',
 'hypothalamus':'Der Hypothalamus ist die Schaltzentrale für Hunger, Durst, Körpertemperatur, Schlaf und Hormone. Er verbindet Nervensystem und Hormonsystem über die Hypophyse.',
 'thalamus':'Der Thalamus ist das „Tor zum Bewusstsein“: Fast alle Sinnesinformationen werden hier gefiltert und an die Großhirnrinde weitergeleitet.',
 'hippocampus':'Der Hippocampus im Schläfenlappen überführt neue Erlebnisse ins Langzeitgedächtnis und orientiert uns im Raum. Er ist bei Alzheimer früh betroffen.',
 'amygdala':'Der Mandelkern bewertet Reize emotional, vor allem Angst und Bedrohung, und löst Stressreaktionen aus.',
 'corpus callosum':'Der Balken ist die größte Faserbrücke des Gehirns mit rund 200 Millionen Nervenfasern. Er verbindet linke und rechte Großhirnhälfte.',
 'pons':'Die Brücke ist der mittlere Teil des Hirnstamms. Sie leitet Signale zwischen Großhirn und Kleinhirn und steuert Atmung, Schlaf und Gesichtsnerven.',
 'medulla oblongata':'Das verlängerte Mark ist der Übergang zum Rückenmark. Hier liegen die Zentren für Atmung, Herzschlag, Blutdruck, Schlucken und Husten.',
 'midbrain':'Das Mittelhirn verbindet Zwischenhirn und Brücke. Es steuert Augenbewegungen, Reflexe auf Licht und Schall und enthält die Substantia nigra (Dopamin).',
 'caudate nucleus':'Der Schweifkern ist Teil der Basalganglien. Er wirkt an Bewegungsplanung, Lernen und Belohnung mit.',
 'putamen':'Das Putamen ist ein Kern der Basalganglien und steuert vor allem automatisierte Bewegungsabläufe.',
 'globus pallidus':'Das Pallidum gibt die Signale der Basalganglien an den Thalamus weiter und bremst überschießende Bewegungen; Zielstruktur der tiefen Hirnstimulation.',
 'optic nerve':'Der Sehnerv bündelt rund eine Million Nervenfasern der Netzhaut und leitet die Bildinformation zur Sehnervenkreuzung.',
 'optic chiasm':'In der Sehnervenkreuzung wechseln die Fasern der nasalen Netzhauthälften die Seite – so sieht jede Hirnhälfte das gegenüberliegende Gesichtsfeld.',
 'spinal cord':'Das Rückenmark verläuft im Wirbelkanal und verbindet Gehirn und Körper. Es leitet Empfindungen und Bewegungsbefehle und steuert Reflexe.',
 'left eye':'Das linke Auge. Hornhaut und Linse bündeln das Licht auf der Netzhaut; der Sehnerv leitet das Bild ins Gehirn.',
 'right eye':'Das rechte Auge. Hornhaut und Linse bündeln das Licht auf der Netzhaut; der Sehnerv leitet das Bild ins Gehirn.',
 'cornea':'Die Hornhaut ist das klare Fenster des Auges und übernimmt etwa zwei Drittel der Lichtbrechung. Sie ist gefäßlos und sehr schmerzempfindlich.',
 'lens':'Die Linse ist elastisch und wird vom Ziliarmuskel verformt, um scharf zu stellen. Mit dem Alter verliert sie an Elastizität und kann sich eintrüben (Katarakt).',
 'iris':'Die Regenbogenhaut regelt wie eine Blende die Pupillenweite und bestimmt die Augenfarbe.',
 'sclera':'Die Lederhaut ist die weiße, feste Außenhülle des Augapfels, an der die Augenmuskeln ansetzen.',
 'choroid':'Die Aderhaut versorgt die äußeren Netzhautschichten mit Blut und verhindert mit ihrem Pigment Streulicht.',
 'vitreous body':'Der Glaskörper ist eine klare, gelartige Masse, die den Augapfel füllt und die Netzhaut an Ort und Stelle hält.',
 'left main bronchus':'Der linke Hauptbronchus ist länger und verläuft flacher als der rechte. Er teilt sich in die Bronchien der beiden linken Lungenlappen.',
 'right main bronchus':'Der rechte Hauptbronchus ist kürzer und steiler als der linke – verschluckte Fremdkörper landen daher meist rechts. Er versorgt drei Lungenlappen.',
 'epiglottis':'Der Kehldeckel ist eine Knorpelklappe, die beim Schlucken den Kehlkopfeingang verschließt und Nahrung von der Luftröhre fernhält.',
 'thyroid cartilage':'Der Schildknorpel ist der größte Kehlkopfknorpel und bildet den Adamsapfel. An ihm sind die Stimmlippen befestigt.',
 'cricoid cartilage':'Der Ringknorpel ist der einzige vollständige Knorpelring der Atemwege und die Basis des Kehlkopfs.',
 'hyoid bone':'Das Zungenbein ist der einzige Knochen ohne Gelenkverbindung zum übrigen Skelett. Es trägt die Zunge und den Kehlkopf.',
 'mandible':'Der Unterkiefer ist der größte und stärkste Gesichtsknochen und der einzige bewegliche Schädelknochen. Er trägt die unteren Zähne.',
 'frontal bone':'Das Stirnbein bildet Stirn und Dach der Augenhöhlen und enthält die Stirnhöhlen.',
 'occipital bone':'Das Hinterhauptbein bildet den hinteren Schädel und umschließt das große Hinterhauptloch, durch das das Rückenmark tritt.',
 'sphenoid bone':'Das Keilbein liegt zentral in der Schädelbasis. Seine Sattelgrube (Sella turcica) beherbergt die Hirnanhangsdrüse.',
 'ethmoid':'Das Siebbein liegt zwischen den Augenhöhlen. Seine Siebplatte leitet die Riechnerven, seine Zellen gehören zu den Nasennebenhöhlen.',
 'vomer':'Das Pflugscharbein bildet den hinteren unteren Teil der Nasenscheidewand.',
 'sacrum':'Das Kreuzbein besteht aus fünf verschmolzenen Wirbeln und verbindet die Wirbelsäule über die Iliosakralgelenke mit dem Becken.',
 'atlas':'Der Atlas ist der erste Halswirbel. Er trägt den Schädel und ermöglicht das Nicken.',
 'axis':'Der Axis ist der zweite Halswirbel. Sein Zahn (Dens) bildet die Drehachse für das Kopfschütteln.',
 'body of sternum':'Der Brustbeinkörper ist der mittlere Teil des Brustbeins, an dem die Rippenknorpel 2–7 ansetzen.',
 'manubrium':'Der Brustbeingriff ist der obere Teil des Brustbeins; hier setzen Schlüsselbeine und erste Rippen an.',
 'xiphoid process':'Der Schwertfortsatz ist der knorpelige untere Zipfel des Brustbeins – Orientierungspunkt bei der Herzdruckmassage.',
 'skin':'Die Haut ist mit etwa 2 m² das größte Organ. Oberhaut, Lederhaut und Unterhaut schützen vor Austrocknung, Keimen und UV-Licht, regeln die Temperatur und nehmen Berührung, Schmerz und Wärme wahr.',
 'hair of head':'Das Kopfhaar besteht aus etwa 100 000 Keratinfasern. Es schützt die Kopfhaut vor Sonne und Kälte; täglich fallen 50–100 Haare aus.',
 'eyebrow':'Die Augenbraue lenkt Schweiß und Regen vom Auge ab und ist wichtig für den Gesichtsausdruck.',
 'lip':'Die Lippen bestehen aus dem Ringmuskel des Mundes und einer dünnen, gefäßreichen Haut. Sie halten Nahrung im Mund, formen Laute und sind sehr berührungsempfindlich.',
 'pubic hair':'Die Schambehaarung entwickelt sich in der Pubertät unter dem Einfluss von Androgenen und schützt die empfindliche Haut vor Reibung.',
 'left lobe of thymus':'Der linke Thymuslappen. Der Thymus hinter dem Brustbein prägt in Kindheit und Jugend die T-Zellen des Immunsystems und verfettet später.',
 'right lobe of thymus':'Der rechte Thymuslappen. Der Thymus hinter dem Brustbein prägt in Kindheit und Jugend die T-Zellen des Immunsystems und verfettet später.',
 'ascending aorta':'Die aufsteigende Aorta entspringt der linken Herzkammer. Von ihr gehen die beiden Herzkranzarterien ab.',
 'arch of aorta':'Der Aortenbogen gibt die Arterien für Kopf, Hals und Arme ab: Truncus brachiocephalicus, linke Halsschlagader und linke Schlüsselbeinarterie.',
 'abdominal aorta':'Die Bauchaorta versorgt Bauchorgane, Nieren und Beine. Unterhalb des Nabels teilt sie sich in die beiden Beckenarterien.',
 'pulmonary trunk':'Der Lungenstamm entspringt der rechten Herzkammer und teilt sich in die rechte und linke Lungenarterie – die einzigen Arterien mit sauerstoffarmem Blut.',
 'superior vena cava':'Die obere Hohlvene sammelt das Blut aus Kopf, Hals, Armen und Brustwand und mündet in den rechten Vorhof.',
 'inferior vena cava':'Die untere Hohlvene ist die größte Vene des Körpers. Sie führt das Blut aus Beinen, Becken und Bauch zum rechten Vorhof.',
 'hepatic portal vein':'Die Pfortader bringt nährstoffreiches Blut aus Magen, Darm, Milz und Bauchspeicheldrüse zur Leber, bevor es in den Kreislauf gelangt.',
 'left coronary artery':'Die linke Herzkranzarterie versorgt den Großteil der linken Herzkammer und der Kammerscheidewand. Ihr Hauptstamm teilt sich in den vorderen absteigenden Ast und den Ramus circumflexus.',
 'right coronary artery':'Die rechte Herzkranzarterie versorgt die rechte Herzkammer, die Hinterwand und meist Sinus- und AV-Knoten – Ausfälle stören daher oft den Herzrhythmus.',
 'left internal carotid artery':'Die linke innere Halsschlagader führt durch die Schädelbasis ins Gehirn und speist die vordere und mittlere Hirnarterie.',
 'right internal carotid artery':'Die rechte innere Halsschlagader führt durch die Schädelbasis ins Gehirn und speist die vordere und mittlere Hirnarterie.',
 'basilar artery':'Die Basilararterie entsteht aus beiden Wirbelarterien und versorgt Hirnstamm, Kleinhirn und Hinterhauptslappen.',
 'left middle cerebral artery':'Die linke mittlere Hirnarterie versorgt große Teile des Großhirns einschließlich der Sprachzentren. Ihr Verschluss ist die häufigste Schlaganfallursache.',
 'right middle cerebral artery':'Die rechte mittlere Hirnarterie versorgt große Teile des Großhirns einschließlich der Zentren für räumliche Aufmerksamkeit. Ihr Verschluss ist eine häufige Schlaganfallursache.',
 'left femoral artery':'Die linke Oberschenkelarterie ist die Hauptschlagader des Beins; sie ist in der Leiste tastbar und Zugangsweg für Herzkatheter.',
 'right femoral artery':'Die rechte Oberschenkelarterie ist die Hauptschlagader des Beins; sie ist in der Leiste tastbar und Zugangsweg für Herzkatheter.',
 'left great saphenous vein':'Die große Rosenvene ist die längste Vene des Körpers. Sie verläuft oberflächlich an der Innenseite des Beins und ist häufigster Ort von Krampfadern.',
 'right great saphenous vein':'Die große Rosenvene ist die längste Vene des Körpers. Sie verläuft oberflächlich an der Innenseite des Beins und ist häufigster Ort von Krampfadern.',
 'left femur':'Der linke Oberschenkelknochen ist der längste und stärkste Knochen des Körpers. Sein Hals ist bei Osteoporose typische Bruchstelle.',
 'right femur':'Der rechte Oberschenkelknochen ist der längste und stärkste Knochen des Körpers. Sein Hals ist bei Osteoporose typische Bruchstelle.',
 'left patella':'Die linke Kniescheibe ist das größte Sesambein. Sie ist in die Quadrizepssehne eingelagert und verbessert deren Hebelwirkung.',
 'right patella':'Die rechte Kniescheibe ist das größte Sesambein. Sie ist in die Quadrizepssehne eingelagert und verbessert deren Hebelwirkung.',
 'left clavicle':'Das linke Schlüsselbein verbindet Brustbein und Schulterblatt und ist der am häufigsten gebrochene Knochen bei Stürzen.',
 'right clavicle':'Das rechte Schlüsselbein verbindet Brustbein und Schulterblatt und ist der am häufigsten gebrochene Knochen bei Stürzen.',
 'left hip bone':'Das linke Hüftbein entsteht aus Darmbein, Sitzbein und Schambein und bildet mit dem Kreuzbein den Beckenring.',
 'right hip bone':'Das rechte Hüftbein entsteht aus Darmbein, Sitzbein und Schambein und bildet mit dem Kreuzbein den Beckenring.',
 'left calcaneal tendon':'Die linke Achillessehne ist die dickste und stärkste Sehne des Körpers. Sie überträgt die Kraft der Wadenmuskeln auf das Fersenbein.',
 'right calcaneal tendon':'Die rechte Achillessehne ist die dickste und stärkste Sehne des Körpers. Sie überträgt die Kraft der Wadenmuskeln auf das Fersenbein.',
 'left gluteus maximus':'Der linke große Gesäßmuskel ist der kräftigste Muskel des Körpers. Er streckt die Hüfte beim Aufstehen, Treppensteigen und Laufen.',
 'right gluteus maximus':'Der rechte große Gesäßmuskel ist der kräftigste Muskel des Körpers. Er streckt die Hüfte beim Aufstehen, Treppensteigen und Laufen.',
 'left sartorius':'Der linke Schneidermuskel ist der längste Muskel des Körpers. Er beugt Hüfte und Knie – die Bewegung des Beinüberschlagens.',
 'right sartorius':'Der rechte Schneidermuskel ist der längste Muskel des Körpers. Er beugt Hüfte und Knie – die Bewegung des Beinüberschlagens.',
 'left sternocleidomastoid':'Der linke Kopfwender dreht den Kopf zur Gegenseite und neigt ihn zur gleichen Seite. Er ist die sichtbare Muskelleiste am Hals.',
 'right sternocleidomastoid':'Der rechte Kopfwender dreht den Kopf zur Gegenseite und neigt ihn zur gleichen Seite. Er ist die sichtbare Muskelleiste am Hals.',
 'left soleus':'Der linke Schollenmuskel liegt unter dem Zwillingswadenmuskel. Er hält uns im Stehen aufrecht und pumpt als „Muskelpumpe“ Venenblut zum Herzen.',
 'right soleus':'Der rechte Schollenmuskel liegt unter dem Zwillingswadenmuskel. Er hält uns im Stehen aufrecht und pumpt als „Muskelpumpe“ Venenblut zum Herzen.',
 'left psoas major':'Der linke große Lendenmuskel ist der wichtigste Hüftbeuger und verbindet Lendenwirbelsäule und Oberschenkel. Verkürzung durch Sitzen begünstigt Rückenschmerzen.',
 'right psoas major':'Der rechte große Lendenmuskel ist der wichtigste Hüftbeuger und verbindet Lendenwirbelsäule und Oberschenkel. Verkürzung durch Sitzen begünstigt Rückenschmerzen.',
 'left external oblique':'Der linke äußere schräge Bauchmuskel dreht und beugt den Rumpf und erhöht den Bauchinnendruck beim Husten, Pressen und Ausatmen.',
 'right external oblique':'Der rechte äußere schräge Bauchmuskel dreht und beugt den Rumpf und erhöht den Bauchinnendruck beim Husten, Pressen und Ausatmen.',
 'left serratus anterior':'Der linke vordere Sägemuskel zieht das Schulterblatt nach vorn und ermöglicht das Heben des Arms über die Horizontale.',
 'right serratus anterior':'Der rechte vordere Sägemuskel zieht das Schulterblatt nach vorn und ermöglicht das Heben des Arms über die Horizontale.',
 'linea alba':'Die weiße Linie ist die sehnige Naht in der Mitte der Bauchwand, an der sich die Bauchmuskeln kreuzen. Sie kann bei Schwangerschaft oder Übergewicht auseinanderweichen (Rektusdiastase).',
 'lateral ventricle':'Die Seitenventrikel sind die beiden größten Hirnkammern in den Großhirnhälften. Ihre Adergeflechte bilden den Großteil des Liquors.',
 'third ventricle':'Der dritte Ventrikel ist ein schmaler Spalt im Zwischenhirn zwischen beiden Thalami.',
 'fourth ventricle':'Der vierte Ventrikel liegt zwischen Hirnstamm und Kleinhirn. Von hier fließt der Liquor in den Subarachnoidalraum.',
 'cerebral aqueduct':'Die Hirnwasserleitung ist der engste Abschnitt des Ventrikelsystems durch das Mittelhirn – häufigste Engstelle bei Hydrozephalus.',
 'mitral valve':'Die Mitralklappe zwischen linkem Vorhof und linker Kammer hat zwei Segel. Sie ist die am häufigsten erkrankte Herzklappe (Insuffizienz, Prolaps).',
 'aortic valve':'Die Aortenklappe hat drei Taschen und öffnet sich bei jedem Herzschlag zur Aorta. Ihre Verengung im Alter ist der häufigste Klappenfehler.',
 'tricuspid valve':'Die Trikuspidalklappe zwischen rechtem Vorhof und rechter Kammer hat drei Segel.',
 'pulmonary valve':'Die Pulmonalklappe leitet das Blut aus der rechten Kammer in den Lungenstamm.',
 'coronary sinus':'Der Koronarsinus sammelt das venöse Blut des Herzmuskels und mündet in den rechten Vorhof.',
 'left ventricle':'Die linke Herzkammer hat die dickste Wand, weil sie das Blut mit hohem Druck in den gesamten Körper pumpt.',
 'right ventricle':'Die rechte Herzkammer pumpt sauerstoffarmes Blut mit niedrigem Druck in die Lunge.',
 'left atrium':'Der linke Vorhof empfängt sauerstoffreiches Blut aus den vier Lungenvenen. Hier entsteht meist das Vorhofflimmern.',
 'right atrium':'Der rechte Vorhof empfängt das venöse Blut aus beiden Hohlvenen und enthält den Sinusknoten, den natürlichen Taktgeber des Herzens.',
 'peritoneum':'Das Bauchfell kleidet die Bauchhöhle aus und überzieht die Organe. Zwischen beiden Blättern liegt ein Gleitfilm, der reibungsarme Darmbewegung erlaubt.',
 'cranial dura mater':'Die harte Hirnhaut ist die äußerste, derbe Hirnhülle. Zwischen ihr und dem Schädel bzw. der Spinnwebenhaut können sich Blutungen ausbreiten.',
 'subarachnoid space':'Der Subarachnoidalraum zwischen Spinnwebenhaut und weicher Hirnhaut ist mit Liquor gefüllt und führt die großen Hirnarterien.',
 'internal capsule':'Die innere Kapsel ist die Engstelle, durch die fast alle Fasern zwischen Großhirnrinde und Körper laufen. Kleine Blutungen hier verursachen halbseitige Lähmungen.',
 'insula':'Die Inselrinde liegt verborgen in der Tiefe der Seitenfurche. Sie verarbeitet Geschmack, Körperempfindungen, Schmerz und Gefühle.',
 'precentral gyrus':'Die vordere Zentralwindung ist die primäre motorische Rinde: Jeder Körperteil hat hier sein Steuerfeld (Homunculus).',
 'postcentral gyrus':'Die hintere Zentralwindung ist die primäre somatosensorische Rinde, die Berührung, Druck und Lage des Körpers verarbeitet.',
 'occipital lobe':'Der Hinterhauptslappen enthält die Sehrinde, in der die Signale der Netzhaut zu Bildern verarbeitet werden.',
 'cingulate gyrus':'Die Gürtelwindung über dem Balken gehört zum limbischen System und verbindet Emotion, Aufmerksamkeit und Schmerzbewertung.',
}

items = {}
for c in atlas['concepts']:
    en = c['name'].lower(); de = DE.get(c['id'], c['name'])
    cls = classify(en, SYS.get(c['id']))
    d = CUR.get(en) or C[cls]['d'].format(n='Diese Struktur', loc=loc(en))
    items[c['id']] = {'c': cls, 'd': d}
classes = {k: {'nu': v['nu'], 'su': v['su'], 'di': v['di']} for k, v in C.items()}
json.dump({'language': 'de', 'classes': classes, 'items': items}, open('public/models/info-de.json', 'w'), ensure_ascii=False, separators=(',', ':'))
import collections
print(len(items), 'items;', 'curated', sum(1 for c in atlas['concepts'] if c['name'].lower() in CUR))
print(collections.Counter(v['c'] for v in items.values()).most_common())
