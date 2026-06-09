# Session 62 — geometry.html: Geometry of Meaning

**Datum:** 9. jun 2026.
**Autor:** Flavio & Claude

---

## Urađeno

### 1. bb_geometry_export.py
- Novi zasebni skript `src/bb_geometry_export.py`
- Učitava s1–s200 iz Hound (knjiga_id=1), EN originale + pobjednike HR/IT/DE
- Enkodira via multilingual-e5-large (intfloat/multilingual-e5-large iz lokalnog keša)
- Zajednički UMAP na 800 vektora (EN+HR+IT+DE zajedno) → 2D koordinate
- Skalira na [0,1], sprema `data/geometry.json`
- Pokreće se ručno (opcija A) — ~160s
- Fix: EMBEDDER_PATH_MAP pattern (isto kao bb_03_prevod.py)

### 2. data/geometry.json
- 200 rečenica, 4 jezička sloja (en/hr/it/de)
- Struktura: meta + sentences[] s umap koordinatama i pobjedničkim scorovima
- Generiran: 9. jun 2026.

### 3. geometry.html
- Nova stranica `/var/www/buchenberg/geometry.html`
- 4 teorijske kartice: rečenica→vektor, dimenzije, cosinus formula, winner formula
- UMAP scatter plot (D3) — toggle EN/HR/IT/DE, hover tooltip s tekstom
- "Measure similarity" — odabir dvije rečenice, cosinus (2D UMAP aproksimacija) + SVG kut vizualizacija
- Info banner: statički JSON, Transformers.js u budućoj verziji
- Navigacija via nav.js, isti CSS kao ostale stranice

### Odluke
- UMAP (ne PCA) — ljepši klasteri, bolja edukativna vrijednost
- EN originali kao osnova scatter plota (ne prevodi)
- Cosinus u "Measure" sekciji je UMAP 2D aproksimacija — puni 1024D cosinus dolazi s Transformers.js
- Transformers.js dolazi u sljedećoj iteraciji — ništa u HTML-u se ne mijenja, samo JS blok

---

## Greške i fix-ovi

- Prva verzija skripte koristila `SentenceTransformer("multilingual-e5-large")` direktno →
  HuggingFace 401 greška jer model nije pronađen pod tim imenom
- Fix: EMBEDDER_PATH_MAP = {"multilingual-e5-large": "intfloat/multilingual-e5-large"}
  (isti pattern kao bb_03_prevod.py)

---

## Sljedeće

- Transformers.js integracija za pravi 1024D cosinus u "Measure" sekciji
- Proširenje prijevoda: hr/sr/it/de → s350, mk/bg → s51–100
- bb_geometry_export.py dodati u README (sekcija 7 — Skripte)
