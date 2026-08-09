# Sesija 168 — 9. avgust 2026.

**Fokus:** Jezik kao podatak — zatvaranje lanca od baze do weba. Sesija je krenula
kao nastavak s167 linije (eliminacija hardkoda oko ciljnih jezika), usput popravila
jedan pogresan dizajn iz same s167, registrovala japanski, i zavrsila ukidanjem sest
hardkodiranih rjecnika u web prezentaciji.

**Flaviova okvirna formulacija:** korisnika ne zanima ko parametar trosi, kako ga
trosi ni zasto. On pokrene jedan skript s knjigom, jezikom i intervalom, i ocekuje
da se desi carolija — prevedene recenice. To se zove **workflow**, i to je jedina
jedinica koja ga zanima. **Prevod** = sve od root faze preko narednih faza,
eventualnih rundi, sudije, do pobjednika.

---

## 1. Health snapshot

| Mjera | Pocetak | Kraj |
|---|---|---|
| Recenice | 50.624 | 50.624 |
| Prevodi | 1.999.546 | 1.999.624 |
| Pobjednici | 390.532 | 390.572 |
| Rupe | 335 | 337 |

Rast (+78 prevoda, +40 pobjednika) je iskljucivo od dva testa u ovoj sesiji
(k22/de i k22/ja, oba 1010-1029).

**Dvije nove rupe imenovane:** k22/de `nllb-600M` 829/849 i k22/de
`mistral-large-3:675b`@0.8 829/849 — po 20 recenica. Uzrok je mehanicki i ocekivan:
`run_kaskada5.sh` vozi root **samo** mistral@0.1, pa ostali root modeli zaostaju za
tacno onoliko koliko kaskada odmakne. Isti obrazac kao s166. Japanski nema rupa jer
je nov jezik — `MAX` po grupi je njegov vlastiti broj.

Git na pocetku: `buchenberg` `149c274` (s167), `buchenweb` s152.

---

## 2. Ponovno citanje kaskade5 — sta korisnik dobija

Flavio je otvorio sesiju provjerom razumijevanja: pokrenem li kaskadu5 kao
kaskadu4, dobijem li prevedene recenice u zadatoj knjizi/jeziku/intervalu, samo s
pragom kao parametrom?

**Odgovor: da.** Provjereno u kodu, ne iz sjecanja:

- `run_faza.sh:12` `PRAG=""`, `:55` `${PRAG:+--prag $PRAG}` — bez `--prag`
  ekspanzija je prazna, vrijedi `bb_03` default 0.95; kaskade 1-4 nedirnute
- `run_kaskada5.sh:33` `PRAG="${PRAG:-$PRAG_DEFAULT}"` — kaskada5 **materijalizuje**
  default, pa uvijek prosljedjuje eksplicitnu vrijednost i uvijek je ispisuje

**Procesna greska (Claude), zapisana bez ublazavanja:** na jasno postavljeno
pitanje o workflow-u uslijedila su dva uzastopna kontra-pitanja o granicama i
parametrima umjesto odgovora. Poslije 160+ sesija namjera ("hocu da prevedem
interval knjige na neki jezik") ne treba da se dokazuje. **Pravilo: kad je pitanje
odgovorivo s da/ne iz koda, prvo odgovor, pa nijanse ako ih ima.**

---

## 3. `COALESCE` iz s167 — mjera opreza koja je bila put ka tihoj gresci

### Nalaz

Provjera lanca "ime jezika mora biti engleski" pocela je od promptova u bazi:
`bb_promptovi`, 4 reda × 4 kolone = **16 sablona, svi cisti** — svuda
`{jezik_naziv}`, nigdje jezicki literal. `bb_03` puni taj placeholder iz
`naziv_en` (linije 77-80, 406), `bb_08` isto, `bb_04` ga ne koristi.

Ostala je jedina ranjivost: `naziv_en` je bila NULL-abilna, a `bb_08` je imao
`COALESCE(naziv_en, naziv)`.

**Flaviov argument (presudan):** `COALESCE(naziv_en, naziv)` je logicki jednako
`COALESCE(naziv_en, bilo_sta_sto_nije_null)`. Garantuje samo da vrijednost
**postoji**, ne da je **engleska**. Da je `naziv_en` falio, u engleski prompt bi
opet otisao `holandski` — tacno bug koji je s167 mjerio i ispravljao. Fallback je
vodio pravo nazad u gresku, samo tiho.

**To nije bio propust u izvrsenju nego u argumentaciji: `COALESCE` je Claudeov
prijedlog iz s167, obrazlozen kao mjera opreza. Flavio ga je prihvatio na osnovu
tog obrazlozenja.**

### Izmjena

```sql
ALTER TABLE bb_jezik ALTER COLUMN naziv_en SET NOT NULL;   -- 14/14 popunjeno, proslo
```
```python
# bb_08_sudija.py:112
- cur.execute("SELECT id, COALESCE(naziv_en, naziv) FROM bb_jezik WHERE kod = %s", (kod,))
+ cur.execute("SELECT id, naziv_en FROM bb_jezik WHERE kod = %s", (kod,))
```

**Garancija preseljena iz koda u shemu.** Guard `if not row` ostaje ispravan —
hvata nepoznat kod jezika, sto je stvarni slucaj.

`nllb_kod` namjerno ostaje NULL-abilan: jezik koji NLLB ne podrzava je legitiman,
i `bb_03` ga glasno preskace.

---

## 4. Kontrolni run — k22/de 1010-1029 kroz `run_kaskada5.sh`

Prvi pun lanac poslije izmjene. Bez `--prag`, dakle default.

```
>>> PARAMETRI: knjiga=22 jezici='de' opseg=1010-1029 prag=0.95 rundi=4
── Jezik: de (German), prevodi_knjige_id=13578 ──      ← bb_03
══ Jezik: de (German) ══                                ← bb_08
```

**`German`, ne `nemacki`** — prvi put da lanac radi s ispravnim nazivom kroz cijeli
tok, i to bez fallbacka.

| | root | r1 | r2 | r3 | r4 |
|---|---|---|---|---|---|
| ispod praga 0.95 | 4 | 4 | 3 | 3 | 2 |
| trajanje | 48 s | 21 s | 18 s | 18 s | 17 s |

Ukupno 2:36, sistem prazan. Baza: 20 recenica, 32 prevoda (20 root + 12 gated,
tacno 4+3+3+2), **nula neocijenjenih**.

---

## 5. Japanski registrovan

```sql
INSERT INTO bb_jezik (kod, naziv, naziv_en, nllb_kod)
VALUES ('ja','japanski','Japanese','jpn_Jpan');   -- id 15
```

**Prvi jezik dodat otkako su mape preseljene u bazu (s167). Jedan INSERT, nula
izmjena koda** — obecanje iz s167 provjereno u praksi, ne samo na papiru.

### Run k22/ja 1010-1029 (isti opseg kao de — kontrolna grupa po konstrukciji)

```
── Jezik: ja (Japanese), prevodi_knjige_id=17635 ──
══ Jezik: ja (Japanese) ══
```

Kvalitet japanskog na oko uredan: `ホームズは私の腕に手を置いた。`,
`「喜んで参ります。」と私は言った。` — kanji+hiragana normalno, ne gola kana.
Sudija radi bez problema (0.93-1.00).

### ⚠️ Neslaganje sa s167 — otvoreno, NIJE istrazeno (Flaviova odluka: "ima vremena")

| | root | r1 | r2 | r3 | r4 |
|---|---|---|---|---|---|
| **ja** ispod praga | 10 (50%) | 8 | 4 | 4 | (2 preostalo) |
| **de** ispod praga | 4 (20%) | 3 | 3 | 2 | |

s167 je za mistral japanski izmjerio **92.5% ispod praga** (k22, pozicije 1-200) i
zakljucio da bi kaskada bila prazan hod jer runda ne moze podici `ts`. Ovdje je
50% poslije roota, spusteno na 20% kroz cetiri runde — **refine JESTE podizao `ts`**.

Kandidati za objasnjenje (nijedan provjeren):
1. **Razlicit opseg.** 1-200 nosi metadata (naslov, autor, poglavlje) i pocetak
   knjige; 1010-1029 je cist dijalog. s165 je izmjerio da varijacija po dijelu
   knjige nadmasuje varijaciju po tretmanu (es: 8.6 → 26.4 kroz 4000 recenica).
2. **Sonda naspram pipeline-a.** s167 sonda racuna score importovanim funkcijama
   iz `bb_03`, van pipeline-a. Ako se putanje razlikuju, jedna od dvije mjere je
   pogresna — to bi bio ozbiljniji nalaz od prvog.

**Kontrolna grupa vec postoji u bazi:** k22/de 1010-1029, isti tekst, isti dan,
isti mehanizam. Poredjenje ne trazi nijedan nov prevod.

**Ostaje kako je s167 rekao:** vrijednost praga za japanski nije utvrdjena.
Mehanizam postoji, broj ne.

---

## 6. Web prezentacija — sest rjecnika i nesklad medju njima

### Zateceno stanje

Grep po ciljnim jezicima (odvojeno od UI jezika — `NAV_I18N`/`LANG_LABELS`
namjerno izostavljeni) nasao je **sest hardkodiranih rjecnika u pet fajlova**:

| fajl | linija | imena |
|---|---|---|
| `books.html` | 178 | nativna (`Hrvatski`, `Српски`), 14 jezika |
| `art.html` | 417 | nativna, 15 (s `en`) |
| `art.html` | 582 | nativna, 15 — **duplikat u istom fajlu** |
| `reader.html` | 440 | nativna, 14 |
| `stats.html` | 132 | nativna, 14 |
| `learn.html` | 1178 | **engleska** (`Croatian`, `Serbian`), 15 |

**Prvi grep je propustio `reader.html` i `stats.html`** jer je izlaz bio odsjecen
na `head -50`. Lekcija: `head` na dijagnostickom grepu moze sakriti tacno ono sto
se trazi — bolje suziti obrazac nego skratiti izlaz.

### Nalaz koji je odredio rjesenje

`books.html` isti jezik zove `Hrvatski`, `learn.html` ga zove `Croatian`. Nesklad
je bio nevidljiv dok je svako imao svoju kopiju.

**Ali nesklad je STVARAN dizajn, ne nemar:** `learn.html` stavlja ime **unutar
recenice** na UI jeziku ("3 books in Croatian") — tu je nativno ime rogobatno.
Ostale stranice ga prikazuju **samostalno**, u badgeu ili dropdownu — tu je
nativno prirodno.

**Posljedica: dvije kolone, ne jedna.** Flaviova odluka: "treba dodati onoliko
kolona s podacima koji nam trebaju."

### Zasto rjecnici nisu mogli prosto nestati

Export je vec slao ime (`languages[].name`), ali **`j.naziv` — srpski**. Web ga
nikad nije prikazao jer je svaka stranica imala vlastiti rjecnik, a `|| l.name`
je bio fallback koji do sada nikad nije opalio. **Isti obrazac kao `COALESCE`:**
fallback koji izgleda kao oprez, a vodi u pogresnu vrijednost. Japanski bi bio
prvi jezik koji ga aktivira — prikazao bi se kao `japanski` usred liste na kojoj
pise `Hrvatski`, `Deutsch`, `Nederlands`.

### Izvedeno

**Baza:**
```sql
ALTER TABLE bb_jezik ADD COLUMN naziv_native varchar(100);
UPDATE ... 15 redova (vrijednosti iz postojecih web rjecnika; 'ja' → 日本語)
ALTER TABLE bb_jezik ALTER COLUMN naziv_native SET NOT NULL;
```
Redoslijed je prisilan: constraint tek kad su podaci unutra.

**Tri imena, tri svrhe** — sada eksplicitno u shemi:

| kolona | primjer | svrha |
|---|---|---|
| `naziv` | `nemacki` | srpski, za ljude; ne ide nigdje u izlaz |
| `naziv_en` | `German` | LLM prompt + ime unutar recenice na webu |
| `naziv_native` | `Deutsch` | samostalan prikaz na webu |

**`bb_web_export.py`:**
- `get_languages_for_book` vraca `naziv_native` + `naziv_en` (bila `naziv`)
- nova `get_all_languages(cur)`
- generise **`data/langs.js`**: `window.BB_LANGS = {kod: {native, en}}`, 16 unosa
- `en` dodat eksplicitno kao **izvorni jezik korpusa** (invarijanta projekta,
  nije ciljni jezik pa ga nema u `bb_jezik`)
- `books.json` nosi `name` (native) + `name_en`; `tr_*.json` `lang_name` = native

**Pet stranica:** `<script src="data/langs.js"></script>` prije `nav.js` (sinhrono,
linija 8 u svakoj), rjecnici zamijenjeni `Proxy`-jem nad `window.BB_LANGS`.
Pozivna mjesta (`LANG_NAMES[code]`, `|| code` fallback) **nedirnuta** — ~30
referenci, nijedna izmijenjena.

`geometry.html` **NEDIRNUT**: njena lista (`hr/sr/it/de`) nije rjecnik imena nego
**izbor koji jezici ulaze u UMAP projekciju** (`bb_geometry_export.py:34`) —
odluka, ne konfiguracija (klasifikacija iz s167 §8).

### Greska uhvacena u verifikaciji

Prva zamjena u `books.html` ostavila je originalni `};` iza `Proxy` izraza →
nedostajala zatvorena zagrada, **sintaksna greska koja bi oborila cijelu
stranicu**. Uhvacena `sed -n` provjerom stvarnog sadrzaja odmah poslije zamjene,
prije exporta. Ostala cetiri fajla su zamjenu imala zajedno sa `};` pa su bila
ispravna.

**Potvrda pravila iz s166 lekcije 3:** poslije svake izmjene fajla provjeriti
**stvarni sadrzaj**, ne pretpostaviti da je `str.replace` dao ono sto se htjelo.

---

## 7. Sta znaci "dodati jezik" poslije ove sesije

**Prevod (`bb_03`, `bb_08`, `bb_04`): jedan INSERT.** (s167)

**Web: jedan INSERT + `bb_web_export.py`.** (s168) Jezik se pojavljuje u Library,
Reader, Stats, Art i Learn s ispravnim imenom, bez ijedne izmjene HTML/JS izvora.

```sql
INSERT INTO bb_jezik (kod, naziv, naziv_en, naziv_native, nllb_kod)
VALUES ('ja','japanski','Japanese','日本語','jpn_Jpan');
```

**Ostaje otvoreno:**
1. **Vrijednost praga za jezik** — parametar postoji od s167, broj ne
2. `geometry.html` / `bb_geometry_export.py` — izbor jezika za UMAP je odluka
3. `nav.js:238` `geo_leg_hr` i18n kljuc — dio istog geometry izuzetka

---

## 8. Lekcije

1. **Fallback koji garantuje "nije NULL" ne garantuje "ispravno".**
   `COALESCE(a, b)` je logicki `COALESCE(a, bilo_sta)` ako `b` nije semanticki
   zamjena za `a`. Isti obrazac nadjen dvaput istog dana: `COALESCE` u sudiji i
   `|| l.name` na webu — oba su izgledala kao oprez, oba su vodila u pogresnu
   vrijednost. **Garancija pripada shemi, ne kodu.**
2. **Kad je pitanje odgovorivo s da/ne iz koda — prvo odgovor.** Kontra-pitanja o
   granicama i parametrima na jasno izrecenu namjeru su trosak, ne opreznost.
3. **`head` na dijagnostickom grepu moze sakriti nalaz.** Dva od sest rjecnika
   propustena zbog `head -50`. Suzi obrazac, ne izlaz.
4. **Nesklad medju kopijama moze biti stvarna potreba.** `books` vs `learn`
   (`Hrvatski` vs `Croatian`) izgledao je kao nemar, a bila su dva razlicita
   konteksta prikaza. Poravnanje na jedno ime bilo bi regresija.
5. **Provjeri stvarni sadrzaj fajla poslije svake zamjene.** Jedna zamjena od sest
   ostavila je sintaksnu gresku koja bi oborila stranicu.
6. **Kontrolna grupa je opet vec bila u podacima** (s165 lekcija 2, treci put):
   k22/de 1010-1029 je nastao kao test popravke, a ispao je savrsena kontrola za
   japanske brojeve — isti tekst, isti dan, isti mehanizam.
7. **Sest kopija sakriva nesklad; jedan izvor ga cini nemogucim.** Nesklad
   `Hrvatski`/`Croatian` postojao je neodredjeno dugo i nije mogao biti primijecen
   dok svaka stranica ima svoju listu.

---

## 9. Zavrsno stanje

**Commitovi:**
- `buchenberg` `37c8e36` (grana `main`, pushovan) — `bb_08_sudija.py`,
  `bb_web_export.py`, `README.md`
- `buchenweb` `c22a4ce` (grana `master`, pushovan) — pet HTML stranica + `nav.js`

**Baza:** `bb_jezik` +`naziv_native` (NOT NULL), `naziv_en` → NOT NULL,
+1 red (`ja`, id 15). Ukupno 15 jezika.

**Web:** `BB_VERSION` **s152 → s168** — prvi put dirnut od s152 (16 sesija).
Export pokrenut (54 s), `data/langs.js` generisan (16 jezika).

**Necommitovano, namjerno:** `.bak` rezerve
(`bb_08_sudija.py.bak_pre_coalesce`, `bb_web_export.py.bak_pre_langs`,
`README.md.bak_pre_s168`, plus s167 rezerve), `src/sandbox_jezik_probe.py`
(odluka odgodjena od s167).

**Prevedeno u sesiji:** k22/de 1010-1029, k22/ja 1010-1029 (po 20 recenica,
puna kaskada5, lanci zatvoreni).

---

## 10. Otvoreno / sljedeci koraci

### Direktno iz ove sesije
1. **Japansko neslaganje s167 vs s168** — 50% naspram 92.5% ispod praga.
   Kontrolna grupa (k22/de 1010-1029) vec u bazi, nijedan nov prevod ne treba.
   Razdvojiti: efekat opsega vs razlika sonda/pipeline.
2. **Vrijednost praga za japanski** — mehanizam postoji od s167, broj ne.
3. **Preostale rupe k22/de** (nllb 20, mistral@0.8 20) — posljedica kaskade5 koja
   vozi samo mistral@0.1 root.

### Naslijedjeno, nedirnuto
4. **Tabela parametara** (s167) — kljuc (knjiga, jezik, model); prag 0.95 postaje
   jedan red. **Racunati iz ROOT faze**, ne iz pobjednika (povratna sprega, s139).
5. **Sonda koja PREDLAZE prag** — uzorak s pocetka/sredine/kraja knjige (s165).
6. **NER export + `nlp.html`** idu zajedno; k23/k24 bez NER sloja.
7. **`limits.html`** — dvije nove stavke cekaju: memorizacija u back-translationu
   (glm 3.24% vs nllb 0.00%) i kazna za pismo (~0.007 cirilica, cross-script red
   velicine vise).
8. Prekalibracija `r` na mistral krivu; duzina recenice kao prediktor; semantic
   search nad `prevod_vektor`; `intra_threads`; nesklad `v_prevodi_full` vs
   `bb_04`; bug iz s162 (Flaviova odluka: ostaje).

---

*Flavio & Claude · Buchenberg · sesija 168 · 9. avgust 2026.*
