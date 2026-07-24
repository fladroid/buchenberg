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

## Run: 8. jul 2026 — Eksperiment: 4 paralelne grupe (nastavak k23 core-4 + prvi bazni prevod es/fr/pt/ro na k22/k23/k24)

*Sve četiri grupe pokrenute skoro istovremeno (~07:42–07:43 UTC / ~09:42–09:43 CEST, Vienna ljetno vrijeme) 8. jula, izvršavale su se konkurentno na Ollama Cloud (Pro tier). Grupa 1 je direktan nastavak s119 Grupe 1 (k23 dehritsr, tada 1001–1500, sada 1501–2000). Grupe 2–4 su prvi prevod (svih 5 modela — Copy knjige uvijek idu direktno kroz pun set, nema NLLB-only međukorak kao kod originalnih knjiga) za opseg 1–500 na jezicima es/fr/pt/ro na sve tri Copy knjige — te rečenice ranije nisu imale nikakav prevod. Sva vremena u tabelama ispod su UTC; CEST (Vienna, jul) = UTC+2. Za razliku od prethodnog 4-grupnog eksperimenta (s119), ovaj run je završen u cjelosti unutar istog dana — nema prelaska preko ponoći.*

### Grupa 1 — k23 (Big Four Copy), de/hr/it/sr, opseg 1501–2000 (nastavak s119 Grupe 1)

**Tabela 1 — Identifikacija & vrijeme**

| Opseg | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|
| 1501–1520 | 07:43 | 08:02 | 0:19:15 | 1.04 |
| 1521–1560 | 08:02 | 08:53 | 0:50:29 | 0.79 |
| 1561–1620 | 08:53 | 09:54 | 1:01:17 | 0.98 |
| 1621–1700 | 09:54 | 11:27 | 1:33:00 | 0.86 |
| 1701–1800 | 11:27 | 13:27 | 1:59:36 | 0.84 |
| 1801–2000 | 13:27 | 17:37 | 4:10:11 | 0.80 |

**Tabela 2 — Kvalitet & pobjede**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 1501–1520 | 0.9647 | 0.9437 | 0.9788 | 46 (57.5%) | 25 (31.2%) | 9 (11.2%) |
| 1521–1560 | 0.9686 | 0.9501 | 0.9873 | 107 (66.9%) | 40 (25.0%) | 13 (8.1%) |
| 1561–1620 | 0.9716 | 0.9572 | 0.9854 | 162 (67.5%) | 56 (23.3%) | 22 (9.2%) |
| 1621–1700 | 0.9684 | 0.9483 | 0.9849 | 190 (59.4%) | 106 (33.1%) | 24 (7.5%) |
| 1701–1800 | 0.9630 | 0.9502 | 0.9765 | 261 (65.2%) | 114 (28.5%) | 25 (6.2%) |
| 1801–2000 | 0.9624 | 0.9465 | 0.9731 | 491 (61.4%) | 263 (32.9%) | 46 (5.8%) |
| **UKUPNO** | **0.9652** | **0.9490** | **0.9785** | **1257 (62.9%)** | **604 (30.2%)** | **139 (7.0%)** |

### Grupa 2 — k22 (Hound Copy), es/fr/pt/ro, opseg 1–500

**Tabela 1**

| Opseg | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|
| 1–20 | 07:42 | 08:08 | 0:26:10 | 0.76 |
| 21–60 | 08:08 | 09:04 | 0:55:14 | 0.72 |
| 61–120 | 09:04 | 10:23 | 1:19:21 | 0.76 |
| 121–200 | 10:23 | 11:53 | 1:30:30 | 0.88 |
| 201–300 | 11:53 | 14:41 | 2:47:50 | 0.60 |
| 301–500 | 14:41 | 18:13 | 3:31:28 | 0.95 |

**Tabela 2**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 1–20 | 0.9623 | 0.9551 | 0.9791 | 51 (63.8%) | 27 (33.8%) | 2 (2.5%) |
| 21–60 | 0.9650 | 0.9444 | 0.9788 | 91 (56.9%) | 61 (38.1%) | 8 (5.0%) |
| 61–120 | 0.9659 | 0.9497 | 0.9767 | 144 (60.0%) | 70 (29.2%) | 26 (10.8%) |
| 121–200 | 0.9677 | 0.9476 | 0.9812 | 184 (57.5%) | 116 (36.2%) | 20 (6.2%) |
| 201–300 | 0.9637 | 0.9445 | 0.9766 | 218 (54.5%) | 173 (43.2%) | 9 (2.2%) |
| 301–500 | 0.9665 | 0.9489 | 0.9807 | 474 (59.2%) | 247 (30.9%) | 79 (9.9%) |
| **UKUPNO** | **0.9658** | **0.9478** | **0.9793** | **1162 (58.1%)** | **694 (34.7%)** | **144 (7.2%)** |

### Grupa 3 — k23 (Big Four Copy), es/fr/pt/ro, opseg 1–500

**Tabela 1**

| Opseg | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|
| 1–20 | 07:42 | 08:12 | 0:29:16 | 0.68 |
| 21–60 | 08:12 | 09:03 | 0:51:38 | 0.77 |
| 61–120 | 09:03 | 10:06 | 1:03:06 | 0.95 |
| 121–200 | 10:06 | 11:28 | 1:21:55 | 0.98 |
| 201–300 | 11:28 | 13:06 | 1:37:32 | 1.03 |
| 301–500 | 13:06 | 16:34 | 3:28:27 | 0.96 |

**Tabela 2**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 1–20 | 0.9557 | 0.9579 | 0.9787 | 50 (62.5%) | 27 (33.8%) | 3 (3.8%) |
| 21–60 | 0.9667 | 0.9437 | 0.9821 | 75 (46.9%) | 74 (46.2%) | 11 (6.9%) |
| 61–120 | 0.9696 | 0.9514 | 0.9858 | 151 (62.9%) | 73 (30.4%) | 16 (6.7%) |
| 121–200 | 0.9698 | 0.9470 | 0.9881 | 187 (58.4%) | 91 (28.4%) | 42 (13.1%) |
| 201–300 | 0.9689 | 0.9475 | 0.9857 | 238 (59.5%) | 120 (30.0%) | 42 (10.5%) |
| 301–500 | 0.9652 | 0.9458 | 0.9818 | 476 (59.5%) | 260 (32.5%) | 64 (8.0%) |
| **UKUPNO** | **0.9669** | **0.9473** | **0.9840** | **1177 (58.9%)** | **645 (32.2%)** | **178 (8.9%)** |

### Grupa 4 — k24 (Frankenstein Copy), es/fr/pt/ro, opseg 1–500

**Tabela 1**

| Opseg | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|
| 1–20 | 07:43 | 08:15 | 0:32:27 | 0.62 |
| 21–60 | 08:15 | 09:23 | 1:07:47 | 0.59 |
| 61–120 | 09:23 | 11:10 | 1:46:44 | 0.56 |
| 121–200 | 11:10 | 13:05 | 1:55:19 | 0.69 |
| 201–300 | 13:05 | 15:55 | 2:50:38 | 0.59 |
| 301–500 | 15:55 | 19:47 | 3:51:40 | 0.86 |

**Tabela 2**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 1–20 | 0.9647 | 0.9628 | 0.9780 | 44 (55.0%) | 34 (42.5%) | 2 (2.5%) |
| 21–60 | 0.9709 | 0.9556 | 0.9811 | 82 (51.2%) | 70 (43.8%) | 8 (5.0%) |
| 61–120 | 0.9645 | 0.9495 | 0.9747 | 110 (45.8%) | 122 (50.8%) | 8 (3.3%) |
| 121–200 | 0.9677 | 0.9491 | 0.9802 | 150 (46.9%) | 161 (50.3%) | 9 (2.8%) |
| 201–300 | 0.9662 | 0.9486 | 0.9781 | 174 (43.5%) | 210 (52.5%) | 16 (4.0%) |
| 301–500 | 0.9669 | 0.9503 | 0.9781 | 410 (51.2%) | 358 (44.8%) | 32 (4.0%) |
| **UKUPNO** | **0.9668** | **0.9506** | **0.9783** | **970 (48.5%)** | **955 (47.8%)** | **75 (3.8%)** |

### Zapažanja (cross-grupa)
- **k24 (Frankenstein Copy) obrazac potvrđen treći put zaredom:** glm-5.2/mistral-large-3 skoro izjednačeni (48.5% vs 47.8%), naspram dosljednog ~2:1 odnosa u preostale tri grupe (58–63% vs 30–35%). Odnos je ovdje IZRAŽENIJI nego u s119 istoj knjizi (tada 55.5% vs 42.45%). k24 je i ovog puta najsporija grupa (aproks. 0.69 rec/min naspram 0.79–0.94 kod ostalih, računato kao 500/ukupno_elapsed_min po grupi). Dosljedno potkrepljuje hipotezu iz s119 da je uzrok sadržaj knjige (Šelijeva gotska proza, 1818), ne artefakt paralelizma ili slučajnost.
- **Agregatna brzina ≈ 3.27 rec/min** (zbir aproksimativnih prosjeka: k22 0.79 + k23-dehritsr 0.84 + k23-esfrptro 0.94 + k24 0.69), u istom rasponu kao s119 eksperiment (~3.47) — potvrđuje da Ollama Cloud Pro tier i dalje nema primjetno usko grlo pri 4 konkurentna toka.
- **Prvi prevod za es/fr/pt/ro na opsegu 1–500** na k22/k23/k24 (standardni Copy-knjiga pristup, direktno kroz svih 5 modela) — kvalitet (avg final 0.9658–0.9669) u istom rasponu kao core-4 nastavak (0.9652).
- **Bez prelaska preko ponoći** — sve četiri grupe završile unutar istog dana (8. jul), za razliku od s119 eksperimenta gdje su tri od četiri grupe prešle u sljedeći dan.

## Run: 8–9. jul 2026 — Eksperiment: 4 paralelne grupe (noćni run; nastavak k23 core-4 2001–2500 + prvi bazni prevod af/nl na k22/k23/k24)

*Sve četiri grupe pokrenute skoro istovremeno (~21:18–21:19 UTC / ~23:18–23:19 CEST) 8. jula, izvršavale su se konkurentno preko ponoći u 9. jul. Grupa 1 je direktan nastavak prethodnog runa (k23 dehritsr, 1501–2000 → sada 2001–2500). Grupe 2–4 su prvi pravi bazni prevod za af/nl na sve tri Copy knjige.*

**Metodološka napomena:** afnl grupe imaju samo 2 jezika (af, nl) naspram 4 jezika u prethodnom (esfrptro/dehritsr) runu. "Rečenica/min" u Tabeli 1 je pozicijska brzina (broj_recenica/elapsed) i NIJE direktno uporediva preko grupa s različitim brojem jezika — manje jezika po poziciji znači manje ukupnog rada po poziciji, pa prividno viša brzina. Za pravo poređenje throughput-a korišten je **prevoda/min** (upisano/elapsed): k23_dehritsr ~3.47, k22_afnl ~2.99, k23_afnl ~3.40, k24_afnl ~2.45 — svi u istom rasponu kao prethodni dnevni run (2.76–3.76), dakle nema stvarne noć/dan razlike u brzini.

### Grupa 1 — k23 (Big Four Copy), de/hr/it/sr, opseg 2001–2500 (nastavak)

**Tabela 1 — Identifikacija & vrijeme**

| Opseg | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|
| 2001–2020 | 21:19 | 21:48 | 0:29:25 | 0.68 |
| 2021–2060 | 21:48 | 22:49 | 1:01:14 | 0.65 |
| 2061–2120 | 22:49 | 00:29(+1d) | 1:39:38 | 0.60 |
| 2121–2200 | 00:29 | 02:08(+1d) | 1:38:34 | 0.81 |
| 2201–2300 | 02:08 | 03:47(+1d) | 1:39:30 | 1.01 |
| 2301–2500 | 03:47 | 06:55(+1d) | 3:07:29 | 1.07 |

**Tabela 2 — Kvalitet & pobjede**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 2001–2020 | 0.9596 | 0.9429 | 0.9709 | 63 (78.8%) | 15 (18.8%) | 2 (2.5%) |
| 2021–2060 | 0.9640 | 0.9418 | 0.9788 | 98 (61.2%) | 51 (31.9%) | 11 (6.9%) |
| 2061–2120 | 0.9709 | 0.9522 | 0.9835 | 134 (55.8%) | 100 (41.7%) | 6 (2.5%) |
| 2121–2200 | 0.9698 | 0.9532 | 0.9810 | 198 (61.9%) | 97 (30.3%) | 25 (7.8%) |
| 2201–2300 | 0.9657 | 0.9464 | 0.9786 | 252 (63.0%) | 119 (29.8%) | 29 (7.2%) |
| 2301–2500 | 0.9718 | 0.9524 | 0.9847 | 518 (64.8%) | 232 (29.0%) | 50 (6.2%) |
| **UKUPNO** | **0.9690** | **0.9501** | **0.9817** | **1263 (63.1%)** | **614 (30.7%)** | **123 (6.2%)** |

### Grupa 2 — k22 (Hound Copy), af/nl, opseg 1–500

**Tabela 1**

| Opseg | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|
| 1–20 | 21:18 | 21:32 | 0:14:05 | 1.42 |
| 21–60 | 21:32 | 22:03 | 0:31:02 | 1.29 |
| 61–120 | 22:03 | 22:46 | 0:43:16 | 1.39 |
| 121–200 | 22:46 | 23:36 | 0:49:50 | 1.61 |
| 201–300 | 23:36 | 01:03(+1d) | 1:26:43 | 1.15 |
| 301–500 | 01:03 | 02:53(+1d) | 1:50:02 | 1.82 |

**Tabela 2**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 1–20 | 0.9770 | 0.9624 | 0.9868 | 23 (57.5%) | 16 (40.0%) | 1 (2.5%) |
| 21–60 | 0.9640 | 0.9464 | 0.9759 | 45 (56.2%) | 31 (38.8%) | 4 (5.0%) |
| 61–120 | 0.9663 | 0.9582 | 0.9717 | 70 (58.3%) | 42 (35.0%) | 8 (6.7%) |
| 121–200 | 0.9674 | 0.9569 | 0.9745 | 91 (56.9%) | 60 (37.5%) | 9 (5.6%) |
| 201–300 | 0.9560 | 0.9495 | 0.9606 | 108 (54.0%) | 89 (44.5%) | 3 (1.5%) |
| 301–500 | 0.9666 | 0.9546 | 0.9794 | 253 (63.2%) | 115 (28.8%) | 32 (8.0%) |
| **UKUPNO** | **0.9648** | **0.9540** | **0.9739** | **590 (59.0%)** | **353 (35.3%)** | **57 (5.7%)** |

### Grupa 3 — k23 (Big Four Copy), af/nl, opseg 1–500

**Tabela 1**

| Opseg | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|
| 1–20 | 21:18 | 21:33 | 0:15:22 | 1.30 |
| 21–60 | 21:33 | 21:59 | 0:25:29 | 1.57 |
| 61–120 | 21:59 | 22:34 | 0:35:08 | 1.71 |
| 121–200 | 22:34 | 23:21 | 0:46:52 | 1.71 |
| 201–300 | 23:21 | 00:14(+1d) | 0:52:45 | 1.90 |
| 301–500 | 00:14 | 02:12(+1d) | 1:58:51 | 1.68 |

**Tabela 2**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 1–20 | 0.9720 | 0.9613 | 0.9792 | 26 (65.0%) | 10 (25.0%) | 4 (10.0%) |
| 21–60 | 0.9615 | 0.9507 | 0.9688 | 47 (58.8%) | 22 (27.5%) | 11 (13.8%) |
| 61–120 | 0.9696 | 0.9540 | 0.9800 | 70 (58.3%) | 39 (32.5%) | 11 (9.2%) |
| 121–200 | 0.9721 | 0.9530 | 0.9849 | 89 (55.6%) | 59 (36.9%) | 12 (7.5%) |
| 201–300 | 0.9712 | 0.9526 | 0.9837 | 129 (64.5%) | 55 (27.5%) | 16 (8.0%) |
| 301–500 | 0.9670 | 0.9538 | 0.9759 | 259 (64.8%) | 104 (26.0%) | 37 (9.2%) |
| **UKUPNO** | **0.9687** | **0.9535** | **0.9790** | **620 (62.0%)** | **289 (28.9%)** | **91 (9.1%)** |

### Grupa 4 — k24 (Frankenstein Copy), af/nl, opseg 1–500

**Tabela 1**

| Opseg | Start | Kraj | Trajanje | Rečenica/min |
|---|---|---|---|---|
| 1–20 | 21:18 | 21:35 | 0:16:25 | 1.22 |
| 21–60 | 21:35 | 22:11 | 0:36:49 | 1.09 |
| 61–120 | 22:11 | 23:15 | 1:03:10 | 0.95 |
| 121–200 | 23:15 | 00:15(+1d) | 1:00:21 | 1.33 |
| 201–300 | 00:15 | 01:44(+1d) | 1:28:52 | 1.13 |
| 301–500 | 01:44 | 04:07(+1d) | 2:23:06 | 1.40 |

**Tabela 2**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 1–20 | 0.9653 | 0.9633 | 0.9667 | 26 (65.0%) | 12 (30.0%) | 2 (5.0%) |
| 21–60 | 0.9640 | 0.9563 | 0.9692 | 41 (51.2%) | 39 (48.8%) | 0 (0.0%) |
| 61–120 | 0.9573 | 0.9479 | 0.9637 | 63 (52.5%) | 52 (43.3%) | 5 (4.2%) |
| 121–200 | 0.9643 | 0.9503 | 0.9736 | 75 (46.9%) | 81 (50.6%) | 4 (2.5%) |
| 201–300 | 0.9571 | 0.9488 | 0.9627 | 85 (42.5%) | 102 (51.0%) | 13 (6.5%) |
| 301–500 | 0.9606 | 0.9504 | 0.9675 | 189 (47.2%) | 195 (48.8%) | 16 (4.0%) |
| **UKUPNO** | **0.9606** | **0.9508** | **0.9672** | **479 (47.9%)** | **481 (48.1%)** | **40 (4.0%)** |

### Zapažanja (cross-grupa)
- **k24 obrazac — mistral prvi put ispred glm:** 48.1% vs 47.9%, četvrti uzastopni run gdje je k24 (Frankenstein Copy) skoro izjednačen, i prvi put da mistral-large-3 stvarno pretekne glm-5.2 (makar minimalno) u ukupnom zbiru grupe. Trend iz s119/prethodnog runa (sve izraženija ravnoteža na ovoj knjizi) se produbljuje.
- **k23_dehritsr ostaje vrlo stabilan** — glm dominacija 63.1% u ovom opsegu (2001–2500), skoro identično prethodnom (62.9% za 1501–2000) — dosljedan obrazac za tu kombinaciju knjiga+core4 kroz uzastopne opsege.
- **Throughput (prevoda/min) bez noć/dan razlike** — nakon korekcije za broj jezika po grupi, sve četiri grupe (2.45–3.47) padaju u isti raspon kao prethodni dnevni run (2.76–3.76); pozicijska "rečenica/min" metrika NIJE uporediva preko grupa s različitim brojem jezika (2 kod afnl naspram 4 kod esfrptro/dehritsr).
- Kvalitet (avg final 0.9606–0.9690) dosljedan i za af/nl kao i za core-4 i esfrptro iz prethodnog runa — nema pada kvaliteta na bilo kojoj od novoaktiviranih jezičkih grupa.

## Run: 22–23. jul 2026 — Knjiga 20 (Dracula), jezici de/hr/it/sr, opseg 4801–6600, faza 1 (baza) — PO-JEZIKU paralelizam

*Za razliku od ranijih "4 paralelne grupe" eksperimenata (s119/s120, gdje je svaka grupa bila 4 jezika sekvencijalno unutar sebe), ovaj run koristi PO-JEZIKU paralelizam: svaki jezik je zaseban proces koji napreduje nezavisno. Šest start-batch-eva kroz dva dana, uključujući period gdje je samo `de` radio solo (bez hr/it/sr) i sam sebe cijepao na 2–4 paralelna pod-procesa. Sva vremena UTC u zagradama; glavni prikaz CEST (Vienna, jul) = UTC+2. Analiza pokrenuta u s151 povodom Flaviovog utiska da su "noćne" sesije performantnije.*

### Batch 1 — sva 4 jezika paralelno, opseg 4801–5000 (22. jul, jutro/prijepodne)

**Tabela 1 — Identifikacija & vrijeme**

| Jezik | Start (CEST) | Kraj (CEST) | Trajanje | Rečenica/min |
|---|---|---|---|---|
| de | 09:57 | 11:49 | 1:52:02 | 1.79 |
| hr | 09:57 | 12:02 | 2:04:06 | 1.61 |
| it | 09:57 | 11:55 | 1:57:59 | 1.70 |
| sr | 09:57 | 12:01 | 2:03:42 | 1.62 |
| **ZBIR** | | | | **6.72** |

**Tabela 2 — Kvalitet & pobjede**

| Jezik | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| de | 0.9643 | 0.9415 | 0.9795 | 102 (51.0%) | 84 (42.0%) | 14 (7.0%) |
| hr | 0.9652 | 0.9455 | 0.9784 | 116 (58.0%) | 76 (38.0%) | 8 (4.0%) |
| it | 0.9681 | 0.9467 | 0.9824 | 86 (43.0%) | 98 (49.0%) | 16 (8.0%) |
| sr | 0.9643 | 0.9420 | 0.9792 | 126 (63.0%) | 65 (32.5%) | 9 (4.5%) |

### Batch 2 — DE solo (bez hr/it/sr), opseg 5001–5800, sam-sebe-paralelan (22. jul, podne)

*de je nastavio odmah nakon Batch-a 1 dok su hr/it/sr bili neaktivni do 15:46 CEST — 4h prozor gdje je samo de trošio Ollama Cloud kapacitet. Unutar ovog prozora, de je sam sebe cijepao: solo (5001–5200), zatim 2 paralelna pod-procesa (5201–5300 + 5301–5400), zatim 4 paralelna pod-procesa (5401–5500 do 5701–5800).*

**Tabela 1**

| Opseg | Start (CEST) | Kraj (CEST) | Trajanje | Rečenica/min | Paralelnih de-procesa |
|---|---|---|---|---|---|
| 5001–5200 | 12:03 | 12:51 | 0:48:43 | 4.11 | 1 (solo) |
| 5201–5300 | 13:48 | 14:41 | 0:52:24 | 1.91 | 2 |
| 5301–5400 | 13:48 | 14:42 | 0:53:53 | 1.86 | 2 |
| 5401–5500 | 14:45 | 15:25 | 0:40:15 | 2.48 | 4 |
| 5501–5600 | 14:45 | 15:19 | 0:34:26 | 2.90 | 4 |
| 5601–5700 | 14:45 | 15:32 | 0:47:51 | 2.09 | 4 |
| 5701–5800 | 14:45 | 15:27 | 0:42:24 | 2.36 | 4 |

**Tabela 2**

| Opseg | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| 5001–5200 | 0.9650 | 0.9470 | 0.9771 | 108 (54.0%) | 86 (43.0%) | 6 (3.0%) |
| 5201–5300 | 0.9668 | 0.9430 | 0.9827 | 59 (59.0%) | 38 (38.0%) | 3 (3.0%) |
| 5301–5400 | 0.9632 | 0.9460 | 0.9747 | 51 (51.0%) | 47 (47.0%) | 2 (2.0%) |
| 5401–5500 | 0.9672 | 0.9496 | 0.9791 | 51 (51.0%) | 47 (47.0%) | 2 (2.0%) |
| 5501–5600 | 0.9614 | 0.9440 | 0.9730 | 56 (56.0%) | 37 (37.0%) | 7 (7.0%) |
| 5601–5700 | **0.9515** | 0.9443 | **0.9564** | 50 (50.0%) | 44 (44.0%) | 6 (6.0%) |
| 5701–5800 | 0.9623 | 0.9453 | 0.9737 | 46 (46.0%) | 50 (50.0%) | 4 (4.0%) |

*Zapažanje: 5601–5700 (4. paralelni pod-proces) ima primjetno niži avg_sudija (0.9564 naspram ~0.97-0.98 kod ostalih) — vjerovatno sadržajni šum na malom uzorku (n=100), ne sistematski efekat pozicije.*

### Batch 3 — hr/it/sr paralelno (de već ispred, izostavljen), opseg 5001–5400 (22. jul, popodne)

**Tabela 1**

| Jezik | Start (CEST) | Kraj (CEST) | Trajanje | Rečenica/min |
|---|---|---|---|---|
| hr | 15:47 | 19:37 | 3:50:43 | 1.73 |
| it | 15:47 | 19:35 | 3:48:21 | 1.75 |
| sr | 15:47 | 19:37 | 3:49:56 | 1.74 |
| **ZBIR (3 jez.)** | | | | **5.22** |

**Tabela 2**

| Jezik | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| hr | 0.9662 | 0.9495 | 0.9773 | 229 (57.2%) | 153 (38.2%) | 18 (4.5%) |
| it | 0.9674 | 0.9497 | 0.9793 | 211 (52.8%) | 166 (41.5%) | 23 (5.8%) |
| sr | 0.9632 | 0.9474 | 0.9738 | 236 (59.0%) | 157 (39.2%) | 7 (1.8%) |

### Batch 4 — hr/it/sr paralelno, opseg 5401–5800 (22. jul, veče)

**Tabela 1**

| Jezik | Start (CEST) | Kraj (CEST) | Trajanje | Rečenica/min |
|---|---|---|---|---|
| hr | 20:26 | 23:20 | 2:54:19 | 2.29 |
| it | 20:26 | 23:15 | 2:49:26 | 2.36 |
| sr | 20:26 | 23:22 | 2:56:06 | 2.27 |
| **ZBIR (3 jez.)** | | | | **6.92** |

**Tabela 2**

| Jezik | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M |
|---|---|---|---|---|---|---|
| hr | 0.9641 | 0.9499 | 0.9736 | 204 (51.0%) | 182 (45.5%) | 14 (3.5%) |
| it | 0.9661 | 0.9488 | 0.9777 | 185 (46.2%) | 190 (47.5%) | 25 (6.2%) |
| sr | 0.9625 | 0.9479 | 0.9723 | 220 (55.0%) | 171 (42.8%) | 9 (2.2%) |

### Batch 5 — sva 4 jezika paralelno, opseg 5801–6200 (23. jul, popodne)

**Tabela 1**

| Jezik | Start (CEST) | Kraj (CEST) | Trajanje | Rečenica/min |
|---|---|---|---|---|
| de | 14:22 | 19:19 | 4:57:20 | 1.35 |
| hr | 14:22 | 19:14 | 4:52:33 | 1.37 |
| it | 14:22 | 19:15 | 4:53:34 | 1.36 |
| sr | 14:22 | 19:18 | 4:56:27 | 1.35 |
| **ZBIR (4 jez.)** | | | | **5.43** |

**Tabela 2**

| Jezik | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M | sudija_real |
|---|---|---|---|---|---|---|---|
| de | 0.9625 | 0.9443 | 0.9746 | 223 (55.8%) | 163 (40.8%) | 14 (3.5%) | 167m24s |
| hr | 0.9656 | 0.9474 | 0.9778 | 239 (59.8%) | 145 (36.2%) | 16 (4.0%) | 151m29s |
| it | 0.9619 | 0.9457 | 0.9728 | 217 (54.2%) | 161 (40.2%) | 22 (5.5%) | 157m51s |
| sr | 0.9622 | 0.9449 | 0.9738 | 254 (63.5%) | 142 (35.5%) | 4 (1.0%) | 132m39s |

### Batch 6 — sva 4 jezika paralelno, opseg 6201–6600 (23. jul, rano veče)

**Tabela 1**

| Jezik | Start (CEST) | Kraj (CEST) | Trajanje | Rečenica/min |
|---|---|---|---|---|
| de | 19:23 | 21:26 | 2:03:19 | 3.24 |
| hr | 19:23 | 21:34 | 2:11:11 | 3.05 |
| it | 19:23 | 21:31 | 2:08:57 | 3.10 |
| sr | 19:23 | 21:39 | 2:16:51 | 2.92 |
| **ZBIR (4 jez.)** | | | | **12.31** |

**Tabela 2**

| Jezik | Final | Komp | Sudija | glm-5.2 | mistral-large-3 | nllb-600M | sudija_real |
|---|---|---|---|---|---|---|---|
| de | 0.9635 | 0.9413 | 0.9783 | 210 (52.5%) | 169 (42.2%) | 21 (5.2%) | 27m31s |
| hr | 0.9635 | 0.9427 | 0.9775 | 225 (56.2%) | 162 (40.5%) | 13 (3.2%) | 29m54s |
| it | 0.9659 | 0.9450 | 0.9799 | 199 (49.8%) | 181 (45.2%) | 20 (5.0%) | 29m14s |
| sr | 0.9603 | 0.9407 | 0.9759 | 239 (59.8%) | 152 (38.0%) | 9 (2.2%) | 29m46s |

### Zapažanja — poređenje sa starim podacima i DAN/VEČE obrazac

**Najčistije poređenje u ovom runu — Batch 5 vs Batch 6:** identičan setup (ista 4 jezika, isti dan 23. jul, ista veličina opsega 400 rečenica po jeziku, isti redoslijed 4-paralelno), jedina razlika je vrijeme starta (14:22 CEST vs 19:23 CEST, ~5h razmaka). Zbir rečenica/min skače sa **5.43 → 12.31 (2.27× brže uveče)**, uz identičan kvalitet (avg_final 0.9605 vs 0.9633, razlika unutar šuma).

**Naspram istorijskih referentnih brojki:**
- Stari solo-sekvencijalni baseline (s117, jedan tok kroz 4 jezika redom): 0.64–1.33 rec/min.
- Stari "4 paralelne grupe" agregat (s119/s132, svaka grupa = 4 jezika sekvencijalno unutar sebe): ~3.47–3.77 rec/min, izmjereni faktor ubrzanja ~2.47× naspram solo.
- Ovaj run, PO-JEZIKU paralelizam (4 nezavisna toka umjesto 4 grupe): Batch 1 (jutro) zbir 6.72, Batch 5 (popodne, sljedeći dan) zbir 5.43 — oba u DAN periodu, oba u istom rasponu kao ili nešto iznad starog "4 paralelne grupe" agregata. Batch 6 (veče) zbir **12.31** — znatno iznad bilo čega ranije izmjerenog, čak i uz raniju pretpostavku o "nema hard ograničenja Pro tier-a".

**Uzrok — razlaganje po komponenti (de, Batch 5 vs Batch 6, identičan opseg 400 rečenica):**
- Sudija (gemma4:31b, isključivo Ollama Cloud): 167m24s → 27m31s — **6.1× brže uveče**
- Prevodi (glm-5.2 + mistral-large-3, Ollama Cloud): 129m44s → 95m37s — 1.36× brže uveče
- NLLB (jedini korak koji radi lokalno, ne na Ollama Cloud): 17m43s → 12m59s — **1.36× brže uveče, identičan faktor kao cloud prevodi**

Podudarnost NLLB-a (lokalno) i prevoda (cloud) na istom ~1.36× faktoru sugeriše zajednički uzrok koji pogađa i lokalno računanje i mrežni saobraćaj podjednako (moguće: opterećenje dijeljenog VPS-a). Sudija ima DODATNI, mnogo veći faktor (6.1×) specifičan samo za taj jedan Ollama Cloud model/poziv — vjerovatno opterećenje na Ollama-inoj strani, nezavisno od Flaviove infrastrukture. Ranija subjektivna napomena u README-u (degradacija 16-18h CEST) NIJE potvrđena ovim podacima — naprotiv, period 19-22h CEST je ovdje dosljedno najbrži period u cijelom setu.

**Kvalitet ostaje stabilan kroz sve batch-eve** (avg_final 0.9603–0.9681) — potvrđuje već uspostavljen nalaz da brzina varira sa opterećenjem, kvalitet ne.

### Dodatak — provjera lokalnih resursa VPS-a (s151, sysstat/sar)

Oracle Cloud VPS (Frankfurt, aarch64, 4 vCPU) ima instaliran `sysstat` sa istorijskim podacima za 16-24. jul (`/var/log/sysstat/sa*`). Provjera %steal (CPU vrijeme oduzeto od strane hipervizora za druge tenante na istom fizičkom hostu) za 22-23. jul: **prosjek 0.03-0.04%, maksimum 0.32%** — zanemarljivo kroz cijeli period, uključujući i najsporije i najbrže batch-eve. **Isključuje "buku komšija" (multi-tenant kontencija) kao uzrok DAN/VEČE razlike izmjerene gore.**

Lokalni %user CPU pravi oštre skokove (do ~98%) koji se poklapaju sa START-om batch-eva, ali ne traju kroz njihovo cijelo trajanje — mašina večinu vremena čeka na Ollama Cloud mrežne pozive, ne računa lokalno. Vjerovatan izvor skokova: NLLB (lokalna inferenca) + e5-large embedding, jedini CPU-vezani koraci pipeline-a; sa 4 paralelna jezika na samo 4 vCPU jezgra postoji stvarna samo-kontencija (procesi se međusobno takmiče za jezgra), sekundaran faktor naspram dominantnog Ollama Cloud opterećenja identifikovanog gore.

Backup prozor (01:10-01:30 CEST) potvrđen identično oba dana u sar podacima, van svih analiziranih batch-eva — nema preklapanja s ovom analizom.
