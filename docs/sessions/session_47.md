# Session 47 — Word Cloud modal, NER pipeline, cache busting

**Datum:** 4. jun 2026.
**Sesija:** 47
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Cache busting — JSON fajlovi

**Problem:** browser kešira JSON fajlove, korisnici vide stare podatke.

**Rješenje:**
- `bb_web_export.py` generira `version.json` s Unix timestampom pri svakom runu
- Sve HTML stranice fetchuju `version.json?t=${Date.now()}` (nikad keširan)
- Svi ostali JSON fetchevi dobijaju `?v=${__v}` parametar
- `.htaccess` pokušaj odbačen — `mod_headers` nije aktivan na serveru

### 2. About.html — formula kompozitnog scora

Dodana formula `composite = (back_score + translation_score) / 2` u pipeline dijagram (bila je samo u tabeli, nedostajala u ASCII dijagramu).

### 3. Word Cloud modal — `books.html`

Implementiran paralelni word cloud prikaz (EN original vs. ciljni jezik):

- d3 + d3-cloud biblioteke s cdnjs
- Modal s language selector dugmadima (sortirana po nativnom imenu)
- Default jezik = jezik s najviše prevedenih rečenica
- Coverage nota: "X od Y rečenica prevedeno (Z%)"
- Stop words filtering (EN + multilingual)
- Boje po tipu entiteta (priprema za NER integraciju)
- Bugfix: `loadAndRenderTr()` umjesto `renderWC()` u lang click handleru — novi jezik nije fetchovao novi JSON

**CSS fix:** varijable `--bb-surface` → `--surface`, `--bb-bg` → `--bg` itd. (shared CSS koristi kratke nazive bez `bb-` prefiksa)

### 4. NER pipeline — `bb_09_ner.py`

Kompletni NER pipeline za sve knjige:

**Faze:**
1. spaCy `en_core_web_sm` — ekstrahuj PERSON/GPE/ORG iz originalnih rečenica
2. Gemma4:31b — normalizacija varijanti ("Holmes", "Mr. Holmes" → "Sherlock Holmes")
3. Upis u `bb_ner_entiteti` + `bb_ner_recenica`

**Rezultati:**

| Knjiga | PERSON | GPE | ORG | Ukupno entiteta | Veze |
|--------|--------|-----|-----|-----------------|------|
| Hound | 85 | 49 | 67 | 201 | 1239 |
| Big Four | 117 | 48 | 94 | 259 | 1544 |
| Frankenstein | 70 | 68 | 58 | 196 | 813 |

**Top PERSON — Hound:**
Sherlock Holmes (189), Henry Baskerville (154), Watson (107), Charles Baskerville (94), James Mortimer (93)

**Nove tabele:**
- `bb_ner_entiteti` — normalizovani entiteti po knjizi (UNIQUE knjiga+ime_norm+tip)
- `bb_ner_recenica` — veze rečenica↔entiteti s originalnim oblikom

### 5. bb_web_export.py — NER export

Dodana `get_ner()` funkcija i generiranje `ner_<id>.json` za svaku knjigu:
- `ner_1.json` — 201 entiteta
- `ner_5.json` — 259 entiteta
- `ner_8.json` — 196 entiteta

---

## Stanje baze na kraju sesije

| Knjiga | ID | Jezik | Rečenice | Status |
|--------|-----|-------|----------|--------|
| Hound | 1 | bs, hr | 350 | ✅ |
| Hound | 1 | af, de, es, fr, it, nl, sl, sr, pt, ro | 100 | ✅ |
| Big Four | 5 | pt, it | 100 | ✅ |
| Frankenstein | 8 | ro, it | 100 | ✅ |

NER: sve 3 knjige ✅

---

## Otvoreno za sljedeće sesije

1. Web integracija NER-a u Word Cloud modal (bojanje entiteta po tipu)
2. Aktivirati NER dugme na `books.html`
3. Proširenje Hound — svih 12 jezika na s101–s350
4. Proširenje Big Four PT i IT — s101–s350
5. Proširenje Frankenstein RO i IT — s101–s350
6. Refaktorisati `bb_web_export.py` da koristi `v_pobjednici` view

---

## Git commits ove sesije

- `cache busting: version.json, .htaccess no-cache, bb_web_export update`
- `cache busting: version.json fetchovan s Date.now() parametrom`
- `session 46: Big Four IT s1-100 (gemma3+ministral+nllb+sudija+pobjednici), web export`
- `bb_09_ner.py: NER pipeline (spaCy + Gemma4 normalizacija), tabele bb_ner_entiteti + bb_ner_recenica`

---

*Flavio & Claude · Buchenberg · Sesija 47 · 4. jun 2026.*
