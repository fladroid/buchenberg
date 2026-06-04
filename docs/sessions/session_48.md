# Session 48 — NLP stranica, network graph, slider, favicon

**Datum:** 4. jun 2026.
**Sesija:** 48
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. NER co-occurrence veze u bb_web_export.py

Dodana `get_ner_veze()` funkcija koja računa co-occurrence veze između entiteta (dva entiteta su u vezi ako se pojavljuju u istoj rečenici). Export u `ner_*.json` s `min_tezina=1` (sve veze, filtering client-side).

**Rezultati:**
- `ner_1.json` — 194 veze
- `ner_5.json` — 198 veza
- `ner_8.json` — 205 veza

### 2. nlp.html — nova stranica

Kompletna NLP stranica s tri panela:

**Word Cloud** — EN original, NER bojanje:
- PERSON = zlatna/žuta
- GPE = zelena
- ORG = ljubičasta
- Ostale riječi = sivo/plavo

**Named Entities** — lista s filter tipova (All/Person/Place/Org), sortirana po pojavljujivanjima, klik → highlight rečenica u tekstu.

**Entity Network** — D3 force-directed graph:
- Čvorovi: entiteti, radius ~ broj pojava
- Veze: co-occurrence, debljina ~ tezina
- Drag & drop čvorova
- Zoom (scroll) + pan (drag) + reset (dvostruki klik)
- **Slider** min. co-occurrences (1–max) — filtrira veze client-side
- Tooltip na hover

**Original Text** — scrollable, highlight rečenica pri klik na entitet.

### 3. Navigacija

NLP link dodan na sve stranice (index, about, stats, books, reader). i18n ključevi `nav_nlp` dodani u sve I18N objekte. NER dugme na `books.html` aktivirano — otvara `nlp.html?book=ID`.

### 4. Bugfixevi ove sesije

- `filteredVeze` definisan prije upotrebe (ReferenceError)
- Duplikat `nlp_net_title` ključ u HR/SR I18N objektima uzrokovao JS syntax error
- `min_tezina=1` u web exportu — sve veze u JSON-u, filtering u browseru

---

## Stanje baze na kraju sesije

Nepromijenjeno — NER podaci za sve 3 knjige.

---

## Otvoreno za sljedeće sesije

1. Proširenje Hound — svih 12 jezika na s101–s350
2. Proširenje Big Four PT i IT — s101–s350
3. Proširenje Frankenstein RO i IT — s101–s350
4. Favicon za buchenberg.opik.net
5. Relation Extraction (Gemma4) — semantičke veze između entiteta
6. Refaktorisati `bb_web_export.py` da koristi `v_pobjednici` view

---

*Flavio & Claude · Buchenberg · Sesija 48 · 4. jun 2026.*
