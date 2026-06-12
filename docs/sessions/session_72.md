# Session 72 — Buchenberg

**Datum:** 12. jun 2026.
**Sesija:** 72
**Autor:** Flavio & Claude

---

## Što je urađeno

### 1. bb_06_enkodiranje.py — retroaktivno pokrenuto

Utvrđeno da od 121.618 prevoda samo 360 ima `prevod_vektor`, a od 8.452 pobjednika samo 73. Skripta ima `WHERE prevod_vektor IS NULL` — sigurna za prekidanje i nastavak.

Pokrenuto u pozadini:
```
nohup time venv/bin/python src/bb_06_enkodiranje.py --embedder "multilingual-e5-large" > logs/bb_06_enkodiranje.log 2>&1 &
```
PID 71663. Na kraju sesije: 81.920/121.238 — završava noću ili sutra ujutro.

**Napomena:** bb_06 treba dodati u standardni pipeline redosljed nakon bb_03:
```
bb_03 → bb_06 → bb_08 → bb_04 → bb_05
```

### 2. naturalness_score — identificiran kao nepohranjeni podatak

`naturalness_score` se računa u `bb_03_prevod.py` ali se ne sprema u bazu. Isti propust kao `prevod_vektor`. Potrebna zasebna skripta (analogna bb_06) koja će retroaktivno popuniti kolonu. **TODO za sljedeću sesiju.**

### 3. nav.js — menu "Books" → "Library" (svih 5 jezika)

| Jezik | Staro | Novo |
|-------|-------|------|
| EN | Books | Library |
| DE | Bücher | Bibliothek |
| IT | Libri | Biblioteca |
| HR | Knjige | Knjižnica |
| SR | Књиге | Библиотека |

Izmjena u nav.js i u svim HTML stranicama koje imaju vlastiti I18N objekt: about.html, index.html, nlp.html, reader.html, stats.html, books.html.

**Naučeno:** Svaki put kad se mijenja nav stavka u nav.js, isti string treba promijeniti i u svim HTML fajlovima koji imaju vlastiti I18N objekt.

### 4. BB_VERSION bumplan na s72

nav.js: BB_VERSION = 's72', datum 12 Jun 2026.

### 5. reader.html — kompletni redesign

#### 5a. Bočni meniji → dva dropdown-a

Uklonjen sidebar grid layout. Dodana dva select dropdown-a gore:
- BOOKS dropdown — lista svih knjiga
- TRANSLATIONS dropdown — lista dostupnih jezika za odabranu knjigu

Rečenice zauzimaju punu širinu. "Show original" two-column layout ostao nepromijenjen.

#### 5b. X-Ray panel — kompletni X-Ray za svaku rečenicu

bb_web_export.py proširen — novi JSON fajlovi sad sadrže:
- back_translation — tekst backtranslationa
- naturalness — naturalness score (trenutno skoro uvijek null)
- sudija_grammar, sudija_natural, sudija_fidelity — individualne sudijske ocjene

X-Ray toggle prikazuje ispod svake prevedene rečenice:
- BT — tekst backtranslationa
- Translation Score — cosine similarity prevod/original
- Back Score — cosine similarity backtranslation/original
- Judge Average, Grammar, Naturalness, Fidelity — sudijske ocjene
- Model i t= temperatura

nat (naturalness_score) skriven dok se retroaktivno ne izračuna za sve rečenice.

#### 5c. X-Ray legenda

Kad je X-Ray toggle uključen, iznad reader-main pojavljuje se legenda u stilu Novel infoboxa (plavi naslov, dvije kolone). Objašnjava sve labele uključujući Model i t=.

#### 5d. Score-info toolbar

Desno u toolbaru: avg Translation Score · avg Back Score · avg Judge

---

## Stanje na kraju sesije

- bb_06_enkodiranje.py radi u pozadini (PID 71663) — 81.920/121.238
- naturalness_score retroaktivno punjenje: TODO (potrebna nova skripta)
- bb_06 u standardni pipeline redosljed: TODO
- Web fajlovi u git: TODO (stalni dug)

---

## Greške koje ne smijemo ponoviti

- Kad vidimo djelomičan napredak, izračunati trajanje i reći "pokreni noću" — ne "tempo je dobar"
- Enumerirati sve "obračunate ali nepohranjene" veličine na početku sljedeće sesije

---

*Flavio & Claude · Buchenberg · sesija 72 · 12. jun 2026.*
