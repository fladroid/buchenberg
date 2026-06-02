# Buchenberg — Project Documentation V2

**Datum kreiranja:** 14. maj 2026.  
**Poslednje ažuriranje:** 2. jun 2026. (sesija 38)  
**Autor:** fladroid  
**Status:** Aktivan razvoj — test pipeline operativan, GA implementiran

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

Isti postupak se radi sa više metoda prevoda. Metoda sa višim score-om **pobeđuje** za tu rečenicu. Krajnji rezultat je hibridni prevod koji kombinuje najbolje od svake metode.

### Genetski algoritam za optimizaciju

Za žute i crvene rečenice (translation_score < 0.90) pokreće se **Genetski algoritam (GA)** koji evoluira populaciju prevoda koristeći pivot jezike kao crossover operator:

```
EN → pivot jezik (npr. HR) → ciljni jezik (IT)
```

Svaki jezik vidi originalnu misao kroz drugačiju prizmu — crossover generiše semantički raznolike kandidate.

### Cilj projekta

Prevod knjiga sa isteklom licencom sa **Project Gutenberg** na više jezika, koristeći isključivo open source i besplatne alate.

**Važna napomena:** *Važniji je put od cilja.* Pipeline koji gradimo je generički i primenljiv daleko šire od samog prevoda knjiga.

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

## 3. Metode prevoda

| Method string | Engine | Parametri | Napomena |
|---------------|--------|-----------|---------|
| `nllb` | NLLB-200 lokalno | beam search, deterministički | Najprecizniji za direktni prevod |
| `nllb_t05` | NLLB-200 lokalno | do_sample=True, temp=0.5 | Stohastičan, raznolikiji |
| `gemma` | Gemma 3 12b cloud | default temperatura | Brz, dobar za kompleksne rečenice |
| `gemma_t05` | Gemma 3 12b cloud | temperature=0.5 | Konzervativniji od default |
| `ministral` | Ministral 3 14b cloud | default temperatura | Jak na evropskim jezicima |
| `ministral_t05` | Ministral 3 14b cloud | temperature=0.5 | Konzervativniji od default |
| `gemma4` | Gemma 4 31b cloud | default temperatura | Veliki model, sporiji |
| `gemma4_t05` | Gemma 4 31b cloud | temperature=0.5 | Konzervativniji od default |
| `claude` | Claude Sonnet 4.6 | temperature=1.0 | Anthropic API, književni stil |
| `claude_t05` | Claude Sonnet 4.6 | temperature=0.5 | Konzervativniji, preporučeni |
| `claude_literal` | Claude Sonnet 4.6 | temperature=1.0 | Doslovan prevod, čuva strukturu |
| `claude_literal_t05` | Claude Sonnet 4.6 | temperature=0.5 | Doslovan + konzervativniji |

**Standard:** svaki jezik u svakom testu uvijek ima sve 6 metoda (gemma, gemma_t05, ministral, ministral_t05, nllb, nllb_t05).

### Kako dodati novu metodu

Samo 4 mjesta u `run_test.py`:
1. `VALID_METHODS` — dodati string
2. `dispatch_translate()` — dodati `elif`
3. `dispatch_back_translate()` — dodati `elif`
4. Batch blokovi u `main()` — dodati `elif` za translate i back_translate batch

Baza ne treba migraciju — `method` je `VARCHAR(20)`. Napomena: proširen sa VARCHAR(10) na VARCHAR(20) zbog `ministral_t05` (13 znakova).

---

## 4. Arhitektura pipeline-a

### Faze

```
Faza 1 (run20.sh) — gemma+gemma_t05+ministral+ministral_t05 za SVE rečenice:
  EN rečenice → gemma, gemma_t05, ministral, ministral_t05 → RF + RFE + score + translation_score → test_results

Faza 2 (run20.sh) — ministral+ministral_t05 za ŽUTE+CRVENE:
  Filtar: --score_to 0.8999 (per jezik!)
  Žute+crvene → ministral, ministral_t05 → test_results

Faza 3 (run20.sh) — nllb+nllb_t05 za CRVENE:
  Filtar: --score_to 0.7999 (per jezik!)
  Crvene → nllb, nllb_t05 → test_results

GA (run30.sh) — optimizacija žutih+crvenih:
  Žute + crvene → GA evoluira populaciju → pobjednik → ga_results
  ga_save_winners.py → pobjednici → test_results (method='ga_<pivot>')
```

**Važno:** `--score_to` filter radi per `(test_id, target_lang)` — ne miješa scoreove različitih jezika.

**Ponavljanje faza:** Faze 1, 2 i 3 mogu se ponavljati više puta na istom testu. `ON CONFLICT WHERE` garantuje da `translation_score` može samo rasti — nikad pasti. Svako ponavljanje je sigurno i može donijeti poboljšanje zbog stohastičnosti modela.

### Pokretanje pipeline-a po fazama

```bash
# Faza 1 — sve rečenice, svi LLM modeli
bash run20.sh --test_id test_018 --sent_from 1 --sent_to 40 \
  --langs it --methods gemma gemma_t05 ministral ministral_t05 > logs/test_018_f1.log 2>&1

# Faza 2 — žute+crvene, ministral
bash run20.sh --test_id test_018 --sent_from 1 --sent_to 40 \
  --langs it --methods ministral ministral_t05 --score_to 0.8999 > logs/test_018_f2.log 2>&1

# Faza 3 — crvene, nllb
bash run20.sh --test_id test_018 --sent_from 1 --sent_to 40 \
  --langs it --methods nllb nllb_t05 --score_to 0.7999 > logs/test_018_f3.log 2>&1

# GA — žute+crvene
bash run30.sh --test_id test_018 --sent_from 1 --sent_to 40 --lang it > logs/test_018_ga_it.log 2>&1

# Upis GA pobjednika
venv/bin/python src/ga_save_winners.py --test_id test_018 --lang it
```

### Paralelni pipeline

Gemma (cloud) i NLLB (lokalni CPU) ne dijele resurse:

```bash
# Paralelno — 2x ubrzanje
nohup venv/bin/python src/run_test.py --test_id test_001 \
  --batch_size 20 --methods gemma gemma_t05 > logs/par_gemma.log 2>&1 &

nohup venv/bin/python src/run_test.py --test_id test_001 \
  --batch_size 20 --methods nllb nllb_t05 > logs/par_nllb.log 2>&1 &
```

### Batch processing

```bash
# Default batch_size=20, može se povećati na 50
bash run20.sh --test_id test_001 --batch_size 20
```

Gemma batch: numerisana lista → jedan API poziv → JSON array
NLLB batch: `tokenizer(texts, padding=True)` → `batch_decode`

**Ubrzanje vs single mode: ~6x**

> ⚠️ **Batch fallback pattern (obavezno):** Svaka skripta s batch API pozivima mora imati fallback na single mode. Uzrok većine padova: rečenice s1–s3 su metadata (naslov, autor, poglavlje) — modeli ih spajaju i vraćaju 19/20 separatora. Pattern iz `run_test.py` i `run_translations.py`:
> ```python
> parts = translate_batch(...)
> if parts is None:
>     parts = [translate_single(text) for text in chunk]
> ```

### Grupiranje rečenica

- 🟢 **Zelene** (translation_score ≥ 0.90) — preskačemo GA
- 🟡 **Žute** (0.80–0.89) — GA optimizacija
- 🔴 **Crvene** (< 0.80) — GA optimizacija (prioritet)

---

## 5. Genetski algoritam (GA)

### Konceptualni okvir

**Populacija:** 4 inicijalna prevoda (po jedan za svaku metodu)
**Fitness:** `translation_score` = cosine(RE, RF) — MiniLM-L12
**Crossover:** EN → nasumični pivot jezik → ciljni jezik
**Mutacija:** individua.tekst → nasumični pivot → ciljni jezik
**Selekcija:** elitizam (top 2) + raznolikost (odbaci duplikate cosine > 0.99)

### Parametri

| Parametar | Default | Opis |
|-----------|---------|------|
| `--pop_size` | 8 | Maksimalna veličina populacije |
| `--elite_n` | 2 | Uvijek preživljava N najboljih |
| `--max_gen` | 20 | Maksimalan broj generacija |
| `--conv_thresh` | 0.005 | Prag konvergencije |
| `--conv_gens` | 3 | Generacija bez poboljšanja → stop |
| `--quality_stop` | 0.95 | Fitness > ovo → stop |
| `--mutate_rate` | 0.15 | Stopa mutacije (15%) |
| `--green_thresh` | 0.90 | Zelene → preskači GA |

### Pokretanje GA

```bash
# Snapshot prije GA
venv/bin/python src/ga_snapshot.py --lang it

# GA za žute/crvene rečenice
bash run30.sh --test_id test_018 --sent_from 1 --sent_to 40 --lang it

# Sa custom parametrima
bash run30.sh --test_id test_018 --sent_from 1 --sent_to 40 --lang it --max_gen 10 --conv_gens 5
```

---

## 6. Tehnički stack

### Translation engines

| Engine | Lokacija | Napomena |
|--------|----------|---------|
| **NLLB-200-distilled-600M** | Lokalno na foxuno (~2.5GB keš) | CPU-bound, ~22-30 rec/min |
| **Gemma 3 12b** | Ollama Cloud (`api.ollama.com`) | GPU cloud, ~53-55 rec/min |
| **Ministral 3 14b** | Ollama Cloud (`api.ollama.com`) | GPU cloud, jak na evropskim jezicima |

> ⚠️ LLM modeli se **ne nalaze** na foxuno niti balsam. Koristi se Ollama Cloud.

### Embeddings

| Model | Dim | Jezici | Brzina | `--embedder` | Napomena |
|-------|-----|--------|--------|-------------|---------|
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 50+ | **41 rec/sec** | `minilm` (default) | Brz, pristran prema doslovnosti |
| `intfloat/multilingual-e5-large` | 1024 | 100+ | ~15 rec/sec | `e5` | **Produkcijski embedder.** Thresholdovi: 🟢≥0.93 🟡0.88-0.92 🔴<0.88. MiniLM je pristran prema doslovnosti — e5 daje realnu sliku. |
| `cointegrated/SONAR_200_text_encoder` | 1024 | 202 | ~8 rec/sec | `sonar` | Pravi cross-lingual, strog |
| `LaBSE` | 768 | 109 | 12 rec/sec | — | Testiran, nije u upotrebi |

**Izbor embeddera:** `--embedder e5` preporučeno za produkciju. MiniLM favorizuje doslovne prevode (NLLB), SONAR je previše strog za zeleno/žuto/crveno sistem s trenutnim thresholdima.

### NLP
- **spaCy** + `en_core_web_sm` — sentence splitting i NER
- **NLTK** + VADER lexicon — sentiment analiza

### Baza podataka
- **PostgreSQL 17.9** + **pgvector 0.8.2**

### Ostalo
- **Python 3.12.3** u virtualenv-u
- **loguru** — logging
- **python-dotenv** — konfiguracija
- **beautifulsoup4** — parsiranje HTML

---

## 7. Shema baze podataka

### Tabele

| Tabela | Opis |
|--------|------|
| `books` | Knjige (naslov, autor, gutenberg_id) |
| `sentences` | Rečenice (text, book_id, position) |
| `test_results` | Prevodi + scores |
| `ga_results` | GA historija generacija |

### `test_results` (ključna tabela)

```sql
CREATE TABLE test_results (
    id                SERIAL PRIMARY KEY,
    test_id           VARCHAR(20) NOT NULL,
    sentence_id       INTEGER REFERENCES sentences(id),
    target_lang       CHAR(2) NOT NULL,
    method            VARCHAR(20) NOT NULL,
    translated_text   TEXT,
    back_translation  TEXT,
    score             REAL,           -- cosine(RE, RFE)
    translation_score REAL,           -- cosine(RE, RF) direktni
    winner            BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMP DEFAULT NOW(),
    UNIQUE (test_id, sentence_id, target_lang, method)
);
```

### `ga_results`

```sql
CREATE TABLE ga_results (
    id            SERIAL PRIMARY KEY,
    sentence_id   INTEGER REFERENCES sentences(id),
    target_lang   CHAR(2) NOT NULL,
    generation    INTEGER NOT NULL,
    individua_id  INTEGER NOT NULL,
    tekst         TEXT NOT NULL,
    fitness       REAL NOT NULL,
    pivot_lang    CHAR(2),
    metoda        VARCHAR(20),
    je_elita      BOOLEAN DEFAULT FALSE,
    je_pobjednik  BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT NOW()
);
```

---

### `translations` (centralna tabela prevoda)

```sql
CREATE TABLE translations (
    id            SERIAL PRIMARY KEY,
    sentence_id   INTEGER REFERENCES sentences(id),
    book_id       INTEGER REFERENCES books(id),
    target_lang   CHAR(2)      NOT NULL,
    model         VARCHAR(30)  NOT NULL,
    temperature   REAL         NOT NULL,
    translation   TEXT,
    created_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE (sentence_id, target_lang, model, temperature)
);
```

**Trenutni sadržaj:** 4480 redova — 14 jezika × 4 modela × 2 temperature × 40 rečenica.  
**Modeli:** `gemma3:12b`, `ministral-3:14b`, `gemma4:31b`, `nllb-600M`  
**Temperature:** 0.1 (deterministički) i 0.5 (stohastički)  
**Namjena:** Jednom prevesti, slobodno evaluirati — bez stalnog pozivanja Ollame.

---

## 8. Skripte

### Run skripte

| Skripta | Opis | Komanda |
|---------|------|---------|
| `run10.sh` | Punjenje baze | `bash run10.sh` |
| `run15.sh` | Sentiment + NER | `bash run15.sh` |
| `run20.sh` | Prevod — test runner | `bash run20.sh --test_id test_001 --batch_size 20` |
| `run30.sh` | GA optimizer | `bash run30.sh --test_id test_018 --sent_from 1 --sent_to 40 --lang it` |

### Python skripte (`src/`)

| Skripta | Opis |
|---------|------|
| `step1_create_tables.py` | Kreira tabele |
| `step2_truncate.py` | Reset podataka |
| `step3_insert_book.py` | Ubacuje knjige |
| `step4_parse_sentences.py` | Parsira HTML → rečenice |
| `step5_sentiment_ner.py` | VADER sentiment + spaCy NER |
| `step6_create_test_table.py` | Kreira `test_results` tabelu |
| `step7_create_ga_table.py` | Kreira `ga_results` tabelu |
| `run_test.py` | Glavni test runner (batch, scoring) |
| `run_translations.py` | Punjenje tabele `translations` — batch prevod s fallback na single |
| `run_ga.py` | GA runner |
| `ga_snapshot.py` | Snapshot zelene/žute/crvene |
| `count_colors.py` | Broji rečenice po boji za dati test |
| `health_check.py` | Infrastrukturna provjera svih komponenti |
| `ram_monitor.sh` | Monitor RAM/swap tokom runa |
| `run_embeddings.py` | Punjenje sentence_embeddings + translation_embeddings |
| `run_pivot.py` | Cross-lingual hint pivot za poboljšanje prevoda (log only) |
| `run_context.py` | Kontekstualni prevod — prozor 3 rečenice za žute/crvene (log only) |
| `run_deepl.py` | DeepL prevod za crvene rečenice (log only) |

---

## 9. Environment i infrastruktura

### Serveri

| Server | Adresa | Uloga |
|--------|--------|-------|
| **foxuno** | `foxuno.dynu.net` | Jedini razvojni server |
| **balsam** | `balsam.dynu.net` | Docker host — PostgreSQL |

> ⚠️ Sav razvoj je na **foxuno**. User se zove `balsam` ali to je user na foxuno serveru!
> ⚠️ `docker exec pgdb psql` komande Claude izvršava direktno putem `balsam:run_command`.

### Struktura direktorijuma

```
/home/balsam/buchenberg/
├── .env                     # secrets — nije u git!
├── README.md
├── run10.sh / run15.sh / run20.sh / run30.sh
├── buch_env.sh
├── venv/                    # nije u git!
├── src/
├── tests/
│   └── test_registry.yaml   # jedini izvor istine za testove
├── docs/
│   ├── ga_readme.md
│   └── sessions/
├── logs/                    # nije u git!
└── books/                   # nije u git!
```

### `test_registry.yaml` format

```yaml
test_001:
  book: hound_of_the_baskervilles
  sent_from: 1
  sent_to: 40
  langs: [hr, sr, de, nl, fr, it]
  methods: [nllb, nllb_t05, gemma, gemma_t05]

test_018:
  book: hound_of_the_baskervilles
  sent_from: 1
  sent_to: 40
  langs: [it]
  methods: [gemma, gemma_t05, ministral, ministral_t05, nllb, nllb_t05]
```

---

## 10. Knjige (testni korpus)

| Knjiga | Autor | Rečenica |
|--------|-------|----------|
| The Hound of the Baskervilles | Arthur Conan Doyle | 3.852 |
| Frankenstein | Mary Wollstonecraft Shelley | 3.384 |
| Poirot Investigates | Agatha Christie | 4.857 |
| **Ukupno** | | **12.093** |

---

## 11. Korisne komande

### PostgreSQL (Claude izvršava putem balsam:run_command)

```bash
docker exec pgdb psql -U pgu -d buchenberg
docker exec pgdb psql -U pgu -d buchenberg -c "TRUNCATE test_results RESTART IDENTITY;"
docker exec pgdb psql -U pgu -d buchenberg -c "TRUNCATE ga_results RESTART IDENTITY;"
```

### Provjera stanja testa

```bash
# Broj boja po jeziku
venv/bin/python src/count_colors.py --test_id test_018 --sent_from 1 --sent_to 40 --langs it

# Infrastrukturna provjera
venv/bin/python src/health_check.py
```

### GA workflow

```bash
venv/bin/python src/ga_snapshot.py --lang it
bash run30.sh --test_id test_018 --sent_from 1 --sent_to 40 --lang it
venv/bin/python src/ga_save_winners.py --test_id test_018 --lang it
```

---

## 12. Performanse (referentne vrijednosti)

| Operacija | Trajanje |
|-----------|---------|
| Faza 1 (40 rec, 4 LLM metode, 1 jezik) | ~2 min |
| Faza 1 (40 rec, 4 LLM metode, 6 jezika) | ~15 min |
| Faza 2 (žute+crvene, 1 jezik) | ~45 sec |
| Faza 3 (crvene, NLLB, 1 jezik) | ~40 sec |
| GA (1 rečenica) | ~1.5 min |
| MiniLM encoding | 41 rec/sec |
| `run_translations.py` (40 rec, 4 modela, 2 temp, 1 jezik) | ~5 min |
| `run_translations.py` (14 jezika serijski) | ~70 min |
| e5-large encoding | ~15 rec/sec (4520 vektora = 12:34 min) |
| SONAR encoding | ~8 rec/sec |

---

## 13. Protokol dokumentacije

1. Claude generiše artifakt
2. Flavio pregleda i kaže OK
3. Na server i GitHub tek nakon OK

**Protokol komandi:** Claude uvijek prikazuje komandu prije izvršavanja. Bez izuzetka.

---

## 14. Sledeći koraci

1. ~~Punjenje baze~~ ✅
2. ~~NER + sentiment~~ ✅
3. ~~Test pipeline (run20)~~ ✅
4. ~~Batch processing~~ ✅
5. ~~GA implementacija~~ ✅
6. ~~Paralelni pipeline~~ ✅
7. ~~GA tuning prvi krug~~ ✅ (conv_gens=6, conv_thresh=0.002)
8. ~~Ministral kao treća LLM metoda~~ ✅
9. ~~Parser fix~~ ✅ — parser refaktor, uklonjen placeholder trik, 0 fallbacka
10. ~~**ON CONFLICT WHERE fix**~~ ✅ — score može samo rasti, nikad pasti
11. ~~**Uklonjen clear_test poziv**~~ ✅ — faze se mogu bezbijedno ponavljati
12. **GA pobjednici kao `method = 'ga'`** — upisati u test_results
13. **GA tuning drugi krug** — crossover_rate, max_children, varijabilni potomci
14. ~~**multilingual-e5-large**~~ ✅ — testiran, preporučen kao produkcijski embedder (`--embedder e5`)
15. **Novi jezici** — bs, sl, mk, af, es, ro
16. **Pipeline orchestrator** — spaja sve zajedno
17. ~~**Tabela `translations`**~~ ✅ — 4480 prevoda, 14 jezika, potpuna
18. **Evaluacija iz tabele `translations`** — metoda koja ne poziva Ollamu
19. **DeepL integracija** — kao peta metoda prevoda u `translations`
20. ~~**Metadata rečenice fix**~~ — s1-s3 tretirati posebno (naslov/autor/poglavlje)
21. ~~**e5-large vektori**~~ ✅ — 4520 vektora (40 EN + 4480 prevoda), 12:34 min
22. **color_summary VIEW rekalibracija** — thresholdovi za e5: 🟢≥0.93, 🟡0.88-0.92, 🔴<0.88
23. **Pipeline orchestrator** — finalni prijevod iz best_translation VIEW-a
24. **COMET-QE** — neuralni QE model bez referentnog prijevoda
25. **Referentni prijevod** — HR prijevod "Psa Baskervillevih" za gold-standard evaluaciju
26. **Batch commits** u `run_embeddings.py` — otpornost na crash (commit svakih 500 redova)
27. ~~**umap-learn instaliran**~~ ✅ — u venv, UMAP redukcija 1024D→2D operativna
28. **`src/export_umap.py`** — skripta za UMAP export (trenutno samo u artifaktu)
29. **Book X-Ray skaliranje** — e5 vektori za cijeli Hound (3852 rečenica)
30. **Višeknjižna vizualizacija** — Hound + Frankenstein + Poirot na istom UMAP platnu
31. **Cellular automaton** — rečenice kao ćelije, semantička sličnost kao pravilo interakcije
32. **HTTPS Book X-Ray** — web stranica koja servira vizualizaciju za svaku knjigu

---

*Dokument će biti ažuriran sa svakom novom verzijom. Uvek čitaj samo poslednju verziju.*
*Flavio & Claude · Buchenberg · V2 · 2. jun 2026.*

---

## 15. bb pipeline (novi minimalistički pipeline)

### Filozofija

Povratak na osnovu (sesija 34): čista shema, nova baza `bb`, bez GA, bez NLP enrichmenta. Jedina metrika kvaliteta je cosinus sličnost + LLM sudija.

### Baza `bb` — tabele

| Tabela | Opis |
|--------|------|
| `bb_jezik` | 14 jezika |
| `bb_modeli` | 9 modela (gemma3, ministral, nllb, claude, gemma4 × temperature) |
| `bb_embeddings` | 2 embeddera (MiniLM, e5-large) |
| `bb_knjige` | Knjige |
| `bb_recenice` | Rečenice (pozicija, tekst) |
| `bb_prevodi_knjige` | UNIQUE(knjiga, jezik, model, embedder) |
| `bb_prevodi_recenica` | Prevod + back_translation + score + translation_score + prevod_vektor + naturalness_score + sudija ocjene |
| `bb_prev_knjige` | Finalni prevod knjige UNIQUE(knjiga, jezik) |
| `bb_prev_recenica` | FK na pobjednika u bb_prevodi_recenica |
| `bb_rag_korpus` | RAG korpus (150k rečenica, hr/it/de, e5-large vektori) |

### Skripte (`src/bb_*.py`)

| Skripta | Opis |
|---------|------|
| `bb_01_init_lookup.py` | Puni bb_jezik, bb_modeli, bb_embeddings |
| `bb_02_insert_knjiga.py` | Ubacuje knjigu i parsira rečenice (spaCy) |
| `bb_03_prevod.py` | Prevod + back-translation + cosine score (batch+fallback); podržava Ollama Cloud i NLLB |
| `bb_04_pobjednik.py` | Bira pobjednika po kompozitnom scoreu `(score + translation_score) / 2`, tiebreak abecedni |
| `bb_05_export.py` | Export finalnog prevoda u `output/naziv_knjige_lang.txt` |
| `bb_06_enkodiranje.py` | Enkodira prevode → upisuje `prevod_vektor` u bb_prevodi_recenica |
| `bb_07_rag_score.py` | k-NN upit u bb_rag_korpus → `naturalness_score` (odgođeno — pogrešan korpus) |
| `bb_08_sudija.py` | Gemma4:31b kao blind sudija → `sudija_grammar/naturalness/fidelity/avg` |
| `bb_rag_init.py` | Stream-download OPUS OpenSubtitles + enkodiranje → bb_rag_korpus |
| `bb_calc_translation_score.py` | UPDATE translation_score za postojeće redove |

### Metrike kvaliteta

| Metrika | Formula | Opis |
|---------|---------|------|
| `score` | cosine(EN, back_EN) | Informacijska stabilnost kroz back-translation |
| `translation_score` | cosine(EN, prevod) | Direktna semantička blizina originalu |
| `kompozitni` | (score + translation_score) / 2 | Trenutni kriterij pobjednika |
| `naturalness_score` | avg cosine(prevod, k-NN u RAG korpusu) | Prirodnost u ciljnom jeziku — odgođeno |
| `sudija_avg` | (grammar + naturalness + fidelity) / 3 | LLM blind evaluacija — ključna metrika |

### Modeli u bb pipeline-u

| Model | Uloga |
|-------|-------|
| gemma3:12b | Prevođenje |
| ministral-3:14b | Prevođenje |
| nllb-600M | Prevođenje |
| gemma4:31b | Sudija (ne prevodi) |

### Pokretanje bb pipeline-a

```bash
# 1. Prevođenje (Ollama Cloud)
venv/bin/python src/bb_03_prevod.py --knjiga 1 --od 1 --do 40 \
    --model "gemma3:12b" --embedder "multilingual-e5-large" --jezici hr it

# 2. Prevođenje (NLLB lokalno)
venv/bin/python src/bb_03_prevod.py --knjiga 1 --od 1 --do 40 \
    --model "nllb-600M" --embedder "multilingual-e5-large" --jezici hr it

# 3. Enkodiranje prevoda
venv/bin/python src/bb_06_enkodiranje.py --embedder "multilingual-e5-large"

# 4. Sudija evaluacija
venv/bin/python src/bb_08_sudija.py --knjiga 1 --od 1 --do 40 --jezici hr it

# 5. Izbor pobjednika
venv/bin/python src/bb_04_pobjednik.py --knjiga 1 --od 1 --do 40 --jezici hr it

# 6. Export
venv/bin/python src/bb_05_export.py --knjiga 1 --jezici hr it
```

### Ključni uvidi

- **NLLB kažnjen od sudije** — bukvalni prevodi imaju visok cosinus score ali nizak sudija_avg
- **gemma3 i ministral dominiraju** po sudija ocjeni, posebno za IT
- **Cosinus score i sudija su komplementarni** — treba kombinovati
- **temp=0.8 generalno bolji** od 0.5 i 0.1, ali nema univerzalne temperature — ovisi o jeziku i dijelu teksta
- **DE specifičnost** — jedini jezik gdje ministral vodi; IT jedini gdje temp=0.1 osvaja 50%+ rečenica

### Formula pobjednika (sesija 38)



Sudija nosi 60% težine. Fallback na samo kompozitni kada .

### Denormalizovani viewovi (sesija 38)



### Kako dodati novi jezik, model, temperaturu, embedder

**Novi jezik:**


**Novi model i temperatura:**

> ⚠️ Skripta traži model po naziv + temperatura kombinaciji. Ako temperatura nije u bazi — greška 

**Novi embedder:**

Dodati logiku učitavanja u .

### Poznati bugovi (riješeni)

- ** DELETE bug** (sesija 38) — DELETE bez range filtera brisao sve pobjednike za jezik. Fix: DELETE sada filtrira po .
- ** retry** (sesija 38) — Ollama Cloud nestabilan. Dodata retry logika: 3 pokušaja, 30s čekanje.

