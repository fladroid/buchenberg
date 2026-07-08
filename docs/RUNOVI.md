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

## Run: 7–8. jul 2026 — Knjiga 23 (Big Four Copy), jezici de/hr/it/sr, opseg 501–1000, faza 1 (baza) — nastavak sekvencijalnog toka

*Dio jednog od "4 grupe" eksperimenta koji je Flavio pustio uporedo: ovaj sekvencijalni tok (k23, dehritsr) nastavlja direktno na baznu tabelu 1–500 iz s117. Uporedo su trčale i tri paralelne grupe (k22/k23/k24, jezici bg/bs/mk/sl) — dokumentuju se posebno kad završe.*

### Tabela 1 — Identifikacija & vrijeme

| Opseg | Jezici | Faza | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|---|---|
| 501–520 | 4 | 1 (baza) | 08:06 | 08:29 | 0:23:47 | 0.84 |
| 521–560 | 4 | 1 (baza) | 08:29 | 09:14 | 0:45:03 | 0.89 |
| 561–620 | 4 | 1 (baza) | 09:14 | 10:14 | 0:59:11 | 1.01 |
| 621–700 | 4 | 1 (baza) | 10:14 | 11:26 | 1:12:11 | 1.11 |
| 701–800 | 4 | 1 (baza) | 11:26 | 13:26 | 2:00:21 | 0.83 |
| 801–1000 | 4 | 1 (baza) | 13:26 | 17:07 | 3:40:26 | 0.91 |

*(svi 7. jul 2026; bez preklapanja — čisto sekvencijalni tok, direktan nastavak s117 bazne tabele 1–500)*

### Tabela 2 — Kvalitet & pobjede

| Opseg | Prosj. final | Prosj. komp | Prosj. sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 501–520 | 0.9617 | 0.9512 | 0.9688 | 50 (62.5%) | 21 (26.3%) | 9 (11.3%) |
| 521–560 | 0.9739 | 0.9535 | 0.9876 | 117 (73.1%) | 37 (23.1%) | 6 (3.8%) |
| 561–620 | 0.9637 | 0.9474 | 0.9746 | 169 (70.4%) | 57 (23.8%) | 14 (5.8%) |
| 621–700 | 0.9664 | 0.9473 | 0.9792 | 214 (66.9%) | 92 (28.8%) | 14 (4.4%) |
| 701–800 | 0.9673 | 0.9499 | 0.9814 | 278 (69.5%) | 96 (24.0%) | 26 (6.5%) |
| 801–1000 | 0.9672 | 0.9480 | 0.9800 | 511 (63.9%) | 244 (30.5%) | 45 (5.6%) |
| **UKUPNO (501–1000)** | **0.9670** | **0.9488** | **0.9797** | **1339 (67.0%)** | **547 (27.4%)** | **114 (5.7%)** |

### Zapažanja
- Prvi batch ovog segmenta (501–520) ima primjetno niži final (0.9617) i najveći udio nllb pobjeda (11.3%) naspram ostatka (~4–6%) — za razliku od s117 gdje je nizak prvi batch bio zbog metapodataka na početku knjige, ovdje to objašnjenje ne važi (501 nije početak knjige); vjerovatno šum na malom uzorku (n=20).
- Rečenica/min i dalje varira (0.83–1.11) bez jasnog trenda po veličini batcha — potvrđuje s117 zaključak da je varijacija Ollama Cloud opterećenje, ne veličina batcha.
- Naspram s117 bazne tabele (1–500: glm 63.0% / mistral 30.7% / nllb 6.3%), ovaj segment (501–1000) pokazuje glm nešto jače (67.0%), mistral nešto slabije (27.4%), nllb slično (5.7%) — pravac isti, razlika unutar očekivanog šuma.
- **Analiza veličine batcha naspram brzine** (Flaviovo pitanje, kombinuje s117+ovaj run): rečenica/min po veličini — 20→0.74 prosjek, 40→0.88, 60→1.09, 80→1.07, 100→1.08, 200→0.96. Samo 20 je dosljedno sporije (fiksni trošak po pozivu bb_03 amortizovan preko manje rečenica); od 40 naviše nema monotonog trenda — 100 NIJE sweet spot, varijacija (0.83–1.33) dominantno dolazi od Ollama Cloud opterećenja u datom trenutku, ne od izbora veličine.
