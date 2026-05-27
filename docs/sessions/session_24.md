# Session 24 — NLLB benchmark & pivot_012

**Datum:** 2026-05-27  
**Učesnici:** Flavio & Claude

---

## Cilj sesije

Istraživanje NLLB-only pivot strategije — bez LLM modela (Ollama Cloud).
Testiranje `nllb` i `nllb_t05` kao init modela, te `facebook/nllb-200-distilled-1.3B` kao alternativa 600M modelu.

---

## Ključni nalazi

### 1. NLLB-only init strategija radi

- `nllb` (deterministički) daje solidan baseline
- `nllb_t05` (stohastički, temp=0.5) poboljšava rezultate pri ponovnom pokretanju — svaki run donosi nova poboljšanja zbog stohastičnosti
- Kombinacija `nllb` + `nllb_t05` bolji od samo `nllb`
- **Kriterij zaustavljanja init faze:** 3 uzastopna runa bez smanjenja crvenih ni u jednom jeziku

### 2. nllb-200-distilled-1.3B vs 600M

| Model | Trajanje (120 prevoda, 3 jezika) | RAM |
|-------|----------------------------------|-----|
| 600M | ~177 sec (~3 min) | ~5.5 GB |
| 1.3B | ~273 sec (~4.5 min) | ~8.9 GB |

- 1.3B je **~1.5× sporiji** od 600M
- 1.3B daje bolji kvalitet — posebno vidljivo za HR (crvene pale s 3 na 1 u prvom runu)
- Sistematična usporedba kvaliteta 600M vs 1.3B ostaje za sljedeću sesiju

### 3. Bottleneck analiza

| Komponenta | Vrijeme | % |
|-----------|---------|---|
| NLLB inference | 268 sec | 98% |
| MiniLM scoring | 5 sec | 2% |
| DB upis (120 slogova) | 1.66 sec | <1% |

**Zaključak:** Jedini bottleneck je NLLB inference. DB i scoring su zanemarljivi.

### 4. Pivot faza vs init iteracije

- Init×6 (600M, ~18 min) ≈ Pivot×1 (~22 min) po broju operacija
- Pivot faza donosi crossover poboljšanja koje init ne može (SR←HR, SR←SL)
- Optimalna strategija: više init iteracija → pivot kao "finishing touch"

### 5. pivot_011 rezultati (fr, hr, de, it — nllb+nllb_t05, 1.3B)

| Lang | Init 🟢🔴 | +Pivot 🟢🔴 |
|------|----------|------------|
| FR | 24 / 2 | 24 / 2 |
| HR | 24 / 1 | 24 / 1 |
| IT | 22 / 3 | 22 / 3 |
| DE | 23 / 3 | 23 / 3 |

### 6. pivot_012 rezultati (sr, hr, sl — nllb_t05, 1.3B)

| Lang | Init×7 (600M) 🟢🔴 | +1.3B init×2 🟢🔴 | +Pivot 🟢🔴 |
|------|-------------------|------------------|------------|
| HR | 24 / 3 | 24 / 1 | 24 / 1 |
| SL | 22 / 3 | 22 / 3 | 22 / 1 |
| SR | 17 / 5 | 18 / 5 | 21 / 3 |

---

## Tvrdi orasi (persistentni kroz sve testove)

- **s2** — "by Sir Arthur Conan Doyle" — SR prevodi u ćirilicu, MiniLM daje nizak score
- **s9** — "the stick" kontekst — SR gubi smisao
- **s31** — "in your debt" — idiom problem
- **s37/s38** — parser fragmenti, poznati problem iz test_018

---

## Na horizontu

1. **Sistematična usporedba 600M vs 1.3B** — isti test, oba modela, mjerenje kvaliteta i brzine
2. **nllb-200-distilled-1.3B** downloadovan na foxuno (~5GB keš)
3. Vraćanje na 600M u `run_pivot_init.py` — trenutno je 1.3B ⚠️
4. Produkcijski run — strategija tek treba biti finalizirana
5. Pipeline orchestrator za finalni output

---

## Tehnički detalji

- `run_pivot_init_bench.py` — kreiran kao benchmark verzija bez DB upisa
- `run_pivot_init.py` — trenutno koristi 1.3B model ⚠️ (treba vratiti na 600M ili donijeti odluku)
- Infrastruktura foxuno: 142GB disk slobodno, 22GB RAM available, swap 8GB

