# Session 44 — Health check bb baza, web poboljšanja, Frankenstein IT

**Datum:** 4. jun 2026.
**Sesija:** 44
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Health check — migracija na bb bazu

`health_check.py` je čitao stari pipeline (`buchenberg` baza — `books`, `sentences`, `test_results`, `ga_results`). Migriran na `bb` bazu.

**Izmjene:**
- Sekcija 2: čita `bb_knjige`, `bb_recenice`, `bb_prevodi_recenica`, `bb_prev_recenica`
- Prikazuje stanje prevoda po knjizi i jeziku (Prev / Pobj kolone)
- Sekcija 6 (`test_registry.yaml`) uklonjena — pripada starom pipelinu
- Ollama modeli: dodan `gemma4:31b` kao sudija
- DB konekcija: hardcodovana na `bb` bazu

**Greška pri implementaciji:** SQL upit koristio pogrešne nazive kolona (`prevod_knjige_id` umjesto `prevodi_knjige_id`, `recenica_id` umjesto `prevodi_recenica_id`). Ispravljeno iterativno kroz provjeru `\d` sheme.

**Stanje prevoda u health checku:**
```
Knjiga                               Lang   Prev   Pobj
Frankenstein; or, the Modern Prome     ro    100    100
The Big Four                           pt    100    100
The Hound of the Baskervilles          af    100    100
                                       bs    350    350
                                       de    100    100
                                       es    100    100
                                       fr    100    100
                                       hr    350    350
                                       it    100    100
                                       nl    100    100
                                       pt    100    100
                                       ro    100    100
                                       sl    100    100
                                       sr    100    100
```

---

### 2. Strategija denormalizovanih viewova — dokumentovana u README

Usvojen princip: sve skripte, reportovi i web export koriste viewove umjesto direktnih JOINova.

**Postojeći viewovi:**
- `v_prevodi` — svi prevodi, flat prikaz s modelom/jezikom/embedderom/scoreovima
- `v_pobjednici` — samo pobjedničke rečenice, isti format

**Dodat u README sekcija 5** — opis viewova, princip, primjeri SQL upita, napomena da novi reportovi idu isključivo kroz viewove.

---

### 3. Web stranica — tri poboljšanja

#### 3a. Prikaz svih originalnih rečenica

**`bb_web_export.py`** — dodata `get_all_sentences()` funkcija koja generira `orig_<knjiga_id>.json` s kompletnim originalnim tekstom knjige.

**`index.html`** — "Original" stavka na vrhu jezičnog menija (EN, sve rečenice knjige). Klik učitava `orig_<id>.json` i prikazuje samo engleski tekst bez toolbar-a.

#### 3b. Jezici sortirani po abecedi

`renderLangList()` sortira jezike po nativnom nazivu (`LANG_NAMES_NATIVE`) prije renderiranja. Jedna linija — `langs.sort((a,b) => na.localeCompare(nb))`.

#### 3c. Paralelni prikaz — neprevedene rečenice

**`bb_web_export.py`** — `tr_<id>_<lang>.json` sada sadrži **sve rečenice knjige**, ne samo prevedene. Neprevedene imaju `"translated": false`.

**`index.html`** — neprevedene rečenice:
- Lijeva kolona (original): isti font i boja kao prevedene (`sentence-translation` klasa umjesto `sentence-original`)
- Desna kolona (prevod): prazna
- Uklonjen `opacity: 0.45` efekt

---

### 4. Frankenstein IT — s1–s100

| Run | Model | Temp | Trajanje |
|-----|-------|------|---------|
| 1 | gemma3:12b | 0.8 + 0.1 | 9:43 min |
| 2 | nllb-600M | 0.0 | 6:47 min (paralelno) |
| 3 | ministral-3:14b | 0.8 + 0.1 | 6:43 min |
| Sudija | gemma4:31b | 0.0 | 4:02 min |

**Napomena:** ministral nije startao pri prvom pokretanju (pokrenut istovremeno s NLLB — nohup nije kreirao log fajl). Pokrenut ručno drugi put.

**Distribucija pobjednika IT (Frankenstein, s1–s100):**

| Model | Temp | Pobjede | % |
|-------|------|---------|---|
| gemma3 | 0.8 | 34 | 34% |
| gemma3 | 0.1 | 21 | 21% |
| ministral | 0.1 | 20 | 20% |
| ministral | 0.8 | 15 | 15% |
| nllb | 0.0 | 10 | 10% |

**Zapažanje:** IT na Frankenstein — gemma3 dominira sa 55%, što je konzistentno s IT na Houndu (35%). Pattern za IT je stabilan.

---

## Stanje baze na kraju sesije

| Knjiga | ID | Jezik | Rečenice | Status |
|--------|-----|-------|----------|--------|
| Hound | 1 | bs, hr | 350 | ✅ |
| Hound | 1 | af, de, es, fr, it, nl, sl, sr, pt, ro | 100 | ✅ |
| Big Four | 5 | pt | 100 | ✅ |
| Frankenstein | 8 | ro, it | 100 | ✅ novi: it |

---

## Otvoreno za sljedeće sesije

1. Proširenje Hound — svih 12 jezika na s101–s350
2. Proširenje PT (Big Four) — s101–s350
3. Proširenje RO+IT (Frankenstein) — s101–s350
4. Refaktorisati `bb_web_export.py` da koristi `v_pobjednici` view
5. README update po potrebi

---

## Git commits ove sesije

- `health_check: prebačen na bb bazu, stanje prevoda po knjizi/jeziku`
- `README: viewovi i strategija denormalizacije, stanje prevoda sesija 44`
- `bb_web_export: orig_<id>.json, sve recenice u tr JSON, jezici sortirani po abecedi`

---

*Flavio & Claude · Buchenberg · Sesija 44 · 4. jun 2026.*
