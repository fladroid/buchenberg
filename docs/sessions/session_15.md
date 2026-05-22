# Session 15 — Buchenberg

**Datum:** 22. maj 2026.
**Autor:** Flavio & Claude

---

## Cilj sesije

Nastavak razvoja pipeline-a. Otkriveni i popravljeni dva kritična buga u `run_test.py`. Potvrđeno da ponavljanje faza može poboljšati rezultate.

---

## Korak 1 — Inicijalizacija sesije

Pročitani: `buchenberg_napomena.md`, `README.md`, session dokumenti 12/13/14.

Health check — infrastruktura OK, sve zeleno.

---

## Korak 2 — Otkriveni bugovi u `run_test.py`

### Bug 1 — `ON CONFLICT DO UPDATE` bez WHERE uslova

`insert_result()` koristila bezuslovni `DO UPDATE SET` — novi prevod bi uvijek prepisao postojeći, čak i ako je novi score lošiji. Rezultat: zelene rečenice mogle pasti u žute ili crvene pri ponovnom pokretanju iste faze.

**Fix:**
```sql
ON CONFLICT (test_id, sentence_id, target_lang, method)
DO UPDATE SET
    translated_text   = EXCLUDED.translated_text,
    back_translation  = EXCLUDED.back_translation,
    score             = EXCLUDED.score,
    translation_score = EXCLUDED.translation_score,
    created_at        = NOW()
WHERE EXCLUDED.translation_score > test_results.translation_score
```

**Commit:** `4ad7e80 fix: ON CONFLICT DO UPDATE samo ako je novi score bolji`

---

### Bug 2 — `clear_test` poziv u `main()`

`clear_test()` brisala sve redove za datu kombinaciju `(test_id, langs, methods)` **prije** svakog pokretanja. Rezultat: faza 2 brisala ministral redove iz faze 1 (uključujući dobre scoreove) i upisivala nove — čime je Bug 1 fix bio potpuno irelevantan.

**Fix:** uklonjen poziv `clear_test(conn, args.test_id, langs, methods)` iz `main()`. Sistem se oslanja isključivo na `ON CONFLICT WHERE`.

**Commit:** `d5f14cb fix: uklonjen clear_test poziv — ON CONFLICT WHERE štiti bolje scoreove`

---

## Korak 3 — Eksperiment ponavljanja faza (test_018, IT)

### Hipoteza
Zbog stohastičnosti (temperature > 0), ponavljanje istih faza može dati bolje prevode. Sa ispravnim `ON CONFLICT WHERE`, score može samo rasti — nikad pasti.

### Rezultati

| Iteracija | 🟢 | 🟡 | 🔴 |
|-----------|----|----|-----|
| Faza 1    | 16 | 18 | 6  |
| Faza 2    | 16 | 19 | 5  |
| Faza 3    | 16 | 21 | 3  |
| Faza 1b   | 16 | 21 | 3  |
| Faza 2b   | 16 | 21 | 3  |
| Faza 3b   | 16 | 21 | 3  |
| Faza 1c   | **17** | 20 | 3 |
| Faza 2c   | 17 | 20 | 3  |
| Faza 3c   | 17 | 20 | 3  |

**Zaključak:** Zelene nikad nisu pale ✅. Treće ponavljanje faze 1 donijelo +1 zelenu. Sistem konvergira — dalje ponavljanje ne donosi poboljšanje.

---

## Testovi pokrenuti u ovoj sesiji

| Test | Jezici | Napomena |
|------|--------|---------|
| test_014 | hr, bg, de, nl, it, pt | Pokrenut sa bugovima — rezultati nevažeći |
| test_015 | hr, bg, de, nl, it, pt | Pokrenut sa bugovima — rezultati nevažeći |
| test_016 | it | Pokrenut djelimično sa bugovima |
| test_017 | it | Pokrenut sa Bug 1 fixom ali Bug 2 još prisutan |
| test_018 | it | **Pokrenut sa oba fixa — referentni test** |

**Napomena:** Sve tabele `test_results` i `ga_results` su truncirane na početku test_018.

---

## Izmjene fajlova u ovoj sesiji

| Fajl | Izmjena |
|------|---------|
| `src/run_test.py` | Fix 1: ON CONFLICT WHERE; Fix 2: uklonjen clear_test poziv |
| `tests/test_registry.yaml` | Dodani test_014, test_015, test_016, test_017, test_018 |
| `docs/sessions/session_15.md` | Ovaj dokument |

---

## Naučene lekcije

- **`clear_test` je bio tihi saboteur** — brisao dobre rezultate prije svakog pokretanja, čineći sve prethodne testove nepouzdanim
- **`ON CONFLICT WHERE` je neophodan** — bez njega stohastični modeli mogu degradirati rezultate
- **Ponavljanje faza je legitimna strategija** — sa ispravnim fixovima, svako ponavljanje može samo poboljšati scoreove
- **Provjera broja redova u bazi** je obavezna nakon faze 1 — očekujemo tačno `N_rečenica × N_metoda` redova

---

## Otvoreno za sljedeću sesiju

1. **GA za test_018 IT** — pokrenuti run30.sh, upisati pobjednike
2. **Proširiti test_018 na sve jezike** — hr, bg, de, nl, pt
3. **Novi jezici** — bs, sl, mk, af, es, ro
4. **Pipeline orchestrator** — finalni prevod iz test_results
5. **multilingual-e5-large** — testirati kao alternativu MiniLM

---

## Handoff blok

- **Zadnji commit:** `d5f14cb fix: uklonjen clear_test poziv`
- **Zadnji test:** test_018 IT — faze 1+2+3 × 3 iteracije, 🟢17 🟡20 🔴3
- **Baza:** test_results i ga_results truncirane — samo test_018 podaci
- **Kritično:** Svaki novi test počinje čisto — ne truncirati bazu bez eksplicitne naredbe

---

*Flavio & Claude · Session 15 · 22. maj 2026.*
