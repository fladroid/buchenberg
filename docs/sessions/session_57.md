# Session 57 — Learn stranica: Language Learning igra

**Datum:** 7. jun 2026.
**Sesija:** 57
**Autor:** Flavio & Claude

---

## Cilj

Implementirati novu web stranicu `learn.html` — interaktivna igra za učenje jezika iz Buchenberg korpusa, inspirisana Duolingo konceptom ali bazirana isključivo na literarnim tekstovima javne domene.

---

## Dizajn igre (dogovoreno)

### Koncepti
- **Jezik koji se uči**: strani jezik (HR, DE, IT...) ili engleski
- **Jezik učionice**: uvijek suprotan od jezika koji se uči
  - Učim HR → kontekst/hint je EN original
  - Učim EN → kontekst/hint je HR pobjednički prevod

### Mehanika — Fill in the blank
- 10 random odabranih rečenica iz pobjedničkih prevoda
- N skrivenih riječi po rečenici (N = težina)
- Igrač prvo dobija **multiple choice** (4 opcije)
- Ako pogreši na MC → mora **utipkati** tačan odgovor
- **Hint** otkriva riječ (−3 poena)

### Scoring
- 8 poena — tačno na multiple choice
- 10 poena — tačno tipkanjem
- −3 poena — hint korišten
- 0 poena — netačno

### Težina
- Easy: 1 blank po rečenici
- Medium: 2 blanka
- Hard: 3 blanka

---

## Implementacija

### Nova stranica: `learn.html`

**Struktura:**
1. **Setup panel** — odabir knjige, jezika, smjera, težine → Start Game
2. **Game panel** — progress bar, score, 10 rečenica jedna po jedna
3. **Results panel** — finalni score, breakdown (correct/wrong/hints), Play Again / New Game

**Tehnički detalji:**
- Čisti HTML/JS/CSS — bez backenda, bez novih API poziva
- Podaci iz postojećih JSON fajlova (`data/books.json`, `data/tr_{id}_{lang}.json`)
- Uklopljeno u Buchenberg dizajn (buchenberg.css, dark mode, navigacija)
- Multiple choice popup — 4 opcije od kojih je 1 tačna, 3 random iz korpusa
- Tokenizer za slavenske jezike (čćšžđ i sl.)
- `show(id)` funkcija koristi `display = 'block'` (ne `''`) zbog CSS `display:none` override

### Navigacija
`Learn` link dodan u sve postojeće stranice:
- index.html, about.html, stats.html, books.html, nlp.html, reader.html

---

## Bugovi i dijagnoza

### Bug 1: Setup panel nije vidljiv na desktopu
**Simptom:** Stranica prikazuje samo hero sekciju, setup panel ispod fold-a.
**Fix:** Smanjen hero padding (`32px → 16px`, `margin-bottom: 32px → 20px`).

### Bug 2: Game panel se ne prikazuje nakon Start Game
**Simptom:** Klik na Start Game sakriva setup ali ne prikazuje game panel.
**Uzrok:** `show(id)` postavljao `style.display = ''` (prazan string) što ne override-uje CSS rule `display: none`.
**Fix:** `show(id)` sada postavlja `style.display = 'block'`.

### Dijagnostički process
- Korišteni `alert()` pozivi da pratimo tok izvršavanja korak po korak
- Potvrđeno: fetch radi (200), books loaded (9), sel-book found — problem isključivo u CSS/JS display logici
- Greške u konzoli (`window.__chromium_devtools_metrics_reporter`, `NoteBoolLM`) su od browser ekstenzija — nisu relevantne

---

## Stanje na kraju sesije

- `learn.html` je live na https://buchenberg.opik.net/learn.html
- Testirano: Hound of the Baskervilles, Croatian, Learn Croatian, Easy — RADI ✅
- Web fajlovi NISU u gitu (Apache2 root `/var/www/buchenberg/` nije u repozitorijumu)

---

## TODO

1. Testirati sve kombinacije (knjiga × jezik × smjer × težina)
2. Testirati rezultate panel i Play Again
3. Dodati `learn.html` u git (web fajlovi refaktor)
4. **sr** — gemma3+ministral s221–s300, sudija --force, pobjednici
5. `ON DELETE CASCADE` na `bb_prev_recenica`
6. hr/it/de → s350
7. Ostali jezici → s101–s350
8. mk/bg → s51–s100
9. `--skip-ollama` flag u health_check.py
10. Favicon
11. Relation Extraction
12. README ažurirati — nove knjige + learn stranica

---

*Flavio & Claude · Buchenberg · Sesija 57 · 7. jun 2026.*
