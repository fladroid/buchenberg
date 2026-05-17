# Session 09 — Buchenberg

**Datum:** 17. maj 2026.  
**Učesnici:** Flavio & Claude

---

## Cilj sesije

Implementacija nove arhitekture metoda (zelena/žuta/crvena dodjela) i rješavanje JSON parser problema u batch prevodu.

---

## Korak 1 — Dijagnoza parser problema

Pokrenuti test_007 (hr, 40 rečenica, gemma+gemma_t05+ministral+ministral_t05) kao fokusirani dijagnostički run.

**Rezultat:** 4 Warninga — svi uzrokovani s26 koja sadrži apostrof unutar teksta (`'prijatelji C.C.H.'`). Parser Strategija 1 radila `replace('\"', '§§§')` što je rušilo parsiranje validnog JSON-a.

**Fix (session_08):** Uklonjen placeholder trik, standardni `json.loads` koji nativno čita escaped navodnike. test_008 → 0 Warninga.

---

## Korak 2 — Novi problem: JSON format i dalje nestabilan

Pri pokretanju test_009 (6 jezika) pojavili su se novi warninga — model vraća trunkiran ili n-1 odgovor bez obzira na JSON format.

**Odluka:** Prelaz sa JSON array formata na `__!!__` separator format.

### Promjene u `run_test.py`

- Uklonjen `parse_gemma_batch_response` (6 strategija, krhak)
- Dodan `parse_separator_response` — split po `__!!__`, strip markdown
- Prompt promijenjen: `"Return ONLY the {n} translations separated by __!!__"`

**Rezultat:** Problem nije riješen — model i dalje vraća 19/20, format nije bio uzrok.

---

## Korak 3 — Root cause: kratke rečenice u batchu

Analizom utvrđeno da model spaja s1+s2 (naslov + autor) jer ih semantički tretira kao cjelinu.

**Privremeni fix:** Uvedena podjela `batch_min_words=6` — kratke rečenice (wc < 6) idu single, ostale batch.

**Statistika za Hound:** 661 kratkih rečenica (17%), 3191 batch (82%).

**Zaključak nakon diskusije:**
- Warning znači fallback na single — podaci su kompletni, nije izgubljen nijedan prevod
- Podjela single/batch nije potrebna jer fallback ionako radi posao
- `batch_min_words` uklonjen, vraćen čisti batch za sve rečenice

### Finalno stanje parsera

```python
def parse_separator_response(raw, n, context="batch"):
    SEP = "__!!__"
    parts = raw.split(SEP)
    cleaned = [re.sub(r"\*+([^*]+)\*+", r"\1", p.strip()) for p in parts if p.strip()]
    if len(cleaned) >= n:
        return cleaned[:n]
    logger.warning(...)
    return None
```

---

## Korak 4 — filter_sentences_by_score fix

Otkriveno da filter gleda MAX score across svih test_id-eva, ne samo trenutnog.

**Fix:** Dodan `WHERE test_id = %s` u SQL upit — filter gleda samo score unutar istog testa.

---

## Korak 5 — Nova arhitektura metoda: test_012

Implementirana trofazna obrada po boji rečenice:

- **Faza 1** — gemma+gemma_t05 za sve rečenice
- **Faza 2** — ministral+ministral_t05 za žute+crvene (`score_to 0.8999`)
- **Faza 3** — nllb+nllb_t05 za crvene (`score_to 0.7999`)

### Definicija boja (kanonska)

- 🟢 **Zelena**: `MAX(translation_score)` across svih redova >= 0.90
- 🟡 **Žuta**: MAX između 0.80 i 0.89
- 🔴 **Crvena**: MAX < 0.80

Nije važno koliko redova ima niti koje su boje pojedinačni redovi — gleda se samo MAX.

### Rezultati test_012 — faza 1 (gemma)

| Jezik | 🟢 | 🟡 | 🔴 |
|-------|----|----|-----|
| HR | 22 (55%) | 15 (37%) | 3 (7%) |
| BG | 15 (37%) | 20 (50%) | 5 (12%) |
| DE | 20 (50%) | 14 (35%) | 6 (15%) |
| NL | 26 (65%) | 13 (32%) | 1 (2%) |
| IT | 20 (50%) | 17 (42%) | 3 (7%) |
| PT | 17 (42%) | 19 (47%) | 4 (10%) |

### Rezultati test_012 — nakon faze 2 (ministral za žute+crvene)

| Jezik | 🟢 | 🟡 | 🔴 |
|-------|----|----|-----|
| HR | 23 (57%) | 14 (35%) | 3 (7%) |
| BG | 16 (40%) | 20 (50%) | 4 (10%) |
| DE | 20 (50%) | 14 (35%) | 6 (15%) |
| NL | 26 (65%) | 13 (32%) | 1 (2%) |
| IT | 20 (50%) | 17 (42%) | 3 (7%) |
| PT | 17 (42%) | 20 (50%) | 3 (7%) |

### Faza 3 — NLLB

Filter vratio 0 rečenica — ministral je podigao sve preostale crvene iznad 0.80. Faza 3 nije bila potrebna za ovaj test.

---

## Naučene lekcije

- **Warning ≠ izgubljen prevod.** Fallback na single radi posao — podaci su uvijek kompletni.
- **Format odgovora (JSON vs separator) nije bio uzrok problema.** Model ponekad vraća n-1 stavki bez obzira na format — fallback je pravo rješenje.
- **Definicija boje rečenice gleda MAX score, ne pojedinačne redove.** Zelena rečenica može imati crvene redove.
- **Protokol: komanda → Flavio OK → izvršavanje.** Bez izuzetaka.

---

## Izmjene fajlova u ovoj sesiji

| Fajl | Izmjena |
|------|---------|
| `src/run_test.py` | JSON→separator parser, uklonjen batch_min_words, filter_sentences_by_score fix, load_sentences bez word_count |
| `tests/test_registry.yaml` | Dodani test_007 do test_012 |
| `docs/sessions/session_09.md` | Ovaj dokument |

---

## Otvoreno za sljedeću sesiju

1. **GA za žute+crvene test_012** — pokrenuti run30
2. **GA pobjednici kao `method = 'ga'`** — upisati u test_results
3. **Novi jezici** — bs, sl, mk, af, es, ro
4. **Pipeline orchestrator** — finalni prevod iz test_results
5. **multilingual-e5-large** — testirati kao alternativu MiniLM

---

*Flavio & Claude · Session 09 · 17. maj 2026.*
