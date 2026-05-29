# Session 31 — Eksperimenti evaluacije: pivot, hint, context, DeepL, e5

**Datum:** 2026-05-29
**Učesnici:** Flavio & Claude
**Nastavlja:** Session 30 (embedding tabele, MiniLM vektori)

---

## Kontekst — gdje smo stali

Session 30 je uspostavila embedding infrastrukturu (sentence_embeddings +
translation_embeddings, MiniLM). Logičan sljedeći korak: eksperimentisanje
s novim pristupima evaluacije i poboljšanja prijevoda.

---

## Korak 1 — color_summary VIEW

Novi VIEW koji za svaki jezik i embedder broji zelene/žute/crvene rečenice
(best score per sentence).

```sql
CREATE VIEW color_summary AS
WITH best_per_sentence AS (
    SELECT target_lang, embedder, sentence_id, MAX(cosine_score) AS best_score
    FROM translation_scores GROUP BY target_lang, embedder, sentence_id
)
SELECT target_lang, embedder,
    COUNT(*) FILTER (WHERE best_score >= 0.90) AS zelene,
    COUNT(*) FILTER (WHERE best_score >= 0.80 AND best_score < 0.90) AS zute,
    COUNT(*) FILTER (WHERE best_score < 0.80) AS crvene,
    COUNT(*) AS ukupno
FROM best_per_sentence GROUP BY target_lang, embedder ORDER BY embedder, target_lang;
```

Embedder je kolona grupisanja — kad se doda novi embedder, automatski se
pojavi kao novi red bez izmjena VIEW-a.

---

## Korak 2 — Cross-lingual analiza HR

Upit: za koliko od 40 rečenica neka druga kombinacija (jezik/model) premašuje
best HR score? Rezultat: **39/40** — samo jedna rečenica gdje je HR globalni
pobjednik (po MiniLM metrici).

---

## Korak 3 — Eksperiment 1: Direktni pivot (logs/pivot_hr_001.log)

**Pristup:** Za svaku rečenicu gdje HR gubi — prevesti pobjednički tekst
(winner_lang → HR) via gemma3. Nova skripta: `src/run_pivot.py`.

**Rezultat: 2/39 poboljšano.**

Katastrofalni padovi: s1 (-0.2231), s39 (-0.3589). Dijagnoza: dvostruki
prijevod bez EN originala kao sidra gubi semantiku.

---

## Korak 4 — Eksperiment 2: Hint metoda (logs/pivot_hr_002.log)

**Pristup:** EN→HR via gemma3, pobjednički prevod iz drugog jezika kao
kontekst/hint u promptu:

```
Translate the following English text to Croatian.
For reference, here is a high-quality {lang} translation: {winner_text}
```

**Rezultat: 6/39 poboljšano** (3× bolje od direktnog pivota).
Nema katastrofalnih padova. Poboljšanja marginalna (+0.002–+0.006).

---

## Korak 5 — Eksperiment 3: Kontekstualni prijevod (logs/context_hr_001.log)

**Pristup:** Za žute+crvene HR rečenice — prozor od 3 uzastopne rečenice.
Nova skripta: `src/run_context.py`.

Pravilo prozora:
- Normalno: [id-1, id, id+1] → prevodi srednju
- Prva: [id, id+1, id+2] → prevodi prvu
- Zadnja: [id-2, id-1, id] → prevodi zadnju

**Rezultat: 4/20 poboljšano.** Veće pojedinačne delte nego hint metoda
(s24: +0.0176, s29: +0.0189). s7 i s29 su nove pobjede kojih nema u hint runu.

---

## Korak 6 — DeepL integracija (logs/deepl_hr_001.log)

DeepL API Free (1,000,000 znakova/mj). Nova skripta: `src/run_deepl.py`.
Testiran na 2 crvene HR rečenice.

**Rezultati:**
- s1 "The Hound of the Baskervilles": `"Baskervilleov hrt"` → `"Pas iz Baskervillesa"`
  score 0.7313 → **0.8442** (+0.1129) ✅
- s38 "It gives us the basis for several deductions.":
  `"dedukcija"` → DeepL `"zaključaka"` → score 0.7812 → **0.5432** ❌

**Ključni nalaz:** s38 je savršena ilustracija MiniLM biasa — "zaključaka" je
bolji hrvatski nego "dedukcija", ali MiniLM ga kažnjava jer se udaljio od
doslovnosti. Metrika je problem, ne prijevod.

---

## Korak 7 — e5-large vektori

```bash
venv/bin/python src/run_embeddings.py --embedder e5 --sent_from 1 --sent_to 40
```

Trajanje: **12:34 min** (brže nego očekivano).
Rezultat: 4480 translation_embeddings + 40 sentence_embeddings s embedder='e5'.

### Poređenje MiniLM vs e5 (color_summary)

| Jezik | MiniLM 🟢 | MiniLM 🔴 | e5 🟢 (prag 0.93) | e5 🔴 (prag 0.88) |
|-------|-----------|-----------|-------------------|-------------------|
| AF    | 8         | 22        | 27                | 0                 |
| HR    | 20        | 2         | 29                | 1                 |
| BG    | 18        | 2         | 8                 | 1                 |
| MK    | 16        | 3         | 7                 | 2                 |

**AF problem je bio 100% MiniLM artefakt.** Sa e5, AF je mid-pack (avg 0.927).

### e5 distribucija scoreva

Opseg: 0.76–1.00 (komprimovaniji od MiniLM-ovog 0.50–1.00).
Rekalibracija thresholdova za e5: 🟢 ≥0.93, 🟡 0.88–0.92, 🔴 <0.88.

S tim pragovima: ukupno samo 8 crvenih rečenica u svim jezicima zajedno.

---

## Izmjene koda i baze

| Komponenta | Izmjena |
|------------|---------|
| `color_summary` | Novi VIEW — zelene/žute/crvene po jeziku i embedderu |
| `sql/create_views.sql` | Dodan color_summary |
| `src/run_pivot.py` | Nova skripta — cross-lingual pivot + hint metoda |
| `src/run_context.py` | Nova skripta — kontekstualni prijevod (3-sentence window) |
| `src/run_deepl.py` | Nova skripta — DeepL prijevod za crvene rečenice |
| `translation_embeddings` | +4480 e5 vektora |
| `sentence_embeddings` | +40 e5 vektora |

---

## Ključni zaključci

1. **Direktni pivot** (winner_lang→HR) ne radi — gubi EN sidro.
2. **Hint metoda** je sigurnija i 3× bolja od direktnog pivota.
3. **Kontekstualni prijevod** daje veće pojedinačne delte za rečenice
   koje ovise o kontekstu.
4. **DeepL** radi dobro ali MiniLM metrika ga ne može pravilno ocijeniti.
5. **e5-large je pravi embedder za produkciju.** MiniLM je bio pristran
   prema doslovnosti i stvorio lažnu sliku (posebno za AF).
6. **Thresholdovi trebaju rekalibraciju** za e5: 🟢≥0.93, 🟡0.88-0.92, 🔴<0.88.

---

## Na horizontu

1. Ažurirati `color_summary` VIEW s e5 thresholdovima (ili parametrizovati)
2. Pipeline orchestrator — finalni prijevod iz best_translation
3. COMET-QE kao alternativa embedder-based evaluaciji
4. Referentni prijevod "Psa Baskervillevih" za gold-standard evaluaciju
5. Batch commits u `run_embeddings.py` (otpornost na crash)

---

## Handoff blok

- **color_summary VIEW:** aktivan u bazi i u sql/create_views.sql
- **run_pivot.py, run_context.py, run_deepl.py:** aktivni u src/
- **e5 vektori:** 4520 redova u embedding tabelama
- **Git:** treba commit
- **Model:** Sonnet 4.6 medium

---

*Flavio & Claude · Session 31 · 2026-05-29*
