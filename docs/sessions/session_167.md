# Sesija 167 — 9. avgust 2026.

**Fokus:** Prvi sistematski napad na hardkodirane dijelove. Sesija je krenula od
usputnog pitanja o japanskom jeziku, preko njega otkrila dvije neizmjerene
slijepe tacke mjernog aparata, pa zavrsila s tri konkretne izmjene: prag postao
parametar, jezicke mape preseljene iz koda u bazu, sudija dobio engleski naziv
jezika.

**Flaviova okvirna formulacija (nosi cijelu sesiju):** kriterij nije da li je
neki broj tacan, nego **da li je potreban, da li je fiksan za sve, i kako se do
njega dolazi.** Test scenarij: prijatelj u Berlinu trazi Buchenberg na svojim
serverima, sa knjigama i jezicima koje mi nismo ni vidjeli. Danas to nije moguce
bez izmjene source-a ili baze. Ovo je prva sesija koja taj scenarij tretira kao
kriterij.

---

## 1. Health snapshot

| Mjera | Pocetak | Kraj |
|---|---|---|
| Recenice | 50.624 | 50.624 |
| Prevodi | 1.999.485 | 1.999.546 |
| Pobjednici | 390.492 | 390.532 |
| Rupe | 335 | 335 |

Rast korpusa (+61 prevod, +40 pobjednika) je iskljucivo od testova u ovoj sesiji
(k22/hr 1070-1109). Rupe nepromijenjene; 333 su poznate od s161, dvije nove su
posljedica s166 testova (k22/hr glm bez roota) — objasnjeno na otvaranju, nije
nova steta.

Git na pocetku: `buchenberg` cist na `dd56a1e` (s166), `buchenweb` na s152.
Ollama: sva tri modela odgovaraju.

---

## 2. Japanski — od usputnog pitanja do nalaza o mjernom aparatu

### 2.1 Polazno pitanje

Flavio je pitao (a) jesmo li vec razgovarali o japanskom i (b) ima li japansko
pismo sluzbenu konverziju na latinicu.

`conversation_search` je pokazao da japanski nikad nije bio na stolu kao ciljni
jezik — pojavljuje se samo u `docs/inspiracija.md` (s11), prica o Bologni i
zivom pivot prevodu IT->DE->JA. README §2 ga nema ni medju "egzoticnim,
identifikovanim, odgodjenim" (yi, fy, lb).

**Romanizacija:** postoji i nedavno je promijenjena — japanska vlada je
16.12.2025. odlucila da 22.12.2025. izda kabinetsku notifikaciju kojom Hepburn
zamjenjuje Kunrei-shiki (ISO 3602) kao standard, prvi put nakon ~70 godina.
**Ali to NIJE analogon `bb_sr_cirilica.py`:** kana<->romaji je skoro bijektivno,
kanji->romaji trazi citanje (isti znak, vise citanja), romaji->kanji je
nepovratno bez konteksta. Znaci jednosmjerna LLM-zavisna transformacija, nova
crna kutija — ne mehanicka zamjena znakova.

### 2.2 Claudeova pogresna pocetna hipoteza (ispravljena mjerenjem)

Claude je tvrdio: prevod i cosine dio bi radili, sudija ne bi (nema referentnu
tacku). Takodje je tvrdio da bi segmentacija bila prepreka.

**Oboje netacno.** Segmentacija se radi nad ENGLESKIM originalom (`bb_02`);
japanski se nikad ne segmentira. A ispalo je da je upravo **cosine dio** taj koji
ne radi, dok sudija nije ni pozvan.

### 2.3 Sonda `src/sandbox_jezik_probe.py` (NOVO, necommitovano)

READ-ONLY. Prevodi opseg recenica na jezik koji NIJE registrovan, racuna
score/translation_score ISTIM putem kao `bb_03` (funkcije importovane, ne
kopirane — `bb_03` ima `__main__` guard pa je import bezbjedan), i poredi s
POSTOJECIM NLLB prevodima istih recenica iz baze (kontrolna grupa nastala usput).
Nula upisa, nula izmjena produkcijskog koda. Parametri: `--nllb-kod`, `--oznaka`,
`--prag`, `--llm`, `--temp`, `--jezik-naziv`, `--uzorak`.

### 2.4 Rezultati (k22, pozicije 1-200, isti tekst za sve)

| model | ts | bts | komp | % ispod 0.95 |
|---|---|---|---|---|
| ja-nllb | 0.8894 | 0.9114 | 0.9004 | 93.5% |
| ja-mistral | 0.8818 | 0.9516 | 0.9167 | 92.5% |
| kontrola nl | 0.9206 | 0.9631 | 0.9418 | 60.5% |
| kontrola bg (najgori) | 0.9032 | 0.9554 | 0.9293 | 83.5% |

**GLAVNI NALAZ: `translation_score` ne razlikuje dobar japanski od loseg.**
NLLB je dao smece (`hearth-rug` -> `火炉のリッチ`, besmislica; back-translation
"chimney"), mistral profesionalan prevod (`暖炉の敷物` tacno, `ペナン・ローヤー`
tacno, `バスカヴィル家の猟犬` kanonski naslov). **Razlika u ocjeni: 1 postotni
poen.** Na evropskim jezicima ista dva modela dijeli **trideset** poena
(s166 §9: nllb 85-93% ispod praga, mistral 32-62%).

Japansko pismo se pise normalno (kanji+hiragana+katakana) — bojazan o goloj kani
odbacena empirijski.

**glm run pokrenut** (Flavio: "za svaki slucaj imamo potvrdu sto vec znamo"), ali
je glm 2.6-3.4x sporiji (s132/s137) i run nije zavrsen do kraja sesije. Log:
`logs/probe_ja_glm_k22_1_200.log`.

### 2.5 Metodoloska lekcija u toku sonde

Prvi mali test (5 recenica, sve metadata: naslov/autor/poglavlje) pokazao je da
`ts` propada a `bts` je normalan. Na 200 recenica je **obrnuto**. Claude je na
osnovu 5 metadata redova iznio interpretaciju koju je puni run oborio.
**Uzorak od 5 nije uzorak.**

---

## 3. Memorizacija u back-translationu (usputni nalaz, mjeren nad korpusom)

U mistral testu se pojavio `bts = 1.0000` — back-translation je vratio **doslovno
originalnu englesku recenicu**, ukljucujuci dugu s `save upon those not
infrequent occasions...`. Model ne prevodi nazad nego reciklira zapamceni tekst;
Doyle je u training setu svakog velikog modela.

Mjereno nad cijelim korpusom. Prvo grubo (`score > 0.999`), sto je konfundirano
kratkim recenicama; zatim ostro — **doslovna jednakost stringa, recenice preko
120 znakova**:

| model | dugih | identican back | % |
|---|---|---|---|
| glm-5.2 | 64.989 | 2.103 | **3.24** |
| mistral-large-3:675b | 91.751 | 464 | 0.51 |
| gemma3:12b | 139.951 | 166 | 0.12 |
| ministral-3:14b | 139.962 | 90 | 0.06 |
| nllb-600M | 101.218 | **4** | 0.00 |

NLLB je kontrolna grupa: 4 slucaja na 101.218 dugih recenica. Doslovna
rekonstrukcija recenice od 120+ znakova nije slucajnost — 600M MT model je ne
postize prakticno nikad. **Gradijent tacno prati velicinu modela.**

**ALI — provjereno, i Claudeova prva tvrdnja ("memorizacija kupuje pobjede")
je OBORENA podacima:**

| model | udio medju svim kandidatima | udio medju pobjednicima |
|---|---|---|
| glm-5.2 | 3.24% | 3.19% |
| mistral | 0.51% | 0.62% |

Udio je prakticno isti; kod glm-a medju pobjednicima cak neznatno nizi.
Memorizacija napumpa `score`, ali ne kupuje mjesto u korpusu — sudija je ponisti.
Nezavisna potvrda s146 nalaza da rangiranje nosi sudija (~92%), ne cosinus.
Isti oblik kao sudijine nule iz s165: kvar je stvaran i mjerljiv, argmax ga
apsorbuje.

**Za `limits.html`** (kad se web bude dirao): dokumentovana granica
back-translationa, ne problem koji trazi popravku.

---

## 4. Kazna za pismo — izmjerena nad postojecim korpusom

Hipoteza iz japanskog nalaza provjerena je na materijalu koji vec imamo. Srpski
je cirilica, hrvatski i bosanski latinica, jezik prakticno isti. Kljucno:
`bb_sr_cirilica.py` transliterira SAMO prevod, `back_translation` ostaje netaknut
(fix s84) — savrsena paralela japanskom slucaju.

k12, pozicije 1-2600, faza 1, `mistral-large-3:675b`:

| jezik | n | ts | bts |
|---|---|---|---|
| bs | 1900 | 0.9085 | 0.9622 |
| hr | 2200 | 0.9072 | 0.9637 |
| sr | 2200 | **0.9004** | 0.9630 |

`bts` se razlikuje za 0.0007 (sum). `ts` pada za **0.0068** kod srpskog — deset
puta vise. Jedina sistematska razlika je pismo.

**Posljedica koju do danas nismo mjerili: srpski nosi stalan, mali hendikep u
takmicenju s ostalim jezicima.**

Ograda: srpski nije samo drugo pismo nego i drugaciji leksik, pa nije savrseno
izolovano; ali `bts` kontrolise za sadrzaj, a pada samo komponenta koja gleda
prevod direktno.

**Razlika prema hendikep pragu iz s164 (MORA ostati zapisana):** tamo je prag po
jeziku ODBACEN s pravom — unutar iste skale samo preraspodjeljuje pozive, i to
suprotno headroom gradijentu. Ovdje su skale STVARNO razlicite jer embedder
drugacije mjeri pismo. Prvo je olaksica za tezak jezik, drugo je korekcija
instrumenta. **Bez ovog razlikovanja izgledace kao da smo se predomislili.**

---

## 5. IZMJENA 1 — prag kao parametar (commit `a0e028e`)

### Zasto

Prag 0.95 je zivio kao CLI default u `bb_03_prevod.py`, a `run_faza.sh` ga NIJE
prosljedjivao (nalaz s162). Svaka gated runda kroz standardne orkestratore isla
je na 0.95, i **nigdje u logu nije pisalo da jeste 0.95**. Nije smetalo to sto je
fiksan — smetalo je to sto je nevidljiv.

### Sta je uradjeno

- `run_faza.sh`: novi opcionalni `--prag`, prosljedjuje se kao
  `${PRAG:+--prag $PRAG}`. Bez njega ekspanzija je prazna i `bb_03` koristi svoj
  default -> **kaskade 1-4 rade nepromijenjeno.** Prag se ispisuje u zaglavlju
  loga (`prag=0.85` ili `prag=default(0.95)`).
- `run_kaskada5.sh` (NOVO): kaskada4 + `--prag` (default 0.95), prosljedjuje ga
  svim gated rundama. **Root fazu namjerno ne dira** — tamo gate ne postoji, pa
  bi slanje praga lazno sugerisalo da nesto radi.

### Testovi (Flavio autorizovao rad BEZ kontrole i odobrenja)

| test | opseg | prag | gate po rundama | trajanje |
|---|---|---|---|---|
| 1 | k22/hr 1070-1089 | default 0.95 | 6 -> 4 -> 3 -> 3 | 3:04 |
| 2 | k22/hr 1090-1109 | `--prag 0.85` | 3 -> 0 -> 0 -> 0 | 2:13 |

**Kljucni dokaz nisu brojevi u prvoj rundi nego PRAZNE runde 2-4 drugog testa —
nula redova u bazi, ne samo drugaciji tekst u logu.** Prag je stvarno stigao do
`bb_03`.

Semanticki tacno: test 2 zavrsio s 0 recenica ispod 0.85 (izgurao sve preko
svog praga) i 7 ispod 0.95 — na njima nije ni pokusavao. Test 1: 3 ispod 0.95.

**Regresija provjerena izolovano** (kao s164 za `pipefail`): `PRAG=""` daje
prazan argument; `run_faza.sh` bez `--prag` ispisuje `prag=default(0.95)`.

Baza poslije: 40 pobjednika na 40 recenica, nula neocijenjenih.

### Zakljucak koji je Flavio trazio

Prag pomjera i cijenu i domet u istom smjeru: nizi prag nije "blazi kriterij"
nego **manji obim posla**. Test 2 je bio brzi i jeftiniji, ali je zavrsio sa 7
recenica ispod 0.95 naspram 3.

**Ograda:** 20 recenica na jednom jeziku dokazuje da mehanizam radi, ne kako se
prag ponasa. Za to treba 400+ (s165: ispod ~200 mjeri se sum sudije).
**Vece runove radi Flavio.**

---

## 6. IZMJENA 2 — jezicke mape iz baze (commit `a476007`)

### Zatecено stanje

Jezik je bio definisan na **tri mjesta**: `bb_jezik` (kod, id), i dva hardkodirana
dicta u `bb_03_prevod.py` — `JEZIK_NAZIVI` (linija 83, engleski naziv za LLM
prompt) i `NLLB_LANG_MAP` (linija 66, NLLB kod). Novi jezik = INSERT + izmjena
koda + commit.

**Provjereno u bazi:** `bb_jezik.naziv` je na SRPSKOM (`hrvatski`, `nemacki`,
`spanski`), a dictovi su engleski — kolona se ne moze upotrijebiti kakva jeste.
Skup je identican u sva tri izvora (14), pa migracija nije imala nesklada.

### DDL (van gita)

Backup prije: `/tmp/bb_backup_pre_jezik_20260809.dump` (1.5G, verifikovan —
24 `TABLE DATA` unosa; u s131 ih je bilo 18, +5 tabela iz s142 refaktora).
**Napomena:** MCP poziv za `pg_dump` vratio je gresku, ali je backup bio uredno
napravljen — provjereno kroz `ls` + `ps`, ne pretpostavljeno. Isti obrazac
MCP timeouta kao s134/s142.

```sql
ALTER TABLE bb_jezik ADD COLUMN naziv_en varchar(100), ADD COLUMN nllb_kod varchar(20);
UPDATE bb_jezik z SET naziv_en = v.en, nllb_kod = v.nllb FROM (VALUES ...) ...;
-- 14 redova, vrijednosti doslovno iz dosadasnjih dictova, btrim jer je kod character(2)
```

Rezultat: 14/14 popunjeno, nula NULL-ova.

### Kod

- `NLLB_LANG_MAP` i `JEZIK_NAZIVI` -> prazni dictovi `{}` uz komentar
- nova `ucitaj_jezike(cur)` puni obje iz `bb_jezik`
- poziv **jednom, iz `main()`**, odmah poslije otvaranja konekcije
- **Namjerno NE na nivou modula:** `import bb_03_prevod` ne smije traziti
  konekciju — sandbox sonde ga importuju zbog `nllb_batch`/`cosine`. Da je
  ucitavanje globalno, danasnja japanska sonda bi pukla.
- Imena mapa nepromijenjena -> pozivne linije (419 `JEZIK_NAZIVI.get`, 473
  `NLLB_LANG_MAP[kod]`) nedirnute

**Flaviova primjedba usvojena:** `old1`/`old2` u `str.replace()` su samo SIDRA za
pronalazenje (ono sto se brise), ne ostaju u fajlu. Ali primjedba je pogodila
stvarnu stvar — prazan `{}` moze navesti nekog da mehanicki dopisuje jezik u
zagrade. Flavio odlucio: ostaviti `{}` uz komentar, jasno je.

### Claudeove dvije greske (obje ispravljene u toku)

1. Tvrdio da `JEZIK_NAZIVI.get(kod)` tiho salje `None` u prompt. **Netacno** —
   guard vec postoji (linije 419-421: `if not jezik_naziv: print("Nepoznat
   jezik"); continue`).
2. Dodao guard za `nllb_kod`. **Duplikat** — ista provjera vec postoji dvije
   linije nize (`if is_nllb and kod not in NLLB_LANG_MAP`). Uklonjen.

**Obrazac:** oba puta je zakljucak izveden iz `grep` izlaza umjesto iz citanja
bloka koda. Pravilo iz s164 (`\d` prije upita) vazi i za kod: **procitaj blok
prije nego tvrdis sta radi.**

### Testovi

- Ollama grana: k22/hr 1070-1071, vec prevedeno -> `already_done()` preskace,
  nula Ollama poziva, ispis `Jezici iz baze: 14 s nazivom, 14 s NLLB kodom`
- NLLB grana: k22/hr 1070-1071, stvarni prevod (`Croatian`/`hrv_Latn` iz baze),
  provjera opsega 2/2 OK; lanac zatvoren sudijom i pobjednikom da ne ostane krnj

---

## 7. IZMJENA 3 — sudija dobija engleski naziv jezika (commit `3d9e27f`)

### Nalaz

Pri provjeri ostatka lanca (Flaviov zahtjev: "posle uradi isto i za web
prezentaciju i posebno web_export i xray_export, mozda i health check")
otkriveno da `bb_08_sudija.py:112` cita `SELECT id, naziv FROM bb_jezik` —
dakle **srpski naziv** — i ubacuje ga u ENGLESKI prompt (linija 173-174,
`lang=jezik_naziv`):

```
You are evaluating hrvatski translations of an English sentence.
- grammar: grammatical correctness in holandski
- naturalness: idiomatic fluency in nemacki
```

**Tako je ocijenjen cijeli dosadasnji korpus** (~2M prevoda, 390k pobjednika).

### Mjerenje prije izmjene (Flavio: "Izmeriti pa menjati")

Nova sonda `src/sandbox_sudija_naziv_probe.py` (commitovana). READ-ONLY, nula
upisa; `PROMPT_TEMPLATE`, `call_sudija`, `parse_ocjene` **importovani** iz
`bb_08` (ima `__main__` guard). Tri prolaza nad istim kandidatima: A1 (srpski
naziv), B (engleski), A2 (srpski opet). **Treci prolaz nije visak** — daje sum
ovog konkretnog seta, pa se efekat mjeri protiv njega, a ne protiv s146 broja
izmjerenog na drugom materijalu.

k22, pozicije 4-33 (prve tri su metadata), 30 recenica i 150 parova po jeziku,
**dva nezavisna runa**:

| run | jezik | MAE naziv | MAE sum | odnos | bias |
|---|---|---|---|---|---|
| 1 | nl (holandski->Dutch) | 0.0160 | 0.0060 | 2.67 | -0.0102 |
| 2 | nl | 0.0189 | 0.0036 | 5.31 | -0.0104 |
| 1 | de (nemacki->German) | 0.0113 | 0.0018 | 6.37 | -0.0064 |
| 2 | de | 0.0147 | 0.0042 | 3.47 | -0.0067 |

**Dopuna nakon Claudeove ograde** (MAE mjeri nivo, a pobjednika bira poredak
MEDJU kandidatima — ako naziv pomjeri sve jednako, rangiranje ostaje isto):

| jezik | argmax promijenjen po nazivu | po sumu |
|---|---|---|
| nl | 3/30 (**10.0%**) | 0/30 (0.0%) |
| de | 4/30 (**13.3%**) | 0/30 (0.0%) |

**Nula promjena od samog ponavljanja poziva.** Sudijin izbor je stabilan na sum,
ali se mijenja u 10-13% recenica kad se promijeni naziv jezika.

`bias` je NEGATIVAN u sva cetiri mjerenja (-0.0064 do -0.0104): engleski —
dakle ispravan — naziv ocjenjuje **stroze**. Citljivo kao: kad model pouzdano
prepozna jezik, sudi stroze. Znaci korpus je ocjenjivan blaze nego sto bi bio.

### Izmjena i cijena

Jedna linija: `SELECT naziv` -> `SELECT COALESCE(naziv_en, naziv)`. `COALESCE`
jer je `naziv_en` NULL-abilna — jezik dodat bez nje pada na srpski naziv umjesto
da posalje `None` u prompt.

Testirano k22 4-5 nl/de/it: zaglavlje ispisuje `Dutch`/`German`/`Italian`,
nijedan poziv sudiji (bez `--force`), nista prepisano.

**CIJENA (svjesna, po s165 §6.4): od sada korpus ima dvije ocjenjivacke ere.**
Postojece ocjene su netaknute; nove nastaju tek pri sljedecem sudijinom prolazu.
Granica je VRIJEME, ne kolona. Poredjenje ocjena prije/poslije nosi zvjezdicu.

**Vazna ograda koja mora ostati zapisana:** mjerenje pokazuje **DA** naziv utice,
**ne koji je izbor bolji.** Vanjskog kriterija nema — sudija je i igrac i mjerni
instrument (s139). Odluka je donesena po koherentnosti artefakta: engleski prompt
trazi engleski naziv.

---

## 8. Inventar hardkodiranih jezika u ostatku sistema

Grep preko `src/*.py`, `*.sh`, i weba:

**CISTO (nijedan jezicki literal):**
- `bb_08_sudija.py` — cita iz baze (sada `naziv_en`)
- `bb_04_pobjednik.py` — samo `SELECT id FROM bb_jezik WHERE kod`
- `bb_web_export.py` — sve preko `lang_kod` iz baze
- `bb_xray_export.py` — isto
- `health_check.py` — samo prikaz

**LEGACY, MRTVO** (s111 potvrdio, zadnje dirano u maju prije `bb` seme):
`run_test.py`, `run_test_gemma4.py`, `run_ga.py`, `run_pivot.py`,
`run_pivot_init.py`, `run_pivot_init_bench.py`, `run_pivot_llm_fix.py`,
`run_translations.py`, `run_claude_test.py`, `run_context.py`, `run_deepl.py`

**SONDE** (literal legitiman, namjenski alati): `sandbox_model_probe.py`,
`sandbox_temp_probe.py`, `sandbox_jezik_probe.py`

**ODLUKA, NE KONFIGURACIJA:** `bb_geometry_export.py:34`
`JEZICI = ["hr","sr","it","de"]` — izbor koji jezici idu u UMAP projekciju

**WEB (nedirnuto, ostaje otvoreno):**
- `geometry.html:346` dugmad + `:465` `LANG_NAME` (5 jezika)
- `learn.html:1179` lista naziva jezika
- `nav.js:238` `geo_leg_hr` i18n kljuc
- `limits.html:48` proza (nebitno)

---

## 9. Sta znaci "dodati japanski" poslije ove sesije

**Za `bb_03` i `bb_08`: jedan INSERT.**

```sql
INSERT INTO bb_jezik (kod, naziv, naziv_en, nllb_kod)
VALUES ('ja','japanski','Japanese','jpn_Jpan');
```

**Ali NE i za cijeli lanac** — ostaje:
1. **Prag za japanski** — parametar postoji, vrijednost ne. Prag 0.95 nije
   prenosiv (dokazano: mistralov vrhunski japanski = 92.5% ispod praga).
2. **Web sloj** — `geometry.html`, `learn.html`, `nav.js` imaju svoje liste.
3. **Kaskada bi bila prazan hod:** na 92.5% ispod praga skoro svaka recenica ulazi
   u sve cetiri runde, a runda ne moze podici `ts` jer kazna dolazi od pisma, ne
   od kvaliteta. Adaptivno pravilo bi vjerovatno presjeklo poslije prve runde
   (prinos < 0.10), pa bi u praksi ispalo root + jedna runda.

---

## 10. Lekcije

1. **Uzorak od 5 nije uzorak.** Interpretacija iz 5 metadata redova (naslov,
   autor, poglavlje) bila je obrnuta od onoga sto je pokazalo 200 recenica.
2. **Procitaj blok koda prije nego tvrdis sta radi.** Dva puta u istoj sesiji
   izveden pogresan zakljucak iz `grep` izlaza (guard za `JEZIK_NAZIVI` vec
   postojao; guard za `nllb_kod` dodat kao duplikat postojeceg).
3. **Prvo tvrdi manje, pa mjeri.** Tvrdnja "memorizacija kupuje pobjede" oborena
   je istim upitom kojim je i postavljena (3.24% kandidata vs 3.19% pobjednika).
4. **Sum se mjeri na istom setu, ne pozajmljuje.** Treci prolaz (A2) u sudijskoj
   sondi je ono sto je razliku pretvorilo u nalaz umjesto u anegdotu.
5. **Argmax nije MAE.** Pomak nivoa ocjene i promjena pobjednika su dva razlicita
   pitanja; prvo je proxy za drugo i moze zavarati u oba smjera.
6. **MCP greska nije dokaz da komanda nije prosla.** `pg_dump` je vratio gresku
   na MCP sloju a backup je bio uredno napravljen — provjereno `ls` + `ps`.
7. **Kontrolna grupa je vec u podacima** (s165 lekcija 2, ponovo potvrdjena):
   sr/hr/bs za pismo, NLLB za memorizaciju — nijedno nije trazilo novi prevod.

---

## 11. Zavrsno stanje

**Commitovi (`buchenberg`, grana `main`, svi pushovani):**
- `a0e028e` — parametrizacija praga: `run_kaskada5.sh` (novo) + `run_faza.sh` passthrough
- `a476007` — jezicke mape iz baze: `bb_jezik` +`naziv_en`/`nllb_kod`, `bb_03_prevod.py`
- `3d9e27f` — sudija dobija engleski naziv + `sandbox_sudija_naziv_probe.py`

**Baza:** `bb_jezik` +2 kolone, 14 redova popunjeno. Backup
`/tmp/bb_backup_pre_jezik_20260809.dump` (1.5G) — **jos nije obrisan.**

**`buchenweb`:** NEDIRNUT, i dalje s152 (15 sesija iza). BB_VERSION nepromijenjen.

**Necommitovano, namjerno:**
- `src/sandbox_jezik_probe.py` — sonda za nov jezik, radi, koriscena za tri mjerenja
- `run_faza.sh.bak_pre_prag`, `src/bb_03_prevod.py.bak_pre_jezik`,
  `src/bb_08_sudija.py.bak_pre_naziv_en` — rezerve

**Prevedeno u sesiji:** k22/hr 1070-1109 (40 recenica, testovi praga),
k22/hr 1070-1071 NLLB (2 kandidata). Sve legitimno, lanac zatvoren.

**Ollama potrosnja:** ~600 poziva ukupno (japanske sonde ~40, sudijske sonde
~360, testovi praga ~200). Flavio prijavio ~45% sedmicnih resursa na raspolaganju
na pocetku.

---

## 12. Otvoreno / sljedeci koraci

### Direktno iz ove sesije
1. **Vrijednost praga za japanski** — mehanizam postoji, broj ne. Flaviova ideja
   (jos neimplementirana): skripta koja uzme 100-200 recenica (po pravilu 5%) s
   **pocetka, sredine i kraja** knjige i predlozi parametar. Uzorkovanje po
   dijelovima knjige nije kozmetika — s165 je izmjerio da varijacija po dijelu
   knjige nadmasuje varijaciju po tretmanu (es: 8.6 -> 26.4 kroz 4000 recenica).
2. **Tabela parametara** (skica dogovorena, NIJE radjena): kljuc = trojka
   (knjiga, jezik, model) koju sema vec nosi; prazan `knjiga`/`model` = vazi za
   jezik; sve prazno = vazi svuda. Danasnjih 0.95 postaje JEDAN RED, ne poseban
   slucaj. **Kriticno pravilo: parametar se mora racunati iz ROOT faze** — ako se
   izvede iz distribucije pobjednika, mjerimo vlastiti otisak (povratna sprega
   s139, ista zamka na koju smo naisli u s164 kod hendikep tabele).
3. **Sonda PREDLAZE, covjek UPISUJE** (Flaviova formulacija prihvacena) — predlog
   je provjerljiv, automatski upis nije.
4. **`created_at` kao granica dviju ocjenjivackih era** — NIJE provjereno postoji
   li kolona na `bb_prevodi_recenica`. Dok Flavio ne pusti novi run, ere se ne
   mijesaju; poslije toga granica je samo vrijeme.
5. **`sandbox_jezik_probe.py` commitovati ili ne** — odluka odgodjena.
6. **glm japanski run** — pokrenut, nije zavrsen
   (`logs/probe_ja_glm_k22_1_200.log`).
7. **Brisanje starog dumpa** `/tmp/bb_backup_pre_jezik_20260809.dump` kad prodje
   period sigurnosti (higijena `/tmp`, Flaviovo pravilo iz s131).

### Naslijedjeno, nedirnuto u ovoj sesiji
8. **Instrumentacija iz s166:** po-fazni header u `run_faza.sh`; `time` u kaskade
   1/2/3
9. **Prekalibracija `r` na mistral krivu** — 0.10 izveden iz NLLB roota
10. **Provjera ograde s166 §9** — gdje lanci zavrse, ne samo gdje pocnu
11. **Duzina recenice kao prediktor**; **semantic search** nad `prevod_vektor`
12. **Sinhronizacija dokumenata i weba** — `buchenweb` 15 sesija iza; NER export
    + `nlp.html` idu zajedno; `limits.html` sad ima dvije nove stavke
    (memorizacija back-translationa, kazna za pismo)
13. **"Treci svijet"** (glm@0.1 -> glm@0.8) — s166 §9 pokazao da ne bi rijesio sl
14. Rupe nl/fr 1601-1700 (OOM iz s164/s165); nesklad `v_prevodi_full` vs `bb_04`;
    `N/A` za nulu; `intra_threads`; bug iz s162 (Flaviova odluka: ostaje)

### Okvirno pitanje koje ostaje otvoreno
15. **Tri vrste brojeva zive u istom sloju** i zato svaka nova ideja trazi izmjenu
    izvora: **identitetski** (0.4/0.6, argmax, jedan sudija, jedan embedder —
    mijenjas ih i to vise nije Buchenberg; pripadaju u `KONCEPT.md` i smiju biti u
    kodu), **kalibracijski** (prag, r, N, X, ventil 0.85 — zavise od korpusa i
    jezika, moraju biti postavljivi bez otvaranja `.py`), **operativni**
    (batch 20, paralelizam, timeout, `intra_threads` — zavise od zeljeza).
    Ova sesija je uradila **prvi kalibracijski parametar do kraja** kao obrazac
    koji ostali poslije samo slijede. **Jedan uradjen do kraja vrijedi vise od pet
    zapocetih.**

---

*Flavio & Claude · Buchenberg · sesija 167 · 9. avgust 2026.*
