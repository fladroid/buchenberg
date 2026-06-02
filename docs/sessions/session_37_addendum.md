# Session 37 — Addendum

**Datum:** 2. jun 2026.

---

## Što je urađeno nakon session_37

### 1. Brisanje gemma4 prevoda

Gemma4:31b je dodijeljen ulozi sudije — ne može ocjenjivati vlastite prevode.
Svi gemma4 prevodi obrisani iz baze:

```sql
DELETE FROM bb_prev_recenica     -- 18 pobjednika
DELETE FROM bb_prevodi_recenica  -- 240 prevoda
DELETE FROM bb_prevodi_knjige    -- 6 redova
```

Napomena: `bb_modeli` sadrži duplikat `gemma4:31b` (id=8 i id=9) — nije smetalo brisanju, ali treba počistiti.

### 2. Finalni pobjednici — hr i it (s1–s40)

`bb_04_pobjednik.py` ponovo pokrenut. Svi pobjednici sada imaju `sudija_avg` — nema više fallback redova.

**Distribucija pobjednika:**

| Model | HR | IT |
|-------|----|----|
| gemma3:12b | 25 | 20 |
| ministral-3:14b | 11 | 18 |
| nllb-600M | 4 | 2 |

### 3. Otvoreno

- **Duplikat u bb_modeli** — gemma4:31b ima dva reda (id=8, id=9)
- **Proširiti na fr, de** — novi prevodni runovi
- **Export** — pokrenuti `bb_05_export.py` za hr i it

---

*Flavio & Claude · Buchenberg · Session 37 addendum · 2. jun 2026.*
