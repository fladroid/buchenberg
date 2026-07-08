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

## Run: 7–8. jul 2026 — Eksperiment: 4 paralelne grupe (isto vrijeme, Ollama Pro tier)

*Sve četiri grupe pokrenute jedna za drugom (~17:20–17:22 UTC / ~19:20–19:22 CEST, Vienna ljetno vrijeme) 7. jula, izvršavale su se konkurentno na Ollama Cloud (Pro tier nalog, vidi README §Paralelno izvršavanje). Sva vremena u tabelama ispod su UTC (server vrijeme); CEST (Vienna, jul) = UTC+2.*

### Grupa 1 — k23 (Big Four Copy), de/hr/it/sr, opseg 1001–1500

**Tabela 1 — Identifikacija & vrijeme**

| Opseg | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|
| 1001–1020 | 17:20 | 17:41 | 0:21:12 | 0.94 |
| 1021–1060 | 17:41 | 18:20 | 0:38:15 | 1.05 |
| 1061–1120 | 18:20 | 19:18 | 0:58:45 | 1.02 |
| 1121–1200 | 19:18 | 20:39 | 1:21:03 | 0.99 |
| 1201–1300 | 20:39 | 22:27 | 1:47:59 | 0.93 |
| 1301–1500 | 22:27 | 01:37(+1d) | 3:09:55 | 1.05 |

**Tabela 2 — Kvalitet & pobjede**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 1001–1020 | 0.9748 | 0.9557 | 0.9875 | 54 (67.5%) | 23 (28.75%) | 3 (3.75%) |
| 1021–1060 | 0.9754 | 0.9569 | 0.9878 | 104 (65.0%) | 40 (25.0%) | 16 (10.0%) |
| 1061–1120 | 0.9720 | 0.9544 | 0.9838 | 148 (61.7%) | 78 (32.5%) | 14 (5.8%) |
| 1121–1200 | 0.9709 | 0.9540 | 0.9822 | 215 (67.2%) | 79 (24.7%) | 26 (8.1%) |
| 1201–1300 | 0.9661 | 0.9490 | 0.9824 | 239 (59.75%) | 122 (30.5%) | 39 (9.75%) |
| 1301–1500 | 0.9680 | 0.9498 | 0.9802 | 510 (63.75%) | 209 (26.1%) | 81 (10.1%) |
| **UKUPNO** | **0.9694** | **0.9517** | **0.9823** | **1270 (63.5%)** | **551 (27.6%)** | **179 (9.0%)** |

### Grupa 2 — k22 (Hound Copy), bg/bs/mk/sl, opseg 1–500

**Tabela 1**

| Opseg | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|
| 1–20 | 17:21 | 17:51 | 0:29:14 | 0.68 |
| 21–60 | 17:51 | 18:48 | 0:57:24 | 0.70 |
| 61–120 | 18:48 | 20:04 | 1:16:09 | 0.79 |
| 121–200 | 20:04 | 21:33 | 1:28:30 | 0.90 |
| 201–300 | 21:33 | 00:07(+1d) | 2:34:39 | 0.65 |
| 301–500 | 00:07 | 03:39 | 3:32:00 | 0.94 |

**Tabela 2**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 1–20 | 0.9680 | 0.9486 | 0.9809 | 60 (75.0%) | 19 (23.75%) | 1 (1.25%) |
| 21–60 | 0.9626 | 0.9412 | 0.9769 | 97 (60.6%) | 59 (36.9%) | 4 (2.5%) |
| 61–120 | 0.9621 | 0.9456 | 0.9731 | 145 (60.4%) | 80 (33.3%) | 15 (6.3%) |
| 121–200 | 0.9642 | 0.9473 | 0.9756 | 198 (61.9%) | 109 (34.1%) | 13 (4.1%) |
| 201–300 | 0.9574 | 0.9408 | 0.9686 | 230 (57.5%) | 163 (40.75%) | 7 (1.75%) |
| 301–500 | 0.9623 | 0.9449 | 0.9752 | 523 (65.4%) | 230 (28.75%) | 47 (5.9%) |
| **UKUPNO** | **0.9619** | **0.9444** | **0.9741** | **1253 (62.7%)** | **660 (33.0%)** | **87 (4.4%)** |

### Grupa 3 — k23 (Big Four Copy), bg/bs/mk/sl, opseg 1–500

**Tabela 1**

| Opseg | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|
| 1–20 | 17:21 | 17:52 | 0:30:51 | 0.65 |
| 21–60 | 17:52 | 18:41 | 0:48:48 | 0.82 |
| 61–120 | 18:41 | 19:39 | 0:58:18 | 1.03 |
| 121–200 | 19:39 | 20:55 | 1:15:59 | 1.05 |
| 201–300 | 20:55 | 22:38 | 1:42:52 | 0.97 |
| 301–500 | 22:38 | 01:50(+1d) | 3:12:20 | 1.04 |

**Tabela 2**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 1–20 | 0.9652 | 0.9537 | 0.9729 | 48 (60.0%) | 30 (37.5%) | 2 (2.5%) |
| 21–60 | 0.9605 | 0.9381 | 0.9754 | 93 (58.1%) | 54 (33.75%) | 13 (8.1%) |
| 61–120 | 0.9667 | 0.9441 | 0.9818 | 160 (66.7%) | 73 (30.4%) | 7 (2.9%) |
| 121–200 | 0.9663 | 0.9416 | 0.9829 | 214 (66.9%) | 83 (25.9%) | 23 (7.2%) |
| 201–300 | 0.9644 | 0.9417 | 0.9846 | 250 (62.5%) | 115 (28.75%) | 35 (8.75%) |
| 301–500 | 0.9637 | 0.9419 | 0.9795 | 523 (65.4%) | 236 (29.5%) | 41 (5.1%) |
| **UKUPNO** | **0.9644** | **0.9422** | **0.9807** | **1288 (64.4%)** | **591 (29.6%)** | **121 (6.1%)** |

### Grupa 4 — k24 (Frankenstein Copy), bg/bs/mk/sl, opseg 1–500

**Tabela 1**

| Opseg | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|
| 1–20 | 17:21 | 17:53 | 0:31:48 | 0.63 |
| 21–60 | 17:53 | 18:56 | 1:03:29 | 0.63 |
| 61–120 | 18:56 | 20:41 | 1:44:53 | 0.57 |
| 121–200 | 20:41 | 22:27 | 1:46:00 | 0.75 |
| 201–300 | 22:27 | 01:10(+1d) | 2:42:37 | 0.61 |
| 301–500 | 01:10 | 05:47 | 4:37:46 | 0.72 |

**Tabela 2**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 1–20 | 0.9625 | 0.9574 | 0.9659 | 52 (65.0%) | 26 (32.5%) | 2 (2.5%) |
| 21–60 | 0.9659 | 0.9534 | 0.9743 | 95 (59.4%) | 63 (39.4%) | 2 (1.25%) |
| 61–120 | 0.9599 | 0.9459 | 0.9693 | 128 (53.3%) | 106 (44.2%) | 6 (2.5%) |
| 121–200 | 0.9611 | 0.9454 | 0.9816 | 177 (55.3%) | 135 (42.2%) | 8 (2.5%) |
| 201–300 | 0.9578 | 0.9441 | 0.9671 | 206 (51.5%) | 183 (45.75%) | 11 (2.75%) |
| 301–500 | 0.9591 | 0.9455 | 0.9684 | 452 (56.5%) | 336 (42.0%) | 12 (1.5%) |
| **UKUPNO** | **0.9599** | **0.9464** | **0.9707** | **1110 (55.5%)** | **849 (42.45%)** | **41 (2.05%)** |

### Zapažanja (cross-grupa)
- **Agregatna brzina:** sve 4 grupe zajedno ≈ 3.47 rečenica/min (zbir 1.006+0.809+0.982+0.670), naspram ≈ 0.924 rečenica/min za solo k23-dehritsr tok (mjeren u prethodnom, ne-paralelnom segmentu 501–1000) — faktor ≈3.77×, blizu linearnog skaliranja sa 4 konkurentna toka. Potvrđuje da Ollama Cloud Pro tier (README, ispravljeno s118) nema hard ograničenje na broj paralelnih sesija; per-model vremena po rečenici u paralelnim tokovima (9–14s) ostaju u istom rasponu kao u solo segmentu (10–21s), bez sistematskog usporavanja zbog konkurencije.
- **k24 (Frankenstein Copy) izdvaja se kvalitetom pobjeda:** mistral-large-3 pobjeđuje skoro podjednako koliko glm-5.2 (42.45% vs 55.5%), dok je u preostale tri grupe odnos dosljedno ~2:1 u korist glm-5.2. Avg_final za k24 je i najniži od četiri (0.9599). Vjerovatno sadržaj (Šelijeva gotska proza iz 1818) a ne efekat paralelizma — per-model brzine su normalne.
- **Sve četiri grupe imaju avg_final u uskom rasponu 0.960–0.969** — stabilan kvalitet novog para (mistral-large-3 + glm-5.2) bez obzira na broj istovremenih tokova.
- **Radni ritam i backup prozori (Flaviovo zapažanje; CEST=UTC+2 u julu):** Flavio subjektivno primjećuje degradaciju performansi prema Ollama Cloud otprilike 16–18h CEST — vjerovatno regionalno opterećenje (Ollama ima servere u US i EU, Flaviova infrastruktura i radni ritam su evropski, pa se poklapa s regionalnim peak periodom). Backup raspored: foxuno 01:00–03:00 CEST (=23:00–01:00 UTC), balsam 03:00–08:00 CEST (=01:00–06:00 UTC). Ova konkretna sesija (start ~19:20 CEST) ne pokriva 16–18h CEST prozor direktno — počela je poslije njega, pa se hipoteza ne može ni potvrditi ni opovrgnuti iz ovih brojeva. Djelimično preklapanje s backup prozorom postoji: posljednji batch k24 (301–500) leži u cjelosti unutar balsam backup prozora (01:10–05:47 UTC), ali k24 je bio dosljedno najsporiji od sve četiri grupe već u ranijim batch-evima prije backup prozora — pa backup nije glavni uzrok njegove sporosti, najviše dodatni faktor. Normalna varijabilnost dijeljenog cloud okruženja, ne greška u sistemu.
