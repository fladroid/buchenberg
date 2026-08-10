# Session 169 — Seed se vratio: dvije grane self-refinea, izmjereno

**Datum:** 10. avgust 2026.
**Trajanje:** ~06:00 – 19:00 CEST
**Fokus:** analiza noćnih kaskada5 prolaza → razrješenje s167/s168 neslaganja →
prvo pošteno mjerenje seed naspram bez-seeda → tri nove kaskade (6, 7, 8) →
klon-stopa kao novi pokazatelj → izmjerena degradacija `gemma4:31b`

---

## 1. Snimak zdravlja

**Na početku sesije:** 50.624 rečenice / 2.019.004 prevoda / 396.672 pobjednika.
Korpus je između s168 i s169 prešao **dva miliona prevoda**.

**Na kraju sesije:** 50.624 / **2.027.541** / **399.172**.

Rupe 337 (nepromijenjeno od s168, sve poznate i Flaviovom odlukom ostavljene).
Ollama 18 modela, sva tri projektna odgovaraju. Git `buchenberg` na `fdc380a` (s168).

---

## 2. Šta je urađeno

### 2.1 Analiza 63 noćna loga (kaskada5, k12)

Nova READ-ONLY skripta `src/sandbox_kaskada_logs.py` parsira kaskadne logove
(okolina, parametri, gate po rundi, `real` po bloku, brojači grešaka) u dva TSV-a.

**Nula Tracebackova i nula timeouta u svih 63 loga.** Nekompletna dva, oba očekivano:
`kaskada4_k12_ja_1_100.log` (Flaviov prekinuti prvi pokušaj) i
`kaskada5_k12_af_4601_4700.log` (još trčao u trenutku analize — **ostaje nekompletan,
njegova runda 4 nedostaje u svakoj kasnijoj analizi**).

### 2.2 RAZRIJEŠENO: neslaganje s167/s168 oko japanskog praga

s168 je ostavio otvoreno pitanje zašto sonda mjeri 92,5% ispod praga a pipeline 50%.
Kandidati su bili "različit opseg" i "sonda vs pipeline". **Oba pogrešna.**

Stvarni uzrok: **sonda i gate mjere različite veličine.** Gate radi nad
`finalni_score` (0,4×kompozitni + 0,6×sudija), sonda je računala samo kosinusne
komponente, bez sudije.

Mjereno na k12 4201–4600, root faza, mistral@0,1 (opseg gdje postoje svi jezici):

| osa | ja | raspon ostalih 14 |
|---|---|---|
| `pct_komp` (kosinus) | **98,5%** | 76,0 – 95,8 |
| `pct_final` (gate) | **78,5%** | 43,5 – 76,3 |

Potvrda mehanizma do decimale: gate u logovima za ja 4201–4600 dao je 73/75/83/83,
prosjek **78,5** — identično `pct_final` iz baze.

**Posljedica:** kazna za pismo je stvarna na `ts` (ja `ts`=0,8686, najniži od 15),
ali sudija je apsorbuje (ja `sud`=0,9243, pri samom vrhu). Na osi koja otvara gate
japanski je **vrh kontinuuma**, 2,2 pp iznad slovenačkog — ne zasebna kategorija.
Kaskada na japanskom nije prazan hod.

### 2.3 Prirodni eksperiment: strategija A naspram B (već u bazi)

Otkriveno usput: k12 4201–4600 za **de/hr/it/sr** nema nijednu refine fazu — imali
su pun 3-way root (5 kandidata: mistral 0,1/0,8 + glm 0,1/0,8 + nllb). To je stari
svijet 1, prije izbacivanja glm-a.

| strategija | prevoda/rečenici | glm poziva | prosječan finalni score |
|---|---|---|---|
| A — 5-way root, bez refinea | **5,00** | 40% | hr 0,9390 · sr 0,9376 · de 0,9416 · it 0,9464 |
| B — kaskada5 | **2,34 – 3,87** | **0** | bs 0,9355 · bg 0,9355 · ja 0,9363 · es 0,9452 |

Kontrolni par hr/sr/bs (praktično isti jezik): razlika 0,002–0,004 — **na pragu šuma
sudije (0,003, s146)**. Kaskada5 postiže isti rezultat bez glm-a i uz manje poziva.

### 2.4 Prinos i cijena po rundi (k12 4201–4600)

Pobjednici koje svaka runda **zadrži** (ne koje gate propusti):

| jz | root | r1 | r2 | r3 | r4 |
|---|---|---|---|---|---|
| ja | 140 | 67 | 60 | **69** | **64** |
| sl | 139 | 70 | 59 | 57 | **75** |
| es | 213 | 87 | 43 | 31 | 26 |
| nl | 247 | 54 | 49 | 27 | 23 |

**Refine nosi 40–65% finalnog teksta.** Opadanje prinosa NIJE univerzalno: es/nl
padaju strmo, ja/sl uopšte ne padaju (sl završava rundom 4 kao najjačom).

Minute po osvojenom pobjedniku:

| korak | af | mk | ja | es | nl |
|---|---|---|---|---|---|
| root | 0,25 | 0,37 | 0,20 | 0,18 | 0,24 |
| r1 | 0,40 | 0,70 | 0,43 | 0,40 | 0,40 |
| r4 | 0,63 | 0,80 | 0,59 | **0,82** | **0,82** |

**Root je 2–3× jeftiniji od bilo koje refine runde.** Runde 3+4 troše ~⅓ vremena
za 12–23% pobjednika.

Prosječan skok pobjednika naspram smijenjenog: **0,015–0,066 kroz sve runde i jezike**,
dakle 5–20× iznad poda šuma sudije. **Nijedna runda ne proizvodi lažne pobjede.**

Minute po 0,001 dizanja prosjeka (af/mk opsezi se tačno poklapaju s logovima):
af r1 3,9 → r4 16,1 · mk r1 5,6 → r4 14,1 · ja r1 ~7,2 → r4 ~10,6.
Kod af/mk četvrta runda košta 4× više po jedinici kvaliteta nego prva; kod ja 1,5×.

### 2.5 Raspodjela ocjena — kvintili

Nad 391.344 pobjednika (bez jedinica i NULL-ova):

| grupa | od | do | širina |
|---|---|---|---|
| 1 | 0,3251 | 0,9332 | **0,608** |
| 2 | 0,9332 | 0,9575 | 0,024 |
| 3 | 0,9575 | 0,9716 | 0,014 |
| 4 | 0,9716 | 0,9816 | 0,010 |
| 5 | 0,9816 | 0,9996 | 0,018 |

**Gornje četiri petine stanu u 0,066; prva petina sama proteže 0,608.**
Prag 0,95 pada usred druge grupe — u najgušćem dijelu raspodjele.

Po jeziku (P20 / P60 / max), prag 0,95 pada u:
- **grupu 2** (~20–40% ispod): bg, bs, de, es, fr, hr, it, nl, pt, ro, sr
- **grupu 3** (~40–60% ispod): **af, ja, mk, sl**

Isti broj, dvostruko različit posao — zato su kaskade na sl/mk/af skupe.

**Japanski je stisnut s oba kraja:** min 0,6540 (svi ostali 0,33–0,40),
max 0,9862 (svi ostali 0,993–0,9996). Dva čitanja se ne mogu razlučiti:
sudija slabije razlikuje japanski, ili je japanski korpus mlad i čist
(nikad nije prošao kroz stari par ni NLLB, pa nema repa od smeća).

### 2.6 Savršene ocjene

- **4.524** pobjednika s ocjenom 1,0000 (1,14% od 397.572)
- **0** pobjednika s ocjenom 0,0000 (kosinus praktično nikad ne pada na nulu; s142)
- 1.704 bez ocjene (NULL, rep gdje sudija još nije prošao)
- Tih 4.524 pobjednika raspoređeno je na samo **1.028 različitih rečenica** —
  prosječno 4,4 jezika po rečenici. **Savršena ocjena je osobina rečenice, ne prevoda.**

Po jeziku (%): af 2,91 · nl 2,69 · de 1,77 · hr **1,40** · it 1,31 · sl 0,79 ·
ro 0,78 · pt 0,78 · bs 0,70 · **sr 0,63** · fr 0,55 · es 0,52 · ja 0,14 · bg 0,08 · mk 0,06

**hr 1,40% naspram sr 0,63% — faktor 2,2 na istom jeziku, jedina razlika je pismo.**
Nezavisna potvrda s167 nalaza, drugim instrumentom. Ali pismo nije jedino: vrh su
germanski (blizina engleskom originalu), es/fr su latinica a pri dnu.

### 2.7 Stopa preuzimanja po pojasu seed-ocjene

Isti obrazac u svih 15 jezika, bez izuzetka — **što je seed bolji, to ga refine
rjeđe preotme:**

| pojas seeda | stopa preuzimanja |
|---|---|
| < 0,80 | 55 – 88% |
| 0,80–0,86 | 45 – 68% |
| 0,86–0,92 | 33 – 55% |
| 0,92–0,95 | **27 – 36%** |

**Paradoks obima:** najslabiji pojas nosi najviše prometa (ja 57%, es 49%, sl 36%).
Trošimo najviše poziva tamo gdje najrjeđe dobijamo.

**Nema praga koji se sam nudi** — pad je gladak, bez ijednog skoka. Ako se uzme
pravilo "zadrži pojas dok preuzima ≥40%", pragovi bi bili: **0,92** za bg/es/fr/it/ja/nl/pt/sr,
**0,89** za af/bs/de/hr/mk/ro/sl. NIJE usvojeno — Flavio: prag nije mjera kvaliteta
nego regulator potrošnje, a broj rundi je jača poluga.

### 2.8 SEED — zašto je ispao iz upotrebe i šta se desilo kad se vratio

**Nikad nije donesena odluka da se seed napusti.** Rekonstrukcija:
- **s155**: gated root rješavao je trošak; glm je tamo trebao prevoditi original
  **nezavisno**, kao drugi takmičar — zato je faza 10 namjerno dobila `base` prompt.
- **s163**: registrovano svih 16 kombinacija (11–14 bez seeda, 15–26 sa seedom),
  obje grane testirane. Ali `run_kaskada.sh` je pisan nad grupom bez seeda.
- **s164–s167**: kaskade 2/3/4/5 naslijedile fazu 11/12. Nijedno mjerenje nikad
  nije poredilo seed naspram bez-seeda u kaskadi.

**Prvi test (k12 4201–4600, faza 16 poslije četiri base runde):**

| | pokušaja | klonova | preuzeo | avg skok | min/pobjedniku |
|---|---|---|---|---|---|
| es seed | 147 | **0** | 74 (50,3%) | 0,0332 | **0,16** |
| ja seed | 256 | **0** | 70 (27,3%) | 0,0210 | 0,34 |
| es base r5 (kontrola) | 120 | **10 (8,3%)** | 15 (12,5%) | 0,0208 | **1,35** |

**Peta runda bez seeda daje osam puta skuplju pobjedu.** Čak i s vremenom sudije
izbačenim (bio anomalno spor) ostaje 4,5×. Kontrola je bila zaprljana u korist
seeda (120 naspram 147 rečenica, jer je seed već pročešljao), ali to objašnjava
dio razlike, ne osmostruku.

**Uravnotežen test na k24 (Frankenstein Copy, djevičanski teren):**

| | pokušaja | preuzeo | klonova | ostatak poslije r4 |
|---|---|---|---|---|
| es base (501–700) | 131 | 43 | **29 (22%)** | 25 od 45 (56%) |
| es seed (701–900) | 80 | **43** | **2 (2,5%)** | 10 od 39 (26%) |
| sl seed (501–700) | 326 | 129 (39,6%) | 10 (3,1%) | −42,9% |
| sl base (901–1100) | 308 | 116 (37,7%) | 31 (10,1%) | −28,3% |

**Španski: isti broj preuzimanja (43=43) za 80 pokušaja umjesto 131**, dvostruko
manji rep, i seed runde su bile brže jer se lijevak brže prazni.

**Slovenački: stope preuzimanja praktično jednake (39,6 naspram 37,7), ali skok u
prvoj rundi dvostruk (0,0964 naspram 0,0463).** Seed **ne pobjeđuje češće, nego jače** —
zato prebacuje preko praga i prazni lijevak 43% naspram 28%.

⚠️ Ograda: sl opsezi nisu jednako teški (112 naspram 92 ispod praga poslije roota).
Dio razlike u skoku može biti građa teksta.

### 2.9 KLON-STOPA — novi pokazatelj

Klon = model vratio doslovno tekst koji već postoji među kandidatima.

| | klon-stopa |
|---|---|
| base grana (bez seeda) | **8 – 22%** |
| seed grana | **0 – 3,1%** |

Očekivanje je bilo obrnuto (s137 je mjerio 7,5% klonova u seed grani). **Klonovi su
problem base grane**, gdje seed uopšte nije poslan: nezavisno izvlačenje na temp 0,8
pogađa isti string koji već postoji.

**To nije kvar nego mjerenje — signal da se distribucija modela skupila.**
Prednosti: ne prolazi kroz sudiju, nula cijene, nula subjektivnosti; jedini
pokazatelj koji ne zavisi od instrumenta koji sami zovemo nesavršenim.
Ograde: nije mjera kvaliteta (visoka klon-stopa na dobroj rečenici je dobra vijest,
na lošoj je ćorsokak); zavisi od temperature (na 0,1 bi bio ~100% po konstrukciji).

### 2.10 Tri nove skripte

| skripta | šta radi |
|---|---|
| `run_kaskada6.sh` | kaskada5 sa SEEDOM — faza 16 umjesto 12. Jedina razlika: `uses_seed=True`, batch 20→5 |
| `run_kaskada7.sh` | **Flaviovo pravilo:** nema `BROJ_RUNDI`. Vrti dok prethodna runda prebaci bar jednu preko praga. Mjera iz gate ispisa; `--faza 12\|16`, `--max` samo kao osigurač (20) |
| `run_kaskada8.sh` | **Dvoetapna:** base runde dok ne dođe nula → **prelazak na fazu 16 (seed)** → seed runde dok ne dođe nova nula. Nula parametara za pogoditi |

Logika kaskade8: nula u etapi 1 ne znači da je rečenica gotova, nego da je nezavisno
izvlačenje iscrpljeno (klon-stopa 10–22%). Seed je jedini alat koji modelu kaže šta
već ima. Prelazak se ne procjenjuje — sistem ga sam prijavi nulom.
Pri prelasku se poređenje resetuje (`PRETHODNI=-1`), inače bi prva seed runda bila
odmah proglašena neproduktivnom.

### 2.11 kaskada7 na 11 jezika (k12, opsezi po 100 rečenica)

| rundi | jezici |
|---|---|
| 9 | bs |
| 8 | sl |
| 7 | af, es, ro |
| 6 | fr, nl, pt |
| 5 | mk |
| 4 | bg, ja |

**Medijana 6,5 — fiksne četiri runde bile su PREKRATKE za 8 od 11 jezika.**
Suprotno od pretpostavke s kojom se krenulo (da su preskupe).

**Prinos vaskrsava**, i zato je nula pravi okidač: bs 6·3·**1**·3·2·**4**·2 ·
es 9·1·1·1·**3** · sl 4·**8**·2·3·1·1. Svako pravilo tipa "stani kad prinos padne
ispod 2" odsjeklo bi oporavak. Predložena "runda strpljenja" je **nepotrebna** —
stroga nula je već strpljiva.

Cijena pravila = tačno jedna runda po jeziku (ona koja potvrdi nulu), na repu jeftina.

**mk je jedini stvarni gubitnik**: 5 rundi za 13% ispražnjenog lijevka.

Ispražnjenost lijevka: fr −45% · bs −36% · pt −34% · af −33% · nl −31% · es −27% ·
sl −25% · ja −25% · ro −23% · bg −18% · **mk −13%**

### 2.12 Izmjerena degradacija Ollama Clouda — po MODELU, ne po regionu

Flavio je donio tvrdnju s weba o "teškom usporenju Ollama Clouda u Evropi danas
zbog geografskog rutiranja". Provjera: simptomi (503/502, timeouti, preopterećenje)
su stvarni i **hronično dokumentovani** na GitHubu, ali dva od četiri navedena izvora
su iz **aprila 2026**, a objašnjenje o evropskom rutiranju nema potvrdu nigdje.

**Naš vlastiti instrument je precizniji.** Iz kaskada7 logova, 12:53–16:59 CEST:

| | s/rečenici |
|---|---|
| `mistral-large-3` (prevod) | **4 – 6, bez trenda kroz 5 sati** |
| `gemma4:31b` (sudija) | **0,88 → 14,49** |

Skokovi sudije su **sinhroni među nezavisnim procesima** (13:04–13:05 fr/es/af svi
na 4,7–5,3; 15:10–15:12 nl/bs na 9,7–11,0) — uzrok je na Ollama strani, ne kod nas
i ne u paralelizmu.

**Nalaz: spor je jedan model, dok drugi kroz isti kod u istom trenutku radi normalno.**
Kapacitet po modelu, ne rutiranje po regionu.

**Prvi timeout u seriji** (do tada 63 loga bez ijednog): `kaskada7_k12_sl_5001_5100.log`
runda 4, `api.ollama.com` read timeout 120s, pokriven mehanizmom ponavljanja iz prvog
pokušaja.

---

## 3. Lekcije

### 3.1 Metodološke

- **Prag nije mjera kvaliteta nego regulator potrošnje.** Argmax je jedini kriterij;
  apsolutna vrijednost pobjednikove ocjene ne mijenja ishod. Kazna za pismo je unutar
  jednog jezika konstanta koja se skraćuje iz svakog poređenja. (Flavio, s169)
- **Kad dva mjerenja iste stvari daju suprotne brojeve, prvo provjeri mjere li istu
  veličinu.** s167/s168 neslaganje nije bilo ni opseg ni sonda-vs-pipeline nego
  kosinus-naspram-finalnog-scorea.
- **Zaprljanost je normalno stanje, ne otkriće.** (Flavio) Čista kontrola postoji samo
  na kopiji knjige. Ogradu treba navesti i nastaviti, ne se čuditi.
- **Gate procenat je artefakt praga, ne mjera napretka.** Mjera koja odgovara na
  "isto ili bolje, jeftinije" je pobjednik po rundi i minuta po pobjedniku.

### 3.2 Greške koje se ne ponavljaju (dodaci ledgeru)

- **Procjena obima iz per-log brojeva:** prognozirano da će faza 16 uzeti ~64 (ja) i
  ~26 (es) rečenica; uzela je 256 i 147. Uzrok: brojka iz jednog loga od 100 rečenica
  pomiješana sa zbirom preko opsega od 400. Eksperiment koštao 4× više od najavljenog.
- **`v_pobjednici_full` NEMA kolonu `runda`** — ide preko `prevodi_knjige_id → bb_prevodi_knjige.id`.
- **`bb_promptovi` kolone su `prompt_prevod_single`/`prompt_prevod_batch`/`prompt_back_*`**,
  ne `prevod_single`.
- **foxuno shell je dash:** `<(...)` process substitution obara CIJELU komandu,
  uključujući heredoc prije nje. Poslije takvog pada uvijek provjeriti je li fajl nastao.
- **Zaključak iz zaprljanih podataka:** iz pokvarenog `kaskada5_k24_sl_701_900` prolaza
  izveden zaključak "seed ne pomaže teškim jezicima"; pao s prvim čistim mjerenjem.
  Dupli prolaz je davao lažno dobru sliku base grani (dvostruki pokušaji prazne lijevak brže).
- **Odgovoriti na cijelo pitanje, ne na jednu njegovu polovinu:** pitanje o rečenicama
  s ocjenom 1,0 imalo je dva različita nazivnika (4.524 pobjednika naspram 1.028 rečenica);
  dat prvo samo jedan. Isto kasnije: na "uradi isto po jeziku" isporučen sažetak umjesto
  traženog oblika.

### 3.3 Konceptualne

- **Dva mehanizma, dva režima.** Nezavisno izvlačenje (base) je jako dok ima šta da
  izvuče; kad se distribucija skupi (klonovi), vrti se u prazno. Seed tada dolazi do
  izražaja jer ne uzorkuje nego cilja. Nisu konkurenti nego faze.
- **Nema čarobnog parametra.** (Flavio) Sve što se proba daje mali uspjeh — to je
  potpis sistema u kojem nijedan pojedinačni parametar ne dominira. Da postoji, već
  bi iskočio kao skok umjesto kao pomak u trećoj decimali.
- **Dužina rečenice je drugačija vrsta kandidata od pisma:** hendikep pisma je
  konstanta po jeziku i skraćuje se u argmaxu, a dužina varira UNUTAR jezika — pa
  ako duge rečenice sistematski nose niže ocjene, one se gomilaju u repu i troše sve
  runde. Neizmjereno.

---

## 4. Završno stanje

- Korpus: **50.624 / 2.027.541 / 399.172**
- Nove skripte: `run_kaskada6.sh`, `run_kaskada7.sh`, `run_kaskada8.sh`
- Nove sonde: `src/sandbox_kaskada_logs.py`, `src/sandbox_kaskada_cijena.py` (obje READ-ONLY)
- Web: **nedirnut**, `BB_VERSION` ostaje s168
- Baza: nijedna izmjena šeme

---

## 5. Sljedeći koraci

1. **`run_kaskada8.sh` prvi prolaz** — es, k12, 5101–5200. Ključni broj: koliko je
   etapa 2 prebacila iz onoga što je etapa 1 proglasila neprobojnim. Nula ili jedan
   → ideja pada; pet ili više → stajali smo prerano jer smo pitali pogrešnog radnika.
2. **`refine-strict` (prompt id 4) nikad mjeren u kaskadi.** Formulisan je tačno za
   iscrpljenu distribuciju ("ako ne možeš bolje, napravi značajno DRUGAČIJE").
   Klonovi nisu problem seed grane nego base grane — a base grana nema seed pa ne zna
   šta da izbjegne. Kandidat za treći režim.
3. **Uticaj dužine rečenice na ocjenu** — provjerljivo bez ijednog novog prevoda.
4. **Pragovi po jeziku (0,89/0,92)** izvedeni iz produktivnosti — NISU usvojeni,
   stoje kao mjerenje.
5. **Vrijeme sudije držati odvojeno od vremena prevoda** u svakoj analizi cijene dok
   `gemma4` ne stabilizuje — inače se metodi pripisuje tuđi zastoj.

### Zaprljani podaci koje treba pamtiti

- `kaskada5_k24_sl_701_900` — dva paralelna identična procesa; taj opseg u bazi ima
  dvostruke pokušaje, log neupotrebljiv. Čista zamjena: 901–1100.
- `kaskada5_k12_af_4601_4700` — nekompletan (runda 4 nedostaje).

---

*Flavio & Claude · Buchenberg · sesija 169 · 10. avgust 2026.*
