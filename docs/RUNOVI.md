# Buchenberg — RUNOVI (statistika po pipeline/refine runovima)

Ovaj dokument raste — svaki novi run (pipeline ili refine) dodaje novu sekciju ispod, generisanu iz `src/parse_run_logs.py` nad log fajlovima iz `logs/`.

**Format po runu:** dvije tabele — (1) identifikacija & vrijeme, (2) kvalitet & pobjede — plus kratak odjeljak zapažanja.

**Skript:** `venv/bin/python src/parse_run_logs.py logs/<fajl1>.log logs/<fajl2>.log ...` → JSON sa svim poljima (knjiga, jezici, broj_jezika, raspon, faza, start, end, elapsed, recenica_po_minutu, prevod_steps, sudija_real, pobjednik_real, po-jeziku: upisano/avg_final/avg_komp/avg_sudija/model_counts).

---

## Run: 6. jul 2026 — Knjiga 23 (Big Four Copy), jezici de/hr/it/sr, opseg 1–500, faza 1 (baza)

### Tabela 1 — Identifikacija & vrijeme

| Opseg | Jezici | Faza | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|---|---|
| 1–20 | 4 | 1 (baza) | 15:05 | 15:36 | 0:31:07 | 0.64 |
| 21–60 | 4 | 1 (baza) | 15:42 | 16:28 | 0:45:43 | 0.87 |
| 61–120 | 4 | 1 (baza) | 16:28 | 17:20 | 0:51:52 | 1.16 |
| 121–200 | 4 | 1 (baza) | 17:20 | 18:38 | 1:18:01 | 1.03 |
| 201–300 | 4 | 1 (baza) | 18:38 | 19:53 | 1:14:57 | 1.33 |
| 301–500 | 4 | 1 (baza) | 19:53 | 23:10 | 3:17:20 | 1.01 |

*(svi datumi 6. jul 2026; nema preklapanja start/kraj između serija — sekvencijalna sesija, baseline referenca za buduće paralelne runove)*

### Tabela 2 — Kvalitet & pobjede

| Opseg | Prosj. final | Prosj. komp | Prosj. sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 1–20 | 0.9549 | 0.9585 | 0.9645 | 52 | 26 | 2 |
| 21–60 | 0.9614 | 0.9485 | 0.9760 | 102 | 46 | 12 |
| 61–120 | 0.9723 | 0.9519 | 0.9859 | 155 | 71 | 14 |
| 121–200 | 0.9723 | 0.9507 | 0.9868 | 203 | 97 | 20 |
| 201–300 | 0.9707 | 0.9504 | 0.9842 | 248 | 120 | 32 |
| 301–500 | 0.9690 | 0.9489 | 0.9849 | 500 | 254 | 46 |
| **UKUPNO** | **0.9691** | **0.9502** | **0.9837** | **1260 (63.0%)** | **614 (30.7%)** | **126 (6.3%)** |

### Zapažanja
- Prvi batch (1–20) ima primjetno niži prosj. final (0.9549) naspram ostalih (~0.97) — poklapa se s poznatim obrascem: prve rečenice knjige su metapodaci (naslov/izdavač/copyright), kratke i bez konteksta (npr. `sr` s3 ovog batcha: `sudija=N/A → final=0.3753`, povlači prosjek dole).
- Rečenica/min varira 0.64–1.33 kroz seriju — vjerovatno Ollama Cloud opterećenje u datom trenutku (viđen bar 1 `Read timed out` retry u batch 1), ne veličina opsega.
- Zbir trajanja (≈7h59m) nešto je kraći od stvarnog razmaka start prve → kraj zadnje serije (≈8h05m) — razlika su pauze između ručnog pokretanja serija, ne greška u mjerenju.
