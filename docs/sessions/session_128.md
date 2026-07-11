# Session 128 — DocRE dizajn (relacije van rečenice): arhitektura + par-vođena proba

**Datum:** 11. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Otvaranje Dio 2 stavke #1 iz s127 — relacije van rečenice (DocRE).
Sesija je bila prvenstveno DIZAJNERSKA: kroz dijalog iskristalisana arhitektura
NER proizvodnje vs izvoza, oblik skladišta relacija, i par-vođena strategija
ekstrakcije. Završeno probnim prolazom (glm-5.2) koji je potvrdio pristup i dao
sirovinu za rječnik grupa. NIJEDNA promjena baze/weba — samo probni skript
(nije commitovan) + dokumentacija. Flavio se udaljio pred kraj; zatvaranje
(session doc, README, memorija) Claude uradio samostalno uz eksplicitno dato
jednokratno ovlaštenje (izuzetak od protokola prikaži→OK→izvrši).

## Health snapshot
Početak: bb_recenice 50.624, bb_prevodi_recenica 1.518.170, bb_prev_recenica
296.578 (nepromijenjeno od s125/s126/s127 — Flavio nije pokretao runove). Git
početak: buchenberg HEAD 283b4cc (s127), buchenweb 4c3e2d5 (s127). Sve zeleno,
Ollama Cloud (glm-5.2, mistral-large-3:675b, gemma4:31b) OK. 8 poznatih `.bak`
fajlova + poznati lažni "buchenweb zaostaje" alarm. Kraj sesije: brojevi
nepromijenjeni.

## Kontekst — pitanje koje je pokrenulo dizajn
Flavio je vjerovao da je `bb_10_ner_llm.py` ugrađen u web-export (pa bi sve knjige
automatski dobile llm NER). Provjereno u kodu: NIJE. `bb_web_export.py` je čist
read/export sloj (`get_ner`/`get_ner_veze` samo SELECT-uju/agregiraju, ništa ne
upisuju). LLM sloj postoji SAMO za Hound (id 1); ostale knjige samo classic.
Ovo je otvorilo dublju raspravu o arhitekturi, koja je i glavni rezultat sesije.

## Ključne dizajnerske odluke (kroz dijalog)

### 1. Proizvodnja vs izvoz — čvrsta granica
- **Proizvodni sloj** (bb_09 classic, bb_10 llm, budući DocRE): zove LLM/spaCy,
  MISLI, UPISUJE u bazu. Sporo, skupo, zavisi od Ollame, pušta se rijetko/namjerno.
- **Izvozni sloj** (bb_web_export): ČITA bazu, pravi JSON. Brzo, često, read-only.
- Isti obrazac kao prevodilački pipeline (bb_03→bb_08→bb_04) odvojen od web-exporta,
  i kao xray-export. LLM poziv unutar web-exporta = anti-pattern (satima bi trajao).
- **Flaviov princip (jači od Claudeovog prvobitnog):** jednom kad je podatak u bazi,
  PRIKAZ ne mari kako je došao. Web-export = strogo read-only.

### 2. Xray-export → kandidat za stapanje u web-export
Flavio: xray-export ne mijenja bazu (samo čita + piše JSON) → po pravilu
"read-only pripada web-exportu" trebalo bi ga stopiti. Zabilježeno kao TODO
(provjeriti da xray-export zaista ništa ne upisuje, pa spojiti; provjeriti i
`--knjiga all` podršku). NIJE rađeno ove sesije.

### 3. NER orkestracija — buduće `ner_prepare` / `run_ner.sh`
Porodica NER proizvodnih skripti (bb_09/bb_10/DocRE) ostaje razdvojena dok se
razvija, pa se objedini pod JEDAN orkestrator (radni naziv `ner_prepare`, prefiks
`ner_`) s `--knjiga all`. Cilj arhitekture:
```
ner_prepare  (classic + llm + docre; --knjiga all; MIJENJA bazu)
      ↓
web_export   (čita sve, READ-ONLY; +xray stopljen)
```
Rješava Flaviovu bojazan od množenja skripti: jedan proizvodni ulaz, jedan izvoz.

### 4. Skladište relacija — DVIJE tabele, ne jedna (Flaviov kriterij)
Claude prvo gurao jednu uniformnu tabelu; Flavio ispravio jasnim kriterijem:
- isti objekat, razlikuje se samo NAČIN DOBIJANJA → jedna tabela + oznaka
  (type/method/faza), kako smo radili entitete.
- **različiti atributi ILI isti atribut s RAZLIČITIM SEMANTIČKIM ZNAČENJEM →
  dvije tabele.**
Co-occurrence i DocRE padaju na drugom kriteriju: `tezina` kod co-occ = broj
zajedničkih rečenica (simetrično, statistički); kod DocRE bi značila pouzdanost.
`entitet1→entitet2` kod co-occ = kanonski poredak BEZ značenja; kod DocRE NOSI
smjer. Isti stupac, različito značenje → DVIJE TABELE.

**Finalni oblik (dizajniran, NIJE još kreiran — sljedeća sesija):**
```
bb_ner_veze  (co-occurrence, simetrična, statistička)
  id serial PK, knjiga_id FK, entitet1_id FK, entitet2_id FK (kanonski manji<veći),
  tezina int
  → materijalizovati (preseliti iz sadašnjeg self-joina u get_ner_veze)

bb_ner_relacije  (docre, USMJERENA, narativna, s dokazom)
  id serial PK, knjiga_id FK, izvor_id FK, cilj_id FK (smjer izvor→cilj),
  tip_veze varchar (kanonska grupa ~10, za boju/filter/graf),
  opis text (slobodni LLM tekst, vjeran, za prikaz na klik),
  dokaz text (citat), dokaz_pozicije int[]
```
- **`method` NIJE u novim tabelama** — implicitan preko `entitet_id` (Watson-classic
  i Watson-llm su različiti id-jevi). Web-export čitač JOIN-uje bb_ner_entiteti i
  filtrira `method` tamo → toggle classic/with-llm bira i sloj veza. Svjesna odluka.

### 5. Materijalizacija co-occurrence — DA (Flaviova odluka)
Trenutno co-occurrence se računa u letu (self-join u `get_ner_veze`). Flavio: po
"web-export read-only" pravilu, materijalizovati u `bb_ner_veze` → web-export čita
obje tabele uniformno, NULA računanja. Jednokratni migracijski posao.

### 6. Rječnik grupa (tip_veze) — dvoprolaz, mjeri prije definisanja
Flaviov prijedlog (= poznati "open IE + kanonikalizacija"): prvi prolaz slobodni
tekst (vjeran), drugi prolaz sažima u ~10 grupa. Dvije varijante drugog prolaza:
- A: LLM sam grupiše (razumije značenje, ali rječnik nestabilan preko knjiga)
- B: **embedding slobodnog opisa → najbliža fiksna grupa** (e5-large kosinus;
  grupe fiksne/uporedive preko knjiga; konzistentno s s90 "grounding kroz
  embedding, ne LLM tumačenje"). **Preporuka: B.**
Odluka: NE definisati grupe unaprijed — pustiti prvi prolaz, pa grupe kristalisati
iz stvarnih opisa (opcija b: mjeri prije nego definišeš).

### 7. Strategija ekstrakcije — PAR-VOĐENA, ne prozor-vođena (Flaviov preokret)
Claudeov prvi probni skript klizao je prozor mehanički preko teksta. Flavio:
zašto "iz početka"? Imamo razriješene entitete i TAČNE POZICIJE svake pojave
(`bb_ner_recenica`). Kreni OD entiteta/parova, ne od teksta. Preokrenuta logika:
```
za svaki PAR entiteta s ≥PRAG bliskih susreta (|poz_a-poz_b| ≤ prozor):
    skupi regione gdje su blizu → daj LLM-u BAŠ te odlomke
    → jedna USMJERENA veza po paru, više dokaza, grounded, rangirano po važnosti
```
Prednosti: ne baca prethodni rad, efikasno (samo tamo gdje entiteti žive),
prirodno hvata "van rečenice" (prozor oko para hvata i susjedne rečenice).

## Mjerenja (read-only statistika — oblikovala dizajn)
Prije ijednog LLM poziva, izmjerena "geografija entiteta" u Houndu (llm sloj, 179
entiteta):
- **Glavni likovi raspoređeni kroz cijelu knjigu:** Holmes 189 pojava (raspon
  3–3688), Henry Baskerville 153, Watson 109 (raspon 3839), Charles Baskerville 94,
  Mortimer 90, Stapleton 64. Par Holmes↔Watson sreće se desetine puta → veza
  višestruko potvrđena.
- **Neki entiteti usko lokalizovani** (čisto lokalne veze): Lestrade 9 pojava,
  raspon samo 236 (sve u finalu 3398–3634); Charing Cross Hospital raspon 833.
- **Dvojnost potvrđena:** Baskerville PERSON (21) i GPE (21) — dva reda, kako je
  llm sloj sačuvao (osoba + imanje).
- **Bliski parovi (±10, rangirani):** Holmes–H.Baskerville 140, Holmes–Mortimer 128,
  Holmes–Watson 127, Stapleton–H.Baskerville 99, ... `najmanja_udalj=0` posvuda
  (glavni parovi često u ISTOJ rečenici). NAPOMENA: razilazi se s s126 baseline
  (co-occ mreža "skoro prazna", 28 veza ≥2) — vrijedi provjeriti zašto sljedeću
  sesiju (moguće: stari co-occ broji samo doslovno istu rečenicu + prag ≥2 filtira).

## Probni prolaz — rezultat (bb_10b_docre_probe.py, 15 najjačih parova)
Par-vođeno, prag ≥3, prozor ±5, glm-5.2 temp 0.0, SAMO ISPIS (nula upisa).
15 parova ispitano, **14 relacija nađeno**. Kvalitet visok, smjer+tip+dokaz legli:
- Henry Baskerville →[is the client of / seeks the help of]→ Holmes (directed)
- Mortimer →[seeks the assistance of]→ Holmes (directed)
- Holmes ↔[friend and companion of]↔ Watson (**mutual** — LLM sam prepoznao simetriju)
- Stapleton →[neighbor who wants Henry to stay at Baskerville Hall]→ Henry (directed)
- Watson →[accompanying and protecting]→ Henry (directed)
- Barrymore →[butler and servant of]→ Henry / →[butler of]→ Charles (isti odnos
  preslikan kroz smjenu vlasnika)
- Holmes →[is investigating the death of]→ Charles (detektivska relacija)
- **Charles →[is the uncle of and left his estate to]→ Henry** (srodstvo+nasljeđe
  iz "son of Sir Charles Baskerville's younger brother" — narativno centralno,
  co-occurrence to nikad ne bi dalo)

**Sirovina za rječnik grupa** (svi slobodni opisi, svaki 1× ali prirodno se grupišu
u ~8–9 grupa): srodstvo/nasljeđe · prijateljstvo · profesionalni angažman
(klijent/konsultuje) · služba (batler) · istraga · zaštita/pratnja · prostorno ·
susjedstvo · poznanstvo. Tačno u ciljanom opsegu (~10).

## Lekcije
- **Provjeri kod prije nego vjeruješ sjećanju o arhitekturi.** Flaviova pretpostavka
  (bb_10 u web-exportu) bila netačna; grep + čitanje razjasnilo za sekunde.
- **Flaviov kriterij "dvije tabele vs jedna":** isti objekat/različit način dobijanja
  → jedna+oznaka; različita semantika istog atributa → dvije. Claude gurao lažnu
  uniformnost; Flaviov kriterij precizniji. Zabilježiti kao trajno pravilo dizajna.
- **Mjeri geografiju prije nego biraš prozor.** Statistika pozicija/udaljenosti
  (Flaviova ideja) dala je par-vođenu strategiju koja je bolja od mehaničkog prozora
  — i pokazala da su glavni parovi u istoj rečenici, sporedni raspršeni.
- **Par-vođeno > prozor-vođeno:** kreni od znanja koje već imaš (entiteti+pozicije),
  ne od sirovog teksta. Isti X-Ray stav: iskoristi prethodni sloj kao temelj.
- **DocRE ima slojeve:** lokalne veze (±N prozor, gradimo sad) vs raspršene veze
  (ubica otkriven poglavlja kasnije — treba širi mehanizam, moguće s90 "rasplet kao
  upit"). Ne rješavati oba odjednom; Sloj 1 prvo.

## Završno stanje
- Baza: NETAKNUTA (nijedan upis; sve mjerenje read-only). llm sloj i dalje samo Hound.
- `src/bb_10b_docre_probe.py`: probni par-vođeni DocRE skript, ISPIS bez upisa.
  Ostavljen na serveru NAMJERNO (živi zapis pristupa), NIJE commitovan.
- `logs/docre_probe.log`: izlaz probe (15 parova).
- Web: NETAKNUT → BB_VERSION ostaje s127.
- Git: buchenberg/buchenweb nepromijenjeni osim ovog session doca (+README).
- Flavio odsutan pred kraj; zatvaranje samostalno (jednokratni izuzetak, dat eksplicitno).

## Sljedeći koraci (redoslijed za sljedeću sesiju)
1. **Kristalisati rječnik grupa (tip_veze)** iz probnih opisa — ~8–10 grupa;
   odlučiti varijantu drugog prolaza (preporuka B: e5-large embedding → najbliža grupa).
2. **Kreirati tabele** `bb_ner_veze` + `bb_ner_relacije` (backup prije DDL, pravilo s123).
3. **Prebaciti probni skript u produkciju** — logika u `bb_10` (nova faza) ili
   `ner_` porodicu; `--knjiga all`; upis u `bb_ner_relacije` (+drugi prolaz grupisanje).
4. **Materijalizovati co-occurrence** u `bb_ner_veze`; prebaciti `get_ner_veze` s
   računanja na čisto čitanje.
5. **Web** — web-export čita obje tabele (method-svjesno preko entitet JOIN-a);
   nlp.html prikaz relacija (usmjeren graf, boja po tip_veze, klik→opis+dokaz).
6. Provjeriti razilaženje s s126 co-occ baseline (28 vs stotine bliskih parova).
7. **xray-export** — provjeriti da je read-only, razmotriti stapanje u web-export;
   `--knjiga all` na NER skriptama.
8. Kasnije: Sloj 2 (raspršene veze, s90 rasplet-kao-upit); bb_10/docre na ostale knjige.
9. Nezavisno stoje: prompt na stranici (X-Ray prozirnost), i18n toggle labela
   (Classic/With LLM), noćni razgovori (s124), SR geo_c4_p1 mixed-script, 8 .bak,
   DB registar→engleski.

---
*Flavio & Claude · Buchenberg · Session 128 · 11. jul 2026.*
