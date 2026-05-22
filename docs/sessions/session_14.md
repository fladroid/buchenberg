# Session 14 — Buchenberg

**Datum:** 21. maj 2026.
**Autor:** Flavio & Claude

---

## Šta smo radili

Implementiran i pokrenut **test_013** — isti setup kao test_012 (6 jezika, 40 rečenica, Hound of the Baskervilles), ali sa refaktorisanim GA: NLLB izbačen iz mutatora, samo gemma+ministral sa temperature=0.8.

### Redoslijed rada

1. Health check — infrastruktura OK
2. Refaktor `run_ga.py` — uklonjen NLLB iz GA mutatora, dodani `GA_MUTATORI`, `GA_TEMPERATURE`, `MINISTRAL_MODEL` konstante, unificirana `translate_llm()` funkcija
3. Dodan `*.bak` u `.gitignore`
4. Registrovan `test_013` u `test_registry.yaml`
5. Faza 1 — gemma + gemma_t05 za svih 6 jezika (6 min 9 sec)
6. Faza 2 — ministral + ministral_t05 za žute+crvene (3 min 24 sec)
7. Faza 3 — nllb + nllb_t05 za crvene (3 min 20 sec)
8. GA — serijalno, jezik po jezik: hr → bg → de → nl → it → pt
9. ga_save_winners za svaki jezik po završetku GA

### Trajanje GA po jeziku

| Jezik | Trajanje | GA pobjednika |
|-------|----------|---------------|
| HR    | 1 min 19 sec | 1 |
| BG    | 9 min 8 sec  | 9 |
| DE    | 2 min 23 sec | 1 |
| NL    | 0 min 56 sec | 1 |
| IT    | 2 min 51 sec | 2 |
| PT    | 4 min 42 sec | 6 |

---

## Finalno stanje test_013

| Lang | 🟢 Zelene | 🟡 Žute | 🔴 Crvene |
|------|-----------|---------|-----------|
| HR   | 18        | 19      | 3         |
| BG   | 14        | 24      | 2         |
| DE   | 22        | 13      | 5         |
| NL   | 24        | 15      | 1         |
| IT   | 16        | 20      | 4         |
| PT   | 16        | 23      | 1         |

---

## Poređenje test_012 vs test_013

| Jezik | 🟢 t012 | 🟢 t013 | 🔴 t012 | 🔴 t013 |
|-------|---------|---------|---------|---------|
| HR    | 23      | 18      | 3       | 3       |
| BG    | 16      | 14      | 4       | 2       |
| DE    | 20      | 22      | 6       | 5       |
| NL    | 26      | 24      | 1       | 1       |
| IT    | 20      | 16      | 3       | 4       |
| PT    | 17      | 16      | 3       | 1       |

---

## Problemi i zapažanja

**Hipoteza djelimično potvrđena:** GA je 2-3x brži (ukupno ~21 min vs ~90 min u test_012). Međutim, kvalitet je blago lošiji — manje zelenih na HR, BG, IT.

**Glavni razlog pada zelenih:** faza 1 u test_013 koristi samo gemma+gemma_t05. Ministral dolazi tek u fazi 2 (samo za žute+crvene) — zelene iz faze 1 nikad ne vide ministral. U test_012 ministral je bio u fazi 1 za sve rečenice. Ovo je posebno izraženo na IT.

**Tvrdi orasi:** s37 i s38 su crvene na svim jezicima u oba testa. Problem vjerovatno nije u metodi prevoda nego u MiniLM embedder modelu koji loše mjeri semantičku sličnost za te konkretne fraze. Kandidat za `multilingual-e5-large` eksperiment.

**s37 fitness po jeziku:**
- HR: 0.7468, BG: 0.7221, DE: 0.7008, NL: crven, IT: crven, PT: crven

**GA crossover koristi srodne jezike kao pivot** (npr. `ga_sr` za HR i BG naslove) — legitimna strategija, ostaviti kako jest.

**BG sporiji od ostalih** jer ima najviše žutih rečenica (24) — GA obrađuje sve žute+crvene, ne samo crvene.

---

## Novo u ovoj sesiji

- `run_ga.py` refaktorisan — NLLB uklonjen iz GA mutatora
- `*.bak` dodan u `.gitignore`
- `test_013` dodan u `test_registry.yaml`

---

## Plan za sljedeću sesiju

### test_014 — ministral u fazi 1

Hipoteza iz ove sesije: dodati ministral+ministral_t05 nazad u fazu 1 (za sve rečenice), zadržati LLM-only GA. Očekujemo test_012 kvalitet + test_013 brzinu GA.

### Ostalo
- Novi jezici: bs, sl, mk, af, es, ro
- multilingual-e5-large — testirati kao alternativu MiniLM (posebno za s37/s38)
- Pipeline orchestrator — finalni prevod iz test_results

---

## Napomene za Claude

- `langs` je uvijek lista
- GA pokretati serijalno (Ollama besplatni tier)
- `count_colors.py` je kanonski način provjere stanja
- `ga_save_winners.py` pokrenuti odmah nakon GA za svaki jezik
- Protokol komandi nepregovoriv — prikaži, čekaj OK, izvrši
- `docker exec pgdb psql` komande idu ručno na balsam serveru
