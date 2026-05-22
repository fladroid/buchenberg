# Session 16 — Buchenberg

**Datum:** 22. maj 2026.
**Autor:** Flavio & Claude

---

## Cilj sesije

Nastavak nakon session_15. GA run za test_018 IT, fix VARCHAR greške u ga_results, finalizacija test_018 IT.

---

## Korak 1 — GA run test_018 IT

Pokrenut GA za test_018, IT, rečenice 1-40.

### Bug — VARCHAR(20) u ga_results.metoda

GA pao sa greškom `StringDataRightTruncation` — kolona `metoda` u `ga_results` je VARCHAR(20), ali crossover generiše metode poput `ministral+ministral` (21 znak) ili `mut:ministral+ministral` (24 znaka).

**Fix:**
```sql
ALTER TABLE ga_results ALTER COLUMN metoda TYPE VARCHAR(40);
```

Izvršeno na balsam serveru putem `balsam:run_command`.

---

## Korak 2 — GA rezultati test_018 IT

GA trajanje: **17 min 20 sec** — 23 optimizacije, 17 zelenih preskočeno.

### Finalno stanje test_018 IT

| Iteracija | 🟢 | 🟡 | 🔴 |
|-----------|----|----|-----|
| Faza 1    | 16 | 18 | 6  |
| Faza 2    | 16 | 19 | 5  |
| Faza 3    | 16 | 21 | 3  |
| Faza 1b   | 16 | 21 | 3  |
| Faza 2b   | 16 | 21 | 3  |
| Faza 3b   | 16 | 21 | 3  |
| Faza 1c   | 17 | 20 | 3  |
| Faza 2c   | 17 | 20 | 3  |
| Faza 3c   | 17 | 20 | 3  |
| **GA**    | **19** | **18** | **3** |

GA dodao 2 zelene:
- **s22** ("Why so?") — 0.8104 → **0.9228** (gen 3)
- **s29** ("It may be that you are not yourself luminous...") — 0.8937 → **0.9085** (gen 2)

3 crvene ostaju tvrdi orasi: s23, s37 i još jedna.

### Zapažanja o GA ponašanju

- Većina rečenica konvergira nakon **2 generacije** bez poboljšanja — GA brzo odustaje
- Kada GA uspije (s22, s29), poboljšanje je značajno (0.81 → 0.92)
- Kratke rečenice ("Why so?") lake za GA — pivot jezici donose raznolike interpretacije
- Dugačke složene rečenice teže za GA — konvergencija bez poboljšanja

---

## Korak 3 — Upis GA pobjednika

```bash
venv/bin/python src/ga_save_winners.py --test_id test_018 --lang it
```

Rezultat: **23 GA pobjednika upisano u test_results**.

---

## Izmjene fajlova u ovoj sesiji

| Fajl | Izmjena |
|------|---------|
| `ga_results.metoda` | VARCHAR(20) → VARCHAR(40) (ALTER TABLE na balsam) |
| `tests/test_registry.yaml` | Dodani test_014 do test_018 |
| `docs/sessions/session_16.md` | Ovaj dokument |

---

## Naučene lekcije

- **ga_results.metoda VARCHAR(20) je premalo** — crossover metode poput `ministral+ministral` (21 znak) prelaze limit. Uvijek VARCHAR(40) za metoda polje.
- **GA konvergira brzo** — `conv_gens=3` znači stop nakon 3 generacije bez poboljšanja. Za kratke rečenice to je dovoljno, za složene možda premalo.
- **GA je efikasan selektivno** — ne poboljšava sve žute/crvene, ali kada pogodi pravi pivot, skok je značajan.

---

## Otvoreno za sljedeću sesiju

1. **Proširiti test_018 na ostale jezike** — hr, bg, de, nl, pt (faze 1+2+3 + GA)
2. **GA tuning** — razmisliti o povećanju `conv_gens` za složene rečenice
3. **Novi jezici** — bs, sl, mk, af, es, ro
4. **Pipeline orchestrator** — finalni prevod iz test_results
5. **multilingual-e5-large** — testirati kao alternativu MiniLM (posebno za tvrde orahe)

---

## Handoff blok

- **Zadnji commit:** `ddb95dd feat: dodani test_014 do test_018 u registry, GA završen za test_018 IT`
- **Zadnji test:** test_018 IT kompletno završen — 🟢19 🟡18 🔴3
- **Baza:** test_results ima samo test_018 podatke (truncirano ranije u sesiji 15)
- **ga_results.metoda:** VARCHAR(40) — promjena samo u bazi, nije u CREATE TABLE skripti!

---

*Flavio & Claude · Session 16 · 22. maj 2026.*
