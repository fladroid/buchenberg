# Session 56 — 6 novih knjiga, NER za sve nove knjige

**Datum:** 7. jun 2026.
**Sesija:** 56
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Dodavanje Moby Dick

- Skinut HTML ZIP sa Gutenberga: `pg2701-h.zip` → `books/moby_dick/`
- Dodан unos u `bb_02_insert_knjiga.py`
- Ubačeno: **9764 rečenica**, knjiga_id=12

### 2. Dodavanje 5 novih knjiga

URL-ovi:
- `pg1513-h.zip` → Romeo and Juliet (Shakespeare)
- `pg11-h.zip` → Alice's Adventures in Wonderland (Carroll)
- `pg43-h.zip` → The Strange Case of Dr. Jekyll and Mr. Hyde (Stevenson)
- `pg345-h.zip` → Dracula (Stoker)
- `pg201-h.zip` → Flatland: A Romance of Many Dimensions (Abbott)

Metapodaci izvučeni automatski iz HTML-a. Sve 5 dodane u `bb_02_insert_knjiga.py` i ubačene u bazu.

### 3. Stanje knjiga nakon inserta

| ID | Knjiga | Autor | Rečenica |
|----|--------|-------|---------|
| 1 | The Hound of the Baskervilles | Conan Doyle | 3852 |
| 5 | The Big Four | Christie | 5055 |
| 8 | Frankenstein | Shelley | 3384 |
| 12 | Moby Dick; Or, The Whale | Melville | 9764 |
| 17 | Romeo and Juliet | Shakespeare | 3172 |
| 18 | Alice's Adventures in Wonderland | Carroll | 1535 |
| 19 | The Strange Case of Dr. Jekyll and Mr. Hyde | Stevenson | 1157 |
| 20 | Dracula | Stoker | 9073 |
| 21 | Flatland: A Romance of Many Dimensions | Abbott | 1341 |

### 4. NER pipeline za sve nove knjige

Pokretano knjiga po knjiga (`bb_09_ner.py --knjiga ID`):

| Knjiga | ID | Entiteti | Veze | Trajanje |
|--------|-----|---------|------|---------|
| Moby Dick | 12 | 1447 | 4281 | 3m 35s |
| Dracula | 20 | 495 | 2700 | 2m 08s |
| Romeo and Juliet | 17 | 240 | 936 | 50s |
| Alice in Wonderland | 18 | 114 | 856 | 47s |
| Jekyll and Hyde | 19 | 52 | 440 | 25s |
| Flatland | 21 | 298 | 1021 | 59s |

### 5. Web export

`bb_web_export.py` pokrenut dva puta — nakon Moby Dick i nakon svih NER-ova. Portal sada prikazuje 9 knjiga sa kompletnim NER podacima.

---

## Napomene

- `bb_02_insert_knjiga.py` ne koristi Ollamu — samo spaCy lokalno
- `bb_web_export.py` ne koristi Ollamu — samo SQL
- `bb_09_ner.py` koristi `gemma4:31b` za normalizaciju — troši Ollama resurse
- NER za Big Four (id=5) nije pokrenut u ovoj sesiji (već ima 259 entiteta iz ranije)

---

## TODO (ažurirano)

1. **sr** — gemma3+ministral s221–s300, sudija --force, bb_sr_cirilica, pobjednici
2. `ON DELETE CASCADE` na `bb_prev_recenica`
3. hr/it/de → s350 (cloud)
4. Ostali jezici → s101–s350
5. mk/bg → s51–s100
6. `--skip-ollama` flag u health_check.py
7. Web fajlovi u git
8. Favicon
9. Relation Extraction
10. `bb_web_export.py` refaktor → `v_pobjednici`
11. README ažurirati — nove knjige

---

*Flavio & Claude · Buchenberg · Sesija 56 · 7. jun 2026.*
