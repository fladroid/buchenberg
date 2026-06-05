# Session 51 — Hound HR s351–s400, SR/IT/DE s101–s150

**Datum:** 5. jun 2026.
**Sesija:** 51
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Health check

Sve zeleno — PostgreSQL 17.9, svi paketi, git čist, sva 3 modela potvrđena na Ollama Cloud (41 modela dostupno).

README napomena: sekcija stanja prevoda zastarjela (pisana u sesiji 44/45) — treba update u nekoj od sljedećih sesija.

### 2. Lokalni NLLB prevodi (info)

Flavio je lokalno preveo sve 3852 rečenice Hounda za hr, sr, it, de koristeći NLLB model — prevodi su već u bazi (`bb_prevodi_recenica`). Nisu prošli sudiju ni pobjednika jer cloud modeli (gemma3, ministral) još nisu prevedeni za cijeli opseg.

**Potvrđeno:** `bb_03_prevod.py` automatski preskače već prevedene rečenice na dva nivoa:
- `already_done()` funkcija (provjera prije prevoda)
- `ON CONFLICT DO NOTHING` na INSERT nivou

Ovo važi i za NLLB i za sve ostale modele — nema rizika od duplikata ili gubljenja podataka.

### 3. Prevod — gemma3 i ministral

Opsezi:
- **hr**: s351–s400 (sljedeći nakon s350)
- **sr, it, de**: s101–s150 (sljedeći nakon s100)

Redosljed izvršavanja (serijski zbog Ollama Cloud single session ograničenja):

| Run | Model | Jezici | Trajanje |
|-----|-------|--------|---------|
| 1 | gemma3:12b (0.8+0.1) | hr | 2:24 min |
| 2 | gemma3:12b (0.8+0.1) | sr, it, de | 9:48 min |
| 3 | ministral-3:14b (0.8+0.1) | hr | 2:22 min |
| 4 | ministral-3:14b (0.8+0.1) | sr, it, de | 6:38 min |

**Napomena:** NLLB run preskočen — svi prevodi za ova 4 jezika već u bazi za cijeli opseg knjige.

### 4. Sudija

| Run | Jezici | Trajanje |
|-----|--------|---------|
| gemma4:31b | hr | 2:45 min |
| gemma4:31b | sr, it, de | 7:10 min |

### 5. Pobjednici

Upisano 50 pobjednika po jeziku, ukupno 200:

**HR s351–s400** — ministral dominira (većina rečenica), gemma3 i nllb povremeno pobjeđuju.

**SR s101–s150** — gemma3 dominira, ćirilica ispravno upisana.

**IT s101–s150** — ravnomjerna raspodjela gemma3/ministral.

**DE s101–s150** — gemma3 blago dominira.

### 6. Web export

Novo stanje na portalu:

| Jezik | Prije | Sada |
|-------|-------|------|
| hr | 350 | **400** |
| sr | 100 | **150** |
| it | 100 | **150** |
| de | 100 | **150** |

---

## Ollama Cloud troškovi

| Period | Početak sesije | Kraj sesije | Potrošnja |
|--------|---------------|-------------|-----------|
| 5h | 0% | 8.6% | +8.6% |
| Weekly | 38.5% | 41.7% | +3.2% |

Ukupno ~2600 cloud poziva (400 gemma3 prevoda + 400 ministral prevoda + 800 back-translacija + 1000 sudija ocjena).

---

## Stanje baze na kraju sesije

| Knjiga | ID | Jezik | Rečenice | Status |
|--------|-----|-------|----------|--------|
| Hound | 1 | bs, hr | 350 / 400 | ✅ |
| Hound | 1 | af, de, es, fr, it, nl, sl, sr, pt/ro | 100 / 150 (de, it, sr) | ✅ |
| Hound | 1 | mk, bg | 50 | ✅ |
| Big Four | 5 | pt, it | 100 | ✅ |
| Frankenstein | 8 | ro, it | 100 | ✅ |

**Napomena:** hr ima 400 pobjednika (bs ostaje na 350), de/it/sr na 150.

---

## Otvoreno za sljedeće sesije

1. Proširenje Hound — nastavak svih 14 jezika prema s350
2. Proširenje Hound mk/bg — s51–s100
3. Proširenje Big Four PT i IT — s101–s350
4. Proširenje Frankenstein RO i IT — s101–s350
5. README update — stanje prevoda zastarjelo (sesija 44/45)
6. Favicon za buchenberg.opik.net
7. Relation Extraction (Gemma4) — semantičke veze između entiteta
8. Refaktorisati `bb_web_export.py` da koristi `v_pobjednici` view

---

*Flavio & Claude · Buchenberg · Sesija 51 · 5. jun 2026.*
