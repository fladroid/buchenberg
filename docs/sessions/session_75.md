# Session 75 — Web portal: Key Concepts, Tapestry, Geometry

**Datum:** 13. jun 2026.
**Sesija:** 75
**Autor:** Flavio & Claude

---

## Što je urađeno

### 1. Checklist (standardni)
- Project files pročitani (buchenberg_napomena_new.md, X-Ray SR/EN)
- README pročitan (V3, s73 — README je bio neažuriran, zadnji session doc bio s74)
- Sessions 72–74 pročitane
- Health check: sve zeleno — 38.333 rečenica, 124.128 prevoda, 8.602 pobjednika
- Git: buchenberg 37ba196, buchenweb 9427100

### 2. Footer provjera
- BB_VERSION = 's74', BB_VERSION_DATE = '13 Jun 2026' — ispravno
- `id="bb-footer"` prisutan na svih 9 stranica — ispravno

### 3. Key Concepts — nova funkcionalnost (about, geometry, art, nlp)

**Ideja:** YouTube-style "key concepts" sekcija — mala kartica s ikonom, imenom koncepta, jednom rečenicom i linkom na Wikipedia.

**Implementacija:**
- `data/concepts.json` — novi statički fajl, EN opisi, 4 stranice × 3–5 koncepta
- `buchenberg.css` — dodani `.bb-key-concepts`, `.bb-concepts-grid`, `.bb-concept-card` stilovi
- `nav.js` — `renderKeyConcepts()` IIFE: detektuje stranicu, fetch concepts.json, injektuje sekciju prije footera

**Ispravke u toku:**
- `max-width: 900px` → `1200px` (poravnanje sa `#bb-page`)
- `display: flex; flex-wrap: wrap` → `display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr))` — kartice u zadnjem redu sada iste širine kao u prvom

**Koncepti po stranicama:**

| Stranica | Koncepti |
|---------|---------|
| about | Back-translation, Cosine similarity, Sentence embedding, Transformer, NLLB-200 |
| geometry | Sentence embedding, UMAP, Cosine similarity, Vector space model |
| art | Synesthesia, Wassily Kandinsky, Alexander Scriabin, BLEU score, Sentence embedding |
| nlp | Named-entity recognition, spaCy, Co-occurrence |

### 4. The Tapestry (art.html) — tri poboljšanja

#### 4a. Tamni okvir (ram)
`#tap-canvas-wrap` dobio `padding: 14px; background: #1c1c1c; border-radius: 6px; box-shadow`.

#### 4b. Samo prevedene rečenice
`render()`: `tapSlice` se gradi isključivo od `s.translated` rečenica:
```javascript
const translated = cur.sentences.filter(s => s.translated);
tapSlice = tapCount ? translated.slice(0, tapCount) : translated;
```
Rezultat: nula sivih piksela.

#### 4c. Centriranje zadnjeg reda
Nepotpuni zadnji red (kad broj rečenica ne popunjava cio red) se centrira:
- `lastRowOffset` i `totalRows` dodani u outer scope
- `render()`: `if (n <= cols) cols = n` — single-row kanvas tačne širine
- forEach loop: `xOff = lastRowOffset * cellSize` za zadnji red
- `mousemove` handler: `adjCol = col - lastRowOffset` za zadnji red
- Padding fix: `clientWidth - 28` (oduzeti 14px padding s obje strane)

### 5. Geometry scatter — grid i zoom

#### 5a. Grid pozadina
D3 grid linije dodane u `renderScatter()` PRIJE dots petlje, u `chartGroup`:
- `xScale.ticks(20)` → minor linija svakih ~0.05
- `yScale.ticks(15)` → minor linija svakih ~0.07
- index `% 10 === 0` → major linija (`rgba(128,128,128,0.28)`)
- ostale minor (`rgba(128,128,128,0.12)`)

#### 5b. D3 zoom
- ClipPath rect `[PAD, PAD, W-2*PAD, H-2*PAD]` — sadržaj se ne prikazuje izvan plot area
- `chartGroup` — grid + dots; zoom transform se primjenjuje na grupu
- `d3.zoom().scaleExtent([1, 12])` → scroll/pinch za zoom, drag za pan
- Reset dugme "1×" (pored `geo-point-count`) → `svg.transition().call(zoomBehavior.transform, d3.zoomIdentity)`

### 6. Measure similarity (geometry.html) — grid i centriranje

#### 6a. Grid iza angle SVG
`drawAngle()`: prepend grid linija (14px korak, 0-140) u `svg.innerHTML`:
```javascript
for (let gx = 14; gx < 140; gx += 14) gridLines += `<line .../>`;
for (let gy = 14; gy < 140; gy += 14) gridLines += `<line .../>`;
svg.innerHTML = gridLines + `...`;
```

#### 6b. Rezultat centriran
`.geo-result-layout`: `display: grid; grid-template-columns: auto 1fr` → `display: flex; flex-direction: column; align-items: center; text-align: center`

#### 6c. Angle SVG povećan
`width="140" height="140"` → `width="220" height="220"` (viewBox nepromijenjen → SVG automatski skalira)

### 7. nav.js → s75 (13 Jun 2026)

---

## Stanje na kraju sesije

- buchenweb: commit na čekanju (nav.js s75 + sve web izmjene s75)
- buchenberg: nepromijenjen (session doc + README commit)
- Corpus: 38.333 / 124.128 / 8.602 — nepromijenjen

---

## Sljedeće (kumulativno)

- naturalness_score retroaktivno punjenje (nova skripta)
- Prijevodi: hr/sr/it/de → s350; mk/bg → s51–s100
- Cache-Control za js/css (.htaccess)
- about.html i18n; learn.html nove igre

---

*Flavio & Claude · Buchenberg · sesija 75 · 13. jun 2026.*
