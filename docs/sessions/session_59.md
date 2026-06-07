# Session 59 — Web: index.html labele, learn.html refaktor + Memory + Scrambled

**Datum:** 7. jun 2026.
**Sesija:** 59
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Health check — protokol outputa

Health check se pokreće komandom:
```bash
cd /home/balsam/buchenberg && venv/bin/python src/health_check.py
```

**Važna napomena:** Sirovi output sadrži ANSI escape kodove koji se ne renderuju u chatu.
Output se formatira ručno u chatu:
- `.env` status
- PostgreSQL tabela prevoda (Knjiga / Lang / Prev / Pobj)
- Ollama Cloud: model odgovori (`gemma3:12b`, `ministral-3:14b`, `gemma4:31b`)
- NLLB keš status
- Python paketi
- Git log (zadnja 3 commita)

### 2. index.html — labele CTA dugmadi

Promijenjeno za sve jezične varijante (EN, DE, IT, HR, SR):
- `Browse translated books` → `Browse library`
- `How it works` → `About`
- `X-Ray statistics` — ostaje nepromijenjeno

### 3. learn.html — refaktor setup UX

**Stari redosljed:** knjiga → jezik → direction (manual)
**Novi redosljed:** jezik → knjiga (filtrirano)

Promjene:
- Dropdown "I want to learn" sada je prvi — prikazuje sve jezike s brojem knjiga (`Croatian — 1 book`, `Italian — 3 books`, `English — 9 books`)
- Dropdown "Book" se filtrira na knjige koje imaju prevod na odabrani jezik
- English je uvijek dostupan (sve knjige imaju EN original)
- Direction row uklonjen — automatski se određuje iz odabranog jezika
- Umjesto direction buttona: info badge (`"You will see English as context and fill in Croatian"`)
- Sentence Match dobio isti redosljed: jezik → knjiga
- English nije opcija u Matchu (Match uvijek uparuje EN ↔ prevod)

### 4. learn.html — Memory igra (treći tab)

**Mehanika:**
- Setup: jezik → knjiga (filtrirano, isti pattern)
- 5 parova = 10 kartica na tabli (grid 5×2)
- Sve kartice okrenute prema dolje sa `?`
- Klik → kartica se okreće (CSS flip animacija)
- Drugi klik → provjera para (EN ↔ prevod istog pairId)
- Tačan par → ostaju okrenute, zelena boja
- Netačan par → crveni flash, flip nazad nakon 900ms
- `memLocked` flag blokira klikove tokom animacije
- Badge na kartici: `EN` ili skraćenica jezika (prva 3 slova)

**Scoring:** broj pokušaja (manji = bolji), minimum = 5 (savršena igra)

**Rezultati:** ukupni pokušaji, parovi pronađeni

### 5. learn.html — Scrambled Sentence igra (četvrti tab)

**Mehanika:**
- Setup: jezik → knjiga (filtrirano)
- 5 rečenica po igri
- Filter: samo rečenice s ≥4 riječi
- EN rečenica prikazana kao kontekst (italic, border-left)
- Sve riječi prevoda prikazane kao klikabilni čipovi (pill shape) — pomiješane
- Klik na chip u pool → ide u "Your answer" zonu
- Klik na chip u answer zoni → vraća se u pool
- **Clear** dugme — resetuje sve u pool
- `scrMovesMade` prati broj premještanja

**Scoring:**
- +10 — tačno, bez premještanja (`scrMovesMade === 0`)
- +5 — tačno, s premještanjem
- 0 — netačno (prikazuje tačan odgovor zeleno)
- Max score: 50 poena (5 × 10)

**Rezultati:** score/50, breakdown (First try / With moves / Wrong)

### 6. Tab switch refaktor

Stara logika (if/else) zamijenjena čišćim pristupom:
```javascript
// Sakrij sve panele
document.getElementById('fillin-panels').style.display = 'none';
document.getElementById('match-panels').style.display = 'none';
document.getElementById('memory-panels').style.display = 'none';
document.getElementById('scrambled-panels').style.display = 'none';
// Prikaži odabrani
document.getElementById(which + '-panels').style.display = 'block'; // (approx)
```

---

## Stanje learn.html tabova na kraju sesije

| Tab | Igra | Status |
|-----|------|--------|
| Fill in the Blank | MC → tipkanje, hint, 10 rečenica | ✅ |
| Sentence Match | Sparivanje EN ↔ prevod, 10 parova | ✅ |
| Memory | Flip kartice, 5 parova, 10 kartica | ✅ |
| Scrambled | Slaganje pomiješanih riječi, 5 rečenica | ✅ |

---

## Ideje za buduće igre (dogovoreno, nije implementirano)

- **True or False** — EN rečenica + jedan prevod, igrač kaže tačno/netačno
- **Multiple Choice** — cijela rečenica, 4 opcije prevoda
- **First Letter** — prevod s vidljivim samo prvim slovima

---

## Arhitekturne napomene

- Sve igre dijele: `books`, `LANG_NAMES`, `fetchVersion()`, `shuffle()`, `showToast()`, `escHtml()`
- Svaka igra ima vlastiti namespace varijabli (prefiks: `match*`, `mem*`, `scr*`)
- Setup pattern je kanonski: `populateXxxLangDropdown()` → `populateXxxBooks()` → `startXxxGame()`
- `show(id)` / `hide(id)` = `display='block'` / `display='none'` — ne koristiti `display=''`
- Web fajlovi NISU u gitu (`/var/www/buchenberg/` nije u repozitorijumu) — TODO

---

## TODO (ažurirano)

1. **sr** — gemma3+ministral s221–s300, sudija --force, pobjednici
2. `ON DELETE CASCADE` na `bb_prev_recenica`
3. hr/it/de → s350
4. Ostali jezici → s101–s350
5. mk/bg → s51–s100
6. `--skip-ollama` flag u health_check.py
7. **Web fajlovi u git** — refaktor da `/var/www/buchenberg/` bude u repozitorijumu
8. **nav.html** — zajednički include za navigaciju (trenutno hardkodirano u svakoj stranici)
9. Konfigurabilni broj rečenica za sve igre (Flavio ideja — buduće proširenje)
10. Favicon
11. Relation Extraction
12. `bb_web_export.py` refaktor → `v_pobjednici`
13. README ažurirati — learn.html igre, index.html labele

---

*Flavio & Claude · Buchenberg · Sesija 59 · 7. jun 2026.*
