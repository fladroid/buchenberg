# Session 65 — Reader infobox, NLP poboljšanja, Geometry + srpski

**Datum:** 10. jun 2026. (druga sesija dana)
**Autor:** Flavio & Claude

---

## Urađeno

### 1. reader.html — Novel infobox premješten
- Infobox (Author/Language/Sentences/Pipeline/Source) premješten iz tekst zone
  u `#book-header`: flex layout — naslov+autor lijevo, infobox desno u istoj ravni
- Na uskim ekranima (flex-wrap) infobox pada ispod naslova

### 2. nlp.html — redosljed panela
- Novi redosljed: Entity Links + Type Conflicts → **Entity Network** → Original Text
- JS netaknut (sve po ID-jevima)

### 3. nlp.html — highlight bug fix ("the Nonpareil Club")
- Bug: `parts.some(p => p.length > 2 && textLower.includes(p))` — "the" (3 slova)
  prolazio filter, substring match bojio praktično sve rečenice
- Fix: STOP lista (the, and, of, mr, sir...) + word-boundary regex umjesto includes()
- Logika po tipu: **PERSON = OR** (hvata samo-prezime pomene), **ostali tipovi = AND**
  (sve značajne riječi) — "the Nonpareil Club" sada traži nonpareil AND club

### 4. nlp.html — redni brojevi + navigacija po žutim
- Superscript redni broj ispred svake rečenice (konvencija iz Readera)
- Kontrole u text headeru (vidljive samo kad je entitet aktivan):
  ◀ n/N ▶ kružna navigacija + "only highlighted" filter
- Trenutna pozicija = jača žuta (`.hl-current`), auto-scroll na centar

### 5. Geometry — dodat srpski (eksperiment: pismo vs značenje)
- `bb_geometry_export.py`: JEZICI = [hr, **sr**, it, de]
- `geometry.json` regenerisan: 1000 vektora (200 rečenica × 5 jezika), 378s
- geometry.html: SR toggle (ljubičasta #8e44ad), LANG_* konstante, render order
- **Rezultat:** hr↔sr tačke praktično preklopljene u UMAP-u — e5-large enkodira
  značenje preko pisma (ćirilica/latinica). Flaviova ranija zapažanja: velika/mala
  slova i interpunkcija ipak mjerljivo utiču na score — forma curi, ali malo
- TODO: ćirilična virtuelna tastatura za custom A/B unos

### 6. nav.js — bump na s65

---

## Sljedeće

- Flavio testira novi NLP/Geometry — feedback za dodatke/izmjene
- Ostalo: prijevodi hr/sr/it/de → s350, mk/bg → s51–100; about.html i18n;
  learn.html igre; web u git
