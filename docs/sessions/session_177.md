# Session 177 — 17. avgust 2026.

**Fokus:** Analiza komada od 80 (poređenje s komadima 50/60), edukativni pregled mehanike sudije i prevodioca (prompt, batch format, pozicija u knjizi), dizajn i implementacija kontrolisane sonde efekta redoslijeda unutar batcha na produkcijskoj skali (kaskada14/15) — negativan nalaz, mešanje odbačeno kao produkciona tehnika.

---

## 1. Analiza komada od 80 (`sandbox_analiza_komadi80.py`)

Nastavak s176 §2-3 (komadi 50 i 60 već analizirani). Novi `sandbox_analiza_komadi80.py` poredi tri kruga na istih 6 produkcijskih jezika (es/fr/nl/bg/mk/sl), parsira kaskada13 logove:

- **Krug 1** — komad 50, 4 radnika, opseg 6001-6400 (48 fajlova)
- **Krug 3** — komad 60, 2 radnika, opseg 6801-7220 (42 fajla)
- **Krug 4** — komad 80, 2 radnika, opseg 7221-7620 (30 fajlova, nova produkcija ove sesije)

Nula fatalnih grešaka u sve tri grupe. Normalizovano po rečenici (elapsed/n), **veći komad je brži na 5/6 jezika** — isti mehanizam kao dužina rečenice (s176): fiksni overhead po pozivu se bolje amortizuje s većim brojem rečenica u pozivu. Root vrijeme po rečenici prati isti obrazac (0.092→0.068→0.057 min/rec). Blok A prazan hod i dalje opada s veličinom (31.9%→27.2%→24.6%), potvrđuje s175 nalaz. Finalni kvalitet (iznad_prag%) stabilan (65.5/65.5/67.8%) — bez degradacije s većim komadom.

**mk je jedini izuzetak** — usporava od komada 60 na 80 (0.722→0.768 min/rec), dok svi ostali jezici ubrzavaju. mk je i jedini jezik koji gotovo uvijek okida blok B (5/5 u krugu 4). Flaviova odluka: zabilježiti kao osobinu jezika, bez dalje analize za sada.

## 2. Edukativni dio — mehanika sudije i prevodioca

Flavio je tražio korak-po-korak provjeru vlastitog razumijevanja pipeline mehanike (svaki korak provjeren u kodu, ne pretpostavljen):

- **Sudija** (`bb_08_sudija.py`): dobija original + SVE neocijenjene kandidate jedne rečenice u JEDNOM pozivu; ocijenjeni kandidati se fizički ne šalju (filter `sudija_avg IS NULL`). Prosjek tri kriterija (grammar/naturalness/fidelity) računa se PO PREVODU, ne za cijelu rečenicu — svaki kandidat dobija svoj `sudija_avg`.
- **Pobjednik** (`bb_04_pobjednik.py`): argmax preko SVIH prevoda rečenice (ocijenjenih i neocijenjenih), ne samo ocijenjenih — neocijenjeni se takmiče slabijom formulom (samo kompozitni, bez sudijskog dijela).
- **Zaštita od neprevedenog teksta**: nema eksplicitne detekcije u kodu. Cosinus je slijep (0.99 za engleski vraćen kao "prevod"), ali sudija to hvata pouzdano preko grammar/naturalness u ciljnom jeziku — arhitekturno neutralisano kroz argmax + sudijinu ~92% težinu, ne posebnom provjerom.
- **Prompt bez seeda** (`base`, iz `bb_promptovi`): batch i single verzija, bez ikakve reference na prethodni pobjednik.
- **Ollama pozivi**: identična struktura za prevodioca i sudiju (isti endpoint, `model`/`messages`/`stream`/`options.temperature`), razlika samo u modelu i temperaturi. Nema `think:false` ni u jednom (samo NER skripte ga koriste).
- **Batch format**: numerisana lista (`1. tekst\n2. tekst...`), model instruisan da vrati isti format. Parsiranje je **pozicijsko** (linija N odgovora = rečenica N na ulazu), ne po ispisanom broju — bitna nijansa za kasniji dio sesije.
- **Model NE vidi poziciju u knjizi** — samo lokalni redni broj 1..N unutar poziva; `recenica_id`/`pozicija` postoje samo na Python strani.

## 3. Kaskada14/15 — kontrolisana sonda redoslijeda (glavna tema sesije)

### Dizajn (Flavio)

Nastavak s176 sonde (`sandbox_redosled_paketa.py`, n=20, p=0.19 neuvjerljivo za kvalitet). Flaviova ideja: testirati na produkcijskoj skali kroz novu kaskadu, baziranu na kaskada13 ali **fiksno izvršavanje** (bez adaptivnog gate-nula izlaska — namjeran izbor za čist eksperimentalni dizajn):

- **Blok A — fiksno 2 kruga**, sve mistral@0.8: krug = faza12-original → faza12-mesano → faza24-original → faza24-mesano (originalni prompt = `refine-strict`). Krug 2 = bazni šum za krug 1 (isti dizajn kao O1/O3, S2/S4 u s176 sondi).
- **Blok B — fiksno 1 krug**, isto ali glm@0.8, okida se pod istim uslovom kao k13 (X=60% default).
- **kaskada15** = identično, ali obrnut redoslijed poziva unutar svakog kruga (mesano prvo, original drugo) — svrha: razdvojiti efekat POZICIJE u nizu od efekta same mešane.

### Implementacija

Nula izmjena šeme — `runda` kolona (postoji od s147) nosi razliku original/mesano/ponavljanje. Prava izmjena je kod:

- `bb_03_prevod.py`: novi `--redoslijed original|mesano` + `--shuffle-seed` (default 42). Mešanje je **pozicijsko unutar chunka** (ne mijenja koje rečenice su zajedno u pozivu), fiksan seed po chunku (baza+indeks) — isti raspored se reprodukuje za ponovljene pozive iste konfiguracije. Rezultat se vraća u kanonski poredak eksplicitno indeksima prije upisa (ne oslanja se na brojeve u modelovom odgovoru — vidi §2). Verifikovano round-trip testom prije puštanja.
- `run_faza.sh`: passthrough oba parametra, isti obrazac kao `--prag` (s167).
- `run_kaskada14.sh` / `run_kaskada15.sh`: novi, izvršni, sintaksno provjereni.

Sve izmjene urađene malim, provjerljivim `str.replace()` koracima (`assert count==1` za svaku), `.bak_pre_redoslijed` napravljen prije dirana oba postojeća fajla.

### Rezultati kaskada14 (parapoc5_*, es+sl, 10 fajlova, k12 7621-8020)

Napisan `sandbox_analiza_kaskada14.py` (nov format loga — `dodala`/`prebacila` po izvršenoj fazi+rundi+redoslijedu). Nula fatalnih grešaka (1 self-recovered timeout). es lako (root 52.6% iznad), sl teško (root 31.2%, blok B 4/5, jedan fajl 110min) — potvrđuje poznatu težinu.

**Sirovi original vs mesano:** original prosj. prebacila=2.417, mesano=1.708 — original naizgled "pobjeđuje". Ali original u kaskadi14 UVIJEK ide prvi u svakom paru.

### Rezultati kaskada15 (parapoc6_*, fr+mk, 10 fajlova, k12 7621-8020)

Isti parser (glob pattern izmijenjen). Nula grešaka. fr umjereno lako, mk teško (root 36.2%, blok B 2/5, jedan fajl 132min).

**Sirovi original vs mesano: PREOKRENUTO** — original=1.182, mesano=3.091, mesano sad "pobjeđuje". Pošto je jedina razlika k14↔k15 redoslijed POZIVA (mesano sad ide prvi), preokret dokazuje da metrika prati **poziciju u nizu**, ne stvarnu original/mesano razliku:

| Slot | k14 (original prvi) | k15 (mesano prvo) |
|---|---|---|
| Krug 1, faza 12, prvi izvršen | original: 5.60 | mesano: 5.70 |
| Krug 1, faza 12, drugi izvršen | mesano: 3.10 | original: 1.90 |
| Krug 1, faza 24, prvi izvršen | original: 3.20 | mesano: 3.70 |
| Krug 1, faza 24, drugi izvršen | mesano: 1.80 | original: 1.40 |

Ko god ide prvi (original ili mesano, svejedno) dobija skoro identičan, veći broj prebačenih preko praga — jer prvi radi na većem preostalom bazenu "ispod praga" kandidata.

### Odluka (Flavio)

Mešanje se NE uvodi u produkciju — hipoteza je pošteno testirana, rezultat jasan (pozicijski efekat, ne stvarna razlika), Flavio je i intuitivno sumnjao u ideju od početka. Kod (`--redoslijed`/`--shuffle-seed`) ostaje u pipeline-u neaktivan po defaultu (`original` = nepromijenjeno ponašanje) kao trag eksperimenta; kaskada14/15 ostaju izvršne ako se ikad požele ponoviti.

## 4. Dokumentacija

README ažuriran (6 izmjena, `README.md.bak_pre_s177` napravljen prije): novi red za `bb_03_prevod.py`/`run_faza.sh` (s177 parametri), novi redovi za `run_kaskada14.sh`/`run_kaskada15.sh` i tri `sandbox_analiza_*` skripte, sekcija "Otvoreno iz s176" zatvorena (stavke 1-3 riješene, stavka 4 — About vizuelni identitet — ostaje otvorena), footer ažuriran (17. avgust, sesija 177). Cijeli fajl provjeren (zaglavlje/tijelo/footer, tabela sekcije 7).

## Stanje na kraju sesije (health check + brza provjera)

Korpus: **50.624** rečenice, **2.154.646** prevoda, **419.832** pobjednika. Ollama sedmično: **10.3%** (+0.4pp), sesija 0.0% (resetovano). Health check nije ponovo pokrenut u punom obliku ove sesije (nema DDL/šema izmjena); brza DB provjera i Ollama snapshot dovoljni za zatvaranje.

## Sljedeća sesija — otvoreno

1. **About vizuelni identitet** (prenosi se iz s176) — kad Flavio dobije skuplju regeneraciju "Geometry of Meaning" u svijetlom modu, uporediti sa jeftinijom; birati konačan referentni stil prije bilo kakve prave implementacije.
2. BPT implementacija i treći-svijet (glm temp split) i dalje čekaju, nepromijenjeno iz s174/s159.
3. Threshold vrijednost po jeziku (mehanizam postoji od s167, vrijednosti nisu određene).
4. "Shuffled kaskada" ideja — sad zatvorena kao produkciona tehnika (§3); ako se ikad ponovo otvori, treba novi ugao (kvalitet na velikom n, ne prebacivanje praga).

---

*Flavio & Claude · Buchenberg · sesija 177 · 17. avgust 2026.*
