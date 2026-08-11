# Sesija 170 — 11. avgust 2026.

**Fokus:** Analiza prvih kaskada8 prolaza → potvrda oporavka `gemma4` → sonda o
ponavljanju u batchu → **kaskada9**: treća etapa (`refine-strict`) sa zaustavljanjem
po prirastu zbira ocjena. Usput popravljen nesklad `v_prevodi_full` naspram `bb_04`
koji je stajao otvoren od s164.

**Flaviova okvirna formulacija (nosi sesiju):** prag i ostali parametri nisu dio
koncepta nego **kočnice zbog novca i vremena**. Vizija je neprekidan proces
poboljšanja: procesi koji idu od knjige do knjige, od rečenice do rečenice, i
gledaju može li se nešto uraditi bolje. Rečenica smije biti prevedena proizvoljno
mnogo puta po proizvoljno mnogo kriterija; **minimalni zahtjev je da u svakom
trenutku ima tačno jednog pobjednika.** Kaskada8 je "back to root" — gotovo čist
self-refine s dvije kočnice.

---

## 1. Snimak zdravlja

| Mjera | Početak | Kraj |
|---|---|---|
| Rečenice | 50.624 | 50.624 |
| Prevodi | 2.034.591 | 2.034.595 |
| Pobjednici | 400.172 | 400.172 |
| Rupe | 345 | 345 |

Korpus je prešao **400 hiljada pobjednika**. Rast u sesiji (+4 prevoda) je isključivo
od smoke testa faze 24. Rupe 345 naspram 337 na kraju s169 — svih 8 novih je k24
(`es` i `sl`, po 4 reda), mehanički potpis kaskade5/6 koja vozi samo mistral@0.1 root,
isti obrazac imenovan u s168.

Git na početku: `buchenberg` `d4d4870` (s169), `buchenweb` `c22a4ce` (s168).

---

## 2. Analiza 11 kaskada8 prolaza (k12, Flaviovi noćni runovi)

Nula Tracebackova, jedan read-timeout (mk, pokriven retryjem).

### 2.1 `gemma4` se vratio u normalu — datirano do minute

Sekunde po pozivu sudiji, tri **nezavisna** procesa:

| vrijeme (UTC) | proces | s/poziv |
|---|---|---|
| 16:43–16:54 | es r8/r9, fr r2, af r1 | 12.3 – 14.9 |
| **17:07** | af r2 | **3.53** |
| **17:09** | fr r4 | **1.87** |
| **17:14** | es r12 | **1.21** |
| 17:14 → 22:41 | svih 127 preostalih blokova | 0.69 – 4.27 |

Prelom **17:05–17:14 UTC (19:05–19:14 CEST)**, **sinhron preko procesa koji ne znaju
jedan za drugog**. Medijana prije ~10.5, poslije ~1.4 → faktor **~8×**.
Kontrola: `mistral-large-3` drži **4–10 s/rečenici bez prekida** kroz cijeli prozor,
uključujući trenutak preloma. **Drugi put, drugim materijalom: kapacitet je po
modelu, ne po regionu ni po infrastrukturi** (potvrda s169 §2.12).

### 2.2 Kaskada8 — etapa 2 nosi 16–44% teksta

| jz | e1/e2 rundi | gate@prelazak | faza 16 pobjeda | % ostatka | prešao 0.95 | prosj. skok |
|---|---|---|---|---|---|---|
| ja | 9/5 | 58 | 43 | 74% | 16 | 0.021 |
| mk | 6/7 | 61 | 43 | 70% | 13 | 0.036 |
| sl | 4/5 | 72 | 44 | 61% | 6 | 0.044 |
| ro | 5/5 | 59 | 35 | 59% | 13 | 0.023 |
| af | 6/3 | 37 | 22 | 59% | 5 | 0.046 |
| pt | 7/5 | 33 | 21 | 64% | 11 | 0.042 |
| bg | 7/3 | 48 | 23 | 48% | 6 | 0.034 |
| es | 8/8 | 32 | 18 | 56% | 9 | 0.025 |
| fr | 9/4 | 27 | 17 | 63% | 7 | 0.033 |
| nl | 15/3 | 40 | 19 | 48% | **1** | 0.038 |
| bs | 7/2 | 34 | 16 | 47% | **1** | 0.038 |

**KLJUČNA NIJANSA:** bs i nl su po gateu izgledali kao promašaj (0 i +1 prelazak), a
dali su seedu 16 odnosno 19 pobjednika. **Seed diže ostatak, ali ga često ne prebaci
preko 0.95** — rep je strukturno ispod praga, ne slučajno. Mjereno gateom, ideja bi
bila odbačena na dva jezika na kojima radi. Potvrda s169 pravila: *gate procenat je
artefakt praga, ne mjera napretka.*

### 2.3 Klon-stopa

| grana | raspon | medijana |
|---|---|---|
| faza 12 (base) | 13 – **42%** | 25% |
| faza 16 (seed) | 2.9 – 16.9% | 11% |

Smjer isti kao s169, brojevi viši u obje grane jer kaskada8 vrti do stroge nule.
**nl je udžbenički slučaj: 15 base rundi, 757 pokušaja, 303 klona (40%)** — etapa 1
je posljednjih sedam-osam rundi mlatila praznu slamu dok je gate i dalje davao po
1–3 prelaska.

### 2.4 Nepreciznost u pravilu prelaska (dokumentovano, neispravljeno)

Runda proglašena nultom i dalje daje prinos, jer se njen efekat vidi tek u sljedećem
gate-u (af r6 dao 2, es r8 dao 1). Prelazak okida **jednu rundu ranije** nego što se
iz loga čini. Bezopasno, ali obavezno pri čitanju logova.

---

## 3. Sonda: ponavljanje rečenice unutar batcha

**Flaviovo pitanje (pozadina: može li se skratiti vrijeme i povećati raznolikost):**
ako u batch od 20 stavimo 5 rečenica ponovljenih 4 puta, dobijamo li 4 klona ili 4
različita prevoda?

Nova READ-ONLY sonda `src/sandbox_batch_ponavljanje.py`. k22 1500–1504, mistral@0.8,
prompt `base`, hr i de, 30 parova po ćeliji.

| rukavac | hr različitih/4 | hr klon-stopa | de različitih/4 | de klon-stopa |
|---|---|---|---|---|
| A1 jedan poziv, prepleteno | **1.00** | **100%** | **1.00** | **100%** |
| A2 jedan poziv, blokovi | **1.00** | **100%** | **1.00** | **100%** |
| B 4 poziva, batch=5 | 3.00 | 23.3% | 2.20 | 46.7% |
| C 4 poziva, batch=20 | 2.60 | 36.7% | 2.20 | 36.7% |

**Odgovor: 4 klona. 60/60 parova, oba jezika, oba rasporeda.**

Mehanizam: dvije sile vuku suprotno — kopiranje iz vlastitog konteksta (batch je
JEDAN autoregresivni tok) naspram Ollaminog `repeat_penalty` (~1.1, prozor 64 tokena).
**Kopiranje pobjeđuje ubjedljivo.** U A1 je ponavljanje stotinama tokena unazad pa ga
kazna ne vidi; u A2 je susjedno, dakle u prozoru, i **svejedno 100% klonova**.

### Tri nalaza vrednija od samog odgovora

1. **Batch je JEDNA odluka, ne 20 nezavisnih.** "Nezavisno izvlačenje" iz s169 je
   nezavisno **preko poziva**, ne unutar poziva.
2. **Sastav batcha mijenja prevod.** A1, A2 i B/C dali su tri različita teksta iste
   rečenice (`Dvoje… naviknu ići` / `Dvoje… se naviknu putovati` / `Dva… smetaju putu`).
   **Neregistrovan parametar iste klase kao prompt u s139.**
3. **Cijena 4× za jedan kandidat**, a šema ionako ne bi primila rezultat:
   `UNIQUE (prevodi_knjige_id, recenica_id)` — četiri kandidata iz istog poziva
   trebala bi četiri `runda` vrijednosti, dakle četiri poziva.

**Zaključak: ne pomaže ni vremenu ni raznolikosti.** Poluga za N kandidata po rečenici
je `runda` (ponovljeni poziv), koja postoji od s147.

**Indicija usput (neizmjereno namjerno):** faza 12 vozi batch 20, faza 16 batch 5 —
četiri puta više poziva, a **isto vrijeme po rečenici** (sl 5.3–5.6 naspram 4.6–5.1).
Trošak vjerovatno prati broj generisanih tokena, ne broj poziva. Konfaund: faza 16
nosi seed u promptu. Flavio odlučio da se u tom pravcu za sada ne mjeri.

---

## 4. `v_prevodi_full` — NULL se više ne propagira (nesklad iz s164 zatvoren)

### Nalaz

`finalni_score` nije kolona nego izraz u viewu; `0.4×komp + 0.6×sudija_avg` je NULL
kad sudija nije prošao. Isti NULL se u sistemu tumačio na **četiri načina**:

| gdje | ponašanje |
|---|---|
| šema | dozvoljava (sudija upisuje UPDATE-om, kasnije od `bb_03`) |
| `bb_04_pobjednik.py` | tolerише — `CASE ... ELSE kompozitni` |
| `v_prevodi_full` | propagira NULL |
| gate u `bb_03` | odbija nastavak, `sys.exit(3)` |

### Flaviov argument

NULL se zamjenjuje **adekvatnom vrijednošću** — sintaksno i semantički. Vrijednost
0.0 je odbačena: **zauzeta je.** U koloni stoji **11.095 stvarnih nula**, od toga
7.402 uz kompozitni > 0.90 — sudija koji je pogledao i rekao "ne valja".
Upis 0.0 tamo gdje sudija nije prošao spojio bi mjerenje i izostanak mjerenja
**nepovratno** (s165 razlika), i proizveo lažnu presudu u jedinoj koloni proglašenoj
dogmom. Adekvatna vrijednost je ona koju `bb_04` **već koristi**: kompozitni.

### Izvedeno

```sql
-- samo izraz finalni_score, ostalo netaknuto; rezerva /tmp/v_prevodi_full.bak_s170.sql
round(CASE WHEN pr.sudija_avg IS NOT NULL
           THEN 0.4*((pr.score+pr.translation_score)/2) + 0.6*pr.sudija_avg
           ELSE (pr.score+pr.translation_score)/2
      END::numeric, 4) AS finalni_score
```

Provjereno prije izmjene: `score`/`translation_score` **nikad nisu NULL** (0 na 2.03M),
pa `ELSE` uvijek daje broj. Jedini produkcijski potrošač je **`bb_03_prevod.py:313`**
(`get_seed_map`) — dakle baš gate; `bb_04`, `bb_web_export`, `bb_xray_export`,
`health_check` ne čitaju view.

| | prije | poslije |
|---|---|---|
| redova s NULL `finalni_score` | 8.660 | **0** |
| pobjednika bez ocjene | 1.704 | **0** |

**Nijedan red u bazi nije dirnut.** Posljedice: grana `PREKID … exit(3)` u `bb_03`
(linije 436–446) je postala **mrtav kod**; poređenja s brojevima iz starijih sesija
nose zvjezdicu, jer 8.660 redova sada ulazi u `SUM`/`AVG` umjesto da ispada.

**Materijalizacija u bazi odgođena** (Flaviova odluka). Kad se radi: nova kolona
`finalni_score` na `bb_prevodi_recenica` po istom `CASE`, a `sudija_avg` netaknut.

---

## 5. Obje mjere u svim petljama

Flaviov zahtjev: sve petlje prikazuju i prirast rečenica iznad praga **i** prirast
zbira ocjena, bez obzira koju vrijednost koriste.

**Podjela odgovornosti: skripta prijavljuje STANJE, omotač prijavljuje PROMJENU.**

- **`bb_04_pobjednik.py`** — novi `--prag` (samo za ispis, ne dira izbor pobjednika)
  i red `BILANS jezika: n= zbir= prosjek= ispod X:`. Računa se iz već učitane liste
  pobjednika — **nula dodatnih upita.** Time ga dobijaju sve putanje odjednom:
  kaskade 5/6/7/8/9, `run_faza.sh`, `run_root_gated.sh`, ručni pozivi.
- **`run_kaskada7.sh` / `run_kaskada8.sh`** — red `ZBIR …` s tri normalizacije
  (sirovo, % od `n`, % rezerve). Postojeća `BILANS` linija **nije dirnuta nijednim
  znakom**, da `sandbox_kaskada_logs.py` nastavi raditi.

**Dvije odluke u dizajnu:**

1. **Gate i zbir mjere različite trenutke.** `GATE` dolazi iz `Refine:` linije koju
   `bb_03` ispiše **prije** prevoda (zato "prethodna runda prebacila"); `BILANS`
   nastaje **poslije**. Zbir nema kašnjenje od jedne runde — izvještava o rundi koja
   je upravo prošla. Zato je u logu izričito označeno `(POSLIJE runde)`.
2. **Zbir se pri prelasku NE resetuje** (za razliku od `PRETHODNI`), jer je delta na
   prelasku upravo najzanimljivija (+0.20 do +1.22 na svih 11 jezika).

**Uhvaćena greška u toku:** prvi raspored je stavio ZBIR blok iza grananja, pa bi
`continue` na prelasku i `break` na kraju preskočili **baš dvije najzanimljivije
runde**, a `ZBIR_PRETHODNI` bi ostao ustajao. Premješteno odmah iza čitanja `GATE`,
prije ijedne grane.

**Test** (k22/ja 1010–1029, već odrađen opseg, `--max 1`, nula Ollama prevoda):
ispis radi, delta +0.0000 tačna. Provjera protiv baze: `n`, `prosjek`, `ispod`
identični; zbir 19.1324 naspram 19.1325 — **redoslijed zaokruživanja**, ne greška
(`bb_04` sabira nezaokruženo pa formatira, view zaokruži svaki red pa sabira).

**Usput otkriveno:** pri ponovljenom prolazu `GATE` i `BILANS` se legitimno razilaze —
`already_done()` skine već odrađeno pa gate vidi samo ostatak. `GATE` odgovara na
"koliko posla preostaje u ovoj konfiguraciji", `BILANS` na "kakvo je stanje opsega".
**Isto se dešava pri oporavku poslije pada: gate potcjenjuje, zbir ne.** Argument više
za zbir kao mjeru.

---

## 6. Kaskada9 — izvod za `x` i implementacija

### 6.1 Analiza nad postojećim podacima (nula novih prevoda)

Rekonstruisana kriva zbira za svih 11 kaskada8 prolaza, **133 runde**.

**Dvije klase rundi su čisto razdvojene:**

| klasa | raspon Δ (% od n) |
|---|---|
| prva runda novog mehanizma (22 slučaja) | +0.195 … +3.238 |
| završna runda iscrpljenog mehanizma (11) | +0.000 … +0.143 |

Između 0.143 i 0.195 **nema nijedne runde**. Posljedica: treća petlja će se uvijek
izvršiti bar jednom — ne zato što je forsiramo, nego zato što se odluka donosi
**poslije** runde, kad delta uopšte postoji.

**Cijena x** (vaskrsavanje brojano **unutar iste etape**, jer se pravilo na prelasku
resetuje):

| x (% od n) | rundi radi | ušteđeno | vaskrsenja | gubitak |
|---|---|---|---|---|
| 0.02 | 120 | 13 | 9 | 1.7% |
| 0.05 | 99 | 34 | 13 | 4.7% |
| **0.10** | **81** | **52** | **5** | **7.3%** |
| 0.15 | 72 | 61 | 5 | 9.7% |
| 0.20 | 67 | 66 | 4 | 11.1% |
| 0.50 | 44 | 89 | 1 | 21.0% |

**x = 0.10% od n je prelomna tačka** — do nje vaskrsenja padaju (13→9→5), poslije nje
prestaju da padaju a gubitak raste. Ušteda 39% rundi za 7.3% prirasta.
**Na 100 rečenica to je 0.10 boda po rundi, ne 1.**

**Vaskrsavanje postoji i u zbiru, ali je pitomije nego u gateu.** Unutar etape 2 delte
su gotovo uredno opadajuće (`ja +0.52 +0.27 +0.06 +0.03 +0.02`); jedini pravi izuzetak
je **ro: +0.28 pa +0.41**. Prag na zbiru je sigurniji od praga na prinosu odbačenog u
s169, ali nije neprobojan.

**Rezerva kao normalizacija ne pomaže** — isti poredak, ista odluka, a traži
pretpostavku o dostižnom plafonu koji ne znamo (ja max u korpusu 0.9862, ne 1.0).
Ostaje jednostavnije: postotak od `n`.

⚠️ **Ograda:** `refine-strict` nikad nije pokrenut. Ovo je izvod iz ponašanja *drugih*
mehanizama na istom materijalu — red veličine i granice, ne izmjerena vrijednost.

### 6.2 `run_kaskada9.sh` (novo, 149 linija)

Kopija kaskade8 s trećom etapom:

| etapa | faza | prompt | pravilo zaustavljanja |
|---|---|---|---|
| 1 | 12 | base, bez seeda | gate-nula |
| 2 | 16 | refine, sa seedom | gate-nula |
| **3** | **24** | **refine-strict, sa seedom** | **prirast zbira < `--prirast`** |

Novi parametar `--prirast` (default **0.10** % od `n`), po obrascu `--prag`.
**Nula izmjena baze:** faza 24 (`refine-strict-mistral-08`) registrovana još u s163;
`bb_aktivni_modeli.py --faza 24` vraća `mistral-large-3:675b|0.8000` kroz katalog-
fallback iz s145, `bb_faza_info.py` vraća `2|self-refine|f`.

**Greška uhvaćena guardom:** slijepa zamjena `%%` → `%` je pala na `assert count==4`
(bilo ih je 7) jer `%%` legitimno stoji i u `awk printf` stringovima. Zamijenjeno po
sidrima, samo u `echo` linijama.

### 6.3 Smoke test faze 24 — prvo izvršavanje ikad

k22/ja 1010–1029, izolovano od kaskade, 29 sekundi:

| | prije | poslije |
|---|---|---|
| zbir | 19.1324 | **19.2619** |
| prosjek | 0.9566 | **0.9631** |
| ispod 0.95 | 4 | **1** |

`Refine: 20 sa seedom -> 20; ispod praga 0.95: 4 (preskoceno 16)` — **3 od 4 prebačene
preko praga**, nula grešaka. Potvrđeni odjednom: novi prompt, seed grana, batch 5,
katalog-fallback u produkcijskom lancu.

⚠️ **Δ = +0.65% od n, daleko iznad defaulta 0.10 — ali to NE potvrđuje ni obara x.**
Taj opseg nikad nije prošao fazu 16, pa je `refine-strict` ovdje bio **prvi mehanizam
sa seedom**, dakle klasa "prva runda novog mehanizma" (0.195–3.238%), ne ono što treća
petlja stvarno dočeka. Uz to n=4 rečenice. **Pravi x izlazi tek iz punog prolaza
kaskade9.**

---

## 7. Lekcije

1. **Kad dvije mjere daju suprotan sud, provjeri mjere li istu stvar u istom
   trenutku.** Gate mjeri prije runde i samo prelaske praga; zbir mjeri poslije runde
   i sve pomake. bs i nl su po prvoj mjeri promašaj, po drugoj 16 i 19 pobjednika.
2. **Zamjenska vrijednost za NULL mora biti semantički slobodna.** 0.0 nije bila —
   11.095 stvarnih nula je već zauzelo tu vrijednost. Adekvatna je bila ona koju je
   drugi dio sistema već izabrao.
3. **Guard u `str.replace` je uhvatio grešku koju bih inače unio** (`%%` u `awk`).
   `assert count == N` nije formalnost.
4. **Provjeri redoslijed grana prije testa, ne poslije.** ZBIR blok iza `continue`/
   `break` bi tiho preskočio baš najvažnije runde.
5. **Claude je dvaput iznio netačnu tvrdnju o infrastrukturi** ("bash ne može do
   baze"). `ssh balsam.dynu.net 'docker exec pgdb psql …'` radi bez lozinke s foxuno.
   Pravilo iz s167 (*pročitaj prije nego tvrdiš*) važi i za okruženje, ne samo za kod.
6. **Flaviove brojeve u konceptualnoj raspravi čitati kao ILUSTRACIJU, ne prijedlog.**
   "1%" i "0" su bili primjeri principa; tretirani kao vrijednosti, odveli su u dvije
   nepotrebne rasprave.

---

## 8. Završno stanje

**Izmijenjeno:**
- `src/bb_04_pobjednik.py` — `--prag` (ispis) + `BILANS jezika` red
- `run_kaskada7.sh`, `run_kaskada8.sh` — `ZBIR` red, tri normalizacije
- `run_kaskada9.sh` — **novo**
- `src/sandbox_batch_ponavljanje.py` — **novo**, READ-ONLY sonda
- baza: `v_prevodi_full` redefinisan (`CASE` umjesto propagacije NULL); **nijedan red
  podataka nije dirnut**

**Rezerve:** `/tmp/v_prevodi_full.bak_s170.sql`, `*.bak_s170` uz svaku izmijenjenu skriptu.

**Web:** NEDIRNUT, `BB_VERSION` ostaje **s168**.

**Prevedeno u sesiji:** k22/ja 1010–1029 faza 24 (4 rečenice) + smoke testovi bez upisa.

---

## 9. Otvoreno / sljedeći koraci

1. **Prvi pun prolaz `run_kaskada9.sh`** — jedini način da se `x` potvrdi. Ključni broj:
   delte etape 3 kad je zatekne teren koji su base i seed već pročešljali.
2. **Mrtav kod:** grana `PREKID / exit(3)` u `bb_03_prevod.py` (linije 436–446).
3. **Kaskade 5 i 6 ne prosljeđuju `--prag` svom `bb_04` pozivu** — `BILANS` bi im
   uvijek brojao po 0.95. Kozmetika dok se ne vozi drugi prag.
4. **Materijalizacija `finalni_score`** kao kolone (Flavio: za kasnije).
5. **Evolucija pobjednika u X-Rayu** — fazni trag postoji (`bb_prev_recenica_faza` +
   `created_at`); istorija **apsolutnog** pobjednika ne postoji, samo tekući pokazivač.
   Za nju treba kolona na `bb_prev_recenica` koja se mijenja samo kad se pobjednik
   stvarno promijeni (danas DELETE+INSERT po opsegu prepisuje sve).
6. **Rep nije razložen.** Popravljali smo ga dvaput i oba puta je popravljen
   **instrument, ne tekst** (s165 separatori, s167 naziv jezika). Prvi pogled u sastav
   (k12): veza s dužinom je **nemonotona** — vrh su kratke rečenice (prosjek 27
   znakova), a najgori pojas ima dvostruko više kratkih (232) nego dugih (79).
   **Dva različita repa**, a kaskada ih tretira isto. Izvedivo bez ijednog novog prevoda.
7. **Sastav batcha kao neregistrovan parametar** (§3) — batch 20, refine batch 5 i
   single fallback su tri različite operacije koje tretiramo kao jednu.
8. Naslijeđeno: `refine-strict` u produkciji; dužina rečenice kao prediktor; NER na
   k22/k23/k24; `limits.html` dvije stavke; `sandbox_jezik_probe.py` commit ili ne.

---

*Flavio & Claude · Buchenberg · sesija 170 · 11. avgust 2026.*
