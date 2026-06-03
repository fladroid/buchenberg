# Session 43 — Web popravke, bb_03_prevod --temp lista, Hound PT+RO

**Datum:** 3. jun 2026.
**Sesija:** 43
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Web stranica — popravke (buchenberg.opik.net)

**Problem 1 — nedosljedna imena jezika:**
- Hound jezici koristili `LANG_NAMES_NATIVE` dict (nativna imena)
- PT i RO nisu bili u dictu → fallback na BHS naziv iz JSON-a
- Fix: dodani `pt:"Português"`, `ro:"Română"`, `mk:"Македонски"`, `bg:"Български"` u `LANG_NAMES_NATIVE`

**Problem 2 — zastavice ne rade na Linuxu:**
- Emoji zastave se prikazuju kao ISO 3166 državni kodovi (RS, ZA...)
- Fix: uklonjen `LANG_FLAGS` dict, zamijenjen s `lang.code.toUpperCase()` — prikazuje ISO 639-1 jezični kod (SR, HR, DE...)

**Problem 3 — "rumunski" u book-meta:**
- `#book-meta` div koristio `tr.lang_name` iz JSON-a (BHS naziv)
- Fix: `LANG_NAMES_NATIVE[state.activeLang] || tr.lang_name`

**Problem 4 — X-Ray toggle:**
- `avg ts`, `avg judge` i `[model]` badge na hoveru uvijek vidljivi
- Fix: dodan X-Ray toggle u toolbar; score-info i model-badge skriveni po defaultu, vidljivi samo kad je X-Ray ON

### 2. bb_03_prevod.py — `--temp` prima listu

**Staro:** `--temp 0.8` — jedna temperatura po pozivu  
**Novo:** `--temp 0.8 0.1` — lista temperatura, loop unutar skripte

Izmjena: `nargs="+"` na `--temp` argumentu; `for temp in args.temp:` petlja obuhvata model lookup, print i `for kod` blok. Embedder i rečenice se učitavaju jednom izvan petlje.

**Primjer:**
```bash
venv/bin/python src/bb_03_prevod.py \
  --knjiga 1 --od 1 --do 100 --model "gemma3:12b" --temp 0.8 0.1 \
  --embedder "multilingual-e5-large" --jezici pt ro
```

### 3. Hound PT+RO s1–s100

| Run | Model | Temp | Jezici | Trajanje |
|-----|-------|------|--------|---------|
| 1 | gemma3:12b | 0.8 + 0.1 | pt, ro | 15:30 min |
| 2 | ministral-3:14b | 0.8 + 0.1 | pt, ro | 16:15 min |
| 3 | nllb-600M | 0.0 | pt, ro | 16:18 min (paralelno) |

Sudija: 16:35 min (2 × 100 × 5 = 1000 ocjena)

**Distribucija pobjednika:**

| Jezik | Model | Temp | Pobjede | % |
|-------|-------|------|---------|---|
| PT | gemma3 | 0.1 | 29 | 29% |
| PT | gemma3 | 0.8 | 25 | 25% |
| PT | ministral | 0.1 | 20 | 20% |
| PT | ministral | 0.8 | 16 | 16% |
| PT | nllb | 0.0 | 10 | 10% |
| RO | ministral | 0.1 | 28 | 28% |
| RO | gemma3 | 0.8 | 25 | 25% |
| RO | gemma3 | 0.1 | 19 | 19% |
| RO | ministral | 0.8 | 19 | 19% |
| RO | nllb | 0.0 | 9 | 9% |

**Zapažanje:** PT na Houndu → gemma3@0.1 dominira (vs. Big Four gdje gemma3@0.8 vodio). RO na Houndu → ministral@0.1 dominira (vs. Frankenstein gdje gemma3@0.8 dominirao sa 41%). Potvrđuje da optimalni model/temperatura ovisi o kombinaciji knjiga+jezik, ne samo o jeziku.

---

## Stanje baze na kraju sesije

| Knjiga | ID | Jezik | Rečenice | Status |
|--------|-----|-------|----------|--------|
| Hound | 1 | bs, hr | 350 | ✅ |
| Hound | 1 | af, de, es, fr, it, nl, sl, sr | 100 | ✅ |
| Hound | 1 | pt, ro | 100 | ✅ novi |
| Big Four | 5 | pt | 100 | ✅ |
| Frankenstein | 8 | ro | 100 | ✅ |

---

## Otvoreno za sljedeće sesije

1. **Proširenje Hound** — svih 12 jezika na s101–s350
2. **Proširenje PT+RO** — Big Four i Frankenstein na s101–s350
3. **Novi jezici** — po knjigama
4. **README update** — sekcija 9 (stanje prevoda), sekcija 4 (--temp lista)

---

## Git

- Commit: `session 43: bb_03_prevod --temp lista, web popravke (jezik kodovi, X-Ray toggle), Hound pt+ro s1-100`

---

*Flavio & Claude · Buchenberg · Sesija 43 · 3. jun 2026.*
