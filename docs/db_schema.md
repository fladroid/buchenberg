# Buchenberg — Shema baze podataka

**Datum:** 15. maj 2026.  
**Baza:** PostgreSQL 17.9 + pgvector 0.8.2  
**Filozofija:** Maksimalno relacioni model, minimalno JSON, pgvector samo za vektore.

---

## Tabele

### books

| Kolona | Tip | Ograničenja | Opis |
|--------|-----|-------------|------|
| id | SERIAL | PK | Interni ID |
| gutenberg_id | INTEGER | UNIQUE NOT NULL | Gutenberg broj (npr. 3070) |
| title | VARCHAR(500) | NOT NULL | Naslov knjige |
| author | VARCHAR(300) | NOT NULL | Autor |
| language | CHAR(2) | NOT NULL DEFAULT 'en' | ISO 639-1 kod |
| html_path | TEXT | | Putanja do raw HTML fajla na foxuno |
| downloaded_at | TIMESTAMP | DEFAULT NOW() | Kad je knjiga skinuta |
| status | VARCHAR(20) | DEFAULT 'downloaded' | downloaded \| parsed \| translating \| done |

---

### sentences

| Kolona | Tip | Ograničenja | Opis |
|--------|-----|-------------|------|
| id | SERIAL | PK | Interni ID |
| book_id | INTEGER | FK → books.id NOT NULL | Knjiga kojoj pripada |
| block_no | INTEGER | NOT NULL | Redni broj bloka/paragrafa u knjizi |
| sentence_no | INTEGER | NOT NULL | Redni broj rečenice unutar bloka |
| text | TEXT | NOT NULL | Originalni engleski tekst rečenice |
| word_count | SMALLINT | NOT NULL | Broj riječi (`len(text.split())`) |
| sentiment_label | VARCHAR(10) | | positive \| negative \| neutral |
| sentiment_score | REAL | | Float 0.0–1.0, pouzdanost labele |

**Constraints:**
```sql
UNIQUE (book_id, block_no, sentence_no)
```

**Napomena:** `block_no.sentence_no` je prirodni ID rečenice u kontekstu knjige (npr. `42.3` = blok 42, rečenica 3). Poravnanje s prevodom je automatsko.

---

### translations

| Kolona | Tip | Ograničenja | Opis |
|--------|-----|-------------|------|
| id | SERIAL | PK | Interni ID |
| sentence_id | INTEGER | FK → sentences.id NOT NULL | Originalna rečenica |
| target_lang | CHAR(2) | NOT NULL | ISO 639-1 kod ciljnog jezika |
| method | VARCHAR(10) | NOT NULL | nllb \| gemma |
| translated_text | TEXT NOT NULL | | Prevod na ciljni jezik |
| back_translation | TEXT | | Prevod nazad na engleski |
| score | REAL | | Cosine similarity (original vs. back-translation) |
| winner | BOOLEAN | DEFAULT FALSE | Pobjednička metoda za ovu rečenicu |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Constraints:**
```sql
UNIQUE (sentence_id, target_lang, method)
```

---

### embeddings

| Kolona | Tip | Ograničenja | Opis |
|--------|-----|-------------|------|
| id | SERIAL | PK | Interni ID |
| sentence_id | INTEGER | FK → sentences.id NOT NULL | Rečenica |
| vector | vector(384) | NOT NULL | pgvector embedding |
| model | VARCHAR(100) | NOT NULL | Naziv modela (npr. all-MiniLM-L6-v2) |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Constraints:**
```sql
UNIQUE (sentence_id, model)
```

---

### named_entities

| Kolona | Tip | Ograničenja | Opis |
|--------|-----|-------------|------|
| id | SERIAL | PK | Interni ID |
| sentence_id | INTEGER | FK → sentences.id NOT NULL | Rečenica kojoj pripada |
| text | VARCHAR(300) | NOT NULL | Tekst entiteta (npr. "Sherlock Holmes") |
| label | VARCHAR(10) | NOT NULL | PERSON \| LOC \| ORG \| MISC |
| start_char | SMALLINT | NOT NULL | Početna pozicija u originalnoj rečenici |
| end_char | SMALLINT | NOT NULL | Krajnja pozicija u originalnoj rečenici |

---

## Odnosi između tabela

```
books
  └── sentences (book_id)
        ├── translations (sentence_id)
        ├── embeddings (sentence_id)
        └── named_entities (sentence_id)
```

---

## SQL — kreiranje tabela

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE books (
    id            SERIAL PRIMARY KEY,
    gutenberg_id  INTEGER UNIQUE NOT NULL,
    title         VARCHAR(500) NOT NULL,
    author        VARCHAR(300) NOT NULL,
    language      CHAR(2) NOT NULL DEFAULT 'en',
    html_path     TEXT,
    downloaded_at TIMESTAMP DEFAULT NOW(),
    status        VARCHAR(20) DEFAULT 'downloaded'
);

CREATE TABLE sentences (
    id              SERIAL PRIMARY KEY,
    book_id         INTEGER NOT NULL REFERENCES books(id),
    block_no        INTEGER NOT NULL,
    sentence_no     INTEGER NOT NULL,
    text            TEXT NOT NULL,
    word_count      SMALLINT NOT NULL,
    sentiment_label VARCHAR(10),
    sentiment_score REAL,
    UNIQUE (book_id, block_no, sentence_no)
);

CREATE TABLE translations (
    id               SERIAL PRIMARY KEY,
    sentence_id      INTEGER NOT NULL REFERENCES sentences(id),
    target_lang      CHAR(2) NOT NULL,
    method           VARCHAR(10) NOT NULL,
    translated_text  TEXT NOT NULL,
    back_translation TEXT,
    score            REAL,
    winner           BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE (sentence_id, target_lang, method)
);

CREATE TABLE embeddings (
    id          SERIAL PRIMARY KEY,
    sentence_id INTEGER NOT NULL REFERENCES sentences(id),
    vector      vector(384) NOT NULL,
    model       VARCHAR(100) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (sentence_id, model)
);

CREATE TABLE named_entities (
    id          SERIAL PRIMARY KEY,
    sentence_id INTEGER NOT NULL REFERENCES sentences(id),
    text        VARCHAR(300) NOT NULL,
    label       VARCHAR(10) NOT NULL,
    start_char  SMALLINT NOT NULL,
    end_char    SMALLINT NOT NULL
);
```

---

*Buchenberg · db_schema v1 · 15. maj 2026.*
