# Session 42 — Frankenstein: nova knjiga, RO prevod

**Datum:** 3. jun 2026.
**Sesija:** 42
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Inicijalizacija sesije

README + posljednje 3 session docs + health check. Sve zeleno.

**Opažanje:** README (V2, sesija 38) nije ažuriran od sesije 38 — sesije 39, 40, 41 nisu reflektovane. Frankenstein je bio naveden u README sekciji 10 (stari testni korpus iz `buchenberg` baze) ali nije postojao u `bb` bazi. Potvrđeno SQL upitom.

---

### 2. Dodavanje Frankenstein u bb pipeline

**Knjiga:** Frankenstein; or, the Modern Prometheus
**Autor:** Mary Wollstonecraft (Godwin) Shelley
**Gutenberg ID:** 84
**URL:** https://gutenberg.org/cache/epub/84/pg84-images.html

**Download:**
```bash
wget -O books/frankenstein.html "https://gutenberg.org/cache/epub/84/pg84-images.html"
```

**Provjera HTML strukture:** s1–s3 metadata (naslov, podnaslov, autor), s4+ pravi tekst. Identična struktura kao Hound i Big Four — parser radi bez izmjena.

**Dodavanje u `bb_02_insert_knjiga.py`:** Frankenstein dodan u `KNJIGE` listu.

**Upis:**
```
Nova knjiga id=8: Frankenstein; or, the Modern Prometheus
  Parsirano: 3384 rečenica
  Upisano: 3384 rečenica
```

---

### 3. RO prevod s1–s100

Rumunjski (ro, id=14) već bio u `bb_jezik`. Pokrenuto 5 modela serijski (cloud) + NLLB paralelno:

| Model | Temp | Trajanje |
|-------|------|---------|
| gemma3:12b | 0.8 | 5:02 min |
| gemma3:12b | 0.1 | 7:36 min |
| ministral-3:14b | 0.8 | 4:03 min |
| ministral-3:14b | 0.1 | 4:15 min |
| nllb-600M | 0.0 | 9:26 min (paralelno) |

Sudija: 4:54 min (100 rec × 5 modela = 500 ocjena)

---

### 4. Distribucija pobjednika — RO (Frankenstein, s1–s100)

| Model | Temp | Pobjede | % |
|-------|------|---------|---|
| gemma3 | 0.8 | 41 | 41% |
| gemma3 | 0.1 | 30 | 30% |
| ministral | 0.1 | 13 | 13% |
| ministral | 0.8 | 9 | 9% |
| nllb | 0.0 | 7 | 7% |

**Zapažanje:** RO se ponaša kao romanski jezik ali gemma3 dominira sa 71% — suprotno od očekivanog "ministral dominira za romanske" patterna. Potvrđuje da temperatura pattern nije univerzalan i ovisi o knjizi/jeziku kombinaciji.

---

### 5. Web export

`bb_web_export.py` — 3 knjige, 12 prijevoda na buchenberg.opik.net.

---

## Stanje baze na kraju sesije

| Knjiga | ID | Jezik | Rečenice | Status |
|--------|-----|-------|----------|--------|
| The Hound of the Baskervilles | 1 | bs, hr | 350 | ✅ |
| The Hound of the Baskervilles | 1 | af, de, es, fr, it, nl, sl, sr | 100 | ✅ |
| The Big Four | 5 | pt | 100 | ✅ |
| Frankenstein | 8 | ro | 100 | ✅ |

---

## Otvoreno za sljedeće sesije

1. **Proširenje RO** — s101–s350 (ili cijela knjiga)
2. **Novi jezici za Frankenstein** — po istom workflow-u
3. **Proširenje PT (Big Four)** — s101–s350
4. **Proširenje Hound** — preostalih 7 jezika na s101–s350
5. **README update** — sesije 39–42, novo stanje baze, Frankenstein

---

## Git

- Commit: `session 42: Frankenstein dodana (knjiga_id=8, 3384 rec), RO prevod s1-100, gemma3@0.8 dominira 41%, web export`

---

*Flavio & Claude · Buchenberg · Sesija 42 · 3. jun 2026.*
