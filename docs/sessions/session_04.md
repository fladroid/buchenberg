# Buchenberg — Session 04

**Datum:** 15. maj 2026.
**Trajanje:** ~4 sata
**Učesnici:** Flavio + Claude

---

## Ciljevi sesije

1. Ažurirati README
2. Skinuti 3 testne knjige sa Project Gutenberg
3. Dizajnirati shemu baze podataka
4. Napraviti plan parsiranja HTML → sentences
5. Napuniti bazu — run10

---

## Urađeno

### Protokol dokumentacije — dogovoren i fiksan

Svaki dokument prolazi kroz tri obavezna koraka:
1. Claude generiše artifakt
2. Flavio pregleda → OK ili primjedbe
3. Server + GitHub — tek nakon OK

Bez izuzetaka. Preskakanje koraka dovodi do haosa koji košta dane, pa i propast projekta.

### README — ažuriran

- Dodana `docs/sessions/` struktura
- Download knjiga kao prvi korak u "Sledeći koraci"
- Dodana kritična napomena o SQL izvršavanju (psycopg2, ne docker sa foxuno)
- Dodana sekcija o knjigama (testni korpus)
- Dodana sekcija Protokol dokumentacije
- Ažurirani sledeći koraci sa ✅ za završene

### Download knjiga

Skinute 3 knjige sa Project Gutenberg u HTML formatu:

| Knjiga | Autor | Gutenberg ID | Veličina |
|--------|-------|-------------|----------|
| The Hound of the Baskervilles | Arthur Conan Doyle | 3070 | 362 KB |
| Frankenstein | Mary Wollstonecraft Shelley | 84 | 468 KB |
| Poirot Investigates | Agatha Christie | 61262 | 359 KB |

**Zašto HTML umjesto TXT:**
- H tagovi identifikuju naslove poglavlja
- `<p>` tagovi su prirodne granice blokova
- `pg-header` i `pg-footer` divovi su standardni u svim Gutenberg knjigama — lako ih ukloniti
- ID sistem `block_no.sentence_no` garantuje poravnatost

**Zašto ove tri knjige:**
Namjerno odabrane da pokriju cijeli spektar — kratke rečenice i brzi dijalozi (Poirot), dugi složeni blokovi (Frankenstein, prosj. 101 riječ/paragraf), sredina (Hound).

### Shema baze — db_schema v1.1

Pet tabela: `books`, `sentences`, `translations`, `embeddings`, `named_entities`.

Ključne odluke:
- `sentence_type` (text/heading/caption) — svi H tagovi su `heading`, bez posebnih slučajeva
- `word_count` — čuva se u bazi, nije on-the-fly; koristi se za NLLB truncation detekciju, embedding limite, identifikaciju suspektnih prevoda
- `named_entities` — zasebna tabela, čisti relacioni model, bez JSON-a
- `sentiment_label` + `sentiment_score` — u sentences tabeli, puni se u run15
- pgvector isključivo za embeddings tabelu

### Parser plan — parser_plan v2

Generalni parser koji radi na bilo kojoj Gutenberg knjizi:
- Uklanja `pg-header` i `pg-footer`
- Sve H tagove (H1–H6) tretira kao `heading`
- TOC blok preskače (identifikacija: tekst = "CONTENTS" ili "TABLE OF CONTENTS")
- spaCy `en_core_web_sm` za sentence splitting unutar `<p>` blokova
- Poravnatost garantovana: `block_no` se inkrementira za svaki element

### run10.sh — inicijalno punjenje baze

Četiri koraka:

| Step | Fajl | Opis |
|------|------|------|
| step1 | `step1_create_tables.py` | CREATE TABLE IF NOT EXISTS, psycopg2 |
| step2 | `step2_truncate.py` | TRUNCATE books CASCADE, tabula raza |
| step3 | `step3_insert_book.py` | INSERT 3 knjige u books tabelu |
| step4 | `step4_parse_sentences.py` | Parsiranje HTML → INSERT u sentences |

**Rezultati run10:**

| Knjiga | Rečenica | Trajanje |
|--------|----------|----------|
| Hound of the Baskervilles | 3.852 | ~1 min |
| Frankenstein | 3.384 | ~1 min |
| Poirot Investigates | 4.857 | ~1 min |
| **Ukupno** | **12.093** | **3:28** |

---

## Greške i naučene lekcije

### 1. Protokol preskočen za README i analizu knjiga
README je pushovan na GitHub bez artifakta i Flavijevog OK. Analiza knjiga prikazana direktno u chatu umjesto kao artifakt.

**Lekcija:** Protokol bez izuzetaka. Jedan preskočen korak otvara vrata za sljedeći.

### 2. docker -H ssh://balsam ne radi
U prvoj verziji `run10.sh` korišten `docker -H ssh://balsam exec -i pgdb psql` — docker nije instaliran na foxuno, SSH hostname nije resolvan.

**Lekcija:** Čitaj README do kraja prije pisanja koda. README jasno kaže: `docker exec` se izvršava ručno na balsam serveru; skripte na foxuno koriste psycopg2.

### 3. beautifulsoup4 nije bio u requirements.txt
`step4_parse_sentences.py` koristi `bs4` ali paket nije bio u `requirements.txt` niti instaliran u venv.

**Lekcija:** Provjeri `venv/bin/pip list` prema importima u skripti prije pokretanja.

---

## Otvoreno za sljedeću sesiju

1. **buch_env.sh** — environment varijable (BUCH_HOME, BUCH_SRC, BUCH_LOG...), sourcuje se na početku svakog runa
2. **run15.sh** — sentiment analiza + NER, spaCy, punjenje `sentences` i `named_entities` tabela
3. **NLLB instalacija** u venv

---

*Buchenberg · session_04 · 15. maj 2026.*
