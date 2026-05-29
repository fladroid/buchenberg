# Session 30 — Embedding tabele: sentence_embeddings + translation_embeddings

**Datum:** 2026-05-29  
**Učesnici:** Flavio & Claude  
**Nastavlja:** Session 29 (tabela translations, 4480 prevoda)

---

## Kontekst — gdje smo stali

Session 29 je uspostavila novu paradigmu: `translations` tabela kešira prevode jednom, evaluacija je odvojena. Logičan sljedeći korak: keširanjem embedding vektora eliminisati i ponovljeno računanje cosinusa.

---

## Korak 1 — Dizajn embedding tabela

### Problem

Ideja je kreirati tabelu koja čuva embedding vektore i omogućava cosinus sličnost između bilo kojeg para tekstova (EN original vs prevod, ali i IT vs FR itd.).

### Razvojni put dizajna

**Pokušaj 1** — jedna tabela s `translation_id` + NULL konvencija:
```
sentence_id | translation_id | embedder | vec
            | NULL           |          |     ← EN original
            | 1234           |          |     ← prevod
```
Problem: NULL = EN original je konvencija koju treba znati. Nestabilno s aspekta dokumentacije i memorije.

**Pokušaj 2** — dodati `lang` kolonu:
```
sentence_id | translation_id | lang | embedder | vec
```
Bolji, ali `translation_id` i dalje može biti NULL za EN. Nije potpuno riješilo konvenciju.

**Ključni uvid (Flavio):** `sentence_id` u embedding tabeli postoji samo zato što EN originali žive u `sentences`, a prevodi u `translations` — dva izvora, otud sva komplikacija.

**Finalno rješenje — dvije odvojene tabele:**

```sql
sentence_embeddings    (sentence_id    → sentences)
translation_embeddings (translation_id → translations)
```

Svaka tabela ima jedan FK, uvijek popunjen, nikad NULL. Nema konvencija koje treba znati.

### Finalna shema

```sql
CREATE TABLE sentence_embeddings (
    id          SERIAL PRIMARY KEY,
    sentence_id INTEGER NOT NULL REFERENCES sentences(id),
    embedder    VARCHAR(20) NOT NULL,
    dim         INTEGER NOT NULL,
    vec         vector(1024),
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (sentence_id, embedder)
);

CREATE TABLE translation_embeddings (
    id             SERIAL PRIMARY KEY,
    translation_id INTEGER NOT NULL REFERENCES translations(id) ON DELETE CASCADE,
    embedder       VARCHAR(20) NOT NULL,
    dim            INTEGER NOT NULL,
    vec            vector(1024),
    created_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE (translation_id, embedder)
);
```

`vector(1024)` — e5-large i SONAR su preporučeni embedderі (oba 1024 dim). MiniLM (384) dodaje se kad zatreba.

### Napomena o višejezičnim embedderima

Višejezički embedder (e5, SONAR, MiniLM) mapira sve jezike u **isti** vektorski prostor. Cosinus između IT i FR vektora izračunljiv je direktno — bez prevoda IT→FR. "Prevodi" u `translations` su tekstualni input za embedder, ne most između jezika.

pgvector `<=>` operator računa cosinus distance direktno u SQL-u: `1 - (vec1 <=> vec2)` = cosinus sličnost.

---

## Korak 2 — Test skripta

Nova skripta: `src/test_embeddings.py`

Parametri testa: rečenice s4–s8 (izbjegavamo s1–s3 metadata), IT prevodi (gemma3:12b, t=0.5), embedder e5-large.

### Rezultati

```
======================================================================
  Cosinus  EN vs IT  |  gemma3:12b  t=0.5  |  embedder: e5
======================================================================

  s4  cosine = 0.9295  — Mr. Sherlock Holmes...
  s5  cosine = 0.8890  — I stood upon the hearth-rug... (the stick)
  s6  cosine = 0.9080  — It was a fine, thick piece of wood...
  s7  cosine = 0.8764  — Just under the head was a broad silver band...
  s8  cosine = 0.9241  — "To James Mortimer, M.R.C.S..."
```

s5 i s7 (rečenice o "the stick") imaju najniže scoreove — konzistentno s ranijim nalazima iz test_018.

---

## Izmjene koda i baze

| Komponenta | Izmjena |
|------------|---------|
| `sentence_embeddings` | Nova tabela — EN originali, UNIQUE (sentence_id, embedder) |
| `translation_embeddings` | Nova tabela — prevodi, UNIQUE (translation_id, embedder) |
| `embeddings` | Dropovana (stara shema, prazna) |
| `src/test_embeddings.py` | Nova skripta — enkodiranje + upis + cosinus query |

---

## Na horizontu

1. **`run_embeddings.py`** — skripta za punjenje svih 4480 prevoda × embedderе (e5 + SONAR)
2. **Evaluacija iz `translations`** — metoda koja čita vektore iz baze, računa cosinus bez Ollame
3. **Cross-lingual parovi** — IT vs FR, HR vs DE itd. iz istih vektora (bez novih prevoda)
4. **DeepL integracija** — peta metoda u `translations`
5. **CREATE TABLE skripta** — ažurirati da uključi `sentence_embeddings` i `translation_embeddings`

---

## Handoff blok

- **`sentence_embeddings`:** kreirana, testirana (5 redova)
- **`translation_embeddings`:** kreirana, testirana (5 redova)
- **`test_embeddings.py`:** aktivan u `src/`
- **Git:** commit `4839384` — pushano na main
- **Model:** Sonnet 4.6 medium

---

*Flavio & Claude · Session 30 · 2026-05-29*

---

## Addendum (session_30b–e)

### run_embeddings.py — punjenje vektora

Nova skripta za punjenje `sentence_embeddings` i `translation_embeddings`.
MiniLM run (40 EN + 4480 prevoda) završen za 2:10 min. ON CONFLICT DO NOTHING.

```bash
venv/bin/python src/run_embeddings.py --embedder minilm --sent_from 1 --sent_to 40
```

### ALTER TABLE — fleksibilna dimenzija

`vec vector(1024)` → `vec vector` (bez fiksne dim) — podržava i MiniLM (384) i e5/SONAR (1024).

### VIEW: translation_scores

Cosinus sličnost direktno iz pgvector — bez pozivanja modela:
```sql
1 - (se.vec <=> te.vec)  -- pgvector cosinus distance operator
```

### VIEW: best_translation

Za svaku rečenicu — jedan red s globalnim best scoreom (svi jezici, svi modeli):
```sql
SELECT DISTINCT ON (sentence_id) ... ORDER BY sentence_id, cosine_score DESC
```

### sql/create_views.sql

Novi direktorij `sql/` s reproducibilnom shemom VIEW-ova.

### Stanje baze

| Tabela | Redova |
|--------|--------|
| `sentence_embeddings` | 40 (MiniLM) |
| `translation_embeddings` | 4480 (MiniLM) |

### Na horizontu

1. Popuniti e5-large vektore (`--embedder e5`) za usporedbu s MiniLM
2. `sql/create_tables.sql` — kompletna shema baze za reproducibilnost
3. Pipeline orchestrator — finalni prevod iz `best_translation`
