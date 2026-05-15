# Buchenberg — Project Documentation V1

**Datum kreiranja:** 14. maj 2026.
**Poslednje ažuriranje:** 15. maj 2026. (sesija 04)
**Autor:** fladroid
**Status:** run10 završen — 12.093 rečenica u bazi

---

## 1. Filozofija i osnovna ideja

### Poreklo ideje

Projekat je nastao iz eksperimentisanja sa **embeddingima i vektorskom aritmetikom**. Centralna spoznaja bila je da se semantičko značenje rečenica može predstaviti kao vektori u višedimenzionalnom prostoru i da se između tih vektora može meriti sličnost (cosine similarity).

### Problem koji rešavamo

Kako proveriti kvalitet mašinskog prevoda kada ne govoriš ni izvorni ni ciljni jezik?

**Rešenje — back-translation pipeline:**

1. Uzmi rečenicu na jeziku **A** (original)
2. Prevedi je na jezik **B** → dobijamo prevod **B**
3. Prevedi **B** nazad na **A** → dobijamo **Ab** (back-translation)
4. Izračunaj cosine similarity između vektora **A** i **Ab**
5. Visok score = prevod je semantički ispravan

### Višestruko takmičenje metoda

Isti postupak se radi sa **najmanje 2 metode prevoda** (npr. NLLB i Gemma). Metoda sa višim cosine score-om **pobeđuje** za tu rečenicu. Krajnji rezultat je hibridni prevod koji kombinuje najbolje od svake metode.

### Engleski kao pivot jezik

Engleski je **centralni meta-jezik** sistema. Direktni prevodi između npr. srpskog i holandskog prolaze kroz engleski:

```
SR ← (EN) → NL
```

EN se ne prikazuje u finalnom outputu, ali služi kao most između jezika.

### Cilj projekta

Prevod knjiga sa isteklom licencom sa **Project Gutenberg** (gutenberg.org) na više jezika, koristeći isključivo **open source i besplatne alate** — dostupno svima, ne samo onima koji si mogu priuštiti komercijalne servise.

**Važna napomena filozofije projekta:** *Važniji je put od cilja.* Pipeline koji gradimo je generički i primenljiv daleko šire od samog prevoda knjiga.

---

## 2. Ciljni jezici

### Grupa 1 — Južnoslovenski
`hr` (hrvatski), `sr` (srpski), `bs` (bosanski), `sl` (slovenački), `mk` (makedonski), `bg` (bugarski)

### Grupa 2 — Zapadnogermanski
`de` (nemački), `nl` (holandski), `af` (afrikaans)

### Grupa 3 — Romanski/Latinski
`fr` (francuski), `it` (italijanski), `es` (španski), `pt` (portugalski), `ro` (rumunski)

---

## 3. Arhitektura pipeline-a

### Osnovna jedinica obrade: rečenica

Tekst knjige se **uvek deli na pojedinačne rečenice** pre prevoda. Razlog: blokovi rečenica su davali probleme sa poravnanjem. Rečenica-po-rečenica je jedina pouzdana jedinica.

### Poboljšanja za kratke rečenice

Kratke rečenice (naslovi, kratki dijalozi) dobijaju **kontekst** — u prompt ulazi i prethodna i sledeća rečenica. Ovo drastično poboljšava kvalitet prevoda kratkih fragmenta.

### Grupiranje rečenica

Rečenice se grupišu u **3 kategorije** po težini:
- 🟢 **Zelene** (score ≥ 0.90) — visok kvalitet
- 🟡 **Žute** (score 0.80–0.89) — srednji kvalitet
- 🔴 **Crvene** (score < 0.80) — nizak kvalitet, potrebna intervencija

### Mini-RAG poboljšanje

Za svaku rečenicu koja se prevodi, u prompt se ubacuju **3 primera uspešnih "zelenih" prevoda** iz iste knjige. Ovo je mini Retrieval-Augmented Generation koji modelu daje stil i kontekst.

### NER i Knowledge Graph

Vlastita imena i nazivi institucija se obrađuju posebno koristeći **spaCy NER** (Named Entity Recognition). Cilj je sprečiti pogrešan prevod npr. "Baker Street" ili "Scotland Yard".

---

## 4. Poznati problemi i planirana rešenja

| Problem | Uzrok | Planirano rešenje |
|---------|-------|-------------------|
| Kratke rečenice — vraća original | NLLB slab ispod ~5 tokena | Kontekst (prev+sledeća rečenica) |
| Naslovi — loši prevodi | Bez glagola, bez konteksta | HTML verzija knjige + posebna obrada |
| Mešana pisma (ćirilica/latinica) | Encoding problem | Eksplicitni language tag u promptu |
| Bukvalni prevod idioma visoko rangiran | Back-translation trap | Kalibracija metrike za idiome |
| NLLB truncation | `max_length` parametar | Eksplicitno postavljanje `max_length` |
| NLLB loop (prevod se ponavlja) | `repetition_penalty` | Podešavanje `repetition_penalty` |
| "Very truly yours" → "Imaš ga" | Idiom bez doslovnog prevoda | Posebna lista idioma + NER |

---

## 5. Tehnički stack

### Translation engines (VAŽNO)
- **NLLB** (No Language Left Behind — Meta) — Neural Machine Translation, instaliran u venv na foxuno
- **Gemma 3 12b** (`gemma3:12b`) — LLM via Ollama Cloud

> ⚠️ **Kritična napomena:** LLM modeli se **ne nalaze** na foxuno niti balsam serverima. Koristi se **Ollama Cloud** (`api.ollama.com`). Lokalni llama.cpp na foxuno je 10x sporiji i **ne koristi se** za prevod.

### Embeddings i evaluacija
- **sentence-transformers** — generisanje embedding vektora
- **sentencepiece** — tokenizer za NLLB (obavezan)
- **sacremoses** — tokenizer utilities za NLLB
- **pgvector** — čuvanje vektora u PostgreSQL
- **cosine similarity** — merenje kvaliteta prevoda

### NLP
- **spaCy** + `en_core_web_sm` — sentence splitting i NER
- **NLTK** + VADER lexicon — sentiment analiza

### Baza podataka
- **PostgreSQL 17.9** + **pgvector 0.8.2**

### Ostalo
- **Python 3.12.3** u virtualenv-u
- **loguru** — logging
- **tqdm** — progress bars
- **python-dotenv** — konfiguracija
- **beautifulsoup4** — parsiranje HTML

---

## 6. Environment i infrastruktura

### Serveri

| Server | Adresa | Uloga |
|--------|--------|-------|
| **foxuno** | `foxuno.dynu.net` | Jedini razvojni server — sav kod, venv, pipeline |
| **balsam** | `balsam.dynu.net` | Docker host — PostgreSQL kontejner |

> ⚠️ **Kritična napomena za buduće sesije:** Sav razvoj je na **foxuno**. Skripte, venv, knjige — sve je na `/home/balsam/buchenberg/` na foxuno serveru. User se zove `balsam` ali to je user na foxuno serveru, ne balsam server!

> ⚠️ **Kritična napomena — SQL izvršavanje:** `docker exec pgdb psql` komande se izvršavaju **ručno na balsam serveru**. Skripte na foxuno koriste **isključivo psycopg2** za konekciju na bazu (`host=balsam.dynu.net`). Na foxuno nema docker-a niti psql klijenta.

### Docker kontejneri (na balsam serveru)

| Kontejner | Servis | Detalji |
|-----------|--------|---------|
| `pgdb` | PostgreSQL 17.9 | user: `pgu`, baza: `buchenberg` |
| `pgad` | PostgreSQL (drugi) | ne koristi se za buchenberg |
| `ollama` | — | ne koristi se — Ollama je Cloud |
| `ntfy` | Notifikacije | ne koristi se za buchenberg |

### Ollama Cloud

| Parametar | Vrednost |
|-----------|---------|
| Base URL | `https://api.ollama.com` |
| Model | `gemma3:12b` |
| API Key | u `.env` fajlu |

Dostupni modeli na nalogu (relevantni):
- `gemma3:4b`, `gemma3:12b`, `gemma3:27b`
- `gemma4:31b`
- `mistral-large-3:675b`

### Struktura direktorijuma na foxuno

```
/home/balsam/buchenberg/
├── .env                  # secrets — nije u git!
├── .gitignore
├── requirements.txt
├── README.md             # uvek = poslednja verzija docs
├── run10.sh              # punjenje baze (tabele + knjige + rečenice)
├── venv/                 # Python virtualenv — nije u git!
├── src/                  # sav Python kod
│   ├── step1_create_tables.py
│   ├── step1_create_tables.sql   # referentni SQL — ne izvršava se direktno
│   ├── step2_truncate.py
│   ├── step2_truncate.sql        # referentni SQL — ne izvršava se direktno
│   ├── step3_insert_book.py
│   └── step4_parse_sentences.py
├── config/               # konfiguracioni fajlovi
├── logs/                 # logovi — nisu u git!
├── books/                # knjige — nisu u git!
│   ├── hound_of_the_baskervilles/raw/hound.html
│   ├── frankenstein/raw/frankenstein.html
│   └── poirot_investigates/raw/poirot_investigates.html
└── docs/
    ├── SESSION_LOG.md        # historija do sesije 02
    ├── db_schema.md          # shema baze podataka
    ├── parser_plan.md        # plan parsiranja HTML → sentences
    └── sessions/
        └── session_NN.md
```

### .env fajl (struktura)

```env
# Ollama Cloud
OLLAMA_API_KEY=<api_key>
OLLAMA_BASE_URL=https://api.ollama.com
OLLAMA_MODEL=gemma3:12b

# PostgreSQL
DB_HOST=balsam.dynu.net
DB_PORT=5432
DB_NAME=buchenberg
DB_USER=pgu
DB_PASSWORD=<password>
```

### Python paketi (requirements.txt)

```
psycopg2-binary       # PostgreSQL konekcija
python-dotenv         # .env učitavanje
spacy                 # sentence splitting, NER
sentence-transformers # embeddings
requests              # HTTP pozivi (Ollama Cloud)
tqdm                  # progress bars
loguru                # logging
pgvector              # pgvector Python adapter
beautifulsoup4        # parsiranje HTML
sentencepiece         # tokenizer za NLLB
sacremoses            # tokenizer utilities za NLLB
nltk                  # sentiment analiza (VADER)
```

---

## 7. Knjige (testni korpus)

| Knjiga | Autor | Gutenberg ID | Rečenica | Lokacija |
|--------|-------|-------------|----------|----------|
| The Hound of the Baskervilles | Arthur Conan Doyle | 3070 | 3.852 | `books/hound_of_the_baskervilles/raw/hound.html` |
| Frankenstein | Mary Wollstonecraft Shelley | 84 | 3.384 | `books/frankenstein/raw/frankenstein.html` |
| Poirot Investigates | Agatha Christie | 61262 | 4.857 | `books/poirot_investigates/raw/poirot_investigates.html` |
| **Ukupno** | | | **12.093** | |

Knjige su odabrane namjerno — pokrivaju cijeli spektar: kratke rečenice i brzi dijalozi (Poirot), dugi složeni blokovi (Frankenstein), sredina (Hound).

---

## 8. GitHub

| Parametar | Vrednost |
|-----------|---------|
| User | `fladroid` |
| Email | `fladroid@gmail.com` |
| Repo | `fladroid/buchenberg` |
| Branch | `main` |
| SSH key | `~/.ssh/id_ed25519` na foxuno |

### Korisne komande

```bash
# Provera SSH autentifikacije
ssh -T git@github.com

# Standardni commit i push
cd /home/balsam/buchenberg
git add .
git commit -m "opis izmena"
git push origin main
```

---

## 9. Korisne komande

### PostgreSQL — ručno na balsam serveru

```bash
# Lista baza
docker exec pgdb psql -U pgu -c "\l"

# Konekcija na buchenberg bazu
docker exec pgdb psql -U pgu -d buchenberg

# Prekid svih konekcija na bazu
docker exec pgdb psql -U pgu -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'buchenberg' AND pid <> pg_backend_pid();"

# Brisanje baze
docker exec pgdb psql -U pgu -c "DROP DATABASE buchenberg;"

# Kreiranje baze
docker exec pgdb psql -U pgu -c "CREATE DATABASE buchenberg OWNER pgu ENCODING 'UTF8' LC_COLLATE 'en_US.utf8' LC_CTYPE 'en_US.utf8';"

# Aktivacija pgvector ekstenzije
docker exec pgdb psql -U pgu -d buchenberg -c "CREATE EXTENSION vector;"
```

### PostgreSQL konekcija iz Pythona (izvršava se na foxuno)

```python
import psycopg2
conn = psycopg2.connect(
    host='balsam.dynu.net',
    port=5432,
    dbname='buchenberg',
    user='pgu',
    password='<password>'
)
```

### Pokretanje runova

```bash
cd /home/balsam/buchenberg

# run10 — punjenje baze (tabele + knjige + rečenice)
nohup time bash run10.sh > logs/run10.log 2>&1 &

# Praćenje loga
tail -f logs/run10.log
```

### Ollama Cloud test

```bash
curl -s -H "Authorization: Bearer <api_key>" https://api.ollama.com/api/tags
```

### venv

```bash
# Direktno pokretanje skripte
cd /home/balsam/buchenberg
venv/bin/python src/script.py

# Provjera instaliranih paketa
venv/bin/pip list
```

---

## 10. Protokol dokumentacije

Svaki dokument (README, session log, plan, shema) prolazi kroz:

1. **Generisanje** — Claude generiše artifakt
2. **Pregled** — Flavio pregleda i kaže OK ili daje primjedbe
3. **Server + GitHub** — tek nakon OK ide na server i git push

Bez izuzetaka.

---

## 11. Sledeći koraci

1. ~~**Download knjiga**~~ ✅ — 3 knjige, HTML format, Gutenberg
2. ~~**Shema baze**~~ ✅ — books, sentences, translations, embeddings, named_entities
3. ~~**Punjenje baze (run10)**~~ ✅ — 12.093 rečenica u bazi
4. ~~**buch_env.sh**~~ ✅ — kreiran, sourcuje se na početku svakog run skripte
5. ~~**run15.sh**~~ ✅ — 12.093 rečenica, 6.364 NER entiteta, ~6 min
6. ~~**NLLB instalacija**~~ ✅ — sentencepiece + sacremoses, facebook/nllb-200-distilled-600M
7. ~~**Test ciklus sistem**~~ ✅ — test_registry.yaml, test_results tabela, run_test.py, run20.sh
8. **Zapadnogermanski jezici** — de, nl, af
9. **Romanski jezici** — fr, it, es, pt, ro
10. **Analiza rezultata** — vizualizacija scores po jeziku i metodi
11. **Pipeline orchestrator** — spaja sve zajedno
8. **Evaluation modul** — embedding + cosine similarity
9. **Pipeline orchestrator** — spaja sve zajedno

---

*Dokument će biti ažuriran sa svakom novom verzijom. Uvek čitaj samo poslednju verziju.*
