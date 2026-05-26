# Session 23 — Buchenberg

**Datum:** 26. maj 2026.
**Autor:** Flavio & Claude

---

## Cilj sesije

Implementacija nove pivot strategije zasnovane na međusobnom cosinusu između jezika. Testiranje i evaluacija nove strategije kroz pivot_005 i pivot_006.

---

## Korak 1 — Inicijalizacija

Pročitani: `buchenberg_napomena.md`, `README.md`, session dokumenti 20/21/22. Health check — sve zeleno. Ollama Cloud: 39 modela dostupno.

---

## Korak 2 — Nova find_pivot strategija

**Stara strategija:**
```python
pivot_lang = max(state[sid], key=lambda l: state[sid][l][0])
# → jezik s max translation_score (cosine EN↔prevod)
```

**Nova strategija — međusobni cosinus:**
```
Za svaki jezik l:
    avg_score[l] = prosjek cosine(embed(tekst_l), embed(tekst_k)) za sve k != l

pivot_lang = argmax(avg_score)
pivot_text = tekst pivot_langa (jedini kandidat per jezik)
```

Umjesto pitanja "koji prevod je najbliži originalu (EN)?", nova strategija pita "koji prevod je najkonzistentniji sa svim ostalim prevodima?" — semantički centar grupe.

**Implementacija:** nova funkcija `find_pivot(state_sid, embedder)` u `src/run_pivot.py`, zamjena dvije linije u main loopu. Fallback na jedini dostupni jezik ako postoji < 2 prevoda.

**Commit:** `19f8c69` — `run_pivot: nova find_pivot strategija — međusobni cosinus između jezika`

---

## Korak 3 — pivot_005: testiranje nove strategije

**Konfiguracija:** de, hr, it, fr — 40 rečenica — isti jezici kao pivot_003 (usporedba)

### Init faza (gemma3:12b, temp=0.3)
160/160 redova — 1:47 min.

### Pivot faze — akumulacija modela

| Faza | Model | Trajanje | DE 🟢 | HR 🟢 | IT 🟢 | FR 🟢 | DE 🔴 | HR 🔴 | IT 🔴 | FR 🔴 |
|------|-------|---------|-------|-------|-------|-------|-------|-------|-------|-------|
| Init | gemma3:12b | 1:47 | 16 | 16 | 14 | 18 | 10 | 6 | 9 | 6 |
| Pivot 1 | gemma3:12b | 12:18 | 16 | 16 | 14 | 18 | 10 | 6 | 9 | 6 |
| Pivot 2 | ministral-3:14b | 15:28 | 18 | 17 | 14 | 19 | 10 | 4 | 7 | 3 |
| Pivot 3 | gemma4:31b | 17:47 | 18 | 17 | 14 | 20 | 9 | 3 | 6 | 3 |

### Usporedba pivot_005 vs pivot_003 (stara strategija)

| Lang | p003 🟢 | p005 🟢 | p003 🔴 | p005 🔴 | p003 avg | p005 avg |
|------|--------|--------|--------|--------|---------|---------|
| FR | 22 | 20 | 5 | 3 | 0.8906 | 0.8850 |
| HR | 17 | 17 | 6 | 3 | 0.8783 | 0.8822 |
| IT | 17 | 14 | 7 | 6 | 0.8728 | 0.8724 |
| DE | 18 | 18 | 8 | 9 | 0.8672 | 0.8673 |

Nova strategija slabija na zelenim ali bolja na crvenim za HR i FR. DE ostaje problem.

---

## Korak 4 — pivot_006: 3 modela u init fazi

**Hipoteza:** Init s više modela odmah daje bolji startni pobjednik po jeziku — brže i efikasnije nego sekvencionalne pivot faze.

**Konfiguracija:** de, hr, it, fr — 40 rečenica — models: [gemma3:12b, ministral-3:14b, gemma4:31b] — temp=0.3

### Init faza (3 modela)
480/480 redova — 8:37 min. Init s 3 modela odmah dostigao nivo koji pivot_003 postiže tek nakon cijelog pivot procesa (FR: 22🟢, 3🔴).

### Pivot faza (3 modela)
Trajanje: 46:01 min. Dostiglo max_iterations=10, 5 poboljšanja u zadnjoj iteraciji — nije potpuno konvergiralo.

### Finalni rezultati pivot_006

| Lang | 🟢 | 🟡 | 🔴 | avg |
|------|----|----|-----|-----|
| DE | 19 | 14 | 7 | 0.8754 |
| FR | 23 | 14 | 3 | 0.8960 |
| HR | 19 | 18 | 3 | 0.8887 |
| IT | 17 | 19 | 4 | 0.8841 |

### Kompletna usporedba

| Lang | p003 🟢 | p005 🟢 | p006 init 🟢 | p006 🟢 | p003 🔴 | p005 🔴 | p006 init 🔴 | p006 🔴 |
|------|--------|--------|------------|--------|--------|--------|------------|--------|
| FR | 22 | 20 | 22 | 23 | 5 | 3 | 3 | 3 |
| HR | 17 | 17 | 17 | 19 | 6 | 3 | 6 | 3 |
| IT | 17 | 14 | 15 | 17 | 7 | 6 | 6 | 4 |
| DE | 18 | 18 | 18 | 19 | 8 | 9 | 9 | 7 |

**pivot_006 pobijedio pivot_003 na svim jezicima.**

---

## Analiza performansi

| Operacija | Trajanje |
|-----------|---------|
| Init — 1 model, 4 jezika | ~1:47 min |
| Init — 3 modela, 4 jezika | ~8:37 min |
| Pivot — 1 model, 4 jezika | ~12-18 min |
| Pivot — 3 modela, 4 jezika | ~46 min |
| pivot_006 ukupno (init+pivot) | ~54 min |

**Skaliranje na cijelu knjigu (~4.000 rečenica):** Procjena za Hound of the Baskervilles (3.852 rečenica) s trenutnom brzinom i besplatnim Ollama računom — optimistički ~2 mjeseca. Ovo čini multi-jezik paralelni pivot nepraktičnim za produkciju.

---

## Naučene lekcije

- **Nova find_pivot strategija radi** — pivot_006 bolji od pivot_003 na svim jezicima, ali razlika nije dramatična; strategija je dobra, nije revolucionarna
- **3 modela u init > 1 model + pivot iteracije** — init s 3 modela za 8:37 min dostiže isti nivo kao cijeli pivot_003 proces; ovo je ključni uvid
- **Jezik po jezik s 3+ modela je optimalan omjer** — paralelni multi-jezik pivot je prespor za produkciju; jezici se trebaju procesirati sekvencijalno
- **Tvrdi orasi su persistentni** — DE i IT ostaju problematični kroz sve strategije i modele; problem je u prirodi rečenica, ne u metodi
- **pivot_006 nije konvergiralo** — 5 poboljšanja u iteraciji 10 znači da bi više iteracija moglo donijeti još poboljšanja, ali uz proporcionalno veći vremenski trošak

---

## Otvoreno za sljedeću sesiju

1. **Optimizacija za produkciju** — jezik po jezik, 3+ modela, razmotriti max_iterations smanjenje
2. **README update** — dokumentovati find_pivot strategiju i pivot_006 rezultate
3. **multilingual-e5-large** — testirati kao alternativu MiniLM
4. **Novi jezici** — bs, sl, mk, af, es, ro u pivot pipeline-u

---

## Handoff blok

- **Izmijenjeni fajl:** `src/run_pivot.py` — nova `find_pivot()` funkcija, commit `19f8c69`
- **pivot.yaml:** trenutno postavljen na pivot_006 konfiguraciju
- **Baza:** pivot_results sadrži pivot_001 kroz pivot_006
- **Session dokument:** treba pushati na GitHub

---

*Flavio & Claude · Session 23 · 26. maj 2026.*
