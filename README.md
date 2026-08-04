# Buchenberg — Project Documentation V3

**Datum kreiranja:** 14. maj 2026.  
**Poslednje ažuriranje:** 2. avgust 2026. (sesija 158)  
**Autor:** fladroid  
**Status:** Aktivan razvoj — bb pipeline operativan, multi-knjiga, web portal

---

## 1. Filozofija i osnovna ideja

### Poreklo ideje

Projekat je nastao iz eksperimentisanja sa **embeddingima i vektorskom aritmetikom**. Centralna spoznaja: semantičko značenje rečenica može se predstaviti kao vektori u višedimenzionalnom prostoru i između tih vektora može se meriti sličnost (cosine similarity).

### Problem koji rešavamo

Kako proveriti kvalitet mašinskog prevoda kada ne govoriš ni izvorni ni ciljni jezik?

**Rešenje — back-translation pipeline:**

```
RE (EN original) → metoda prevoda → RF (ciljni jezik)
RF → ista metoda → RFE (back-translation na EN)
score = cosine_similarity(RE, RFE)   ← back_score
score = cosine_similarity(RE, RF)    ← translation_score (direktni)
```

### Dvije metrike kvaliteta

| Metrika | Formula | Opis |
|---------|---------|------|
| `score` | cosine(RE, RFE) | Kvalitet back-translationa |
| `translation_score` | cosine(RE, RF) | Direktna semantička sličnost |

`translation_score` je pouzdaniji pokazatelj jer ne ovisi o back-translation procesu.

### Višestruko takmičenje metoda

Isti postupak se radi sa više metoda prevoda. Metoda sa višim kompozitnim scoreom **pobeđuje** za tu rečenicu. Krajnji rezultat je hibridni prevod koji kombinuje najbolje od svake metode.

### LLM sudija

Gemma4:31b kao blind sudija ocjenjuje svaki prevod po 3 kriterija (grammar, naturalness, fidelity) na skali 0.0–1.0. Formula pobjednika:

```
finalni_score = 0.4 × kompozitni + 0.6 × sudija_avg
kompozitni = (score + translation_score) / 2
```

Sudija nosi 60% težine — kvalitativna ocjena važnija od čistog cosinus scorea.

### Cilj projekta

Prevod knjiga sa isteklom licencom sa **Project Gutenberg** na više jezika, koristeći isključivo open source i besplatne alate.

**Važna napomena:** *Važniji je put od cilja.* Pipeline koji gradimo je generički i primenljiv daleko šire od samog prevoda knjiga.

### Authorship & Collaboration

Buchenberg is conceived, designed and maintained by **Flavio** (fladroid). The project's philosophy, methodology, architecture and all final design decisions are his — and remain his sole responsibility.

The project is built in ongoing collaboration with **[Claude](https://claude.ai)** (Anthropic) — not as a code-completion tool, but as a working partner across more than 100 documented sessions: implementation, debugging, analysis, and the conceptual dialogue that shaped pages like *Geometry of Meaning* and *Art*. Every session is recorded in `docs/sessions/`, where both names appear — a deliberate choice, in the spirit of this project's X-Ray attitude: the process of building should be as transparent as the thing built.

*Flavio & Claude · Buchenberg · 2026*

---

## 2. Ciljni jezici

### Grupa 1 — Južnoslovenski
`hr` (hrvatski), `sr` (srpski), `bs` (bosanski), `sl` (slovenački), `mk` (makedonski), `bg` (bugarski)

### Grupa 2 — Zapadnogermanski
`de` (nemački), `nl` (holandski), `af` (afrikaans)

### Grupa 3 — Romanski/Latinski
`fr` (francuski), `it` (italijanski), `es` (španski), `pt` (portugalski), `ro` (rumunski)

### Egzotični (identificirani, odgođeni)
- Jidiš `yi` (`ydd_Hebr`) — NLLB podržava, Gemma slaba
- Frizijski `fy` (`fry_Latn`) — ~470k govornika, ograničena NLLB podrška
- Luksemburški `lb` (`ltz_Latn`) — NLLB podržava, ~400k govornika

---

## 3. Modeli prevoda

| Model | Engine | Temperatura | Faza | Napomena |
|-------|--------|-------------|------|---------|
| `mistral-large-3:675b` | Ollama Cloud | 0.1 / 0.8 | 1 (+0.8 faza 2) | Novi par od s114; nativno ne-misleći |
| `glm-5.2` | Ollama Cloud | 0.1 / 0.8 | 1 (+0.8 faza 2) | Novi par od s114; poštuje think:false |
| `nllb-600M` | Lokalno (CPU) | 0.0 | 1 | Deterministički; dobar za kratke rečenice |
| `gemma4:31b` | Ollama Cloud | 0.0 | — | Samo sudija — ne prevodi |

**Aktivni modeli žive u bazi** (`bb_modeli.aktivan`, s114) — orchestratori ih čitaju kroz `src/bb_aktivni_modeli.py --faza N`. Stari par `gemma3:12b`/`ministral-3:14b` (Ollama retire 15. jul 2026) zamrznut kao istorijska referenca: `aktivan=false`, svi prevodi netaknuti.

**Zamjena IZVRŠENA (s114):** novi par registrovan (id 18–23) i testiran kroz cijeli lanac (Hound Copy hr 1–10). Sudija gemma4:31b i NLLB nepogođeni. Istorijat izbora: s109–s112.

### Temperatura pattern po jezičnoj grupi

Utvrđen empirijski na uzorku s1–s350 (HR, BS) i s1–s100 (ostali):

| Jezična grupa | Pobjednički model | Temperatura |
|--------------|-----------------|-------------|
| Južnoslavenski (hr, bs, sr, sl) | gemma3 | 0.1 blago bolja |
| Germanski (de, nl, af) | gemma3 / ministral | 0.8 bolja |
| Romanski (fr, it, es, pt) | ministral | 0.1 bolja |
| Rumunski (ro) | gemma3 | 0.8 (odstupanje od romanskog patterna) |

> ⚠️ Pattern je statistički trend, ne pravilo — na manjim uzorcima može odstupati. Uvijek koristiti sve 4 cloud kombinacije i pustiti sudiju da odluči.

### Paralelno izvršavanje

**Ollama Cloud nalog je Pro tier (nadograđeno s free) — paralelni pozivi su podržani.** Najmanje posljednje dvije sedmice (od otprilike sredine/kraja juna 2026) svi pipeline runovi — i sa starim i sa novim modelima — redovno trče paralelno; sa starim (jeftinijim) modelima Flavio je često pokretao i 5 paralelnih tokova odjednom. NLLB (lokalni CPU) i dalje radi nezavisno paralelno s bilo kojim cloud tokom. Eksperiment s118/s119 (4 paralelne grupe) izmjerio je ~3.77× agregatno ubrzanje sa 4 paralelna toka naspram jednog solo — **taj broj je KORIGOVAN u s132 na ~2.47×** (efikasnost ~62%, ne linearno skaliranje). s119 baseline (0.924 rec/min) bio je izveden iz drugog dana/knjige/jezika i sam degradiran; prvi kontrolisani A/B (iste knjige, isti jezici, susjedni opsezi) daje solo 1.33–1.48 rec/min. Pojedinačni proces usporen **1.5–1.7×** u četvorci. Dio usporenja je LOKALAN (NLLB na foxuno CPU: do 2.66× sporiji — nezavisan instrument, ne cloud). glm-5.2 pati znatno više od mistral-large-3 (2.6× vs 1.1×). ⚠️ Konfaund: paralelni prolaz uveče, sekvencijalni noću — režim i doba dana nisu razdvojeni. Kvalitet nepromijenjen u oba režima. Detalji: `docs/sessions/session_132.md`.

> ⚠️ **Istorijska napomena:** do nadogradnje na Pro (sredina/kraj juna 2026) nalog je bio free tier s ograničenjem od jedne sesije u isto vrijeme — stariji session dokumenti (npr. do ~s100) pominju to ograničenje i tretiraju paralelne procese kao grešku za ispravljanje. To više NE VAŽI.

---

## 4. bb pipeline — arhitektura

### Filozofija

Povratak na osnovu (sesija 34): čista shema, nova baza `bb`, bez GA, bez NLP enrichmenta. Jedina metrika kvaliteta je cosinus sličnost + LLM sudija.

### Faze pipeline-a

```
bb_03_prevod.py    → prevod + back-translation + cosine score (5 modela)
bb_06_enkodiranje.py → enkodira prevode → upisuje prevod_vektor
bb_08_sudija.py    → Gemma4 blind evaluacija (grammar/naturalness/fidelity)
bb_04_pobjednik.py → izbor pobjednika po finalnom scoreu
bb_05_export.py    → export u output/naziv_knjige_lang.txt
bb_web_export.py   → JSON export → Apache2 web prikaz
```

### Pokretanje — standardni workflow

> ⚠️ **s114:** modeli se čitaju iz baze (aktivni po fazi, helper `bb_aktivni_modeli.py`) — kanonski put je `run_pipeline.sh` (faza 1) / `run_faza.sh --faza N` (s134). `bb_03` prima `--faza N` (default 1; 2+ = refine), `--refine` flag NE POSTOJI. Primjeri ispod su istorijski obrazac direktnog poziva — imena modela zamijeni aktivnima.

```bash
# 1. gemma3@0.8 (cloud)
PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_03_prevod.py \
  --knjiga 1 --od 1 --do 100 --model "gemma3:12b" --temp 0.8 \
  --embedder "multilingual-e5-large" --jezici hr \
  > logs/naziv_hr_gemma3_08.log 2>&1 &

# 2. gemma3@0.1 i 0.8 u jednom pozivu (cloud, nakon što Run 1 završi)
PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_03_prevod.py \
  --knjiga 1 --od 1 --do 100 --model "gemma3:12b" --temp 0.8 0.1 \
  --embedder "multilingual-e5-large" --jezici hr \
  > logs/naziv_hr_gemma3.log 2>&1 &

# 3. NLLB (lokalni, paralelno s cloud)
PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_03_prevod.py \
  --knjiga 1 --od 1 --do 100 --model "nllb-600M" --temp 0.0 \
  --embedder "multilingual-e5-large" --jezici hr \
  > logs/naziv_hr_nllb.log 2>&1 &

# 4. ministral@0.8 i 0.1 u jednom pozivu (cloud, nakon gemma3)
PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_03_prevod.py \
  --knjiga 1 --od 1 --do 100 --model "ministral-3:14b" --temp 0.8 0.1 \
  --embedder "multilingual-e5-large" --jezici hr \
  > logs/naziv_hr_ministral.log 2>&1 &

# 5. bb_sr_cirilica (SAMO za srpski — pokrenuti nakon bb_03, prije sudije!)
venv/bin/python src/bb_sr_cirilica.py

# 6. Sudija
PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_08_sudija.py \
  --knjiga 1 --od 1 --do 100 --jezici hr \
  > logs/naziv_hr_sudija.log 2>&1 &

# 7. Pobjednici
venv/bin/python src/bb_04_pobjednik.py --knjiga 1 --od 1 --do 100 --jezici hr

# 8. Web export
venv/bin/python src/bb_web_export.py
```

> ⚠️ **Logovanje:** uvijek koristiti `PYTHONUNBUFFERED=1 nohup time` — trajanje mora biti vidljivo u logu.
> ⚠️ **`--temp` prima listu:** `--temp 0.8 0.1` pokreće obje temperature u jednom pozivu (sesija 43).

### Batch + fallback pattern

Kritičan za sve LLM pozive. S1–s3 su metadata (naslov/autor/poglavlje) — modeli ih spajaju i vraćaju pogrešan broj separatora. `bb_03_prevod.py` ima automatski fallback na single mode:

```python
parts = translate_batch(...)
if parts is None:
    parts = [translate_single(text) for text in chunk]
```

---

## 4b. NER / DocRE — imenovani entiteti i relacije

Paralelni analitički sloj uz pipeline prevoda — NE utiče na prevod ili izbor pobjednika, služi za istraživanje strukture teksta (likovi, mjesta, odnosi).

> ⚠️ Ne miješati s "NER-kao-kontekst-za-prevod" (pokušaj da NER poboljša kvalitet prevoda, s135-138) — ta nit je ZATVORENA negativnim nalazom (s138) i potpuno je odvojena od ovog analitičkog sloja.

### Tri sloja (svaki gradi na prethodnom)

| Sloj | Skripta | Motor | Šta radi |
|------|---------|-------|----------|
| Classic | `bb_09_ner.py` | spaCy | NER ekstrakcija (osoba/mjesto/org) + co-occurrence veze unutar rečenice |
| LLM | `bb_10_ner_llm.py` | glm-5.2 | Type reconciliation — rješava spaCy nekonzistentnosti (isto ime, različit tip), grounding u dokaznim rečenicama |
| DocRE | `bb_10c_docre.py` | glm-5.2 | Usmjerene relacije (izvor→cilj) van granica rečenice; PERSON-PERSON parovi; Massey/Bamman taksonomija (29 fine kategorija → 3 coarse: social/familial/professional) + afinitet (positive/negative/neutral) |

### Orkestracija

`run_ner.sh --knjiga N|all [--force]` — pokreće `bb_09→bb_10→bb_10c`. `--force` je svojstvo PROLAZA ne faze — prosljeđuje se svim trima skriptama podjednako.

### Ključne tabele

- `bb_ner_veze` — co-occurrence, materijalizovan (simetrična, `entitet1<entitet2`, `tezina`=broj zajedničkih rečenica)
- `bb_ner_relacije` — DocRE usmjerene relacije (`izvor_id→cilj_id`, opis, dokaz, fine/coarse/afinitet/audit_kosinus)
- `bb_ner_massey` — Massey/Bamman lookup (29 fine kategorija: friend/enemy/parent/servant/lovers…)

FK politika: veze/relacije padaju kroz `CASCADE` kad entitet nestane — zavisnost enkoduje shema, ne skripta.

### Pokrivenost (s147)

Classic+LLM: svih 9 originalnih knjiga. DocRE: 5/12 (Hound, Alice, J&H, Flatland, Hound Copy) — namjerno ograničeno na knjige <2000 rečenica (s133); veće knjige idu sekvencijalno kad ima resursa, Flavio pokreće samostalno.

### Kriterij zatvaranja linije (s133)

Prihvatanje je TEHNIČKO — izvršava se / upisuje potpun sloj / izvoziv u web. Kvalitet same klasifikacije je NALAZ, ne kriterij (npr. Flatland ima samo 1 fine kategoriju od 101 relacije — nalaz o žanru: nema likova u karakternom smislu, ne kvar mehanizma).

### Web prikaz

`nlp.html` ("Named Entities & Relations") — tri ravnopravna pogleda: Classic | With LLM | DocRE, usmjeren graf (D3 force), klik→opis+dokaz.

---

## 5. Baza podataka — bb shema

### Tabele

| Tabela | Opis |
|--------|------|
| `bb_jezik` | 14 jezika |
| `bb_metode` | **Metod = tip operacije** (s134). `root` boolean: `base` (root, izvršiv tačno jednom) i `self-refine` (ponovljiv M puta). Metod nosi SADRŽAJ (šta se radi, koji seed); faza nosi REDOSLIJED. |
| `bb_faze` | **Faza = jedno izvršavanje metoda** (s134): redni broj + jedinstveni identifikator. `metod_id` FK → `bb_metode` (**1 metod : M faza**). Partial UNIQUE `WHERE metod_id=1` čuva ROOT-invarijantu u SHEMI. |
| `bb_modeli` | **s142: ČIST katalog imena** (`id, naziv, aktivan`, UNIQUE(naziv)) — a1 osa. Slijepljivanje s temperaturom/fazom (staro, do s142) UKLONJENO. |
| `bb_temperature` | **NOVO s142** — a2 osa. `id, vrijednost REAL UNIQUE`. |
| `bb_promptovi` | **NOVO s142** — a3 osa. `id, naziv UNIQUE, prompt_prevod_batch, prompt_prevod_single, prompt_back_batch, prompt_back_single` (TEXT, `.format()` template s placeholderima `{jezik_naziv}`,`{numerirani}`,`{tekst}`,`{seed}`,`{prevod}`). **s143:** 4 reda: `base`, `refine`, `refine-lenient` (pre-s135 stil, "keep if optimal"), `refine-strict` ("must be better or meaningfully different") — nijedan od zadnja dva još nije vezan za fazu preko `bb_faze_a3`. |
| `bb_faze_a1` / `bb_faze_a2` / `bb_faze_a3` | **NOVO s142** — tri simetrične veze faza↔osa: `faza_id` FK + izbor FK (`model_id`/`temperatura_id`/`prompt_id`) + `aktivan`, UNIQUE(faza_id, izbor). Faza bira iz svake ose NEZAVISNO — nema sprege, nema "parova" u shemi. `bb_aktivni_modeli.py` i dalje vraća samo istorijski korišćene (model,temp) parove (Flaviova odluka s142) — orkestratori NE rade pun unakrsni proizvod a1×a2. |
| `bb_embeddings` | Embedder definicije |
| `bb_knjige` | Knjige (naziv, autor, gutenberg_id UNIQUE) |
| `bb_recenice` | Rečenice (pozicija, tekst, knjiga_id) |
| `bb_prevodi_knjige` | **s142:** `faza_id, model_id, temperatura_id, prompt_id` sad EKSPLICITNE kolone (ranije samo `model_id` slijepljen). UNIQUE(knjiga, jezik, faza, model, temperatura, prompt, embedder) — 7 kolona. |
| `bb_prevodi_recenica` | Prevod + back_translation + score + translation_score + prevod_vektor + sudija ocjene |
| `bb_prev_knjige` | Finalni prevod knjige UNIQUE(knjiga, jezik) |
| `bb_prev_recenica` | FK na ukupnog pobjednika u bb_prevodi_recenica |
| `bb_prev_recenica_faza` | Fazni pobjednik po (rečenica, faza) — UNIQUE(prev_knjige, prevodi_recenica, faza). Puni ga bb_04 (faza-blok, DELETE+INSERT po opsegu, od s106). |
| `bb_model_registar` | Registar modela po IMENU (naziv PK, vrsta, uloge TEXT[]) — s123. Vrsta/uloga = identitet imena (ne instance); uloge 1:N. Uzak registar, bb_modeli nedirnut. Bez DEFAULT. Hrani stats Tabelu 0. |
| `bb_ner_veze` | Co-occurrence MATERIJALIZOVAN (s129): `entitet1_id<entitet2_id` (kanonski), `tezina` (broj zajedničkih rečenica). Preseljeno iz get_ner_veze self-joina → web-export čita. method implicitan preko entitet_id. |
| `bb_ner_relacije` | DocRE usmjerene relacije: `izvor_id→cilj_id`, `opis` (slobodni LLM tekst), `smjer`, `dokaz`, `dokaz_pozicije` int[], `pouzdanost` + **Massey klasifikacija (s131)**: `fine` FK na bb_ner_massey (NULL=ventil/osoba-mjesto), `afinitet` CHECK (positive/negative/neutral), `audit_kosinus` (e5-large audit metrika, ne sudija). UNIQUE(izvor_id,cilj_id) — jedna relacija po usmjerenom paru. Hound 78 (29 fine) / Alice 60 (10 fine). |
| `bb_ner_massey` | Massey/Bamman lookup (s131): `fine` PK (29 kategorija: friend/enemy/parent/servant...), `coarse` CHECK (social/familial/professional — dominantno mapiranje izmjereno iz podataka). Čista 1:1 preslika Massey sheme, bez naših dopuna (s130 O6). 'ostalo' NIJE red — ventil je fine=NULL. |
| **FK politika (s130)** | **5 FK-ova na `bb_ner_entiteti(id)` = `ON DELETE CASCADE`**: `bb_ner_recenica.entitet_id`, `bb_ner_veze.entitet1_id`/`entitet2_id`, `bb_ner_relacije.izvor_id`/`cilj_id`. Izvedeni slojevi padaju kad im temelj nestane. Ostala 4 FK-a (`knjiga_id` ×3, `fine`→bb_ner_massey od s131) ostaju **NO ACTION namjerno** — lookup/domen veze, ne izvedeni slojevi. **Skripta briše samo svoj sloj; shema čisti ostatak.** |
| `bb_rag_korpus` | RAG korpus (odgođeno) |

### Metrike kvaliteta

| Metrika | Formula | Opis |
|---------|---------|------|
| `score` | cosine(EN, back_EN) | Informacijska stabilnost |
| `translation_score` | cosine(EN, prevod) | Direktna semantička blizina |
| `kompozitni` | (score + translation_score) / 2 | Cosinus komponenta |
| `sudija_avg` | (grammar + naturalness + fidelity) / 3 | LLM evaluacija |
| `finalni_score` | 0.4 × kompozitni + 0.6 × sudija_avg | Kriterij pobjednika |

### Viewovi — strategija denormalizacije

**Princip:** Sve skripte, reportovi i web export koriste viewove umjesto direktnih JOINova nad tabelama. Kompleksna join logika je enkapsulirana na jednom mjestu — ispravka se radi samo u viewu.

| View | Opis | Tipična upotreba |
|------|------|-----------------|
| `v_prevodi` | Svi prevodi iz `bb_prevodi_recenica` — flat prikaz s modelom, jezikom, embedderom, originalnom rečenicom i svim score-ovima | Analiza, debugging, poređenje modela |
| `v_pobjednici` | Samo pobjedničke rečenice iz `bb_prev_recenica` — isti flat format | Web export, finalni reportovi, statistika |
| `v_knjige_recenice` | knjiga_id, knjiga_naziv, ukupno rečenica po knjizi | Statistika, join osnova |
| `v_prevodi_po_modelu` | knjiga_id, jezik, model, temperatura, broj prevedenih rečenica | Analiza pokrivenosti po modelu |
| `v_sudija_pokrivenost` | knjiga_id, jezik, broj rečenica s ocjenom sudije | Praćenje sudija pipeline-a |
| `v_pobjednici_pokrivenost` | knjiga_id, jezik, broj pobjednika | Praćenje pobjednika |
| `v_status_knjige` | Pivot po modelu/temperaturi — jedan red po knjiga×jezik, sve kolone pokrivenosti | **Dashboard — koristiti na početku svake sesije** |
| `v_status_faza` | **LONG** (s134): knjiga × jezik × faza → broj rečenica s bar jednim prevodom u toj fazi. Deriviran iz majke. **N-faza-safe bez izmjena.** | Pokrivenost po fazama |
| `v_status_faza_model` | **LONG** (s136): knjiga × jezik × faza × model × temp → broj rečenica tog modela. Derivat majke. Detekcija rupa: MAX po (knjiga,jezik,faza) grupi = očekivano. Vidi "počeo pa nije završio", NE "nikad nije počeo". | Kompletnost po modelu; hrani health_check 2b |
| `v_status_faza_matrica` | ⚠️ PRIVREMEN (s134): pivot `f1/f2/f3` — **hardkodovane kolone, NE SKALIRA**; faza 4 traži `CREATE OR REPLACE`. Rješenje = analitičke funkcije (Flavio demonstrira). | Brzi pregled, ne oslanjati se |

#### `_full` sloj (s107) — maksimalna denormalizacija

**Arhitektura:** `v_prevodi_full` je **majka svih analitičkih viewova** — svi budući brojači i namjenski viewovi izvode se iz nje (kreiraju i brišu po potrebi). Stari viewovi gore ostaju netaknuti. Konvencija: sufiks `_full`; svaka kolona nosi prefiks izvora (`knjiga_`, `recenica_`, `jezik_`, `model_`, `faza_`, `embeddings_`) — porijeklo čitljivo iz imena.

| View | Opis |
|------|------|
| `v_corpus` | Domen: `bb_knjige` × `bb_recenice`, svaki ID + njegove vrijednosti. Namjerno IZ BAZNIH TABELA, ne iz majke — 46,6% rečenica još nema nijedan prevod, corpus iz majke bio bi krnji i pomičan. |
| `v_prevodi_full` | **MAJKA**: v_corpus + `bb_prevodi_recenica` + jezik/model/faza (LEFT)/embedder — svi kandidati, sve ocjene, `kompozitni` + `finalni_score` (kanonska formula). Jedini izuzetak od "sve kolone": `prevod_vektor` (1024-dim). |
| `v_pobjednici_full` | Apsolutni pobjednici: `bb_prev_recenica` (pokazivač) → JOIN majka (`pf.*`). |
| `v_pobjednici_faza_full` | Fazni pobjednici: `bb_prev_recenica_faza` + `takmicenje_faza_*` iz pokazivača → JOIN majka. Invarijanta (provjerena, 0 prekršaja): `takmicenje_faza_id = faza_id`. |

`v_corpus` = domen ("šta postoji za prevesti"); `v_prevodi_full` = činjenice ("šta smo uradili"); razlika = napredak (neprevedeno).

**Primjer upotrebe:**
```sql
-- Pobjednici za hrvatski, prvih 10 rečenica
SELECT s_id, model, temperatura, prevod, finalni_score
FROM v_pobjednici
WHERE jezik = 'hr'
ORDER BY s_id
LIMIT 10;

-- Statistika pobjednika po modelu i jeziku
SELECT jezik, model, temperatura, COUNT(*) AS pobjede
FROM v_pobjednici
GROUP BY jezik, model, temperatura
ORDER BY jezik, pobjede DESC;
```

> ⚠️ Novi reportovi i novi JSON exporti pišu se isključivo nad viewovima. Direktni JOINovi nad tabelama su dozvoljeni samo pri inicijalnoj izgradnji novih viewova.

---

## 6. Embedder

| Model | Dim | `--embedder` | Napomena |
|-------|-----|-------------|---------|
| `intfloat/multilingual-e5-large` | 1024 | `multilingual-e5-large` | **Produkcijski embedder** |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | `minilm` | Legacy; bias prema doslovnosti |

**Uvijek koristiti e5-large** u produkciji. MiniLM favorizuje literalne prevode (NLLB) što iskrivljuje pobjednike.

---

## 7. Skripte (`src/bb_*.py`)

| Skripta | Opis |
|---------|------|
| `bb_01_init_lookup.py` | Puni bb_jezik, bb_modeli, bb_embeddings |
| `bb_02_insert_knjiga.py` | Ubacuje knjigu i parsira rečenice (spaCy); lista knjiga je hardcodovana u `KNJIGE` |
| `bb_03_prevod.py` | Prevod + back-translation + cosine score (batch+fallback); Ollama Cloud i NLLB; `--temp` prima listu; `--faza N` default 1, 2+=refine (s114) |
| `bb_04_pobjednik.py` | Bira pobjednika po finalnom scoreu; DELETE filtrira po opsegu |
| `bb_05_export.py` | Export finalnog prevoda u `output/naziv_knjige_lang.txt` |
| `bb_06_enkodiranje.py` | Enkodira prevode → upisuje `prevod_vektor` |
| `bb_08_sudija.py` | Gemma4:31b kao blind sudija → sudija_grammar/naturalness/fidelity/avg; ocjenjuje kandidate aktivnih modela (s114) |
| `bb_aktivni_modeli.py` | Ispisuje aktivne modele zadane faze (`naziv\|temp` linije) — DB izvor za run_pipeline.sh i run_faza.sh |
| `bb_faza_info.py` | Faza -> metod (`metod_id\|naziv\|root`) iz `bb_faze` JOIN `bb_metode`; exit 1 ako faza ne postoji (s134) |
| `run_faza.sh` | **Kanonski orkestrator faze** — `--faza N` (obavezan) `--knjiga --jezici --od --do [--force]`. Metod cita iz baze, modele iz `bb_modeli`. Zamijenio `run_refine.sh` (s134) |
| `bb_toggle_model.py` | Uključuje/isključuje jedan model (a1) za zadanu fazu preko `bb_faze_a1.aktivan` (s156) — koristi ga `run_root_gated.sh` |
| `run_root_gated.sh` | **Wrapper za "gated root"** (s156) — jedan poziv: isključi model iz faze 1 → root (suzen bazen) → gated faza (default 10) → model se UVIJEK vraća aktivan (trap na EXIT). `--knjiga --jezici --od --do [--gated-faza N]` |
| `bb_09_ner.py` | NER classic sloj: spaCy ekstrakcija + **glm-5.2** normalizacija (s130: NE sudija — gemma4 ostaje slijep i fiksan) + upis u bb_ner_entiteti/bb_ner_recenica + **vlastite co-occ veze**. `--knjiga N\|all`, `--force`; spaCy učitan jednom van petlje. DELETE samo svog sloja (`method='classic'`) — izvedeno pada kroz CASCADE. |
| `bb_geometry_export.py` | Generira `data/geometry.json` — UMAP 2D projekcija EN+HR+SR+IT+DE embeddinga za geometry.html; pokreće se ručno (~380s) |
| `bb_web_export.py` | Generira JSON fajlove za Apache2 web prikaz (books, orig, tr, ner, version). NER: get_ner/get_ner_veze primaju `method` param; get_ner_veze ČITA materijalizovanu bb_ner_veze (s129, read-only); nova get_ner_relacije (DocRE) → relacije u llm grani; ner_<id>.json = `{classic, llm:{entiteti,veze,relacije}}` — s127/s129 |
| `bb_sr_cirilica.py` | Transliterira srpske prevode latinica → ćirilica (idempotentna) |
| `bb_10_ner_llm.py` | LLM NER (glm-5.2): type reconciliation konfliktnih entiteta s groundingom dokaznim rečenicama; upis method='llm' paralelno uz classic (s126). Kompletira llm sloj — kopira i nekonfliktne classic entitete kao čiste llm redove (s127). s130: `--knjiga N\|all`, `--force`, održava **vlastite co-occ veze**, preskače knjige bez classic sloja. |
| `bb_10c_docre.py` | DocRE: par-vođena ekstrakcija usmjerenih relacija (prvi prolaz glm-5.2, nedirano od s129) + **drugi prolaz s131 (Massey)**: glm-5.2 (think:false, temp 0.0) klasifikuje iz zatvorene liste 29 fine kategorija (iz baze) + afinitet; "ostalo"→fine=NULL (živ ventil). Deterministički filter: klasifikacija SAMO za PERSON-PERSON parove. `audit_kosinus` = e5-large audit metrika. `--reklasifikuj` = samo drugi prolaz nad postojećim relacijama (UPDATE). `--knjiga N\|all`, `--force`, `--dry-run`. |
| `run_ner.sh` | **NER orkestrator (s130)** — proizvodni ulaz: bb_09 → bb_10 → bb_10c, `set -euo pipefail`. `--knjiga N\|all`, `--force`. **`--force` je svojstvo PROLAZA, ne faze** — prosljeđuje se svim trima. Pojedinačne skripte ostaju samostalno pokretljive (istraživački alat). |
| `bb_xray_export.py` | Generira X-Ray JSON fajlove (`data/xray_<id>_<lang>.json`) — svih 5 kandidata po rečenici s kompletnim scoreovima; pokrenuti nakon `bb_web_export.py` |
| `health_check.py` | Infrastrukturna provjera svih komponenti; čita bb bazu |
| `sandbox_cluster_probe.py` | READ-ONLY dijagnostička sonda (s131): k-means + silhouette nad e5-large embeddinzima DocRE opisa — mjeri vidi li embedding prostor strukturu. Presudila arhitekturu drugog prolaza (klasifikator NE, audit DA). |
| `sandbox_model_probe.py` | READ-ONLY sonda ponašanja Ollama modela (s109). Prima `--models` listu, `--jezik`, `--no-think`. Mjeri: čistoća izlaza, thinking+eval_count+sec (trošak), temp reakcija, batch N/N, round-trip. Baseline (gemma3/ministral)=etalon. Ne dira bazu/pipeline. Vidi §15. |

### Kako dodati novu knjigu

1. Download HTML s Project Gutenberga u `books/`
2. Provjeriti HTML strukturu (`<p>`, `<h*>` tagovi, prvih 30 elemenata)
3. Dodati unos u `KNJIGE` listu u `bb_02_insert_knjiga.py`
4. Pokrenuti `bb_02_insert_knjiga.py`
5. Verificirati upis u bazi

### Kako dodati novi jezik

```sql
INSERT INTO bb_jezik (kod, naziv) VALUES ('xx', 'naziv') ON CONFLICT DO NOTHING;
```

### Kako dodati novi model i temperaturu (s142: tri nezavisne ose)

```sql
-- a1 (model, katalog): novo ime u bb_modeli
INSERT INTO bb_modeli (naziv, aktivan) VALUES ('model:tag', true) ON CONFLICT (naziv) DO NOTHING;

-- a2 (temperatura, katalog): nova vrijednost u bb_temperature
INSERT INTO bb_temperature (vrijednost) VALUES (0.5) ON CONFLICT (vrijednost) DO NOTHING;

-- registruj IZBOR za konkretnu fazu (npr. faza 1) preko bb_faze_a1 / bb_faze_a2
INSERT INTO bb_faze_a1 (faza_id, model_id, aktivan)
    SELECT 1, id, true FROM bb_modeli WHERE naziv='model:tag';
INSERT INTO bb_faze_a2 (faza_id, temperatura_id, aktivan)
    SELECT 1, id, true FROM bb_temperature WHERE ROUND(vrijednost::numeric,4)=ROUND(0.5::numeric,4);
```

> ⚠️ `bb_03_prevod.py` traži model+temp preko `EXISTS` na `bb_faze_a1`/`bb_faze_a2`/`bb_faze_a3` za zadatu fazu (s142). Ako kombinacija nije aktivna na sve tri ose za tu fazu — preskače uz poruku.
> ⚠️ Float precision (temperatura REAL): UVIJEK `ROUND(vrijednost::numeric,4)` pri poređenju — bez toga tiho vraća 0 redova bez greške (s110 lekcija, i dalje važi).
> ⚠️ `bb_aktivni_modeli.py` vraća samo ISTORIJSKI korišćene (model,temp) parove za fazu (čita iz `bb_prevodi_knjige`, ne pun unakrsni proizvod a1×a2) — novododata kombinacija se pojavljuje u orkestratoru tek nakon prvog stvarnog prevoda njome.

### Kako pokrenuti NOVU FAZU (s134)

**Model: 1 metod : M faza.** Faza je samo redni broj + identifikator izvršavanja; SADRŽAJ je u metodu (`bb_metode`). Nova faza = **dva INSERT-a, nula linija koda.**

```sql
-- 1) registruj fazu (metod_id 2 = self-refine)
INSERT INTO bb_faze (naziv, redoslijed, metod_id, opis)
VALUES ('refine-2', 3, 2, 'Drugi prolaz self-refine metoda.');

-- 2) registruj a1/a2/a3 izbore TE faze (s142: tri nezavisne ose, katalozi bez
--    faza_id — isti model/temp/prompt smije se ponoviti u novoj fazi bez sukoba)
INSERT INTO bb_faze_a1 (faza_id, model_id, aktivan)
    SELECT 3, id, true FROM bb_modeli WHERE naziv IN ('mistral-large-3:675b','glm-5.2');
INSERT INTO bb_faze_a2 (faza_id, temperatura_id, aktivan)
    SELECT 3, id, true FROM bb_temperature WHERE ROUND(vrijednost::numeric,4)=ROUND(0.8::numeric,4);
INSERT INTO bb_faze_a3 (faza_id, prompt_id, aktivan)
    SELECT 3, id, true FROM bb_promptovi WHERE naziv='refine';
```

```bash
# 3) pokreni
bash ./run_faza.sh --faza 3 --knjiga 22 --jezici "de hr it sr" --od 1 --do 40
```

**Pravila:**
- `--faza` je **OBAVEZAN i ne auto-inkrementira se.** Skripta ne izmišlja faze — *vidi se šta radiš*. Nepostojeća faza → guard je odbija (`exit 1`).
- **Faze se ne popunjavaju unazad.** Ako registruješ samo fazu 6, ona radi; faze 4/5 ne trebaju. Jedini preduslov je **postojanje pobjednika** (faza 1).
- **Seed = trenutni apsolutni pobjednik**, iz bilo koje prethodne faze. Zato faze **nisu komutativne** — put je dio rezultata.
- `redoslijed` je metapodatak koji **ti** upisuješ; ako preskačeš faze, on može lagati o stvarnom broju prolaza.
- `--force` ide **samo sudiji** (`bb_08`); `bb_03` nema force — `already_done()` je namjerna idempotentnost.

> ⚠️ **`nextval` NIJE transakcijski.** Ako INSERT u `bb_faze` padne pa se ponovi, sekvenca je odmakla i faza dobija pogrešan `id` (s134: dobila 5 umjesto 3). Poslije pale transakcije sa `serial` PK — **provjeri `id` prije nego se osloniš na njega**; po potrebi `setval('bb_faze_id_seq', N)`.

> ⚠️ **s144→ISPRAVLJENO s145:** raniji opis ovdje ("run_faza.sh TIHO NE RADI NIŠTA") bio je netačan — live test (s145) pokazao da `bb_aktivni_modeli.py` uvijek imao `exit(1)` zaštitu, pa `set -e` u `run_faza.sh` zaustavlja skriptu GLASNO (greška na stderr, bez "ZAVRŠENO"), ne tiho. Pravi uzrok: `bb_aktivni_modeli.py` čita AKTIVNE modele/temperature iz ISTORIJE (`bb_prevodi_knjige`), ne iz kataloga (`bb_faze_a1`/`bb_faze_a2`) — za potpuno novu fazu istorija je prazna. **Popravljeno u kodu (s145):** ako je istorija prazna, skripta sad pada na katalog (`bb_faze_a1` × `bb_faze_a2`) kao fallback — ispravno za sve self-refine faze (uvijek tačno 1 aktivna temperatura po fazi). Bootstrap direktnim `bb_03_prevod.py` pozivima **više nije potreban** za takve faze. Faza 1 (root) ostaje netaknuta — ima >1 temperaturu (nllb determinizam), uvijek ima punu istoriju, nikad ne stiže do fallback grane. Detalji: `docs/PLAN-KONFIGURACIJA.md` §4.8.

---

## 8. Knjige (bb korpus)

| ID | Knjiga | Autor | Gutenberg ID | Rečenica |
|----|--------|-------|-------------|----------|
| 1 | The Hound of the Baskervilles | Arthur Conan Doyle | 2852 | 3.852 |
| 5 | The Big Four | Agatha Christie | 70114 | 5.055 |
| 8 | Frankenstein; or, the Modern Prometheus | Mary Wollstonecraft Shelley | 84 | 3.384 |
| 12 | Moby Dick; Or, The Whale | Herman Melville | 2701 | 9.764 |
| 17 | Romeo and Juliet | William Shakespeare | 1513 | 3.172 |
| 18 | Alice's Adventures in Wonderland | Lewis Carroll | 11 | 1.535 |
| 19 | The Strange Case of Dr. Jekyll and Mr. Hyde | Robert Louis Stevenson | 43 | 1.157 |
| 20 | Dracula | Bram Stoker | 345 | 9.073 |
| 21 | Flatland: A Romance of Many Dimensions | Edwin Abbott Abbott | 201 | 1.341 |
| 22 | The Hound of the Baskervilles Copy | Arthur Conan Doyle | 2852c | 3.852 |
| 23 | The Big Four Copy | Agatha Christie | 70114c | 5.055 |
| 24 | Frankenstein; or, the Modern Prometheus Copy | Mary Wollstonecraft Shelley | 84c | 3.384 |

---

## 9. Stanje prevoda

> **s159 snapshot (3. avgust 2026):** Batch fix + otkriven timeout trade-off.
> `bb_03_prevod.py` popravljen: batch=20 za gated-base refine (bez seeda,
> faza 10), batch=5 ostaje za pravi refine (sa seedom) — ranije je gated-base
> pogrešno dobijao batch=5 jer je logika gledala samo `is_refine`, ne i
> `PROMPT_NAZIV`. Log naslov sad prati stvarno stanje ("sa seedom"/"bez
> seeda"). Mikro test k22 1000-1009 čist, commit `f68d367`. **Ideja 1 iz
> s157 (podjela glm gated faze po temperaturi) razrađena**: retrospektivna
> analiza na postojećim faza=10 podacima (float-precision bug usput
> otkriven i ispravljen, `ROUND(model_temperatura::numeric,1)`) pokazala da
> **0.1 rješava isto ili više nego 0.8 u sva četiri core jezika** s
> glm-5.2 — stari README §3 pattern (drugi modeli) se ne prenosi direktno.
> Preporučen redoslijed **0.1 prvo, pa 0.8** (obrnuto od Flaviovog prvog
> prijedloga), ~10% procijenjena dodatna ušteda — NEIMPLEMENTIRANO, čeka
> kraj tekućeg k12 prevoda. **Kritičan operativni nalaz**: batch=20 izaziva
> rastući broj Ollama Cloud read-timeout-a (120s) kasnije u dugim (6+h)
> neprekidnim sesijama (0-4 timeout/0 neuspjeha rano → 12-17 timeout/1-2
> trajna neuspjeha kasno, isti run, k12 opseg 9001-9800) — pobjednik i
> dalje pokriva sve rečenice (root fallback), samo nekoliko desetina
> "teških" rečenica ostane bez glm pokušaja. Flavio odlučio: stepenasti
> retry (30/60/120s umjesto fiksnog 30/30/30s) i vjerovatno povratak na
> max 400 rečenica/sesiju — NEIMPLEMENTIRANO. Usput: potvrđen
> `docs/KAKO-NovaFaza.md` kao ažuran i dovoljan za planirani "treći
> svijet"; preuzet i analiziran Gutenberg katalog
> (`data/external/pg_catalog.csv`, 79.071 stvarnih zapisa pravim CSV
> parsingom, 120 jezika, svih 9 izvora potvrđeno, nije u gitu); provjerena
> NLLB-200 podrška za grčki/albanski/mađarski/turski/esperanto (svi
> podržani) i latinski (nije podržan, ni starogrčki nema poseban kod).
> Korpus 50.624/1.905.033/360.832 (rastao kroz sesiju, Flaviov k12 rad
> paralelno). BB_VERSION ostaje s157 (web nedirnut). Sesija zatvorena
> SAMOSTALNO od Claudea (Flavio eksplicitno autorizovao). Detalji:
> `docs/sessions/session_159.md`.

> **s158 snapshot (2. avgust 2026):** Prio 1 iz s157 (race condition u
> `run_root_gated.sh`) RIJEŠEN — ali kroz dvije iteracije dizajna. Prvi
> pokušaj (ručni relativni toggle preko `bb_toggle_model.py --aktivan
> true/false` prije/poslije rada) mehanički je radio (testirano na k22
> 930-939) ali je Flavio ispravio pristup: "svijet" mora biti POTPUNA,
> eksplicitna deklaracija cijelog stanja (svi modeli a1 + sve temperature a2
> za fazu), ne relativni toggle jedne stvari — jer relativni toggle ne
> generalizuje na buduće svjetove (npr. mistral isključen, ili neka
> temperatura isključena). **Finalno rješenje:** novi generički alat
> `src/bb_deklarisi_svet.py` (`--faza --modeli --temperature`, postavlja
> aktivan=true SAMO za navedeno, aktivan=false za SVE ostalo u katalogu) +
> dvije neutralno imenovane, nezavisne skripte `bb_svet_1.sh` (puna 3-way
> root: mistral+nllb+glm) / `bb_svet_2.sh` (sužen root za gated obrazac,
> bez glm) — svaka potpuna izjava namjere, ne referencira drugu. Novi svijet
> ubuduće = nova tanka skripta, nula izmjena logike. `run_root_gated.sh`
> prerađen (auto-toggle uklonjen, sad samo pokreće root+gated fazu).
> **Test niz** (k22 Hound Copy core-4, budžet <1%): 930-939 (prvi pokušaj,
> ručni toggle), 940-949 (svijet 2 — Claudeov propust: pozvan samo root
> korak direktno preko `run_faza.sh`, gated faza 10 zaboravljena; Flavio
> primijetio bez detalja, Claude pronašao propust, ispravljeno pozivom
> punog `run_root_gated.sh` lanca), 950-959 (svijet 1, standardni tok, 5
> kandidata po rečenici uklj. glm u rootu). Oba svijeta funkcionalno
> potvrđena end-to-end. Usput: `balsam` MCP konektor prekid/oporavak
> (OAuth greška, riješeno Flaviovim restartom balsam servera, ne
> disconnect/reconnect); tri teoretska pitanja o pragu/kombinacijama/
> minimumu kandidata odgovorena; otkriven legacy red `claude-sonnet-4-6` u
> `bb_modeli` katalogu (istorijski, ~s-nešto rana sesija, testiranje
> raznih modela — nepovezano s ovom sesijom, pominjanje u README ostaje
> otvoreno). Korpus 50.624/1.873.845/352.936 (+468/+120 kroz test niz).
> BB_VERSION ostaje s157 (web nedirnut). Sesija zatvorena SAMOSTALNO od
> Claudea (Flavio eksplicitno autorizovao, "izuzetno bez moje kontrole i
> odobrenja"). Detalji: `docs/sessions/session_158.md`.

> **s157 snapshot (1. avgust 2026):** KONCEPTUALNA sesija — nula pipeline/kod/baza
> izmjena. Dvije nove ideje za dalje sužavanje glm troška dokumentovane ali
> NEIMPLEMENTIRANE (vidi §14): (1) podjela gated glm faze po temperaturi
> (0.1 prvo, 0.8 samo za ostatak); (2) radikalnija varijanta koja gatuje i
> mistral@0.8. **Glavni nalaz sesije — KRITIČAN, BLOKIRA odluku o usvajanju
> gated-root u produkciju:** `run_root_gated.sh` (s156) mehanizam (toggle
> `bb_faze_a1.aktivan` za fazu 1) je race-condition-ovan pod paralelnim radom
> po jeziku — Flaviov standardni obrazac. Globalno stanje na jednom DB redu,
> toggle-ovano unutar svakog automatizovanog poziva (`trap` na EXIT), nije
> izolovano po procesu/jeziku — paralelni pozivi tiho pokvare jedan drugom
> root konfiguraciju bez ijedne greške. Root uzrok: privremeno sužavanje ROOT
> faze krši ROOT invarijantu (s112: stabilan identitet faze u svakom
> trenutku) — refine faze nikad nisu imale ovaj problem jer se njihova
> konfiguracija upisuje JEDNOM (INSERT), nikad ne prepisuje usred izvršavanja.
> **Dogovoreno rješenje (prio 1 za s158):** promjena root konfiguracije
> postaje ručan, protokolom-vođen čin (prikaži→OK→izvrši), potpuno odvojen
> od automatizovanih skripti — deklariši svijet jednom, radi paralelno
> koliko hoćeš dok važi, vrati ručno na kraju. `run_root_gated.sh` u
> sadašnjem auto-toggle obliku se povlači iz upotrebe za paralelan rad dok
> se ne preradi. Korpus nepromijenjen (50.624/1.873.377/352.816). BB_VERSION
> nepromijenjen (web nedirnut). Detalji: `docs/sessions/session_157.md`.

> **s156 snapshot (31. jul 2026):** Bug fix iz s155 Dio 4 IZVRŠEN i DVOSTRUKO
> VERIFIKOVAN. `bb_03_prevod.py` grananje (`elif is_refine:` → `elif is_refine
> and PROMPT_NAZIV != 'base':`) — jedna linija, `git diff` pregledan,
> `py_compile` čist. Prije testa, prethodni s155 mislabeled test-podaci (k22
> 701-740, faza 10) obrisani — nakon komunikacijskog nesporazuma oko obima
> brisanja (razriješenog eksplicitnim Flaviovim pojašnjenjem: obrisati SVE
> faze za taj opseg, ne samo fazu 10), taj opseg je sada potpuno prazan kroz
> sve faze (480 redova obrisano ukupno, root+faza10 zajedno). Test ponovljen
> na dva svježa opsega: **k22 741-780** (gate 25/160=15,6%, glm pobjeđuje
> 21/25=84%) i **k22 781-820** (gate 27/160=16,9%, glm pobjeđuje 25/27=92,6%)
> — oba u skladu sa istorijskim rasponom (s145/s146/s154: 79-93% win-rate kad
> gate otvori). `prompt: base` potvrđen u oba loga — seed NIJE poslan modelu,
> bug stvarno ispravljen. **Nova infrastruktura:** `src/bb_toggle_model.py`
> (DB toggle helper) + `run_root_gated.sh` (wrapper, jedan poziv radi cijeli
> lanac: isključi model → root → gated faza → model se UVIJEK vraća aktivan
> preko `trap` na EXIT, i u slučaju greške) — drugi test (781-820) pokrenuo
> je Flavio SAM, jednim pozivom, potvrđujući da wrapper radi bez asistencije.
> Prvi tool-poziv za root fazu (741-780) je timeout-ovao na klijentskoj
> strani (proces nastavio raditi na serveru bez `nohup`, praćen `ps aux`
> provjerama do kraja) — ubuduće svaki dugi poziv ide sa
> `PYTHONUNBUFFERED=1 nohup time ... > logs/*.log 2>&1 &`, potvrđeno u
> drugom testu bez problema. **Dva nova KAKO dokumenta**
> (`docs/KAKO-BrisanjePrevoda.md`, `docs/KAKO-NovaFaza.md`) — na Flaviov
> eksplicitan zahtjev, napisani na kraju sesije sa svježim, konkretnim
> koracima iz ove sesije. Ollama Cloud "Weekly usage" screenshot (93,3%
> potrošeno): glm segment trake vizuelno najveći uprkos najmanje zahtjeva
> (4.780 naspram gemma 24.360, mistral 5.568) — vizuelna potvrda s155 nalaza
> o cijeni-po-pozivu, ne broju poziva. Odluka o usvajanju gated-root pristupa
> u produkciju ostaje za ponedjeljak (sedmični Ollama reset ~02:00, svjež
> pogled). Korpus 50.624/1.871.857/352.380. BB_VERSION ostaje nepromijenjen
> (web nedirnut ove sesije). Sesija zatvorena SAMOSTALNO od Claudea (Flavio
> eksplicitno autorizovao, odsutan od PC-a). Detalji:
> `docs/sessions/session_156.md`.

> **s155 snapshot (31. jul 2026):** Dva dijela. **(1) Analiza Ollama Cloud
> troškova** — Flavio dostavio čist podatak: k12 (Moby Dick) de/hr/it/sr,
> 3600 rečenica × 4 jezika, sedmična potrošnja 32,5%→92,9% (delta 60,4%).
> Istraženo (web search): Ollama Cloud naplaćuje po GPU-VREMENU, ne po
> tokenu/klasi; glm-5.2 i mistral-large-3:675b skoro identični po aktivnim
> parametrima (~40B oba, MoE) pa arhitektura ne objašnjava razliku; Ollamin
> vlastiti library page etiketira glm-5.2:cloud "High Usage" naspram
> mistral/gemma4 "Medium Usage"; DOKUMENTOVAN bag na Ollaminom backendu
> specifično za glm-5.2:cloud (GitHub #16779, #17091 — 10-75s naspram <2s za
> uporediv model) poklapa se sa projektovim vlastitim s132/s137 nalazima
> (glm 2,6-3,4× sporiji od mistrala). Flaviova odluka: ograničiti glm na
> gated drugi korak — ne optimizovati nepredvidljivu tuđu cijenu, minimizovati
> izloženost njoj. **(2) "Gated root" dizajn + implementacija — MEHANIČKI
> USPJEŠNA, KONCEPTUALNO NEISPRAVNA (bug otvoren, neispravljen).** Cilj:
> sužen root (mistral+nllb, bez glm-a) → sudija → pobjednik → gate (prag 0,95,
> postojeći mehanizam, automatski za fazu≥2) → nova self-refine faza (10,
> "root-gated-glm-base") sa glm + BASE promptom (bez pivota/reference — za
> razliku od faze 9 koja koristi refine prompt SA referencom). Test na k22
> (Hound Copy) 701-740, de/hr/it/sr: korak 1-3 (2-way root, 17m32s) i korak
> 5-7 (gated glm, 5m08s) oba prošla BEZ grešaka; gate ispravno filtrirao
> 40/160 (25,0%), poklapa se sa s146/s154 stopama. `run_faza.sh` ne podržava
> `--prag` (nije potrebno — `bb_03_prevod.py` default 0,95 automatski važi za
> fazu≥2). **BUG (Flaviov ulov, iz pažljivog čitanja loga):** uprkos `base`
> promptu, glm JE dobio seed/referencu u stvarnom pozivu modelu — grananje u
> `bb_03_prevod.py` (`elif is_refine:`, `is_refine = args.faza >= 2`) zavisi
> SAMO od broja faze, ne od zakačenog prompta; `prevedi_refine_batch()`
> hardkoduje "Reference {lang}: {seed}" u tekst poruke NEZAVISNO od prompt
> template-a iz baze. Claude je ranije pogrešno tvrdio da pivot zavisi
> isključivo od `{seed}` placeholdera u promptu — provjereno samo protiv
> single-mode fallback funkcije, ne protiv batch-mode funkcije koja se
> stvarno izvršila. Predložena ispravka (grananje i na `PROMPT_NAZIV`) NIJE
> primijenjena — Flavio zatvorio sesiju prije toga. 40 test-prevoda pod fazom
> 10 ostaju u bazi ali su MISLABELED (baza kaže base prompt, stvarni sadržaj
> poruke bio je refine-sa-referencom) — sudbina (obrisati/zadržati) otvorena
> pitanja za sljedeću sesiju. Korpus 50.624/1.871.353/352.220 (raslo Flaviovim
> k12 radom van fokusa sesije). BB_VERSION ostaje s154 (web nedirnut). Kod
> NIJE mijenjan. Sesija zatvorena SAMOSTALNO od Claudea (Flavio eksplicitno
> autorizovao, odsutan od PC-a). Detalji: `docs/sessions/session_155.md`.

> **s154 snapshot (29. jul 2026):** EKSPERIMENTALNA sesija — testirana "gated
> bazna konkurencija" (varijanta B), pokrenuta Flaviovim opažanjem da glm-5.2
> (cjenovni nivo 3/4 na Ollama) troši višestruko više resursa nego mistral+nllb
> zajedno. Retrospektivna analiza (Dracula/Moby Dick, faza 1) pokazala 12,5-22%
> rečenica bi imalo lošijeg pobjednika bez glm-a u bazi, delta blizu praga šuma
> (0,003, s146). Otkriven POSTOJEĆI `--prag` gate mehanizam u `bb_03_prevod.py`
> (ograničen na refine granu) — omogućio test bez ijedne linije koda. Nova
> faza 9 (glm-only, temp 0,8+0,1, prompt 'refine', prag 0,95). Prvi pokušaj
> (Hound k1) propao dva puta (NULL finalni_score - zaboravljena sudija; zatim
> gate se nikad nije otvorio - kontaminacija godinama refine istorije starog
> zamrznutog para). Ispravka: Hound Copy (k22), virgin opseg 501-700 (n=200
> rečenica × 4 jezika = 800). **Rezultat:** gate otvoren 225/800 (28,1%),
> stvarna pobjeda 173/800 (21,6%), prosj. delta pobjede ~0,05 (u skladu sa
> s146 +0,047). **KLJUČNA POTVRDA:** apsolutni pobjednik (KONCEPT.md argmax
> preko svih faza) potvrđen 0 neslaganja na 830 provjerenih parova - varijanta
> B je po dizajnu bezbjedna za kvalitet, neuspjeli glm pokušaji nikad ne
> dopiru do korpusa. Cijena (Ollama dashboard %) NERIJEŠENO mjerena - identičan
> skok (+1,2pp) za 30 i za 225 poziva, uzrok nepoznat. Sesija samokritički
> haotična (SQL greške, isti propust ponovljen dvaput) - Flaviov feedback
> prihvaćen bez ograde. Flaviov stvarni problem (glm sam ~90% budžeta, treba
> mu ~150% trenutnih resursa) ostaje NERIJEŠEN - test dokazuje bezbjednost
> mehanizma, ne rješava razmjeru. Odluka o usvajanju ODLOŽENA (nedostaje:
> pouzdana mjera uštede, ekstrapolacija na stvarni obim, test na drugom
> žanru). Korpus 50.624/1.802.993/338.460 (raslo Flaviovim paralelnim radom).
> BB_VERSION ostaje s153 (web nedirnut). Sesija zatvorena SAMOSTALNO od
> Claudea (Flavio eksplicitno autorizovao). Detalji: `docs/sessions/session_154.md`.

> **s153 snapshot (25. jul 2026):** ANALITIČKA sesija — analiza 16 novih log
> fajlova (k20 Dracula, opseg 6601–8200, de/hr/it/sr), nula pipeline poziva u
> sesiji (korpus 50.624/1.728.725/323.768, rastao Flaviovim pozadinskim
> runovima prije sesije). **Glavni nalaz:** obrazac izvršavanja promijenjen
> usred niza — prva serija (6601–7000) paralelna (agregat 11.85 rec/min, u
> skladu s ranijim rasponom), preostale tri serije (7001–8200) strogo
> sekvencijalne (jezici se izvršavaju jedan za drugim bez pauze) — cijena
> ~2.8–3.1× sporiji agregatni napredak korpusa naspram paralelnog režima za
> isti obim. Flavio potvrdio: namjerna promjena. Sudija bez jasnog dan/noć
> obrasca u ovom uzorku (18–32 min raspon, slabiji efekat nego 6.1× iz
> prethodnog runa). Kvalitet stabilan (avg_final 0.9593–0.9684) kroz oba
> režima. Dracula core-4 napredovao 6600→8200 (od 9.073 ukupno). Rezultat
> upisan u `docs/RUNOVI.md` (novi run-blok, 4 serije). BB_VERSION ostaje
> s152 (web nedirnut). Sesija zatvorena SAMOSTALNO od Claudea (Flavio
> unaprijed autorizovao, odsutan od PC-a). Detalji: `docs/sessions/session_153.md`.

> **s152 snapshot (24. jul 2026):** Prva "generalni predlog" sesija — izvršenje
> svih 5 nalaza iz `docs/PREGLED-teksta-s150.md`. Korpus 50.624/1.704.725/318.968
> (nula pipeline poziva, raslo Flaviovim pozadinskim runovima). **(1)** "Tačno 2
> faze" pretpostavka ispravljena na 6 mjesta: `about.html` dijagram, `index.html`
> proza, `reader.html` dvije X-Ray legende (EN-only), `nav.js` tri ključa × 5
> jezika (uklj. `about_p_refine4` koji je opisivao napušten pre-s144 dizajn).
> **(2)** Nova README `§4b` sekcija za NER/DocRE (tri sloja, orkestracija, tabele,
> pokrivenost, kriterij zatvaranja, web prikaz) — numeracija §5-15 netaknuta.
> **(3)** `limits.html` "236 coverage gaps" → opisna tvrdnja bez fluktuirajućeg
> broja. **(4)** `limits.html` "measurably different stylistic signature" →
> omekšano ("cause has not been isolated"), s137 nikad nije dokazao uzrok.
> `PREGLED-teksta-s150.md` označen zatvorenim. BB_VERSION s146 → **s152**.
> Detalji: `docs/sessions/session_152.md`.

> ⚠️ Koristiti `SELECT * FROM v_status_knjige;` ili `health_check.py` za tačno stanje — server je source of truth. Tabela ispod je ilustrativna (snapshot s87) i ne ažurira se mid-run.
>
> **s100 snapshot (28. jun 2026):** 38.333 rečenice · 888.390 prevoda · 174.270 pobjednika. Alice, Flatland, Jekyll&Hyde kompletni (prev=pobj) na svih 14 jezika; Big Four i core-4 (de/hr/it/sr) puni po knjigama. (Uključuje ~400 self-refine prevoda J&H hr — vidi s100.)
>
> **s101 snapshot (29. jun 2026):** 38.333 rečenice · ~954k prevoda · ~187k pobjednika · 9.633 rečenice s pobjednikom na svih 14 jezika. Brojevi živi iz baze (`stats.json`).
>
> **s102 snapshot (29. jun 2026):** 38.333 rečenice · 962.570 prevoda · 189.870 pobjednika. Self-refine učinjen vidljivim kao X-Ray eksponat u readeru (legenda objašnjava `-refine` varijante; svih 7 kandidata po rečenici gdje refine postoji — J&H hr s1–100). Refine ostaje pun takmičar: pobjednik se bira iz bazena od 7, ništa se ne filtrira ni prepisuje (odluka s102).
>
> **s103 snapshot (30. jun 2026):** 38.333 rečenice · 1.006.510 prevoda · 195.070 pobjednika. Flaviov full refine run — self-refine na SVIM knjigama, prvih 100 rečenica, svih 14 jezika, oba refine modela (gemma3-refine 12.060 / ministral-refine 12.080 prevoda). Refine pobjede: gemma3-refine 2.406 (20.0%), ministral-refine 1.420 (11.8%) — UPOZORENJE: win-rate je selekcijski artefakt (refine biran iz bazena od 7), NE dokaz nadmašivanja sopstvenog seeda (head-to-head ostaje korektna mjera, vidi docs/ANALIZA.md). 8 nepotpunih ćelija (seed-missing, Flavio koriguje).
>
> **s104 snapshot (30. jun 2026):** 38.333 rečenice · ~1.007.450 prevoda · 195.070 pobjednika (živo iz baze; raste). Refine rupe ZATVORENE — 252/252 ćelije pune (gemma3-refine 12.600 / ministral-refine 12.600). Refine pobjede: 2.487 + 1.465 = 3.952 (win-rate 15.7% — i dalje SELEKCIJSKI ARTEFAKT, vidi ANALIZA.md). **Uzrok rupa NIJE bio seed-missing nego seed-is-refine** (get_seed_map filtrirao \`NOT LIKE '%-refine'\` -> rečenice gdje je refine već pobijedio ispadale van; fix: anchoraj na trenutnog pobjednika ma koji bio). MiniLM legacy OBRISAN (120 redova, 22 ćelije) -> embedder sad jedinstven (e5-large). bb_03 retry fix (Ollama timeout). **NOVO: pobjednik po fazama** — \`bb_faze\` tabela + \`bb_modeli.faza_id\` (faza=svojstvo modela; base/refine). Redizajn pobjednika + rekonstrukcija faze-1 = sljedeća sesija.
>
> **s105 snapshot (1. jul 2026):** 38.333 rečenice · 1.049.545 prevoda · 204.793 pobjednika. Hound (id 1) potpuno preveden → četvrta potpuna knjiga (uz Alice, Flatland, J&H). **Rekonstrukcija faznog pobjednika ZAVRŠENA** (horizont #1 iz s104): nova tabela `bb_prev_recenica_faza` — faza 1 = 204.793 (svi pobjednici), faza 2 = 12.600 (refine opseg ≤100), ukupno 217.393. Faza-1 pobjednik na 3.952 refine-prepisanih mjesta eksplicitno vraćen (argmax nad baznima, determinističan tie-break). bb_prev_recenica netaknut. Sljedeće: bb_04 da sam puni faznu tabelu ubuduće.
>
> **s106 snapshot (1. jul 2026):** 38.333 rečenice · 1.049.545 prevoda · 204.793 pobjednika (nepromijenjeno od s105). **bb_04 sad SAM puni `bb_prev_recenica_faza`** (horizont #1 iz s105) — faza-blok bira faznog pobjednika po (rečenica, faza) preko `bb_modeli.faza_id`, DELETE+INSERT po opsegu, idempotentno; kraj ručne rekonstrukcije. Fazni pobjednik se od sada osvježava pri svakom pipeline runu. Hound (id 1) refine proširen na 1–200 (prvi izuzetak od "refine samo na prvih 100"). Read-path (web/xray export) provjeren — Reader X-Ray prikazuje sve kandidate, ali fazni pobjednik još NEMA web prikaz (sljedeća sesija). Web nedirnut → BB_VERSION s102.
>
> **s107 snapshot (2. jul 2026):** ~1,116M prevoda · ~216k pobjednika · ~234k faznih pobjednika (živo iz baze — procesi prevođenja trče). Fokus: **view sloj** — `v_prevodi_full` kao *majka svih analitičkih viewova* (svi kandidati + sve vrijednosti + kanonski `finalni_score`; izostavljen jedino `prevod_vektor`). Izvedeni: `v_corpus` (domen, 38.333 — namjerno iz baznih tabela jer 46,6% rečenica još nema nijedan prevod), `v_pobjednici_full` (apsolutni), `v_pobjednici_faza_full` (fazni + `takmicenje_faza_*`; invarijanta `takmicenje_faza_id = faza_id` prekršena 0×). Konvencija: sufiks `_full`, prefiks izvora u kolonama; stari viewovi netaknuti. Svi budući brojači izvode se iz majke. Web nedirnut → BB_VERSION s102.
>
>
> **s151 snapshot (24. jul 2026):** ANALITIČKA sesija — nula pipeline poziva
> (korpus nepromijenjen sesijskim djelovanjem, 50.624/1.696.725/317.368 na
> početku). Otvaranje otkrilo memorijski zaostatak (6 sesija, s143->stvarno
> s150) preko git log-a — Flavio ukazao da `conversation_search` (aktiviran
> za ovaj projekat) treba koristiti PRIJE pitanja čovjeka, ne poslije;
> uspješno pronašao s150. Rasprava o korijenu ponavljanih grešaka: Flavio
> odbio predlog za novi checklist korak ("suvišno") — popravka je
> bihevioralna (slijediti postojeći signal do kraja), ne strukturna.
> **RUNOVI.md** dobio analizu 24 nova loga (k20 Dracula, de/hr/it/sr, opseg
> 4801-6600, PO-JEZIKU paralelizam, različito od s119/s120 grupa-eksperimenata):
> Batch 5 vs 6 (isti dan, isti setup, 5h razmaka starta) pokazao 2.27x bržu
> veče-brzinu (zbir 5.43->12.31 rec/min), kvalitet identičan. Razlaganje:
> sudija (Ollama Cloud) 6.1x varijacije, prevodi 1.36x, NLLB (lokalno) 1.36x
> — isti faktor kao cloud. `sysstat`/`sar` provjera VPS-a (Frankfurt, Oracle
> Cloud, Flaviovo pitanje o dijeljenim resursima): %steal zanemarljiv
> (0.03-0.04%) — ISKLJUČUJE multi-tenant kontenciju; lokalni CPU skokovi
> poklapaju se sa START-om batch-eva ali ne traju kroz njihovo trajanje
> (samo-kontencija 4 jezika/4 jezgra, sekundaran faktor). Stara README §15
> pretpostavka (degradacija 16-18h) NIJE potvrđena — obrnuto, 19-22h CEST
> najbrži period. Detalji: `docs/RUNOVI.md` (2 nova bloka), `session_151.md`.
> Flavio najavio novi set logova za sljedeću sesiju.
>
> > **s149 snapshot (23. jul 2026):** ANALITIČKA/DIZAJNERSKA sesija — nula
> pipeline poziva, jedan probni fajl kreiran necommitovan
> (`src/predlog_root_DRAFT.py`). Korpus na početku 50.624/1.680.725/314.168
> (živ, Flaviovi pozadinski runovi). **Potvrđeno:** `bb_web_export.py`/
> `bb_xray_export.py` rade na starom s142 kodu, s148 pokušaj refaktora nije
> ostavio nijedan trag (grep + git log na oba fajla). **Fokus: Flaviova uloga
> u odabiru šta se prevodi** — formalizovana hijerarhija jezičnih grupa (G1
> de/hr/it/sr, G2 bg/bs/mk/sl, G3 es/fr/pt/ro, G4 af/nl): radi se unutar
> grupe dok ima ijedna nepotpuna knjiga, tek onda sljedeća grupa. Šira ideja
> o "agentima" (planer/worker/refine-worker/supervizor kao producer-consumer
> red poslova, uz pomen MQTT-a) razmotrena i namjerno SUŽENA — nova web
> stranica ODBIJENA kao nepotrebna, cilj sveden na jednu funkciju: iz
> `run_pipeline.sh --knjiga KK --jezici JJ --od OD --do DO` odrediti
> KK/JJ/OD/DO za sljedeći ROOT korak (1 knjiga, 1 jezik, opseg max 200;
> paralelizam/cijepanje ODLOŽENI). **Ključna Flaviova korekcija (2 pokušaja):**
> knjiga+jezik pokrivena do pozicije N ako je BILO KOJI model u root fazi
> (ne nužno aktivan/nov) preveo tu poziciju — po poziciji, ne po
> (model,temp) kombinaciji. Ovo je uklonilo petlju po aktivnim kombinacijama
> iz prve, pogrešne verzije frontier računanja. `predlog_root_DRAFT.py`:
> `generate_series` + `LEFT JOIN` nalazi prvu nedostajuću poziciju po
> (knjiga,jezik,faza=1) preko BILO KOJEG modela → frontier; OD=frontier+1,
> DO=min(frontier+200,total); petlja kroz grupe redom. Validirano naspram
> health checka (Hound/de 3852/3852 ispravno preskočen nakon korekcije;
> Moby Dick/de frontier=1800/9764 poklapa se tačno sa "Stanje prevoda"
> tabelom). **OTVOREN dizajnerski problem — "u toku" stanje:** baza zna samo
> "prevedeno"/"nije prevedeno", nema treće stanje za posao koji je pokrenut a
> nije završen → ponovljen poziv predloga dok je posao u toku daje IDENTIČAN
> predlog (demonstrirano uživo). Flaviova odluka: treba I tabela I nezavisan
> proces koji je ažurira — eksplicitno upozorenje protiv naivne simulacije DB
> transakcija samo tabelom+indikatorima; da li je taj proces čovjek ili
> "inteligentan" agent ostaje OTVORENO, dizajn odložen. Ollama Cloud usage/quota
> API i dalje ne postoji zvanično (provjereno pretragom, tri otvorena GitHub
> feature requesta 2026, nijedan implementiran) — ručni unos za sada. Kratak
> prekid `balsam`/`foxuno` konektora usred sesije (van kontrole oboje, riješeno
> Flaviovim ručnim reconnect-om) — infrastrukturna bilješka. Nije dodat nov
> memorijski zapis za "refaktoring poslije dokumentacije" — pravilo već
> postoji (METHOD.md §5, memorija s126). BB_VERSION ostaje s146 (web
> nedirnut). Sesija zatvorena SAMOSTALNO od Claudea (Flavio eksplicitno
> autorizovao, odsutan od PC-a). Detalji: `docs/sessions/session_149.md`.
>
>
> **s148 snapshot (22. jul 2026):** Status-provjera (Flaviov zahtjev) + tri
> zadatka, jedan vraćen nakon incidenta. Korpus 50.624/1.660.725/310.168
> (zadatak 1 = UPDATE postojećih redova, ne novi upisi). **(1)
> bb_sr_cirilica.py fix:** w/y/q/x dodani u LAT_CIR mapu; PRAVI uzrok bio
> `is_cirilica()` — `cir>=lat` lažno preskakala tekst s većinski ćirilicom +
> par zalutalih latiničnih slova, ispravljeno na strogi uslov (nema NIJEDNO
> latinično slovo). 3.959 prevoda ispravljeno (više od procijenjenih 1.466 —
> is_cirilica fix otkrio i druge zaboravljene ostatke, npr. skraćenice).
> **(2) Key Concepts kartice za limits.html:** Goodhart's law, Untranslatability,
> Construct validity — dodano u concepts.json + CONCEPT_PAGES u nav.js, slugovi
> provjereni HTTP 200 prije upisa, Flavio potvrdio u browseru. BB_VERSION bump
> NAMJERNO PRESKOČEN (Flaviova odluka — concepts.json ima automatski cache-bust,
> bump nije ritual za svaku izmjenu nego garancija svježine kad je stvarno
> potrebna). **(3) bb_web_export.py refaktor NA VIEW — POKUŠANO, VRAĆENO NA
> ORIGINAL:** 4 funkcije prebačene na v_pobjednici_full/v_pobjednici_faza_full,
> ekvivalentnost upita verifikovana EXCEPT testom na k22/23/24 PRIJE izmjene
> (metod ispravan) — ALI `get_phase_winners()` cross-view JOIN
> (`v_pobjednici_faza_full LEFT JOIN v_pobjednici_full`) tjera Postgres na pun
> sequential scan bb_prevodi_recenica (696.773 reda), otkriveno tek nakon što
> je proces zastao bez greške (dva paralelna zaboravljena procesa,
> pg_terminate_backend). Ukupno trajanje do pucanja na DRUGOM propustu
> (get_stats coverage/scores i dalje stari aliasi) 84.79s naspram Flaviovog
> baseline-a <30s. CIJELI refaktor vraćen (`git checkout`), original čist test
> 46.49s (sporije od starog baseline-a zbog prirodnog rasta korpusa, ali duplo
> brže od nedovršenog refaktora). Backlog stavka ostaje otvorena s
> upozorenjem: cross-view JOIN dva `_full` view-a je skup, budući pokušaj
> treba materijalizovan view ili indeks, ili ostati na direktnim JOIN-ovima za
> funkcije koje kombinuju apsolutne+fazne pobjednike. **Kritika procesa
> (Flavio, zapisano bez ublažavanja):** poređenje 46s/30s (prirodni rast)
> predstavljeno u istom dahu kad 84s+/46s (tada još neotkrivena greška)
> ostalo neizmjereno — opravdanje stiglo prije otkrića greške; protokol
> (prikaži→OK→izvrši) NIJE primjenjivan tokom debagovanja incidenta
> (kill/terminate/explain/revert/čišćenje izvršeni direktno) — isti obrazac
> kao s125/s135/s136 (memorija #24), POJAČAN pod stresom umjesto popravljen.
> TRAJNA POUKA: greška u toku je razlog za VIŠE provjere ne manje. Detalji:
> `docs/sessions/session_148.md`.
>
>
> **s147 snapshot (21. jul 2026):** Tri niti, sve ANALITIČKE/INFRASTRUKTURNE
> (nula pipeline poziva osim malog testa u niti 3). Korpus 50.624/1.647.363/
> 307.768 (živo, Flaviovi pozadinski runovi). **(1) Permutacijski eksperiment**
> (Flaviov ručni prevod + refine, k20 Dracula, 2801-3400, hr/de/it/sr, 6 blokova
> po 100 rečenica, svih 6 permutacija redoslijeda faza 4/5/6): pozicija u lancu
> ima jasan, monoton efekat na ocjenu (gate otvoren 21,0%→13,9%→11,3% kroz
> 1./2./3. korak, prosječan pomak +0,0237→+0,0077→+0,0080 kad otvoren) —
> samo-sužavajući lijevak radi kako je dizajniran. Konkretna faza (4 vs 5 vs 6,
> kontrolisano za poziciju zahvaljujući uravnoteženom dizajnu) pokazuje slab,
> nekonzistentan efekat. Efekat REDOSLIJEDA (bloka) ostaje nerazdvojiv od
> sadržaja rečenica u ovom dizajnu (between-block, ne within-sentence) — vodi
> direktno u nit 3. **(2) NER export provjera** (Flaviov zahtjev): web JSON
> sloj (`ner_*.json`) potvrđen 100% sinhronizovan s bazom (brojevi entiteta i
> DocRE relacija provjereni tačno po knjizi). Ono što NIJE sinhronizovano je
> sam NER pipeline: DocRE relacije postoje na samo 5/12 knjiga (Hound, Alice,
> J&H, Flatland, Hound Copy); Big Four/Frankenstein/Moby Dick/Romeo&Juliet/
> Dracula imaju classic+llm ali ne DocRE (otvoreno od s133 — "kad bude
> resursa"); **The Big Four Copy (23) i Frankenstein Copy (24) nemaju NIJEDAN
> NER sloj** — `run_ner.sh` nikad pokrenut na njima. Flavio pokreće samostalno.
> **(3) "Runda" IMPLEMENTIRANA kraj-do-kraja** (odgovor na nit 1: runda sama
> NE mjeri uticaj redoslijeda bez dodatnog seed-lock mehanizma — detaljno
> raspravljeno i dizajnirano, ali NEIMPLEMENTIRANO, posebna buduća odluka).
> `bb_prevodi_knjige.runda` (INTEGER, default 1) u UNIQUE ograničenju;
> `v_prevodi_full` dopunjen (additive); `bb_03_prevod.py --runda` + `run_faza.sh
> --runda` passthrough; `already_done()` automatski runda-svjestan preko
> `prevodi_knjige_id`. Backup prije DDL: `/tmp/bb_backup_pre_runda_20260721.
> dump`. Testirano na k22/hr/faza4/pozicija109: runda=1 bez regresije,
> runda=2 napravio nezavisan red, refine izvršen, bb_04 argmax ispravno
> odabrao bolji rezultat (glm-5.2 runda=2, final=0,9344) preko obje runde.
> Health check poslije: sve zeleno, web/xray export skripte nedodirnute
> (nema `SELECT *` ni zavisnost na `v_prevodi_full`). Web nedirnut → BB_VERSION
> ostaje s146. Detalji: `docs/sessions/session_147.md`, `docs/PLAN-KONFIGURACIJA.md` §4.9/§6.
>
> **s146 snapshot (20. jul 2026):** ANALITIČKA sesija + nova web stranica.
> Korpus NEPROMIJENJEN (50.624/1.617.141/302.168 — nula pipeline poziva, sve READ-ONLY).
> **(1) Gated refine potvrđen na širem uzorku** (k20 Dracula + k21 Flatland,
> de/hr/it/sr, 1–1000, faze 4/5/6): gate otvoren 2.337/8.000 (29,2%), gated refine
> pobjeđuje **93,4%** kad je otvoren, delta **+0,047**, klon-stopa 0,7%. Flaviova
> sumnja da stara faza 2 kvari rane rečenice — provjerena i uglavnom oborena
> (6+21 od 1.200); niži gate u ranim poglavljima je svojstvo teksta, ne kontaminacija.
> **(2) PRVI AUDIT MJERNOG APARATA** (glavna nit, sve trajno u `docs/ANALIZA.md`):
> **prag šuma sudije = 0,003** mjeren na 212.443 klon-grupe (98,74% identična ocjena)
> → ⚠️ obara s137 nalaz o nedeterminizmu sudije (n=30 bio premali), i znači da je
> rasipanje unutar grupe kandidata STVARNA razlika. **sd sudija 0,2065 vs sd cosinus
> 0,0277** → formula 0,4/0,6 u praksi rangira **~8% cosinusom, ~92% sudijom**.
> **Cosinusove strukturne slijepe tačke:** neprevedeni fragment 0,99 (2.784 sl.),
> latinično `w/y` u ćirilici 0,95 (1.466 sr prevoda), slomljena gramatika 0,97 —
> sve tri sudija hvata pouzdano. Sudijine nule NISU sentinel (provjereno u kodu).
> ⚠️ **ODLUKA: NE standardizovati komponente** (z-score bi promijenio 24,98%
> pobjednika u smjeru slijepih tačaka) — nesklad 8/92 trenutno ŠTITI izbor.
> **(3) Jedini pravi negativan nalaz:** sudija mjeri tečnost, književnost je namjerno
> krši — Abbott *Flatland* de, autorova namjerna složenica izbrisana refine-om i
> nagrađena **+0,157 (najveća delta u uzorku)**. "Ne mjerimo vjernost autoru nego
> vjernost normi jezika." **(4) NOVA STRANICA `limits.html`** ("What We Don't Measure",
> menu **Limits** iza Stats) — publikovani svi negativni nalazi i granice: slijepe
> tačke, sistematsko kažnjavanje autorskog odstupanja, sve iznad rečenice (prelom
> stiha, ilustracije — jedinica je rečenica), kontekst, poznata nepotpunost.
> EN-only tijelo (svjestan izuzetak), meni+naslov ×5 jezika. **BB_VERSION s140 → s146**
> (buchenweb 921efe6 — prvi put dirnut od s140). OTVORENO: `bb_sr_cirilica.py` w/y fix,
> Key Concepts za novu stranicu, permutacijski eksperiment faza 4/5/6.
> Detalji: `docs/sessions/session_146.md`, `docs/ANALIZA.md`.
>
> **s145 snapshot (19. jul 2026):** Analiza + dvije popravke, NULA uticaja na
> korpus (Flavio je samostalno pustio faze 4/5/6 na Hound (k1) 200 rečenica ×
> de/hr/it/sr prije sesije). **Analiza:** od 800 rečenica-jezik parova, gate se
> otvorio na 62 (7.75%); novi gated refine pobijedio **79%** (49/62) kad je gate
> otvoren — snažna potvrda gating dizajna (naspram ranijeg ne-gated head-to-head
> 25%, s134). Poslije 4/5/6, gate bi se ponovo otvorio na 22/800 (2.75%) — tvrd
> rep, uglavnom skorovi 0.92–0.95. **Ispravka 1 — bootstrap problem (s144)
> pogrešno OPISAN, sad ispravno objašnjen i STVARNO POPRAVLJEN:** live test
> (`bash -c 'set -e; x=$(exit 1); echo NEDOSTIŽNO'`) pokazao da `run_faza.sh`
> NE pada tiho — `bb_aktivni_modeli.py` je oduvijek imao `exit(1)` zaštitu, pod
> `set -e` to zaustavlja skriptu GLASNO. Pravi uzrok: skripta čita AKTIVNE
> modele/temperature iz ISTORIJE (`bb_prevodi_knjige`), ne iz kataloga
> (`bb_faze_a1`/`bb_faze_a2`) — jer za fazu 1 (root) katalog nije jednoznačan
> (nllb determinizam, samo 5 od 9 mogućih model×temp kombinacija stvarno
> korišteno). Popravka: fallback na katalog kad je istorija prazna — ispravno
> za sve self-refine faze (uvijek 1 aktivna temperatura). Bootstrap ručnim
> pozivima više nije potreban za takve faze. Testirano (py_compile, faza 4
> nepromijenjena, fallback grana kroz rollback-transakciju) — kod izmijenjen,
> NEKOMITOVAN. **Ispravka 2 — "runda" dizajn razrađen i testiran, NIJE
> implementiran:** Flaviova ideja — alternativa klon-triku (faza 7/8/9) za
> ponovno pokretanje iste konfiguracije: nov atribut `runda` na
> `bb_prevodi_knjige`, uključen u UNIQUE umjesto novog `faza_id` po pokušaju.
> Testirano pravom DDL migracijom (ADD COLUMN + UNIQUE zamjena) u
> rollback-transakciji na produkcionoj tabeli — duplikat na runda=1 pao kao i
> prije, isti tuple na runda=2 prošao čisto, `v_prevodi_full` nastavio raditi,
> `ROLLBACK` potvrđen (0 zaostalih redova). Dokumentovano kao spremna opcija
> (PLAN-KONFIGURACIJA.md §4.9), implementacija odložena po Flaviovoj odluci.
> Korpus nepromijenjen (50.624/1.608.553/302.168). BB_VERSION ostaje s138.
> Sesija zatvorena SAMOSTALNO (Flavio unaprijed autorizovao, odsutan od PC-a).
> Detalji: `docs/sessions/session_145.md`, `docs/PLAN-KONFIGURACIJA.md` §4.8-4.9.
>
> **s144 snapshot (19. jul 2026):** **DIO B PREOKRENUT** — random selekcija
> (plan §4.1-§4.6) NAPUŠTENA, zamijenjena s tri fiksne gated faze
> (`refine-gated`=4, `refine-lenient-gated`=5, `refine-strict-gated`=6),
> prag `seed_score<0.95`. Flaviova provokacija o sopstvenom istorijskom
> iskustvu ("6 minuta po rečenici") razotkrila da GA mašinerija (mutacija,
> anti-elitizam, marginalna preferenca) ima smisla samo za OGROMAN prostor
> pretrage — sa fiksnim katalogom od 6 kombinacija (2 modela × 3 prompta ×
> 1 temperatura), taj problem ne postoji. Pravi problem reformulisan: ne
> "koju kombinaciju", nego "vrijedi li uopšte probati OVU rečenicu" — headroom
> gate. Prag 0.95 usvojen na čistom novi-model-vs-novi-model presjeku (mješani
> agregat davao 0.92, konfaund starih penzionisanih modela). Svaka gated faza
> gleda TRENUTNOG apsolutnog pobjednika (ne originalni seed) — samo-sužavajući
> lijevak. Otkriven i popravljen PRAVI bug u `bb_04_pobjednik.py` (čitao
> obrisane `m.faza_id`/`m.temperatura` kolone iz s142 migracije — nikad
> testirano jer nijedan refine nije pokretan između s142 i ovog testa).
> Testirano kraj-do-kraja (`bb_03`→sudija→`bb_04`) na k22. Korpus
> 50.624/1.608.277(+6 test)/302.168. BB_VERSION ostaje s138. Detalji:
> `docs/sessions/session_144.md`, `docs/PLAN-KONFIGURACIJA.md` §4.7.
>
> **s143 snapshot (18. jul 2026):** RAZRADA DIJELA B (mjerenje + konkretizacija
> dizajna), nastavak istog dana nakon s142. Korpus NEPROMIJENJEN (50.624/1.608.271/
> 302.168) — samo `bb_promptovi` 2→4 reda, dokumentacija. BB_VERSION ostaje s138.
> **Mjerenje (nove kanonske upite trajno u docs/ANALIZA.md):** faze `root=false`
> (metod_id→bb_metode, NE `faza_id>1` — otporno na buduće faze bilo kog porijekla)
> čine 2.44% obima svih prevoda (39.286/1.608.271) ali samo 1.73% apsolutnih
> pobjednika (5.217/302.168) na CIJELOM korpusu — konzistentno gubi agregatno,
> slaže se s malim uzorcima s134-138. **Tri nivoa granularnosti razjašnjena:**
> Knjiga 50% (knjiga+jezik+root=false) / Jezik 25% (jezik+root=false, sve knjige) /
> Biblioteka 25% (samo root=false, sve knjige i jezici) — dimenzije se puštaju
> POSTEPENO šire, ne dodaju svugdje; ponder FIKSAN za sada (revizija nakon analize
> par hiljada refine prevoda). Demonstrisano na Alice/hr: temperatura DEGENERISANA
> (100% na sva tri nivoa — refine je ikad aktivirao samo 0.8), model (a1) pokazao
> STVARNU razliku (Knjiga nivo = samo stari retired par, Jezik/Biblioteka = i novi
> par) → otkrilo da anti-elitizam/strop ima smisla SAMO kad osa ima ≥2 PODOBNE
> vrijednosti u kontekstu; inače je 100% deterministički izbor, ne kršenje pravila.
> **NLLB isključen iz a1 za refine faze** preko postojećeg
> `bb_model_registar.vrsta<>'namenski MT model'` filtera (registry iz s123, samo
> povezan za novu svrhu) — BEZ nove tabele/kolone (Flavio: "mijenjamo strukturu
> baze najmanje moguće"). Sudija potvrđen potpuno van a1/a2/a3 rotacije (fiksna
> konstanta). **bb_promptovi popunjen sa sve tri refine varijante:** `refine`
> (postojeći), `refine-lenient` (pre-s135 tekst, single citiran tačno iz
> bb_03_prevod.py.bak_s114, batch konstruisan po analogiji jer je batch-refine
> uveden tek u s137), `refine-strict` (nov tekst, Flavio odobrio). Nijedna od tri
> refine varijante još nije vezana za fazu preko bb_faze_a3 — mehanizam selekcije
> Dijela B nije građen, samo katalog + dizajn. Sesija zatvorena SAMOSTALNO od
> Claudea (Flavio unaprijed autorizovao, odsutan od PC-a). Detalji:
> `docs/sessions/session_143.md`, `docs/PLAN-KONFIGURACIJA.md` (§4 dopunjen).
>
> **s142 snapshot (18. jul 2026):** DIO A PLANA (konfiguracija kao faza) IZVRŠEN
> kraj-do-kraja. Korpus 50.624/1.608.271(+11 test)/302.168. Shema: `bb_modeli`
> čist katalog (25→9 redova); nove `bb_temperature`, `bb_promptovi`; nove
> `bb_faze_a1/a2/a3` (tri nezavisne ose, faza bira svaku nezavisno — nema
> sprege/parova u shemi); `bb_prevodi_knjige` dobio eksplicitne
> `faza_id/model_id/temperatura_id/prompt_id` + pun UNIQUE (7 kolona). Backup
> `/tmp/bb_backup_pre_konfiguracija_20260718.dump` prije DDL. **View sloj**:
> `v_prevodi`, `v_pobjednici`, `v_prevodi_po_modelu`, `v_prevodi_full`
> prepisani (`CREATE OR REPLACE`, isti izlaz) — 6 izvedenih pogleda
> (`v_pobjednici_full`, `v_status_faza*`, itd.) nastavilo raditi bez izmjene
> (Postgres prati zavisnost po koloni, ne imenu). **Kod**: `bb_aktivni_modeli.py`
> vraća istorijske (model,temp) parove (Flaviova odluka — ne pun unakrsni
> proizvod a1×a2); `bb_03_prevod.py` čita a1/a2/a3 iz baze i radi `.format()`
> na prompt šablonima umjesto hardkoda; `bb_web_export.py`/`bb_xray_export.py`
> otkriveni polomljeni (čitali stare `m.temperatura`/`.faza_id`) i popravljeni
> (testirano u `/tmp`, NIJE pokrenuto na živi export). E2E test na k22
> (baza+refine, stvarni Ollama pozivi) potvrdio identitet kroz cijeli lanac.
> NER export (classic/LLM/DocRE) potvrđeno nepogođen. `health_check.py` 2b
> radi na novoj šemi. BB_VERSION ostaje s138 (buchenweb netaknut; export kod
> popravljen ali živi JSON nije regenerisan). Detalji: `docs/sessions/session_142.md`.
>
> **s141 snapshot (17. jul 2026):** PLANSKA sesija — nula izmjena koda/baze
> (korpus 50.624/1.608.260/302.168, READ-ONLY), samo snimljen plan-dokument
> `docs/PLAN-KONFIGURACIJA.md`. Spojena dva s140 prioriteta (prompt-kao-atribut +
> random selekcija) u jedan zahvat sa zavisnošću A→B (random bira prompt kao atribut
> → prompt-kao-atribut je temelj). **KONCEPTUALNI POMAK (kroz tri iteracije plana):
> zahvat narastao od "dodaj prompt na bb_faze" u REDEFINICIJU FAZE.** s140 odluka
> (prompt = TEXT kolona na bb_faze) NADOGRAĐENA: random zahtijeva katalošku tabelu
> promptova (bira iz nje), pa prompt postaje TABELA + veza, ne kolona. **Faza =
> konfiguracija = kombinacija izbora iz TRI NEZAVISNE OSE** (a1=model, a2=temperatura,
> a3=prompt). Model prestaje biti "model+temperatura" (slijepljivanje a1+a2 u jedan
> bb_modeli red = ad-hoc odluka s početka, ISPRAVLJA se). **Ciljna shema:** tri
> kataloga (`bb_modeli` čist naziv, `bb_temperature` nova, `bb_promptovi` nova — svaki
> prompt = svi tekstovi prevod+back batch+single) + tri odvojene simetrične veze
> (`bb_faze_a1/a2/a3`, faza_id+izbor+aktivan, NIJEDNA spojena — faza bira svaku osu
> NEZAVISNO). **Migracija:** raspakuj 25 bb_modeli redova u tri ose, prebaci 1.268
> bb_prevodi_knjige FK na eksplicitne veze; `bb_prevodi_recenica` (1.6M) netaknut (ispod
> knjiga-nivoa). Pun redoslijed 0–8 u planu; Korak 5 (migracija traga) najveći/najrizičniji.
> Base=UPDATE (SCD Tip 1, root ostaje); refine=traži-ili-kreiraj po skupu (nikad namjerni
> duplikat; isti skup na više faza → min id). **LEKCIJA (Claude, 3×):** semantika imena
> ("temperatura","faza","broj faze") natovaruje lažne pretpostavke na strukturu (sprega
> model↔temp, "parovi", redoslijed faza) — a1/a2/a3 okvir ih skida. Plan sa "otvorenim
> pitanjima" koja su MOJA zbunjenost (ne rupa u konceptu) nije plan: prvo raščistiti
> razumijevanje, PA plan. Zatečeni podaci ≠ koncept. BB_VERSION ostaje s138 (web netaknut).
> Detalji: `docs/sessions/session_141.md`.
>
> **s140 snapshot (17. jul 2026):** KONCEPTUALNA sesija — nula izmjena koda/baze
> (korpus 50.624/1.595.460/302.168, READ-ONLY osim web dodatka). Nastavak s139 horizonta.
> **Tri okvirne odluke (Flavio):** (1) "web glačanje" NIJE trajni horizont ("nikad neće
> biti gotovo, ne ponavljati") — web izmjene ad-hoc uz konkretan povod; (2) ti/vi +
> NER/sažetak kontekst-injection nit ZATVORENA ("ne radimo"); (3) fokus na dva s139
> koncepta. **(A) PROMPT KAO ATRIBUT FAZE:** EAV (atribut,vrijednost po redu) razmotren
> i ODBAČEN — Flaviov argument: shemu moraš i ČITATI, ako za to treba priručnik izgubili
> smo; gubi tipsku sigurnost (temp NUMERIC, s110) i UNIQUE(naziv,temp,faza_id) garanciju.
> Prompt ide na `bb_faze` kao TEXT kolona (Claudeov s139 stav "bb_metode" ISPRAVLJEN):
> "tanka faza" nikad nije značila "zabranjeno dodavati atribute" nego ergonomski čitljiv
> redni broj; **faza = SVI atributi koji je opisuju**, prompt je jedan od njih (finiji od
> metoda; metod ostaje krupna kategorija base/self-refine). Mehanika = **slowly changing
> dimension Tip 1** (UPDATE prepiše tekući prompt; istorija živi u prevodima, ne u fazi).
> `\d bb_faze` potvrdio: `bb_faze_root_jednom` (partial UNIQUE metod_id=1) OSTAJE — root
> je JEDAN red, mijenja se sadržaj ne broj redova; nov refine prompt = nova refine faza
> (metod_id=2, novi redoslijed). PRAZNINA (Flavio prihvatio): prompt trag za stare prevode
> ne postoji → ručni upis u istoriju. Posao kad se gradi: ADD COLUMN + UPDATE + bb_03 čita
> iz baze + header loga + sve što se radi s modelom/temp radi se i s promptom.
> **(B) RANDOM SELEKCIJA S MARGINALNIM PREFERENCAMA:** faza 1 = temelj bez filozofije
> (deterministična, seed za sve iznad); random tek od refine faza. Mehanika = traži-ili-
> kreiraj fazu po skupu atributa (postoji→nastavi, ne→INSERT). **KLJUČNO: preferenca je
> MARGINALNA PO ATRIBUTU, ne po kombinaciji** (MB favorit-model, TA favorit-temp, PB
> favorit-prompt, kombinuju se NEZAVISNO → MB+TA+PB možda nikad nije postojao) — održava
> raznolikost po konstrukciji, ne konvergira u jedan vrh; anti-elitizam "niko 100% ni 0%".
> Mutacija = odvojen korak POSLIJE izbora (jeftina, zatvoren skup). Strop protiv preuzimanja
> (~50% rečenica/knjiga max jedne kombinacije) = anti-konvergencija kao tvrdo pravilo.
> **Granularnost uspjeha:** tri nivoa Biblioteka/Jezik/Knjiga ponderisano (kao finalni_score
> filozofija), **Knjiga najviše/Biblioteka najmanje**; ponder raste s količinom podataka
> (rani prevod → biblioteka vodi; zreo → knjiga). Klasa/žanr NE preko LLM (nova crna kutija)
> — knjiga-kao-svoja-klasa zaobilazi definisanje. Prag ulaska = **proporcionalan ~10%**
> (ne apsolutnih 400 — ne skalira); ispod praga uniformni random, iznad vođeni.
> **FLAVIOVA OGRAĐA:** "ne simuliramo evoluciju" — jumping-genes (McClintock) je ANALOGIJA
> ne specifikacija; X-Ray je promatranje pojave kad se desi, ne teorijsko predviđanje kvara.
> "Sve što se događa je naš cilj, sve radimo zbog nas, i dobro i loše." **Web:** McClintock
> u about.html + Key Concepts kartica (`Barbara_McClintock`). BB_VERSION s138→s140. Detalji:
> `docs/sessions/session_140.md`.
>
> **s139 snapshot (16. jul 2026):** KONCEPTUALNA sesija — nula izmjena koda/baze
> (korpus 50.624/1.595.460/302.168, sve READ-ONLY). Dva bloka. **(1) Potvrda mehanike
> self-refine** (Flavio provjerava razumijevanje, svaka tvrdnja verifikovana čitanjem
> koda/baze): svaki refine korak traži samo da faza 1 ima pobjednika; bilo koja faza
> se pokreće ako pobjednik postoji (pobjednik je pobjednik, nezavisno od redoslijeda —
> argmax je argmax; redoslijed mijenja samo SADRŽAJ SIDRA za budući poziv, ne
> ispravnost selekcije); idempotentnost po (model,temp,faza) preko
> UNIQUE(naziv,temp,faza_id) — ista trojka u fazi 2/3 su različiti redovi; faza mora
> biti registrovana u bb_faze (guard exit 1) pa se faza 999 ne može pokrenuti a 2/3
> mogu; **faze 2 i 3 su tehnički identične** (isti metod_id=2, isti modeli — faza 3
> uvedena samo zbog UNIQUE ograničenja da isti model+temp prevede drugi put).
> **(2) NALAZ — prompt je neregistrovan parametar:** prompt utiče na prevod jednako kao
> model/temp, ali živi samo kao string-literal u bb_03; nije u (model,temp,faza) trojci
> → promjena prompta (npr. s135 klon-fix) je NEVIDLJIVA jer already_done() preskače
> rečenicu → ne možemo ni uporediti ni koegzistirati stari-vs-novi-prompt prevod.
> Idempotentnost aktivno sakriva efekat promjene prompta. Tri mjesta za prompt
> (analiza, bez odluke): A=bb_faze, B=bb_metode (Claudeov stav — najčišće, "self-refine
> s promptom A/B" = dva metoda, po s134 disciplini sadržaj-u-metod), C=bb_modeli.
> **(3) IDEJA (horizont, ne plan) — random selekcija s evoluirajućim preferencama:**
> random izbor (2 modela × temp × prompt × redovi) → "šarolik" prevod; iz šarolikosti
> čitati preference za sljedeći "dirigovani random". Anti-elitizam: bolji element dobija
> ŠIRI ali NENULTI interval slučajnih brojeva (0.8 pobjeđuje 70% → interval 70%, 0.1 →
> 30%; slabiji nikad ne ispada). Jumping-genes analogija (McClintock, web-provjereno):
> čitala šaru zrna kukuruza kao podatak o mehanizmu — tačno "iz šarolikog prevoda čitaj
> preference". **Claudeova analiza:** ovo je kanonski **fitness-proportionate
> (roulette-wheel) selection** (Holland); Flaviov instinkt pogodio alat I motiv. Dvije
> poznate zamke pogađaju baš ovaj slučaj: prerana konvergencija (povratna sprega
> zaključa favorita prije poštenog uzorkovanja) i nekonzistentan pritisak (preslab blizu
> plafona = projektov s134 pejsmejker). Popravka: **rank selection** (interval ∝ rang,
> ne sirovi score) radi i na 0.95+ korpusu. **Trajna ograda:** interval dolazi od pobjeda
> PO NAŠEM SUDIJI → preferenca je X-Ray vlastitog ocjenjivanja, ne istina o jeziku
> (McClintock imala nezavisnu istinu, mi imamo sudiju koji je i igrač i mjerni
> instrument). Sve ostaje horizont; s138 Odluka 2 (web glačanje) i dalje važi. Detalji:
> `docs/sessions/session_139.md`.
>
> **s138 snapshot (15. jul 2026):** Dvije web izmjene + konceptualno istraživanje ZATVORENO negativnim nalazom. **Web:** (1) reader.html X-Ray Full mod sad prikazuje FAZU po svakom kandidatu (ne samo pobjedniku) — `bb_xray_export.py` je fazu izvozio od s114, samo se nije prikazivala; jedan red u `renderXrayPage()`, postojeci `reader_phase_n` i18n kljuc, bez backend izmjene (buchenweb 5feb09e). (2) nlp.html metod-kartice (Classic/With LLM/DocRE) postale KLIKABILNI birac — stari sitni tasteri (`.nlp-method-btn`) skriveni `display:none`, kartice `.nlp-mcard` proksiraju klik na skriveni taster (nula duplikacije logike), veci font/hover/jaci active indikator (buchenweb 4270b02). BB_VERSION s136->s138.2. **Istrazivanje (NER<->prevod, sazetak<->prevod — kontekst-injection za kvalitet prevoda):** invarijanta cijelo vrijeme — sudija slijep/fiksan, kontekst SAMO prevodiocu (s124). Svi testovi standalone, van produkcije, NULA upisa u bazu. Nalaz: (a) NER (DocRE relacije) daje STRUKTURU odnosa ali zadatak (ti/vi registar) trazi EPOHU/registar — pogresna osa informacije, nije los alat nego pogresan (Flaviova odluka: odustajemo od NER-prevod veze). (b) Sazetak (deepseek-v4-pro "prevodilacki brief") je izvanredan artefakt (hvata epohu/registar/oslovljavanje) ALI ne mijenja prevod pouzdano; Gutenbergov sadrzajni sazetak ~ gol prompt (ne sluzi svrsi). (c) **GLAVNI NALAZ: signal ispod suma** — ista recenica (Holmes->Watson "Don't move, I beg you") PREOKRENULA ti/vi izbor izmedju dva prolaza istog prompta na temp 0.8; varijacija poziva > razlika promptova, pa je svaki "efekat" iz jednog poziva bio slucajnost. (d) Flaviov uvid rusi premisu: "prijatelji->ti" NIJE univerzalno ispravno (Holmes/Watson na njemackom = "Sie"; viktorijanski registar formalan uprkos prijateljstvu) — cilj sam po sebi nejasan. **ODLUKA 1: kontekst-injection za kvalitet prevoda ZATVOREN** (i NER i sazetak). **ODLUKA 2: sljedecih nekoliko sesija = web stabilizacija i estetsko glacanje.** Korpus netaknut (50.624/1.582.660/302.168). Detalji: `docs/sessions/session_138.md`.

> **s137 snapshot (15. jul 2026):** Analiza Flaviovih noćnih prevoda (Hound 1-1300, Big Four/Frankenstein/Moby Dick/R&J 1-200, de/hr/it/sr): novi par pobjeđuje agregatno (55-65%), ali stari retired par neočekivano jak na Moby Dick i Romeo&Juliet (37-65% pobjeda, arhaičniji stil) — original Frankenstein potvrđuje "near-equal glm/mistral" obrazac poznat s k24 Copy. **ti/vi baseline korak 1 (inventar) izveden** (8093 dijaloških rečenica HR korpusa, 1076 ti/1171 vi/23 oba/5869 nijedan, uzorak 2224 za buduće korake) **pa svjesno napušten** — Flaviov zahtjev da rješenje ne smije biti jezično/knjižno specifično isključuje regex pristup; pravac se pomjera ka NER-kao-kontekst (jezično neutralan, relacija iz originala). **Batch-refine implementiran** (`REFINE_BATCH_SIZE=5`, nova `prevedi_refine_batch()`, batch+fallback isti obrazac kao bazni prevod) — prvi put od s100 plana ("faza 2: pristupačna verzija"). Testiran mehanički besprijekorno (poravnanje, idempotentnost, retry-oporavak) na knjizi 22 (test knjiga); produkcioni run (400 refine pokušaja, de/hr/it/sr) pokazao head-to-head 16.75% (niže od s134 single-mode 25%, uzorci nisu kontrolisano uporedivi), klon-stopa 7.5% (poboljšanje od 16.25% prije s135 fix-a). Nov nalaz: glm-5.2 3.4× sporiji od mistral-a sekvencijalno (bez kontencije), različit fenomen od paralelizam-osjetljivosti (s132). Otkriven suptilan efekat: sudija (gemma4:31b) daje različitu ocjenu na identičnom kloniranom tekstu u zasebnim pozivima (nedeterminizam na temp=0.0) — 17/30 klonova u ovom testu imalo je različit score uprkos identičnom tekstu. **NER-kao-kontekst tehnički test** (standalone, van produkcionog koda): mehanizam radi (kontekst jednom po batch-u, ispravno poravnanje), ali čisto-NER pristup (bez seeda) dao formalno "vi" umjesto očekivanog neformalnog "ti" uprkos kontekstu "close friends" — otvoreno pitanje je li seed ipak potreban uz NER. Kod (`bb_03_prevod.py`) necommitovan do kraja sesije. BB_VERSION ostaje s136 (web netaknut). Detalji: `docs/sessions/session_137.md`.

> **s136 snapshot (14. jul 2026):** **KONTROLA KOMPLETNOSTI — nivo 1a + 1b.** Analiza jučerašnjih f2 runova (k22/k23/k24, 1–100): k22/k23 čisti; k24 glm-5.2 pukao na it 81–100 (ReadTimeout, nehvatana iznimka, sr nikad počeo) → rupa it 80/100, sr 20/100 — mistral restartovan čisto. **Novi view `v_status_faza_model`** (long, knjiga×jezik×faza×model×temp, derivat majke; rupa = COUNT < MAX u grupi; bez praga — rupa=1 i rupa=999M isti nalaz). **1a:** `bb_03_prevod.py` provjera opsega na kraju svakog jezika (COUNT nad zadatim --od/--do intervalom tog runa vs do-od+1 → ✅/❌ u log). **1b:** `health_check.py` nova sekcija 2b `check_kompletnost()` (view + MAX logika, kolone s knjiga_id i faza_id). Nalaz: 87 rupa, SVE faza 1, SVE retired modeli — **Flaviova odluka: ostaju na miru dok imamo pobjednike (prio 2)**. Popravka k24: `run_faza.sh` f2 1–110 ×4 jezika — 8/8 provjera 110/110 OK, view potvrdio. **stats.html Coverage + kolona "Ukupno"** (uzrok: coverage broji pobjednike po rečenici, ne kompletnost po modelu — dvije istine; bb_web_export `total` iz get_books, nav.js `stats_col_total_sent` ×5, sortabilna kolona; Hound/ro 3852/3852 vs Copy 500/3852 sad vidljivo). Konceptualno (bez implementacije): kontekst-injection mišljenje + **skica ti/vi baseline analize u 3 koraka** (inventar SQL/regex → konzistentnost po DocRE paru → tačnost na uzorku) — session_136.md. LEKCIJA: prije test-runa provjeriti da kombinacija postoji u bazi (10 neplaniranih Ollama poziva, obrisano 13706). BB_VERSION s135→s136. Detalji: `docs/sessions/session_136.md`.

> **s135 snapshot (13. jul 2026):** Nastavak s134 DUG liste. N-faza-safe web sloj ZAVRŠEN: reader.html dinamički phase panel, nav.js parametrizovani ključevi (`reader_phase_n`, `stats_col_phase_n`), stats.html dinamične kolone "Wins by engine and phase" — sve verifikovano browserom na k22/hr (3 faze) i starim slučajevima (2 faze). BB_VERSION s133→s135, buchenweb commit a3d203c. **NO-OP REFINE POTVRĐEN I ISPRAVLJEN:** SQL provjera pokazala 39/40 "izjednačenih" refine slučajeva iz s134 (240-uzorak) su bukvalno identičan tekst kao seed, ne koincidencija scorea (16,25% potrošenih refine poziva). Uzrok: `bb_03_prevod.py :: prevedi_refine_single()` prompt sadržavao "Keep the reference only if it is already optimal." — eksplicitna dozvola za klon. Live test potvrdio uzrok (stari prompt 3/3 klon uživo) i pokazao trade-off (agresivnija zabrana 0/3 klona ALI rizik promjene značenja na kratkim rečenicama). Flaviova odluka: minimalna izmjena — samo uklonjena "keep if optimal" rečenica, bez dodate zabrane. Necommitovano do kraja sesije. `v_status_faza_matrica` — pokušaj dinamičke PL/pgSQL funkcije (RETURNS SETOF record + EXECUTE) pukao na tačno-poklapanje-tipa ograničenju Postgresa (varchar≠text); Flavio odlučio da ne nastavlja — modifikacija SPUŠTENA na nizak prioritet. Novi horizont: NER+relacije kao kontekst-injection za refine kvalitet (ne samo ti/vi baseline) — zaseban budući session. Detalji: `docs/sessions/session_135.md`.

> **s134 snapshot (13. jul 2026):** **FAZA ≠ METOD — strukturno razdvajanje.** Nova tabela `bb_metode` (`base` root / `self-refine`), `bb_faze.metod_id` FK → **1 metod : M faza**; faza degradirana na redni broj + identifikator izvršavanja. ROOT-invarijanta ("base ide tačno jednom") preseljena iz ničije glave u SHEMU: partial unique index `WHERE metod_id=1` (verifikovano da puca). `bb_modeli` netaknut — UNIQUE(naziv,temp,faza_id) je N faza podržavao od s114; **uskost je bila isključivo u orkestratoru**. Novi `run_faza.sh --faza N` (+ `src/bb_faza_info.py`) **zamijenio `run_refine.sh`** (obrisan): `--faza` obavezan, ne auto-inkrementira; `--force` samo sudiji. **Faza 3 (`refine-2`) pokrenuta bez ijedne linije koda** — dva INSERT-a → k22/hr 1–40. Refine k22/23/24 × de/hr/it/sr × 1–20 (faza 2) + analiza: win-rate 30,0% (baseline 2/7=28,6%), **head-to-head 25,0%** (stari par: 0/100) — i **headroom gradijent**: k23 (najslabiji seedovi) jedina s pozitivnom deltom na sva 4 jezika (k23/sr seed 0,9267 → 11/20 pobjeda), k24 (najjači seedovi) −0,008…−0,021. OTVORENO: 40/240 refine prevoda ima **identičan finalni_score** kao seed (no-op sumnja). Novi viewovi `v_status_faza` (long, N-faza-safe) + `v_status_faza_matrica` (privremen pivot). NER k22 (85 relacija). **Faza 3 otkrila hardkod "refine=faza 2" u web sloju:** `bb_web_export.py` l.235 POPRAVLJEN (generički filter); **DUG:** `reader.html` l.746, `nav.js` i18n (`reader_phaseN`, `stats_col_phaseN` — treba jedan parametrizovan ključ), `stats.html` kolone. **Re-export namjerno NIJE pokrenut** (backend bi slao `faza3` koji reader ne zna prikazati — backend i frontend idu zajedno). Web kod netaknut → **BB_VERSION ostaje s133**. Detalji: `docs/sessions/session_134.md`.

> **s133 snapshot (13. jul 2026):** **NER LINIJA ZATVORENA.** Kriterij (Flavio):
> prihvatanje je TEHNIČKO (izvršava se / upisuje potpun sloj / izvoziv u web) — kvalitet
> klasifikacije je NALAZ, ne kriterij. **Odluka o obimu: proba/test samo na knjigama
> <2000 rečenica**; velike knjige idu sekvencijalno kad bude resursa (pokretanje, ne razvoj).
> Sva tri metoda rade. DocRE proširen: **J&H 23 relacije (1:15), Flatland 101 (4:05)** —
> daleko jeftinije od s130 procjene (28 min/knjiga; sitni promptovi iz s131). DocRE sad na
> 4 knjige: Hound 78/29 fine, Alice 60/10, J&H 23/10, **Flatland 101/1** — Flatland je
> najčistiji dokaz da ventil radi kao mjerni instrument (nema likova u karakternom smislu;
> Massey je character-character → 100 u ventilu = **nalaz o žanru, ne kvar**).
> **Web usklađen (stajalo razdvojeno od s131):** nlp.html KLASA_COLOR (P/M/O) →
> COARSE_COLOR (social/familial/professional/other), klik-panel `fine · coarse [± afinitet]`,
> **afinitet = stil linije (dashed = negative)**, pouzdanost zadržava debljinu; nav.js DocRE
> kartica ×5 jezika prepisana (taksonomija + afinitet + **imenovan ventil**), bez imena modela
> (s115). **Oba exporta pokrenuta:** `bb_web_export` (40s, ner_*.json nova shema) +
> `bb_xray_export` (1:09, **168 fajlova** — pokriveni novi opsezi, otvoreno od s132).
> Argumenti verifikovani u kodu: bb_09/bb_10/bb_10c + run_ner.sh svi imaju `--knjiga N|all`
> + `--force`; exporti ih nemaju jer im ne trebaju (regenerišu sve, idempotentno).
> **BB_VERSION s129.4 → s133.** Detalji: `docs/sessions/session_133.md`.
>
> **s132 snapshot (13. jul 2026):** ANALITIČKA sesija — kod/baza/web NETAKNUTI
> (BB_VERSION ostaje s129.4). Korpus narastao Flaviovim runovima: 50.624 / **1.544.460**
> prevoda / **301.368** pobjednika. **Prvi kontrolisani A/B paralelno-vs-sekvencijalno**
> (iste knjige k22/k23/k24, isti jezici de/hr/it/sr, opseg 200, susjedni rasponi):
> paralelni agregat 13.95 prevoda/min vs solo 5.64 → **2.47×, NE 3.77× (s119 korigovan)**.
> Pojedinačni proces 1.5–1.7× sporiji u četvorci. **NLLB kao nezavisan instrument** (lokalni
> CPU, ne dira Ollamu): do 2.66× sporiji → dio kontencije je na foxuno, ne u cloudu.
> **Asimetrija modela:** glm-5.2 @0.1 2.63× sporiji pod paralelizmom, mistral-large-3 @0.1
> samo 1.08× — neobjašnjeno. ⚠️ **Konfaund:** paralelni 17:31–22:06 CEST, sekvencijalni
> 22:29–03:14 CEST — režim i doba dana NISU razdvojeni. **k24 obrazac nijansiran:** prvi put
> mjeren na core-4 → glm 59.9% / mistral 37.3% (ranije ~48/48 na drugim jezičnim grupama);
> efekat knjige realan ali **jezično moduliran** (interakcija sadržaj × jezik, ne prosto
> "gotska proza"). Kvalitet nepromijenjen (0.962–0.971 oba režima). **Flaviova hipoteza
> "umorna baza"** (autovacuum/autoanalyze poslije danâ mirovanja) — ne objašnjava A/B (isti
> dan), ali objašnjava pomak baseline-a s119→s132; provjera `pg_stat_user_tables` otvorena.
> SLJEDEĆE: RUNOVI.md zapis (čeka k24 201–400), pa s132 web (bb_web_export + nlp.html ZAJEDNO).
> Detalji: `docs/sessions/session_132.md`.
>
> **s131 snapshot (12. jul 2026):** MASSEY IMPLEMENTIRAN kraj-do-kraja (baza+bb_10c).
> Korpus nepromijenjen (50.624 / 1.518.170 / 296.578). **(1) Dijagnostika prije
> arhitekture:** `sandbox_cluster_probe.py` (novo, read-only, 22s) — k-means+silhouette
> nad 138 opisa: silhouette 0.10-0.12 (globalno slabo) ali lokalna koherencija
> (klaster "neprijateljstvo" postoji!) → embedding za AUDIT da, za SUDIJU ne.
> Varijante (a)/(b)/(d=k-means, Flaviova hashing ideja) odbačene s dokazom; usvojena
> **(c): glm-5.2 klasifikuje iz zatvorene liste**. **(2) Shema** (backup
> pre_massey_20260712; stari dump obrisan — higijena /tmp): `bb_ner_massey` (29 fine
> + dominantni coarse IZMJEREN iz podataka — fine→coarse NIJE čista funkcija kod
> Masseya); `bb_ner_relacije` +fine (NULL=ventil)/afinitet/audit_kosinus, −tip_veze,
> UNIQUE(izvor,cilj); `bb_ner_tip_veze` DROPPED (odluka: brisanje, ne zamrzavanje).
> **(3) bb_10c prepisan:** Massey lista IZ BAZE; klasifikacija SAMO PERSON-PERSON
> (deterministički filter — Massey je character-character; mjesta=NULL bez LLM);
> `--reklasifikuj` (UPDATE bez ponavljanja prvog prolaza); think:false. **(4) Obje
> knjige reklasifikovane:** Hound 29/78 fine (enemy/negative za "plotting to murder",
> lovers/negative za lažnu romansu — afinitet dimenzija radi!), Alice 10/60.
> **VENTIL ŽIV PRVI PUT:** Hound 17, Alice 21 — sadržaj dosljedno RADNJE (istraga,
> razgovor) = s130 dijagnoza sada mjerena. Nedeterminizam ±1-3 uz temp 0.0.
> **(5) NALAZ — šum tipova (Alice):** Dodo/Duchess/March Hare→ORG, Cheshire Cat→GPE
> (spaCy news-bias na fantastici); bb_10 rješava samo konflikte → **"type audit" na
> horizont uz koreferenciju** (koja se javila 3. put: "is the same person as" u
> ventilu). Hound tipovi zdravi (provjereno). **(6) bb_web_export.get_ner_relacije
> prepravljen** (fine/coarse/afinitet/audit, LEFT JOIN — NULL relacije ostaju) ali
> **export NIJE pokrenut**: web konzistentan (staro+staro); ⚠️ novi JSON + nlp.html
> idu ZAJEDNO u s132. BB_VERSION ostaje s129.4. Margin-based ventil SKINUT s liste
> (nepotreban — LLM "ostalo" živ po konstrukciji). SLJEDEĆE (s132): nlp.html
> (coarse boje, afinitet prikaz) + export + browser test; koreferencija+type audit
> u bb_10; tek onda run_ner.sh --knjiga all --force. Detalji:
> `docs/sessions/session_131.md`.
>
> **s130 snapshot (12. jul 2026):** NER ORKESTRACIJA + CASCADE shema + **otkriće da je DocRE
> rječnik pogrešno postavljen**. Korpus nepromijenjen (50.624 / 1.518.170 / 296.578).
> **(1) `run_ner.sh`** — orkestrator bb_09→bb_10→bb_10c; `--knjiga N|all`, `--force`.
> **PRAVILO: `--force` je svojstvo prolaza, ne faze** ("sve je force ili nije force").
> Bez flaga: radi samo ono čega nema, i **glasno kaže šta preskače**. Prazan prolaz = 20s.
> **(2) SHEMA — ON DELETE CASCADE** (backup `/tmp/bb_backup_pre_cascade_20260712.dump`):
> 5 FK-ova na `bb_ner_entiteti(id)` (recenica.entitet_id, veze.entitet1/2_id,
> relacije.izvor/cilj_id) `NO ACTION`→`CASCADE`. Ostala 4 (knjiga_id ×3, tip_veze)
> ostaju NO ACTION namjerno (lookup, ne izvedeni sloj). **PRAVILO (Flavio): skripta ne
> ruši ništa ispod sebe i ne zna za slojeve iznad sebe — zavisnost enkoduje SHEMA, ne kod.**
> Dokazano: bb_10 --force obrisao llm entitete → 74 DocRE relacije pale same.
> **(3) bb_09 — TRI zaostatka iz s126/s129:** DELETE bez `method` (rušio llm sloj);
> ON CONFLICT bez `method` (pucao — s126 proširio UNIQUE); i **sudija gemma4 radio NER
> normalizaciju** (kršenje s124!) → sad **glm-5.2**, think:false. Sve tri popravljene.
> **(4) llm sloj sad na svih 9 originalnih knjiga** (bb_10 --knjiga all, 9:44).
> Hound preračunat: classic 200/199, llm 181/191, **DocRE 78**. Alice: llm 107, DocRE 60.
> Nedeterminizam faze 2 mjeren: spaCy pojave identične (1239 ×3), entiteti variraju
> ±5% uz temp 0.0 → **`--force` na bb_09 znači "preračunaj", ne "prepiši istim"**.
> **(5) GLAVNI NALAZ — rječnik nije loš, nego pogrešno postavljen.** Ventil `ostalo`
> **mrtav po konstrukciji** (najniži kosinus u J&H = 0.857, prag = 0.85 → nikad se ne
> aktivira). Ne curi u ventil — **curi u pogrešne grupe, tiho**: "murdered"→`kretanje`,
> "condemns"→`kretanje`, "converses with"→`susjedstvo` (16× u Alisi = skriveni ventil).
> **Korijen: miješali smo STATUS (srodstvo/sluzba) i RADNJU (kretanje/istraga)** — dvije
> nespojive ose u jednoj ravnoj listi. Nemamo pojam za neprijateljstvo, samo za kretanje.
> Uz to: **koreferencija promiče NER sloju** (Jekyll=Hyde, King=Majesty — a to je zaplet).
> **(6) RJEŠENJE — Massey/Bamman taksonomija USVOJENA** (`data/external/characterRelations.txt`,
> repo `dbamman/characterRelations`, 2.170 anotacija iz 109 knjiga, Homer→Joyce).
> **Ortogonalna, ne ravna:** coarse (social/familial/professional) × fine (29: friend,
> enemy, parent, servant, lovers, master…) × **affinity (positive/negative/neutral —
> dimenzija koju uopšte nemamo)**. "murdered" → social/enemy/**negative**.
> DocRED (96 tipova) **odbačen** — enciklopedijski (lični život samo 4,2%).
> ⚠️ Massey `detail` polja **NISU upotrebljiva kao centroidi**: 1.622/2.170 su `NR`, ostatak
> šumovit ("tries to kill him" → friend). **Uzimamo shemu, ne njihove podatke.**
> **(7) Mjerenja:** DocRE ≈ 28 min/knjiga (4% CPU — čeka Ollamu; 5× 524; `--knjiga all`
> ≈ 4-6h). **524 ∝ veličina prompta potvrđeno drugi put.** PRAVILO: dug LLM proces
> UVIJEK `PYTHONUNBUFFERED=1 nohup time ... > logs/*.log 2>&1 &` — i za NER skripte.
> **SLJEDEĆE (s131):** (a) od čega graditi centroide za 29 fine kategorija — ime
> kategorije / naši seedovi / LLM iz zatvorene liste? (b) `bb_ner_relacije` → coarse+fine
> +afinitet; (c) **margin-based ventil** umjesto apsolutnog praga (kosinusi 0.857-0.98 =
> nema diskriminacije); (d) koreferencija kao faza u bb_10; (e) nlp.html afinitet;
> (f) tek onda `run_ner.sh --knjiga all --force`. Detalji: `docs/sessions/session_130.md`.
>
> **s129 snapshot (11. jul 2026):** DocRE KOMPLETIRAN kraj-do-kraja (baza+web).
> Korpus nepromijenjen (1.518.170 prevoda / 296.578 pobjednika). **3 nove tabele**
> (backup prije DDL, s123): `bb_ner_tip_veze` (rječnik grupa, 13 redova: klasa P/M/O
> + tip_veze PK + opis_grupe; lookup obrazac kao bb_model_registar), `bb_ner_veze`
> (co-occurrence materijalizovan, 3820 parova, entitet1<entitet2+tezina), `bb_ner_relacije`
> (DocRE usmjeren izvor→cilj, tip_veze FK, opis/smjer/dokaz/dokaz_pozicije/pouzdanost,
> 74 relacije Hound). `method` implicitan preko entitet_id (s128). **Rječnik 12 grupa**
> (8 P osoba-osoba: srodstvo/prijateljstvo/angazman/sluzba/istraga/zastita/prevara/
> susjedstvo + 4 M osoba-mjesto: kretanje/prebivaliste/posjed/radnja + O ostalo-ventil),
> kristalisan iz 75 probnih opisa. **`bb_10c_docre.py`** (commit 39ae0b1): prvi prolaz
> par-vođen (glm-5.2, iz s128 probe), drugi prolaz e5-large embedding opisa → najbliži
> od 12 centroida (SEED_OPISI; goli .encode() konzistentno s bb_06) → tip_veze; prag
> ostalo 0.85 (kalibrisan na kosinusima 0.86-0.98, "mjeri pa definiši"). A/B bug fix
> (LLM vraća "A"/"B"/"Ime (TIP)" → _norm mapiranje). `get_ner_veze` prepisan da ČITA
> materijalizovanu tabelu (web-export read-only, s128; verifikovan bit-identično sa
> starim self-joinom). Nova `get_ner_relacije` → relacije u llm grani JSON-a
> (`{knjiga_id, classic, llm:{entiteti,veze,relacije}}`, opcija a). **nlp.html: DocRE
> TREĆI RAVNOPRAVAN POGLED** (Flaviov ispravak: ne skriveni switch nego treći taster
> Classic|With LLM|DocRE); usmjeren graf (strelica+boja po klasi, legenda, klik→
> opis+dokaz); **tri infoboxa (šta+kako)** s DocRE naglaskom "sami implementirali,
> gotov softver ne postoji"; i18n ×5 (nlp_mcard_*; What/How po jeziku). Intro skraćen
> ×5 (uska praznina). BB_VERSION s127→s129.4. Commits: buchenberg (bb_web_export +
> session_129 + README), buchenweb 668af2d. SLJEDEĆE: bb_10c --knjiga all kad llm sloj
> sazrije na drugim knjigama, tjuning rječnika/ventila na drugim žanrovima, prompt na
> stranici, ner_ orkestracija. Detalji: `docs/sessions/session_129.md`.
>
> **s128 snapshot (11. jul 2026):** DIZAJNERSKA sesija — otvoren Dio 2 #1 (DocRE,
> relacije van rečenice). Baza/web NETAKNUTI → BB_VERSION ostaje s127. Ključne odluke:
> **(1) Proizvodnja vs izvoz — čvrsta granica:** proizvodni sloj (bb_09/bb_10/DocRE)
> zove LLM/spaCy i UPISUJE; izvozni (bb_web_export) samo ČITA/agregira, READ-ONLY.
> LLM u web-exportu = anti-pattern. **(2) Skladište relacija — DVIJE tabele** (Flaviov
> kriterij: isti atribut/različita semantika → dvije tabele; co-occ `tezina`=broj
> rečenica simetrično vs DocRE smjer nosi značenje): `bb_ner_veze` (co-occurrence,
> simetrična, `entitet1<2`, tezina) + `bb_ner_relacije` (DocRE, USMJERENA izvor→cilj,
> tip_veze/opis/dokaz/dokaz_pozicije). `method` implicitan preko entitet_id (web-export
> JOIN+filter). **(3) Materijalizovati** i co-occurrence (get_ner_veze self-join →
> čitanje). **(4) DocRE strategija PAR-VOĐENA** (Flaviov preokret): kreni od entiteta+
> tačnih pozicija (bb_ner_recenica), nađi parove s ≥prag bliskih susreta, LLM daje
> jednu USMJERENU vezu po paru. **(5) Rječnik grupa (~10 tip_veze) = dvoprolaz**
> (slobodni opis→embedding e5-large→najbliža fiksna grupa, s90 princip); kristalisati
> IZ podataka. **Proba** (`bb_10b_docre_probe.py`, NIJE commitovan, nula upisa): 15
> najjačih parova Hounda, glm-5.2 → 14 relacija, smjer+tip+dokaz visok kvalitet
> (Charles→[uncle of/left estate to]→Henry; Holmes↔Watson mutual; Holmes→[investigating
> death of]→Charles). Sirovina za ~8–9 grupa dobijena. Mjerena geografija entiteta
> (Holmes 189 pojava raspon 3–3688; bliski parovi rangirani). Zatvaranje samostalno
> (Flavio odsutan, jednokratni izuzetak). SLJEDEĆE: kristalisati grupe → kreirati
> tabele (backup!) → proba u produkciju (bb_10 faza/ner_ porodica, --knjiga all) →
> materijalizovati co-occ → web (usmjeren graf, boja po tip_veze, klik→opis+dokaz).
> Detalji: `docs/sessions/session_128.md`.
>
> **s127 snapshot (11. jul 2026):** LLM NER Dio 2 (planirani redoslijed 1→3). **(1) Kompletiran llm sloj** — `bb_10_ner_llm.py` sad kopira i nekonfliktne classic entitete kao čiste llm redove (unutar `upisi_llm`). Hound llm sloj: 181 entitet (163 nekonfliktna + 18 razriješenih) / 1219 veza; classic netaknut (201/1236). Manje veza kod llm = čišća mreža (uklonjeni lažni entiteti + pogrešne type-veze). Commit buchenberg f4a725a. **(2) Web export** — `get_ner`/`get_ner_veze` +`method` param; `ner_<id>.json` nova struktura `{knjiga_id, classic:{...}, llm?:{...}}` (llm grana SAMO ako knjiga ima llm sloj). **(3) nlp.html preimenovan** u **"Named Entities & Relations"** (fajl ostaje nlp.html; meni "Entities", naslov+meni prevedeni ×5); **word cloud UKLONJEN** (redundantan s books.html, ne hrani NER — X-Ray: šum, ne signal); **classic/with-llm toggle** (grana-svjesno: `nerFull`/`nerData`=aktivna grana, ~15 postojećih referenci netaknuto; toggle skriven ako nema llm); **method intro + dinamični opis** (statični intro imenuje **spaCy** uokvireno kao about-modeli — "tool we chose, could be replaced"; dinamični red prati aktivni sloj; svi ×5 jez). Toggle labele "Classic"/"With LLM" = svjestan preostali EN i18n izuzetak. BB_VERSION s125.5→s127. Commits: buchenberg f4a725a, buchenweb (ovaj commit). SLJEDEĆE: relacije van rečenice (DocRE, najkrupnije), prompt na stranici, bb_10 na ostale knjige. Detalji: `docs/sessions/session_127.md`.
>
> **s126 snapshot (10. jul 2026):** Početak LLM-potpomognute NER analize (Dio 1: type reconciliation). Nova **`method` kolona** na `bb_ner_entiteti` + `bb_ner_recenica` (TEXT NOT NULL DEFAULT 'classic'; UNIQUE bb_ner_entiteti → +method) — classic i llm NER koegzistiraju paralelno, "prije/poslije" prikaz. Backup prije DDL (1.5G, `/tmp/bb_backup_pre_method_20260710_145601.dump`). Nova skripta **`bb_10_ner_llm.py`** (glm-5.2, NE sudija — s124 princip): čita konfliktna imena (isto ime, >1 tip = spaCy nekonzistentnost) + do 4 dokazne rečenice po tipu, LLM presuđuje IZ TEKSTA (grounding, s90), tri ishoda — `greska` (spoji u primarni), `dvojnost` (2 legitimna smisla, npr. Baskerville osoba+imanje), `ne_entitet` (odbaci, npr. "I."=zamjenica). LLM smije predložiti tip van postojećih labela (Coombe Tracey classic PERSON/ORG→llm GPE). Baseline (Hound, prije gradnje): 18 type conflicta + relacije samo 28 na pragu ≥2 od 194 ukupno (mreža gotovo prazna — co-occurrence samo iste-rečenice). Test Hound: 18 konflikata, 0 JSON grešaka, 17/18 očigledno tačne → upis 18 llm entiteta / 365 veza. Web NETAKNUT → BB_VERSION s125.5. bb_web_export.py NIJE još diran. SLJEDEĆE (Dio 2): kompletiranje llm sloja (sad samo 18 konfliktnih imena), relacije van rečenice (DocRE/koreferencija, prozor N rečenica + grounding), web toggle classic/with-llm na nlp.html, prompt prikazan na stranici. Detalji: `docs/sessions/session_126.md`.
>
> **s125 snapshot (10. jul 2026):** Korpus nepromijenjen (1.518.170 prevoda / 296.578 pobjednika — Flavio prekinuo runove za vrijeme sesije). Word cloud univerzalno pismo (`\p{L}` regex, books.html+nlp.html — ćirilica sr/bg/mk sad radi). **learn.html i18n potpuno zatvoren** (otvoren od s120) — runtime JS (40 zamjena, 29 novih ključeva) + statični HTML (18 zamjena, 5 novih ključeva), oba dijela u jednoj sesiji, sve 4 igre verifikovane u browseru. Sentence Match estetika (CSS grid, redovi poravnati po visini). Privremeni prikazni prevod DB registra (Type/Role) na stats.html — baza netaknuta, jasno označeno kao izuzetak dok se ne uradi trajni fix. BB_VERSION s123.2→s125.5. Commits: buchenberg 39f43cc, buchenweb 7171738/345e759/d331f87/7cc43ca/015efc5. Detalji: `docs/sessions/session_125.md`.
>
> **s123 snapshot (9. jul 2026):** **WEB FAZA 3 KOMPLETNA** — fazni prikaz kroz cijeli lanac. Detaljan plan `docs/WEB-FAZA3-KORACI.md` (Claude iz konceptualnih docs → izvršni koraci). **Nova tabela `bb_model_registar`** (naziv PK, vrsta, uloge TEXT[]; backup 1.5G prije DDL; 10 redova: opšti LLM/namenski MT model/embeder × prevodilac/sudija/vektorizacija; uzak registar, bb_modeli nedirnut, bez DEFAULT). `bb_web_export.py`: faza u `get_translations` (tr_ nosi faza po rečenici) + `get_stats` (winners_by_config Tabela 2, winners_by_engine Tabela 1 s faza1/faza2/ukupno, models Tabela 0 iz registra; stari `winners` uklonjen) + novi `get_phase_winners` → `phases_<id>_<lang>.json` (127 fajlova, Nivo B before/after, sparse). stats.html: tri tabele (0 modeli+uloge / 1 by-engine+faza / 2 by-config); reader.html: "refined" badge (faza 2 apsolutni pobjednik) + klik→before/after panel s "winner" oznakom. nav.js: 20 novih ključeva × 5 jezika. Nalaz: faza-2 win-rate svuda niži od faza-1 (ANALIZA pejsmejker, brojkom). Odluke zabilježene: DB vrijednosti→engleski (budući izuzetak kao Key Concepts); uloga-po-instanci (ekstremni slučaj) budući redizajn; ministral Markdown `**` artefakt ostaje (server=istina). BB_VERSION s120→s123.2. Commits: buchenberg b014ed5, buchenweb 26e34c3. Detalji: `docs/sessions/session_123.md`.

> **s122 snapshot (9. jul 2026):** Analiza 48 log fajlova (dva Flaviova paralelna runa, 4+4 grupe) preko `parse_run_logs.py` → dva nova unosa u `docs/RUNOVI.md`. Dnevni run (8. jul): k23 core-4 nastavak (1501-2000) + prvi bazni prevod es/fr/pt/ro na k22/k23/k24 — k24 (Frankenstein Copy) obrazac treći put potvrđen (glm/mistral 48.5/47.8%). Noćni run (8-9. jul, preko ponoći): k23 core-4 nastavak (2001-2500) + prvi bazni prevod af/nl na k22/k23/k24 — k24 obrazac četvrti put, PRVI PUT mistral ispred glm (48.1% vs 47.9%). Metodološka lekcija: pozicijska "rečenica/min" nije uporediva preko grupa s različitim brojem jezika — throughput mjeriti kao prevoda/min. Takođe: provjerena i prihvaćena s121 (Windows Cowork app sesija bez pristupa memoriji, verifikovana kroz git hronologiju kao legitimna). Baza/web nedirnuti (Flaviovi pozadinski runovi rastu nezavisno). Detalji: `docs/sessions/session_122.md`.
>
> **s120 snapshot (8. jul 2026):** Web Faza 2 implementacija ZAVRŠENA — svih 9 stranica (WEB-FAZA1.md → Faza 2, "u jednom dahu", odluka s118). index.html: G1 hardkod sync. about.html: nova Self-refinement sekcija (5 jezika, dijagram) + okvir o imenima modela (svjesni izuzetak). stats.html: naslov "X-Ray Stats"→"Stats"/"Statistics" (3 mjesta, 5j); reading_note bez imena/zastarjelih brojki; model-boja u winner tabeli name-independent (hash→HSL, isti obrazac kao art.html); -2 Key Concepts kartice (index/about/stats). books.html: naslov "Library" usklađen na 5 jezika. geometry.html: uklonjeno "(Gemma4:31b)" (5j). art.html: novi `art_title` ključ (5j, jedina stranica bez njega prije ovoga); Tapestry `MODEL_COLORS` (fiksna lista) → hash-bazirana boja + dinamička legenda iz stvarnih podataka. reader.html (najveći zadatak): lokalni `const I18N` objekat POTPUNO obrisan — migriran u centralni NAV_I18N (14 `reader_` ključeva × 5j); SR `author`/`language` ispravljeni latinica→ćirilica ("Autor"→"Аутор", "Jezik"→"Језик"); X-Ray legenda ostaje EN hardkod (navedeni izuzetak, netaknuto) + "(gemma4:31b)" uklonjen iz Judge Average reda. Sva 4 dokumenta u `docs/` (KAKO-JeziciUI.md, STRANICE.md) ažurirana da reflektuju novo stanje. Baza netaknuta. BB_VERSION s115 → s120. Commit `5d2f470` (buchenweb). Detalji: `docs/sessions/session_120.md`.
>
> **s117 snapshot (7. jul 2026):** Dva posla. (1) **RUNOVI statistika — trajni alat:** `src/parse_run_logs.py` (parsira pipeline/refine logove → JSON: knjiga/jezici/broj_jezika/raspon/faza/start-end/elapsed/recenica_po_minutu/prevod_steps/sudija_real/pobjednik_real/po-jeziku avg_final+komp+sudija+model_counts) + `docs/RUNOVI.md` (rastući, 2 tabele po runu: identifikacija&vrijeme / kvalitet&pobjede + zapažanja). Prvi run: k23 Big Four Copy de/hr/it/sr 1–500 faza 1 — avg_final 0.9691, pobjede glm-5.2 63.0%/mistral-large-3 30.7%/nllb 6.3%. Commit `3b78ff6`. (2) **Web faza 1 start:** novi pristup "prvo priprema pa implementacija u jednom dahu" (kao s114); dvije faze (1=tekst/UI-prevodi/vidljivi elementi, 2=tehnička implementacija), stranica po stranica, cross-cutting nalazi→globalna pravila. Novi `docs/WEB-FAZA1.md`. index.html obrađen: i18n rječnik ČIST (s115 stoji), ali otkriveno **globalno pravilo G1** (HTML hardkod fallback još imenuje modele — mora pratiti očišćeni rječnik) + **G2** (title↔menu↔naslov provjera po stranici). Memorija: KONFLIKT pravilo ublaženo (može biti stop ako suštinski, ne rigidno). Baza/buchenweb netaknuti → BB_VERSION s115. Detalji: `docs/sessions/session_117.md`.
> **s116 snapshot (6. jul 2026):** Tri nova referentna dokumenta u `docs/` — motivisano Flaviovim opažanjem da Claude (tekstualni AI, bez pristupa vizuelnom prikazu) ne može pouzdano znati stranica↔menu↔naslov mapiranje ni i18n/Key Concepts proceduru bez eksplicitne provjere. **`STRANICE.md`** — tabela svih 9 stranica × menu tačka × naslov, generisana iz stvarnog stanja (`nav.js`+HTML, ne pamćenje); otkrila 4 nesklada (art.html naslov hardkodovan bez i18n; books.html `<title>` zaostao "Books" iza `<h1>` "Library"; stats.html menu≠naslov; index/reader nemaju fiksan naslov). **`KAKO-JeziciUI.md`** — kompletna referenca za i18n tekst (arhitektura NAV_I18N, checkliste dodaj/izmijeni/obriši, tehnička metoda + anchor pravila, ledger 10 bagova s61-s115). **`KAKO-KeyConcepts.md`** — ista vrsta reference za Key Concepts/Wikipedia kartice, mehanizam verifikovan direktno iz `nav.js` (CONCEPT_PAGES/CONCEPT_TITLES/#bb-footer, kartice jednojezične, tih fail na broken JSON — briše kartice sajt-široko bez greške). Usput: verifikacija `run_pipeline.sh`/`run_refine.sh` poziva za k23 — sintaksa OK, nedostajao `nohup`/pozadinsko izvršavanje; nijansa iz s102 (vanjski `time` suvišan za ove skripte) imenovana. Baza/web netaknuti → BB_VERSION ostaje s115. Detalji: `docs/sessions/session_116.md`.

> **s115 snapshot (6. jul 2026):** Korak 4 (web), prvi dio. **Trajni princip: nijedan model se ne imenuje NIGDJE u web prezentaciji — opiši ulogu/proces, ne komponente (imena su prolazna, dva retirement talasa/nedjelji to dokazuju); konkretne vrijednosti iz baze su izuzetak.** Reader legenda: uklonjena imena + `-refine` pojam iz Model reda, NOVI Phase red (rješava s114 lekciju 5 — kandidati iste trojke nerazlučivi bez faze), Self-Refine vezan za "Phase 2". Home (index.html) proza: 4 ključa × 5 jezika (how_desc, how_desc2, pillar_judge, pillar_refine) — uklonjena sva imena (gemma3/ministral/nllb/gemma4-sudija) i brojevi ("two refine models", "three models"). Sudija opisan po ulozi ("LLM chosen only to judge, never translate"). Otkriveno: `index_funnel_*`/`lbl_*`/`cta_*` mrtvi ključevi (index.html ih ne poziva). Lekcija: koristiti README §"Web how-to: i18n" PRIJE improvizacije. buchenweb → BB_VERSION s115. Baza netaknuta. Sljedeće: stats.html `stats_reading_note` (isti tretman). Detalji: `docs/sessions/session_115.md`.

> **s114 snapshot (6. jul 2026):** IMPLEMENTACIONA SESIJA ("jedan dah") IZVRŠENA — backup (1.5G pg_dump na hostu) → shema bb_modeli (faza_id NOT NULL, +aktivan, UNIQUE trojka, rename 12/13 bez sufiksa, novi par id 18–23) → skripte (bb_03 `--faza` umjesto `--refine`; NOVI bb_aktivni_modeli.py; run_pipeline/run_refine DB-vođeni; bb_08 aktivan-filter + sudija1 obrisan; health_check DB-vođen; bb_xray_export +faza) → test cijelog lanca Hound Copy k22/hr/1–10 (50+20 kandidata, 10 pobjednika, s4 = prva refine pobjeda novog para: glm-5.2@0.8 faza 2). 9 dana prije retirement roka. Web kod netaknut → BB_VERSION s108.4 (data regenerisan). Korak 4 (web) sljedeći. Detalji: `docs/sessions/session_114.md`.
>
> **s113 snapshot (5. jul 2026):** Copy knjige — fizičke kopije 3 potpuno prevedene knjige kao nove knjige (id 22/23/24: Hound/Big Four/Frankenstein + " Copy", gutenberg_id +"c"); +12.291 rečenica (korpus 50.624), 0 prevoda — original ostaje zamrznuta referenca starih modela, Copy se prevodi novim parom poslije refaktora → direktno staro-vs-novo poređenje na punom korpusu. Kopije bit-identične (0 razlika u tekstu). Kod netaknut → BB_VERSION s108.4. Detalji: `docs/sessions/session_113.md`.
>
> **s112 snapshot (5. jul 2026):** Novi kanonski dokument `docs/KONCEPT.md` — identitet pipeline-a (minimumi + proces, ne komponente; refine = iteracija istog procesa; apsolutni pobjednik = najbolji preko SVIH faza; min 1 model u refine fazi; trojka (model, konfiguracija, faza) umjesto `-refine` sufiksa). Audit: UNIQUE(naziv,temperatura) → mora +faza_id; redovi 12/13 se samo preimenuju (prevodi netaknuti); bb_03 refine već ide flagom, sufiks samo lookup+replace; exporti ne iznose fazu → bb_xray_export +faza polje. **ODLUKE: refaktor + zamjena zajedno ("jedan dah") prije 15. jula; par gemma3:27b+ministral-3:8b prihvaćen pa ISTOG DANA poništen drugim retirement talasom (kompletna Ollama lista — obje familije nestaju) → NOVI PAR kroz sondu: mistral-large-3:675b + glm-5.2 (vidi dodatke s112).** Kompletna mapa: `docs/sessions/session_112.md`. Baza/web netaknuti → BB_VERSION s108.4.
>
> **s111 snapshot (4. jul 2026):** Kompletna mapa uticaja zamjene modela (nezavisno od finalnog izbora) — 5 skripti za izmjenu identifikovano (`run_pipeline.sh`, `run_refine.sh`, `bb_08_sudija.py`, `health_check.py`, `bb_01_init_lookup.py`); 10 legacy skripti potvrđeno mrtvo (zadnje diranje maj, prije bb šeme). `bb_modeli` ne treba schema promjenu za registraciju; opciona kolona `aktivan` za trajni refaktor ostaje otvorena. Puna mapa: `docs/sessions/session_111.md`. Baza/web netaknuti → BB_VERSION s108.4.
>
> **s110 snapshot (4. jul 2026):** gemma3:27b + ministral-3:8b registrovani (id 14–17). Test Dracula/bs, 42 rečenice, swap-dizajn: prosjek finalni_score stari>novi u obje porodice, ali statistički neodlučivo (t<2, n=42); head-to-head skoro 50/50. Odluka o zamjeni OTVORENA. Otkriven i zaobiđen hardkod OCJENJIVANI_MODELI u bb_08_sudija.py (test-kopija bb_08_sudija1.py). Baza vraćena u prvobitno stanje za test-opsege. Web netaknut → BB_VERSION s108.4.
>
> **s109 snapshot (3. jul 2026):** ~1,187M prevoda / ~230k pobjednika (health-check početak s109; procesi trče — živi broj iz baze). Ollama najavila retire gemma3:12b + ministral-3:14b za 15.jul. Izgrađena `sandbox_model_probe.py` (read-only sonda ponašanja modela). Otkriće: **thinking (ne veličina) je glavni množilac troška** — gpt-oss:20b 251tok/nemotron:30b 907tok vs etaloni 12-15tok; `think:false` poštuje nemotron (907→10) ali NE gpt-oss (zaglavljen). Unutar-familije gemma3:27b/ministral:8b = jeftin drop-in (9-11tok, ponašanje kao etaloni). Odluka: produkcijski test para **gemma3:27b + ministral-3:8b** (sljedeća sesija, kroz sudiju). Baza/web netaknuti → BB_VERSION s108.4.
>
> **s108 snapshot (2. jul 2026):** Web prezentacija self-refine na Home. „How it works" dobio fazu 2: drugi pasus (anchored mutation) + kartica 🧬 Self-refinement + winner „across both phases"; prevedeno na svih 5 UI jezika. Grid 2+2. Key Concepts: dodata **Mutation** (`Mutation_(evolutionary_algorithm)`); self-refine nema Wikipedia članak → izostavljen (odluka: samo postojeći EN wiki članci). **buchenweb DIRNUT prvi put od s102 → BB_VERSION s108.4.** Korpus strukturno nepromijenjen (živ rast tokom sesije — Flaviovi procesi). README: higijena (header/authorship/§9 s107 red, 10 `.bak` obrisano) + novi §10 how-to.

| Knjiga | id | Jezik | Prevodi | Pobjednici |
|--------|-----|-------|---------|-----------|
| Hound | 1 | hr | 3852 | 3852 ✅ |
| Hound | 1 | sr | 3852 | 300 |
| Hound | 1 | bs | 3852 | 350 |
| Hound | 1 | de, it, af, bg, es, fr, mk, nl, pt, ro, sl | 3852 | 200 |
| Flatland | 21 | sr | 1341 | 1000 |
| Flatland | 21 | de, it | 1341 | 500 |
| Flatland | 21 | hr | 1341 | 200 |
| Moby Dick | 12 | hr, sr, it, de | 1500 | 150 |
| Romeo and Juliet | 17 | hr, sr, it, de | 1500 | 150 |
| Alice | 18 | hr, sr, it, de | 1500 | 150 |
| Dracula | 20 | hr, sr, it, de | 1500 | 150 |
| Jekyll & Hyde | 19 | hr, sr, it, de | 1157 | 150 |
| Frankenstein | 8 | hr, sr, it, de | 260 | 150 |
| Frankenstein | 8 | ro | 300 | 100 |
| Big Four | 5 | hr, it, de | 260 | 150 |
| Big Four | 5 | sr | 260 | 200 |
| Big Four | 5 | pt | 300 | 100 |

**Napomena:** Jezici bez pobjednika (af, bg, bs, es, fr, mk, nl, pt, ro, sl za većinu knjiga) imaju samo NLLB prevode — namjerna taktika (pre-fetch), nisu anomalija.

**Srpski (sr):** prevodi transliterirani u ćirilicu (`bb_sr_cirilica.py`). `back_translation` se ne dira (fix s84).

---

## 10. Infrastruktura

### Serveri

| Server | Adresa | Uloga |
|--------|--------|-------|
| **foxuno** | `foxuno.dynu.net` | Razvoj, kod, Python venv, git |
| **balsam** | `balsam.dynu.net` | Docker host — PostgreSQL |

> ⚠️ Sav razvoj je na **foxuno**. User se zove `balsam` ali to je user na foxuno serveru!

### Backup raspored (CET/CEST, Vienna — ljeti CEST=UTC+2)

| Server | Backup prozor |
|--------|---------------|
| foxuno | ~01:00–03:00 |
| balsam | ~03:00–08:00 |

Oba backupa mogu dodatno opteretiti server tokom tih prozora — uzeti u obzir pri planiranju velikih pipeline runova.

### MCP alati

- `foxuno:run_command` — skripte, fajlovi, git
- `balsam:run_command` — SQL operacije (`docker exec pgdb psql`)
- **Ne miješati** — SQL komande idu isključivo na balsam

### Docker host (strato) — pgAdmin / pgdb

> 📌 **Saznanje s98:** `balsam:run_command` se izvršava na **strato hostu** (`hostname`=strato) kao user `balsam`. To je isti fizički host gdje žive Docker kontejneri. Kontejnere starta user `vespa` iz `/home/vespa/docker/pg/docker-compose.yml`. **I `balsam` i `vespa` su u `docker` grupi** → dijele docker socket; `balsam` user može `docker ps/logs/exec/stats` (read-only dijagnostika) **bez sudo**, bez obzira ko je startao kontejner.

| Kontejner | Servis (YAML) | Port | Uloga |
|-----------|---------------|------|-------|
| `pgdb` | `db` (postgres:17) | 5432→5432 | **Produkcijska baza bb — NE dirati pri pgAdmin intervencijama** |
| `pgad` | `pgadmin` (dpage/pgadmin4) | 8080→80 | pgAdmin web UI |

- **pgAdmin pristup:** https://viapola.dynu.net → Apache reverse proxy (443) → `127.0.0.1:8080` → `pgad`.
- **Podjela privilegija:** Claude = samo user `balsam` (read-only docker dijagnostika). Flavio = sudo + `vespa` komande (`docker compose` recreate, izmjene compose fajla, Apache logovi).
- **Privilegija ≠ postojanje:** prazan `ls /home/vespa/...` kao balsam = nemam pravo gledati tuđi home, NE "ne postoji".

**pgAdmin FD-exhaustion obrazac (s98):** gunicorn worker (`-w 1 --threads 25`) s niskim soft `nofile`=1024 vremenom napuni file descriptore → `OSError: [Errno 24]` → worker se zaglavi (živ proces, 0% CPU, ne odgovara; "funkcionalno mrtav"). Dijagnostički potpis: `curl 127.0.0.1:8080` timeout + log staje na "Worker exiting / Errno 24" + `ps -eo etime` pokazuje stare procese (npr. 18d, restart ih nije pomjerio).
- **Privremena popravka (Opcija 1):** `docker rm -f pgad && docker compose up -d pgadmin` (volume `pgad_data` ostaje → konekcije sačuvane). `restart` i `--force-recreate` ne pomažu (zaglavljen kontejner, conflict na imenu).
- **Trajna popravka (Opcija 2, odgođeno):** dodati `ulimits: nofile: {soft: 65536, hard: 65536}` u `pgadmin` servis + `docker compose up -d pgadmin`.

### Web prikaz

- **URL:** https://buchenberg.opik.net
- **DocumentRoot:** `/var/www/buchenberg/`
- **JSON data:** `/var/www/buchenberg/data/`
- Apache2 odmah servira novi sadržaj — nema potrebe za restartem
- **Git repo:** `fladroid/buchenweb` — odvojen od buchenberg; inicijalni commit s73
- **Workflow izmjena:** `cd /var/www/buchenberg && git add . && git commit -m "opis" && git push`

> ⚠️ `buchenberg` i `buchenweb` su dva odvojena git repozitorijuma. Web izmjene se commituju isključivo iz `/var/www/buchenberg/`.

**Struktura web stranica (sesija 45):**

| Fajl | Stranica | Opis |
|------|----------|------|
| `index.html` | Landing page | Čist pitch: hero (heksagon + MT Lab), Key Concepts kartice, How it works (3 stuba), open-source nota. Current status (kartice + funnel) preseljen na stats.html (s101). |
| `about.html` | O projektu | Detaljna dokumentacija: pipeline, modeli, scoring, infrastruktura |
| `stats.html` | Stats (od s120, bilo "X-Ray Stats") | Corpus funnel (38k rečenice → kandidati → izabrani prevodi + full-14), definiciona nota ("kako čitati brojeve": prevod=rečenica-jezik par, engine vs konfiguracija, NLLB=dedicated MT), 5 summary kartica (uklj. 14 jezika i 126 kombinacija), winner distribution, coverage, avg scoreovi. **DB-side agregacija (s99):** čita `data/stats.json` (generiše `bb_web_export.py:get_stats()` — od s101 +total_sentences/total_candidates/total_languages/full_all_langs). |
| `limits.html` | Limits (s146) | **What We Don't Measure** — publikovane granice i negativni nalazi mjernog aparata: slijepe tačke cosinusa (neprevedeno / slomljeno pismo / slomljena gramatika), deklarisane naspram stvarnih težina komponenti (8/92 umjesto 40/60), sistematsko kažnjavanje namjernog autorskog odstupanja (Abbott slučaj), sve iznad rečenice (prelom stiha, ilustracije), kontekst, poznata nepotpunost. **Tijelo EN-only** (svjestan izuzetak); meni i naslov ×5 jezika. Vlastiti scoped `<style>` blok — dijeljeni CSS netaknut. Nije u `CONCEPT_PAGES`. |
| `books.html` | Library | Kartice s lang badges i brojem prevedenih jezika; Word cloud radi za sve knjige (neprevedene prikazuju EN original); linkovi: Read, Gutenberg, NLP, Word cloud |
| `nlp.html` | Named Entities & Relations | TRI ravnopravna pogleda (s129): Classic \| With LLM \| DocRE. Entity Network graph (D3 force); DocRE mod = usmjeren graf (strelica+boja po klasi P/M/O, legenda, klik→opis+dokaz). Tri infoboxa (šta+kako, DocRE naglašava vlastitu implementaciju, i18n ×5). Named Entities lista + Original tekst s highlight/navigacijom. Word cloud uklonjen (s127). |
| `reader.html` | Čitač | Prima `?book=ID` URL param; X-Ray Full mod — paginacija po 25 rečenica, svih 5 kandidata s kompletnim scoreovima i back translationom |
| `learn.html` | Language Learning | Landing overview s 4 game kartice; 4 igre: Fill in the Blank (MC + tipkanje, hint lang za EN), Sentence Match, Memory (trunkiranje 80 znakova), Scrambled (Hold to Peek hint) |
| `geometry.html` | Geometry of Meaning | D3 UMAP scatter embeddinga (EN+HR+SR+IT+DE), grid pozadina, D3 zoom (scaleExtent 1–12, reset dugme), Transformers.js cosine similarity, SVG angle vizualizacija s gridom (220×220), centriran rezultat, A/B corpus selektor; i18n ✅ (s82) |
| `art.html` | Art | Sinestezija teza (Abbott/Borges/Wittgenstein/Kandinski-Skrjabin lineage); The Tapestry — score heatmap (samo prevedene rečenice, tamni okvir, centriran zadnji red, apsolutna/relativna skala, model mode); Sentence Fingerprints |
| `buchenberg.css` | Shared CSS | Dark mode, navigacija, sve dijeljene komponente |

**Shared funkcionalnosti:**
- Dark mode toggle (☀️/🌙) — persista u `localStorage`
- UI jezik (EN/DE/IT/HR/SR) — persista u `localStorage`, dijeli se između stranica
- `books.html` → "Read" dugme otvara `reader.html?book={id}`

### Web how-to: i18n prevod i Key Concepts kartice

Dva mjesta gdje se najčešće zastaje — trajna referenca (raskriveno s108).

#### Višejezični UI prevod (i18n)

Tekst NIJE u HTML hardkodu — hardkod je samo **no-JS fallback**. Izvor istine je i18n rječnik u `nav.js`:
- **5 jezičkih blokova:** `en`, `de`, `it`, `hr`, `sr` (`LANG_LABELS = {en,de,it,hr,sr}`).
- **Ključevi po stranici, s prefiksom:** `index_*`, `about_*`, `geo_*`, `art_*`, …
- **Apply-kod je u samoj stranici** (`<page>.html`, inline `<script>`), NE u nav.js: `const x = t('kljuc'); if (x && x !== 'kljuc') document.getElementById('id').innerHTML = x;` (ili `.textContent`). Na **svakom** jeziku, uključujući EN, JS prepisuje hardkod rječničkom vrijednošću.

**Dodati/izmijeniti prevedeni tekst — checklist:**
1. Dodaj ključ u **svih 5** jezičkih blokova u `nav.js` (`index_novi:\`...\`,`).
2. Dodaj apply-liniju u `<page>.html` inline script: `t('novi')` → `getElementById('novi-id')`.
3. Element u HTML-u mora imati taj `id`.

> Preskočiš (1) → tekst ostaje hardkod-EN na svim jezicima. Preskočiš (2) → rječnik se ne primjenjuje. Oba su tiha (bez greške).

#### Key Concepts kartice

- Fajl: `data/concepts.json`, grupisano **po stranici** (`index`, `about`, `geometry`, …).
- Kartica: `{icon, name, description, wiki}`. `name` **kratko** (bez zagrada); `wiki` **pun slug** s zagradama (npr. `Mutation_(evolutionary_algorithm)`, `Attention_(machine_learning)`).
- Link se auto-gradi: `https://en.wikipedia.org/wiki/{wiki}`. Fetch s `?t=Date.now()` (cache-bust).
- **Pravilo: samo članci koji STVARNO postoje na engleskoj Wikipediji** (odluka). Ako pojam nema wiki članak (npr. self-refinement), kartica se NE dodaje — pojam se može spomenuti u `description` srodne kartice.
- Poslije izmjene **validiraj JSON** (`json.load`) — slomljen JSON ruši sve Key Concepts kartice.

### Struktura direktorijuma

```
/home/balsam/buchenberg/
├── .env                     # secrets — nije u git!
├── README.md
├── src/
│   └── bb_*.py              # bb pipeline skripte
├── books/                   # HTML knjige — nije u git!
├── docs/
│   └── sessions/            # session_NN.md dokumenti
├── logs/                    # nije u git!
├── output/                  # export prevoda — nije u git!
└── venv/                    # nije u git!
```

---

## 11. Performanse (referentne vrijednosti)

| Operacija | Trajanje |
|-----------|---------|
| `bb_03_prevod.py` — gemma3, 100 rec, 1 jezik | ~5 min |
| `bb_03_prevod.py` — ministral, 100 rec, 1 jezik | ~4 min |
| `bb_03_prevod.py` — nllb, 100 rec, 1 jezik | ~5–10 min |
| `bb_03_prevod.py` — gemma3, 350 rec, 1 jezik | ~22 min |
| `bb_03_prevod.py` — gemma3, 100 rec, 2 jezika (--temp lista) | ~15 min |
| `bb_08_sudija.py` — 100 rec, 1 jezik (500 ocjena) | ~5 min |
| `bb_08_sudija.py` — 350 rec, 1 jezik | ~14 min |
| Cloud ukupno (5 modela, 350 rec, 1 jezik) | ~70 min |
| e5-large encoding | ~15 rec/sec |

---

## 12. Protokol rada

### Inicijalizacija svake sesije (obavezno)

```bash
# 0. Project knowledge / docs reference (prije README; s121 dodatak)
cat docs/KONCEPT.md docs/ANALIZA.md docs/KAKO-JeziciUI.md docs/KAKO-KeyConcepts.md docs/KAKO-BrisanjePrevoda.md docs/KAKO-NovaFaza.md docs/STRANICE.md
ls docs/ | grep -i "^WEB-FAZA"   # provjeriti ima li novijeg nacrta (npr. WEB-FAZA3.md)

# 1. README
cat /home/balsam/buchenberg/README.md

# 2. Posljednja 3 session dokumenta
ls docs/sessions/  # naći posljednja 3
cat docs/sessions/session_NN.md ...

# 3. Health check
cd /home/balsam/buchenberg && venv/bin/python src/health_check.py
```

### Protokol komandi

**Claude uvijek prikazuje komandu prije izvršavanja. Bez izuzetka.**  
Flavio kaže OK → tek onda se izvršava.  
Važi za: `foxuno:run_command`, `balsam:run_command`, git operacije, izmjene fajlova.

**Ko pokreće pipeline:** Prevođenje i refine pokreće isključivo Flavio, prema
raspoloživim resursima i potrebi za poređenjem performansi/kvaliteta. Claude ne
planira niti pokreće pipeline runove. (s121)

### Dokumentacija

Svaka sesija završava:
1. `session_NN.md` — artefakt u chatu → Flavio OK → save na server
2. README update ako je potrebno
3. Bump `BB_VERSION` i `BB_VERSION_DATE` u `/var/www/buchenberg/nav.js`
4. `git add -A && git commit -m "..." && git push`

---

## 13. Poznati bugovi (riješeni)

| Bug | Sesija | Fix |
|-----|--------|-----|
| `bb_04_pobjednik.py` DELETE bez range filtera brisao sve pobjednike za jezik | 38 | DELETE sada filtrira po opsegu |
| Ollama Cloud retry nedostajao | 38 | 3 pokušaja, 30s čekanje |
| `bb_knjige.gutenberg_id` bez UNIQUE constrainta — dupli insert prolazio tiho | 41 | `ALTER TABLE bb_knjige ADD CONSTRAINT bb_knjige_gutenberg_id_unique UNIQUE (gutenberg_id)` |

| Orphan pobjednici u `bb_prev_recenica` — FK bez CASCADE — 11 redova pokazivalo na nepostojeće `bb_prevodi_recenica` | 54 | `DELETE FROM bb_prev_recenica WHERE prevodi_recenica_id NOT IN (SELECT id FROM bb_prevodi_recenica)` — obrisano 11 orphana; `ON DELETE CASCADE` odgođeno |
| Base64 za prenos tekstualnog sadržaja na foxuno — nepouzdan za duže stringove | 119 | Uvijek heredoc `cat > file << 'EOF' ... EOF`, nikad base64 za tekstualni sadržaj |

---

## 14. Sljedeći koraci

### Gated root (s155 dizajn, s156 bug ispravljen, s157 otkriven race condition, s158 riješeno — deklarisani svjetovi, s159 batch/timeout nalaz, s160 oporavak nakon pada)
Cilj: sužen root (mistral+nllb, glm isključen) -> sudija -> pobjednik -> gate
(prag 0,95, postojeći mehanizam) -> nova self-refine faza 10 (glm, BASE
prompt, bez pivota) -> sudija -> pobjednik (argmax preko cijelog bazena).
Motiv: Ollama Cloud glm-5.2 nesrazmjerno troši sedmični budžet (vidi s155
snapshot, §9) — cilj je ograničiti glm na uslovni drugi korak umjesto stalnog
baznog konkurenta.

> ✅ **s158 RIJEŠENO:** `run_root_gated.sh` više NE toggle-uje `bb_faze_a1`
> automatski — Korak 1 (toggle off) i `trap`-cleanup (toggle on) uklonjeni iz
> skripte. Umjesto toga: ulazak/rad/izlazak je ručan, protokolom-vođen čin
> (prikaži→OK→izvrši), potpuno odvojen od skripte — vidi
> `docs/KAKO-NovaFaza.md` §"Protokol za gated root". Skripta se sad smije
> pozivati paralelno po jeziku dok je svijet ručno postavljen. Vidi
> `docs/sessions/session_157.md` (nalaz) i `docs/sessions/session_158.md`
> (rješenje).

> ✅ **s160 — oporavak nakon pada usred prevođenja, dokumentovan i testiran:**
> `bb_03_prevod.py` nema top-level try/except; ako i batch I single-fallback
> potroše sva 3 pokušaja, proces umire neuhvaćen (traceback), gubeći sve
> nezapisano u tom chunk-u I sve naredne batch-eve/jezike u istom pozivu.
> Bash wrapperi (`set -e` bez `set -o pipefail`, cijev na `tee`) zato **tiho
> nastavljaju** na Sudiju/Pobjednika — POZNATA, NEPOPRAVLJENA rupa.
> **Oporavak ne treba novu logiku** — `already_done()`+prag (faze≥2) već
> ispravno određuju šta nedostaje; prosto ponovi ISTU komandu. Novi flag
> `--uradi-ako-nema` (bool, čisto label u logu, ne mijenja logiku) dodat u
> `bb_03_prevod.py`/`run_faza.sh`/`run_root_gated.sh` da označi namjeran
> nastavak. Testirano na stvarnom k12 (Moby Dick) incidentu (3.avg, de
> glm@0.1 pukao usred `run_root_gated.sh` na batch 18/19) — rerun 4.avg
> dovršio sve stvarno nedostajuće (21 nova de rečenica), a 7 de rečenica je
> ISPRAVNO ostalo bez glm@0.1 jer je glm@0.8 sam već prešao prag 0,95 prije
> oporavka (dinamičko prera-čunavanje praga — namjerno ponašanje, ne bug,
> vidi `docs/KAKO-NovaFaza.md` §"Oporavak nakon pada"). hr/it/sr nisu trebali
> oporavak (glm@0.1 već potpun od 3.avg uveče). ⚠️ Otvoreno: session_159.md
> je za isti raspon (9001-9800) prijavio 2 potpuna neuspjeha za IT — stvarni
> log (`gated_k12_it_9001_9800.log`) ne pokazuje nijedan Traceback i završava
> čisto istog dana bez ijednog reda dodanog 4.avg. Neusklađeno, nije dalje
> istraženo — mogući uzrok: log je prepisan (`>`, ne `>>`) naknadnim ručnim
> rerunom prije kraja s159, ili je s159-ov nalaz bio netačan. Detalji:
> `docs/sessions/session_160.md`.

**s155 bug (grananje `elif is_refine:` zavisilo SAMO od broja faze, ne od
prompta — glm dobijao seed uprkos BASE promptu) ISPRAVLJEN u s156:**
`elif is_refine and PROMPT_NAZIV != 'base':`. Verifikovano DVA PUTA na
svježim opsezima (k22 741-780 i 781-820, de/hr/it/sr) — `prompt: base`
potvrđen u logu, glm pobjeđuje 84% i 92,6% kad gate otvori (u skladu sa
s145/s146/s154 istorijskim rasponom 79-93%), gate stopa 15,6%/16,9%
(niže od s146/s154 28-29%, normalna varijacija na uzorku od 40 rečenica).

**Infrastruktura (s156, prerađena s158):** `src/bb_deklarisi_svet.py` (novo
s158 — deklariše CIJELO stanje a1/a2 za fazu, ne relativni toggle) +
imenovane skripte `bb_svet_1.sh` (puna 3-way root) / `bb_svet_2.sh` (sužen
root bez glm), svaka potpuna izjava namjere, nezavisna od prethodnog stanja
+ `run_root_gated.sh` (s158: pokreće SAMO root+gated fazu, pretpostavlja da
je svijet već aktiviran — auto-toggle uklonjen). `src/bb_toggle_model.py`
(s156) ostaje kao ad-hoc alat za pojedinačni model, van standardnog toka.
Dva KAKO dokumenta: `docs/KAKO-BrisanjePrevoda.md` (FK-svjestan redoslijed
brisanja prevoda), `docs/KAKO-NovaFaza.md` (prošireno §7, uključujući
gated-fazu obrazac, s156 bug/fix, i s158 deklarisani svjetovi).

Ollama Cloud "Weekly usage" screenshot (s156, Flavio): glm segment trake
potrošnje vizuelno najveći uprkos NAJMANJE zahtjeva (4.780 naspram gemma
24.360, mistral 5.568) — vizuelna potvrda cijene-po-pozivu nalaza iz s155.

Otvoreno za ponedjeljak (sedmični Ollama reset ~02:00): odluka o usvajanju u
produkciju, pravo testiranje na većem obimu, provjera da li k22 501-700
(faza 9, s154) treba isti tretman kao 701-740 (koje je s156 potpuno
obrisala i ponovo čisto testirala), formalna dopuna KONCEPT.md ako se
usvoji. Detalji: `docs/sessions/session_156.md`.

### Zamjena modela — IZVRŠENO (s114): mistral-large-3:675b + glm-5.2 u produkciji
**Refaktor + zamjena izvršeni i testirani kroz cijeli lanac (session_114.md). Korak 4 (web) ZAVRŠEN s120 (Faza 1 priprema s115-118, Faza 2 implementacija s120, svih 9 stranica) — vidi §9 s120 snapshot.** Istorijat odluke ispod.
**Drugi retirement talas (5. jul, kompletna Ollama lista) povukao i gemma3:27b i ministral-3:8b — prva s112 odluka nevažeća.** Novi par kroz sandbox sondu (6 kandidata, 2 kruga): **mistral-large-3:675b + glm-5.2** (oba ne-misleća/gase thinking, temp-živa, 10–13 tok, različite familije). Rezerve: deepseek-v4-flash (temp-mrtav), kimi-k2.6. Zamjena i refaktor idu zajedno ("jedan dah"), prije 15. jula — po principima iz `docs/KONCEPT.md` i mapi iz `docs/sessions/session_112.md` (koraci: backup → shema → skripte → test → web; puna lista povučenih + sonda u dodacima s112). Istorijat starog testa ispod.
Test na Dracula/bs (42 rečenice, swap-dizajn A/B/C): prosjek finalni_score stari>novi u obje porodice (gemma3 0.9085 vs 0.8742; ministral 0.8500 vs 0.8346), ali uparen t-test slab (t≈1.23/0.70, n=42) — statistički neodlučivo. Head-to-head skoro 50/50. Nedovoljno za odluku u bilo kom smjeru. Sljedeće: veći uzorak (100+ rečenica) ili ponavljanje na drugoj knjizi prije 15. jula, istim receptom (`bb_08_sudija1.py`, swap A/B/C). Poslije odluke: pravi refaktor `OCJENJIVANI_MODELI` → kolona u `bb_modeli`. Kompletna mapa svih pogođenih skripti i tabela (nezavisno od finalnog izbora modela) — vidi `docs/sessions/session_111.md` (s111).

### Self-refine — NEGATIVAN nalaz starog para (s100), REVIDIRAN novim parom (s134), REDIZAJNIRAN gated fazama (s144)

**s100 (stari par, gemma3/ministral):** hipoteza — pobjednik kao hint poboljšava prevod. **Rezultat: ne radi na jakim seedovima.** J&H hr s1-100: head-to-head vs svoj seed = **0/100** (avg delta −0,076). Win-rate 36/100 bio je artefakt selekcije iz šireg bazena — head-to-head otkrio konfaund. Uzrok: seed je već pobjednik od 5 modela (blizu plafona), "popravi ovo" perturbuje optimalni anchor → regresija. Detalji: `docs/sessions/session_100.md`.

**s134 (novi par, mistral-large-3 + glm-5.2; k22/23/24 × de/hr/it/sr × 1–20, n=240):**

| mjera | s100 (stari par) | s134 (novi par) |
|---|---|---|
| head-to-head vs seed | **0/100** | **60/240 = 25,0 %** (40 izjednačeno, 140 gore) |
| win-rate (apsolutni) | 36/100 | 72/240 = 30,0 % (baseline 2/7 = **28,6 %**) |

**Refine više nije mrtav, ali agregatno i dalje gubi** (win-rate ≈ slučajni baseline).

**Ključni nalaz — headroom gradijent (izmjeren, ne pretpostavljen):** refine dobija tamo gdje seed ima prostora, gubi gdje je seed blizu plafona.
- k23 Big Four Copy — **najslabiji seedovi, jedina knjiga s pozitivnom deltom na sva 4 jezika**. k23/sr: seed 0,9267 → delta **+0,0178**, 11/20 pobjeda. k23/it: seed 0,9535 → **+0,0226**.
- k24 Frankenstein Copy — **najjači seedovi**: k24/de seed 0,9777 → −0,0093, **2/20**. k24/it → 1/20.

To potvrđuje s100-ovu dijagnozu (plafon), ali je pretvara u **kontinuum umjesto presude**.

> ⚠️ **Metodološka ograda (Flavio, s134):** ispravna formulacija nije *"refine kvari jak prevod"* nego **"naš sudija i embedder ne vide poboljšanje na jakom seedu"**. Ocjenjivač je jedina mjera koju imamo i mjeri sam sebe. Blizu plafona i "poboljšanje" i "kvarenje" gube sadržaj. Pravi zadatak: **izmjeriti gdje sudija prestaje da razlikuje** i tu povući granicu poboljšavanja — umjesto pretpostavljati da razlikuje.

**RIJEŠENO (s135):** no-op refine sumnja iz s134 POTVRĐENA i ISPRAVLJENA. SQL provjera (seed=faza-1 pobjednik JOIN najbolji faza-2 kandidat po rečenici) pokazala **39/40 "izjednačenih" slučajeva su bukvalno identičan tekst** kao seed, ne koincidencija scorea (samo 1/40 stvarna slučajnost). Uzrok: `bb_03_prevod.py :: prevedi_refine_single()` prompt sadržavao "Keep the reference only if it is already optimal." — eksplicitna dozvola LLM-u da vrati klon. Live test (3 kratke rečenice/naslova, izvan baze) potvrdio uzrok i pokazao trade-off: agresivnija zabrana ("do NOT repeat verbatim") rješava 0/3 klona ALI rizikuje promjenu ZNAČENJA na kratkim/trivijalnim rečenicama ("Frankenstein;"→"Čudovište Frankensteina"). Flaviova odluka (izbjegavanje scope-creepa): minimalna izmjena — samo uklonjena "keep if optimal" rečenica, bez dodate eksplicitne zabrane. Primijenjeno u kodu, necommitovano do kraja s135. Detalji: `docs/sessions/session_135.md`.

Otvoreno i dalje: (a) selektivni re-translate na SLABIM seedovima (prag <0,85) — s134 pokazuje da je to najizgledniji režim; (b) refaktor `OCJENJIVANI_MODELI` → kolona `grupa` u bb_modeli; (c) novi horizont (s135): NER+relacije kao kontekst-injection za refine kvalitet — zaseban budući session. **s137 napredak:** batch-refine implementiran i mehanički testiran (`REFINE_BATCH_SIZE=5`, vidi §9 s137) — head-to-head 16.75% na produkcionom testu, nije kontrolisano razdvojeno od batch-efekta. NER-kao-kontekst prvi tehnički test urađen (standalone, van produkcionog koda) — mehanizam radi, ali čisto-NER (bez seeda) nije samostalno pouzdano upravljao ti/vi formalnošću; otvoreno je li seed potreban uz NER kontekst kao hibridni pristup. **s138 ZATVARA nit (kontekst-injection za kvalitet prevoda):** prošireno i na sažetak-kao-kontekst (deepseek-v4-pro brief + Gutenberg sažetak). GLAVNI NALAZ — signal ispod šuma: ista rečenica preokrenula ti/vi izbor između dva prolaza istog prompta na temp 0.8 (varijacija poziva > razlika promptova). Plus: NER daje strukturu ne registar; cilj sam nejasan ("prijatelji→ti" nije univerzalno — viktorijanski registar formalan). ODLUKA: kontekst-injection za kvalitet prevoda ZATVOREN (i NER i sažetak). Ako se vrati, treba drugačiji režim (niža temp / deterministički), ne prompt-na-temp-0.8. Vidi §9 s138 + session_138.md.

**Nastavak (s141-147) — arhitektura redizajnirana, Dio B preokrenut:**

s141-142 (Dio A): faza redefinisana kao kombinacija tri nezavisne ose — a1=model
(`bb_modeli`), a2=temperatura (`bb_temperature`), a3=prompt (`bb_promptovi`) —
vidi §7 "Kako dodati novi model i temperaturu" i `docs/PLAN-KONFIGURACIJA.md`.

**s144 — DIO B PREOKRENUT:** plan za random selekciju (fitness-proportionate
izbor a1/a2/a3, GA-stil mutacija/anti-elitizam, dizajniran s139-143) je NAPUŠTEN.
Uzrok: ta mašinerija ima smisla samo za ogroman prostor pretrage, a stvarni
katalog ima samo 6 kombinacija (2 modela × 3 prompta × 1 temperatura). Pravo
pitanje reformulisano iz "koju kombinaciju izabrati" u "da li uopšte pokušati
refine na OVOJ rečenici" — headroom gate. Zamjena: **tri fiksne gated faze**
(`refine-gated`=4, `refine-lenient-gated`=5, `refine-strict-gated`=6), prag
`seed_score<0.95` (svaka rečenica ispod praga ulazi u refine pokušaj; iznad
praga se preskače — direktna implementacija s134 headroom-gradijent nalaza kao
ugrađeni filter, ne naknadna dijagnoza). Svaka gated faza gleda TRENUTNOG
apsolutnog pobjednika (ne originalni faza-1 seed) — samo-sužavajući lijevak.

**s145:** bootstrap bug u `run_faza.sh` STVARNO popravljen (fallback na katalog
`bb_faze_a1`×`bb_faze_a2` kad je istorija prazna — vidi §7 upozorenje). "Runda"
dizajn (alternativa klon-triku za ponovno pokretanje iste konfiguracije,
`bb_prevodi_knjige.runda` u UNIQUE) razrađen i testiran DDL migracijom, tada
ODLOŽEN.

**s146:** gated refine potvrđen na širem uzorku (Dracula+Flatland, 8.000
rečenica) — gate otvoren 29,2%, gated refine pobjeđuje 93,4% kad otvoren, delta
+0,047, klon-stopa 0,7%. Isti session je proizveo AUDIT MJERNOG APARATA
(`docs/ANALIZA.md`) direktno relevantan za čitanje refine rezultata: sudija
nosi ~92% finalnog scorea, ne deklarisanih 60%; sudija kažnjava namjernu
autorsku devijaciju (Flatland de primjer, +0,157 delta za brisanje autorove
složenice).

**s147:** permutacijski eksperiment (6 blokova × 6 permutacija faza 4/5/6) —
POZICIJA u lancu ima jasan monoton efekat na stopu otvaranja gate-a
(21,0%→13,9%→11,3% kroz 1./2./3. korak); KONKRETNA faza (4 vs 5 vs 6) ima slab,
nekonzistentan efekat kontrolisano za poziciju. "Runda" IMPLEMENTIRANA
kraj-do-kraja (kolona + UNIQUE + `--runda` flag) — seed-lock mehanizam (za
izolaciju efekta redoslijeda od sadržaja rečenica) dizajniran, NEIMPLEMENTIRAN.

Otvorene stavke (a)/(b) iz gornjeg pasusa (selektivni re-translate na slabim
seedovima; refaktor `OCJENJIVANI_MODELI`) su superseded s144 gated-fazama i
s142 tro-osnom arhitekturom — ne prate se više odvojeno.

Detalji: `docs/sessions/session_141.md` – `session_147.md`, `docs/PLAN-KONFIGURACIJA.md`.


### Performanse — NLLB CTranslate2 int8 — URAĐENO (s93)
NLLB radi kroz **CTranslate2 int8** (CPU), default. ~6–7× brže od FP32 na Neoverse-N1 (ARM); NLLB više nije usko grlo lanca.
- **Motor:** `NLLB_ENGINE` env — `ct2` (default) ili `fp32` (fallback). Params: `NLLB_CT2_DIR`, `NLLB_CT2_BATCH=200`, `NLLB_CT2_MAXBATCH=14`, `NLLB_CT2_INTER=4`, `NLLB_CT2_INTRA=1`.
- **Upotreba:** `run_pipeline.sh` nepromijenjen (default ct2, automatski brz). Stari put: `NLLB_ENGINE=fp32 bash ./run_pipeline.sh ...`.
- **Model:** `models/nllb-600M-ct2-int8/` (594 MB, gitignored). Regeneracija: `ct2-transformers-converter --model facebook/nllb-200-distilled-600M --quantization int8 --output_dir models/nllb-600M-ct2-int8`.
- **Drift:** int8 mijenja ~50% izlaza kozmetički (red riječi/sinonimi, jednak kvalitet); NLLB je 1 od 5 kandidata, deterministički (greedy). Detalji: `docs/sessions/session_93.md`.
- **Preostalo opciono:** length bucketing (besplatno, nula drifta) — sad manje hitno.

### Performanse — DB optimizacija health_check — URAĐENO (s97)
`health_check.py` "Stanje prevoda" query bio usko grlo: **7:02 elapsed, 5% CPU** (čeka bazu, ne računa). Dijagnoza `time` + `EXPLAIN`: ne CPU, ne promet, ne autovacuum — **loš oblik upita**.
- **Uzrok:** fan-out — prevodi (`pr`) × pobjednici (`po`) po knjiga×jezik grupi u istom SELECT-u → ~750M redova (`EXPLAIN`: `rows=753.023.732`). `COUNT(DISTINCT)` postojao da poništi taj double-counting. Klasičan anti-pattern.
- **Popravka:** razdvojene agregacije — `prev` CTE (`COUNT(DISTINCT recenica_id)`) i `pobj` CTE (goli `COUNT(*)`, nema fan-outa), spojene `LEFT JOIN` po knjiga×jezik. Bez sheme, bez indeksa.
- **Rezultat:** query 7min → **1.26s** (~335×); cijeli health check **7:02 → 0:23**, CPU 5% → 88%. `diff` stari vs novi izlaz **bit-identičan** (126 redova).
- **Lekcija (prvi SQL-tuning slučaj projekta):** 90% loših DB performansi = korisnički SQL. `time` (wall-clock vs CPU%) je prva dijagnoza: 5% = čeka I/O, 88% = računa. Fan-out + `COUNT(DISTINCT)` = signal za razdvajanje agregacija.
- **Preostalo opciono:** `work_mem` bump (prev-sort sad 15MB na disk → RAM, <1s).

### Performanse — stats.html DB-side agregacija — URAĐENO (s99)
`stats.html` je serijski fetchao **126 `tr_*.json` (~165 MB)** i 4× petljao kroz sve u browseru (dizajn iz prve verzije s par jezika; sad 803k redova). Stranici trebaju samo agregati (~par KB) — browser je vukao 165 MB da izračuna par KB.
- **Popravka:** `bb_web_export.py:get_stats()` — 4 `GROUP BY` (summary, winner-dist, coverage, score-by-lang) nad zajedničkim JOIN lancem + `bb_knjige`; generiše `data/stats.json`. `stats.html:loadStats()` čita **1 fajl** umjesto 126, mapira na iste `_winnerRows/_coverageRows/_scoreRows` (render netaknut). + loading state + ojačan error catch.
- **Rezultat:** **165 MB → 14.6 KB** (~11.000×), 126 fetch → 1. SQL <0.5s po agregatu (mjereno `\timing`). Stranica učitava trenutno (bilo: sekunde praznine).
- **Lekcija:** isti X-Ray obrazac kao s97 — pomakni posao gdje je jeftin. Mjeri prije izbora rješenja (`du -ch tr_*.json` = 165 MB dao dijagnozu jednim potezom).
- **Preostalo opciono:** isti pattern provjeriti u nlp.html backendu; `stats_loading` i18n ključ (sad fallback "Loading…").

### Web portal
1. ✅ **Favicon** (s95) — Flatland heksagon, light/high-contrast (crno na sivom); `favicon.svg` + link kroz nav.js (`document.write`, svih 9 stranica). Footer tagline: `Buchenberg · an X-Ray project · open-source MT pipeline`.
2. ✅ **MT Lab identitet** (s96) — `<title>Buchenberg — MT lab</title>` + `.bb-hero-lab` red "Machine Translation Lab" ispod home loga (Xpong RL Lab paralela, nepreveden EN).
3. ✅ **Home hero ikona** (s96) — heksagon `favicon.svg` (64×64) lijevo od loga; `.bb-hero-logo` flex-centriran.
4. ✅ **X-Ray Key Concepts kartice** (s96, dodano) → **OBRISANE s120** (Flaviova odluka): 🩻 X-ray style art + 🎸 Rock Art and the X-Ray Style uklonjene sa index/about/stats (`data/concepts.json`). "Key Concepts" naslov se i dalje ne prevodi.
5. **`bb_web_export.py`** — refaktorisati da koristi `v_pobjednici_full`/`v_pobjednici_faza_full` view (POKUŠANO s148, VRAĆENO — cross-view JOIN dva `_full` view-a tjera pun sequential scan; sljedeći pokušaj treba materijalizovan view ili indeks, ne direktan LEFT JOIN. Vidi §9 s148 snapshot)
6. ✅ **Stats dvije tabele + fazni pobjednik** — KOMPLETNO (s123, vidi §9 s123 snapshot)
3. **Cache-Control za JS/CSS**

### Odloženo / u razmatranju
- **NLP — Relation Extraction** (s90 koncept, "leži"): tretirati kao summarization-klasu problema, ne co-occurrence. Grounding-by-evidence kao princip; provjera kroz embedding kosinus (ne LLM tumačenje). Ideja: **rasplet detektivskog romana kao ulaz** — autorov vlastiti opis relacija na kraju knjige kao upit + semantička pretraga unazad za potkrepu; daje i zlatni standard za evaluaciju. Žanrovski uslovljeno (Hound, Big Four imaju rasplet). Detalji: `docs/sessions/session_90.md`.

### Završeno (s90)
- ✅ **Key Concepts proširenje** — svih 9 stranica (index, about, geometry, art, nlp, stats, learn, reader, books); books → Wikipedia link po knjizi; `concepts.json` sad pod gitom (izuzet iz `.gitignore`)
- ✅ **SR ekavica fix** — sve stranice (reader nema SR teksta)
- ✅ **X-Ray JSON export** — `bb_xray_export.py` pokrenut za sve knjige × jezike (126 JSON fajlova)
- ✅ **learn.html i18n — statični UI** (s85); **runtime JS + preostali statični labeli** (s125, propust otvoren s120, sad potpuno zatvoren)

---

## 15. Ollama Cloud API — how-to (raskriveno s109)

Mjesta gdje uvijek zapnemo pri radu s Ollamom. Trajna referenca.

### Autentikacija — ključ iz koda, ne ručno
`.env` sadrži `OLLAMA_API_KEY` i `OLLAMA_BASE_URL`. Skripta MORA sama učitati:
```python
from dotenv import load_dotenv
load_dotenv()   # prije svakog os.getenv("OLLAMA_API_KEY")
```
> ⚠️ Bez `load_dotenv()` ključ je prazan → **401 Unauthorized na SVE modele** (i one koji rade). Simptom prevari — izgleda kao da model ne radi, a problem je prazan ključ. (Bug s109.)
> Za ručni curl: `. /home/balsam/buchenberg/.env &&` PRIJE poziva (`source` ne radi u sh, koristi `.`).

### Poziv (chat) — isti obrazac kao bb_03 ollama_chat
```bash
. /home/balsam/buchenberg/.env && curl -s https://api.ollama.com/api/chat \
  -H "Authorization: Bearer $OLLAMA_API_KEY" \
  -d '{"model":"MODEL","stream":false,"options":{"temperature":0.1},
       "messages":[{"role":"user","content":"..."}]}'
```
Prevod je u `message.content`. `stream:false` obavezno (inače NDJSON striming).

### Detalji modela — /api/show (veličina, kvant, kontekst, capabilities)
```bash
. /home/balsam/buchenberg/.env && curl -s https://api.ollama.com/api/show \
  -H "Authorization: Bearer $OLLAMA_API_KEY" -d '{"model":"MODEL"}'
```
Vraća `details.parameter_size`, `quantization_level`, `model_info.<fam>.context_length`, `capabilities` (npr. `thinking`, `vision`, `tools`). Tako se veličina/tip PROVJERAVA, ne pretpostavlja.

### Thinking modeli — presudno za trošak
Neki modeli (capability `thinking`: gpt-oss, nemotron, deepseek, glm, qwen3.5…) generišu reasoning.
- Ollama ga stavlja u ODVOJEN `message.thinking` field — `message.content` ostaje čist prevod. **Pipeline (`ollama_chat` čita samo content) radi bez izmjene.**
- ALI thinking troši tokene: gpt-oss:20b ~250, nemotron:30b ~900 vs etaloni ~12 po prevodu. **Thinking, ne veličina, je glavni množilac troška/vremena.**
- `"think": false` u telu zahtjeva GASI reasoning — ali **poštuje se po modelu**: nemotron sluša (907→10 tok), gpt-oss ignoriše (ostaje zaglavljen). Provjeri sondom, ne pretpostavljaj.
- Gašenje thinkinga može sniziti kvalitet (nemotron bez thinkinga → slabiji prevod). Trade-off mjeri sudija.

### Prije usvajanja novog modela — pusti sondu
`venv/bin/python src/sandbox_model_probe.py --models "MODEL" --jezik hr`
Mjeri ponašanje (čistoća/thinking/trošak/batch/round-trip) naspram etalona. Kvalitet ide zasebno kroz pravi `bb_03`+`bb_08` na malom opsegu. Registracija u `bb_modeli` (a1 katalog) + `bb_faze_a1`/`bb_faze_a2` izbor za ciljanu fazu (s142) je preduslov za pravi run.

### Radni ritam — očekivano opterećenje po dobu dana

Flaviovo subjektivno zapažanje (nepotvrđeno formalnom analizom, ali vrijedno zapisati): performanse prema Ollama Cloud primjetno degradiraju otprilike između 16 i 18h CET/CEST (Vienna) vremena. Vjerovatno objašnjenje: Ollama ima servere u US i EU, a Flaviova infrastruktura i radni ritam su evropski — očekivano je da se poklapa sa regionalnim peak opterećenjem. Ovo nije laboratorijsko okruženje s garantovanim resursima; varijacija u rečenica/min (vidi `docs/RUNOVI.md`) je normalna, ne signal greške.

**Ažurirano s151 (24. jul 2026):** formalna analiza (24 loga, k20 Dracula, `docs/RUNOVI.md`) NIJE potvrdila degradaciju 16-18h CEST — naprotiv, period ~19-22h CEST bio je dosljedno najbrži u analiziranom setu (do 2.27× brže od popodnevnih batch-eva, isti dan, isti setup). `sar`/`sysstat` provjera VPS-a (Frankfurt, Oracle Cloud) pokazala zanemarljiv %steal (0.03-0.04%) — isključuje kontenciju sa drugim tenantima. Vjerovatan dominantan faktor: opterećenje na Ollama Cloud strani (sudija gemma4:31b pokazao 6.1× varijaciju). Stara pretpostavka ostaje iznad kao istorijski kontekst.

---

*Dokument će biti ažuriran sa svakom novom verzijom. Uvek čitaj samo poslednju verziju.*  
*Flavio & Claude · Buchenberg · V3 · 4. avgust 2026. (sesija 160)*
