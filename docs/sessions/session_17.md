# Session 17 — Buchenberg

**Datum:** 23. maj 2026.
**Autor:** Flavio & Claude

---

## Cilj sesije

Nastavak test_018 — iteracije GA za IT, analiza tvrdih oraha, dodavanje PT u test_018, kompletne faze + GA za PT.

---

## Korak 1 — Inicijalizacija

Pročitani: `buchenberg_napomena.md`, `README.md`, session dokumenti 14/15/16. Health check — sve zeleno. Ollama Cloud ima mnoštvo novih modela (gemma4, deepseek-v4, kimi-k2, qwen3...).

---

## Korak 2 — IT: GA2 i GA3

Stanje na početku sesije: test_018 IT 🟢19 🟡18 🔴3.

| Run | Trajanje | 🟢 | 🟡 | 🔴 |
|-----|----------|----|----|-----|
| GA2 | 13 min 43 sec | 22 | 15 | 3 |
| GA3 | 11 min 14 sec | 23 | 14 | 3 |

GA2 dodao 3 zelene (s6, s28, jedna više). GA3 dodao još 1. Sistem konvergira — svaki krug donosi manje poboljšanja.

---

## Korak 3 — Analiza tvrdih oraha IT

Tri trajne crvene: **s9, s23, s37**.

| ID | Best score | Original |
|----|-----------|---------|
| s9 | 0.7999 | *It was just such a stick as the old-fashioned family practitioner used to carry—dignified, solid, and reassuring.* |
| s23 | 0.7746 | *"Because this stick, though originally a very handsome one has been so knocked about...* |
| s37 | 0.7782 | *"There are certainly one or two indications upon the stick.* |

**Zaključak:** s23 i s37 su **fragmenti** — parser razbio govorni blok na dvije rečenice po tački (s23+s24, s37+s38 su logički jedne misli). MiniLM evaluira fragment → nizak cosine score. Problem nije u prijevodu nego u parsiranju. Odluka: ostaviti originale kakvi jesu.

---

## Korak 4 — Dodavanje PT u test_018

PT dodan u `test_registry.yaml` (`langs: [it, pt]`) umjesto novog test_019 — radi boljeg praćenja i otkrivanja eventualnih grešaka.

---

## Korak 5 — PT: Faze 1+2+3 (tri kruga)

| Iteracija | 🟢 | 🟡 | 🔴 |
|-----------|----|----|-----|
| Faza 1 | 16 | 20 | 4 |
| Faza 2 | 16 | 21 | 3 |
| Faza 3 | 16 | 23 | 1 |
| Faze 1b+2b+3b | 16 | 23 | 1 |
| Faze 1c+2c+3c | 16 | 23 | 1 |

Sistem konvergirao nakon prvog kruga — ponavljanje nije donijelo poboljšanje.

---

## Korak 6 — PT: GA1

GA trajanje: **22 min 39 sec** — 24 optimizacije, 16 zelenih preskočeno.

**Finalno stanje PT: 🟢20 🟡20 🔴0** — nula crvenih!

Posebno zapažanje: s6 (tvrdi orah, početni score 0.7138) GA podigao na 0.8733 kroz 9 generacija — jedina crvena koja je prešla u žutu.

---

## Finalno stanje test_018

| Lang | 🟢 | 🟡 | 🔴 |
|------|----|----|-----|
| IT | 23 | 14 | 3 |
| PT | 20 | 20 | 0 |

---

## Naučene lekcije

- **Fragmenti su tvrdi orasi** — rečenice koje su logički dijelovi duže misli daju nizak MiniLM score bez obzira na kvalitet prijevoda. Rješenje nije spajanje — original ostaje kako jest.
- **GA konvergira brzo** — većina rečenica 2 generacije, ali kada pogodi pravi pivot skok je značajan (s6 PT: 0.71 → 0.87 kroz 9 generacija).
- **Ponavljanje faza konvergira** — nakon prvog kruga faza, drugi i treći ne donose promjenu. GA je efikasniji za dalja poboljšanja.
- **PT bez crvenih** — GA eliminisao sve 4 početne crvene.

---

## Otvoreno za sljedeću sesiju

1. **Novi jezici** — bs, sl, mk, af, es, ro (dodati u test_018 ili novi test)
2. **GA tuning** — razmisliti o `conv_gens` povećanju za složene rečenice
3. **multilingual-e5-large** — testirati kao alternativu MiniLM (posebno za fragmente)
4. **Pipeline orchestrator** — finalni prevod iz test_results

---

## Handoff blok

- **Zadnji commit:** `7b902bc feat: test_018 PT — faze 1+2+3 x3 + GA1; test_018 IT GA2+GA3`
- **Baza:** test_results — test_018 sa IT i PT podacima
- **ga_results.metoda:** VARCHAR(40) — samo u bazi, nije u CREATE TABLE skripti!
- **test_018 langs:** `[it, pt]` — ažurirano u registry

---

*Flavio & Claude · Session 17 · 23. maj 2026.*
