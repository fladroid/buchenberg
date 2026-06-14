# Session 76 — Lang dropdown, footer refactor, about Project info

**Datum:** 14. jun 2026.
**Sesija:** 76
**Autor:** Flavio & Claude

---

## Što je urađeno

### 1. Checklist (standardni)
- Project files pročitani (buchenberg_napomena_new.md, X-Ray SR/EN)
- README pročitan (V3, s75)
- Sessions 73–75 pročitane
- Health check: sve zeleno — 38.333 rečenica, 132.128 prevoda (+8.000 od s75), 8.602 pobjednika
- Git: buchenberg ba54f4e, buchenweb 66ca79e

### 2. Lang dropdown
Zamijenili 5 `bb-lang-btn` dugmadi s `<select id="bb-lang-select">` u nav.js.

- `buildHeaderHTML()`: `#bb-ui-lang-bar` → `<select>` s 5 opcija (EN default)
- Listener: `change` event umjesto `click` po dugmadima
- CSS: uklonjen `#bb-ui-lang-bar`, `.bb-lang-btn` → novi `#bb-lang-select` stil
- Mobile breakpoint: `.bb-lang-btn` → `#bb-lang-select`

### 3. Footer refactor
Footer sadržaj premješten iz HTML fajlova u nav.js.

- Sve 9 HTML stranice: `<div id="bb-footer">` ostaje prazan
- nav.js: `footer.innerHTML` renderira "Buchenberg · Open-source MT pipeline · s76 (14 Jun 2026)"
- Vanjski linkovi (Gutenberg, GitHub) uklonjeni iz footera svake stranice

### 4. about.html — Project info infobox
- Gornji infobox "Project info": zamijenjen stari generički GitHub link s dva specifična reda:
  - Source: github.com/fladroid/buchenberg (pipeline)
  - Web: github.com/fladroid/buchenweb (web portal)
  - Books: Project Gutenberg — public domain
- Uklonjen dupli "Project Info" blok koji je greškom bio dodan na dno stranice

### 5. nav.js → s76 (14 Jun 2026)

### 6. buchenweb commit
`62cd5cd` — 11 fajlova, 49 insertions, 111 deletions

---

## Filozofska napomena
Višejezičnost UI-ja identifikovana kao neizgovoreni prioritet projekta koji propagira malofrekventne jezike. Ispravka greške koja nije bila koncepcijski opisana od početka. Pouka: višejezičnost treba biti arhitekturalna odluka od dana nula.

---

## Sljedeće (kumulativno)

### i18n (novi prioritet)
- **Infrastruktura**: centralizacija lang logike u BB_NAV — ukloniti lokalni `uiLang`/`t()`/listener iz svih stranica
- **Prijevodi**: proširiti NAV_I18N u nav.js s DE/IT/HR/SR stringovima za sve stranice
- Redosljed: stats.html → books.html → index.html → about.html → art.html → geometry.html → nlp.html → learn.html
- reader.html ima vlastiti i18n sistem — ostaviti kao je

### Pipeline
- Prijevodi: hr/sr/it/de → s350; mk/bg → s51–s100 (Ollama reset ~18h)
- naturalness_score retroaktivno punjenje

### Web
- Cache-Control za js/css (.htaccess) — nizak prioritet
- learn.html nove igre — nizak prioritet
- about.html sadržajni i18n

---

*Flavio & Claude · Buchenberg · sesija 76 · 14. jun 2026.*
