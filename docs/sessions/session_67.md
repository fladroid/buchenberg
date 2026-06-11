# Session 67 — art.html v1: Synesthesia kartica + The Tapestry

**Datum:** 11. jun 2026.
**Autor:** Flavio & Claude

---

## Urađeno

### 1. Checklist (standardni)
- Memorija osvježena, README pročitan (V3, s65), sessions 64–66 pročitani
- Health check: **sve zeleno** — 38.333 rečenica, 107.028 prevoda (+742 od s66),
  8.452 pobjednika; git čist (b2d90e1)

### 2. Zagrevanje: art.html skeleton + navigacija
- Minimalni art.html (naslov + subtitle) kreiran prvi — test navigacije
  izolovano prije sadržaja (svjesna strategija: nav je čest izvor grešaka)
- nav.js: `art` dodan u i18n svih 5 jezika (Art / Kunst / Arte / Umjetnost /
  Уметност), NAV_LINKS nakon geometry, bump na **s67**
- Test: navigacija ✅, active state ✅, i18n switch ✅, footer s67 ✅

### 3. Kartica "Synesthesia" (teorijski temelj stranice)
- **Lineage tabela** — 4 reda (Abbott/Borges/Wittgenstein/Kandinsky-Scriabin),
  četvrti član istaknut; kolone: Figure / Gift / Question
- **Kandinsky · 1911** — Schönberg koncert (2. jan 1911) → Impression III →
  O duhovnom u umjetnosti; boja/oblik/zvuk = projekcije istog sadržaja
- **Scriabin · 1910** — Prometej, clavier à lumières; djelo nekompletno
  u jednom kanalu; "single sense under-samples the content"
- **Buchenberg · 2026** — "The embedding is already synesthesia": e5-large
  tačka prije čula; UMAP/melodija/otisak = sjenke iste kugle; puni krug ka
  Abbottu (Kvadrat sa dvije projekcije); hronološka fusnota (1910–11 < 1921)
- **X-Ray citat** — istaknuti serif blok ("rečenica 847")

### 4. Eksponat 1: The Tapestry
- Selektor knjiga+jezik iz books.json; Canvas grid, ćelija 8px,
  rečenica = ćelija, redoslijed čitanja; siva = "not woven yet"
- **Score mode**: finalni_score računat client-side
  (0.4×(back+ts)/2 + 0.6×judge) — postojeći tr_*.json ima sva polja,
  bb_web_export.py netaknut ✅
- **Model mode**: 5 fiksnih boja po model@temp kombinaciji
- Hover tooltip (pozicija, score, model, tekst prevoda), klik → Reader,
  resize re-render, legenda + statistika (woven/min/avg/max)

### 5. Absolute vs Relative skala (Flaviovo zapažanje)
- Problem: distribucija zbijena uz vrh — p50=0.966, p25=0.937; linearna
  skala 0.60–1.00 daje uniformno zelenu tkaninu
- Analiza distribucije (Hound HR, 3852): polovina podataka u 3% skale;
  logaritam ne pomaže (vrijednosti uz 1.0)
- Rješenje: **percentilna (rank/ECDF) skala** — boja = rang rečenice unutar
  knjige; binarna pretraga nad sortiranim finalnim scorovima
- Toggle Absolute | Relative (default Relative); tooltip dobio percentil
  (npr. "0.937 (p25)")
- Objašnjenje na stranici: "Absolute shows how good the weave is;
  Relative shows where it is thinnest" — crvena ćelija ≠ loš prevod

---

## Sljedeće

- **The Sound of Translation** — sonifikacija (Tone.js CDN provjeriti prije
  implementacije — princip kompatibilnosti!)
- **Sentence Fingerprints** — embedding → generativni otisak
- Ostalo: prijevodi hr/sr/it/de → s350, mk/bg → s51–100; about.html i18n;
  learn.html igre; web u git

---

## Git

(commit nakon snimanja)
