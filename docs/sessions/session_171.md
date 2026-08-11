# Sesija 171 — 11. avgust 2026.

**Fokus:** analiza prvih punih `run_kaskada9.sh` prolaza (es/ro/nl, k12 5201–5300)
→ nalaz da `refine-strict` na procesljanom terenu nije novi mehanizam →
**kaskada10**: jedna petlja, krug = tri faze s istom rundom.

**Flaviova okvirna formulacija:** strict prompt je izabran zato sto je treca petlja
morala imati *neki* nosac — nije nas zanimao rezultat tog prompta nego **kriterij**
(prirast ocjene). Sesija je pokazala da se kriterij ne moze izmjeriti na mehanizmu
koji umre u prvoj rundi.

---

## 1. Snimak zdravlja

| Mjera | Pocetak | Kraj |
|---|---|---|
| Recenice | 50.624 | 50.624 |
| Prevodi | 2.037.764 | 2.040.431 |
| Pobjednici | 400.872 | 401.072 |
| Rupe | 344 | 343 |

Rast je iskljucivo od Flaviovih runova koji su tekli paralelno sa sesijom —
**u sesiji nije pokrenut nijedan prevod.** Sav rad je bio citanje logova, citanje
koda i pisanje jedne bash skripte.

Git na pocetku: `buchenberg` `f9ef0bd` (s170), `buchenweb` `c22a4ce` (s168).

---

## 2. Prvi puni kaskada9 prolazi — etapa 3 je stala poslije JEDNE runde

Analizirana tri loga (`kaskada9_k12_{es,ro,nl}_5201_5300.log`), 100 recenica po
jeziku. Nula Tracebackova, nula timeouta.

| | root zbir / ispod | e1 rundi | e2 kraj | e3 Δ (% n) | STOP | kraj: zbir / ispod | trajanje |
|---|---|---|---|---|---|---|---|
| es | 92.2996 / 56 | 4 | r12 | **+0.005%** | r14 | 95.7612 / 23 | 43 min |
| ro | 91.0023 / 59 | 3 | r13 | **+0.032%** | r15 | 94.6343 / 35 | 65 min |
| nl | 90.0269 / 59 | 3 | r13 | **+0.018%** | r15 | 95.5666 / 29 | 63 min |

### 2.1 Glavni nalaz

Izvod iz s170 (nad 133 runde kaskade8) razdvojio je dvije klase rundi:

| klasa | raspon Δ (% n) |
|---|---|
| prva runda **novog** mehanizma | 0.195 – 3.238 |
| zavrsna runda **iscrpljenog** mehanizma | 0.000 – 0.143 |

**Sva tri strict-prolaza padaju u donju klasu, i to duboko** (0.005–0.032 naspram
gornje granice 0.143). Za poredjenje, umiruce runde etape 2 iste sesije: es r11
+0.009, r12 +0.000 — **isti red velicine kao strict.**

**Zakljucak: `refine-strict` na terenu koji su base i seed upravo procesljali ne
otvara novu distribuciju.** Promjena teksta prompta unutar seed grane nije novi
mehanizam — seed je seed.

Ograda iz s170 smoke testa (k22/ja +0.65 % n) time je **potvrdjena, ne oborena**:
tamo je strict bio *prvi* mehanizam sa seedom, ovdje *treci*.

### 2.2 `x = 0.10` nije iskusan

Nijedan prolaz nije dosao do druge strict runde, pa pravilo nikad nije moralo
birati. **Bilo koje `x` izmedju ~0.04 i 0.19 dalo bi identican ishod.** Ono sto je
izmjereno nije prag nego **domet mehanizma**.

I to je strukturno, ne slucajno: odluka se donosi *poslije* runde, pa se treca
petlja uvijek izvrsi bar jednom; ako mehanizam u toj prvoj rundi ne predje `x`,
druge runde nema nikad. Uz ovaj prompt je **etapa 3 po konstrukciji tacno jedna
runda**, bez obzira na `x`.

Cijena etape 3: es 1m43, ro 2m34, nl 3m40 — za 0.0055 / 0.0318 / 0.0183 boda.

**Odgovor na Flaviovo pitanje:** de facto isti rezultat kao kaskada8, uz tacno
jednu dodatnu rundu koja nije bila prazna ali je bila premala da bilo sta odluci.

### 2.3 Usput

- **Gate i BILANS se u repu razilaze za tacno 1** (nl r11–r15: gate 30/29/28/28/28,
  BILANS 30/29/29/29/29). Ovdje NEMA ponavljanja pa objasnjenje iz s170
  (`already_done`) ne vazi. Vjerovatan uzrok: **zaokruzivanje na granici** —
  `v_prevodi_full` zaokruzi svaki red pa poredi s 0.95, `bb_04` poredi
  nezaokruzeno; jedna recenica na 0.9499x. **Nije provjereno u bazi.**
- **Prelazak i dalje kasni jednu rundu** (SAZETAK `e1 rundi=3` a izvrsene su 4) —
  dokumentovano u s170 §2.4, potvrdjeno treci put.
- **Rep ne pada:** poslije 14–15 rundi ostaje es 23, nl 29, ro 35 ispod praga.
- `gemma4` bez degradacije u ovom prozoru (20 s – 3 min po bloku).

---

## 3. Kaskada10 — jedna petlja, krug od tri faze

### 3.1 Flaviov algoritam (doslovno)

```
root
ponavljaj:
    faza bez seeda      (12, base)
    faza sa seedom      (16, refine)
    faza sa seedom+strict (24, refine-strict)
dok god ima novih iznad praga
```

Time se root i sve tri faze izvrse **najmanje jednom**.

### 3.2 Zasto ovo rjesava nalaz iz §2

U kaskadi 8/9 se svaki mehanizam posjeti **tacno jednom i zatvori zauvijek**. Ali
faze 16 i 24 rade nad **sidrom** (trenutni apsolutni pobjednik) — kad se sidro
promijeni, to vise nije isti posao. Drugi prolaz kroz seed fazu nije ponavljanje
nego nova operacija nad novim ulazom.

Konkretno za strict: u devetci je mjeren **jednom, u najgorem mogucem trenutku**.
U petlji ga vidimo vise puta sa svaki put drugacijim sidrom — tek tu `x` moze
dobiti krivu umjesto tacke.

### 3.3 Definicija kruga (Flaviova, preciznija od prve)

> U svakom krugu imamo **tri razlicite faze sa istom vrijednoscu runde**. U jednom
> krugu izvrsavamo tri razlicite faze samo jednom.

Posljedica koja je time postala eksplicitna: **runda ne postoji zbog kruga.** Tri
faze istog kruga su ionako tri razlicita reda — `UNIQUE` ih razlikuje po `faza_id`.
Runda sluzi samo da **drugi krug smije ponoviti vec potrosenu fazu.** Dakle faza
kaze STA se radi, runda KOJI PUT.

Dobitak: prvi put se krug moze citati iz baze kao cjelina — `GROUP BY faza_id,
runda` daje "koja faza je u kojem krugu sta donijela", bez parsiranja logova.

### 3.4 Kriterij zaustavljanja (Flaviova odluka)

**Vrti po najstarijem kriteriju — novi prevodi iznad praga.** Zbir i klon-stopa
ostaju **informacija u logu**, ne zaustavljaju.

Obrazlozenje koje je odlucilo: gate-only prolaz dozvoljava da se `ILI` pravilo
(gate ILI prirast zbira) **simulira retroaktivno** iz istih logova — vidjece se
tacno na kojim jezicima je petlja stala dok je zbir jos rastao. Obrnuto ne radi:
da odmah vrtimo `ILI`, nikad ne bismo saznali gdje bi sam gate stao. Isti obrazac
kojim je izveden `x` u s170 i `r` u s165 — **jedan pun prolaz nosi sve varijante
pravila, odsjeceni prolazi ne sadrze jedni druge.**

Konzistentno i sa s169: stroga nula je jedini okidac koji ne grijesi, jer prinos
vaskrsava.

**Nula se broji po KRUGU**, ne po fazi — krug je neproduktivan kad nijedna od tri
faze nije prebacila nijednu preko praga. Petlja je time strpljivija nego dosad:
tri prilike po krugu umjesto jedne.

### 3.5 Klon-stopa — provjereno, nikad nije postojala u kodu

`grep -i klon` po `bb_03_prevod.py`, `sandbox_kaskada_logs.py` i `run_kaskada8.sh`
daje **jedan pogodak: komentar** u kaskadi8 koji citira nalaz iz s169. Brojevi u
s169/s170 su svaki put racunati ad hoc SQL-om.

**Odluka: ne diramo `bb_03`.** Obrazlozenje se tokom razgovora **promijenilo, i to
je bitno zabiljeziti** — prvi argument ("klonovi su retroaktivni") bio je tacan
zakljucak s pogresnim razlogom. Pravi razlog, poslije Flaviovog potpitanja:

| mjera | priroda | moze li se rekonstruisati poslije runa |
|---|---|---|
| gate, zbir | **stanje** | ne po krugu — pobjednik je tekuci pokazivac, `DELETE+INSERT` prepisuje |
| klon-stopa | **dogadjaj** | da — klon je osobina reda u `bb_prevodi_recenica`, koji nikad ne nestaje, i zna se cija je (faza, runda) |

Dakle gate i zbir **moraju** u log; klonovi **ne moraju**, jer ih baza cuva
zauvijek. Isti zakljucak, suprotan razlog.

### 3.6 `run_kaskada10.sh` (novo, 132 linije)

Struktura: `while` po krugu, unutra `for` po `FAZE="12 16 24"`, sve tri sa
`--runda "$KRUG"`.

**Jedna mehanicka odluka:** provjera nule ide **poslije PRVE faze narednog kruga**,
ne na kraju kruga. Gate se cita prije prevoda (poznato kasnjenje), pa gate faze 12
u krugu N+1 zapravo izvjestava o **cijelom** krugu N. Time potvrda nule kosta
**jednu fazu umjesto tri**.

Ispis po fazi: `ZBIR krug K faza F` (tri normalizacije). Odluka: `BILANS krug K-1:
ispod praga G — prethodni krug prebacio D`.

`--max 30` **broji krugove** (Flaviova odluka), default kao u 8/9. Nikad nije
opalio ni u jednoj kaskadi.

**Naslijedjena rupa, svjesno nepopravljena:** `bash run_faza.sh ... | tee` znaci da
izlazni kod dolazi od `tee`, pa `set -e` ne vidi pad faze (Rupa A iz s160).
Desetka je time konzistentna s 7/8/9, ali ne bolja.

**Verifikovano:** `bash -n` cist, `cat -n` cijelog fajla bez duplikata,
`run_faza.sh` potvrdjeno prosljedjuje `--runda "$RUNDA"` (l.54) i
`${PRAG:+--prag $PRAG}` (l.55).

### 3.7 Poziv

```bash
PYTHONUNBUFFERED=1 nohup time ./run_kaskada10.sh \
  --knjiga 12 --jezici "es" --od 5301 --do 5400 \
  > logs/kaskada10_k12_es_5301_5400.log 2>&1 & echo "PID: $!"
```

⚠️ **Treba netaknut opseg.** 5201–5300 je prosao kroz devetku, pa bi tamo
`--runda 1` naisla na postojece redove. Flavio planira 11 jezika × 100 recenica.

---

## 4. Lekcije

### 4.1 Konceptualne

1. **Kad mehanizam umre u prvoj rundi, kriterij se ne moze izmjeriti.** Da bi `x`
   bio iskusan, treci mehanizam mora dati **krivu**, ne tacku. Nalaz nije "kriterij
   ne valja" nego **"nosac ne valja"**.
2. **Prompt nije mehanizam.** Promjena teksta prompta unutar iste (seed) grane ne
   otvara novu distribuciju. Novi mehanizam bi trazio drugu osu — drugi model ili
   drugu temperaturu.
3. **Sidro je ono sto ponavljanje cini smislenim.** Faza nad promijenjenim sidrom
   nije ista faza. To je cijeli argument za petlju umjesto niza etapa.
4. **Stanje naspram dogadjaja** (§3.5) — odredjuje sta MORA u log, a sta baza
   ionako cuva. Korisna podjela i izvan ovog slucaja.

### 4.2 Greske koje se ne ponavljaju (dodaci ledgeru)

- **Eksplicitna lista je granica opsega, ne polazna tacka.** Flavio je imenovao tri
  loga; glob `kaskada9_*` pokupio je cetvrti (`sl`) i ja sam ga jos i gurnuo
  naprijed. Kolege ne testiraju jedan drugog — ako je data lista, lista vazi.
- **`{a,b,c}` brace expansion ne radi na foxunu** (dash). Zapisano jos u s169
  ledgeru, ponovljeno danas. Glob umjesto toga.
- **Ne izmisljati treceg aktera.** "Neko je dao `chmod +x`" — u ovom projektu
  postoje tacno dvije osobe; ako nisam ja, Flavio je. Ispravno pitanje je "jesi li
  ti", ne bezlicna konstrukcija.
- **Ne tvrditi nesklad prije nego se provjeri.** Iz "README kaze 20, log kaze 30"
  napravljena kontradikcija koje nema: `run_kaskada7.sh`=20, `run_kaskada8/9.sh`=30,
  README dokumentuje samo sedmicu. Rupa u dokumentaciji, ne nesklad.
- **Ne hedzovati o postojanju mehanizma** ("`bb_03` je vec ispisuje? ako ne…") —
  `grep` traje sekundu i daje odgovor umjesto pretpostavke.
- **Otvaranje sesije registrom koji nije nas.** Prve poruke su isle u izvjestajni,
  formalan ton; Flavio je to imenovao. Lista zadataka bez cekanja OK nije razlog za
  promjenu registra.

### 4.3 Mjerni aparat

- **README se cita cijeli, log se filtrira.** Limit nije na velicini fajla nego na
  jednom tool rezultatu (~100–150 KB). Tri loga su ~1.1 MB, ali je `grep`-om uzeto
  ~30 KB (3%). **Posljedica koju treba imenovati: o preostalih 97% loga — ispisi po
  recenici, tekstovi prevoda, sta je strict stvarno promijenio — nemamo nikakvo
  misljenje.**

---

## 5. Zavrsno stanje

**Novo:** `run_kaskada10.sh` (132 linije, `100755`).

**Izmijenjeno:** `run_kaskada9.sh` — samo mod `100644 → 100755` (Flavio dao `+x`),
nijedna linija sadrzaja.

**Commit:** `919e463` (grana `main`, pushovan `f9ef0bd..919e463`).

**Baza:** nijedna izmjena — ni sheme ni podataka.

**Web:** NEDIRNUT, `BB_VERSION` ostaje **s168** (`buchenweb` zaostaje 3 sesije).

**Prevedeno u sesiji:** nista.

**Necommitovano, namjerno:** 13 `.bak` rezervi + `src/sandbox_jezik_probe.py`
(odluka odgodjena od s167).

---

## 6. Otvoreno / sljedeci koraci

### Direktno iz ove sesije

1. **Prvi prolaz `run_kaskada10.sh`** — 11 jezika × 100 recenica, netaknut opseg
   (Flavio pokrece). Kljucna tri broja: (a) koliko krugova kad faze rotiraju
   umjesto da idu u nizu; (b) daje li faza 24 nad **promijenjenim** sidrom vise od
   0.005–0.032 % n; (c) klon-stopa po fazi po krugu, iz baze, kao **serija**.
2. **Retroaktivna simulacija `ILI` pravila** iz istih logova — na kojim jezicima je
   gate stao dok je zbir jos rastao, i koliko bi krugova `ILI` dodalo.
3. **Razilazenje gate/BILANS za 1** (§2.3) — hipoteza o zaokruzivanju na granici
   nije provjerena u bazi. Jedan upit.
4. **Ako i u petlji strict ostane u donjoj klasi** — pitanje postaje trazimo li
   drugi nosac za trecu fazu (drugi model / druga temperatura) ili poslije
   base+seed jednostavno nema treceg mehanizma.

### Naslijedjeno, nedirnuto

5. **Rep nije razlozen** (s170 §9.6) — veza s duzinom je nemonotona, vrh su kratke
   recenice; **dva razlicita repa, a kaskada ih tretira isto.** Izvedivo bez ijednog
   novog prevoda. Ostaje najjaca analiticka stavka.
6. Mrtav kod `PREKID/exit(3)` u `bb_03` (436–446).
7. Kaskade 5 i 6 ne prosljedjuju `--prag` svom `bb_04` pozivu (kozmetika).
8. Materijalizacija `finalni_score` kao kolone.
9. Evolucija **apsolutnog** pobjednika u X-Rayu — trazi kolonu na
   `bb_prev_recenica`.
10. Sastav batcha kao neregistrovan parametar.
11. Tabela parametara (s167); vrijednost praga po jeziku.
12. NER na k22/k23/k24; `limits.html` dvije stavke; `sandbox_jezik_probe.py` commit
    ili ne.

---

*Flavio & Claude · Buchenberg · sesija 171 · 11. avgust 2026.*
