# Buchenberg — Project Documentation V3

**Datum kreiranja:** 14. maj 2026.  
**Poslednje ažuriranje:** 11. jul 2026. (sesija 127)  
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

**Ollama Cloud nalog je Pro tier (nadograđeno s free) — paralelni pozivi su podržani.** Najmanje posljednje dvije sedmice (od otprilike sredine/kraja juna 2026) svi pipeline runovi — i sa starim i sa novim modelima — redovno trče paralelno; sa starim (jeftinijim) modelima Flavio je često pokretao i 5 paralelnih tokova odjednom. Eksperiment s118/s119 (4 paralelne grupe) izmjerio je ~3.77× agregatno ubrzanje sa 4 paralelna toka naspram jednog solo. NLLB (lokalni CPU) i dalje radi nezavisno paralelno s bilo kojim cloud tokom.

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

> ⚠️ **s114:** modeli se čitaju iz baze (aktivni po fazi, helper `bb_aktivni_modeli.py`) — kanonski put je `run_pipeline.sh` / `run_refine.sh`. `bb_03` prima `--faza N` (default 1; 2+ = refine), `--refine` flag NE POSTOJI. Primjeri ispod su istorijski obrazac direktnog poziva — imena modela zamijeni aktivnima.

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

## 5. Baza podataka — bb shema

### Tabele

| Tabela | Opis |
|--------|------|
| `bb_jezik` | 14 jezika |
| `bb_modeli` | Modeli × temperature × faza; `aktivan` boolean; UNIQUE(naziv, temperatura, faza_id) — s114 |
| `bb_embeddings` | Embedder definicije |
| `bb_knjige` | Knjige (naziv, autor, gutenberg_id UNIQUE) |
| `bb_recenice` | Rečenice (pozicija, tekst, knjiga_id) |
| `bb_prevodi_knjige` | UNIQUE(knjiga, jezik, model, embedder) |
| `bb_prevodi_recenica` | Prevod + back_translation + score + translation_score + prevod_vektor + sudija ocjene |
| `bb_prev_knjige` | Finalni prevod knjige UNIQUE(knjiga, jezik) |
| `bb_prev_recenica` | FK na ukupnog pobjednika u bb_prevodi_recenica |
| `bb_prev_recenica_faza` | Fazni pobjednik po (rečenica, faza) — UNIQUE(prev_knjige, prevodi_recenica, faza). Puni ga bb_04 (faza-blok, DELETE+INSERT po opsegu, od s106). |
| `bb_model_registar` | Registar modela po IMENU (naziv PK, vrsta, uloge TEXT[]) — s123. Vrsta/uloga = identitet imena (ne instance); uloge 1:N. Uzak registar, bb_modeli nedirnut. Bez DEFAULT. Hrani stats Tabelu 0. |
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
| `bb_aktivni_modeli.py` | Ispisuje aktivne modele zadane faze (`naziv\|temp` linije) — DB izvor za run_pipeline.sh i run_refine.sh (s114) |
| `bb_09_ner.py` | NER pipeline: spaCy ekstrakcija + Gemma4 normalizacija + upis u bb_ner_entiteti/bb_ner_recenica |
| `bb_geometry_export.py` | Generira `data/geometry.json` — UMAP 2D projekcija EN+HR+SR+IT+DE embeddinga za geometry.html; pokreće se ručno (~380s) |
| `bb_web_export.py` | Generira JSON fajlove za Apache2 web prikaz (books, orig, tr, ner, version). NER: get_ner/get_ner_veze primaju `method` param; ner_<id>.json = `{classic, llm?}` (llm grana samo ako knjiga ima llm sloj) — s127 |
| `bb_sr_cirilica.py` | Transliterira srpske prevode latinica → ćirilica (idempotentna) |
| `bb_10_ner_llm.py` | LLM NER (glm-5.2): type reconciliation konfliktnih entiteta s groundingom dokaznim rečenicama; upis method='llm' paralelno uz classic (s126). Kompletira llm sloj — kopira i nekonfliktne classic entitete kao čiste llm redove (s127). Relacije van rečenice = ostatak Dio 2. |
| `bb_xray_export.py` | Generira X-Ray JSON fajlove (`data/xray_<id>_<lang>.json`) — svih 5 kandidata po rečenici s kompletnim scoreovima; pokrenuti nakon `bb_web_export.py` |
| `health_check.py` | Infrastrukturna provjera svih komponenti; čita bb bazu |
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

### Kako dodati novi model i temperaturu

```sql
INSERT INTO bb_modeli (naziv, temperatura, faza_id) VALUES ('model:tag', 0.5, 1) ON CONFLICT DO NOTHING;
-- aktivan je DEFAULT true; deaktivacija: UPDATE bb_modeli SET aktivan=false WHERE id=N;
```

> ⚠️ `bb_03_prevod.py` traži model po trojci `naziv + temperatura + faza_id` (s114). Ako trojka nije u bazi — greška.
> ⚠️ Pri kopiranju `faza_id` iz postojećeg modela (`INSERT...SELECT...WHERE temperatura=X`) UVIJEK `ROUND(temperatura::numeric,4)=X` i u SELECT-izvoru — bez toga float precision tiho vraća `INSERT 0 0`, bez greške. Otkriveno s110.

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
| `books.html` | Library | Kartice s lang badges i brojem prevedenih jezika; Word cloud radi za sve knjige (neprevedene prikazuju EN original); linkovi: Read, Gutenberg, NLP, Word cloud |
| `nlp.html` | NLP analiza | Word cloud (EN original, NER bojanje) + Named Entities lista + Entity Network graph (D3 force, zoom, slider co-occurrence) + Original tekst s rednim brojevima, highlight (word-boundary match; PERSON=OR, ostali=AND) i navigacijom po pogocima (prev/next, only-highlighted) |
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
cat docs/KONCEPT.md docs/ANALIZA.md docs/KAKO-JeziciUI.md docs/KAKO-KeyConcepts.md docs/STRANICE.md
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

### Zamjena modela — IZVRŠENO (s114): mistral-large-3:675b + glm-5.2 u produkciji
**Refaktor + zamjena izvršeni i testirani kroz cijeli lanac (session_114.md). Korak 4 (web) ZAVRŠEN s120 (Faza 1 priprema s115-118, Faza 2 implementacija s120, svih 9 stranica) — vidi §9 s120 snapshot.** Istorijat odluke ispod.
**Drugi retirement talas (5. jul, kompletna Ollama lista) povukao i gemma3:27b i ministral-3:8b — prva s112 odluka nevažeća.** Novi par kroz sandbox sondu (6 kandidata, 2 kruga): **mistral-large-3:675b + glm-5.2** (oba ne-misleća/gase thinking, temp-živa, 10–13 tok, različite familije). Rezerve: deepseek-v4-flash (temp-mrtav), kimi-k2.6. Zamjena i refaktor idu zajedno ("jedan dah"), prije 15. jula — po principima iz `docs/KONCEPT.md` i mapi iz `docs/sessions/session_112.md` (koraci: backup → shema → skripte → test → web; puna lista povučenih + sonda u dodacima s112). Istorijat starog testa ispod.
Test na Dracula/bs (42 rečenice, swap-dizajn A/B/C): prosjek finalni_score stari>novi u obje porodice (gemma3 0.9085 vs 0.8742; ministral 0.8500 vs 0.8346), ali uparen t-test slab (t≈1.23/0.70, n=42) — statistički neodlučivo. Head-to-head skoro 50/50. Nedovoljno za odluku u bilo kom smjeru. Sljedeće: veći uzorak (100+ rečenica) ili ponavljanje na drugoj knjizi prije 15. jula, istim receptom (`bb_08_sudija1.py`, swap A/B/C). Poslije odluke: pravi refaktor `OCJENJIVANI_MODELI` → kolona u `bb_modeli`. Kompletna mapa svih pogođenih skripti i tabela (nezavisno od finalnog izbora modela) — vidi `docs/sessions/session_111.md` (s111).

### Self-refine eksperiment — NEGATIVAN nalaz (s100)
Hipoteza: dati pobjednika kao hint pri ponovnom prevodu (self-refine / MoA interakcija) poboljšava prevod. **Rezultat: ne radi na jakim seedovima.** Test J&H hr s1-100: refine head-to-head vs svoj seed = **0/100** (nikad bolji; avg delta -0.076). Win-rate 36/100 bio je artefakt selekcije iz šireg bazena, ne stvarno poboljšanje — head-to-head otkrio konfaund. Uzrok: seed je već pobjednik od 5 modela (blizu plafona), "popravi ovo" perturbuje optimalni anchor -> regresija. Infrastruktura (`bb_03 --refine`, `run_refine.sh`, pseudo-modeli `*-refine` id 12/13, `bb_08` fix) ostaje za buduće hipoteze. Detalji: `docs/sessions/session_100.md`.
Otvoreno: (a) selektivni re-translate na SLABIM seedovima (apsolutni prag <0.85, jedini netestiran režim); (b) refaktor `OCJENJIVANI_MODELI` -> kolona `grupa` u bb_modeli.


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
5. **`bb_web_export.py`** — refaktorisati da koristi `v_pobjednici` view
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
Mjeri ponašanje (čistoća/thinking/trošak/batch/round-trip) naspram etalona. Kvalitet ide zasebno kroz pravi `bb_03`+`bb_08` na malom opsegu. Registracija u `bb_modeli` (naziv+temperatura+faza_id) je preduslov za pravi run.

### Radni ritam — očekivano opterećenje po dobu dana

Flaviovo subjektivno zapažanje (nepotvrđeno formalnom analizom, ali vrijedno zapisati): performanse prema Ollama Cloud primjetno degradiraju otprilike između 16 i 18h CET/CEST (Vienna) vremena. Vjerovatno objašnjenje: Ollama ima servere u US i EU, a Flaviova infrastruktura i radni ritam su evropski — očekivano je da se poklapa sa regionalnim peak opterećenjem. Ovo nije laboratorijsko okruženje s garantovanim resursima; varijacija u rečenica/min (vidi `docs/RUNOVI.md`) je normalna, ne signal greške.

---

*Dokument će biti ažuriran sa svakom novom verzijom. Uvek čitaj samo poslednju verziju.*  
*Flavio & Claude · Buchenberg · V3 · 11. jul 2026. (sesija 127)*
