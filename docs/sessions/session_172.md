# Session 172 — Sonde nad sidrom i ulogama, treći worker, kaskade 11/12/13

**Datum:** 12. avgust 2026.
**Fokus:** četiri READ-ONLY sonde (random sidro, zamjena uloga, kandidati za model, novi worker) → registracija `qwen3.5:397b` → `run_kaskada11.sh` / `run_kaskada12.sh` / `run_kaskada13.sh` → produkcijski test kaskade11 uz mjerenje potrošnje na Ollami.

---

## 1. Snimak zdravlja (početak sesije)

| Metrika | Vrijednost |
|---|---|
| Rečenice | 50.624 |
| Prevodi | 2.057.322 |
| Pobjednici | 402.772 |
| Rupe | 343 (nepromijenjeno od s171) |

Sve zeleno. `buchenberg` na `013f479`, `buchenweb` čist ali zaostaje 3 sesije (BB_VERSION s168).

---

## 2. Analiza 16 kaskada10 logova (k12, 11 jezika)

Nula Tracebackova, 6 timeouta (svi pokriveni retryjem). Svi prolazi stali po gate-nuli, `--max 30` nije opalio nigdje.

**Krugova:** medijana **7 = 21 izvršena faza** (kaskada8 je imala ~12 rundi).

**Ispražnjenost lijevka je dvostruko dublja nego u kaskadi7** na 9 od 10 jezika:
pt −68% (k7: −34%), es −67% (−27%), nl −54% (−31%), ja −45…−77% (−25%),
sl −42% (−25%), bg −41…−51% (−18%), ro −40% (−23%), mk −26% (−13%).
Jedini fr je gori (−33% naspram −45%).
⚠️ Ograda: drugi opsezi, a sedmica je vrtjela jednu fazu po rundi — dio razlike je veći obim posla po krugu.

### 2.1 Prazan rep je strukturno neizbježan — potvrda Flaviove procjene

Stajanje traži krug u kojem nijedna faza nije prebacila (**3 prazne faze**) plus potvrdu iz prve faze sljedećeg kruga (**+1**) = **minimum 4 faze u prazno po prolazu, po konstrukciji.**

Izmjereno (delta između susjednih gate tačaka, pripisana fazi između njih):
raspon **4–6, medijana 5**. Ukupno **79 od 358 faza (22%)** dokazano bez doprinosa.
Flavio je procijenio "5 je skoro pravilo" prije mjerenja — tačno.

Drugi izvor praznog hoda: **jedna prebačena rečenica kupuje cijeli sljedeći krug od tri faze.**
ja₅₀₀₁ zadnjih 7 krugova = 21 faza za 10 rečenica; sl krugovi 5–8 = 12 faza za 4 rečenice.

### 2.2 KOREKCIJA s171: faza 24 (strict) NIJE mrtva

| osa | prelazaka | udio | po izvršavanju |
|---|---|---|---|
| f12 base | 173 | 32% | 1.41 |
| f16 seed | 234 | **44%** | **1.97** |
| **f24 strict** | **127** | **24%** | 1.09 |

Ukupno 534 prelaska na 358 faza (1.49 po fazi).

s171 je strict mjerio **jednom, poslije iscrpljenog base+seed niza**, dobio 0.005–0.032 % n i klasifikovao ga kao "završnu rundu iscrpljenog mehanizma". U petlji, nad sidrom koje se svaki krug mijenja, daje **1.09 prelazaka po izvršavanju** — isti red veličine kao base. Flaviov argument iz s171 §3.2 ("faza nad promijenjenim sidrom nije ista faza") je time **izmjeren, ne više izveden**.

Najjači: ja₂₀₀₁ **17** (više od f16), ja₁₉₀₁ 15, ja₄₉₀₁ 15, ja₅₀₀₁ 12, bg₅₀₀₁ 11 (gdje f16 daje 5), pt 11, bs₅₁₀₁ 10. Nula jedino es.

---

## 3. SONDA 1 — random sidro umjesto pobjednika (`sandbox_random_seed.py`)

**Flaviova ideja:** seed je danas uvijek apsolutni pobjednik; uzeti umjesto toga slučajan prevod iz skupa, po mogućnosti uz isključenje pobjednika kad alternativa postoji. Motiv: to više liči na mutaciju.

**Dizajn:** tri rukavca nad istim rečenicama, isti model/temp/prompt (mistral@0.8, `refine`):
- **A1** seed = pobjednik (današnje ponašanje)
- **B** seed = random NE-pobjednik (stroga verzija)
- **A2** seed = pobjednik, opet (šum ponavljanja — bez njega se A1−B mjeri protiv ničega)

Svi kandidati + pobjednik ocijenjeni **jednim** pozivom sudiji po rečenici, redoslijed randomizovan. Pobjednik preračunat istom formulom i **istom novom** sudijinom ocjenom (njegov `finalni_score` u bazi nosi ocjenu iz druge sudijske ere — s167).

**Teren:** k23/de i k23/hr (svjež, samo faza 1), k24/sl (**iscrpljen** — faze 12 i 16 prošle). n=40 svaki.

### Rezultat

| teren | 1 poziv A1 → B | uparena razlika B−A1 | šum A2−A1 | t |
|---|---|---|---|---|
| k23/de svjež | 0.8947 → 0.8990 | +0.0043 | −0.0055 | 0.52 |
| k23/hr svjež | 0.9095 → 0.8934 | −0.0161 | +0.0089 | −1.30 |
| k24/sl iscrpljen | 0.8835 → 0.8747 | −0.0089 | +0.0078 | −0.65 |

**Nijedna razlika ne izlazi iz šuma ponavljanja** (|t| < 2 svugdje). Smjer dvaput negativan.

Budžet od dva poziva (argmax): čisto A1+A2 naspram mješovito A1+B → de +0.0094, hr −0.0031, sl −0.0023.

**Prelasci praga — random sidro gubi 2:1 do 5:1:**

| teren | B jedini prešao | A-par jedini prešao |
|---|---|---|
| de | 4/40 | 7/40 |
| hr | 2/40 | 10/40 |
| sl | 2/40 | 5/40 |

### Jedini pozitivan nalaz

**Na iscrpljenom terenu random sidro ne proizvodi klonove uopšte:** k24/sl A1 12.5%, A2 10.0%, **B 0.0%**. Na svježem terenu razlike nema. Mehanizam radi kako je Flavio predvidio — promjena sidra razbija klon-zaglavljenost — ali daje **različit**, ne **bolji** tekst.

**Zaključak:** ideja je konceptualno tačna, ali raznolikost se ne pretvara u prelaske praga. Izlaz regresira ka kvalitetu sidra (isti gradijent kao s169 §2.7). Mjesto joj je kao **uslovni okidač za klon-zaglavljenost**, ne kao opšta strategija — i tada nema nijednog slobodnog broja, kao ni pravilo o strogoj nuli.

---

## 4. SONDA 2 — zamjena uloga: gemma prevodi, mistral sudi (`sandbox_zamjena_uloga.py`)

**Dizajn:** po rečenici četiri kandidata — M (mistral iz baze), G (glm), N (nllb), GW (novi gemma prevod). Isti skup ocijenjen tri puta: **S1** gemma4, **S2** mistral, **S1b** gemma opet (šum). k23/de n=40, k23/hr n=39.

`bb_08` NIJE mijenjan — `SUDIJA_MODEL` zamijenjen samo u memoriji sonde.

### 4.1 Sudija nije zamjenjiva komponenta

| | de | hr |
|---|---|---|
| slaganje argmaxa gemma↔mistral | **57.5%** | **46.2%** |
| slaganje gemma↔sama sebe (šum) | 95.0% | 97.4% |
| MAE gemma↔mistral | 0.0733 | 0.1169 |
| MAE gemma↔gemma | 0.0019 | 0.0015 |

**MAE između sudija je 40–75× iznad šuma**, izbor pobjednika se mijenja na **42–54% rečenica**. Za poređenje, s167 je izmjerio da promjena naziva jezika u promptu mijenja argmax u 10–13%.

**Posljedica:** korpus od 402.772 pobjednika je artefakt izbora gemme kao sudije. S drugim sudijom skoro polovina bila bi drugi tekst. Ne znači da je pogrešan — znači da je "najbolji prevod" operativno definisan kao "ono što gemma preferira" (ograda iz s139).

Mistral je sistematski stroži — spušta sve kandidate (de −0.026 do −0.067; hr −0.005 do −0.062).

### 4.2 Self-preference NIJE potvrđena

Razlika-razlika (koliko mistral podiže svoj prevod naspram gemminog): de **+0.0229**, hr **−0.0158**. Suprotan znak, male veličine. Rangiranje po pobjedama gotovo netaknuto (de M 25→26, hr M 21→19).

Konflikt interesa koji je dizajn tražio se nije materijalizovao — dobra vijest za buduću upotrebu mistrala kao rezervnog sudije.

### 4.3 Gemma kao prevodilac — treća od četiri

| autor | de (S1/S2) | hr (S1/S2) | pobjede de | pobjede hr |
|---|---|---|---|---|
| M mistral | 0.9650 / 0.9392 | 0.9359 / 0.8744 | 25→26 | 21→19 |
| G glm | 0.9483 / 0.9204 | 0.9325 / 0.8923 | 8→8 | 10→12 |
| GW gemma | 0.9417 / 0.8929 | 0.8846 / 0.8389 | 5→4 | 7→5 |
| N nllb | 0.7708 / 0.7042 | 0.6325 / 0.6278 | 2→2 | 1→3 |

Iznad nllb-a, ispod oba produkcijska LLM-a. Gemmin kompozitni je pritom visok (hr 0.9485 naspram sudijine 0.8846) — potvrda s146 da kosinus i sudija mjere različite stvari.

⚠️ Gemma ocjenjuje **sopstveni** prevod; mistral ga spušta koliko i ostale, pa se ni gemmina self-preference ne vidi, ali dizajn je tu slabiji (nema trećeg nezavisnog sudije).

**Zaključak:** zamjena se ne preporučuje. Ali **izbor sudije je najkrupniji neregistrovani parametar dosad izmjeren** — veći od prompta (s139), sastava batcha (s170) i naziva jezika (s167). Materijal za `limits.html`.

**Gemma ostaje sudija iz pozicionog, ne kvalitetnog razloga: jedina je komponenta koja ne prevodi.**

---

## 5. Istraživanje Ollama katalog — klase potrošnje

Ollama naplaćuje po GPU vremenu; svaki model nosi *usage level* 1–4 objavljen na `library/<model>/tags`.
Referenca: **mistral-large-3:675b-cloud = Medium (klasa 2)**.

| model | klasa |
|---|---|
| gpt-oss:20b | 1 — low |
| **mistral-large-3:675b** | **2 — Medium** (naš) |
| **qwen3.5:397b** | **2 — Medium** |
| **nemotron-3-super** | **2 — Medium** |
| **deepseek-v4-flash** (3 taga) | **2 — Medium** |
| minimax-m2.7 | 2 — Medium |
| **glm-5.2** | **3 — High** (naš) |
| minimax-m3 | 3 — High |
| kimi-k2.6 | 3 — High |
| kimi-k3 | 4 — Extra High |
| deepseek-v4-pro | 4 — Extra heavy |
| glm-5.1, gpt-oss:120b, nemotron-3-ultra/nano, kimi-k2.7-code, gemma4:31b | nije objavljeno |

**glm-5.2 je klasa 3** — poklapa se s onim što je Flavio vizuelno vidio na dashboardu u s156.

---

## 6. SONDA 3 — ponašanje kandidata (`sandbox_model_probe.py`, hr, `think:false`)

| model | think | evalC | s/poziv | čistoća | batch |
|---|---|---|---|---|---|
| mistral (etalon) | ne | 10 | 1.1 | čist | 5/5 |
| **qwen3.5:397b** | ne | 11 | 1.5 | čist | 5/5 |
| **deepseek-v4-flash:0731** | ne | 12 | **0.9** | čist | 5/5 |
| nemotron-3-super | ne | 8 | **36.3** | čist | 5/5 |
| minimax-m2.7 | **DA** | **785** | **17.6** | čist | 5/5 |
| gemma4:31b (kontrola) | ne | 10 | 1.0 | čist | 5/5 |

**Otpali:** minimax-m2.7 (ignoriše `think:false`, 785 tokena — obrazac gpt-oss iz s109), nemotron-3-super (36 s po pozivu, 33× sporiji).

**Ispravka sonde:** `temp_react` mjeri **jedan par poziva na jednoj rečenici** (n=1) — nedovoljno da se model proglasi temp-mrtvim. Proširena provjera (5 poziva × 2 rečenice × 2 temperature) pokazala je da qwen **nije** temp-mrtav: na dugoj rečenici 5/5 različitih već na 0.1, šira distribucija od mistrala.

---

## 7. SONDA 4 — qwen kao treći worker (`sandbox_novi_worker.py`)

**Dizajn:** pet kandidata po rečenici (M, G, N, Q1=qwen@0.1, Q8=qwen@0.8) — isti broj kao produkcijski "svijet 1". Sudija gemma4 ocjenjuje svih pet jednim pozivom; drugi identičan poziv daje šum. Knjiga konstanta (k23), četiri jezika rastuće težine, n=40.

| | sudija M / G / Q1 / Q8 | pobjede Q1+Q8 | najbolji bez Q → s Q | šum |
|---|---|---|---|---|
| **de** | 0.967 / 0.937 / 0.906 / 0.908 | 8/40 | 0.9643 → 0.9703 | 0.0043 |
| **hr** | 0.936 / 0.899 / 0.924 / 0.914 | 17/40 | 0.9584 → 0.9714 | 0.0018 |
| **sl** | 0.912 / 0.917 / **0.933** / 0.915 | 14/40 | 0.9540 → 0.9659 | 0.0033 |
| **mk** | 0.931 / 0.949 / 0.899 / **0.952** | 15/40 | 0.9570 → 0.9661 | 0.0050 |

Dobitak **2–7× iznad šuma**. Na sl je qwen@0.1 najbolji pojedinačni model u polju; na mk je qwen@0.8 izjednačen s glm-om.

**Efekat na gate:** ispod praga bez qwena → s qwenom: de 9→7, hr 9→**4**, sl 12→8, mk 12→9. Qwen prazni lijevak za **22–56% već u root fazi**.

Obje temperature žive (Q1 vodi na mk, Q8 na hr/sl). Klon-stopa 12–28%.

**Zaključak sonde:** qwen se kvalifikuje. ⚠️ **Ova sonda NE mjeri potrošnju — to je propust koji je kasnije ispao odlučujući (§11).**

---

## 8. KOREKCIJA — glm je najbolji worker, ne mistral

Sonda je na 160 rečenica sugerisala da je mistral jači na de/hr, glm na sl/mk. Upit nad **zajedničkim terenom** (rečenice gdje su oba modela imala kandidata) to obara:

**glm pobjeđuje mistrala na SVIH 14 jezika, 58–64%, bez ijednog izuzetka** — uključujući de (10.939 : 7.890) i hr (11.947 : 7.732). Nema jezičke specijalizacije.

Uzrok greške: 40 rečenica po jeziku iz jedne knjige, uz ocjene preračunate novim sudijskim pozivom nad drugačijim skupom kandidata. Efekat sastava skupa je bio izmjeren u istoj sesiji, pa pušten u zaključak umjesto odbijen.

**Kumulativni upit po modelu je zavaravajući:** gemma3:12b (34.1%) i ministral-3:14b (25.0%) drže 59% pobjednika jer su radili sami prije nego što su mistral i glm ušli. Prosjek `finalni_score` po pobjedniku mjeri lakoću osvojenih rečenica, ne kvalitet modela.

---

## 9. Registracija qwena i nove faze

| stavka | vrijednost |
|---|---|
| `bb_modeli` | **id 28**, `qwen3.5:397b`, aktivan |
| faza 1 (base) | qwen dodan s temp 0.0 / 0.1 / 0.8 |
| **faza 27** | qwen3.5:397b @ 0.8, `base` |
| **faza 28** | qwen3.5:397b @ 0.8, `refine-strict` |

Faze 12 (mistral@0.8 base) i 24 (mistral@0.8 strict) su preuzete postojeće.

---

## 10. Kaskade 11, 12 i 13

### 10.1 `run_kaskada11.sh` / `run_kaskada12.sh`

| | kaskada11 | kaskada12 |
|---|---|---|
| root | qwen@0.1 | mistral@0.1 |
| krug (max 3) | faza 12 → faza 27 | faza 27 → faza 12 |
| seed blok (1×) | faza 24 → faza 28 | faza 28 → faza 24 |

**Razlike u odnosu na kaskadu10:** tvrdi plafon od 3 kruga; stop **odmah** čim obje faze kruga vrate nulu (bez potvrdnog kruga); seed blok izvan petlje, izvršava se uvijek pri izlasku, tačno jednom svaka faza.

`diff` pokazuje da se skripte razlikuju **isključivo u 4 konfiguracijske linije**. Oba `bash -n` čista.

**Mini test (k22/hr, 20 rečenica):** k11 root ostavio 5, kraj 0; k12 root ostavio 7, kraj 2. Oba stala gate-nulom u 2. krugu, 0 Tracebackova.

Zapažanje iz mini testa: **faza 27 dala nulu u jedanaestici, +3 u dvanaestici** — vrijednost modela zavisi od toga čiji je materijal već u bazenu.

### 10.2 `run_kaskada13.sh` (napisan, NIJE testiran)

Dvoblokovska, uslovni skupi blok:
- root mistral@0.1
- **blok A** max 4 kruga: faza 12 → faza 24 (mistral). Najmanje 1×; izlaz kad krug nema prirasta.
- **uslov:** ako je % pobjednika iznad praga **< X** (novi parametar `--x`, default **60**) → blok B
- **blok B** max 2 kruga: faza 14 → faza 26 (glm@0.8 base → glm@0.8 strict). Isto pravilo izlaza.

Cijena: najbolji **3 faze**, A do plafona bez B **9**, najgori **13**.

**X mjeri STANJE, stop unutar bloka mjeri PRIRAST** — namjerno različito: X bira *da li* platiti glm, prirast bira *koliko dugo*.

Obrazloženje X=60: postotak iznad praga na kraju mistralovog bloka je 43–55 (mk, pt, sl), 60–68 (fr, af, ro, bg, bs, nl), 78–86 (es, ja). X=60 pušta glm na teške jezike, preskače es/ja.

Nijedna nova faza — sve četiri postoje. Grananje testirano suho (59% → B, 60% → preskače), bez ijednog poziva Ollami.

---

## 11. PRODUKCIJSKI TEST kaskade11 (k12, 11 jezika × 100 rečenica)

Flavio vozio 3 paralelna procesa. **9 jezika kompletno, mk i ja prekinuti** (§12).

### 11.1 Ishod

| jz | root ostavio | kraj | krugova |
|---|---|---|---|
| es | 52 | **14** | 3/3 plafon |
| fr | 66 | 35 | 3/3 |
| af | 66 | 35 | 3/3 |
| ro | 55 | 27 | 3/3 |
| pt | 64 | 41 | 3/3 |
| nl | 70 | 25 | 3/3 |
| bg | 66 | 42 | 3/3 |
| sl | 71 | 33 | 3/3 |
| bs | 76 | 40 | 3/3 |
| mk | 75 | prekinut | 2 |
| ja | 81 | prekinut | 0 |

**Plafon od 3 kruga opalio na svih 9** — nijedan nije stao gate-nulom.

**Kaskada11 postiže isti ishod kao desetka s trećinom faza:**

| jz | kaskada10 | kaskada11 |
|---|---|---|
| es | 14 | 14 |
| fr | 36 | 35 |
| af | 36 | 35 |
| ro | 40 | **27** |
| pt | 22 | **41** |
| nl | 32 | **25** |
| **prosjek** | **30.0** | **29.5** |

Desetka: medijana **21 faza**. Jedanaestica: fiksno **8**. **Arhitektura je bolja; problem je model u njoj.**

### 11.2 Doprinos po modelu (9 kompletnih jezika)

| | mistral (f12) | qwen (f27) | seed mistral (f24) | seed qwen (f28) |
|---|---|---|---|---|
| prelazaka | **186** | **57** | 32 | 19 |

Mistral ukupno **218**, qwen **76** — odnos **2.9:1**.
⚠️ f27 uvijek ide **druga** u krugu (nasljeđuje prorijeđen teren) — ista zamka zbog koje je s171 pogrešno proglasio strict mrtvim. Na sl (14) i bs (12) je qwen bio znatno jači nego na ostalima.

Qwen kao **root** se drži dobro: ostavlja 52–81 ispod praga, uporedivo s onim što je u kaskadi10 ostavljao mistral+nllb **zajedno**.

### 11.3 Vrijeme — qwen je 2.5× sporiji po rečenici

| jz | f12 mistral | f27 qwen | s/rečenici mistral → qwen |
|---|---|---|---|
| es | 8:10 / 95 rec | 11:33 / 64 rec | 5.2 → 10.8 |
| fr | 9:12 / 155 | 25:13 / 132 | 3.6 → 11.5 |
| af | 21:26 / 163 | 33:43 / 143 | 7.9 → 14.1 |
| ro | 10:45 / 129 | 18:55 / 111 | 5.0 → 10.2 |
| pt | 8:42 / 166 | 27:56 / 150 | 3.1 → 11.2 |
| nl | 9:34 / 156 | 24:29 / 125 | 3.7 → 11.8 |
| **ukupno** | **67:49** | **141:49** | **4.7 → 11.6** |

### 11.4 POTROŠNJA — glavni nalaz sesije

Snapshoti Ollama dashboarda (CEST):

| vrijeme | sedmično | gemma4 | mistral | qwen |
|---|---|---|---|---|
| 09:56 (baseline) | 13.6% | 42.371 | 9.922 | 65 |
| 11:27 | 16.4% | 43.384 | 10.002 | 155 |
| 14:11 | 23.0% | 45.537 | 10.152 | 404 |
| 16:00 | 26.6% | 46.696 | 10.234 | 543 |
| 16:56 | 27.9% | 46.955 | 10.260 | 595 |
| **18:09 (kraj)** | **28.7%** | **47.134** | **10.288** | **626** |

**Delta: gemma +4.763, mistral +366, qwen +561. Sedmično +15.1 poena.**

**Ollama sortira listu po potrošnji — qwen je na kraju bio PRVI, ispred mistrala (10.288) i gemme (47.134).**

Po zahtjevu qwen troši oko **35× više od mistrala** i preko **300× više od gemme**. Odnos stabilan kroz cijeli test.

**Vrijeme to ne objašnjava** (2.5× sporiji ≠ 35× skuplji). Naplaćuje se GPU-zauzeće, ne zidno vrijeme — 397B model raširen preko više GPU-a troši višestruko GPU-sekundi po sekundi rada.

### 11.5 Flaviova ocjena — prihvaćena

> "Model troši višestruko više za isti ili gori posao."

Zatvoreno s obje strane: **nije brži** (2.5× sporiji), **nije bolji** (slabiji od mistrala na de/hr; dobitak 0.006–0.013 gdje pobjeđuje), **troši višestruko više**. Deklarisana klasa 2 nije pokriće.

**Greška u preporuci (Claude):** qwen je preporučen na osnovu deklarisane klase i sekundi po pozivu — a nijedno ne mjeri potrošnju. Trebalo je reći da mjera potrošnje nedostaje, umjesto predstaviti dvije zamjene kao dovoljne.

**Sonda ponašanja i sonda kvaliteta ne vide potrošnju. Za nju je potreban produkcijski run uz dashboard.**

---

## 12. INCIDENT — dva zaglavljena procesa

Oba puta **qwen faza 27**, oba puta isti obrazac:

| jezik | zadnji upis | stajao | CPU za 2h+ rada |
|---|---|---|---|
| mk | 16:33 | 19 min | 9 s |
| ja | 17:48 | 16 min | 9 s |

Prethodilo: `500 Server Error` na batchu ×3 → fallback na single → `Read timed out (read timeout=120)` → tišina.

**Dijagnoza (Claude), prva verzija POGREŠNA:** pretpostavljeno da `timeout` pokriva samo read. Provjera pokazala `timeout=120` kao goli broj, što u `requests` pokriva **i connect i read**. Rupe kakva je opisana nema.

**Vjerovatno stvarno objašnjenje:** read timeout u `requests` mjeri **razmak između primljenih bajtova**, ne ukupno trajanje odgovora. Server koji odgovara u kapima drži konekciju živom neograničeno. Poklapa se s 9 s CPU vremena (proces sjedi na socketu).

**Popravka nije jedna linija** — traži ukupni watchdog (`stream=True` uz mjerenje proteklog vremena, ili sličan mehanizam). Odgođeno da ne blokira Flavia.

Ollama je tog popodneva bila nestabilna generalno — 500-ke na dva jezika u razmaku od pola sata, uz nepromijenjenu našu stranu.

---

## 13. Lekcije

**Mjerenje:**
- Sonda ponašanja mjeri sekunde, sonda kvaliteta ocjene — **ni jedna ne vidi potrošnju**. Za nju treba produkcijski run uz dashboard.
- Deklarisana klasa modela kod Ollame **ne predviđa stvarnu potrošnju** (qwen i mistral su ista klasa, odnos 35:1).
- 40 rečenica po jeziku isključuje **veliki** efekat, ne mali. Upit nad korpusom nadjačava sondu (§8).
- Sastav skupa kandidata mijenja sudijinu ocjenu — poređenje mora ići kroz **isti poziv**.
- Faza koja ide **druga u krugu** nasljeđuje prorijeđen teren; njeni brojevi nisu uporedivi s prvom (s171 strict, s172 faza 27).
- `temp_react` u `sandbox_model_probe.py` je n=1 — nije dokaz.

**Arhitektura:**
- Prazan rep u kaskadi10 je **strukturno neizbježan**: minimum 4 faze, medijana 5, 22% ukupnog rada.
- Kaskada11 postiže ishod desetke s **8 faza umjesto 21** — plafon + stop bez potvrdnog kruga rade.
- Izbor sudije je **najkrupniji neregistrovani parametar** (42–54% argmaxa), veći od prompta, batcha i naziva jezika.
- Gemma ostaje sudija iz **pozicionog** razloga: jedina ne prevodi.

**Proces:**
- Kad brojka u poruci ne odgovara skripti, greška je vjerovatno u poruci — provjeriti prije nego što se korisnik zapita je li pogrešno razumio.
- Ne konvertovati vremenske zone bez potrebe i bez najave; Flavio gleda svoj sat.
- Kad korisnik dvaput ukaže na isti nalaz, ne tražiti treći dokaz — traka na dashboardu je bila dovoljna prvi put.

---

## 14. Stanje na kraju

**Baza:** qwen registrovan (id 28), faze 27 i 28 dodane. Sonde nisu ništa upisivale.

**Novi fajlovi (necommitovano do ove tačke):**
- `src/sandbox_random_seed.py`, `src/sandbox_zamjena_uloga.py`, `src/sandbox_novi_worker.py`
- `run_kaskada11.sh`, `run_kaskada12.sh`, `run_kaskada13.sh`

**Prekinuto:** mk (krug 3) i ja (krug 1) u kaskadi11 — mogu se ponovo pustiti, `already_done` preskače urađeno.

**NIJE urađeno:** kaskada12 nije pokrenuta (Flavio prešao direktno na 13); mini test kaskade13 odgođen da ne zamuti mjerenje.

**Otvoreno za s173:**
1. **Odluka o qwenu** — po izmjerenom, ne opravdava cijenu. Faze 27/28 i model ostaju registrovani do odluke.
2. **Watchdog na Ollama poziv** — `timeout=120` ne sprečava visenje pri sporom odgovoru.
3. **Rezultati kaskade13** — Flavio vozi, baseline 18:17: gemma 47.134, mistral 10.288, qwen 626, **glm 8** (glm praktično netaknut → izolovana cijena bloka B).
4. `deepseek-v4-flash` kao alternativa — jedini brži od mistrala u sondi, potrošnja neizmjerena.
5. Rezervni sudija (deepseek / nemotron) — samo ako Ollama nešto povuče.
6. Sonda "sidro iz modela van rotacije" — Flaviova ideja o gemma-seedu odbijena jer bi potrošila gemminu neutralnost.

---

*Flavio & Claude · Buchenberg · sesija 172 · 12. avgust 2026.*
