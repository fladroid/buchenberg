# Session 46 — Big Four IT s1–s100

**Datum:** 4. jun 2026.
**Sesija:** 46
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Inicijalizacija sesije

README + posljednje 3 session docs (43, 44, 45) + health check — sve zeleno.

---

### 2. Big Four IT s1–s100

Dodano 100 rečenica talijanskog prevoda za The Big Four (knjiga_id=5).

| Run | Model | Temp | Trajanje |
|-----|-------|------|---------|
| 1 | gemma3:12b | 0.8 + 0.1 | 6:19 min |
| 2 | nllb-600M | 0.0 | 10:11 min (paralelno s ministral) |
| 3 | ministral-3:14b | 0.8 + 0.1 | 9:32 min (paralelno s nllb) |
| Sudija | gemma4:31b | 0.0 | 6:43 min (500 ocjena) |

**Distribucija pobjednika IT (Big Four, s1–s100):**

| Model | Temp | Pobjede | % |
|-------|------|---------|---|
| gemma3:12b | 0.1 | 28 | 28% |
| ministral-3:14b | 0.1 | 28 | 28% |
| ministral-3:14b | 0.8 | 19 | 19% |
| gemma3:12b | 0.8 | 18 | 18% |
| nllb-600M | 0.0 | 7 | 7% |

**Zapažanje:** gemma3 i ministral izjednačeni na 0.1 temperaturi — drugačiji pattern od Frankenstein IT gdje je gemma3@0.8 dominirao sa 34%. Potvrđuje da optimalni model/temperatura ovisi o kombinaciji knjiga+jezik.

---

### 3. Web export

`bb_web_export.py` pokrenut — `tr_5_it.json` generiran (100 prevedenih / 5055 ukupno).

---

## Stanje baze na kraju sesije

| Knjiga | ID | Jezik | Rečenice | Status |
|--------|-----|-------|----------|--------|
| Hound | 1 | bs, hr | 350 | ✅ |
| Hound | 1 | af, de, es, fr, it, nl, sl, sr, pt, ro | 100 | ✅ |
| Big Four | 5 | pt, it | 100 | ✅ novi: it |
| Frankenstein | 8 | ro, it | 100 | ✅ |

---

## Napomena — v_pobjednici view

Pri analizi distribucije pobjednika, `v_pobjednici` view nije vratio točne rezultate za filter po knjizi (nema `knjiga_id` kolonu). Distribucija dobivena direktnim JOINom kroz `bb_prev_recenica → bb_prevodi_recenica → bb_prevodi_knjige → bb_modeli`. Ovo je poznato ograničenje viewa — dodati `knjiga_id` u `v_pobjednici` je kandidat za buduću sesiju.

---

## Otvoreno za sljedeće sesije

1. Proširenje Hound — svih 12 jezika na s101–s350
2. Proširenje Big Four PT i IT — s101–s350
3. Proširenje Frankenstein RO i IT — s101–s350
4. Refaktorisati `bb_web_export.py` da koristi `v_pobjednici` view
5. Dodati `knjiga_id` u `v_pobjednici` view
6. spaCy NER i Word cloud (odgođeno)

---

## Git

- Commit: `session 46: Big Four IT s1-100 (gemma3+ministral+nllb+sudija+pobjednici), web export`

---

*Flavio & Claude · Buchenberg · Sesija 46 · 4. jun 2026.*
