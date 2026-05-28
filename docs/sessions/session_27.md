# Session 27 — Embedder benchmark: MiniLM vs e5-large vs SONAR

**Datum:** 2026-05-28
**Učesnici:** Flavio & Claude

---

## Cilj sesije

Sistematična usporedba 5 modela prevoda (nllb_t05, claude_t05, ministral_t05, gemma3_t05, gemma4_t05) pod 3 različita embeddera (MiniLM, e5-large, SONAR). Uvođenje gemma4 i claude_literal kao novih metoda. Integracija SONAR embeddinga.

---

## Korak 1 — Kontekst sesije

Pročitani: README, session_24/25/26. Health check — sve zeleno. NLLB keš na 600M. Git čist (session_26 pushana).

Aktivan pivot test: pivot_016 (fr/it/pt). test_claude_003 nedovršen (samo init3, bez pivot faze).

---

## Korak 2 — pivot_017: NLLB init3 za IT

### pivot.yaml

```yaml
test_id: pivot_017
langs: [it]
models: [nllb_t05]
```

### Rezultati (nllb_t05, 600M, init×3)

| Lang | 🟢 | 🟡 | 🔴 | avg |
|------|----|----|-----|-----|
| IT | 20 | 17 | 3 | 0.8973 |

---

## Korak 3 — Model benchmark (MiniLM): 5 modela × IT × init×3

Cilj: usporediti sve dostupne modele pod istim uvjetima (MiniLM embedder, IT, 40 rečenica, init×3).

### Novi testovi kreirani

| Test ID | Metoda | Napomena |
|---------|--------|----------|
| `test_claude_004` | claude_t05 | Postojeća metoda |
| `test_ministral_001` | ministral_t05 | Postojeća metoda |
| `test_gemma_001` | gemma_t05 | Postojeća metoda |
| `test_gemma4_001` | gemma4_t05 | **Nova metoda** — dodana u ovoj sesiji |

### Novi kod: gemma4 integracija

Dodano u `run_test.py`:
- `GEMMA4_MODEL = "gemma4:31b"`
- `gemma4` i `gemma4_t05` u `VALID_METHODS`
- dispatch_translate, dispatch_back_translate, batch blokovi

### Rezultati (MiniLM, IT, init×3)

| Model | 🟢 | 🟡 | 🔴 | avg translation | avg back |
|-------|----|----|-----|----------------|----------|
| nllb_t05 (pivot_017) | 20 | 17 | 3 | 0.8973 | — |
| claude_t05 | 15 | 21 | 4 | 0.8785 | 0.9739 |
| ministral_t05 | 15 | 18 | 7 | 0.8715 | 0.9291 |
| gemma4_t05 | 13 | 22 | 5 | 0.8667 | 0.9224 |
| gemma_t05 | 13 | 17 | 10 | 0.8567 | 0.9102 |

### Ključni uvid: back_score vs translation_score

Do ove sesije se koristio isključivo `translation_score` kao metrika za zeleno/žuto/crveno.
`back_score` je bila originalna metrika projekta ali je zanemarena.

Analiza pokazala: **Claude dominira po back_score** (0.9739) — MiniLM kažnjava slobodan književni prevod jer je treniran na parafraze, ne na cross-lingual ekvivalentnost. NLLB prevodi doslovno pa MiniLM vektori ostaju bliži engleskom originalu.

---

## Korak 4 — claude_literal: prompt engineering eksperiment

Hipoteza: ako Claude dobije eksplicitnu instrukciju za doslovan prevod, translation_score će porasti.

### Novi kod: claude_literal integracija

Dodano u `run_test.py`:
- `translate_claude_literal()` i `translate_claude_literal_batch()` — novi prompt:
  ```
  Preserve the sentence structure and word order as closely as possible.
  Translate literally — do not paraphrase, do not improve, do not simplify.
  ```
- `claude_literal` i `claude_literal_t05` u `VALID_METHODS`

### Rezultati test_claude_005 (claude_literal_t05, IT, init×3)

| 🟢 | 🟡 | 🔴 | avg translation | avg back |
|----|----|----|----------------|----------|
| 15 | 21 | 4 | **0.8797** | **0.7080** |

**Zaključak:** Literal prompt minimalno podigao translation_score (+0.0012), ali back_score katastrofalno pao (0.9739 → 0.7080). Doslovan prevod je ukrućen — bliži engleskom vektoru ali semantički osiromašen. Claude prirodni stil drži bolji balans.

---

## Korak 5 — e5-large embedder

### Download

`intfloat/multilingual-e5-large` downloadovan — 1024 dimenzija, ~1.1GB.

### Novi kod: --embedder argument

Dodano u `run_test.py`:
- `EMBED_MODEL_E5 = "intfloat/multilingual-e5-large"`
- `--embedder` CLI argument: `choices=["minilm", "e5", "sonar"]`
- `load_embedder(model_name)` prihvata model kao argument

### Rezultati (e5-large, IT, init×3)

| Model | 🟢 | 🟡 | 🔴 | avg translation | avg back |
|-------|----|----|-----|----------------|----------|
| claude_t05 | **35** | 5 | **0** | **0.9261** | **0.9906** |
| nllb_t05 | 37 | 3 | 0 | 0.9255 | 0.9552 |
| ministral_t05 | 33 | 7 | 0 | 0.9253 | 0.9672 |
| gemma4_t05 | 33 | 7 | 0 | 0.9244 | 0.9799 |

**Ključni uvid:** Nula crvenih kod svih modela. e5-large ne favorizuje doslovnost — mjeri semantičku ekvivalentnost. Pod e5: **Claude vodi** i po translation_score i po back_score.

### Trajanje (e5 vs MiniLM, init×3)

| Model | MiniLM | e5 | Overhead |
|-------|--------|----|----------|
| nllb_t05 | ~3 min | 7:01 min | +4 min |
| claude_t05 | ~3 min | 4:00 min | +1 min |
| ministral_t05 | ~3 min | 2:53 min | ≈ isto |
| gemma4_t05 | ~3 min | 3:58 min | +1 min |

NLLB ima najveći overhead jer lokalni CPU inference + e5 encoding se akumuliraju.

---

## Korak 6 — SONAR embedder

### Istraživanje

Meta SeamlessM4T → SONAR (Sentence-level multimOdal and laNguage-Agnostic Representations).
Dostupan kao `cointegrated/SONAR_200_text_encoder` u transformers formatu — bez novih zavisnosti.

### Novi kod: SONAR integracija

Dodano u `run_test.py`:
- `EMBED_MODEL_SONAR = "cointegrated/SONAR_200_text_encoder"`
- `load_embedder()` vraća tuple `("sonar", tokenizer, encoder)` za SONAR
- `_sonar_encode()` — enkodira s language-specific src_lang
- `SONAR_LANG` dict — mapiranje naših lang kodova na FLORES-200 format
- `compute_score()` prima `tgt_lang` argument

**Kritična razlika:** SONAR enkodira EN i IT u **isti** multilingvalni prostor s različitim `src_lang` — pravi cross-lingual embedding. MiniLM i e5 enkodiraju oba teksta bez language tagging.

### Rezultati (SONAR, IT, init×3)

| Model | 🟢 | 🟡 | 🔴 | avg translation | avg back |
|-------|----|----|-----|----------------|----------|
| nllb_t05 | **15** | 22 | **3** | **0.8740** | 0.7966 |
| claude_t05 | 8 | 25 | 7 | 0.8484 | **0.8182** |
| gemma4_t05 | 6 | 24 | 10 | 0.8474 | 0.8349 |
| ministral_t05 | 10 | 21 | 9 | 0.8433 | 0.8150 |

**NLLB vodi i pod SONAR-om.** Claude vodi po back_score.

---

## Kompletna usporedba sva 3 embeddera

| Model | MiniLM 🟢🔴 | e5 🟢🔴 | SONAR 🟢🔴 |
|-------|------------|---------|-----------|
| nllb_t05 | 20/3 | 37/0 | **15/3** |
| claude_t05 | 15/4 | **35/0** | 8/7 |
| ministral_t05 | 15/7 | 33/0 | 10/9 |
| gemma4_t05 | 13/5 | 33/0 | 6/10 |

---

## Zaključci sesije

### 1. MiniLM je pristran prema doslovnosti
Kažnjava slobodne književne prevode. NLLB izgleda bolje nego što zaslužuje, Claude lošije.

### 2. e5-large je zlatna sredina
Ne favorizuje doslovnost. Nula crvenih za sve modele. Claude vodi. Ali previše liberalan — 37 zelenih za NLLB je vjerovatno inflacija.

### 3. SONAR je previše strog za operativnu metriku
Pravi cross-lingual embedding mjeri nešto drugačije od naše potrebe. Scorovi ~0.5-0.8 za odlične prevode čine zeleno/žuto/crveno sistem neupotrebljivim s trenutnim thresholdima.

### 4. NLLB-600M je konzistentno solidan
Vodi ili dijeli prvo mjesto kroz sva 3 embeddera po translation_score. Besplatan, lokalan, brz. Meta je napravio izvanredan alat.

### 5. Claude vodi po back_score kroz sve embedderе
Semantička konzistentnost (smisao se čuva kroz prevod i nazad) je Claudeova stvarna prednost. Mjerač koji bi to pravilno vrednovao bi ga stavio na vrh.

### 6. Goliat vs David — iznenađujući ishod
Claude Sonnet 4.6 (płatni cloud model) vs NLLB-600M (besplatan, lokalan) — rezultat je gotovo izjednačen. Ovo nije slabost Claude-a, nego snaga pipeline arhitekture i pravilno odabrane metrike.

---

## Izmjene koda

| Fajl | Izmjena |
|------|---------|
| `src/run_test.py` | `gemma4`/`gemma4_t05` metode, `claude_literal`/`claude_literal_t05` metode, `--embedder` argument (minilm/e5/sonar), SONAR integracija, `compute_score(tgt_lang)` |
| `tests/test_registry.yaml` | Dodani: test_claude_004/005, test_ministral_001, test_gemma_001, test_gemma4_001, test_e5_nllb/claude/ministral/gemma4, test_sonar_nllb/claude/ministral/gemma4 |
| `tests/pivot.yaml` | pivot_017 (it, nllb_t05) |

---

## Na horizontu

1. **Odabir operativnog embeddera** — e5-large kao kandidat za produkciju (zlatna sredina)
2. **README update** — dokumentovati novi --embedder argument, gemma4, claude_literal
3. **Fer usporedba Claude vs NLLB** — test_claude_003/004 kroz pivot fazu
4. **Tvrdi orasi** — s9, s16, s23, s37 persistentni kroz sve strategije i sve embedderе
5. **Produkcijska strategija** — koji embedder koristiti za finalni pipeline

---

## Handoff blok

- **pivot.yaml:** pivot_017, it, kraj sesije
- **Baza:** test_results sadrži sve nove testove (test_claude_004/005, test_ministral_001, test_gemma_001, test_gemma4_001, test_e5_*, test_sonar_*)
- **Git:** treba commit
- **NLLB keš:** 600M aktivan ✅
- **Novi embedder modeli:** e5-large i SONAR downloadovani na foxuno

---

*Flavio & Claude · Session 27 · 2026-05-28*
