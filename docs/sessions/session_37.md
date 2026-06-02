# Session 37 — Sudija: LLM evaluacija kvaliteta prevoda

**Datum:** 2. jun 2026.
**Učesnici:** Flavio & Claude
**Nastavlja:** Session 36 (RAG scorer, kompozitni score)

---

## Kontekst

Nakon evaluacije RAG scorera (session 36) i zaključka da OpenSubtitles nije pravi korpus za književnu prozu, fokus se pomjerio na fundamentalni problem: cosinus score mjeri semantičku stabilnost, ali ne razlikuje gramatičke greške od ispravnih prevoda. Uvedena je nova dimenzija evaluacije — LLM kao blind sudija.

---

## Što je urađeno

### 1. Analiza limita cosinus scorea

Konkretni primjer — HR s4, svi prevodi:

| Model | kompozitni | Prevod |
|-------|-----------|--------|
| gemma4 | 0.9673 | "...sjedio je za doručkanim stolom." |
| nllb | 0.9663 | "...sjedio u doručku stol." ← gramatička greška |
| ministral | 0.9651 | "...sjedio je za doručnim stolom." |
| gemma3 | 0.9601 | "...sjedio je za stolom za doručak." |

NLLB drugi po kompozitnom scoreu — a ima gramatičku grešku. Score to ne vidi.

**Zaključak:** cosinus score mjeri informacijsku stabilnost i semantičku blizinu, ali ne:
- gramatičku ispravnost
- stilsku prirodnost
- idiomatsku ispravnost

### 2. Odluka: gemma4 kao sudija

Gemma4:31b izbačen iz pipeline-a prevođenja i dodijeljen ulozi blind sudije. Razlozi:
- Nije pristran prema vlastitim prevodima (ne ocjenjuje sebe)
- Najjači lokalni model — najpouzdanija ocjena
- Temperature=0.0 — deterministički, konzistentni rezultati

**Modeli koji se ocjenjuju:** gemma3:12b, ministral-3:14b, nllb-600M

### 3. Izmjene sheme baze

```sql
ALTER TABLE bb_prevodi_recenica ADD COLUMN sudija_grammar real;
ALTER TABLE bb_prevodi_recenica ADD COLUMN sudija_naturalness real;
ALTER TABLE bb_prevodi_recenica ADD COLUMN sudija_fidelity real;
ALTER TABLE bb_prevodi_recenica ADD COLUMN sudija_avg real;
```

### 4. bb_08_sudija.py

Blind evaluacija — modeli se prezentuju bez oznaka, sudija ocjenjuje 0.0–1.0 po tri kriterija.

**Prompt:**
```
Rate each translation on a scale 0.0–1.0 for:
- grammar: grammatical correctness in {lang}
- naturalness: idiomatic fluency in {lang}
- fidelity: faithfulness to the original meaning
```

**Tehničke karakteristike:**
- Idempotentna — preskače redove gdje `sudija_avg IS NOT NULL`
- Commit nakon svake rečenice
- Fallback JSON parser (regex extraction ako direktni parse ne uspije)
- ~4.5 sek/rečenica/jezik

**Run:** s1–s10, hr + it — 60 redova upisano, ~45 sek ✅

### 5. Rezultati s1–s10

**HR — sudija_avg:**

| pozicija | gemma3 | ministral | nllb |
|----------|--------|-----------|------|
| s1 | 0.467 | 0.400 | **1.000** |
| s2 | **1.000** | 0.833 | 0.833 |
| s3 | 0.833 | **1.000** | 0.867 |
| s4 | **0.933** | 0.867 | 0.233 |
| s5 | **0.900** | 0.833 | 0.367 |
| s6 | **0.933** | 0.667 | 0.400 |
| s7 | 0.267 | **0.900** | 0.933 |
| s8 | 0.733 | **0.967** | 0.633 |
| s9 | 0.933 | **0.967** | 0.267 |
| s10 | **1.000** | 0.867 | **1.000** |

**IT — sudija_avg:**

| pozicija | gemma3 | ministral | nllb |
|----------|--------|-----------|------|
| s1 | **1.000** | 0.967 | 0.967 |
| s2 | **1.000** | **1.000** | **1.000** |
| s3 | **1.000** | **1.000** | 0.833 |
| s4 | **1.000** | **1.000** | 0.400 |
| s5 | 0.967 | **1.000** | 0.367 |
| s6 | 0.933 | **1.000** | 0.467 |
| s7 | 0.900 | **1.000** | 0.800 |
| s8 | 0.700 | **1.000** | 0.767 |
| s9 | **1.000** | 0.967 | 0.567 |
| s10 | **1.000** | **1.000** | **1.000** |

### 6. README ažuriran

Dodana sekcija `## 15. bb pipeline` — dokumentuje bb bazu, sve bb_* skripte, metrike kvaliteta i workflow.

---

## Ključni uvidi

- **NLLB dramatično kažnjen** — sudija prepoznaje gramatičke greške koje cosinus score propušta (HR s4: nllb komp=0.9663, sudija=0.233)
- **s1 HR zanimljiv slučaj** — ministral prevodi "Hound" kao "Pasulj" (sudija=0.400), gemma3 "Psa od Baskervila" (sudija=0.467), nllb jedini tačan "Pas Baskervilsa" (sudija=1.000)
- **IT konzistentno bolji** — gemma3 i ministral dominiraju s ocjenama blizu 1.000
- **Sudija i cosinus score su komplementarni** — često biraju različite pobjednike
- **Uvođenje LLM sudije je ključni korak** — jedini način da se izmjeri gramatička ispravnost i idiomatska prirodnost bez human evaluacije

---

## Otvoreno za sljedeću sesiju

1. **Ažurirati `bb_04_pobjednik.py`** — uključiti `sudija_avg` u kriterij pobjednika
2. **Definisati finalnu formulu** — kombinacija kompozitnog scorea i sudija ocjene
3. **Pokrenuti sudiju na s1–s40** — cijeli testni skup
4. **Analiza korelacije** — koliko se sudija i cosinus score slažu/razilaze
5. **Proširiti na fr, de** — dodati NLLB run za de, pokrenuti fr

---

## Git

- Commit `992ae67`: `feat: bb_08_sudija — gemma4 blind evaluator`
- Commit (ovaj): `docs: session_37 + README sekcija 15 bb pipeline`

---

*Flavio & Claude · Buchenberg · Session 37 · 2. jun 2026.*
