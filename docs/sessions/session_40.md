# Session 40 — Proširenje jezičnog pokrića na 100 rečenica

**Datum:** 3. jun 2026.
**Sesija:** 40
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Provjera HR s81–s350 (nastavak sesije 39)

HR prevodi s81–s350 pokrenuti na kraju sesije 39 — provjerili smo logove i potvrdili uspješno završavanje:

- Cloud (gemma3@0.8, gemma3@0.1, ministral@0.8, ministral@0.1): 45:34 min
- NLLB: 16:54 min (paralelno)

Pokrenuti sudija i pobjednici za HR s81–s350:
- Sudija: 22:10 min (270 rečenica)
- Pobjednici: 4 sek, 270 upisano

**Distribucija pobjednika HR s81–s350:**

| Model | temp | Pobjede | % |
|-------|------|---------|---|
| gemma3 | 0.1 | 85 | 31.5% |
| gemma3 | 0.8 | 78 | 28.9% |
| ministral | 0.1 | 53 | 19.6% |
| ministral | 0.8 | 37 | 13.7% |
| nllb | 0 | 17 | 6.3% |

**Zapažanje:** gemma3@0.1 ispred gemma3@0.8 — isti pattern kao BS. Na dužim tekstovima (s81+) HR favorizuje nižu temperaturu, suprotno od prvih 80 rečenica.

---

### 2. Analiza korelacije jezika, modela i temperature

Upitom po svim jezicima i pobjednicima identificiran stabilan pattern:

| Grupa | Pobjednički model | Temperatura |
|-------|-----------------|-------------|
| Južnoslavenski (hr, bs, sr, sl) | gemma3 | 0.1 blago bolja |
| Germanski (de, nl, af) | gemma3/ministral | 0.8 bolja |
| Romanski (fr, it, es) | ministral | 0.1 bolja |

**Anomalija:** DE jedini jezik gdje ministral dosljedno pobjeđuje gemma3 — vjerovatno zbog trening podataka (Mistral AI je europski model s jakim fokusom na zapadnoeuropske jezike).

**Zaključak sesije 39+40:** Pattern je dovoljno stabilan za praktične odluke, ali uzorak je nejednak (HR/BS 350 rec vs ostali 80-100 rec).

---

### 3. Provjera stanja jezičnog pokrića

Utvrđeno da svi jezici osim HR i BS imaju samo 80 rečenica. Cilj: minimum 100 za svaki jezik.

**Jezici koji trebaju proširenje:** af, sl, sr, de, es, fr, it, nl (s81–s100, 20 rečenica svaki)

---

### 4. Prevodi s81–s100 za 7 jezičnih grupa

Napomena: Ollama Cloud dopušta samo jednu sesiju u isto vrijeme — cloud skripte se izvršavaju **striktno serijski**. NLLB (lokalni) može se pokrenuti paralelno s cloud skriptama ali ne i cloud s cloud.

Pokrenutih 5 runova serijski:

| Run | Model | Temp | Trajanje |
|-----|-------|------|---------|
| 1 | gemma3:12b | 0.8 | 6:09 min |
| 2 | gemma3:12b | 0.1 | 6:11 min |
| 3 | ministral-3:14b | 0.8 | 4:27 min |
| 4 | ministral-3:14b | 0.1 | 4:56 min |
| 5 | nllb-600M | — | 7:55 min |

**Napomena:** Inicijalni pokušaj paralelnog pokretanja svih 5 procesa odjednom nije uspio — samo gemma3@0.8 je upisao podatke, ostali logovi nisu ni nastali. Uzrok: konflikt na Ollama Cloud API-ju. Rješenje: striktno serijsko izvršavanje.

---

### 5. Sudija i pobjednici s81–s100

Sudija za svih 8 jezika (af, sl, sr, de, es, fr, it, nl), s81–s100:
- Trajanje: 11:29 min (160 rečenica)

Pobjednici: 4 sek, 160 upisano (8 × 20).

---

## Stanje baze na kraju sesije

| Jezik | Rečenica | Status |
|-------|----------|--------|
| bs | 350 | ✅ prevod + sudija + pobjednici |
| hr | 350 | ✅ prevod + sudija + pobjednici |
| af | 100 | ✅ prevod + sudija + pobjednici |
| de | 100 | ✅ prevod + sudija + pobjednici |
| es | 100 | ✅ prevod + sudija + pobjednici |
| fr | 100 | ✅ prevod + sudija + pobjednici |
| it | 100 | ✅ prevod + sudija + pobjednici |
| nl | 100 | ✅ prevod + sudija + pobjednici |
| sl | 100 | ✅ prevod + sudija + pobjednici |
| sr | 100 | ✅ prevod + sudija + pobjednici |

---

## Ključni uvidi sesije

- **Ollama Cloud = jedna sesija** — nikad pokretati više cloud skripti paralelno. NLLB može paralelno jer je lokalni.
- **Temperatura pattern po jezičnoj grupi** — potvrđen na većem uzorku:
  - Južnoslavenski → gemma3, temp 0.1
  - Germanski → gemma3/ministral, temp 0.8
  - Romanski → ministral, temp 0.1
- **gemma3@0.1 vs 0.8 za HR** — na s1–s80 dominira 0.8, na s81–s350 dominira 0.1. Tekstualni kontekst mijenja optimalnu temperaturu.

---

## Otvoreno za sljedeće sesije

1. **Prikaz na Apache2 serveru** (foxuno) — web vizualizacija pipeline rezultata
2. **Proširenje na s101–s350** za 7 jezika (af, sl, sr, de, es, fr, it, nl)
3. **Export** — `bb_05_export.py` za sve jezike s dovoljno rečenica
4. **README update** — reflektovati novo stanje (10 jezika, pokriće)

---

## Git

- Commit: `session 40: HR s81-350 završen, 7 jezika prošireno na 100 rečenica, analiza temperatura po jezičnim grupama`


---

## Dodatak — Web stranica (Apache2)

### Infrastruktura (zatečeno stanje)
- Apache2 aktivan na `buchenberg.opik.net`, HTTPS s Let's Encrypt certifikatima
- DocumentRoot: `/var/www/buchenberg/`
- Stari fajlovi arhivirani u `/var/www/buchenberg/BBOLD/`

### JSON export
Nova skripta `src/bb_web_export.py` generira statičke JSON fajlove:
- `data/books.json` — katalog knjiga i dostupnih prijevoda
- `data/tr_{knjiga_id}_{lang}.json` — pobjednički prevodi po jeziku

### Web stranica (`index.html`)
Wikipedia-inspirisan dizajn. Funkcionalnosti:
- Sidebar: odabir knjige → lista prijevoda sa zastavicama
- Čitač: svaka rečenica u novom redu, superscript numeracija
- Toggle: prikaz originalnog engleskog teksta lijevo, prijevod desno
- Hover: koji model je pobijedio za tu rečenicu
- Score info: avg translation_score i avg judge u toolbaru
- Infobox: autor, jezik, broj rečenica, link na Project Gutenberg
- **Multijezički UI**: EN/DE/IT/HR/SR — labeli u realnom vremenu

### Srpska ćirilica
Nova skripta `src/bb_sr_cirilica.py`:
- Transliterira sve srpske prevode latinica → ćirilica u bazi
- Idempotentna (tekst već u ćirilici se ne mijenja)
- Digrame (lj→љ, nj→њ, dž→џ, dj→ђ) se obrađuju ispravno
- 340 prevoda konvertovano
- `--dry-run` mod za provjeru bez upisa

### Git commit
`b1c2160`: `session 40: web export skripta, SR cirilica transliteracija, Apache stranica`
