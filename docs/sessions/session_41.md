# Session 41 — The Big Four: nova knjiga, PT prevod, workflow dokumentacija

**Datum:** 3. jun 2026.
**Sesija:** 41
**Autor:** Flavio & Claude

---

## Cilj sesije

Obnova i dokumentacija kompletnog Buchenberg workflow-a na primjeru nove knjige:
- **The Big Four** — Agatha Christie (eBook #70114)
- **Jezik:** portugalski (pt)
- **Raspon:** s1–s100

Sesija je služila i kao referentna dokumentacija za novog saradnika koji nije upoznat s projektom.

---

## Kompletni workflow — korak po korak

### Korak 1: Inicijalizacija sesije (obavezan protokol)

Svaka sesija počinje sa:

```bash
# 1. Čitanje README
cat /home/balsam/buchenberg/README.md

# 2. Čitanje posljednjih 3 session dokumenta
cat /home/balsam/buchenberg/docs/sessions/session_38.md
cat /home/balsam/buchenberg/docs/sessions/session_39.md
cat /home/balsam/buchenberg/docs/sessions/session_40.md

# 3. Health check
cd /home/balsam/buchenberg && venv/bin/python src/health_check.py
```

**Protokol komandi:** Claude uvijek prikazuje komandu prije izvršavanja. Bez izuzetka. Flavio kaže OK → tek onda se izvršava.

---

### Korak 2: Provjera stanja lookup tabela

Prije dodavanja nove knjige uvijek provjeriti da li su potrebni jezici i modeli već u bazi:

```bash
docker exec pgdb psql -U pgu -d bb \
  -c "SELECT * FROM bb_jezik ORDER BY kod;" \
  -c "SELECT * FROM bb_modeli ORDER BY naziv, temperatura;" \
  -c "SELECT * FROM bb_knjige;"
```

**Zatečeno stanje:**
- `pt` (portugalski) — ✅ već u `bb_jezik` (id=13)
- Svi potrebni modeli prisutni: gemma3@0.1, gemma3@0.8, ministral@0.1, ministral@0.8, nllb@0

---

### Korak 3: Skidanje HTML knjige s Project Gutenberga

```bash
cd /home/balsam/buchenberg && mkdir -p books
wget -O books/the_big_four.html "https://gutenberg.org/cache/epub/70114/pg70114-images.html"
```

**Provjera strukture HTML-a** — obavezno prije parsiranja:

```bash
cd /home/balsam/buchenberg && venv/bin/python3 -c "
from bs4 import BeautifulSoup
with open('books/the_big_four.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')
tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4'])[:30]
for i, t in enumerate(tags):
    print(f'[{i:02d}] <{t.name}> {t.get_text(strip=True)[:120]}')
"
```

**Zatečena struktura The Big Four:**
- s1–s3: naslov, autor, izdavač (metadata)
- s4–s10: copyright i izdavačke napomene (metadata specifične za ovu ediciju)
- s11: naziv poglavlja ("1. THE UNEXPECTED GUEST")
- s12+: pravi tekst knjige

Parser `bb_02_insert_knjiga.py` koristi spaCy sentence splitter na `<p>` tagove i direktno uzima `<h*>` tagove kao zasebne rečenice — identična struktura kao Hound, radi bez izmjena.

---

### Korak 4: Upisivanje knjige u bazu

#### 4a. Dodavanje knjige u `bb_02_insert_knjiga.py`

Skripta ima hardcodovanu `KNJIGE` listu. Svaka nova knjiga se dodaje ovdje:

```python
KNJIGE = [
    {
        "naziv":        "The Hound of the Baskervilles",
        "autor":        "Arthur Conan Doyle",
        "gutenberg_id": "2852",
        "html":         "books/hound_of_the_baskervilles/raw/hound.html",
    },
    {
        "naziv":        "The Big Four",
        "autor":        "Agatha Christie",
        "gutenberg_id": "70114",
        "html":         "books/the_big_four.html",
    },
]
```

#### 4b. Bug fiksiran u ovoj sesiji — UNIQUE constraint

**Problem:** `bb_knjige.gutenberg_id` nije imao UNIQUE constraint. `ON CONFLICT DO NOTHING` u skripti je bio beskoristan — dupli insert je prošao tiho, Hound je upisan dvaput.

**Fix — constraint u bazi:**
```sql
ALTER TABLE bb_knjige
ADD CONSTRAINT bb_knjige_gutenberg_id_unique UNIQUE (gutenberg_id);
```

**Fix — skripta:**
```python
# Staro (pogrešno):
ON CONFLICT DO NOTHING

# Novo (ispravno):
ON CONFLICT (gutenberg_id) DO NOTHING
```

#### 4c. Pokretanje skripte

```bash
cd /home/balsam/buchenberg && venv/bin/python src/bb_02_insert_knjiga.py
```

**Očekivani output:**
```
Knjiga već postoji id=1: The Hound of the Baskervilles
  Rečenice već postoje (3852), preskačem.
Nova knjiga id=5: The Big Four
  Parsirano: 5055 rečenica
  Upisano: 5055 rečenica
Gotovo.
```

**Verifikacija:**
```bash
docker exec pgdb psql -U pgu -d bb -c "SELECT * FROM bb_knjige ORDER BY id;"
docker exec pgdb psql -U pgu -d bb -c "SELECT pozicija, tekst FROM bb_recenice WHERE knjiga_id = 5 ORDER BY pozicija LIMIT 15;"
```

---

### Korak 5: Prevođenje

#### Principi

- **Konzistentnost:** uvijek koristiti iste modele i temperature za sve jezike — omogućava poređenje
- **Modeli:** gemma3@0.8, gemma3@0.1, ministral@0.8, ministral@0.1 (cloud), nllb@0 (lokalni)
- **Serijski vs paralelni:** Ollama Cloud dopušta **samo jednu sesiju u isto vrijeme** — cloud skripte se izvršavaju striktno serijski. NLLB je lokalni CPU i može se pokrenuti paralelno s cloud skriptama.
- **Logovanje:** uvijek koristiti `PYTHONUNBUFFERED=1 nohup time` — trajanje mora biti vidljivo u logu

#### Redoslijed pokretanja

```bash
# Run 1 — gemma3@0.8
PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_03_prevod.py \
  --knjiga 5 --od 1 --do 100 --model "gemma3:12b" --temp 0.8 \
  --embedder "multilingual-e5-large" --jezici pt \
  > logs/bigfour_pt_gemma3_08.log 2>&1 &

# Run 2 — gemma3@0.1 (nakon što Run 1 završi)
PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_03_prevod.py \
  --knjiga 5 --od 1 --do 100 --model "gemma3:12b" --temp 0.1 \
  --embedder "multilingual-e5-large" --jezici pt \
  > logs/bigfour_pt_gemma3_01.log 2>&1 &

# Run 3 — NLLB paralelno s Run 2 (lokalni, ne ometa cloud)
PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_03_prevod.py \
  --knjiga 5 --od 1 --do 100 --model "nllb-600M" --temp 0.0 \
  --embedder "multilingual-e5-large" --jezici pt \
  > logs/bigfour_pt_nllb.log 2>&1 &

# Run 4 — ministral@0.8 (nakon Run 2)
PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_03_prevod.py \
  --knjiga 5 --od 1 --do 100 --model "ministral-3:14b" --temp 0.8 \
  --embedder "multilingual-e5-large" --jezici pt \
  > logs/bigfour_pt_ministral_08.log 2>&1 &

# Run 5 — ministral@0.1 (nakon Run 4)
PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_03_prevod.py \
  --knjiga 5 --od 1 --do 100 --model "ministral-3:14b" --temp 0.1 \
  --embedder "multilingual-e5-large" --jezici pt \
  > logs/bigfour_pt_ministral_01.log 2>&1 &
```

**Provjera toka:**
```bash
tail -5 logs/bigfour_pt_gemma3_08.log
```

**Trajanje (referentne vrijednosti za 100 rečenica, 1 jezik):**

| Model | Trajanje |
|-------|---------|
| gemma3@0.8 | 2:50 min |
| gemma3@0.1 | 2:49 min |
| ministral@0.8 | 3:04 min |
| ministral@0.1 | 3:04 min |
| nllb@0 | 4:56 min (paralelno) |

---

### Korak 6: Sudija

Gemma4:31b kao blind sudija — ocjenjuje svaki prevod po 3 kriterija (grammar, naturalness, fidelity) na skali 0.0–1.0. Deterministički (temperature=0.0).

```bash
PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_08_sudija.py \
  --knjiga 5 --od 1 --do 100 --jezici pt \
  > logs/bigfour_pt_sudija.log 2>&1 &
```

**Provjera:**
```bash
tail -5 logs/bigfour_pt_sudija.log
```

**Trajanje:** ~7 min za 100 rečenica × 5 modela = 500 ocjena.

---

### Korak 7: Pobjednici

Formula: `finalni_score = 0.4 × kompozitni + 0.6 × sudija_avg`
gdje je `kompozitni = (score + translation_score) / 2`.

```bash
cd /home/balsam/buchenberg && venv/bin/python src/bb_04_pobjednik.py \
  --knjiga 5 --od 1 --do 100 --jezici pt
```

**Distribucija pobjednika PT (The Big Four, s1–s100):**

| Model | Temp | Pobjede | % |
|-------|------|---------|---|
| gemma3 | 0.8 | 27 | 27% |
| ministral | 0.1 | 22 | 22% |
| gemma3 | 0.1 | 22 | 22% |
| ministral | 0.8 | 18 | 18% |
| nllb | 0 | 11 | 11% |

**Zapažanje:** PT se nije ponašao kao tipični "romanski pattern" (gdje ministral@0.1 dominira). gemma3@0.8 vodi — potvrda da je važno koristiti sve temperature umjesto pretpostavljenog optimalnog modela.

---

### Korak 8: Web export i publikovanje

```bash
cd /home/balsam/buchenberg && venv/bin/python src/bb_web_export.py
```

Skripta iterira kroz **sve knjige** i **sve jezike** u bazi i generiše:
- `/var/www/buchenberg/data/books.json` — katalog knjiga
- `/var/www/buchenberg/data/tr_{knjiga_id}_{lang}.json` — prevodi po knjizi i jeziku

Apache2 odmah servira novi sadržaj — nema potrebe za restartem.

**Verifikacija:**
```bash
curl -s https://buchenberg.opik.net/data/books.json
```

---

## Stanje baze na kraju sesije

| Knjiga | ID | Jezik | Rečenice | Status |
|--------|-----|-------|----------|--------|
| The Hound of the Baskervilles | 1 | bs, hr | 350 | ✅ |
| The Hound of the Baskervilles | 1 | af, de, es, fr, it, nl, sl, sr | 100 | ✅ |
| The Big Four | 5 | pt | 100 | ✅ |

---

## Bugovi fiksirani u ovoj sesiji

### 1. `bb_knjige` — nedostajao UNIQUE constraint na `gutenberg_id`

**Simptom:** Pokretanje `bb_02_insert_knjiga.py` na bazi koja već sadrži Hound upisalo je dupli red jer `ON CONFLICT DO NOTHING` nije imao na čemu da detektuje konflikt.

**Fix:**
```sql
ALTER TABLE bb_knjige
ADD CONSTRAINT bb_knjige_gutenberg_id_unique UNIQUE (gutenberg_id);
```
```python
# bb_02_insert_knjiga.py
ON CONFLICT (gutenberg_id) DO NOTHING  # eksplicitni conflict target
```

---

## Otvoreno za sljedeće sesije

1. **Proširenje PT** — s101–s350 (ili cijela knjiga)
2. **Novi jezici za The Big Four** — po istom workflow-u
3. **Proširenje Hound** — preostalih 7 jezika na s101–s350
4. **README update** — dokumentovati novi workflow i bug fix

---

## Git

- Commit: `session 41: The Big Four dodana, PT prevod s1-100, bb_knjige UNIQUE fix, web export ažuriran`

---

*Flavio & Claude · Buchenberg · Sesija 41 · 3. jun 2026.*
