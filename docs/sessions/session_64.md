# Session 64 — Lineage timeline, Borges/Wittgenstein kartice, verzioniranje

**Datum:** 10. jun 2026.
**Autor:** Flavio & Claude

---

## Urađeno

### 1. Checklist (standardni)
- Memorija osvježena, README pročitan, sessions 61–63 pročitani
- Health check: sve zeleno — 38.333 rečenica, 97.486 prevoda, 8.352 pobjednika
- Bez novih prevoda od s63; Flavio pokrenuo bb_web_export.py — portal ažuriran
  (tr_21_de/it sada 500 na webu)

### 2. Lekcija o komunikaciji
- "Prikaži sve rezultate" znači SVE — Claude sažeo health check (grupisao jezike,
  izostavio liste) umjesto kompletnog prikaza. Uzrok: refleks kompresije pregazio
  eksplicitan zahtjev
- Dogovor: Flavio pokreće health check sam u terminalu (vidi pun output bez ANSI
  problema) i traži od Claudea komentar/interpretaciju

### 3. NLLB misterija razjašnjena
- Health check prijavljivao keš `nllb-200-distilled-1.3B`, dokumentacija kaže 600M
- HF keš sadrži TRI NLLB modela: 3.3B, distilled-1.3B, distilled-600M (ostaci
  ranijih eksperimenata)
- `bb_03_prevod.py` linija 53: `NLLB_MODEL_NAME = "facebook/nllb-200-distilled-600M"`
  hardkodirano — svi prevodi konzistentno rađeni sa 600M ✅
- Health check samo pattern-matchuje keš — prijavljuje pogrešan model
- Odluka: ostaviti sve kako je (ni čišćenje keša ni fix health checka)

### 4. geometry.html — "Two readings of this space" (723 → 802 linija)
- Kartica **"The Library and the Compass"** (Borges 1941): embedding prostor kao
  kontinuirana Babelska biblioteka; informacija bez selekcije je šum; Buchenberg =
  bibliotekar s kompasom; zato sudija nosi 60%; Pierre Menard (1939) kao precizna
  definicija problema prevođenja
- Kartica **"Meaning as Use"** (Wittgenstein 1953): cosinus = kvantifikovana
  porodična sličnost; UMAP klasteri = porodice značenja; back-translation testira
  preživljavanje značenja, ne forme; naturalness = kompetencija u jezičkoj igri
- Završna napomena: Abbott (geometrija) + Borges (semantika) + Wittgenstein (most);
  Flatland = knjiga 21 u korpusu

### 5. about.html — tri dodatka (226 → 391 linija)
- **Lineage D3 timeline** (nakon Key learnings): FORM linija (crvena) Tractatus →
  Georgetown → Chomsky → ALPAC ✕ (krah); USE linija (zelena) Borges → Investigations
  → Firth → IBM Candide → word2vec → Attention → NLLB → Buchenberg (presjek);
  isprekidana Chomsky→NLLB ("weak vindication"); klik na čvor → opis;
  responsive: vertikalan ispod 620px; D3 v7 CDN
- **"LLM vs. NLLB — two different kinds of machine"** (ispod Models tabele):
  generalista vs specijalista, temperatura vs determinizam, 12B vs 600M,
  zašto takmičenje funkcioniše
- **Philosophy infobox**: X-Ray stav + potpis "— Flavio"

### 6. nav.js — verzioniranje + autorstvo (svih 8 stranica)
- `BB_VERSION = 's64'`, `BB_VERSION_DATE = '10 Jun 2026'` — konstante na vrhu
- Footer injekcija na DOMContentLoaded:
  "Flavio · X-Ray approach to machine translation · s64 (10 Jun 2026)"
- `window.BB_NAV.version` dostupan svim stranicama
- **Novi ritual kraja sesije: bump BB_VERSION u nav.js**

---

## Sljedeće

- Proširenje prijevoda: hr/sr/it/de → s350, mk/bg → s51–100
- about.html prevesti na ostale jezike (trenutno EN)
- learn.html nove igre (True/False, Multiple Choice, First Letter)
- Web fajlovi u git (dugogodišnji TODO)

---

## Git

(commit nakon snimanja)
