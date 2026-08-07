# Sesija 165 — 7. avgust 2026.

**Fokus:** adaptivna kaskada koja sama odlučuje kad je gotova; kalibracija parametara iz postojećih podataka; otkriven i popravljen sistemski zastoj sudije na ne-tekstualnim linijama.

---

## 1. Snimak zdravlja (početak sesije)

- Korpus: **50.624 rečenice / 1.969.546 prevoda / 379.832 pobjednika**
- Rupe: 333 (nepromijenjeno od s161)
- Git: oba working tree čista; `buchenberg` na `4b1700c` (s164), `buchenweb` zaostaje na `3c12ca9` (s152, namjerno)
- Ollama: 18 modela dostupno; tri projektna modela odgovaraju
- Kraj sesije: **50.624 / 1.977.665 / 384.032**

---

## 2. Paralelizam — Flaviova stepenasta strategija

**Kontekst.** U s164 je 10 istovremenih procesa izazvalo OOM (nl 1601–1700, exit 137). Flavio je sinoć primijenio drugačiju taktiku: pusti najviše 4 prevoda, sačekaj da NLLB dio završi, pa pusti sljedeća 4.

**Izmjereno iz logova `kaskada2_k12_*_2001_2100.log`** (rekonstrukcija valova: start procesa = kraj − elapsed):

| Val | Jezici | Start | Trajanje NLLB roota |
|---|---|---|---|
| 1 | af, nl | 23:33:23 | 6.7 / 8.7 min |
| 2 | bg, bs, sl, mk | 23:39:37 | 14.0–17.0 min |
| 3 | pt, fr, es, ro | 23:52:45 | 20.4–23.7 min |

- **10 jezika za 74 min = 8.1 jezika/h** — bolje od s164 optimuma (8 paralelnih = 6.49) i mnogo bolje od 10-odjednom (4.92)
- Root se usporava **3.1×** od 2 na 8 istovremenih procesa
- Flavio nije zapravo čekao NLLB: val 2 startovao 26 s prije nego je af-ov root završio; u prozoru 23:52:45–23:56:35 osam procesa je istovremeno bilo u rootu

**Hardver (izmjeren prvi put):** foxuno ima **23 GB RAM, 8 GB swap, 4 jezgra**.

**Analiza uzroka.**
- `maxresident` 5.10–5.37 GB po procesu (ne 3.2 GB kao procijenjeno u s164)
- e5-large na disku 2.2 GB (safetensors → mmap → dijeljene stranice preko page cachea), NLLB ct2 int8 0.6 GB
- Ostatak (~2.5 GB po procesu) je privatna anonimna memorija
- Računica: 8 × 2.5 + 2.8 ≈ 23 GB (na ivici, prošlo); 10 × 2.5 + 2.8 ≈ 28 GB (probilo)
- **Flaviova hipoteza o batch size ODBAČENA:** `NLLB_CT2_BATCH=200` je samo veličina chunka; `max_batch_size=14` je tvrdi limit koji CT2 poštuje iznutra
- **Ono što u Flaviovoj intuiciji ostaje tačno:** root faza jeste najskuplja jer jedina drži oba modela (e5-large + NLLB) i jedina troši lokalni CPU; sve ostalo čeka mrežu. Poluga je bila broj procesa u rootu, ne veličina batcha.

**Tvrd dokaz stigao kasnije u sesiji:** kaskada3 nema NLLB i `maxresident` je pao na **2.92 GB** — razlika od 2.4 GB je tačno NLLB + CT2 baferi.

**Procesna greška (Claude):** predložen `sudo dmesg` iako Claude nema sudo prava. Pravilo: **komande sa sudo piše Claude, izvršava Flavio.** Bez sudo, `dmesg`/`journalctl`/`kern.log` su prazni — OOM event nije potvrđen mjerenjem, ostaje dedukcija.

**Neiskorišteni prijedlozi za ubrzanje (Flaviova primjedba da od Claudea nije došao nijedan):**
1. `intra_threads` u CT2 — ako je default > 1, 4 procesa × N niti na 4 jezgra se međusobno guraju; `intra_threads=1` kod višeprocesnog rada obično daje 20–40%
2. Razdvojiti valove po tipu resursa umjesto po jeziku: root za svih 10 jezika s `-P 4` (CPU-bound), pa Ollama faze za svih 10 odjednom (mrežno-bound)

---

## 3. Flaviova ideja — kaskada koja sama odlučuje kad je gotova

**Originalna formulacija.** Definiši procenat rečenica ispod praga 0.95 koji toleriramo (npr. 15%). Radi mistral runde dok se cilj ne dostigne. Da se ne vrti beskonačno, definiši i maksimalan broj rundi (npr. 3). Ako ni maksimum ne pomogne, pozovi skupi model u jednoj rundi.

**Terminološka ispravka (Flavio).** Ocjena i kvalitet nisu sinonimi. Naš sistem proizvodi **ocjenu**; o kvalitetu ne tvrdimo ništa. „X% ispod praga" nije oznaka kvaliteta nego opis raspodjele naše ocjene. Ako „Baskervilski pasulj" ima ocjenu 2 a „Pas pao s Baskervila" 1, prvi je bolji **jer ima višu ocjenu**, ne jer je bolji prevod.

### 3.1 Kalibracija iz postojećih podataka

**Raspodjela pobjednika ispod praga (k12, svi opsezi — gruba slika):**

| | nl | sr |
|---|---|---|
| ispod 0.95 | 16.3% | 48.0% |
| 0.90–0.95 | 13.0% | 35.4% |
| 0.80–0.90 | 2.3% | 10.5% |
| ispod 0.80 | 1.0% | 2.1% |

Tvrdi pod je samo **1–2%**; ogromna većina ostatka sjedi tik ispod praga. **15% je ispod svega što ijedan jezik trenutno postiže** (najbolji nl 16.3%).

**Varijacija po dijelovima knjige veća od varijacije po tretmanu:** es ide 8.6 → 16.0 → 23.0 → 26.4 kroz prve četiri hiljade rečenica. Tekst postaje teži, metoda ne slabi. Fiksni prag zato tretira različite dijelove knjige kao isti problem.

**Ključni mehanički nalaz:** broj obrađenih rečenica u svakoj gated fazi **jeste** broj rečenica ispod praga u tom trenutku. Kriva opadanja se čita direktno iz logova (`grep -i preskoceno`), bez ijednog novog prevoda.

**Medijane po koracima (10 jezika, k12 2001–2100, kaskada2):**

| korak | medijana ispod praga | pad |
|---|---|---|
| poslije roota (nllb) | 90 | — |
| poslije 11r1 | 45.5 | −44.5 |
| poslije 12r1 | 37.5 | −8 |
| poslije 11r2 | 33.5 | −4 |

Prvi korak nosi devet desetina posla.

**Rani prekid štedi malo:** nl je potrošio 88+27+17+13 = 145 refine poziva; prag 20% bi uštedio 13 poziva = **9%**. Gate već sam čini kasne korake jeftinim; skupi dio je prvi korak koji se izvršava uvijek.

### 3.2 Prag prinosa — kriterij koji zamjenjuje fiksni procenat

**Prinos koraka = rečenica prešlo prag / rečenica obrađeno u tom koraku.**

| jezik | k1 | k2 | k3 | k4 |
|---|---|---|---|---|
| nl | 0.69 | 0.37 | 0.24 | **0.00** |
| bs | 0.53 | 0.35 | 0.08 | 0.08 |
| af | 0.42 | 0.13 | 0.11 | 0.05 |
| mk | 0.43 | 0.04 | 0.08 | 0.09 |
| sl | 0.26 | 0.07 | **0.16** | 0.08 |
| ro | 0.43 | 0.08 | 0.06 | 0.04 |

Prvi korak vraća 0.26–0.69, svi ostali padnu ispod 0.15.

**Simulacija pravila „stani ako je prinos < 0.10":** ukupno poziva pada s **2094 na ~1688 (−19%)**, uz rast rečenica ispod praga za **3.5 procentna poena**.

**Prinos ne opada monotono** — `sl` je pao na 0.07 pa se vratio na 0.16.

### 3.3 Dogovoreni parametri

| par. | vrijednost | uloga |
|---|---|---|
| **r** | 0.10 | prag prinosa — glavni mehanizam; siječe tamo gdje se kriva lomi |
| **N** | 4 | osigurač, ne plan; rijetko dostignut ako r radi |
| **X** | 25% | cilj; rijetko zaustavlja (danas ga dostigli samo es/nl/fr) |
| **tolerancija** | 2 | broj **uzastopnih** promašaja prinosa prije zaustavljanja |

**Redoslijed provjere:** X → r → N (najjeftinije zaustavljanje prvo).

**Tolerancija nije `repeat...until`.** `repeat` rješava *ulaz* u petlju (tijelo se izvrši bar jednom prije prve provjere); kod nas se to pitanje ne postavlja jer prvu rundu ionako uvijek radimo. „Još jedna runda" je pitanje *izlaza* — brojač uzastopnih promašaja koji se **resetuje na nulu** kad prinos poraste. Jedan dobar korak vraća petlji puni kredit. S tolerancijom 2 `sl` bi bio spašen; cijena je otprilike polovina uštede od 19%.

**Ograničenje r:** prinos se računa iz razlike dva gate broja koji nose šum sudije. Ispod ~200 rečenica po pozivu mehanizam mjeri šum koliko i signal. **400 je minimum, 800 pošteno.**

---

## 4. Kaskada3 — mistral root umjesto NLLB

**NOVO: `run_kaskada3.sh`** — mistral@0.1 root (faza 1) → 2× mistral@0.8 (faza 12) → 1× glm@0.8 (faza 14).

Prije pisanja provjereno u bazi da su sve tri kombinacije ožičene (`bb_faze_a1`/`a2`/`a3`, prompt `base`) — direktan poziv `bb_03_prevod.py` validira model/temp protiv kataloga i tiho preskače ako nije aktivno.

**Rezultat (k12, 2101–2200, 10 jezika):**

| korak | kaskada2 (nllb root) | kaskada3 (mistral@0.1 root) |
|---|---|---|
| poslije roota | 90 | **56.5** |
| poslije 1. gated | 45.5 | 49.5 |
| poslije 2. gated | 37.5 | 44.5 |
| pad po koraku | −44.5, −8, −4 | −7, −5 |

Root je mnogo jači, ali refine zato nema odakle da uzme. **Trošak LLM poziva medijano: kaskada2 = 206 (root besplatan, lokalni NLLB), kaskada3 = 250 (svi plaćeni).**

**Kontrolna grupa riješila prividno pogoršanje.** Kaskada3 je gora u 12 od 14 jezika, ali `de`/`hr`/`it`/`sr` **nisu prošli kaskadu3** (išli su punim rootom sa 5 modela, ista metoda na oba opsega) i pogoršali su se **više**: medijana +9.5 naspram +8 kod kaskada3 jezika. **Pogoršanje je od teksta, ne od metode.** Kaskada3 je po ishodu izjednačena s kaskadom2.

**Gdje plaćaš:** +44 Ollama poziva medijano, −2.4 GB RAM, bez CPU kontenzije.

### 4.1 Fer test skupog modela (glm samo na ostatku)

Prvi put je glm radio isključivo na ostatku poslije mistralove konvergencije:

| jezik | pozvano | prešlo prag | prinos |
|---|---|---|---|
| es | 30 | 8 | 0.27 |
| fr | 34 | 8 | 0.24 |
| bs | 46 | 7 | 0.15 |
| mk | 60 | 9 | 0.15 |
| bg | 43 | 6 | 0.14 |
| nl | 30 | 4 | 0.13 |
| sl | 59 | 6 | 0.10 |
| pt | 42 | 3 | 0.07 |
| ro | 58 | 4 | 0.07 |
| af | 49 | 3 | 0.06 |

**Medijana 0.135**, naspram 0.125 i 0.10 za dvije mistral runde prije njega.

**Zaključak: glm na ostatku nije kvalitativno drugačiji od još jedne mistral runde.** Nije model koji vidi ono što mistral ne može — samo još jedan pokušaj, skuplji. **Ne zaslužuje posebno mjesto u mehanizmu; pada pod isto pravilo prinosa kao svaka runda.**

(Napomena: glm je pobijedio 13–27 puta po jeziku, dakle podiže score i kad ne prevede rečenicu preko praga. Da li je to vrijedno zavisi od toga mjeri li se broj iznad praga ili raspodjela u cjelini — Flaviova odluka, nije razriješeno.)

---

## 5. Kaskada4 — mjerni run

**NOVO: `run_kaskada4.sh`** — mistral@0.1 root → **4 runde mistral@0.8, bez ranog izlaza.**

**Obrazloženje dizajna (odgovor na Flaviovo pitanje o 100/200/400/800 i varijantama parametara):** parametre uopšte ne treba testirati prevođenjem. Pun run bez zaustavljanja snima cijelu krivu, i onda se svaka kombinacija X/N/r/tolerancije simulira retroaktivno upitom. Suprotno ne važi: tri runa s tri različita r daju tri odsječene krive i nijednu punu. Na 800 rečenica su sadržani i podskupovi od 200 i 400, pa se i pitanje minimalne veličine odgovara iz istog runa.

Jezici: nl, es (najbolji) + ro, sl (najgori). Opseg 2201–3000.

---

## 6. Zastoj sudije na ne-tekstualnim linijama (glavni nalaz sesije)

### 6.1 Simptom

`kaskada4_k12_es_2201_3000.log` stao s exit 3. Gate iz s164 odradio posao — stao **prije** ijednog Ollama poziva, baza netaknuta.

Uzrok: sudija nije ocijenio pozicije 2299, 2304, 2628. Prevod na tim pozicijama je `*` — separator odjeljka koji je segmentacija propustila u korpus. Cosine daje 1.0 (zvjezdica se savršeno prevodi u zvjezdicu), sudija vraća prazan JSON niz.

Ne-tekstualne linije u opsegu 2201–3000: `*` (2299, 2304, 2628), `* *` (2629, 2890, 2891, 2892). Uz njih `Oh!`, `Ah!`, `No!`, `I.`, `II.` — te sudija ocjenjuje uredno.

### 6.2 Slijepe ulice (dokumentovano da se ne ponavlja)

- **Ponavljanje sudije ne pomaže pouzdano.** nl uspio iz drugog pokušaja (dao 0.000), sl i ro djelimično, **es 0 od devet pokušaja.**
- **Ručni `UPDATE` pet ćelija krpi posljedicu, ne uzrok.** Svaka nova runda pravi **nove** prevode za iste zvjezdice, sudija ih opet ne ocijeni, gate opet stane. Potvrđeno: nl pao na rundi 3, ro na rundi 2, sl na rundi 2.
- **Claudeova greška u tumačenju:** poruka „nije moguće parsirati odgovor: `[]`" ne znači kvar parsiranja — model je vratio **validan JSON, praznu listu**. To je koherentan odgovor „nemam šta ocijeniti". U `sl` logu sudija je čak napisao razlog riječima: ne može ocijeniti jer originalna engleska rečenica nedostaje, označena je zvjezdicom.

### 6.3 Popravka (implementirana)

`src/bb_08_sudija.py` — prije poziva sudiji ubačena provjera:

```python
if not re.search(r'[^\W_]', data["tekst"] or "", re.UNICODE):
    cur.execute("""
        UPDATE bb_prevodi_recenica
        SET sudija_avg = (score + translation_score) / 2
        WHERE id = ANY(%s) AND sudija_avg IS NULL
    """, ([p["prevod_id"] for p in prevodi],))
    conn.commit()
    continue
```

Rečenica koja nema **nijedan** alfanumerički znak ne šalje se sudiji; upisuje joj se kompozitni kao `sudija_avg` — isti fallback koji `bb_04_pobjednik.py` već primjenjuje na NULL sudiju. Uslov je namjerno strog (prazno *nakon* uklanjanja, ne kratko), da `Oh!` i `I.` ne padnu unutra.

Backup: `src/bb_08_sudija.py.bak`.

**Verifikovano:** sve zvjezdice popunjene bez ijednog poziva sudiji; `* *` uhvaćen jednako kao samostalna zvjezdica.

### 6.4 Šta NIJE popravljeno i zašto

- **Prazan odgovor kao nula** — odbačeno. Upisali bismo najgoru ocjenu tamo gdje mjerenja nije bilo. Bolje NULL i vidljiv zastoj nego tiha nula.
- **Sudijin režim „sve nule"** — odbačeno. Nula je *mjerenje* („ne valja"), NULL je *izostanak mjerenja*. Prepisivanje nule kompozitnim oduzelo bi sudiji pravo da presudi protiv cosinea — a to neslaganje je razlog zašto sudija postoji.
- **Nesklad `v_prevodi_full` (bez CASE → NULL) vs `bb_04_pobjednik.py` (CASE ELSE komp)** — i dalje otvoren, od s164.

**Napomena o riziku svake popravke sudije:** korpus od ~1.98 M prevoda ocijenjen je sudijom kakav jeste. Promjena ponašanja prekida uporedivost prije/poslije. Ako se radi, radi se **prije** velikog mjernog runa, ne usred njega.

---

## 7. Sudijin režim „sve nule" — izmjereno

Otkriveno usput: `bb_04_pobjednik.py` ispisuje `sudija=N/A` i za `sudija_avg = 0`, jer je nula u Pythonu falsy. **Greška prikaza, ne podataka.**

Stvarni nalaz: sudija ponekad da 0.00 na sve tri ose na sasvim urednom prevodu. Primjer ro/2340: „Era doar condensarea omului.", kompozitni 0.9636, sudija 0 → final 0.3854.

| mjera | vrijednost |
|---|---|
| prevoda ukupno | 1.975.278 |
| `sudija_avg = 0` | 10.930 (0.55%) |
| nula uz kompozitni > 0.90 | 7.279 (**0.369%**) |
| pobjednika ukupno | 384.032 |
| pobjednik s nulom | 457 |
| pobjednik s nulom uz komp > 0.90 | 440 (**0.115%**) |

**Argmax apsorbuje kvar redundancijom kandidata** — kad jedan kandidat dobije lažnu nulu, drugi preuzme. Zaglavljeno je 0.115% korpusa.

**Posljedica za kalibraciju:** tvrdi pod izmjeren jutros (1–2% ispod 0.80) je **stvarno svojstvo teksta i ocjenjivača, ne artefakt sudije** — artefakt objašnjava tek desetinu toga. Prag i konvergencijski kriterij ostaju upotrebljivi kakvi su postavljeni.

Ovo je failure mode koji se **dokumentuje umjesto da se popravlja**, jer popravka nije potrebna dok postoji drugi put (X-Ray Appendix, „failure modes kao filozofija").

---

## 8. Odbačeno: normalizacija nealfabetskih znakova prije embeddinga

Flavio pročitao preporuku da se prije embeddinga uklone nealfa znakovi i provjerio: `"A B C"` i `"A, B, C"` daju različite vektore.

**Odbačeno, i to je argument protiv normalizacije.** Razlika nije šum nego informacija — interpunkcija mijenja značenje. Prevod koji je izgubio zareze postao bi neodvojiv od onog koji ih je sačuvao, a to je stvarna razlika koju mjerimo. Preporuka dolazi iz pretrage/klasterovanja, gdje je cilj da varijante budu **iste**; kod nas je cilj suprotan.

Za sudiju još jasnije: prva ocjena mu je gramatika, a gramatika je pola interpunkcija.

**Jedino legitimno mjesto:** normalizacija kao **test detekcije**, ne kao obrada ulaza — rečenica koja *nakon* uklanjanja ostane prazna nije tekst. To je tačno popravka iz §6.3.

---

## 9. Self-refine — konvergencija koncepta

Flaviova opaska: od prvog pominjanja self-refinea do danas, kad je praktično sve što koristimo.

**Kako je stiglo dovde — svaki nalaz je oduzimao komponentu, nijedan nije dodavao:**
- diverzifikacija modela otpala (s164 + danas: glm ne vidi ništa što mistral ne vidi)
- temperatura otpala (s164 sonda: razlika između temperatura manja od varijacije unutar iste — nova temperatura nije novi kandidat, **ponovni poziv jeste**)
- NLLB otpao iz rutine (danas izmjereno: 2.4 GB RAM + sva CPU kontenzija za ~12 rečenica preko praga po stotini)

Ostalo je najjednostavnije: isti model, ponovo, svjež pokušaj. Varijacija + selekcija — Flaviova teza iz `ANALIZA.md` (refine kao jedini operator mutacije koji čuva gramatiku), sada s brojevima umjesto intuicije.

**Ako adaptivni mehanizam proradi, otpada i posljednja fiksna stvar — broj rundi.**

### NLLB — mjesto u repertoaru

Flaviov obrazloženi stav: NLLB je prvi njemu poznat MT produkt koji pokriva toliko niskofrekventnih jezika, besplatan i nezahtjevan lokalno. Poštovanje prema onima koji daju produkte za opšte dobro.

**Zadržava se formalno, van standardnog toka.** Vrijednost mu nije u broju pobjeda nego u tome što je jedini model koji radi bez mreže i bez Ollame — ako Ollama padne ili budžet pukne, on je jedino što još prevodi. Isti argument kao rsync backup iz X-Ray Appendixa: nije bio pametniji, bio je izolovan.

Kontekst za pravednu ocjenu: danas mjeren na en→zapadnoevropski, na Moby Dicku, u društvu modela od 675 B parametara — najnepovoljniji mogući teren. Tri reda veličine manje parametara za jedan red veličine manji doprinos.

**Podsjetnik za buduće (Flaviova ideja o kaskadi bez ijednog LLM-a):** NLLB s različitim temperaturama **neće raditi** — CT2 kod nas radi deterministički (beam search), zato je NLLB uvijek na 0.0. Za varijaciju treba eksplicitno uključiti sampling (izmjena koda). **Bolja alternativa: uzeti više hipoteza iz beam searcha odjednom** — nekoliko kandidata iz jednog poziva, bez ikakve slučajnosti. Za GA okvir čistije od temperature.

Više od 50% korpusa napravljeno je NLLB-om i malim modelima (gemma3:12b, ministral-3:14b). Mistral i glm su u korpusu manjina.

---

## 10. Šta je promijenjeno

**Kod:**
- `run_kaskada3.sh` (novo)
- `run_kaskada4.sh` (novo)
- `src/bb_08_sudija.py` — preskakanje ne-tekstualnih linija (backup `.bak`)

**Baza:**
- `UPDATE` 5 ćelija `sudija_avg` (es ×3, ro ×2, pozicije 2299/2304/2628) — ručna popravka prije nego je skript popravljen
- `bb_08_sudija.py` popunio zvjezdice za nl/ro/sl automatski
- `bb_04_pobjednik.py` ponovo pokrenut za es/ro pa za nl/ro/sl na 2201–3000

**Web:** ništa. `buchenweb` i dalje na s152.

---

## 11. Lekcije

1. **Log nosi krivu prinosa besplatno.** `grep -i preskoceno` daje broj rečenica ispod praga na ulazu u svaki gated korak. Nema potrebe za novim prevodima da bi se kalibrisao mehanizam.
2. **Kontrolna grupa je uvijek negdje u podacima.** Jezici koji nisu prošli novi tretman, a jesu isti opseg, razdvajaju efekat metode od efekta teksta. Bez njih bi kaskada3 bila proglašena lošijom.
3. **Krpiti posljedicu koja se reprodukuje pri svakom prolazu je gubljenje vremena.** Ručni UPDATE je tri puta pao na istom mjestu. Flaviova primjedba („ili prepravljamo sudiju ili ne radimo više") bila je tačna i trebala je doći od Claudea.
4. **Prazan JSON niz nije greška parsiranja.** Poruka u kodu obmanjuje. Model koji vrati `[]` je odgovorio koherentno.
5. **Nula i NULL nisu ista stvar.** Nula je mjerenje, NULL izostanak mjerenja. Samo drugo se smije prepisati kompozitnim.
6. **Ocjena ≠ kvalitet.** Formulacija se mora držati u svim analizama.
7. **Sudo komande piše Claude, izvršava Flavio.** Prekršeno u ovoj sesiji.
8. **Simulacija nad punim runom > više odsječenih runova.** Pun run bez zaustavljanja sadrži sve varijante parametara; odsječeni runovi ne sadrže jedni druge.

---

## 12. Otvoreno / sljedeći koraci

- **Kaskada4 nije završena** — es je još trčao na kraju sesije; nl/ro/sl treba ponovo pustiti (kreću od runde na kojoj su stali). Za es poslije završetka: `bb_08_sudija.py` pa `bb_04_pobjednik.py` na 2201–3000, tek onda nastavak.
- **Implementacija adaptivne petlje** (X=25%, N=4, r=0.10, tolerancija=2) — parametri dogovoreni, kod nije pisan
- **Simulacija parametara nad kaskada4 podacima** kad run završi
- `intra_threads` u CT2 — neprovjeren prijedlog za ubrzanje
- Razdvajanje valova po tipu resursa (CPU-bound root `-P 4` + mrežne faze `-P 10`)
- Nesklad `v_prevodi_full` vs `bb_04_pobjednik.py` oko NULL sudije — otvoren od s164
- `bb_04_pobjednik.py` prikazuje `N/A` za nulu (falsy bug u ispisu) — kozmetika
- Ne-tekstualne linije u korpusu (`*`, `* *`, `I.`, `II.`) — sada zaobiđene, ali i dalje u korpusu; brisanje je otvorena opcija
- Bug iz s162 (gated-bez-seeda tiho preskače rečenice bez pobjednika) — Flaviova odluka: ostaje
- Rupe nl/fr 1601–1700 iz s164
- NER web export + `nlp.html` (idu zajedno)
- Sinhronizacija dokumenata i weba prije novih eksperimenata (Flaviov redoslijed)
- Kaskada bez ijednog LLM-a (NLLB + mali modeli) — poslije sinhronizacije

---

*Flavio & Claude · Buchenberg · sesija 165 · 7. avgust 2026.*
