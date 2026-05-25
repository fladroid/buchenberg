# Session 20 — Buchenberg

**Datum:** 25. maj 2026.
**Autor:** Flavio & Claude

---

## Cilj sesije

Testiranje `gemma4:31b-cloud` kao nove metode prevoda u fazi 2. Istraživanje konceptualnog redizajna pipeline-a — eliminacija back-translationa.

---

## Korak 1 — Inicijalizacija

Pročitani: `buchenberg_napomena.md`, `README.md`, session dokumenti 17/18/19. Health check — sve zeleno.

Stanje test_018 na početku sesije (14 jezika):
| Lang | 🟢 | 🟡 | 🔴 |
|------|----|----|-----|
| IT | 23 | 14 | 3 |
| PT | 20 | 20 | 0 |
| HR | 23 | 16 | 1 |
| BG | 17 | 22 | 1 |
| DE | 26 | 9 | 5 |
| NL | 28 | 12 | 0 |
| FR | 28 | 11 | 1 |
| RO | 15 | 23 | 2 |
| ES | 19 | 20 | 1 |
| AF | 11 | 9 | 20 |
| BS | 20 | 17 | 3 |
| SR | 21 | 17 | 2 |
| SL | 17 | 19 | 4 |
| MK | 18 | 20 | 2 |

---

## Korak 2 — Razrješavanje Ollama Cloud autentikacije

Problem iz session_19: curl testovi vraćali `unauthorized`. Testiranjem Python skriptom (identičnom onoj u projektu — `requests` + `dotenv`) potvrđeno da autentikacija radi ispravno za oba trenutna modela:

- `gemma3:12b` ✅
- `ministral-3:14b` ✅

**Zaključak:** curl testovi nisu koristili ispravnu autentikaciju. Python + requests + dotenv radi kako treba. Ovo je bio lažni alarm iz session_19.

---

## Korak 3 — Testiranje gemma4:31b-cloud

Novi model na Ollama Cloud listi: `gemma4:31b-cloud`. Test autentikacije prošao uspješno.

### Implementacija run_test_gemma4.py

Kreirana kopija `run_test.py` → `run_test_gemma4.py` s minimalnim izmjenama:

1. Nova konstanta: `GEMMA4_MODEL = "gemma4:31b-cloud"`
2. `VALID_METHODS` proširen: dodani `gemma4` i `gemma4_t05`
3. `dispatch_translate()` — dodana dva `elif` bloka
4. `dispatch_back_translate()` — dodan `elif` blok
5. Batch loop u `main()` — dodana dva `elif` bloka (translate + back-translate)

**Napomena:** `run_test_gemma4.py` je **temporarni skript** za testiranje — nije dio permanentnog pipeline-a.

---

## Korak 4 — Faza 2 sa gemma4 za sve jezike

Pokrenuta faza 2 (`--score_to 0.8999`) sa metodama `gemma4 gemma4_t05` za sve 14 jezika test_018.

### Rezultati po jezicima

| Lang | 🟢 prije | 🟢 poslije | 🔴 prije | 🔴 poslije | Δ🟢 | Δ🔴 |
|------|---------|-----------|---------|-----------|-----|-----|
| FR | 28 | 29 | 1 | 1 | +1 | 0 |
| IT | 23 | 24 | 3 | 3 | +1 | 0 |
| PT | 20 | 20 | 0 | 0 | 0 | 0 |
| ES | 19 | 20 | 1 | 1 | +1 | 0 |
| RO | 15 | 15 | 2 | 2 | 0 | 0 |
| DE | 26 | 26 | 5 | 5 | 0 | 0 |
| NL | 28 | 28 | 0 | 0 | 0 | 0 |
| AF | 11 | 11 | 20 | 20 | 0 | 0 |
| HR | 23 | 23 | 1 | **0** | 0 | **-1** |
| SR | 21 | 22 | 2 | 2 | +1 | 0 |
| BG | 17 | 18 | 1 | 1 | +1 | 0 |
| BS | 20 | 21 | 3 | **2** | +1 | **-1** |
| MK | 18 | 19 | 2 | 2 | +1 | 0 |
| SL | 17 | 19 | 4 | **3** | +2 | **-1** |

### Zapažanja

- **Romanski jezici:** gemma4 dao +1 zelenu za FR, IT, ES. PT i RO bez pomaka (već optimizovani ili tvrdi orasi).
- **Germanski jezici:** DE, NL, AF bez ikakve promjene — zid koji gemma4 ne može probiti.
- **Južnoslavenski jezici:** Najjači učinak — HR eliminisao jedinu crvenu (s37 bio tvrdi orah kroz GA runde, gemma4 ga podigao na 0.977), BS i SL smanjili crvene.
- **AF ostaje otvoreni problem** — 20 crvenih, ni jedan model nije uspio probiti taj zid.

### Finalno stanje test_018 nakon sesije 20

| Lang | 🟢 | 🟡 | 🔴 |
|------|----|----|-----|
| IT | 24 | 13 | 3 |
| PT | 20 | 20 | 0 |
| HR | 23 | 17 | 0 |
| BG | 18 | 21 | 1 |
| DE | 26 | 9 | 5 |
| NL | 28 | 12 | 0 |
| FR | 29 | 10 | 1 |
| RO | 15 | 23 | 2 |
| ES | 20 | 19 | 1 |
| AF | 11 | 9 | 20 |
| BS | 21 | 17 | 2 |
| SR | 22 | 16 | 2 |
| SL | 19 | 18 | 3 |
| MK | 19 | 19 | 2 |

---

## Korak 5 — Konceptualna rasprava: eliminacija back-translationa

### Trenutni pipeline (po rečenici, po metodi)

```
EN → [LLM] → RF (prevod)
RF → [LLM] → RFE (back-translation)
embed(EN) + embed(RFE) → cosine → score
embed(EN) + embed(RF)  → cosine → translation_score
```

**Trošak:** 2 LLM poziva + 2 embedding poziva po metodi po rečenici.

### Predloženi novi pipeline

```
EN → [LLM] → RF (prevod)
embed(EN) + embed(RF) → cosine → translation_score
```

**Trošak:** 1 LLM poziv + 2 embedding poziva po metodi po rečenici.

### Analiza

**Šta se gubi:**
- `score` kolona (cosine EN↔back-translation) — već zaključeno da je `translation_score` pouzdaniji pokazatelj
- Back-translation kao tekst (potencijalno korisno za debugging)

**Šta se dobija:**
- ~2x ubrzanje na LLM pozivima
- Jednostavniji pipeline

**GA kompatibilnost:**
GA koristi `translation_score` kao fitness funkciju — `cosine(embed(EN), embed(IT_prevod))`. Back-translation nije dio GA logike. GA ostaje **u potpunosti funkcionalan** bez back-translationa.

**Kvalitet scoringa:**
`translation_score` je direktna semantička sličnost EN originala i prevoda u ciljnom jeziku. Ovo je bolji signal od back-translation cosine jer ne uvodi grešku drugog LLM poziva. Već u trenutnom pipeline-u `translation_score` koristimo kao primarni pokazatelj kvaliteta.

### Nova schema (skica)

```
Jedinstveni identifikator: (book_id, sentence_id, model, target_lang)

Kolone:
  - id
  - book_id / sentence_id
  - model (gemma3:12b, ministral-3:14b, gemma4:31b-cloud, ...)
  - target_lang
  - translated_text
  - translation_score   ← cosine(EN, prevod)
  - winner (bool)
  - created_at
```

`score` kolona (back-translation cosine) se eliminiše. `back_translation` tekst se eliminiše.

### Otvorena pitanja

1. **Kako definisati "pobjednika" bez back-translationa?** — `translation_score` je dovoljan za selekciju pobjednika među metodama.
2. **Da li je `translation_score` bez back-translationa dovoljno pouzdan za GA?** — Da, GA fitness je već `translation_score`.
3. **Crossjezični embeddinzi:** MiniLM (`paraphrase-multilingual-MiniLM-L12-v2`) je treniran za crossjezičnu sličnost — cosine(EN, IT) je smislen i pouzdan signal.

---

## Naučene lekcije

- **gemma4 je brz i konzistentan** — batch obrada radi odlično, odgovori su čisti (bez objašnjenja), ubrzanje vidljivo.
- **gemma4 pomaže na južnoslavenskim jezicima** — posebno impresivno za HR gdje je eliminisao tvrdog oraha s37 koji GA nije mogao popraviti.
- **Tvrdi orasi su strukturalni, ne modelski** — AF (20 crvenih), DE (5 crvenih), fragmenti — ni jedan model ne može probiti taj zid jer problem nije u modelu nego u prirodi rečenica/embeddings.
- **`translation_score` je bolji signal od `score`** — ovo je potvrđeno kroz sve dosadašnje sesije.

---

## Otvoreno za sljedeću sesiju (prioritetno)

1. **Odluka o redizajnu pipeline-a** — eliminacija back-translationa (Flavio razmišlja)
2. **GA za RO, ES, BS, SR, SL, MK** — još nisu pokrenuti GA runde
3. **AF** — poseban slučaj, 20 crvenih; razmotriti drugačiji pristup
4. **multilingual-e5-large** — testirati kao alternativu MiniLM

---

## Handoff blok

- **test_018 langs:** `[it, pt, hr, bg, de, nl, fr, ro, es, af, bs, sr, sl, mk]`
- **Novi fajl:** `src/run_test_gemma4.py` — temporarni skript, nije u git-u
- **ga_results.metoda:** VARCHAR(40) — samo u bazi, nije u CREATE TABLE skripti
- **Zadnji commit:** session_19 — session_20 treba pushati

---

*Flavio & Claude · Session 20 · 25. maj 2026.*
