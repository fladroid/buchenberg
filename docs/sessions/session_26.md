# Session 26 — Claude API integracija & pivot_016

**Datum:** 2026-05-28
**Učesnici:** Flavio & Claude

---

## Cilj sesije

1. Novi pivot test za fr, it, pt — kompletni pipeline (init3 + llm_fix + pivot)
2. Referentni test — Claude Sonnet 4.6 kao metoda prevoda (usporedba s NLLB pipeline-om)

---

## Korak 1 — Kontekst sesije

Pročitani: `buchenberg_napomena.md`, `README.md`, session_23/24/25. Health check — sve zeleno. NLLB keš na 600M (session_24 napomena o 1.3B nije bila relevantna — `run_pivot_init.py` već bio na 600M). Ollama Cloud: 39 modela dostupno.

---

## Korak 2 — pivot_016: init3 + llm_fix + pivot (fr, it, pt)

### pivot.yaml

```yaml
test_id: pivot_016
book: hound_of_the_baskervilles
sent_from: 1
sent_to: 40
langs: [fr, it, pt]
models: [nllb_t05]
temperatures: [0.5]
llm_models: [gemma4:31b]
max_iterations: 10
```

### Init3 rezultati (nllb_t05, 600M, 3× serijalno)

Trajanje: ~9:38 min.

| Lang | 🟢 | 🟡 | 🔴 | avg |
|------|----|----|-----|-----|
| FR | 24 | 14 | 2 | 0.9078 |
| IT | 20 | 16 | 4 | 0.8943 |
| PT | 17 | 21 | 2 | 0.8969 |

### LLM fix rezultati (gemma4:31b, 8 crvenih)

Trajanje: 16 sekundi. Poboljšano: **1/8** (samo s15 PT: 0.7901 → 0.8128). gemma4 nije uspio popraviti tvrde orahe (s9, s16, s23, s37).

| Lang | 🟢 | 🟡 | 🔴 | avg |
|------|----|----|-----|-----|
| FR | 24 | 14 | 2 | 0.9078 |
| IT | 20 | 16 | 4 | 0.8943 |
| PT | 17 | 22 | 1 | 0.8975 |

### Pivot faza rezultati (nllb_t05, 600M, 10 iteracija)

Trajanje: ~22:48 min.

| Lang | 🟢 | 🟡 | 🔴 | avg |
|------|----|----|-----|-----|
| FR | 25 | 14 | 1 | 0.9166 |
| IT | 23 | 13 | 4 | 0.9077 |
| PT | 22 | 18 | 0 | 0.9082 |

PT: 0 crvenih. FR: 1 crvena. IT: 4 crvene (s9, s16, s23, s37 — persistentni tvrdi orasi).

---

## Korak 3 — Analiza stanja

### Otvoreno pitanje kvaliteta i performansi

Nakon pivot_016 urađena kritička analiza:

- **Žutih previše** — 40-45% rečenica ostaje u 0.80-0.89 zoni
- **Tvrdi orasi neprobojni** — s9, s16, s23, s37 kroz sve testove i sve strategije
- **LLM fix praktički beskoristan** — 1/8 poboljšanja
- **Performance** — 33 min za 40 rečenica × 3 jezika; ~53h/jezik za punu knjigu (neprihvatljivo)
- **Pivot strategija** — crossover između loših NLLB prevoda ne može kompenzirati fundamentalno ograničenje modela

### Referentno pitanje

Flavio postavio pitanje: koliko bi Claude direktno (kao model prevoda) postigao za iste rečenice? Kao referentna tačka, ne kao zamjena za pipeline.

---

## Korak 4 — Claude API integracija (prvi pokušaji — pogrešan smjer)

### test_claude_001 — poseban skript (greška u pristupu)

Napravljen `src/run_claude_test.py` — poseban skript van pipeline-a. Greška: trebalo je od početka integrirati claude kao standardnu metodu u `run_test.py`, kao gemma i ministral.

Dodatni problemi u skriptu:
- Pogrešan naziv kolone (`sentence_text` umjesto `text`)
- Pogrešan filter (`position` umjesto `id`)
- Temperatura nije postavljena (Anthropic default = 1.0)
- Nema batch obrade — svaka rečenica poseban API poziv

Rezultati test_claude_001 (temperature=1.0, single mode):

| Lang | 🟢 | 🟡 | 🔴 | avg |
|------|----|----|-----|-----|
| FR | 15 | 17 | 8 | 0.8583 |
| IT | 13 | 22 | 5 | 0.8727 |
| PT | 13 | 17 | 10 | 0.8543 |

Trajanje: 7:43 min za 120 rečenica (single mode, ~3.8 sec/rečenica).

### test_claude_002 — integracija u run_test.py, ali bez batcha (greška)

Claude dodan kao standardna metoda (`claude`, `claude_t05`) u `run_test.py`:
- `VALID_METHODS` proširen
- `translate_claude()` i `back_translate_claude()` dodane
- `CLAUDE_MODEL = "claude-sonnet-4-6"`, `ANTHROPIC_KEY` iz `.env`

**Kritična greška:** batch if/elif blokovi nisu ažurirani za claude — `translateds` nikad ne dobija vrijednost, svaki batch pada na fallback single mode. Ovo nije bilo provjereno prije pokretanja.

Rezultati test_claude_002 (claude_t05, single mode fallback):

| Lang | 🟢 | 🟡 | 🔴 | avg |
|------|----|----|-----|-----|
| FR | 13 | 19 | 8 | 0.8538 |
| IT | 14 | 18 | 8 | 0.8722 |
| PT | 15 | 17 | 8 | 0.8655 |

Trajanje: 8:32 min za 120 rečenica (single mode).

### test_claude_003 — batch implementiran, init3, samo FR

Dodane `translate_claude_batch()` i `back_translate_claude_batch()` u `run_test.py` — isti `__!!__` separator format kao gemma_batch. Batch blokovi ažurirani.

Napravljen `run_test3.sh` — ekvivalent `run_init3.sh` za test_registry testove (pokreće `run20.sh` 3× serijalno).

Rezultati test_claude_003 (claude_t05, batch, 3× init, samo FR):

| Lang | 🟢 | 🟡 | 🔴 | avg |
|------|----|----|-----|-----|
| FR | 15 | 15 | 10 | 0.8515 |

Trajanje: **3:04 min** za 3× 40 rečenica FR — dramatično brže od single mode.

---

## Korak 5 — Analiza i otvorena pitanja

### Zašto su Claude rezultati lošiji od NLLB pipeline-a?

Ključni nalaz iz test_claude_003:

| Rečenica | translation_score | back_score |
|----------|-------------------|------------|
| s7 | 0.5149 | 1.0000 |
| s36 | 0.5986 | 1.0000 |
| s31 | 0.6584 | 1.0000 |

`back_score` ≈ 1.0 znači Claude savršeno prevodi i vraća nazad. Ali `translation_score` (direktni cosine EN↔FR) je nizak. Kod NLLB ove dvije metrike su bliže jedna drugoj.

**Ovo ukazuje na problem s metrikom, ne nužno s kvalitetom prevoda.** MiniLM možda bolje prepoznaje sličnost između engleskog i "doslovnog" NLLB prevoda nego između engleskog i slobodnijeg književnog Claude prevoda.

### Šta nedostaje za fer usporedbu

test_claude_003 = samo init3 korak. pivot_016 = init3 + llm_fix + pivot. **Ovo nije fer usporedba.** Razvoj je krenuo u pogrešnom smjeru — pravimo zaključke bez kompletnog pipeline-a za Claude.

Prave rezultate očekujemo u sljedećoj sesiji kada:
1. test_claude_003 prođe kroz llm_fix i pivot fazu (ili ekvivalent)
2. Ili se dizajnira fer eksperiment koji poštuje razlike u prirodi modela

---

## Izmjene koda

| Fajl | Izmjena |
|------|---------|
| `src/run_test.py` | Dodan `import anthropic`, `CLAUDE_MODEL`, `ANTHROPIC_KEY`, `claude/claude_t05` u `VALID_METHODS`, `translate_claude()`, `back_translate_claude()`, `translate_claude_batch()`, `back_translate_claude_batch()`, batch blokovi ažurirani |
| `src/run_claude_test.py` | Novi standalone skript (zastarjeo — koristiti `run_test.py`) |
| `run_test3.sh` | Novi skript — pokreće `run20.sh` 3× serijalno |
| `tests/test_registry.yaml` | Dodani `test_claude_002`, `test_claude_003` |
| `.env` | Dodan `ANTHROPIC_API_KEY` |

---

## Napomene za sljedeću sesiju

1. **Fer usporedba** — pokrenuti test_claude_003 kroz pivot fazu (ili llm_fix + pivot), pa porediti s pivot_016
2. **Metrika** — istražiti zašto `translation_score` i `back_score` toliko divergiraju za Claude vs NLLB; razmotriti `multilingual-e5-large`
3. **Batch za claude** — testirati da li `__!!__` separator format radi pouzdano (nije potvrđeno u ovoj sesiji)
4. **README update** — dokumentovati claude integraciju i run_test3.sh
5. **Tvrdi orasi** — s9, s16, s23, s37 persistentni kroz sve strategije i modele

---

## Handoff blok

- **pivot.yaml:** pivot_016, fr/it/pt, kraj sesije
- **Baza:** pivot_results sadrži pivot_001–pivot_016; test_results sadrži test_claude_001/002/003
- **Git:** nije pushano — treba commit na kraju
- **Ključna napomena:** `run_pivot_init.py` je na 600M modelu ✅

---

*Flavio & Claude · Session 26 · 2026-05-28*
