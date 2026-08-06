# Sesija 164 — 6. avgust 2026.

**Fokus:** Ekonomija kaskade. Polazeći od analize k12 runova, sesija je kroz niz mjerenja došla do zaključka da se glm faze mogu zamijeniti ponovljenim mistral rundama uz **3× manju potrošnju Ollama resursa za praktično identičan kvalitet**. Usput: eksperiment s paralelnošću (2→10 procesa), otkriće da je granica RAM a ne Ollama, i dijagnoza dva bug-a čiji je okidač bio spoljni a uzrok latentan.

---

## Otvaranje sesije

Standardni checklist proveden (project files, README u dva `sed` poziva, session_161/162/163, health check). Korpus na početku: 50.624/1.947.748/372.832 — narastao od kraja s163 (Flaviov k12 rad van sesije).

**Procesna greška na samom početku, ispravljena tek nakon Flaviove intervencije.** U izlazu health checka pojavio se red `k12 / de / faza 10 / glm-5.2 / 0.1 / 875 od 882 / rupa=7`. Claude ga je prijavio kao "mali novi red u rupama koji ranije nije bio u listi" i, na Flaviovo pitanje, krenuo u istragu uzroka — šest uzastopnih SQL upita, uključujući klasičnu `NOT IN`+NULL zamku koja je dvaput tiho vratila prazan rezultat.

Flavio je prekinuo ("Claude stani. Ovo više nema smisla.") i pitao odakle uopšte informacija da ima rupa.

Dvije greške u tome:
1. **"Novo" nije provjereno.** s161/s162/s163 sve prijavljuju istih 333 rupe, koliko i danas — red nije bio nov.
2. **Definicija "rupe" nije primijenjena.** README §5 i sam kod (`health_check.py`, linije 142-155) definišu rupu kao razliku od `MAX(prevedeno)` unutar grupe (knjiga, jezik, faza). Za **gated** fazu ta mjera ne važi — gate po dizajnu propušta različit broj rečenica po (model, temp) kombinaciji. Claude je isto to objasnio Flaviu za faze 11-14 pola sata ranije, pa nije primijenio na fazu 10.

---

## Dio 1 — Analiza k12 runova (10 logova, opsezi 1101-1200 i 1201-1400)

**Logovi:** nula traceback-ova, svi retry-evi riješeni na prvom pokušaju (503 / read timeout), svih 10 fajlova sa 4 `ZAVRŠENO` markera.

**Baza:** root faza 300/300 po jeziku, pobjednik za svih 300/300 rečenica u svakom od 10 jezika. Kompletnost 100%.

**Es/fr vs mk/sl obrazac objašnjen brojkama** — gate-ulazi po fazi (koliko rečenica ispod praga 0.95):

| Jezik | f11 | f12 | f13 | f14 |
|---|---|---|---|---|
| es | 261 | 128 | 106 | 83 |
| fr | 267 | 120 | 95 | 75 |
| mk | 272 | 186 | 172 | 146 |
| sl | 277 | 199 | 180 | 150 |

Mk/sl imaju skoro dvostruko više gated poziva u kasnijim fazama → direktan uzrok sporosti.

**Pitanje o dva `ZAVRŠENO` reda na kraju loga:** nisu duplikat. `run_faza.sh:67` piše `ZAVRŠENO` (sa Š) na kraju svakog poziva; `run_kaskada.sh:53` piše svoj `ZAVRSENO` (bez Š) na kraju cijele kaskade. Kozmetička nedosljednost, Flaviova odluka: ostaviti kako je.

---

## Dio 2 — Non-Ollama dio je jezično neutralan (Flaviova hipoteza, potvrđena)

Flaviova teza: sve što ne traži Ollamu (NLLB prevod, `bb_04_pobjednik`) mora biti slično za sve jezike.

**Pobjednik korak** (`real` vremena iz logova, sekunde):

| Par | 1101-1200 (f11/12/13/14) | 1201-1400 |
|---|---|---|
| es+fr | 10.3 / 10.4 / 10.4 / 12.8 | 14.5 / 20.6 / 21.0 / 22.5 |
| mk+sl | 8.0 / 11.1 / 12.2 / 13.2 | 16.3 / 22.8 / 21.8 / 24.6 |

Praktično identično.

**Korak 1** (root + sudija + pobjednik) nema vlastito `time` mjerenje — izveden računski (elapsed minus zbir faza):

| Par | Korak 1 (1101-1200) | Korak 1 (1201-1400) |
|---|---|---|
| es+fr | 30:11 | 49:57 |
| af+nl | 29:15 | 53:42 |
| bg+bs | 27:10 | 50:36 |
| pt+ro | 27:35 | 50:37 |
| mk+sl | **28:29** | **49:37** |

**Hipoteza potvrđena jače nego formulisana:** mk+sl je u drugom opsegu **najbrži od svih pet** u non-Ollama dijelu. Računica se zatvara: u opsegu 1201-1400 mk+sl je ukupno 36:18 sporiji od es+fr, u gated fazama 36:38 sporiji, a u koraku 1 je 20s **brži**.

Ograda: korak 1 sadrži i sudiju (Ollama), pa nije 100% čist blok. Za čisto mjerenje `run_kaskada.sh` bi trebao mjeriti root/sudiju/pobjednika zasebno.

---

## Dio 3 — Hendikep prag: ideja razmotrena i odbačena

Flaviova ideja: prag kao **hendikep** — ne apsolutni standard kvaliteta, nego kvantil vlastite distribucije po jeziku, tako da svaki jezik dobija isti udio pokušaja.

**Prvo je ispravljen smjer.** Flavio je predložio es/fr 0.94, mk/sl 0.96; gate propušta ispod praga, pa bi to mk/sl učinilo još skupljim. Flavio je grešku odmah priznao i preformulisao ideju kroz pojam hendikepa, što je pravo ime za mehanizam.

**Izmjereno** (k12, isti opseg 1-1400 za svih 14 jezika):

| Jezik | % ispod 0.95 | P25 (prag za 25% ulaza) |
|---|---|---|
| es | 14.8 | 0.9571 |
| nl | 15.4 | 0.9558 |
| fr | 17.1 | 0.9550 |
| pt | 19.6 | 0.9531 |
| bg | 23.4 | 0.9508 |
| bs | 23.9 | 0.9508 |
| ro | 28.4 | 0.9475 |
| af | 28.6 | 0.9439 |
| mk | 30.7 | 0.9439 |
| sl | 35.6 | 0.9361 |
| it | 36.1 | 0.9351 |
| de | 39.9 | 0.9330 |
| hr | 49.5 | 0.9087 |
| sr | 50.0 | 0.9121 |

Kolona P25 je gotova hendikep tabela (raspon 0.048, četiri puta veći od razlike u medijanama).

**Zašto odbačeno.** Flavio je postavio kriterij grubo i jasno: cijela vježba postoji da bi se smanjila potrošnja skupog modela; ako teoretski daje 4400 umjesto 4000 rečenica, ne vrijedi počinjati. Hendikep prag ne štedi ništa — preraspoređuje isti broj poziva između jezika. Gore: preraspodjela ide **suprotno headroom gradijentu** (s134) — uzima pokušaje tamo gdje se najviše dobija (mk/sl, niži seed) i daje tamo gdje se najmanje dobija (es/fr, blizu plafona).

**Metodološka ograda zabilježena:** mjerenje je rađeno na apsolutnim pobjednicima koji su već prošli kroz gate sa pragom 0.95 — distribucija koju je sam prag oblikovao (s139 povratna sprega). Stvarne razlike među jezicima vjerovatno su **veće** nego što tabela pokazuje.

---

## Dio 4 — Doprinos glm faza (13, 14) izmjeren

Opseg 1101-1400, 10 jezika, 3000 rečenica.

**Pobjede po fazi:**

| Faza | Poziva | Pobjeda | Win-rate | Prosjek pobjede |
|---|---|---|---|---|
| 1 (root) | — | 368 | — | 0.9582 |
| 11 (mistral@0.1) | 2668 | 1390 | 52.1% | 0.9557 |
| 12 (mistral@0.8) | 1536 | 456 | 29.7% | 0.9343 |
| 13 (glm@0.1) | 1326 | 406 | 30.6% | 0.9352 |
| 14 (glm@0.8) | 1125 | 380 | 33.8% | 0.9269 |

**Scenario-računica (argmax bez pojedinih faza):**

| Scenario | Prosjek | Rečenica gubi | Ušteda poziva |
|---|---|---|---|
| A: sve faze | 0.9463 | — | — |
| B: bez 14 | 0.9426 (−0.0037) | 378 | 1.125 (17%) |
| C: bez 13+14 | 0.9340 (−0.0123) | 767 | 2.451 (37%) |

**Ključno:** faze 13 i 14 su jedine glm faze — scenario C uklanja glm potpuno.

**Flaviov metodološki doprinos:** predložio permutacije (11,12,13,14 → 11,12,14,13 → bez 13 → bez 14 → bez oba) i pitao može li se to izračunati bez novih prevoda. Odgovor: **djelomično, i granica nije proizvoljna.** Faze 11-14 su bez seeda, pa prevod ne zavisi od prethodnika — redoslijed mijenja samo koje rečenice uđu kroz gate. Zato se scenariji "bez 14" i "bez 13+14" računaju **tačno** (ništa iza njih ne postoji), dok "bez 13 ali sa 14" i permutacija 14↔13 daju samo donju granicu (faza 14 bi dobila širi ulaz, a za te dodatne rečenice prevod ne postoji).

**Glm prednost nad mistralom** (786 glm pobjeda u opsegu): prosječna prednost nad najboljim mistralom **0.0507** (17× prag šuma sudije), od čega 241 (31%) ubjedljivo (>0.05) i 201 (26%) tijesno (<0.01). Znači glm donosi stvarnu vrijednost, ali na uskom dijelu korpusa (241/3000 = 8%).

---

## Dio 5 — Temperatura: šta je i gdje živi

Flaviovo pitanje: Ollama dozvoljava temperature do 2, a temperatura bi trebala biti atribut modela — radi li Ollama konverziju?

**Odgovor (zvanična dokumentacija + `/api/show`):** temperatura **nije atribut modela**. Model proizvodi logite; temperatura je parametar **samplera** koji ih dijeli prije softmaxa (`p = softmax(logit/T)`). Sampler je dio runtime-a, ne modela — Ollama ne konvertuje ništa, samo prosljeđuje broj.

Posljedice:
- **T=1.0 nije ekstrem** nego nedirnuta distribucija modela. Cijeli dosadašnji raspon (0.1-0.8) je ispod 1.0, dakle uvijek izoštrena distribucija.
- Ollamin globalni default je 0.8 — Flaviova "visoka" temperatura je fabrička postavka.
- Raspon 0-2 dolazi iz OpenAI API konvencije. Zvanična Ollama dokumentacija navodi samo `float` bez gornje granice; `bb_03_prevod.py` koristi native `/api/chat`, gdje tog ograničenja nema.

**`/api/show` za tri modela:** nijedan ne izlaže `parameters` (preporučene sampling vrijednosti). Cloud API vraća samo `capabilities`, `details`, `model_info`, `modified_at`.

| Model | Capabilities |
|---|---|
| mistral-large-3:675b | completion, tools, vision — **nema thinking** |
| gemma4:31b (sudija) | completion, **thinking**, tools, vision |
| glm-5.2 | **thinking**, completion, tools (kontekst 1.000.000) |

**Posljedica za optimizaciju brzine:** mistral nema thinking, dakle na glavnom trošku (prevod) nema šta gasiti. Sudija gemma4 ima, ali je invarijanta projekta — gašenje bi promijenilo ponašanje i učinilo nove ocjene neuporedivim sa 376.000 postojećih pobjednika. Metodološki rez, ne optimizacija.

---

## Dio 6 — Sonda: temperatura vs ponovni poziv (NOVI ALAT)

Flaviov prijedlog: umjesto glm faza, dodati mistral@0.5 i mistral@1.0.

**Napisana namjenska sonda** `src/sandbox_temp_probe.py` (postojeća `sandbox_model_probe.py` mjeri samo 0.1 vs 0.8 i daje binarni "razlika/identično"). Mjeri raznolikost izlaza kroz e5-large kosinus: 5 rečenica × 4 temperature × 3 ponavljanja = 60 mistral poziva (~0.06% sedmičnog budžeta).

**Prvi pokušaj pao na read timeout** — sonda nije imala retry, iako je projekat to već dokumentovao (s159/s160). Dodan retry (3 pokušaja, pauza 30s).

**Rezultat:**

| Temp | Kosinus UNUTAR iste T (3 ponavljanja) |
|---|---|
| 0.1 | 0.9966 |
| 0.5 | 0.9917 |
| 0.8 | 0.9888 |
| 1.0 | 0.9868 |

| Par | Kosinus IZMEĐU temperatura |
|---|---|
| 0.1 vs 0.5 | 0.9954 |
| 0.1 vs 0.8 | 0.9930 |
| 0.1 vs 1.0 | 0.9880 |
| 0.5 vs 0.8 | 0.9944 |
| 0.5 vs 1.0 | 0.9899 |
| 0.8 vs 1.0 | 0.9909 |

**NALAZ:** razlika između 0.8 i 1.0 (0.9909) je **manja** od varijacije unutar same 0.8 (0.9888). Isto za 0.5 vs 0.8 (0.9944) naspram unutar-0.5 (0.9917). Dva poziva na istoj temperaturi razlikuju se više međusobno nego dvije različite temperature.

Mistral **jeste** temp-živ (monotono opadanje), ali je signal ispod šuma — isti nalaz kao s138, sada na drugoj osi. 11/60 parova bilo bukvalno identično (klon-stopa, s135).

**Zaključak:** mistral@0.5 i @1.0 kao nove faze bile bi ekvivalent runda=2 postojećih faza, ne novi kandidati.

---

## Dio 7 — Runda: mehanika razjašnjena kroz kod

Flaviova pitanja: može li faza 51 (mistral@0.1) i 52 (mistral@0.8)? Može li redoslijed 11,12,11,12?

**Provjereno u kodu** (`bb_03_prevod.py:278`): `already_done()` gleda samo `prevodi_knjige_id + recenica_id`, a taj id enkodira knjigu + jezik + fazu + model + temp + prompt + embedder + **rundu**.

1. **Faze 51/52 rade.** Nova faza = novi `prevodi_knjige_id` = `already_done()` prazan. Gate se primjenjuje (faza ≥2).
2. **Redoslijed 11,12,11,12 ne radi ništa.** Prevedene rečenice blokira `already_done()`; preskočene su bile *iznad* praga, a pobjednik može samo rasti, pa su i dalje iznad. Prazan `todo`.
3. **Korekcija Flaviove pretpostavke:** runda **jeste** pod pragom. Gate zavisi samo od `is_refine` (faza ≥2), nezavisno od runde. Runda mijenja `prevodi_knjige_id` pa `already_done()` propušta sve; gate i dalje filtrira.

**Sudija i pobjednik ne znaju za rundu** (`grep` na `runda` u `bb_08_sudija.py`/`bb_04_pobjednik.py` = nula pogodaka), i to je ispravno: sudija ocjenjuje sve neocijenjeno, pobjednik radi argmax preko svih redova. `run_faza.sh` zove pun ciklus (prevod → sudija → pobjednik) pri svakom pozivu, pa svaka runda mjeri prag protiv rezultata prethodne.

**Praktična posljedica:** ponovni poziv mistral@0.8 daje varijaciju 0.9888 — **veću nego prelazak na drugu temperaturu**. Runda daje više novih kandidata nego nova temperatura, bez ijedne nove ose u konfiguraciji.

---

## Dio 8 — `run_kaskada2.sh` (NOVA SKRIPTA)

Napisana na Flaviov zahtjev: nllb root → mistral-only kaskada, dvije runde po fazi, redoslijed **11(r1) → 12(r1) → 11(r2) → 12(r2)**, bez glm faza.

Flavio je primijetio da runda "izgleda kao for petlja" — u kodu nije (samo argument), ali u bash skripti je prirodno napisana kao petlja `for RUNDA in $RUNDE`, čime redoslijed 11,12,11,12 ispada sam od sebe.

Provjere pri upisu: `bash -n` sintaksa, `grep -c` na duplikate, `chmod +x`.

---

## Dio 9 — REZULTAT: kaskada2 vs stara kaskada

Flavio pustio k12 opseg 1401-1500 (100 rečenica × 10 jezika, 5 paralelnih parova).

**Logovi:** svih 5 sa `ZAVR=5`, nula grešaka.

**Gate ulazi i pobjede:**

| Faza / runda | Poziva | Pobjeda | Win-rate |
|---|---|---|---|
| 11 r1 | 886 | 473 | 53.4% |
| 12 r1 | 518 | 173 | 33.4% |
| 11 r2 | 457 | 127 | 27.8% |
| 12 r2 | 426 | 105 | 24.6% |
| root | — | 122 | — |

Runda 2 ukupno: 232 pobjede / 883 poziva = **26.3%** (glm faze su imale 30.6% i 33.8%).

**Kvalitet:**

| Varijanta | Prosjek |
|---|---|
| NOVA 1401-1500 (mistral, 2 runde) | **0.9447** |
| STARA 1101-1200 (mistral+glm) | **0.9449** |

Razlika **0.0002** — 15× ispod praga šuma sudije.

**Kontrola težine teksta** (root/nllb baseline, identičan u obje kaskade):

| Opseg | Root prosjek |
|---|---|
| 1101-1200 (stara) | 0.7102 |
| 1401-1500 (nova) | **0.6733** |

Novi opseg je **teži za 0.037** — nova kaskada postigla isti finalni rezultat polazeći sa lošijeg starta.

**Doprinos runde 2 unutar istog opsega:** 0.9447 sa naspram 0.9380 bez = **+0.0067**, mijenja ishod na 230/1000 rečenica.

**Efikasnost po pozivu (poštena usporedba):**

| | Dobitak | Poziva/rečenica | Dobitak po pozivu |
|---|---|---|---|
| glm 13+14 | +0.0123 | 0.82 | 0.0151 |
| runda 2 | +0.0067 | 0.88 | 0.0076 |

Po pozivu je glm **dvostruko efikasniji** — druga familija daje kandidate koje mistral ne može proizvesti ni na kojoj temperaturi ni u kojoj rundi.

### FLAVIOV PODATAK O POTROŠNJI — ODLUČUJUĆI

- **Stara kaskada:** 6.5% sedmičnih Ollama resursa za 300 rečenica = **2.17% na 100 rečenica**
- **Kaskada2:** **0.7% na 100 rečenica**

**3× manja potrošnja za praktično identičan kvalitet.** Poziv nije jedinica troška — sedmični budžet jeste, a glm poziv košta znatno više od mistral poziva. Time je pitanje efikasnosti-po-pozivu riješeno u korist kaskade2.

Trajanje je duže (kaskada2 sporija), ali potrošnja beznačajna. Flavio potvrdio da ni 5-satni limit nije problem.

---

## Dio 10 — Eksperiment s paralelnošću (2 → 10 procesa)

Flavio pustio po jezik zasebno, opsezi 1501-1600, 1601-1700, 1701-1800.

| Paralelnih | Jezici | Vrijeme | Ollama | Propusnost (jezika/h) |
|---|---|---|---|---|
| 2 | af, nl | 32 min | 0.1% | 3.75 |
| 4 | es, fr, pt, ro | 44 min | 0.2% | 5.45 |
| 4 | bg, bs, mk, sl | 51 min | 0.3% | 4.71 |
| 8 | 8 jezika | 74 min | 0.5% | **6.49** |
| 10 | 10 jezika | 122 min | 0.5% | 4.92 |

**Optimum je oko 8** — na 10 propusnost **pada**, klasična kriva zasićenja.

**Stanje logova:**
- 1501-1600 (2 i 4 paralelna): potpuno čisto, nula retry-eva, nula traceback-ova
- 1601-1700 (8 paralelnih): retry kod es/mk/pt (po jedan), **fr 2 traceback-a**, `nl` pao
- 1701-1800 (10 paralelnih): retry kod pet od osam, svi završili, vremena skoro udvostručena

---

## Dio 11 — Dva kvara, dijagnoza

### nl 1601-1700: OOM Killer

```
./run_kaskada2.sh: line 38: 140635 Killed  venv/bin/python src/bb_03_prevod.py ...
Command exited with non-zero status 137
36.15user 7.18system 3:04.06elapsed 23%CPU (0avgtext+0avgdata 3282828maxresident)k
```

Exit 137 = SIGKILL. Svaki proces drži ~3.2GB (e5-large embedder + NLLB). Deset paralelnih traži preko 30GB — **foxuno ostao bez RAM-a**.

**KLJUČAN NALAZ:** granica paralelnosti je **lokalni RAM, ne Ollama**. Ollama potrošnja bila je beznačajna na svim nivoima (max 0.5%). Flaviov empirijski nalaz "preko 4 je rizično" je tačan, ali razlog nije mrežni.

Isti mehanizam koji je oborio Balsam u martu 2026 (X-Ray Appendix), drugi server.

**Šteta:** nl 1601-1700 potpuno prazan u bazi (nula redova). Čista rupa.

### fr 1601-1700: lanac od tri sloja

**Sloj 1 (spoljni):** sudija pao na `500 Internal Server Error` nakon 3 pokušaja. Rečenice ostale bez ocjene.

**Sloj 2 (naš, latentan):**
```
TypeError: '<' not supported between instances of 'NoneType' and 'float'
bb_03_prevod.py:449:  todo = [x for x in todo if seed_map[x[0]][1] < args.prag]
```

**Prava dijagnoza — ista veličina definisana na dva mjesta različito:**

`bb_04_pobjednik.py` (linije 108-121):
```sql
CASE WHEN sudija_avg IS NOT NULL THEN 0.4*komp + 0.6*sudija ELSE komp END
```

`v_prevodi_full`:
```sql
round(0.4*komp + 0.6*pr.sudija_avg, 4)     -- BEZ CASE
```

View nema `ELSE` granu → NULL aritmetika → `finalni_score` NULL. `bb_04` u istoj situaciji uredno izračuna kompozitni i **izabere pobjednika**. Otud: pobjednik postoji (prvi filter prolazi), ali mu je score NULL (drugi filter puca).

**Šire od jednog TypeError-a:** svaki upit nad `v_prevodi_full.finalni_score` tiho ispušta neocijenjene prevode (`AVG` ih ignoriše, `MAX` preskače). Efekat vjerovatno mali, ali nevidljiv.

**Sloj 3 (naš, od večeras):** `run_faza.sh` **ima** `set -e` (linija 10), ali svaki Python poziv završava sa `| tee -a "$LOG"`. U bash pipeline-u izlazni kod je kod **zadnje** komande — `tee` uvijek uspije. Zato `set -e` nije vidio pad, kaskada je nastavila i ispisala `ZAVRŠENO`.

**Posljedica:** fr ima `ZAVR=5` ali faza 11 runda 2 **nikad nije izvršena** (0 prevoda u bazi). Brojanje `ZAVR` markera nije pouzdan indikator kompletnosti — a upravo je tako korišteno ranije u ovoj sesiji.

**Stanje fr nakon svega:** 100 pobjednika, nula bez ocjene (kasniji sudija poziv popunio). Nije oštećen — samo je propustio jednu fazu, dakle manje pokušaja.

### Uzrok vs okidač (Flaviovo pitanje)

| Sloj | Čije |
|---|---|
| Ollama 500 / OOM Killer | Spoljno, neizbježno |
| View i `bb_04` različito definišu isti score | Naše, latentno od ranije |
| Kaskada ne hvata pad podfaze (`tee` guta kod) | Naše, od večeras |

Spoljni kvar je **otkrio** latentnu nedosljednost, nije je stvorio.

---

## Dio 12 — Popravke (Flaviove odluke)

Flavio donio tri odluke:

1. **Nesklad view/`bb_04` ostaje kako jeste** — promjena view-a dira portal i sve postojeće statistike. Nesklad postaje poznat i dokumentovan umjesto latentan (isti pristup kao s162 bug).
2. **Gate staje umjesto da sam popravlja preduslov.** Flaviov argument protiv spajanja skripti: *"nešto je pogrešno, mi pozovemo skript koji je tu grešku uradio i sa time rješavamo problem. Pa kad i to pukne onda pozivamo nešto drugo treće."* Prednost varijante koja staje: sve skripte rade po pravilu "uradi-ako-nema", pa je ponovni poziv idempotentan — kvar ostavlja sistem u stanju iz kojeg je oporavak jedna komanda umjesto istrage.
3. **`.err` fajl se ne radi.** (Razmatran sentinel obrazac: `.err` → `.ERR` kod greške, plus `KRAJ:` red za razlikovanje prekinutog procesa. Odbačeno.)

### Izmjena 1 — `src/bb_03_prevod.py` (linija 449)

Umjesto `TypeError`, gate ispisuje razlog, pozicije, potvrdu da baza nije dirana i tačnu komandu za oporavak, pa izlazi kodom **3** (razlikuje ga od običnog pada = 1):

```python
bez_ocjene = [x for x in todo if seed_map[x[0]][1] is None]
if bez_ocjene:
    ...
    print(f"  PREKID: {len(bez_ocjene)} pobjednika bez sudijine ocjene (jezik {kod})")
    print(f"    Stanje: nijedan prevod nije napravljen, baza netaknuta.")
    print(f"    Rjesenje: pokreni sudiju za ovaj opseg, pa ponovi ovaj isti poziv:")
    ...
    sys.exit(3)
```

Ključno: prekid nastupa **prije ijednog Ollama poziva** — nula potrošnje.

### Izmjena 2 — `run_faza.sh` (linija 11)

```bash
set -o pipefail   # bez ovoga | tee guta izlazni kod Pythona i set -e ne vidi pad
```

**Testirano izolovano:**
- `bash -c 'set -e; false | tee /dev/null; echo NASTAVILO'` → ispisuje (pogrešno)
- `bash -c 'set -e; set -o pipefail; false | tee /dev/null; echo NASTAVILO'` → ne ispisuje (ispravno)

Obje kaskade (`run_kaskada.sh:5`, `run_kaskada2.sh:11`) imaju `set -e`, pa sada staju kada `run_faza.sh` vrati non-zero.

### Usput razjašnjeno: `--uradi-ako-nema` je dekorativan

Parametar postoji (`run_faza.sh:21` → `bb_03_prevod.py:355`), ali help tekst kaže izričito: *"Label u logu: namjeran nastavak/dovrsavanje raspona (already_done()+prag logika se ne mijenja)"*. Samo ispiše red u log (linija 397). Nema funkciju koja bi pomogla kod ovog problema.

---

## Razgovor o modelu (Sonnet 5 → Opus 5)

Flavio je usred sesije prešao sa Sonnet 5 na Opus 5 i pitao je li projekat postao previše kompleksan za Sonnet, navodeći "neobične preokrete prouzrokovane različitim interpretiranjem činjenica između sesija".

Claudeov odgovor, tri dijela:
1. **Ne može porediti sebe sa sobom** — nema doživljaj prethodnih poruka kao "drugog modela", vidi isti transkript. Podatak da je odmah nakon prelaska priznao grešku slabiji je dokaz nego izgleda: došao je poslije Flaviovog "STANI".
2. **Obrazac nije nov i provjerljiv je:** s125, s135, s136 (protokol se ne primjenjuje pri debagovanju), s148 (isti obrazac, pojačan pod stresom), s143/s147/s151/s158/s159/s161 (memorija zaostala), s155 (tvrdnja provjerena na pogrešnoj funkciji). Mjeseci unazad, kroz razne modele.
3. **Vjerovatan uzrok:** projekat kažnjava odgovaranje iz onoga što *izgleda* kao znanje — 1737 redova README-a, 164 sesije, 26 faza, shema redefinisana tri puta. Kompleksnost povećava **cijenu** te navike, ne njeno postojanje. Preporuka: jači model griješi rjeđe, ali pouzdanije je napraviti da provjera ne zavisi od Claudeove procjene (s161 nalaz: eksplicitan okidač radi, pasivno pravilo u memoriji ne).

---

## Lekcije

1. **Definicija "rupe" iz health checka ne važi za gated faze.** `v_status_faza_model` računa razliku od `MAX` u grupi; gate po dizajnu propušta različit broj rečenica po (model, temp). Prije istrage "rupe" — provjeriti je li faza gated.
2. **"Novo" se provjerava, ne pretpostavlja.** Broj rupa (333) bio je isti u s161/s162/s163.
3. **`NOT IN` s podupitom koji može sadržati NULL tiho vraća prazan rezultat.** Dvaput je zavarao u ovoj sesiji. Koristiti `EXCEPT` ili `NOT EXISTS`.
4. **`| tee` guta izlazni kod — `set -e` bez `pipefail` je iluzija zaštite.** Vrijedi za svaku skriptu u projektu koja koristi taj obrazac.
5. **Brojanje `ZAVRŠENO` markera nije dokaz uspjeha.** Marker se ispisuje bez obzira na ishod podkoraka.
6. **Ista veličina definisana na dva mjesta se prije ili kasnije razilazi.** Prvi korak nije birati bolju definiciju nego ih učiniti identičnim — ili svjesno dokumentovati nesklad.
7. **Granica paralelnosti je RAM po procesu, ne mrežna propusnost.** Svaki proces = embedder + NLLB ≈ 3.2GB.
8. **Temperatura je parametar samplera, ne atribut modela.** T=1.0 je nedirnuta distribucija; sve ispod je izoštravanje.
9. **Sonda bez retry-a na Ollama pozivima je gubljenje vremena** — timeouti su redovni (s159/s160).
10. **Scenario-računica iz postojećih podataka zamjenjuje eksperiment** — ali samo za faze bez seeda, i samo za scenarije koji uklanjaju *zadnje* korake lanca.

---

## Završno stanje

**Korpus:** 50.624 rečenica / 1.959.796 prevoda / 376.532 pobjednika

**Izmijenjeni fajlovi:**
- `src/bb_03_prevod.py` — PREKID zaštita u gate filtru (exit 3)
- `run_faza.sh` — `set -o pipefail`
- `run_kaskada2.sh` — NOVO (mistral-only kaskada, dvije runde)
- `src/sandbox_temp_probe.py` — NOVO (sonda za temperaturnu raznolikost)

**BB_VERSION:** nepromijenjen (web nedirnut).

**Otvorene rupe (za Flavia, prevodi su njegov posao):**
- `nl` 1601-1700 — prazno (OOM), treba ponoviti cijeli opseg
- `fr` 1601-1700 — faza 11 runda 2 nikad izvršena (0 prevoda)

---

## Sljedeći koraci

1. **Kaskada2 kao standardni tok** — 3× manja potrošnja za isti kvalitet je najjači argument koji je projekat dosad imao za promjenu produkcionog toka. Odluka je Flaviova.
2. **Paralelnost: 8 procesa je optimum** (6.49 jezika/h naspram 4.92 na deset). Preko toga RAM postaje ograničenje.
3. **Korak 1 nije instrumentiran** — `run_kaskada*.sh` zove root/sudiju/pobjednika bez `time`, a to je trećina ukupnog vremena. Mjerenje bi pokazalo koliko od toga uzima NLLB, a koliko sudija.
4. **Nesklad view/`bb_04`** ostaje otvoren kao svjesna odluka — vrijedi izmjeriti koliko prevoda u korpusu nema sudijinu ocjenu, da se zna obim.
5. **Ostaje iz s163:** "Treći svijet" (glm@0.1 → uslovno @0.8) — s obzirom na nalaze ove sesije, vrijedi preispitati ima li smisla.

---

*Flavio & Claude · Buchenberg · Sesija 164 · 6. avgust 2026.*
