import json, csv
atlas = json.load(open('public/models/atlas.json'))
T = {
 'corpus cavernosum of penis':('Penisschwellkörper','Corpus cavernosum penis'),
 'corpus spongiosum of penis':('Harnröhrenschwellkörper','Corpus spongiosum penis'),
 'glans penis':('Eichel','Glans penis'),
 'prostate':('Vorsteherdrüse','Prostata'),
 'left deferent duct':('Linker Samenleiter','Ductus deferens sinister'),'right deferent duct':('Rechter Samenleiter','Ductus deferens dexter'),
 'left epididymis':('Linker Nebenhoden','Epididymis sinistra'),'right epididymis':('Rechter Nebenhoden','Epididymis dextra'),
 'left seminal vesicle':('Linke Samenblase','Glandula vesiculosa sinistra'),'right seminal vesicle':('Rechte Samenblase','Glandula vesiculosa dextra'),
 'left testis':('Linker Hoden','Testis sinister'),'right testis':('Rechter Hoden','Testis dexter'),
 'left kidney':('Linke Niere','Ren sinister'),'right kidney':('Rechte Niere','Ren dexter'),
 'left ureter':('Linker Harnleiter','Ureter sinister'),'right ureter':('Rechter Harnleiter','Ureter dexter'),
 'urethra':('Harnröhre','Urethra'),'urinary bladder':('Harnblase','Vesica urinaria'),
 'eyebrow':('Augenbraue','Supercilium'),'hair of head':('Kopfhaar','Capilli'),'lip':('Lippe','Labium oris'),
 'pubic hair':('Schamhaar','Pubes'),'skin':('Haut','Cutis'),
 'left adrenal gland':('Linke Nebenniere','Glandula suprarenalis sinistra'),'right adrenal gland':('Rechte Nebenniere','Glandula suprarenalis dextra'),
 'pineal body':('Zirbeldrüse','Glandula pinealis'),'pituitary gland':('Hirnanhangsdrüse','Hypophysis'),
 'left lobe of thymus':('Linker Thymuslappen','Lobus sinister thymi'),'right lobe of thymus':('Rechter Thymuslappen','Lobus dexter thymi'),
 'spleen':('Milz','Splen'),
}
rows=[]
for sy in ('reproductive','urinary','integumentary','endocrine','lymphatic'):
    for t in sorted(set(p['name'].lower() for p in atlas['parts'] if p['system']==sy)):
        rows.append({'english':t,'german':T[t][0],'latin':T[t][1],'system':sy})
print(len(rows))
with open('translate/atlas-de-other-systems.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['english','german','latin','system']); w.writeheader(); w.writerows(rows)
json.dump(rows,open('translate/atlas-de-other-systems.json','w'),ensure_ascii=False,indent=1)
with open('translate/atlas-de-other-systems.md','w') as f:
    f.write('# Human Atlas – Fortpflanzung, Harnwege, Haut, Hormone, Lymphe (Deutsch / Latein)\n\n| English | Deutsch (Latein) |\n|---|---|\n')
    for r in rows: f.write(f"| {r['english']} | {r['german']} ({r['latin']}) |\n")
