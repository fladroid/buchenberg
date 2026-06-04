# Session 50 — Hound MK+BG s1–s50

**Datum:** 4. jun 2026.
**Sesija:** 50
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Hound MK+BG s1–s50

Dodano 50 rečenica makedonskog i bugarskog prevoda za The Hound of the Baskervilles (knjiga_id=1).

| Run | Model | Temp | Trajanje |
|-----|-------|------|---------|
| 1 | gemma3:12b | 0.8 + 0.1 | 9:40 min |
| 2 | nllb-600M | 0.0 | 4:22 min (paralelno) |
| 3 | ministral-3:14b | 0.8 + 0.1 | 5:56 min |
| Sudija | gemma4:31b | 0.0 | 8:39 min (500 ocjena) |

**Napomena:** ministral prvi put pao jer nije pokrenut iz ispravnog direktorija (`venv/bin/python` nije nađen). Pokrenut ručno drugi put.

**Distribucija pobjednika:**

| Jezik | Model | Temp | Pobjede | % |
|-------|-------|------|---------|---|
| MK | gemma3 | 0.1 | 20 | 40% |
| MK | gemma3 | 0.8 | 12 | 24% |
| MK | nllb | 0.0 | 7 | 14% |
| MK | ministral | 0.1 | 6 | 12% |
| MK | ministral | 0.8 | 5 | 10% |
| BG | ministral | 0.8 | 14 | 28% |
| BG | gemma3 | 0.1 | 12 | 24% |
| BG | gemma3 | 0.8 | 10 | 20% |
| BG | ministral | 0.1 | 9 | 18% |
| BG | nllb | 0.0 | 5 | 10% |

**Zapažanje:** MK — gemma3@0.1 dominira (40%), slično kao HR pattern. BG — uravnoteženiji, ministral@0.8 vodi s 28%.

### 2. Web export

`bb_web_export.py` pokrenut — `tr_1_bg.json` i `tr_1_mk.json` na portalu.

---

## Stanje baze na kraju sesije

| Knjiga | ID | Jezik | Rečenice | Status |
|--------|-----|-------|----------|--------|
| Hound | 1 | bs, hr | 350 | ✅ |
| Hound | 1 | af, de, es, fr, it, nl, sl, sr, pt, ro | 100 | ✅ |
| Hound | 1 | mk, bg | 50 | ✅ novi |
| Big Four | 5 | pt, it | 100 | ✅ |
| Frankenstein | 8 | ro, it | 100 | ✅ |

---

## Napomene

- Albanski (sq) i grčki (el) su zasebne indo-evropske grane bez bliskih srodnika — dodavanje odgođeno do odluke o Ollama Cloud pretplati
- NLLB overnight run razmatran za proširenje više jezika odjednom

---

## Otvoreno za sljedeće sesije

1. Proširenje Hound — svih 14 jezika na s51–s100 (mk, bg) i s101–s350 (hr, bs)
2. Proširenje Big Four PT i IT — s101–s350
3. Proširenje Frankenstein RO i IT — s101–s350
4. Favicon za buchenberg.opik.net
5. Relation Extraction (Gemma4) — semantičke veze između entiteta
6. Refaktorisati `bb_web_export.py` da koristi `v_pobjednici` view

---

*Flavio & Claude · Buchenberg · Sesija 50 · 4. jun 2026.*
