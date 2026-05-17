# Session 07 — Buchenberg

**Datum:** 17. maj 2026.  
**Učesnici:** Flavio & Claude

---

## Šta smo radili

Produktivna sesija sa dva glavna pravca: GA tuning prvog kruga i uvođenje treće LLM metode (Ministral).

---

## Korak 1 — GA tuning (prvi krug)

### Parametri

Pokrenuli smo GA za IT jezik sa novim parametrima:

| Parametar | Staro | Novo |
|-----------|-------|------|
| `conv_gens` | 3 | 6 |
| `conv_thresh` | 0.005 | 0.002 |

Komanda:
```bash
nohup bash run30.sh \
  --sent_from 1 --sent_to 40 --lang it \
  --conv_gens 6 --conv_thresh 0.002 \
  > logs/run30_ga_tuning_it.log 2>&1 &
```

### Rezultati GA tuninga

| Metrika | Session 06 | Session 07 |
|---------|-----------|-----------|
| Obrađeno | 6 rečenica | 20 rečenica |
| Prešlo na zeleno | 1/6 | 4/20 |
| Poboljšano (ista boja) | — | 13/20 |
| Bez promjene | — | 3/20 |
| Pogoršano | — | 0/20 |
| Crvene → žute | — | 3/4 |
| Ostalo crveno | — | 1/4 (s37) |
| Trajanje | ~5 min | ~52 min |

**Ključni uvid:** `conv_gens=6` daje GA više prostora — poboljšanja u gen 5, 8, 10 koja bi sa starim `conv_gens=3` bila izgubljena. s35 posebno — 9.5 min, 19 generacija, poboljšanje u tri odvojena skoka.

### Diskusija o brzini GA

Za cijeli Hound (3.852 rečenica) GA bi trajao ~10+ dana. Razlog: NLLB CPU-bound.

**Odluka:** NLLB se ne koristi u GA crossover/mutaciji — samo kao inicijalna individua. GA iteracije idu samo kroz LLM-ove (Gemma, Ministral).

---

## Korak 2 — Uvođenje treće LLM metode (Ministral)

### Istraživanje modela

Pretražili smo Ollama Cloud za multilingvalne modele. Dostupni cloud modeli ne uključuju Mistral Nemo, ali imaju **ministral-3:14b** — Mistral familija, poznata po evropskim jezicima.

Test prevoda i batch moda — oba uspješna, ~0.7-1.2 sec po rečenici u single modu, ~1.8 sec za 5 rečenica u batch modu.

### Izmjene run_test.py

Dodane 2 nove metode: `ministral` i `ministral_t05`.

Arhitekturalna odluka: dodali smo `model` parametar u sve 4 LLM funkcije (`translate_gemma`, `back_translate_gemma`, `translate_gemma_batch`, `back_translate_gemma_batch`) — Ministral koristi **isti kod**, samo drugi model string. Ortogonalno.

| # | Izmjena |
|---|---------|
| 1 | Docstring — dokumentacija novih metoda |
| 2 | `MINISTRAL_MODEL` konstanta (env override podržan) |
| 3 | `VALID_METHODS` proširen |
| 4-7 | `model` parametar u svim LLM funkcijama |
| 8-9 | `dispatch_translate` i `dispatch_back_translate` — novi elif |
| 10 | Batch loop — novi elif blokovi |

### Bug — VARCHAR(10) prelaz na VARCHAR(20)

`ministral_t05` ima 13 znakova — premašuje stari limit kolone `method VARCHAR(10)`.

**Fix:**
```sql
ALTER TABLE test_results ALTER COLUMN method TYPE VARCHAR(20);
```

README i shema ažurirani.

### test_002 — Ministral IT

```
Knjiga: Hound of the Baskervilles
Rečenice: 1–40
Jezik: it
Metode: ministral, ministral_t05
Ukupno: 80 prevoda
Trajanje: ~2 min
```

### Poređenje Gemma vs Ministral (IT, 40 rečenica)

**Ministral bolji:** s13 (0.787→0.870), s31 (0.573→**0.851!**), s32, s36, s26, s25, s21, s24  
**Gemma bolji:** s5, s16, s17, s23, s28, s40  
**Izjednačeni:** s1, s2, s3, s4, s7, s10, s14, s20, s30, s38

### Kombinovani rezultat (test_001 + test_002)

Sa sva tri modela zajedno (gemma + nllb + ministral):

| Boja | Samo gemma+nllb | Sva 3 modela |
|------|----------------|--------------|
| Zelene | 20 | 20 (+s31 koja je bila 0.573!) |
| Žute | 16 | 16 |
| Crvene | 4 | 4 (s9, s16, s23, s37) |

**Ključni uvid:** s31 prešla iz skoro crvene (0.573) u zelenu (0.929) isključivo zahvaljujući Ministralu. Bez trećeg modela ta rečenica ostaje loša.

---

## Konceptualne diskusije

### GA i biološka analogija

Diskutirali smo o broju potomaka u GA. U prirodi: većina parova ima 1-2 potomka, neki 0. Trenutni GA uvijek daje tačno 2 djece (klasični crossover). Razmatramo varijabilni broj djece — **odgođeno za drugi krug tuninga**.

### Nova arhitektura metoda (zelena/žuta/crvena)

Dogovorena nova filozofija dodjele metoda po boji rečenice:
- **Zelena** = 2 reda (gemma + gemma_t05)
- **Žuta** = 4 reda (+ nllb + nllb_t05)
- **Crvena** = 6 reda (+ treća metoda × 2)

GA koristi samo LLM-ove za crossover/mutaciju — NLLB kao inicijalna individua.

**Implementacija odgođena** — trenutno još radimo sa standardnim pristupom.

### GA pobjednici kao nova metoda `ga`

Dogovoreno: GA pobjednik se upisuje u `test_results` kao `method = 'ga'`. **Implementacija odgođena.**

### Log poboljšanja (dogovoreno, nije implementirano)

Dodati GA summary na kraju svake rečenice i ukupnu statistiku na kraju runa.

---

## Bugovi

### Parser — escaped quotes u Ministral odgovoru

Ministral vraća JSON sa escaped navodnicima unutar stringa:
```
"\"Penso anche che...\"",
```
Naš parser ne prepoznaje taj format — pada na batch, fallback na single radi.  
**Odgođeno za sljedeću sesiju.**

---

## Izmjene fajlova

| Fajl | Izmjena |
|------|---------|
| `src/run_test.py` | Ministral metoda, model parametar, VARCHAR fix u komentaru |
| `README.md` | Tabela metoda, standard, VARCHAR napomena, datum |
| `docs/sessions/session_07.md` | Ovaj dokument |

---

## Otvoreno za sljedeću sesiju

1. **Parser fix** — escaped quotes u Ministral batch odgovoru
2. **GA pobjednici kao `method = 'ga'`** — upisati u test_results
3. **Log standardizacija** — GA summary i ukupna statistika
4. **GA drugi krug tuninga** — crossover_rate, max_children, varijabilni broj potomaka
5. **Novi jezici** — bs, sl, mk, bg, af, es, pt, ro
6. **Nova arhitektura metoda** — zelena/žuta/crvena dodjela
7. **Pipeline orchestrator** — finalni prevod iz test_results + ga_results
8. **multilingual-e5-large** — testirati kao alternativu MiniLM

---

*Flavio & Claude · Session 07 · 17. maj 2026.*

---

# Session 07 — Dopuna (nastavak sesije)

## Korak 3 — Parser fix za Ministral escaped quotes

Ministral vraća JSON sa escaped navodnicima unutar stringa što je rušilo batch parser. Iterativno smo popravili parser kroz više commitova:

- `parser strategija 5` — prepoznavanje Ministral escaped quotes formata
- `parser strategija 1b` — escaped quotes bez JSON omotača
- `parser poboljšanja i debug` — dodatne korekcije
- `parser strategija 1 prihvata više od n stavki` — uzima prvih n
- `parser strategija 1 konsolidovana` — placeholder pokriva sve formate

**Commit historija fixa:**
```
d86e169 fix: parser strategija 5 za Ministral escaped quotes format
cefba00 fix: parser strategija 1b za escaped quotes bez json omotaca
cc941dc fix: parser poboljsanja i debug
fec60de fix: parser strategija 1 prihvata vise od n stavki (uzima prvih n)
ea532c8 fix: parser strategija 1 konsolidovana - placeholder pokriva sve formate
```

## Korak 4 — Novi parametri `--score_from` i `--score_to`

Dodani parametri za scoring fazu — omogućuje rekalkulaciju scores za podskup rečenica bez ponovnog prevoda.

```
1b6f35a feat: dodani --score_from i --score_to parametri
```

## Korak 5 — Test_006

Pokrenut i završen test_006:
- Knjiga: Hound of the Baskervilles
- Rečenice: 1–40
- Jezici: hr, bg, it, pt, de, nl
- Metode: gemma, gemma_t05
- Rezultat: 480/480

### Rezultati test_006

| lang | method | tr_score | back_score |
|------|--------|----------|------------|
| bg | gemma | 0.8267 | 0.8620 |
| bg | gemma_t05 | 0.8205 | 0.8654 |
| de | gemma | 0.8508 | 0.8816 |
| de | gemma_t05 | 0.8439 | 0.8931 |
| hr | gemma | 0.8405 | 0.8780 |
| hr | gemma_t05 | 0.8527 | 0.8668 |
| it | gemma | 0.8375 | 0.8870 |
| it | gemma_t05 | 0.8531 | 0.8650 |
| nl | gemma | 0.8736 | 0.8972 |
| nl | gemma_t05 | 0.8635 | 0.9032 |
| pt | gemma | 0.8532 | 0.9083 |
| pt | gemma_t05 | 0.8483 | 0.9179 |

## Napomena o kontekst prozoru

U ovoj sesiji dostignut je limit kontekst prozora — Claude je izgubio uvid u raniji tok sesije. Ovo je poznati problem sa dugim sesijama. Rješenje: kraće sesije, češće snimanje session dokumenta.

## Otvoreno za sljedeću sesiju (ažurirano)

1. **Parser fix** — provjeriti da li je escaped quotes problem potpuno riješen
2. **GA pobjednici kao `method = 'ga'`** — upisati u test_results
3. **Log standardizacija** — GA summary i ukupna statistika
4. **GA drugi krug tuninga** — crossover_rate, max_children
5. **Novi jezici** — bs, sl, mk, af, es, ro
6. **Nova arhitektura metoda** — zelena/žuta/crvena dodjela
7. **Pipeline orchestrator**
8. **multilingual-e5-large** — testirati kao alternativu MiniLM

---

*Flavio & Claude · Session 07 dopuna · 17. maj 2026.*
