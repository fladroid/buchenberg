# Session 49 — Bugfixevi: reader, navigacija, cache busting

**Datum:** 4. jun 2026.
**Sesija:** 49
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. reader.html — `__v` ReferenceError

`selectOriginal()` i `selectLang()` koristile `__v` koja je bila lokalna varijabla unutar `init()`. Fix: `window.__v = __ver.v` u `init()`, a vanjske funkcije koriste `window.__v || Date.now()`.

### 2. reader.html — NLP nav link nedostajao

`sed` nije dodao NLP link u `reader.html` jer je Reader imao `active` klasu. Ručno dodano:
```html
<a href="nlp.html" class="bb-nav-link">NLP</a>
<a href="reader.html" class="bb-nav-link active">Reader</a>
```

### 3. README update

- Dodana `bb_09_ner.py` u tabelu skripti
- `books.html` — NER i Word cloud označeni kao aktivni
- Dodana `nlp.html` u web portal tabelu s opisom
- Sljedeći koraci: uklonjen "spaCy NER coming soon", dodan "Relation Extraction via Gemma4"

---

## Stanje baze — nepromijenjeno

---

## Otvoreno za sljedeće sesije

1. Proširenje Hound — svih 12 jezika na s101–s350
2. Proširenje Big Four PT i IT — s101–s350
3. Proširenje Frankenstein RO i IT — s101–s350
4. Favicon za buchenberg.opik.net
5. Relation Extraction (Gemma4) — semantičke veze između entiteta
6. Refaktorisati `bb_web_export.py` da koristi `v_pobjednici` view
7. `stats.html` — dedicated `stats.json` iz `bb_web_export.py`

---

*Flavio & Claude · Buchenberg · Sesija 49 · 4. jun 2026.*
