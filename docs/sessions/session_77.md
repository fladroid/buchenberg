# Session 77 — i18n refactor: centralizacija u nav.js

**Datum:** 14. jun 2026.
**Sesija:** 77
**Autor:** Flavio & Claude

---

## Što je urađeno

### 1. Checklist (standardni)
- Project files pročitani (buchenberg_napomena_new.md, X-Ray SR/EN)
- README pročitan (V3, s76)
- Sessions 74–76 pročitane
- Health check: sve zeleno — 38.333 rečenica, 132.308 prevoda, 8.602 pobjednika
- Git: buchenberg b70218f, buchenweb 62cd5cd

### 2. Diskusija o arhitekturi i18n
- Odluka: svi prijevodi u nav.js (jedan fajl, jedan mehanizam, bez async fetch)
- Alternativa (i18n/page.json) odbijena kao over-engineering za sadašnji opseg
- nav.js trenutno ~31KB — prihvatljivo
- Filozofska napomena: srpska ćirilica kao arhitekturalna odluka, ne samo estetska

### 3. i18n refactor — sve stranice

**Princip:** ukloniti lokalni `I18N`/`uiLang`/`t()`/`applyI18n()`/listener iz svake stranice. Stranica koristi `BB_NAV.t('key')` i `BB_NAV.onLangChange`.

**nav.js** — dodani ključevi za 5 jezika (EN/DE/IT/HR/SR):
- `stats_*` — 21 ključ (naslovi, podnaslovi, kolone tabela)
- `books_*` — 14 ključeva (naslovi, dugmad, word cloud stringovi)
- `index_*` — 16 ključeva + dugi HTML sadržaj (hero_desc, how_desc, pillar_*, opensource)
- `nlp_*` — 20 ključeva (naslovi, labele, tabele, entity tip labele)

**Stranice — potpun refactor:**
- `stats.html` — lokalni I18N uklonjen; `applyPageI18n()` + `BB_NAV.onLangChange`; tabele renderuju kolone via `BB_NAV.t()`
- `books.html` — lokalni I18N uklonjen; `t()` wrapper koji dodaje `books_` prefix; `applyPageI18n()` + `BB_NAV.onLangChange`
- `index.html` — lokalni I18N uklonjen (uključujući dugi HTML sadržaj); `applyPageI18n()` + `BB_NAV.onLangChange`
- `nlp.html` — lokalni I18N uklonjen; `applyPageI18n()` + `BB_NAV.onLangChange`; MutationObserver za theme redraw zadržan

**Stranice — hook dodan (sadržajni prijevodi TODO):**
- `about.html` — lokalni I18N uklonjen, prazan `BB_NAV.onLangChange` hook
- `art.html` — prazan hook dodan
- `geometry.html` — prazan hook dodan
- `learn.html` — prazan hook dodan

**Preskočeno namjerno:**
- `reader.html` — ima vlastiti kompletni i18n sistem, ostaviti kao je

### 4. nav.js → s77 (14 Jun 2026)

### 5. buchenweb commit
`7c6be82` — 9 fajlova, 431 insertions, 430 deletions

---

## Stanje na kraju sesije

- buchenweb: commit 7c6be82, git čist
- buchenberg: nepromijenjen
- Corpus: 38.333 / 132.308 / 8.602 — nepromijenjen

---

## Sljedeće (kumulativno)

### i18n (nastavak)
- `about.html` sadržajni prijevodi (DE/IT/HR/SR) — velik posao, posebna sesija
- `art.html`, `geometry.html`, `learn.html` sadržajni prijevodi — nizak prioritet

### Pipeline
- Prijevodi: hr/sr/it/de → s350; mk/bg → s51–s100
- naturalness_score retroaktivno punjenje

### Web
- Cache-Control za js/css (.htaccess) — nizak prioritet
- learn.html nove igre — nizak prioritet

---

*Flavio & Claude · Buchenberg · sesija 77 · 14. jun 2026.*
