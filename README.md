# Buchenberg — Project Documentation V3

**Datum kreiranja:** 14. maj 2026.  
**Poslednje ažuriranje:** 4. jun 2026. (sesija 44)  
**Autor:** fladroid  
**Status:** Aktivan razvoj — bb pipeline operativan, multi-knjiga, web prikaz

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

| Model | Engine | Temperatura | Napomena |
|-------|--------|-------------|---------|
| `gemma3:12b` | Ollama Cloud | 0.1 / 0.8 | Dominira za južnoslavenske i RO |
| `ministral-3:14b` | Ollama Cloud | 0.1 / 0.8 | Jak na germanskim i romanskim; jedini gdje DE dominira |
| `nllb-600M` | Lokalno (CPU) | 0.0 | Deterministički; dobar za kratke rečenice |
| `gemma4:31b` | Ollama Cloud | 0.0 | Samo sudija — ne prevodi |

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

**Ollama Cloud = jedna sesija u isto vrijeme.** Cloud skripte se izvršavaju **striktno serijski**. NLLB je lokalni CPU — može se pokrenuti paralelno s cloud skriptom ali ne i cloud s cloud.

---

## 4. bb pipeline — arhitektura

### Filozofija

Povratak na osnovu (sesija 34): čista shema, nova baza `bb`, bez GA, bez NLP enrichmenta. Jedina metrika kvaliteta je cosinus sličnost + LLM sudija.

### Faze pipeline-a

```
bb_03_prevod.py    → prevod + back-translation + cosine score (5 modela)
bb_08_sudija.py    → Gemma4 blind evaluacija (grammar/naturalness/fidelity)
bb_04_pobjednik.py → izbor pobjednika po finalnom scoreu
bb_05_export.py    → export u output/naziv_knjige_lang.txt
bb_web_export.py   → JSON export → Apache2 web prikaz
```

### Pokretanje — standardni workflow

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

# 5. Sudija
PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_08_sudija.py \
  --knjiga 1 --od 1 --do 100 --jezici hr \
  > logs/naziv_hr_sudija.log 2>&1 &

# 6. Pobjednici
venv/bin/python src/bb_04_pobjednik.py --knjiga 1 --od 1 --do 100 --jezici hr

# 7. Web export
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
| `bb_modeli` | Modeli × temperature |
| `bb_embeddings` | Embedder definicije |
| `bb_knjige` | Knjige (naziv, autor, gutenberg_id UNIQUE) |
| `bb_recenice` | Rečenice (pozicija, tekst, knjiga_id) |
| `bb_prevodi_knjige` | UNIQUE(knjiga, jezik, model, embedder) |
| `bb_prevodi_recenica` | Prevod + back_translation + score + translation_score + prevod_vektor + sudija ocjene |
| `bb_prev_knjige` | Finalni prevod knjige UNIQUE(knjiga, jezik) |
| `bb_prev_recenica` | FK na pobjednika u bb_prevodi_recenica |
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
| `bb_03_prevod.py` | Prevod + back-translation + cosine score (batch+fallback); Ollama Cloud i NLLB; `--temp` prima listu |
| `bb_04_pobjednik.py` | Bira pobjednika po finalnom scoreu; DELETE filtrira po opsegu |
| `bb_05_export.py` | Export finalnog prevoda u `output/naziv_knjige_lang.txt` |
| `bb_06_enkodiranje.py` | Enkodira prevode → upisuje `prevod_vektor` |
| `bb_08_sudija.py` | Gemma4:31b kao blind sudija → sudija_grammar/naturalness/fidelity/avg |
| `bb_web_export.py` | Generira JSON fajlove za Apache2 web prikaz |
| `bb_sr_cirilica.py` | Transliterira srpske prevode latinica → ćirilica (idempotentna) |
| `health_check.py` | Infrastrukturna provjera svih komponenti; čita bb bazu |

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
INSERT INTO bb_modeli (naziv, temperatura) VALUES ('model:tag', 0.5) ON CONFLICT DO NOTHING;
```

> ⚠️ `bb_03_prevod.py` traži model po `naziv + temperatura` kombinaciji. Ako kombinacija nije u bazi — greška.

---

## 8. Knjige (bb korpus)

| ID | Knjiga | Autor | Gutenberg ID | Rečenica |
|----|--------|-------|-------------|----------|
| 1 | The Hound of the Baskervilles | Arthur Conan Doyle | 2852 | 3.852 |
| 5 | The Big Four | Agatha Christie | 70114 | 5.055 |
| 8 | Frankenstein; or, the Modern Prometheus | Mary Wollstonecraft Shelley | 84 | 3.384 |

---

## 9. Stanje prevoda (na kraju sesije 44)

| Knjiga | Jezik | Rečenice | Status |
|--------|-------|----------|--------|
| Hound (id=1) | hr, bs | 350 | ✅ prevod + sudija + pobjednici |
| Hound (id=1) | af, de, es, fr, it, nl, sl, sr, pt, ro | 100 | ✅ prevod + sudija + pobjednici |
| Big Four (id=5) | pt | 100 | ✅ prevod + sudija + pobjednici |
| Frankenstein (id=8) | ro | 100 | ✅ prevod + sudija + pobjednici |

**Srpski (sr):** prevodi transliterirani u ćirilicu (`bb_sr_cirilica.py`).

---

## 10. Infrastruktura

### Serveri

| Server | Adresa | Uloga |
|--------|--------|-------|
| **foxuno** | `foxuno.dynu.net` | Razvoj, kod, Python venv, git |
| **balsam** | `balsam.dynu.net` | Docker host — PostgreSQL |

> ⚠️ Sav razvoj je na **foxuno**. User se zove `balsam` ali to je user na foxuno serveru!

### MCP alati

- `foxuno:run_command` — skripte, fajlovi, git
- `balsam:run_command` — SQL operacije (`docker exec pgdb psql`)
- **Ne miješati** — SQL komande idu isključivo na balsam

### Web prikaz

- **URL:** https://buchenberg.opik.net
- **DocumentRoot:** `/var/www/buchenberg/`
- **JSON data:** `/var/www/buchenberg/data/`
- Apache2 odmah servira novi sadržaj — nema potrebe za restartem

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

### Dokumentacija

Svaka sesija završava:
1. `session_NN.md` — artefakt u chatu → Flavio OK → save na server
2. README update ako je potrebno
3. `git add -A && git commit -m "..." && git push`

---

## 13. Poznati bugovi (riješeni)

| Bug | Sesija | Fix |
|-----|--------|-----|
| `bb_04_pobjednik.py` DELETE bez range filtera brisao sve pobjednike za jezik | 38 | DELETE sada filtrira po opsegu |
| Ollama Cloud retry nedostajao | 38 | 3 pokušaja, 30s čekanje |
| `bb_knjige.gutenberg_id` bez UNIQUE constrainta — dupli insert prolazio tiho | 41 | `ALTER TABLE bb_knjige ADD CONSTRAINT bb_knjige_gutenberg_id_unique UNIQUE (gutenberg_id)` |

---

## 14. Sljedeći koraci

1. **Proširenje Hound** — svih 12 jezika na s101–s350
2. **Proširenje PT (Big Four)** — s101–s350
3. **Proširenje RO (Frankenstein)** — s101–s350
4. **Novi jezici za sve knjige** — po workflow-u iz sesije 41
5. **Export** — `bb_05_export.py` za jezike s dovoljno rečenica
6. **SR ćirilica** — provjeriti da li se `bb_sr_cirilica.py` automatski poziva nakon `bb_04_pobjednik.py`
7. **bb_web_export.py** — refaktorisati da koristi `v_pobjednici` view

---

*Dokument će biti ažuriran sa svakom novom verzijom. Uvek čitaj samo poslednju verziju.*  
*Flavio & Claude · Buchenberg · V3 · 4. jun 2026.*
