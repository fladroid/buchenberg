# Session 05 — Buchenberg

**Datum:** 15. maj 2026.  
**Učesnici:** Flavio & Claude

---

## Šta smo radili

Produktivna sesija — završili smo korake 4, 5 i 6 iz plana, plus uspostavili kompletan test ciklus sistem i pokrenuli prvi pravi test sa 5 južnoslavenskih jezika.

---

## Korak 4 — `buch_env.sh`

Kreiran fajl `/home/balsam/buchenberg/buch_env.sh` koji se sourcuje na početku svake run skripte.

**Važna napomena:** sourcovati uvijek kao `bash -c 'source buch_env.sh && ...'` — ne radi u `sh`, samo u `bash`.

Exportuje:
- `BUCH_HOME`, `BUCH_SRC`, `BUCH_LOG`, `BUCH_BOOKS`, `BUCH_VENV`
- Učitava secrets iz `.env` via `set -a / source / set +a`
- Kreira `logs/` direktorij ako ne postoji

---

## Korak 5 — Sentiment + NER (`run15.sh`)

### Instalirani paketi
- `nltk 3.9.4` — instaliran u ovoj sesiji, dodan u `requirements.txt`
- VADER lexicon — sentiment analiza kratkih rečenica
- `spacy en_core_web_sm` — već instaliran

### Naučena lekcija — dokumentacija instalacija
Instalirali smo `nltk` ali ga nismo odmah dodali u `requirements.txt`. Otkriveno tek na Flavijevu primjedbu. **Protokol:** instaliraj → odmah dodaj u `requirements.txt`.

### Skripte
- `src/step5_sentiment_ner.py` — VADER sentiment + spaCy NER, batch 500
- `run15.sh` — orchestrator

### Rezultati run15
| | Broj |
|--|--|
| Rečenica obrađeno | 12.093 |
| NER entiteta | 6.364 |
| Trajanje | ~6 min |

**Sentiment distribucija:**
- neutral: 5.221 (43%)
- positive: 3.694 (31%)
- negative: 3.178 (26%)

**NER po tipu:**
- PERSON: 2.645
- GPE: 652
- ORG: 532
- DATE: 564
- TIME: 480
- ostalo: 491

### Poznati bug u logu
`step5` log prikazuje originalni tekst rečenice, ne prevod — ispravi u sljedećoj verziji.

---

## Korak 6 — NLLB instalacija

### Clarification — šta je NLLB
NLLB nije zasebni pip paket. To je Meta-ov model koji se koristi kroz `transformers` (već instaliran). Zasebni paketi koji nedostaju bili su tokenizer zavisnosti.

### Instalirani paketi
```
sentencepiece 0.2.1   — tokenizer za NLLB (obavezan)
sacremoses 0.1.1      — tokenizer utilities za NLLB
```

Oba dodana u `requirements.txt`.

### Test prijevoda
```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
model = "facebook/nllb-200-distilled-600M"
```
Test rečenica "The dog is barking." → "Пси је лака." — netačan prevod, ali poznati problem NLLB-a s kratkim rečenicama bez konteksta. Model funkcionira ispravno.

### Napomena o veličini modela
Model se downloaduje i kešira lokalno na foxuno pri prvom pozivu (~2.5GB za 600M varijantu). Provjera prostora: 146GB slobodno — bez problema.

---

## Test ciklus sistem

### Arhitektura

**`tests/test_registry.yaml`** — jedini izvor istine za definiciju testova:
```yaml
test_001:
  book: hound_of_the_baskervilles
  sent_from: 1
  sent_to: 20
  langs: [sr, hr, mk, bs, bg]
  methods: [nllb, gemma]
```

**Nova tabela `test_results`:**
```sql
CREATE TABLE test_results (
    id               SERIAL PRIMARY KEY,
    test_id          VARCHAR(20) NOT NULL,
    sentence_id      INTEGER REFERENCES sentences(id),
    target_lang      CHAR(2) NOT NULL,
    method           VARCHAR(10) NOT NULL,
    translated_text  TEXT,
    back_translation TEXT,
    score            REAL,
    winner           BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE (test_id, sentence_id, target_lang, method)
);
```

Tabela `translations` (produkcija) se **ne dira** — test rezultati su potpuno odvojeni.

### Pokretanje

```bash
# Samo test_id — koristi parametre iz registry:
bash run20.sh --test_id test_001

# Registracija (novi test, prvi put):
bash run20.sh --test_id test_002 --book frankenstein \
  --sent_from 1 --sent_to 50 --langs sr de --methods nllb gemma
```

### Nezavisnost testova — važna izmjena u sesiji

**Inicijalni dizajn:** `clear_test` brisao sve rezultate za `test_id`.

**Problem:** ponovni run s novim jezicima brisao bi i stare jezike.

**Rješenje:** `clear_test` briše samo kombinaciju `test_id + langs`:
```python
DELETE FROM test_results 
WHERE test_id = %s AND target_lang = ANY(%s)
```

Na taj način svaki jezik unutar testa je nezavisan — možeš dodavati jezike bez gubitka prethodnih rezultata.

### Fajlovi

| Fajl | Opis |
|------|------|
| `tests/test_registry.yaml` | Definicija svih testova |
| `src/step6_create_test_table.py` | CREATE TABLE test_results + indeksi |
| `src/run_test.py` | Glavni runner — registry, prevod, back-trans, scoring, winners |
| `run20.sh` | Orchestrator |

---

## Rezultati test_001

**Parametri:** Hound of the Baskervilles, rečenice 1–20, 5 jezika, 2 metode

**Ukupno:** 200 prevoda

| lang | method | count | avg_score |
|------|--------|-------|-----------|
| bg   | gemma  | 20    | 0.792 |
| bg   | nllb   | 20    | 0.836 |
| bs   | gemma  | 20    | 0.837 |
| bs   | nllb   | 20    | 0.847 |
| hr   | gemma  | 20    | 0.856 |
| hr   | nllb   | 20    | 0.841 |
| mk   | gemma  | 20    | 0.751 |
| mk   | nllb   | 20    | 0.832 |
| sr   | gemma  | 20    | 0.789 |
| sr   | nllb   | 20    | 0.803 |

**Opservacije:**
- NLLB generalno bolji od Gemme na južnoslavenskim jezicima
- Izuzetak: `hr` (gemma 0.856 vs nllb 0.841) — Gemma blago bolja
- Makedonski (mk) ima najniže Gemma score (0.751) — ćirilica možda problem
- Score 1.000 se pojavljuje za kratke rečenice ("Good!", "Excellent!") — back-translation savršeno pogađa original

### Poznati bug — log prikazuje original, ne prevod
U `run_test.py` log format string koristi `text[:50]` umjesto `translated[:50]`. Vizualno zbunjuje jer izgleda kao da se ne prevodi. **Ispraviti u sljedećoj sesiji.**

---

## Izmjene u requirements.txt

```
nltk                  # sentiment analiza (VADER)
sentencepiece         # tokenizer za NLLB
sacremoses            # tokenizer utilities za NLLB
```

---

## Otvoreno za sljedeću sesiju

1. **Log bug** — `run_test.py` log: `text[:50]` → `translated[:50]`
2. **Zapadnogermanski jezici** — `de`, `nl`, `af` u test_001 ili novi test_002
3. **Romanski jezici** — `fr`, `it`, `es`, `pt`, `ro`
4. **Analiza rezultata** — vizualizacija scores po jeziku i metodi
5. **README ažuriranje** — test ciklus sekcija
6. **Pipeline orchestrator** — spaja sve zajedno (korak 9 iz plana)

---

*Flavio & Claude · Session 05 · 15. maj 2026.*
