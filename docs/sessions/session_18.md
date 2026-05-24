# Session 18 — Buchenberg

**Datum:** 24. maj 2026.
**Autor:** Flavio & Claude

---

## Cilj sesije

Dodavanje HR, BG, DE, NL u test_018. Pokretanje faza 1+2+3 i GA optimizacije za sve 4 nova jezika.

---

## Korak 1 — Inicijalizacija

Pročitani: `buchenberg_napomena.md`, `README.md`, session dokumenti 15/16/17. Health check — sve zeleno. Ollama Cloud ima 39 modela dostupno.

Stanje test_018 na početku sesije:
| Lang | 🟢 | 🟡 | 🔴 |
|------|----|----|-----|
| IT | 23 | 14 | 3 |
| PT | 20 | 20 | 0 |

---

## Korak 2 — Dodavanje jezika u test_registry.yaml

`test_018` proširen sa `[it, pt]` na `[it, pt, hr, bg, de, nl]`.

```bash
sed -i 's/langs: \[it, pt\]/langs: [it, pt, hr, bg, de, nl]/' tests/test_registry.yaml
```

---

## Korak 3 — Faze 1+2+3 za HR, BG, DE, NL

### Faza 1 — sve metode (gemma, gemma_t05, ministral, ministral_t05)
640/640 prevoda — **10 min 20 sec**

| Lang | 🟢 | 🟡 | 🔴 |
|------|----|----|-----|
| HR | 19 | 17 | 4 |
| BG | 12 | 20 | 8 |
| DE | 19 | 12 | 9 |
| NL | 24 | 13 | 3 |

### Faza 2 — ministral+ministral_t05 za žute+crvene
172/320 prevoda — **3 min 9 sec**

| Lang | 🟢 | 🟡 | 🔴 |
|------|----|----|-----|
| HR | 20 | 16 | 4 |
| BG | 12 | 21 | 7 |
| DE | 20 | 11 | 9 |
| NL | 24 | 13 | 3 |

### Faza 3 — nllb+nllb_t05 za crvene
46/320 prevoda — **2 min 24 sec**

| Lang | 🟢 | 🟡 | 🔴 |
|------|----|----|-----|
| HR | 20 | 18 | 2 |
| BG | 12 | 27 | 1 |
| DE | 22 | 11 | 7 |
| NL | 25 | 13 | 2 |

**Zapažanje:** NLLB izuzetno efikasan na BG — 7 crvenih → 1.

---

## Korak 4 — GA optimizacija

### HR — 3 runde GA

| Runda | Trajanje | 🟢 | 🟡 | 🔴 |
|-------|----------|----|----|-----|
| GA1 | 15 min 31 sec | 22 | 17 | 1 |
| GA2 | 12 min 24 sec | 22 | 17 | 1 |
| GA3 | 12 min 14 sec | **23** | 16 | 1 |

GA3 donio +1 zelenu zahvaljujući stohastičnosti. 1 crvena ostaje (fragment — s37).

### DE — 3 runde GA

| Runda | Trajanje | 🟢 | 🟡 | 🔴 |
|-------|----------|----|----|-----|
| GA1 | 13 min 53 sec | 25 | 10 | 5 |
| GA2 | 11 min 9 sec | 25 | 10 | 5 |
| GA3 | 13 min 35 sec | **26** | 9 | 5 |

GA3 donio +1 zelenu. 5 crvenih ostaju tvrdi orasi.

### BG — 3 runde GA

| Runda | Trajanje | 🟢 | 🟡 | 🔴 |
|-------|----------|----|----|-----|
| GA1 | 20 min 51 sec | 16 | 23 | 1 |
| GA2 | 16 min 53 sec | 16 | 23 | 1 |
| GA3 | 18 min 39 sec | **17** | 22 | 1 |

GA3 donio +1 zelenu. 1 crvena ostaje.

### NL — 3 runde GA

| Runda | Trajanje | 🟢 | 🟡 | 🔴 |
|-------|----------|----|----|-----|
| GA1 | 8 min 49 sec | 27 | 12 | 1 |
| GA2 | 8 min 13 sec | **28** | 12 | **0** |
| GA3 | 6 min 39 sec | 28 | 12 | 0 |

GA2 eliminisao jedinu crvenu — **NL nula crvenih!**

---

## Finalno stanje test_018

| Lang | 🟢 | 🟡 | 🔴 |
|------|----|----|-----|
| IT | 23 | 14 | 3 |
| PT | 20 | 20 | 0 |
| HR | 23 | 16 | 1 |
| BG | 17 | 22 | 1 |
| DE | 26 | 9 | 5 |
| NL | 28 | 12 | 0 |

---

## Naučene lekcije

- **GA3 se isplati** — treći round GA (koji izgleda redundantan) donio +1 zelenu za HR, DE i BG zahvaljujući stohastičnosti LLM modela. 15 minuta nije večnost.
- **NLLB dominira na BG** — Faza 3 (NLLB) smanjila crvene s 7 na 1, daleko efikasnije od LLM metoda.
- **NL je najjači jezik** u ovoj sesiji — 28/40 zelenih, 0 crvenih.
- **DE ima najviše tvrdih oraha** — 5 crvenih koje GA ne može popraviti, vjerovatno kombinacija fragmenata i složenih rečenica.
- **GA konvergira brzo ali ne potpuno** — većina rečenica 2 generacije, ali stohastičnost povremeno pronađe bolji put i u kasnim rundama.

---

## Otvoreno za sljedeću sesiju

1. **Novi jezici** — bs, sl, mk, af, es, ro (dodati u test_018 ili novi test)
2. **multilingual-e5-large** — testirati kao alternativu MiniLM (posebno za fragmente/tvrde orahe)
3. **Pipeline orchestrator** — finalni prevod iz test_results
4. **GA tuning** — razmisliti o višim conv_gens za složene rečenice

---

## Handoff blok

- **Zadnji commit:** acc866e (session_17) — novi commit slijedi
- **Baza:** test_results — test_018 sa IT, PT, HR, BG, DE, NL podacima
- **test_018 langs:** `[it, pt, hr, bg, de, nl]` — ažurirano u registry
- **ga_results.metoda:** VARCHAR(40) — samo u bazi, nije u CREATE TABLE skripti!

---

*Flavio & Claude · Session 18 · 24. maj 2026.*
