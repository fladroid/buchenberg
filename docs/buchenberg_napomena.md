# Buchenberg — Napomena za Claude

**Datum pisanja:** 9. jun 2026.
**Autor:** Flavio & Claude
**Verzija:** 2.0

---

## Protokol rada (nepregovoriv)

**Svaka komanda — bez izuzetka — prikazuje se prije izvršavanja.**

Claude prikazuje komandu → Flavio kaže OK → tek onda se izvršava.

Važi za: foxuno komande, SQL upite, git operacije, izmjene fajlova.

---

## Checklist na početku svake sesije (redosljed fiksan)

1. Pročitati project files (`buchenberg_napomena.md` i relevantne X-Ray dokumente)
2. Pročitati README — prikazati komandu, čekati OK
3. Pročitati posljednje 3 session dokumenta — prikazati komandu, čekati OK
4. Pokrenuti health check — prikazati komandu, čekati OK

---

## Radni stil i komunikacija

- Kolegijalna komunikacija, terse stil — ravnopravni partneri
- Flavio potvrđuje s "OK", provjerava s "Proveri"
- Claude prikazuje raw output bez interpretacije; health check rezultate formatira ručno (ANSI kodovi)
- Claude ne pretpostavlja greške u Flaviovom radu bez provjere — Flavio ima jasnu strategiju
- NLLB pre-fetch je namjerna taktika (prevodi bez Ollama resursa) — nije anomalija
- Prijevodi po 50 rečenica za 4 jezika je namjerna strategija — bogatiji korpus za igre
- Na kraju svake sesije: pisati session_NN.md, ažurirati README, commitati i pushati

---

## Infrastruktura

| Komponenta | Lokacija |
|-----------|----------|
| Dev server | `foxuno` — `/home/balsam/buchenberg/` |
| Baza | PostgreSQL 17.9 u Docker `pgdb` na `balsam`, db=`bb`, user=`pgu` |
| Git | `fladroid` na GitHub, SSH key na foxuno |
| Python env | `/home/balsam/buchenberg/venv/` |
| Ollama Cloud | `api.ollama.com` — gemma3:12b, ministral-3:14b, gemma4:31b (sudija) |
| NLLB | Lokalno na foxuno — facebook/nllb-200-distilled-600M |
| Embedder | **UVIJEK** `multilingual-e5-large` (intfloat/multilingual-e5-large) — bez izuzetka |
| Web | Apache2, `/var/www/buchenberg/`, nije u gitu; source u `/home/balsam/buchenberg/` |

**Serverske komande:**
- `foxuno:run_command` — sve Python skripte, file operacije, git, log monitoring
- `balsam:run_command` — isključivo PostgreSQL via `docker exec pgdb psql -U pgu -d bb -c "..."`
- Miješanje ovih alata uzrokuje greške

---

## Pipeline

**Redosljed:** `bb_03_prevod.py → bb_08_sudija.py → bb_04_pobjednik.py → bb_05_export.py`

**Modeli (5):** gemma3:12b@0.8, gemma3:12b@0.1, ministral-3:14b@0.8, ministral-3:14b@0.1, nllb-600M@0.0

**Finalni score:** `0.4 × kompozitni + 0.6 × sudija_avg`, gdje `kompozitni = (back_score + translation_score) / 2`

**Pokretanje:**
```bash
nohup time bash run_pipeline.sh --knjiga [ID] --jezici "[lang1 lang2]" --od [start] --do [end] > logs/[logname].log 2>&1 & echo "PID: $!"
```

**Monitoring:** `tail -5 logs/[logfile].log`

**Web export** se pokreće zasebno: `venv/bin/python src/bb_web_export.py`

---

## Web portal

**Stranice:** index.html, about.html, stats.html, books.html, nlp.html, reader.html, learn.html, geometry.html

**Centralni nav:** `/var/www/buchenberg/nav.js` — ubacuje header sinhrono via document.write; mora biti prva skripta u <head>

**NER pipeline:** `bb_09_ner.py` (spaCy + gemma4:31b normalizacija)

**Cache busting:** `version.json?t=Date.now()`

---

## Knjige (Project Gutenberg)

| ID | Naslov |
|----|--------|
| 1 | The Hound of the Baskervilles |
| 5 | The Big Four |
| 8 | Frankenstein |
| 12 | Moby Dick |
| 17 | Romeo and Juliet |
| 18 | Alice's Adventures in Wonderland |
| 19 | The Strange Case of Dr Jekyll and Mr Hyde |
| 20 | Dracula |
| 21 | Flatland |

---

## Greške koje se ne smiju ponoviti

- Nikad komandu bez prikaza i OK — bez iznimaka, uključujući read-only
- `sed` za višelinijske zamjene ne radi — uvijek Python `str.replace()` via heredoc
- Uvijek `time` u `nohup` pozivima
- Float precision u PostgreSQL: `ROUND(temperatura::numeric, 4)`
- FK-safe bulk delete: `SET session_replication_role = 'replica'`
- Embedder je UVIJEK `multilingual-e5-large` — nigdje drugdje
- Server restarts nikad nisu uzrok pipeline grešaka — sve greške su code ili konfiguracija
- PostgreSQL tabele bb_knjige: kolone `id`, `naziv`, `autor` (ne `naslov`)

---

## X-Ray filozofija

Flavio je autor dokumenta "X-Ray" (v3b, 2026) — živog dokumenta koji opisuje njegovu filozofiju učenja i izgradnje sistema. Ključni pojmovi: X-Ray stav (gledanje iznutra), meta-učenje, crna kutija i sivi gradijent, emergencija, samoorganizacija, genetski algoritmi, rezilijentnost, neuroplasticitet. Inspirisan Iličem i Abotom.

Buchenberg je praktična implementacija X-Ray filozofije — pipeline koji osvetljava proces prevoda iznutra.

---

*Flavio & Claude · Buchenberg · 9. jun 2026.*
