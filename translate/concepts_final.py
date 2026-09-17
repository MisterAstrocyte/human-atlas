import json, re, sys, io, contextlib, csv
sys.path.insert(0, 'translate')
from topo_vocab import B, NOUN_GEN as TNG
exec(open('translate/concepts_pass1.py').read().split('# ---- pass 2')[0].replace("print(len(done)", "#"))
# reuse: try_all, ve (vessel engine), done dict of covered terms; recompute pass2
exec('\n'.join(l for l in open('translate/concepts_pass1.py').read().split('# ---- pass 2')[1].split('\n')[1:] if not l.startswith('print(') and not l.startswith('json.dump') and not l.startswith('open(')))
todo = todo2

NOM_END = {'m':'er','f':'e','n':'es','p':'e'}; ART = {'m':'des','f':'der','n':'des','p':'der'}
def cap(s): return s[0].upper()+s[1:]
def de_adj(st, g, gen=False): return ' '.join(s+('en' if gen else NOM_END[g]) for s in st.split() if s)
def ngen(noun, g):
    if g in ('f','p'): return noun
    if noun in TNG: return TNG[noun]
    if ' ' in noun:  # "Teil des Krummdarms" -> genitive on first word
        h, r = noun.split(' ',1); return ngen(h,g)+' '+r
    if noun.endswith(('el','er','en')): return noun+'s'
    if noun.endswith(('s','ß','x','z')): return noun+'es'
    return noun+'s'

class NP:
    def __init__(s,dn,dg,ln,lg): s.de_nom,s.de_gen,s.la_nom,s.la_gen=dn,dg,ln,lg

SIDE_LA = {'m':('sinister','dexter','sinistri','dextri'),'f':('sinistra','dextra','sinistrae','dextrae'),
           'n':('sinistrum','dextrum','sinistri','dextri'),'p':('sinistrae','dextrae','sinistrarum','dextrarum')}
LA_G = {'ventricle':'m','ventricle proper':'m','atrium':'n','heart':'n','side of heart':'n','eye':'m','eyeball':'m','foot':'m','foot proper':'m',
 'hand':'f','hand proper':'f','thigh':'n','knee':'n','leg':'n','arm':'n','forearm':'n','wrist':'m','hip':'f','lung':'m','liver':'n','shoulder':'f',
 'upper limb':'n','lower limb':'n','free upper limb':'f','free lower limb':'f','thumb':'m','index finger':'m','middle finger':'m','ring finger':'m',
 'little finger':'m','big toe':'m','second toe':'m','third toe':'m','fourth toe':'m','little toe':'m','cheek':'f','frontal lobe':'m','cerebral hemisphere':'n',
 'pectoral girdle':'n','pelvic girdle':'n','bronchial tree':'f','hepatic biliary tree':'f','lacrimal duct':'m','side of internal nose':'n','pectoralis major':'m',
 'posterior choroidal artery':'f','costocervical artery':'m','thyrocervical artery':'m','deep femoral artery':'f','papillary muscle of left ventricle':'m',
 'lateral papillary muscle of left ventricle':'m','investing fascia':'f','fascia lata':'f','knee':'n','liver (in-vivo)':'n'}
def base(t):
    """Noun phrase for a base term, with optional leading side."""
    side = None
    m = re.match(r'^(left|right) (.+)$', t)
    if m and m.group(2) in B: side = 0 if m.group(1)=='left' else 1; t = m.group(2)
    if t in B:
        st, noun, g, ln, lg = B[t]
        st2 = (('link','recht')[side]+' '+st).strip() if side is not None else st
        dn = cap((de_adj(st2,g)+' '+noun).strip()); dg = ART[g]+' '+(de_adj(st2,g,True)+' '+ngen(noun,g)).strip()
        if side is not None:
            sl = SIDE_LA[LA_G.get(t, g)]; ln = f'{ln} {sl[side]}'; lg = f'{lg} {sl[2+side]}'
        return NP(dn, dg, ln, lg)
    # vessel engine gives full genitives
    try:
        p = ve['parse'](t); return NP(p.de_nom, p.de_gen, p.la_nom, p.la_gen)
    except Exception: pass
    # last resort: covered term nominative + heuristic genitive
    r = done.get(t) or try_all(t)
    if r:
        dn, ln = r
        fem = dn.split()[-1].endswith(('e','ie','ung','ader','arterie','vene','haut','drüse','muskeln'))
        g = 'f' if fem else 'm'
        words = dn.split(); adjs = [w for w in words[:-1]]; noun = words[-1]
        dg = ART[g]+' '+' '.join([re.sub(r'(er|es|e)$','en',w.lower()) if not w[0].isupper() or i==0 and len(words)>1 and w.endswith(('er','es','e')) else w for i,w in enumerate(adjs)]+[ngen(noun,g)])
        lg = ve['la_gen'](ln, 'f')
        return NP(dn, dg, ln, lg)
    raise KeyError(t)

# relation -> (german head, german gender, latin head)  ("{gen}" = genitive of the base)
REL = {
 'muscle':('Muskel','m','Musculus'), 'musculature':('Muskulatur','f','Musculatura'), 'segment':('Segment','n','Segmentum'),
 'subdivision':('Unterabschnitt','m','Subdivisio'), 'zone':('Zone','f','Zona'), 'region':('Region','f','Regio'),
 'wall':('Wand','f','Paries'), 'content':('Inhalt','m','Contentum'), 'branch':('Ast','m','Ramus'), 'tributary':('Zufluss','m','Ramus'),
 'trunk of branch':('Stamm eines Astes','m','Truncus rami'), 'skeleton':('Skelett','n','Sceletum'), 'cortex':('Rinde','f','Cortex'),
 'subcortex':('Subkortex','m','Subcortex'), 'myocardium':('Myokard','n','Myocardium'), 'investing fascia':('Hüllfaszie','f','Fascia investiens'),
 'subsegmental part':('Subsegmentaler Teil','m','Pars subsegmentalis'), 'intrapulmonary part':('Intrapulmonaler Teil','m','Pars intrapulmonalis'),
 'cavity':('Höhle','f','Cavitas'), 'head':('Kopf','m','Caput'), 'phalanx':('Phalanx','f','Phalanx'), 'lobe':('Lappen','m','Lobus'),
 'lobule':('Läppchen','n','Lobulus'), 'nucleus':('Kern','m','Nucleus'), 'commissure':('Kommissur','f','Commissura'),
 'peduncle':('Stiel','m','Pedunculus'), 'septum':('Septum','n','Septum'), 'stria':('Streifen','m','Stria'), 'fornix':('Fornix','m','Fornix'),
 'lamina':('Lamina','f','Lamina'), 'gyrus':('Windung','f','Gyrus'), 'brachium':('Arm','m','Brachium'), 'cusp':('Tasche','f','Valvula'),
 'leaflet':('Segel','n','Cuspis'), 'chamber':('Kammer','f','Camera'), 'trunk':('Stamm','m','Truncus'), 'compartment':('Kompartiment','n','Compartimentum'),
 'ligament':('Band','n','Ligamentum'), 'side':('Seite','f','Latus'), 'part':('Teil','m','Pars'), 'process':('Fortsatz','m','Processus'),
 'body':('Körper','m','Corpus'), 'parenchyma':('Parenchym','n','Parenchyma'), 'papillary muscle':('Papillarmuskel','m','Musculus papillaris'),
 'free wall':('Freie Wand','f','Paries liber'), 'anterior wall':('Vordere Wand','f','Paries anterior'), 'inferior wall':('Untere Wand','f','Paries inferior'),
 'lateral wall':('Seitliche Wand','f','Paries lateralis'), 'inflow part':('Einflussteil','m','Pars afferens'), 'outflow part':('Ausflussteil','m','Pars efferens'),
 'fibrous layer':('Faserschicht','f','Tunica fibrosa'), 'vascular layer':('Gefäßhaut','f','Tunica vasculosa'), 'layer of wall':('Wandschicht','f','Tunica'),
 'fibrous ring':('Faserring','m','Anulus fibrosus'), 'fascia lata':('Oberschenkelfaszie','f','Fascia lata'), 'skeletal system':('Skelettsystem','n','Systema skeletale'),
 'anterior sector':('Vorderer Sektor','m','Sector anterior'), 'posterior sector':('Hinterer Sektor','m','Sector posterior'),
 'patellar part':('Kniescheibenteil','m','Pars patellaris'), 'anterior part':('Vorderer Teil','m','Pars anterior'), 'scapular part':('Schulterblattteil','m','Pars scapularis'),
 'pectoral part':('Brustteil','m','Pars pectoralis'), 'orbital part':('Augenhöhlenteil','m','Pars orbitalis'), 'upper lobe':('Oberlappen','m','Lobus superior'),
 'lower lobe':('Unterlappen','m','Lobus inferior'), 'upper lobe part':('Oberlappenteil','m','Pars lobi superioris'), 'lower lobe part':('Unterlappenteil','m','Pars lobi inferioris'),
 'middle lobe part':('Mittellappenteil','m','Pars lobi medii'), 'intervertebral disk':('Bandscheibe','f','Discus intervertebralis'), 'articular disk':('Gelenkscheibe','f','Discus articularis'),
 'cartilaginous skeleton':('Knorpelskelett','n','Sceletum cartilagineum'), 'osseous skeleton':('Knochenskelett','n','Sceletum osseum'),
 'subendocardial layer of myocardium':('Subendokardiale Schicht des Myokards','f','Stratum subendocardiale myocardii'),
 'myocardium of free wall':('Myokard der freien Wand','n','Myocardium parietis liberi'), 'myocardium of inferior wall':('Myokard der unteren Wand','n','Myocardium parietis inferioris'),
 'myocardium of lateral wall':('Myokard der seitlichen Wand','n','Myocardium parietis lateralis'), 'wall of inflow part':('Wand des Einflussteils','f','Paries partis afferentis'),
 'region of anterior sector':('Region des vorderen Sektors','f','Regio sectoris anterioris'), 'region of posterior sector':('Region des hinteren Sektors','f','Regio sectoris posterioris'),
 'space of compartment':('Raum des Kompartiments','m','Spatium compartimenti'),
 'set':None,
}
SETS = {'arteries':('Arterien','Arteriae'),'veins':('Venen','Venae'),'cervical vertebrae':('Halswirbel','Vertebrae cervicales'),
        'thoracic vertebrae':('Brustwirbel','Vertebrae thoracicae'),'lumbar vertebrae':('Lendenwirbel','Vertebrae lumbales'),
        'facial hairs':('Gesichtshaare','Pili faciei'),'hairs':('Haare','Pili'),'heterogeneous clusters':('Heterogene Cluster','Aggregata heterogenea'),
        'organ parts':('Organteile','Partes organorum'),'organ regions':('Organregionen','Regiones organorum'),'organs':('Organe','Organa')}
RELS = sorted(REL, key=len, reverse=True)

ORD = {'first':('erst','prima'),'second':('zweit','secunda'),'third':('dritt','tertia'),'fourth':('viert','quarta'),'fifth':('fünft','quinta'),
       'sixth':('sechst','sexta'),'seventh':('siebt','septima'),'eighth':('acht','octava'),'ninth':('neunt','nona'),'tenth':('zehnt','decima'),
       'eleventh':('elft','undecima'),'twelfth':('zwölft','duodecima')}
VERT = {'cervical':('Hals','cervicalis'),'thoracic':('Brust','thoracica'),'lumbar':('Lenden','lumbalis')}
BPS = {'apical':('Apikales','apicale'),'anterior':('Vorderes','anterius'),'posterior':('Hinteres','posterius'),'superior':('Oberes','superius'),
       'medial':('Mediales','mediale'),'lateral':('Seitliches','laterale'),'anterior basal':('Vorderes basales','basale anterius'),
       'posterior basal':('Hinteres basales','basale posterius'),'lateral basal':('Seitliches basales','basale laterale'),
       'medial basal':('Mediales basales','basale mediale'),'apicoposterior':('Apikoposteriores','apicoposterius'),
       'superior lingular':('Oberes Lingula-','lingulare superius'),'inferior lingular':('Unteres Lingula-','lingulare inferius')}

# direct dictionary for abstract / topographic / plain terms
P = {
 'abdominal segment of trunk':('Bauchabschnitt des Rumpfes','Segmentum abdominale trunci'),'thoracic segment of trunk':('Brustabschnitt des Rumpfes','Segmentum thoracicum trunci'),
 'alimentary system':('Verdauungssystem','Systema digestorium'),'anal part of perineum':('Afterregion des Damms','Regio analis perinei'),
 'anastomosis':('Anastomose','Anastomosis'),'vascular anastomosis':('Gefäßanastomose','Anastomosis vascularis'),
 'anatomical boundary entity':('Anatomische Grenzentität','Ens anatomicum limitans'),'anatomical cavity':('Anatomische Höhle','Cavitas anatomica'),
 'anatomical cluster':('Anatomischer Cluster','Aggregatum anatomicum'),'anatomical compartment space':('Anatomischer Kompartimentraum','Spatium compartimenti anatomici'),
 'anatomical conduit space':('Anatomischer Leitungsraum','Spatium conductus anatomici'),'anatomical entity':('Anatomische Entität','Ens anatomicum'),
 'anatomical junction':('Anatomische Verbindungsstelle','Junctio anatomica'),'anatomical line':('Anatomische Linie','Linea anatomica'),
 'anatomical lobe':('Anatomischer Lappen','Lobus anatomicus'),'anatomical set':('Anatomische Menge','Copia anatomica'),
 'anatomical space':('Anatomischer Raum','Spatium anatomicum'),'anatomical structure':('Anatomische Struktur','Structura anatomica'),
 'material anatomical entity':('Materielle anatomische Entität','Ens anatomicum materiale'),'immaterial anatomical entity':('Immaterielle anatomische Entität','Ens anatomicum immateriale'),
 'physical anatomical entity':('Physische anatomische Entität','Ens anatomicum physicum'),
 'anterior cardiac venous tree':('Vorderer Herzvenenbaum','Arbor venarum cardiacarum anteriorum'),'coronary sinus tree':('Koronarsinusbaum','Arbor sinus coronarii'),
 'anterior chest':('Vordere Brust','Pectus anterius'),'posterior chest':('Hintere Brust','Pectus posterius'),
 'anterior chest wall':('Vordere Brustwand','Paries pectoris anterior'),'chest wall':('Brustwand','Paries pectoris'),
 'superficial chest wall':('Oberflächliche Brustwand','Paries pectoris superficialis'),'anterior superficial chest wall':('Vordere oberflächliche Brustwand','Paries pectoris superficialis anterior'),
 'anterior thoracic wall':('Vordere Brustkorbwand','Paries thoracis anterior'),'posterior thoracic wall':('Hintere Brustkorbwand','Paries thoracis posterior'),
 'thoracic wall':('Brustkorbwand','Paries thoracis'),'body wall':('Körperwand','Paries corporis'),'pelvic wall':('Beckenwand','Paries pelvis'),
 'anterior segmental hepatic artery':('Vordere Lebersegmentarterie','Arteria segmentalis hepatica anterior'),'posterior segmental hepatic artery':('Hintere Lebersegmentarterie','Arteria segmentalis hepatica posterior'),
 'lateral segmental hepatic artery':('Seitliche Lebersegmentarterie','Arteria segmentalis hepatica lateralis'),'medial segmental hepatic artery':('Mediale Lebersegmentarterie','Arteria segmentalis hepatica medialis'),
 'anterior suboccipital muscle':('Vorderer Subokzipitalmuskel','Musculus suboccipitalis anterior'),'posterior suboccipital muscle':('Hinterer Subokzipitalmuskel','Musculus suboccipitalis posterior'),
 'anterior tributary of right hepatic biliary tree':('Vorderer Zufluss des rechten Gallengangsystems','Ramus anterior arboris biliaris dextri'),
 'posterior tributary of right hepatic biliary tree':('Hinterer Zufluss des rechten Gallengangsystems','Ramus posterior arboris biliaris dextri'),
 'lateral tributary of left hepatic biliary tree':('Seitlicher Zufluss des linken Gallengangsystems','Ramus lateralis arboris biliaris sinistri'),
 'medial tributary of left hepatic biliary tree':('Medialer Zufluss des linken Gallengangsystems','Ramus medialis arboris biliaris sinistri'),
 'segmental tributary of left hepatic biliary tree':('Segmentzufluss des linken Gallengangsystems','Ramus segmentalis arboris biliaris sinistri'),
 'segmental tributary of right hepatic biliary tree':('Segmentzufluss des rechten Gallengangsystems','Ramus segmentalis arboris biliaris dextri'),
 'anterior ventricular branch of right coronary artery':('Vorderer Kammerast der rechten Koronararterie','Ramus ventricularis anterior arteriae coronariae dextrae'),
 'posterior ventricular branch of right coronary artery':('Hinterer Kammerast der rechten Koronararterie','Ramus ventricularis posterior arteriae coronariae dextrae'),
 'ventricular branch of right coronary artery':('Kammerast der rechten Koronararterie','Ramus ventricularis arteriae coronariae dextrae'),
 'antero-medial basal segmental artery':('Vordere mediale basale Segmentarterie','Arteria segmentalis basalis anteromedialis'),
 'apicoposterior division of right upper lobar artery':('Apikoposteriorer Ast der rechten oberen Lappenarterie','Ramus apicoposterior arteriae lobaris superioris dextrae'),
 'apicoposterior segmental vein':('Apikoposteriore Segmentvene','Vena segmentalis apicoposterior'),
 'atypical rib':('Atypische Rippe','Costa atypica'),'typical rib':('Typische Rippe','Costa typica'),'true rib':('Echte Rippe','Costa vera'),
 'false rib':('Falsche Rippe','Costa spuria'),'floating rib':('Freie Rippe','Costa fluctuans'),'rib':('Rippe','Costa'),
 'autonomic ganglion':('Autonomes Ganglion','Ganglion autonomicum'),'parasympathetic ganglion':('Parasympathisches Ganglion','Ganglion parasympathicum'),
 'cranial parasympathetic ganglion':('Kraniales parasympathisches Ganglion','Ganglion parasympathicum craniale'),'ganglion':('Ganglion','Ganglion'),
 'axial skeletal system':('Axiales Skelettsystem','Systema skeletale axiale'),'axial skeleton':('Achsenskelett','Skeleton axiale'),
 'back of abdomen':('Rückseite des Bauches','Dorsum abdominis'),'back of neck':('Nacken','Regio cervicalis posterior'),'back of thorax':('Rücken des Brustkorbs','Dorsum thoracis'),
 'basal ganglion of telencephalon':('Basalganglion des Endhirns','Nucleus basalis telencephali'),'basal segmental bronchial tree':('Basaler Segmentbronchialbaum','Arbor bronchialis segmentalis basalis'),
 'basicranial part of head proper':('Schädelbasisteil des Kopfes','Pars basicranialis capitis proprii'),'basicranium':('Schädelbasis','Basis cranii'),
 'bile duct':('Gallengang','Ductus biliaris'),'extrahepatic bile duct':('Extrahepatischer Gallengang','Ductus biliaris extrahepaticus'),
 'intrahepatic biliary tree':('Intrahepatisches Gallengangsystem','Arbor biliaris intrahepatica'),
 'body cavity content':('Körperhöhleninhalt','Contentum cavitatis corporis'),'body compartment':('Körperkompartiment','Compartimentum corporis'),
 'body proper':('Eigentlicher Körper','Corpus proprium'),'human body':('Menschlicher Körper','Corpus humanum'),
 'bony part of nasal septum':('Knöcherner Teil der Nasenscheidewand','Pars ossea septi nasi'),'cartilaginous part of nasal septum':('Knorpeliger Teil der Nasenscheidewand','Pars cartilaginea septi nasi'),
 'brainstem':('Hirnstamm','Truncus encephali'),'bronchus':('Bronchus','Bronchus'),
 'canine tooth':('Eckzahn','Dens caninus'),'incisor tooth':('Schneidezahn','Dens incisivus'),'molar tooth':('Molar','Dens molaris'),'premolar tooth':('Prämolar','Dens premolaris'),
 'secondary canine tooth':('Bleibender Eckzahn','Dens caninus permanens'),'secondary incisor tooth':('Bleibender Schneidezahn','Dens incisivus permanens'),
 'secondary molar tooth':('Bleibender Molar','Dens molaris permanens'),'tooth':('Zahn','Dens'),
 'upper secondary incisor tooth':('Oberer Schneidezahn','Dens incisivus superior'),'lower secondary incisor tooth':('Unterer Schneidezahn','Dens incisivus inferior'),
 'upper secondary molar tooth':('Oberer Molar','Dens molaris superior'),'lower secondary molar tooth':('Unterer Molar','Dens molaris inferior'),
 'upper secondary premolar tooth':('Oberer Prämolar','Dens premolaris superior'),'lower secondary premolar tooth':('Unterer Prämolar','Dens premolaris inferior'),
 'capsule of cerebral hemisphere':('Kapsel der Großhirnhemisphäre','Capsula hemispherii cerebri'),'cardiac vein':('Herzvene','Vena cardiaca'),
 'cardinal organ part':('Organhauptteil','Pars cardinalis organi'),'cardinal segment of brain':('Hauptabschnitt des Gehirns','Segmentum cardinale encephali'),
 'cardinal tissue part':('Gewebehauptteil','Pars cardinalis textus'),'cardiovascular system':('Herz-Kreislauf-System','Systema cardiovasculare'),
 'carpal bone':('Handwurzelknochen','Os carpi'),'distal carpal bone':('Distaler Handwurzelknochen','Os carpi distale'),'proximal carpal bone':('Proximaler Handwurzelknochen','Os carpi proximale'),
 'tarsal bone':('Fußwurzelknochen','Os tarsi'),'cuneiform bone':('Keilbein','Os cuneiforme'),'metacarpal bone':('Mittelhandknochen','Os metacarpale'),'metatarsal bone':('Mittelfußknochen','Os metatarsale'),
 'sesamoid bone':('Sesambein','Os sesamoideum'),'long bone':('Röhrenknochen','Os longum'),'short bone':('Kurzer Knochen','Os breve'),'flat bone':('Platter Knochen','Os planum'),
 'irregular bone':('Unregelmäßiger Knochen','Os irregulare'),'pneumatized bone':('Pneumatisierter Knochen','Os pneumaticum'),
 'cartilage organ':('Knorpel','Cartilago'),'cartilage organ component':('Knorpelkomponente','Componens cartilaginis'),'costal cartilage':('Rippenknorpel','Cartilago costalis'),
 'laryngeal cartilage':('Kehlkopfknorpel','Cartilago laryngis'),'nasal cartilage':('Nasenknorpel','Cartilago nasi'),
 'cavitated organ':('Organ mit Hohlraum','Organum cavitatum'),'organ with organ cavity':('Organ mit Organhöhle','Organum cum cavitate'),
 'organ with cavitated organ parts':('Organ mit hohlraumhaltigen Teilen','Organum cum partibus cavitatis'),
 'cecum':('Blinddarm','Caecum'),'cell part cluster':('Zellteil-Cluster','Aggregatum partium cellularum'),'cell part cluster of neuraxis':('Zellteil-Cluster der Neuraxis','Aggregatum partium cellularum neuraxis'),
 'cervical vertebral column':('Halswirbelsäule','Columna vertebralis cervicalis'),'thoracic vertebral column':('Brustwirbelsäule','Columna vertebralis thoracica'),
 'lumbar vertebral column':('Lendenwirbelsäule','Columna vertebralis lumbalis'),'vertebra':('Wirbel','Vertebra'),
 'circumventricular organ of neuraxis':('Zirkumventrikuläres Organ der Neuraxis','Organum circumventriculare neuraxis'),
 'constrictor muscle of pharynx':('Schlundschnürer','Musculus constrictor pharyngis'),'corticomedullary organ':('Rinden-Mark-Organ','Organum corticomedullare'),
 'cricothyroid ligament':('Ringknorpel-Schildknorpel-Band','Ligamentum cricothyroideum'),'thyrohyoid ligament':('Schildknorpel-Zungenbein-Band','Ligamentum thyrohyoideum'),
 'decussation':('Kreuzung','Decussatio'),'deep extrinsic muscle of shoulder':('Tiefer extrinsischer Schultermuskel','Musculus extrinsecus profundus regionis deltoideae'),
 'extrinsic muscle of shoulder':('Extrinsischer Schultermuskel','Musculus extrinsecus regionis deltoideae'),'intrinsic muscle of shoulder':('Intrinsischer Schultermuskel','Musculus intrinsecus regionis deltoideae'),
 'deep fascial system':('Tiefes Fasziensystem','Systema fasciarum profundarum'),
 'deep muscle of anterior compartment of forearm':('Tiefer Muskel der vorderen Unterarmloge','Musculus profundus compartimenti antebrachii anterioris'),
 'deep muscle of posterior compartment of forearm':('Tiefer Muskel der hinteren Unterarmloge','Musculus profundus compartimenti antebrachii posterioris'),
 'deep muscle of posterior compartment of leg':('Tiefer Muskel der hinteren Unterschenkelloge','Musculus profundus compartimenti cruris posterioris'),
 'superficial muscle of anterior compartment of forearm':('Oberflächlicher Muskel der vorderen Unterarmloge','Musculus superficialis compartimenti antebrachii anterioris'),
 'superficial muscle of posterior compartment of forearm':('Oberflächlicher Muskel der hinteren Unterarmloge','Musculus superficialis compartimenti antebrachii posterioris'),
 'superficial muscle of posterior compartment of leg':('Oberflächlicher Muskel der hinteren Unterschenkelloge','Musculus superficialis compartimenti cruris posterioris'),
 'superficial muscle of neck':('Oberflächlicher Halsmuskel','Musculus superficialis colli'),
 'deep postvertebral muscle':('Tiefer Rückenmuskel','Musculus dorsi profundus'),'intermediate postvertebral muscle':('Mittlerer Rückenmuskel','Musculus dorsi intermedius'),
 'superficial postvertebral muscle':('Oberflächlicher Rückenmuskel','Musculus dorsi superficialis'),'postvertebral muscle':('Rückenmuskel','Musculus dorsi'),'prevertebral muscle':('Prävertebraler Muskel','Musculus prevertebralis'),
 'digital artery of foot':('Zehenarterie','Arteria digitalis pedis'),'dorsum of nose':('Nasenrücken','Dorsum nasi'),'root of nose':('Nasenwurzel','Radix nasi'),
 'duct':('Gang','Ductus'),'endocrine system':('Endokrines System','Systema endocrinum'),'epithalamus':('Epithalamus','Epithalamus'),
 'extra-ocular muscle':('Äußerer Augenmuskel','Musculus externus bulbi oculi'),'extrinsic ligament of larynx':('Extrinsisches Kehlkopfband','Ligamentum laryngis extrinsecum'),
 'intrinsic ligament of larynx':('Intrinsisches Kehlkopfband','Ligamentum laryngis intrinsecum'),'extrinsic muscle of tongue':('Äußerer Zungenmuskel','Musculus linguae extrinsecus'),
 'faucial part of mouth':('Rachenenge','Isthmus faucium'),'fibrous skeleton of heart':('Herzskelett','Skeleton fibrosum cordis'),
 'frontal part of head':('Stirnregion des Kopfes','Pars frontalis capitis'),'occipital part of head':('Hinterhauptregion des Kopfes','Pars occipitalis capitis'),
 'gastrointestinal tract':('Magen-Darm-Trakt','Tractus gastrointestinalis'),'upper gastrointestinal tract':('Oberer Magen-Darm-Trakt','Tractus gastrointestinalis superior'),
 'lower gastrointestinal tract':('Unterer Magen-Darm-Trakt','Tractus gastrointestinalis inferior'),'gemellus':('Zwillingsmuskel','Musculus gemellus'),
 'genital system':('Geschlechtssystem','Systema genitale'),'gingiva':('Zahnfleisch','Gingiva'),'gluteal muscle':('Gesäßmuskel','Musculus gluteus'),
 'gray matter of diencephalon':('Graue Substanz des Zwischenhirns','Substantia grisea diencephali'),'gray matter of hypothalamus':('Graue Substanz des Hypothalamus','Substantia grisea hypothalami'),
 'gray matter of neuraxis':('Graue Substanz der Neuraxis','Substantia grisea neuraxis'),'internal gray matter component':('Innere Komponente der grauen Substanz','Componens interna substantiae griseae'),
 'hair':('Haar','Pilus'),'hair of trunk':('Rumpfhaar','Pilus trunci'),'skin appendage':('Hautanhangsgebilde','Appendix cutis'),
 'hepatovenous subsector':('Lebervenen-Subsektor','Subsector hepatovenosus'),'heterogeneous cluster':('Heterogener Cluster','Aggregatum heterogeneum'),
 'hollow tree organ':('Hohles Baumorgan','Organum arboris cavum'),'hypothenar muscle':('Kleinfingerballenmuskel','Musculus hypothenaris'),'thenar muscle':('Daumenballenmuskel','Musculus thenaris'),
 'iliocostalis':('Darmbein-Rippen-Muskel','Musculus iliocostalis'),'longissimus':('Längster Rückenmuskel','Musculus longissimus'),'semispinalis':('Halbdornmuskel','Musculus semispinalis'),
 'splenius':('Riemenmuskel','Musculus splenius'),'serratus posterior':('Hinterer Sägemuskel','Musculus serratus posterior'),'infraspinatus':('Untergrätenmuskel','Musculus infraspinatus'),
 'inferior division of upper lobe part of left bronchial tree':('Unterer Ast des Oberlappenteils des linken Bronchialbaums','Ramus inferior partis lobi superioris arboris bronchialis sinistrae'),
 'superior division of upper lobe part of left bronchial tree':('Oberer Ast des Oberlappenteils des linken Bronchialbaums','Ramus superior partis lobi superioris arboris bronchialis sinistrae'),
 'inferior genicular artery':('Untere Kniearterie','Arteria inferior genus'),'superior genicular artery':('Obere Kniearterie','Arteria superior genus'),
 'superior lateral genicular artery':('Obere seitliche Kniearterie','Arteria superior lateralis genus'),'superior medial genicular artery':('Obere mediale Kniearterie','Arteria superior medialis genus'),
 'inferior segmental renal artery':('Untere Nierensegmentarterie','Arteria segmentalis renalis inferior'),'superior segmental renal artery':('Obere Nierensegmentarterie','Arteria segmentalis renalis superior'),
 'posterior segmental renal artery':('Hintere Nierensegmentarterie','Arteria segmentalis renalis posterior'),'segmental renal artery':('Nierensegmentarterie','Arteria segmentalis renalis'),
 'inferior systemic venous tree':('Unterer Körpervenenbaum','Arbor venosa systemica inferior'),'superior systemic venous tree':('Oberer Körpervenenbaum','Arbor venosa systemica superior'),
 'inferomedial branch of right pulmonary artery':('Inferomedialer Ast der rechten Lungenarterie','Ramus inferomedialis arteriae pulmonalis dextrae'),
 'inferomedial part of right bronchial tree':('Inferomedialer Teil des rechten Bronchialbaums','Pars inferomedialis arboris bronchialis dextrae'),
 'infrahyoid muscle':('Unterzungenbeinmuskel','Musculus infrahyoideus'),'suprahyoid muscle':('Oberzungenbeinmuskel','Musculus suprahyoideus'),
 'integument':('Hautdecke','Integumentum commune'),'integumentary system':('Hautsystem','Systema integumentale'),'intercostal muscle':('Zwischenrippenmuskel','Musculus intercostalis'),
 'intermediate hypothalamic region':('Mittlere Hypothalamusregion','Regio hypothalamica intermedia'),'interosseous membrane':('Zwischenknochenmembran','Membrana interossea'),
 'interosseous of foot':('Zwischenknochenmuskel des Fußes','Musculus interosseus pedis'),'plantar interosseous of foot':('Sohlenzwischenknochenmuskel des Fußes','Musculus interosseus plantaris pedis'),
 'lumbrical of foot':('Spulmuskel des Fußes','Musculus lumbricalis pedis'),'interspinalis muscle':('Zwischendornmuskel','Musculus interspinalis'),
 'intertransversarius muscle':('Zwischenquerfortsatzmuskel','Musculus intertransversarius'),'lumbar intertransversarius':('Zwischenquerfortsatzmuskel der Lende','Musculus intertransversarius lumborum'),
 'intervertebral symphysis':('Zwischenwirbelsymphyse','Symphysis intervertebralis'),'intervertebral symphysis of axis':('Zwischenwirbelsymphyse des Axis','Symphysis intervertebralis axis'),
 'intracranial branch of vertebral artery':('Intrakranialer Ast der Wirbelarterie','Ramus intracranialis arteriae vertebralis'),
 'intrinsic muscle of dorsum of foot':('Intrinsischer Muskel des Fußrückens','Musculus intrinsecus dorsi pedis'),'intrinsic muscle of foot':('Intrinsischer Fußmuskel','Musculus intrinsecus pedis'),
 'intrinsic muscle of hand':('Intrinsischer Handmuskel','Musculus intrinsecus manus'),'intrinsic muscle of larynx':('Innerer Kehlkopfmuskel','Musculus laryngis intrinsecus'),
 'intrinsic muscle of plantar part of foot':('Intrinsischer Muskel der Fußsohle','Musculus intrinsecus plantae pedis'),
 'irregular connective tissue':('Ungeordnetes Bindegewebe','Textus connectivus irregularis'),'loose connective tissue':('Lockeres Bindegewebe','Textus connectivus laxus'),
 'mucoid tissue':('Gallertgewebe','Textus mucoideus'),'portion of connective tissue':('Bindegewebsanteil','Portio textus connectivi'),'portion of tissue':('Gewebeanteil','Portio textus'),
 'leaf of cardiac valve':('Segel einer Herzklappe','Cuspis valvae cordis'),'ligament organ':('Band','Ligamentum'),'ligament organ component':('Bandkomponente','Componens ligamenti'),
 'skeletal ligament':('Skelettband','Ligamentum skeletale'),'nonskeletal ligament':('Nichtskelettales Band','Ligamentum non skeletale'),'tarsal ligament':('Fußwurzelband','Ligamentum tarsi'),
 'plantar tarsal ligament':('Fußsohlen-Fußwurzelband','Ligamentum tarsi plantare'),'lingular vein':('Lingula-Vene','Vena lingularis'),'lobar artery':('Lappenarterie','Arteria lobaris'),
 'middle lobar artery':('Mittlere Lappenarterie','Arteria lobaris media'),'middle lobar vein':('Mittlere Lappenvene','Vena lobaris media'),'middle lobe of lung':('Mittellappen der Lunge','Lobus medius pulmonis'),
 'lobular organ':('Läppchenorgan','Organum lobulare'),'lobular organ component':('Läppchenorgankomponente','Componens organi lobularis'),'lobular segment':('Läppchensegment','Segmentum lobulare'),
 'lower jaw':('Unterkiefer','Mandibula'),'upper jaw':('Oberkiefer','Maxilla'),'lower respiratory tract':('Untere Atemwege','Tractus respiratorius inferior'),'respiratory tract':('Atemwege','Tractus respiratorius'),
 'lower urinary tract':('Untere Harnwege','Tractus urinarius inferior'),'urinary system':('Harnsystem','Systema urinarium'),
 'major salivary gland':('Große Speicheldrüse','Glandula salivaria major'),'salivary gland':('Speicheldrüse','Glandula salivaria'),
 'mandibular part of mouth':('Unterkieferteil des Mundes','Pars mandibularis oris'),'maxillary part of mouth':('Oberkieferteil des Mundes','Pars maxillaris oris'),
 'medial collateral artery':('Mittlere Kollateralarterie','Arteria collateralis media'),'radial collateral artery':('Speichenseitige Kollateralarterie','Arteria collateralis radialis'),
 'membrane organ':('Membran','Membrana'),'membrane organ component':('Membrankomponente','Componens membranae'),'membranous layer':('Membranöse Schicht','Stratum membranosum'),
 'mesentery of large intestine':('Dickdarmgekröse','Mesocolon'),'peritoneal mesentery':('Peritoneales Gekröse','Mesenterium peritoneale'),'peritoneal sac':('Bauchfellsack','Saccus peritonealis'),
 'mons pubis':('Schamhügel','Mons pubis'),'muscle layer of large intestine':('Muskelschicht des Dickdarms','Tunica muscularis intestini crassi'),
 'musculature':('Muskulatur','Musculatura'),'musculoskeletal system':('Bewegungsapparat','Systema musculoskeletale'),
 'myocardial zone 4':('Myokardzone 4','Zona myocardii 4'),'myocardial zone 11':('Myokardzone 11','Zona myocardii 11'),'myocardial zone 12':('Myokardzone 12','Zona myocardii 12'),
 'nasal skeleton':('Nasenskelett','Skeleton nasi'),'nerve':('Nerv','Nervus'),'nerve trunk':('Nervenstamm','Truncus nervi'),'neurocranium':('Hirnschädel','Neurocranium'),'viscerocranium':('Gesichtsschädel','Viscerocranium'),
 'nonparenchymatous organ':('Nichtparenchymatöses Organ','Organum non parenchymatosum'),'parenchymatous organ':('Parenchymatöses Organ','Organum parenchymatosum'),
 'nuclear complex of neuraxis':('Kernkomplex der Neuraxis','Complexus nuclearis neuraxis'),'obturator muscle':('Hüftlochmuskel','Musculus obturatorius'),
 'organ cavity subdivision':('Organhöhlenabschnitt','Subdivisio cavitatis organi'),'organ chamber':('Organkammer','Camera organi'),'organ component cluster':('Organkomponenten-Cluster','Aggregatum componentium organi'),
 'organ component gland':('Drüsenkomponente eines Organs','Glandula componens organi'),'organ component layer':('Schichtkomponente eines Organs','Stratum componens organi'),
 'organ component of neuraxis':('Organkomponente der Neuraxis','Componens organi neuraxis'),'organ part cluster':('Organteil-Cluster','Aggregatum partium organi'),
 'organ region':('Organregion','Regio organi'),'organ segment':('Organsegment','Segmentum organi'),'organ zone':('Organzone','Zona organi'),
 'pancreatic artery':('Pankreasarterie','Arteria pancreatica'),'pancreaticobiliary system':('Pankreatikobiliäres System','Systema pancreaticobiliare'),
 'parenchyma':('Parenchym','Parenchyma'),'pectoral muscle':('Brustmuskel','Musculus pectoralis'),'pelvic skeleton':('Beckenskelett','Skeleton pelvis'),'perineal muscle':('Dammmuskel','Musculus perinei'),
 'portal venous system':('Pfortadersystem','Systema venae portae'),'portal venous tree':('Pfortaderbaum','Arbor venae portae'),
 'posterior intercostal artery':('Hintere Zwischenrippenarterie','Arteria intercostalis posterior'),'supreme intercostal artery':('Oberste Zwischenrippenarterie','Arteria intercostalis suprema'),
 'posterior part of pelvis':('Hinterer Teil des Beckens','Pars posterior pelvis'),
 'pulmonary arterial tree':('Lungenarterienbaum','Arbor arteriosa pulmonalis'),'pulmonary arterial trunk':('Lungenarterienstamm','Truncus pulmonalis'),
 'pulmonary segment of bronchial tree':('Lungensegment des Bronchialbaums','Segmentum pulmonale arboris bronchialis'),'pulmonary vascular system':('Lungengefäßsystem','Systema vasorum pulmonalium'),
 'pulmonary venous tree organ':('Lungenvenenbaum','Arbor venosa pulmonalis'),'segmental pulmonary artery':('Segmentale Lungenarterie','Arteria pulmonalis segmentalis'),
 'subsegmental pulmonary artery':('Subsegmentale Lungenarterie','Arteria pulmonalis subsegmentalis'),'subsegmental pulmonary vein':('Subsegmentale Lungenvene','Vena pulmonalis subsegmentalis'),
 'respiratory system':('Atmungssystem','Systema respiratorium'),'retinaculum':('Halteband','Retinaculum'),'rotator muscle':('Drehmuskel','Musculus rotator'),'scalene muscle':('Treppenmuskel','Musculus scalenus'),
 'skeletal system':('Skelettsystem','Systema skeletale'),'skeleton (in vivo)':('Skelett (in vivo)','Skeleton (in vivo)'),'skull':('Schädel','Cranium'),
 'soft palate':('Weicher Gaumen','Palatum molle'),'solid organ':('Solides Organ','Organum solidum'),'spinal cord':('Rückenmark','Medulla spinalis'),
 'sternal part of chest':('Brustbeinteil der Brust','Pars sternalis pectoris'),'subaortic curtain of left ventricle':('Subaortaler Vorhang der linken Herzkammer','Velum subaorticum ventriculi sinistri'),
 'subarachnoid incisure':('Subarachnoidale Einkerbung','Incisura subarachnoidea'),'subdivisionof autonomic nervous system':('Unterabschnitt des autonomen Nervensystems','Subdivisio systematis nervosi autonomici'),
 'superior pancreaticoduodenal artery':('Obere Pankreas-Duodenal-Arterie','Arteria pancreaticoduodenalis superior'),
 'superior terminal branch of middle cerebral artery':('Oberer Endast der mittleren Hirnarterie','Ramus terminalis superior arteriae cerebri mediae'),
 'systemic arterial system':('Arterielles Körperkreislaufsystem','Systema arteriosum systemicum'),'systemic arterial tree':('Körperarterienbaum','Arbor arteriosa systemica'),
 'systemic arterial trunk':('Körperarterienstamm','Truncus arteriosus systemicus'),'systemic venous system':('Venöses Körperkreislaufsystem','Systema venosum systemicum'),
 'taenia coli':('Dickdarmtänie','Taenia coli'),'tarsal plate of eyelid':('Lidplatte','Tarsus palpebrae'),'temporal artery':('Schläfenarterie','Arteria temporalis'),'tendon':('Sehne','Tendo'),
 'thoracic part of tracheobronchial tree':('Brustteil des Tracheobronchialbaums','Pars thoracica arboris tracheobronchialis'),'thymus':('Thymus','Thymus'),
 'ulnar recurrent artery':('Rückläufige Ellenarterie','Arteria recurrens ulnaris'),'uvula':('Zäpfchen','Uvula'),'variant artery':('Variante Arterie','Arteria varians'),
 'variant bronchial artery':('Variante Bronchialarterie','Arteria bronchialis varians'),'variant systemic artery':('Variante Körperarterie','Arteria systemica varians'),
 'vascular tree':('Gefäßbaum','Arbor vascularis'),'vasculature of body':('Gefäßsystem des Körpers','Vasa corporis'),'venous trunk':('Venenstamm','Truncus venosus'),
 'white matter of telencephalon':('Weiße Substanz des Endhirns','Substantia alba telencephali'),
 # sided plain
 'left archicortex':('Linker Archikortex','Archicortex sinister'),'right archicortex':('Rechter Archikortex','Archicortex dexter'),
 'left prefrontal cortex':('Linker präfrontaler Kortex','Cortex prefrontalis sinister'),'right prefrontal cortex':('Rechter präfrontaler Kortex','Cortex prefrontalis dexter'),
 'left limbic lobe':('Linker limbischer Lappen','Lobus limbicus sinister'),'right limbic lobe':('Rechter limbischer Lappen','Lobus limbicus dexter'),
 'left parietal lobe':('Linker Scheitellappen','Lobus parietalis sinister'),'right parietal lobe':('Rechter Scheitellappen','Lobus parietalis dexter'),
 'left temporal lobe':('Linker Schläfenlappen','Lobus temporalis sinister'),'right temporal lobe':('Rechter Schläfenlappen','Lobus temporalis dexter'),
 'left hippocampal formation':('Linke Hippocampusformation','Formatio hippocampi sinistra'),'right hippocampal formation':('Rechte Hippocampusformation','Formatio hippocampi dextra'),
 'left orbit':('Linke Augenhöhle','Orbita sinistra'),'right orbit':('Rechte Augenhöhle','Orbita dextra'),
 'left orbital compartment':('Linkes Augenhöhlenkompartiment','Compartimentum orbitale sinistrum'),'right orbital compartment':('Rechtes Augenhöhlenkompartiment','Compartimentum orbitale dextrum'),
 'left orbital content':('Inhalt der linken Augenhöhle','Contentum orbitae sinistrae'),'right orbital content':('Inhalt der rechten Augenhöhle','Contentum orbitae dextrae'),
 'left lacrimal apparatus':('Linker Tränenapparat','Apparatus lacrimalis sinister'),'right lacrimal apparatus':('Rechter Tränenapparat','Apparatus lacrimalis dexter'),
 'left upper eyelid':('Linkes Oberlid','Palpebra superior sinistra'),'right upper eyelid':('Rechtes Oberlid','Palpebra superior dextra'),
 'left lower eyelid':('Linkes Unterlid','Palpebra inferior sinistra'),'right lower eyelid':('Rechtes Unterlid','Palpebra inferior dextra'),
 'left lateral wall of internal nose':('Linke Seitenwand der inneren Nase','Paries lateralis sinister nasi interni'),'right lateral wall of internal nose':('Rechte Seitenwand der inneren Nase','Paries lateralis dexter nasi interni'),
 'left parietal part of head':('Linke Scheitelregion des Kopfes','Pars parietalis sinistra capitis'),'right parietal part of head':('Rechte Scheitelregion des Kopfes','Pars parietalis dextra capitis'),
 'left bony pectoral girdle':('Linker knöcherner Schultergürtel','Cingulum pectorale osseum sinistrum'),'right bony pectoral girdle':('Rechter knöcherner Schultergürtel','Cingulum pectorale osseum dextrum'),
 'left pectoral part of chest':('Linke Brustregion','Pars pectoralis sinistra pectoris'),'right pectoral part of chest':('Rechte Brustregion','Pars pectoralis dextra pectoris'),
 'left lateral chest wall':('Linke seitliche Brustwand','Paries pectoris lateralis sinister'),'right lateral chest wall':('Rechte seitliche Brustwand','Paries pectoris lateralis dexter'),
 'left lateral superficial chest wall':('Linke seitliche oberflächliche Brustwand','Paries pectoris superficialis lateralis sinister'),'right lateral superficial chest wall':('Rechte seitliche oberflächliche Brustwand','Paries pectoris superficialis lateralis dexter'),
 'left side of bony pelvis':('Linke Hälfte des knöchernen Beckens','Latus sinistrum pelvis osseae'),'right side of bony pelvis':('Rechte Hälfte des knöchernen Beckens','Latus dextrum pelvis osseae'),
 'left side of rib cage':('Linke Hälfte des Brustkorbskeletts','Latus sinistrum caveae thoracis'),'right side of rib cage':('Rechte Hälfte des Brustkorbskeletts','Latus dextrum caveae thoracis'),
 'left pulmopleural compartment':('Linkes Lungen-Pleura-Kompartiment','Compartimentum pulmopleurale sinistrum'),'right pulmopleural compartment':('Rechtes Lungen-Pleura-Kompartiment','Compartimentum pulmopleurale dextrum'),
 'left hemiliver':('Linke Leberhälfte','Hemihepar sinistrum'),'right hemiliver':('Rechte Leberhälfte','Hemihepar dextrum'),
 'left lobe of liver':('Linker Leberlappen','Lobus hepatis sinister'),'right lobe of liver':('Rechter Leberlappen','Lobus hepatis dexter'),
 'left upper urinary tract':('Linke obere Harnwege','Tractus urinarius superior sinister'),'right upper urinary tract':('Rechte obere Harnwege','Tractus urinarius superior dexter'),
 'left common basal vein':('Linke gemeinsame Basalvene','Vena basalis communis sinistra'),'right common basal vein':('Rechte gemeinsame Basalvene','Vena basalis communis dextra'),
 'left inferior basal vein':('Linke untere Basalvene','Vena basalis inferior sinistra'),'right inferior basal vein':('Rechte untere Basalvene','Vena basalis inferior dextra'),
 'left superior basal vein':('Linke obere Basalvene','Vena basalis superior sinistra'),'right superior basal vein':('Rechte obere Basalvene','Vena basalis superior dextra'),
 'left upper lobar vein':('Linke obere Lappenvene','Vena lobaris superior sinistra'),'right upper lobar vein':('Rechte obere Lappenvene','Vena lobaris superior dextra'),
 'left lower lobar artery':('Linke untere Lappenarterie','Arteria lobaris inferior sinistra'),'right lower lobar artery':('Rechte untere Lappenarterie','Arteria lobaris inferior dextra'),
 'left basal segmental artery':('Linke basale Segmentarterie','Arteria segmentalis basalis sinistra'),'right basal segmental artery':('Rechte basale Segmentarterie','Arteria segmentalis basalis dextra'),
 'left deep femoral artery':('Linke tiefe Oberschenkelarterie','Arteria profunda femoris sinistra'),'right deep femoral artery':('Rechte tiefe Oberschenkelarterie','Arteria profunda femoris dextra'),
}

def translate(t):
    if t in P: return P[t]
    m = re.match(r'^(\w+) (cervical|thoracic|lumbar) intervertebral symphysis$', t)
    if m:
        o = ORD[m.group(1)]; v = VERT[m.group(2)]
        return (f'{cap(o[0])}e {v[0]}wirbel-Zwischenwirbelsymphyse', f'Symphysis intervertebralis {v[1]} {o[1]}')
    m = re.match(r'^(?:(left|right) )?(.+) bronchopulmonary segment$', t)
    if m and m.group(2) in BPS:
        d,l = BPS[m.group(2)]; sd = m.group(1)
        de = f'{d} Lungensegment'; la = f'Segmentum bronchopulmonale {l}'
        if sd: de = f'{"Linkes" if sd=="left" else "Rechtes"} {de[0].lower()+de[1:]}'; la += ' sinistrum' if sd=='left' else ' dextrum'
        return (de, la)
    m = re.match(r'^set of (.+)$', t)
    if m and m.group(1) in SETS: return SETS[m.group(1)]
    for r in RELS:
        m = re.match(r'^'+re.escape(r)+r' of (.+)$', t)
        if m and REL[r]:
            hd, hg, hl = REL[r]; b = base(m.group(1))
            return (f'{hd} {b.de_gen}', f'{hl} {b.la_gen}')
    b = base(t); return (b.de_nom, b.la_nom)

rows, missing = [], []
for t in todo:
    try: rows.append((t,)+tuple(translate(t)))
    except KeyError as e: missing.append(str(e))
print(len(rows), 'translated;', len(missing), 'missing'); print(missing[:60])
for t,(de,la) in done.items(): rows.append((t,de,la))
rows.sort()
rs = [{'english':e,'german':d,'latin':l,'system':'concept'} for e,d,l in rows]
with open('translate/atlas-de-concepts.csv','w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=['english','german','latin','system']); w.writeheader(); w.writerows(rs)
json.dump(rs, open('translate/atlas-de-concepts.json','w'), ensure_ascii=False, indent=1)
with open('translate/atlas-de-concepts.md','w') as f:
    f.write('# Human Atlas – Konzepte / Gruppierungsbegriffe (Deutsch / Latein)\n\n| English | Deutsch (Latein) |\n|---|---|\n')
    for r in rs: f.write(f"| {r['english']} | {r['german']} ({r['latin']}) |\n")
print('total concept rows', len(rs))
