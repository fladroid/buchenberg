# Session 38 — Buchenberg

**Datum:** 2. jun 2026.
**Sesija:** 38
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Popunjavanje prevoda za DE i FR

Na početku sesije DE i FR jezici nisu imali kompletne prevode:

| Jezik | Model | MiniLM | e5-large |
|-------|-------|--------|----------|
| de | gemma3 | ✅ | ❌ |
| de | ministral | ✅ | ❌ |
| de | nllb | ❌ | ❌ |
| fr | gemma3 | ❌ | ✅ |
| fr | ministral | ❌ | ✅ |
| fr | nllb | ✅ | ✅ |

Pokrenuti runovi:
- NLLB + e5-large za DE
- NLLB + MiniLM za DE
- gemma3 + e5-large za DE (temp=0.5)
- ministral + e5-large za DE (temp=0.5)
- gemma3 + MiniLM za FR (temp=0.5)
- ministral + MiniLM za FR (temp=0.5)

Rezultat: sva 4 jezika (hr, it, fr, de) imaju kompletne prevode za sva 3 modela × 2 embeddera.

---

### 2. Sudija i pobjednici za DE i FR (s1–s40)

Pokrenuti `bb_08_sudija.py` i `bb_04_pobjednik.py` za DE i FR, s1–s40.

**Distribucija pobjednika s1–s40:**

| Jezik | gemma3 | ministral | nllb |
|-------|--------|-----------|------|
| hr | 25 | 11 | 4 |
| it | 21 | 17 | 2 |
| fr | 24 | 14 | 2 |
| de | 16 | 19 | 5 |

DE je jedini jezik gdje ministral vodi. Svi LLM pobjednici na DE bili su temp=0.5 jer to je bila jedina dostupna temperatura za e5-large embedder.

---

### 3. Kreirani denormalizovani viewovi

Kreirani su dva SQL viewa koji eliminišu potrebu za ručnim JOIN-ovima:

**`v_prevodi`** — svi prevodi sa svim detaljima:
```sql
SELECT jezik, model, temperatura, embedder, s_id, original,
       prevod, back_translation, score, translation_score,
       kompozitni, sudija_grammar, sudija_naturalness,
       sudija_fidelity, sudija_avg, finalni_score, created_at
FROM v_prevodi
WHERE jezik = 'hr' AND s_id = 5
ORDER BY finalni_score DESC;
```

**`v_pobjednici`** — samo pobjednici sa svim detaljima:
```sql
SELECT * FROM v_pobjednici WHERE jezik = 'de' ORDER BY s_id;
```

`finalni_score` je automatski izračunat u viewu: `0.4 × kompozitni + 0.6 × sudija_avg`.

---

### 4. Istraživanje temperature: 0.8 za DE

Opaženo da su svi DE pobjednici s1–s40 bili temp=0.5 jer temp=0.8 još nije bio dostupan za e5-large. Pokrenuti gemma3 i ministral za DE s temp=0.8:

**Rezultat — distribucija pobjednika DE s1–s40 nakon dodavanja temp=0.8:**

| Model | temp=0.5 | temp=0.8 | Ukupno |
|-------|----------|----------|--------|
| ministral | 8 | 13 | 21 |
| gemma3 | 5 | 10 | 15 |
| nllb | — | — | 4 |

**Zaključak:** temp=0.8 dominira (23 od 40 pobjednika). Viša temperatura daje prirodniji, manje mehanički prijevod.

---

### 5. Istraživanje temperature: 0.1 za sva 4 jezika (s1–s40)

Dodani novi modeli u `bb_modeli`:
```sql
INSERT INTO bb_modeli (naziv, temperatura) VALUES
  ('gemma3:12b', 0.1),
  ('ministral-3:14b', 0.1);
```

Pokrenuti gemma3 i ministral s temp=0.1, e5-large, sva 4 jezika.

**Distribucija pobjednika s1–s40 (sve temperature):**

| Jezik | gemma3 0.1 | gemma3 0.8 | ministral 0.1 | ministral 0.8 | nllb |
|-------|-----------|-----------|--------------|--------------|------|
| hr | — | 18 | — | 16 | 6 |
| it | 9 | — | 11 | — | — |
| fr | — | 15 | — | 13 | — |
| de | 5 | 10 | 8 | 13 | 4 |

**Zaključak:** temp=0.8 generalno bolji, ali temp=0.1 nije zanemariv — posebno za IT gdje osvoji 20 od 40.

---

### 6. Proširenje na s41–s80

Pokrenuti svi runovi za rečenice 41–80, sva 4 jezika, temperature 0.1 i 0.8:

- gemma3 temp=0.8, e5-large, hr/it/fr/de
- gemma3 temp=0.1, e5-large, hr/it/fr/de
- ministral temp=0.8, e5-large, hr/it/fr/de
- ministral temp=0.1, e5-large, hr/it/fr/de
- nllb, e5-large, hr/it/fr/de
- nllb, MiniLM, hr/it/fr/de

Zatim sudija i pobjednici za s41–s80.

**Distribucija pobjednika s41–s80:**

| Jezik | gemma3 0.1 | gemma3 0.8 | ministral 0.1 | ministral 0.8 | nllb |
|-------|-----------|-----------|--------------|--------------|------|
| hr | 10 | 6 | 12 | 7 | 5 |
| it | 6 | 17 | 7 | 4 | 6 |
| fr | 10 | 7 | 6 | 14 | 3 |
| de | 8 | 6 | 8 | 12 | 6 |

**Ključno zapažanje:** Na s41–s80 slika se mijenja — HR i FR favorizuju temp=0.1 više nego s1–s40. Nema univerzalne pobjedničke temperature — ovisi o jeziku i dijelu teksta.

---

### 7. Popravka buga u `bb_04_pobjednik.py`

**Bug:** `DELETE FROM bb_prev_recenica WHERE prev_knjige_id = %s` brisao je **sve** pobjednike za jezik (uključujući prethodni raspon) pri svakom novom pozivu.

**Simptom:** Nakon pokretanja s41–s80, pobjednici s1–s40 su nestali.

**Fix:**
```python
# Briše samo pobjednike za trenutni raspon rečenica
DELETE FROM bb_prev_recenica
WHERE prev_knjige_id = %s
AND prevodi_recenica_id IN (
    SELECT id FROM bb_prevodi_recenica
    WHERE recenica_id IN (
        SELECT id FROM bb_recenice
        WHERE knjiga_id = %s AND pozicija BETWEEN %s AND %s
    )
)
```

---

### 8. Dodavanje retry logike u `bb_08_sudija.py`

Ollama Cloud je dva puta pao tokom sesije (500 Server Error, ReadTimeout). Dodata retry logika:

```python
def call_sudija(prompt, max_retries=3, wait=30):
    import time
    for attempt in range(max_retries):
        try:
            resp = requests.post(...)
            resp.raise_for_status()
            return resp.json()["message"]["content"].strip()
        except (requests.exceptions.HTTPError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                print(f"  Greška ({e}), čekam {wait}s pa ponavljam (pokušaj {attempt+1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise
```

3 pokušaja, 30s između. Sudija preskače prevode koji već imaju `sudija_avg` — restart je uvijek siguran.

---

## Uloga sudije i novi način ocjenjivanja

### Zašto sudija

Cosinus score mjeri semantičku stabilnost, ali ne vidi gramatičke greške. Primjer — HR s4:

| Model | kompozitni | Prevod |
|-------|-----------|--------|
| nllb | 0.9663 | *"sjedio u doručku stol"* ← gramatička greška |
| gemma3 | 0.9673 | *"sjedio je za doručkanim stolom"* |

NLLB bi pobijedio samo na kompozitnom scoreu. Sudija to ispravlja.

### Gemma4:31b kao blind sudija

Model ocjenjuje svaki prevod na skali 0.0–1.0 po 3 kriterija:

| Kriterij | Opis |
|----------|------|
| `sudija_grammar` | Gramatička ispravnost u ciljnom jeziku |
| `sudija_naturalness` | Idiomatska tečnost |
| `sudija_fidelity` | Vjernost originalnom značenju |

`sudija_avg = (grammar + naturalness + fidelity) / 3`

**Blind** = prevodi se šalju bez oznaka koji model je što preveo. Temperature=0.0 — deterministički.

### Formula pobjednika

```
finalni_score = 0.4 × kompozitni + 0.6 × sudija_avg
```

gdje je `kompozitni = (score + translation_score) / 2`.

Sudija nosi 60% težine. Fallback na samo kompozitni kada `sudija_avg IS NULL`.

---

## Kako dodati novi jezik, model, temperaturu, embedder

### Novi jezik

```sql
INSERT INTO bb_jezik (kod, naziv) VALUES ('es', 'Spanish');
```

Zatim pokrenuti prevod s `--jezici es`.

### Novi model i temperatura

```sql
INSERT INTO bb_modeli (naziv, temperatura) VALUES ('novi-model:tag', 0.7);
```

Zatim pokrenuti `bb_03_prevod.py` s `--model "novi-model:tag" --temp 0.7`.

> ⚠️ Skripta traži model po **naziv + temperatura** kombinaciji. Ako temperatura nije u bazi — greška `Model 'X' temp=Y nije u bb_modeli!`

### Novi embedder

```sql
INSERT INTO bb_embeddings (naziv) VALUES ('intfloat/multilingual-e5-base');
```

Dodati logiku učitavanja u `bb_03_prevod.py` (trenutno podržava e5-large i MiniLM).

---

## Stanje baze na kraju sesije

| Jezik | Raspon | Prevodi | Sudija | Pobjednici |
|-------|--------|---------|--------|------------|
| hr | s1–s80 | ✅ | ✅ | ✅ |
| it | s1–s80 | ✅ | ✅ | ✅ |
| fr | s1–s80 | ✅ | ✅ | ✅ |
| de | s1–s80 | ✅ | ✅ | ✅ |

Svaki jezik: 5 modela × 2 embeddera × 80 rečenica = 800 redova u `bb_prevodi_recenica`.
(gemma3 0.1, gemma3 0.8, ministral 0.1, ministral 0.8, nllb)

---

## Za sljedeću sesiju

**Prioritet:** Minimizacija modela i temperatura u svrhu poboljšanja performansi.

Pitanja za razmatranje:
- Da li je jedna temperatura (0.8?) dovoljna ili treba zadržati obje?
- Može li jedan LLM (gemma3 ili ministral) pokriti dovoljno rečenica da drugi postane suvišan?
- Optimalna temperatura po jeziku — ima li smisla koristiti različite temperature za različite jezike?
- Što uraditi s NLLB koji konzistentno osvaja mali broj rečenica ali je lokalni i besplatan?

---

*Flavio & Claude · Buchenberg · Sesija 38 · 2. jun 2026.*
