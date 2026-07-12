# Sesija 131 — Massey implementacija: shema, klasifikacija, reklasifikacija obje knjige

**Datum:** 12. jul 2026.
**Fokus:** Riješiti otvoreno pitanje s130 (od čega graditi centroide za 29 fine
kategorija) i implementirati Massey taksonomiju kraj-do-kraja u bazi i bb_10c.
**Ishod:** Centroidi ODBAČENI na osnovu izmjerene dijagnostike; usvojena varijanta
(c) — glm-5.2 klasifikacija iz zatvorene liste, embedding degradiran u audit-metriku.
Shema prepravljena, bb_10c prepisan, obje knjige (Hound+Alice) reklasifikovane.
Ventil ŽIV prvi put. Web namjerno NIJE diran (konzistentnost staro+staro).

---

## 1. Polazno stanje (health check)

Korpus nepromijenjen od s130: 50.624 rečenice, 1.518.170 prevoda, 296.578 pobjednika.
NER relacije: Hound 78, Alice 60 (stari rječnik od 12 grupa). Sve zeleno; 13 .bak
fajlova; poznati lažni "buchenweb zaostaje" alarm.

## 2. Put do odluke — dijagnostika prije arhitekture

Flavio otvorio pitanje iz vlastitog iskustva: hashing paradigma ("prvo grupiši,
pa imenuj grupe") — primjenjivo? Razjašnjeno: hash je semantički slijep (namjerno),
ali dublja ideja = klasterovanje (k-means), imenovana kao varijanta **(d)** uz
postojeće (a)/(b)/(c) iz s130.

**Odluka procesa (Flavio OK): dijagnostički klaster-eksperiment PRIJE izbora
arhitekture** — "mjeri pa definiši" primijenjen na samu arhitektonsku odluku.

### sandbox_cluster_probe.py (novo, read-only, s131)
138 opisa iz bb_ner_relacije → e5-large → k-means (k=8/15/25) + silhouette.
Trajanje: 22s, nula LLM poziva, nula upisa.

**Rezultat — dvoznačan, i upravo zato presudan:**
- **Silhouette 0.10–0.12 na sve tri k** → globalno slaba struktura, granice
  proizvoljne. Numerička potvrda s130 pojasa (0.857–0.98). Varijante (a)/(b)/(d)
  padaju s dokazom.
- **Golim okom: lokalna koherencija postoji** — k=25 klaster 6 (recitacije),
  10 (converses with, 7/7), 13 (prijatelji), 17 (assistance) čisti.
- **Klaster 12 = neprijateljstvo** ("plotting to murder" + "threatens and defies"
  + "abuses" + "hostile encounter") — empirijski dokaz da Massey enemy/negative
  dimenzija ima uporište u našim podacima.
- Stari problem uživo: "is threatening" i "is investigating" u istom klasteru →
  argmax nad ovim prostorom pravi tačno greške tipa "murdered→kretanje".

**Presuda: instrument hvata površinsku semantiku glagola, ne može povući oštru
granicu ni nositi afinitet → klasifikator NE, audit-metrika DA.**

## 3. Odluke (Flavio)

**O1 — Varijanta (c):** glm-5.2 klasifikuje iz zatvorene Massey liste (29 + "ostalo").
Embedding = audit_kosinus(opis, ime kategorije) — mjerni instrument, ne sudija.
s90 čitanje: grounding se već desio u prvom prolazu (dokaz+pozicije); drugi prolaz
je etiketiranje ukotvljene činjenice, ista klasa posla kao bb_10 type reconciliation.

**O2 — Dominantno coarse mapiranje:** Massey podaci NISU čista funkcija fine→coarse
(enemy: social 124 + professional 22; lovers na 4 coarse...) — "without any
adjudication". Dominanta izmjerena IZ PODATAKA (Python, ne awk — v. Lekcije):
najniža dominanca enemy 85%, sve ostalo >95%. LLM bira samo fine+afinitet;
coarse se izvodi JOIN-om.

**O3 — NULL ventil:** fine=NULL = "klasifikacija nije primijenjena / nijedna
kategorija ne odgovara". 'ostalo' NIJE red u bb_ner_massey — lookup ostaje čista
1:1 preslika Masseya (O6 s130: bez naših dopuna).

**O4 — UNIQUE(izvor_id, cilj_id):** jedna relacija po usmjerenom paru (odgovara
par-vođenoj logici). Provjereno prije DDL: 0 duplikata u postojećih 138.

**O5 — Stari rječnik: brisanje (opcija a), ne zamrzavanje.** 138 redova koji se
ionako reklasifikuju ≠ 1,39M prevoda; istorijska vrijednost mala, dvostruka shema
trajno zbunjuje.

**O6 — Deterministički filter osoba–osoba:** Massey je striktno character-character
taksonomija; klasifikacija se poziva SAMO kad su oba tipa PERSON. Osoba–mjesto:
fine/afinitet/audit = NULL bez LLM poziva (strukturno van opsega ≠ ventil-nalaz;
razlika čitljiva iz tipova entiteta JOIN-om). Ekstenzija za mjesta ako ikad
zatreba: LitBank (isti Bamman) — horizont.

## 4. Shema (backup + DDL, jedna transakcija)

Backup: `/tmp/bb_backup_pre_massey_20260712.dump` (1.5G, verifikovan 18 TABLE DATA
= tačan broj tabela). Stari pre_docre dump obrisan (Flaviov podsjetnik — higijena
/tmp-a pri svakom novom backupu).

- **`bb_ner_massey`** (novo): fine PK + coarse CHECK — 29 redova
  (familial 14 / professional 9 / social 6).
- **`bb_ner_relacije`**: +fine (FK massey, NULLABLE=ventil), +afinitet
  (CHECK positive/negative/neutral), +audit_kosinus REAL;
  −tip_veze; novi UNIQUE(izvor_id, cilj_id).
- **`bb_ner_tip_veze` DROPPED** — stari rječnik van.
- FK politika održana: fine FK = NO ACTION (lookup), izvor/cilj CASCADE netaknuti.

## 5. bb_10c_docre.py — prepravka (backup .bak_s131, diff pregledan u cjelini)

- SEED_OPISI / izgradi_centroide / mapiraj_grupu / PRAG_OSTALO — VAN.
- `ucitaj_massey()` — 29 kategorija IZ BAZE (izvor istine, ne hardkod).
- `klasifikuj_relaciju()` — glm-5.2, think:false, temp 0.0, zatvorena lista u
  promptu, JSON {fine, afinitet}; "ostalo"/nepoznato → NULL.
- `je_osoba_osoba()` — deterministički filter (O6).
- `audit_kos()` — e5-large kosinus(opis, ime kategorije); NULL uz NULL fine.
- **`--reklasifikuj`** (novo): preskače prvi prolaz, UPDATE samo
  fine/afinitet/audit_kosinus nad postojećim relacijama — migracija bez ponavljanja
  skupe ekstrakcije.
- `think:false` dodan i u ollama_call payload (konzistentno bb_09/bb_10).
- Mali promptovi po relaciji (524 ∝ veličina prompta — s129/s130 lekcija);
  0× 524 u svim runovima ove sesije.
- Prvi prolaz bit-identičan s129 verziji.

## 6. Reklasifikacija — rezultati

| Knjiga | Relacija | s fine (dry→live) | s afinitetom | avg audit |
|---|---|---|---|---|
| Hound | 78 | 28 → **29** | 45 | 0.844 |
| Alice | 60 | 7 → **10** | 28 | 0.810 |

Dry-run i live upis na obje knjige; trajanja 35s–1:09 (sitni promptovi).
**Nedeterminizam klasifikacije ±1–3 uz temp 0.0** — ista s130 pojava kao entiteti.

**Kvalitet (Hound, ključni testovi):**
- "is plotting to murder and is the enemy of" → **enemy/negative** (s130 rak-rana
  "murdered→kretanje" riješena)
- "deceived and manipulated by pretending to be a single man..." →
  **lovers/negative** — Stapleton→Laura lažna romansa uhvaćena dvodimenzionalno;
  afinitet dimenzija dokazuje vrijednost
- "is infatuated with..." → **unrequited love interest** (Henry→Beryl — u knjizi
  zaista neuzvraćena)
- "is the brother-in-law of and assists in the escape of" → **in-law relation**
  (bivša "prevara")
- srodstvo/služba precizni: uncle/aunt, niece/nephew, brother/sister, servant ×3...
- Afinitet dosljedan: enemy uvijek negative, friend uvijek positive.

**Ventil ŽIV — prvi put:** Hound 17/45, Alice 21/28 osoba–osoba u ventilu.
Sadržaj ventila = dosljedno RADNJE/INTERAKCIJE ("is investigating" ×6,
"converses with", "recites", "provided financial assistance") — tačno s130
dijagnoza (status vs radnja) sada mjerena, ne pretpostavljena. Nalazi o žanru:
Alice = interakcije; Hound = detektivske radnje. Ventil radi kao mjerni instrument.

## 7. NALAZ — šum tipova u entitetskom sloju (Alice)

PERSON-PERSON filter razotkrio sloj ispod sebe: u Alisi **Dodo, Duchess,
Mock Turtle, March Hare, Rabbit, Caterpillar, Cat, Time → ORG**;
**Cheshire Cat, Dinah, Tortoise, Wonderland → GPE**; PERSON lista sadrži šum
("CHAPTER I. Down", "Beautiful Soup", "fig"...). spaCy news-bias na fantastici.
bb_10 type reconciliation rješava samo KONFLIKTE — jednotipne greške prolaze
neprovjerene. → **"Type audit" na horizont kao faza u bb_10**, uz koreferenciju
(srodni: oba su kvalitet entitetskog sloja). Posljedica: dio stvarnih statusa u
Alisi ("is the companion and former friend of") nije ni klasifikovan.
Hound provjeren: svi nosioci relacija ispravno PERSON — temelj zdrav,
reklasifikacija tamo mjerodavna.

**Koreferencija — treće viđenje:** "is the same person as" (Baskerville=Henry)
opet u ventilu. Potvrda s130: pripada bb_10, ne bb_10c.

## 8. bb_web_export — popravljen, NIJE pokrenut (namjerno)

`get_ner_relacije` prepravljen (backup .bak_s131, str.replace+assert):
tip_veze/klasa → fine/coarse/afinitet/audit; JOIN bb_ner_tip_veze → **LEFT** JOIN
bb_ner_massey (fine NULL relacije MORAJU ostati u izlazu — mapa kretanja).

**Export NIJE pokrenut:** web trenutno konzistentan sam sa sobom (stari JSON +
stari JS koji čita klasa P/M/O). Pokretanje exporta bez prilagodbe nlp.html =
javno slomljen DocRE tab. **Novi JSON i novi JS idu ZAJEDNO sljedeće sesije**
("u jednom dahu" obrazac). BB_VERSION ostaje s129.4.

## 9. Lekcije

1. **Dijagnostika prije arhitekture** — 22-sekundni read-only eksperiment
   presudio izbor između 4 varijante s dokazom umjesto slutnje. "Mjeri pa
   definiši" važi i za arhitektonske odluke, ne samo pragove.
2. **Dvoznačan nalaz je nalaz** — silhouette (globalno slabo) + golo oko
   (lokalno koherentno) zajedno su dali precizniju presudu nego bilo koji sam:
   instrument za audit da, za sudiju ne.
3. **awk pada na kategorijama s razmacima** ("unrequited love interest") —
   moj pipeline za dominantno mapiranje slomljen, prešlo se na Python.
   Za parsiranje s netrivijalnim poljima: Python, ne awk/sed (proširenje
   postojećeg ledger pravila).
4. **Filter razotkriva sloj ispod sebe** — PERSON-PERSON filter nije pogriješio
   na Alisi, on je IZMJERIO šum tipova. Popravka pripada sloju gdje je problem
   (bb_10), ne labavljenju filtera u bb_10c (liječenje simptoma u pogrešnom sloju).
5. **Higijena /tmp backupova** — pri svakom novom dumpu obrisati prethodni
   (Flaviov podsjetnik; pre_cascade već bio obrisan, pre_docre obrisan sad).
6. **Provjeri kvalitet javnih podataka IZ PODATAKA** (drugi put, s130 #6):
   fine→coarse nije čista funkcija — dominanta izmjerena, ne pretpostavljena.

## 10. Završno stanje

- **Baza:** bb_ner_massey (29), bb_ner_relacije s fine/afinitet/audit_kosinus,
  UNIQUE(izvor,cilj); bb_ner_tip_veze NE POSTOJI. Hound 78 (29 fine) + Alice 60
  (10 fine) reklasifikovani. Backup: bb_backup_pre_massey_20260712.
- **Kod:** bb_10c_docre.py prepisan (+--reklasifikuj); bb_web_export.py
  get_ner_relacije prepravljen; sandbox_cluster_probe.py novo (dijagnostička
  sonda, ostaje kao alat). Backupi: .bak_s131 ×2.
- **Web:** NETAKNUT → BB_VERSION s129.4. ⚠️ NE pokretati bb_web_export dok
  nlp.html ne bude prilagođen.
- **Logovi:** cluster_probe_s131, reklas_{hound,alice}_dry_s131,
  reklas_{hound,alice}_s131.

## 11. Sljedeći koraci (s132)

1. **nlp.html + bb_web_export pokretanje — ZAJEDNO:** DocRE tab čita
   fine/coarse/afinitet; boja po coarse (3 klase umjesto P/M/O), afinitet kao
   vizuelni predznak (boja/stil ivice?), ventil/mjesta vizuelno razlučivi;
   i18n ×5; browser test; BB_VERSION bump.
2. Koreferencija kao faza u bb_10 (+ type audit — novi, s131).
3. Margin-based razmatranja ventila VIŠE NISU POTREBNA (ventil sad LLM-ov
   "ostalo", živ po konstrukciji) — skinuto s liste.
4. Tek potom: `run_ner.sh --knjiga all --force` (pokreće Flavio).
5. Nezavisno stoje: prompt na stranici, xray-export stapanje, Sloj 2 DocRE,
   noćni razgovori, DB registar→engleski, .bak čišćenje (sad 16).

---
*Flavio & Claude · Buchenberg · Sesija 131 · 12. jul 2026.*
