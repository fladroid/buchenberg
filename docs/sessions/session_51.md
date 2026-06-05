# Session 51 — Prevodi HR/SR/IT/DE, NLP tabele, sortiranje

**Datum:** 5. jun 2026.
**Sesija:** 51
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Health check

Sve zeleno — PostgreSQL 17.9, svi paketi, git čist, sva 3 modela potvrđena (41 modela na Ollama Cloud).

### 2. Lokalni NLLB prevodi (info)

Flavio je lokalno preveo sve 3852 rečenice Hounda za hr, sr, it, de koristeći NLLB — prevodi su u bazi. Potvrđeno da `bb_03_prevod.py` automatski preskače već prevedene rečenice na dva nivoa (`already_done()` + `ON CONFLICT DO NOTHING`). NLLB run nije potrebno ponavljati.

### 3. bb_sr_cirilica.py — workflow razjašnjen

Skripta mora ići **nakon `bb_03_prevod.py` za sr, a prije `bb_08_sudija.py` i `bb_04_pobjednik.py`**. Nije automatska — pokreće se ručno. U ovoj sesiji je propuštena u prvom runu (s101–s150), naknadno ispravljena: transliterirano 3952 redova, pobjednici za sr s101–s150 ponovo upisani.

### 4. Prevod — dva runa po 50 rečenica

**Run 1:**
- hr: s351–s400
- sr, it, de: s101–s150

**Run 2:**
- hr: s401–s450
- sr, it, de: s151–s200

Redosljed (serijski, Ollama Cloud single session):

| Model | Jezici | Trajanje |
|-------|--------|---------|
| gemma3:12b (0.8+0.1) | hr | ~2:30 min |
| gemma3:12b (0.8+0.1) | sr, it, de | ~10–13 min |
| ministral-3:14b (0.8+0.1) | hr | ~2:30 min |
| ministral-3:14b (0.8+0.1) | sr, it, de | ~7–8 min |

Napomena: ministral hr (Run 1) pao zbog ReadTimeout — automatski restart, preskočio već prevedene rečenice.

### 5. bb_sr_cirilica.py

Pokrenuta nakon svakog ministral runa za sr. Run 1: 3952 redova. Run 2: 200 redova.

### 6. Sudija i pobjednici

Sudija + pobjednici pokrenuti za svaki run, obje grupe. Ukupno upisano 200 novih pobjednika.

### 7. Novo stanje prevoda

| Jezik | Prije | Sada |
|-------|-------|------|
| hr | 350 | **450** |
| sr | 100 | **200** |
| it | 100 | **200** |
| de | 100 | **200** |

### 8. bb_web_export.py — od_tip/do_tip u vezama

Funkcija `get_ner_veze()` proširena: veze sada sadrže `od_tip` i `do_tip` polja (tip entiteta za oba kraja veze). JSON regenerisan.

### 9. nlp.html — dvije nove tabele

**Entity Links** — tabelarni prikaz svih co-occurrence veza s tipovima entiteta (PERSON/GPE/ORG badge), težinom i search filterom.

**Type Conflicts** — entiteti koji se pojavljuju pod više od jednog tipa (npr. Watson kao PERSON i GPE). Otkriven veći broj konflikata nego očekivano.

Sortiranje na obje tabele: klik na zaglavlje kolone, toggle asc/desc.

### 10. nlp.html — sortiranje Named Entities

Sort header dodan iznad NER liste: "Name" (abecedno) i "Count" (po pojavljujivanjima), toggle asc/desc.

### 11. stats.html — sortiranje svih 3 tabela

Sve tri tabele (Winner distribution, Coverage, Average scores) dobilo klikabilno sortiranje po svim kolonama. Defaulti: Winner → Wins ▼, Coverage → Sentences ▼, Scores → Language ▲.

---

## Ollama Cloud troškovi (sesija)

| Period | Početak | Kraj | Potrošnja |
|--------|---------|------|-----------|
| 5h | 8.6% (reset) → 0% | ~17% ukupno | ~17% |
| Weekly | 38.5% → 41.7% (+3.2%) → kraj ~45% | | ~6.5% |

---

## Stanje baze na kraju sesije

| Knjiga | ID | Jezik | Pobjednici |
|--------|-----|-------|-----------|
| Hound | 1 | hr | 450 |
| Hound | 1 | bs | 350 |
| Hound | 1 | sr, it, de | 200 |
| Hound | 1 | af, es, fr, nl, sl, pt, ro | 100 |
| Hound | 1 | mk, bg | 50 |
| Big Four | 5 | pt, it | 100 |
| Frankenstein | 8 | ro, it | 100 |

---

## Otvoreno za sljedeće sesije

1. Nastavak prevoda hr, sr, it, de → s350
2. Proširenje ostalih 10 jezika Hounda → s101–s350
3. Proširenje Hound mk/bg → s51–s100
4. Proširenje Big Four PT/IT → s101–s350
5. Proširenje Frankenstein RO/IT → s101–s350
6. Web fajlovi (nlp.html, stats.html) dodati u git repozitorijum
7. Favicon za buchenberg.opik.net
8. Relation Extraction (Gemma4)
9. Refaktorisati `bb_web_export.py` → `v_pobjednici` view

---

*Flavio & Claude · Buchenberg · Sesija 51 · 5. jun 2026.*
