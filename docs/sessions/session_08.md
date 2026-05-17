# Session 08 — Buchenberg

**Datum:** 17. maj 2026.  
**Učesnici:** Flavio & Claude

---

## Cilj sesije

Dijagnostika i fix JSON parser buga koji je uzrokovao ~2-3% warninga (fallback na single mode) pri batch prevodu sa Gemma i Ministral metodama.

---

## Dijagnostika — test_007

Pokrenut fokusirani test sa samo 1 jezikom (hr), 40 rečenica, batch 20, samo LLM metode (bez NLLB koji nije problem):

```
test_007: hr | gemma, gemma_t05, ministral, ministral_t05 | sent 1–40
```

**Rezultat:** 4 Warninga / 8 batch poziva — svi "sve strategije parsiranja neuspješne", svi fallback na single mode.

### Root cause

Sva 4 failinga uzrokovana istom rečenicom — s26 koja sadrži:
> `'prijatelji C.C.H.'`

Model vraća **validan JSON** u kome string sadrži `\"` (escaped navodnici) ili apostrof unutar teksta. Primjer failing raw odgovora:

```json
[
  "\"Savršeno ispravno!\" rekao je Holmes.",
  "\"A onda je tu i 'prijatelji C.C.H.' Pretpostavljam..."
]
```

**Bug:** Strategija 1 radila `replace('\"', '§§§')` prije `json.loads` — što je rušilo parsiranje jer je Python `json` modul ionako nativno čita escaped navodnike. Placeholder trik nije bio potreban i bio je kontraproduktivan.

---

## Fix — refaktor `parse_gemma_batch_response`

### Stara verzija — 6 strategija, placeholder trik, dupliciran kod

- Strategija 1: `replace('\"', '§§§')` + `json.loads` — **uzrok buga**
- Strategija 5: skoro identična strategiji 1 — duplikat
- Strategija 6: split po linijama — krhko

### Nova verzija — 4 strategije, čist kod

| Strategija | Opis |
|-----------|------|
| 1 | Čisti markdown ``` blokove, direktni `json.loads` — Python nativno čita `\"` |
| 2 | Bracket counting — pronalazi `[...]` blok ako ima tekst oko JSON-a |
| 3 | Regex quoted strings — `"([^"\\]*(?:\\.[^"\\]*)*)"` |
| 4 | Numbered list — `1. tekst`, `1) tekst` |

Ključna promjena: sve strategije sada prihvaćaju `>= n` i uzimaju `[:n]` — robusnije od striktnog `== n`.

### Commit

```
d295fb6 fix: parser refaktor — uklonjen placeholder trik, standardni json.loads pokriva sve formate
```

Promjena: `38 insertions, 63 deletions` — kod je kraći i čišći.

---

## Verifikacija — test_008

Isti parametri kao test_007:

```
test_008: hr | gemma, gemma_t05, ministral, ministral_t05 | sent 1–40
```

**Rezultat: 160/160 prevoda, 0 Warninga, 0 fallbacka.**

---

## Naučene lekcije

- **Standardni alati su bolji od custom trikova.** Python `json.loads` nativno čita sve validne JSON formate uključujući escaped navodnike — nema potrebe za placeholder zamjenama.
- **Svaki "fix" treba pratiti fokusirani test.** Dijagnostički run na 1 jeziku otkrio je problem brže i jasnije nego 6-jezični run.
- **Manje koda = manje buga.** Refaktor je uklonio 63 linije koda i eliminirao problem.

---

## Otvoreno za sljedeću sesiju

1. **GA pobjednici kao `method = 'ga'`** — upisati u test_results
2. **GA drugi krug tuninga** — crossover_rate, max_children
3. **Novi jezici** — bs, sl, mk, bg, af, es, pt, ro
4. **Nova arhitektura metoda** — zelena/žuta/crvena dodjela
5. **Log standardizacija** — GA summary i ukupna statistika
6. **Pipeline orchestrator**
7. **multilingual-e5-large** — testirati kao alternativu MiniLM

---

*Flavio & Claude · Session 08 · 17. maj 2026.*
