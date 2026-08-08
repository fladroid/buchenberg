# Session 166 — Vidljivost mjerenja: instrumentacija kaskade i forenzika s165

**Datum:** 8. avgust 2026.
**Fokus:** Provjera štete od haotičnih ponovnih pokretanja kaskade4 (s165) → instrumentacija `bb_03` i `run_kaskada4.sh` → analiza krive prinosa i poređenje root modela

---

## 1. Health snapshot (početak sesije)

| Mjera | Vrijednost |
|---|---|
| Rečenice | 50.624 |
| Prevodi | 1.985.746 |
| Pobjednici | 386.032 |
| Rupe | 333 (nepromijenjeno od s161) |
| Git `buchenberg` | `17275da` (s165), čisto |
| Git `buchenweb` | s152, namjerno iza |
| Ollama | mistral-large-3:675b, glm-5.2, gemma4:31b — svi odgovaraju |

Korpus je narastao od kraja s165 (+8.081 prevoda, +2.000 pobjednika) — Flaviov rad van sesije, ne nesklad.

**Napomena o memoriji:** polazna slika iz memorije bila je zastarjela (brojevi iz s163, `run_kaskada3.sh` prijavljen kao "status nepoznat" iako je napravljen i izmjeren). README i health check ispravili su to na startu — potvrda pravila da je server izvor istine, ne memorija.

---

## 2. Forenzika: šta je haos iz s165 ostavio u bazi

### 2.1 Kontekst

Flavio je u s165 više puta pokretao `run_kaskada4.sh` sa poznatom nepopravljenom greškom, bez pokušaja popravke između pokretanja. Njegova sopstvena ocjena: neodgovorno i amaterski. Zatražena provjera da li je time nastala šteta u bazi.

**Podjela odgovornosti (zapisano radi tačnosti):** greška nije bila jednostrana. Claude je u s165 tri puta krpio posljedicu ručnim `UPDATE`-om umjesto da imenuje da se problem reprodukuje pri svakoj rundi i da treba stati. To je već zapisano kao lekcija 3 u session_165.md.

### 2.2 Logovi

Šest logova, svi od 7. avgusta:

| log | mtime |
|---|---|
| kaskada4_k12_es_2201_3000.log | 16:52 |
| kaskada4_k12_nl_2201_3000.log | 17:22 |
| kaskada4_k12_ro_2201_3000.log | 19:46 |
| kaskada4_k12_sl_2201_3000.log | 19:49 |
| kaskada4_k12_es_3001_4000.log | 21:52 |
| kaskada4_k12_nl_3001_4000.log | 22:23 |

**Bitno ograničenje:** Flaviov obrazac poziva koristi `> logs/...log` (prepisivanje), ne `>>`. Svaki ponovni start briše prethodni log. Logovi zato pokazuju **samo posljednji pokušaj** — rekonstrukcija "šta je pokretano koliko puta" iz njih nije moguća.

Svih šest završilo je čisto: 4 runde, 4 `ZAVRŠENO`, finalni `ZAVRSENO`, nula `PREKID`/`Traceback`/`Killed`.

### 2.3 Trajanja rundi kao trag istorije

| log | r1 | r2 | r3 | r4 |
|---|---|---|---|---|
| es 2201–3000 | 77 min | 26 | 36 | 24 |
| nl 2201–3000 | **49 s** | **48 s** | 22 min | 28 |
| ro 2201–3000 | **53 s** | 65 min | 68 | 63 |
| sl 2201–3000 | **54 s** | 59 min | 69 | 69 |
| es 3001–4000 | 32 min | 22 | 23 | 22 |
| nl 3001–4000 | 60 min | 26 | 22 | 22 |

Runde od ~50 sekundi nisu prazan gate nego `already_done()` koji preskače već odrađenu rundu. Poklapa se tačno sa session_165 §6.2 (nl pao na rundi 3, ro na rundi 2, sl na rundi 2). **Idempotentnost je odradila posao — ponovljeni pokušaji su nastavili odakle je stalo, ne duplirali rad.**

### 2.4 Stanje baze — opseg 2201–4000, četiri jezika

Prevodi po fazi i rundi:

| jezik | faza 1 (root) | r1 | r2 | r3 | r4 |
|---|---|---|---|---|---|
| es | 1800 | 775 | 642 | 593 | 556 |
| nl | 1800 | 707 | 557 | 487 | 451 |
| ro | 800 | 515 | 465 | 429 | 396 |
| sl | 800 | 538 | 483 | 451 | 423 |

- `bez_ocjene = 0` u svakom redu — nijedan prevod bez sudijine ocjene; popravka `bb_08_sudija.py` iz s165 drži
- `prevoda = recenica` u svakom redu — **nula duplikata**
- Pojavile se samo faze 1 i 12 — nijedna zalutala faza iz pogrešnog poziva

Pobjednici:

| jezik | pobjednika | rečenica | NULL sudija | sudija=0 | prosjek |
|---|---|---|---|---|---|
| es | 1800 | 1800 | 0 | 0 | 0.9526 |
| nl | 1800 | 1800 | 0 | 2 | 0.9546 |
| ro | 800 | 800 | 0 | 6 | 0.9222 |
| sl | 800 | 800 | 0 | 0 | 0.9338 |

Osam pobjednika sa `sudija_avg = 0` (0,17%) — poznati "sve nule" režim sudije izmjeren u s165 §7 (0,115% na cijelom korpusu). Postojeća pojava, ne nova šteta.

### 2.5 Zaključak forenzike

**Nula duplikata, nula praznina, nula sirotih redova, nula neocijenjenih prevoda.** Baza je haos apsorbovala bez ogrebotine.

Razlog je arhitektonski, ne srećan: `already_done()` je idempotentan po tačnoj konfiguraciji, `UNIQUE` preko sedam kolona onemogućuje duplikat, `bb_04_pobjednik.py` radi argmax nad svim redovima bez obzira na redoslijed nastanka, a gate iz s164 staje prije ijednog Ollama poziva. Ponovljeni run u najgorem slučaju ne uradi ništa.

Stvarna cijena haosa bila je vrijeme i Ollama resursi, ne integritet podataka. Mjerni run je preživio i kompletan je.

---

## 3. Analiza krive prinosa — es/nl 3001–4000 (puni mjerni run)

Rekonstrukcija stanja poslije svakog koraka (za svaku rečenicu najbolji rezultat dostupan do tog trenutka):

| korak | es prosjek | es ispod praga | nl prosjek | nl ispod praga |
|---|---|---|---|---|
| 0 (root) | 0.9331 | 455 | 0.9266 | 423 |
| 1 | 0.9439 | 373 | 0.9417 | 341 |
| 2 | 0.9472 | 348 | 0.9478 | 306 |
| 3 | 0.9496 | 323 | 0.9495 | 286 |
| 4 | 0.9506 | 308 | 0.9524 | 258 |

Prinos po koraku (prešlo prag / obrađeno):

| | k1 | k2 | k3 | k4 |
|---|---|---|---|---|
| es | 0.180 | 0.067 | 0.072 | 0.046 |
| nl | 0.194 | **0.103** | 0.065 | **0.098** |

### Tri nalaza koji mijenjaju kalibraciju iz s165

**1. Prinos prvog koraka je upola manji nego u kalibraciji.** U s165 je prvi korak davao 0.26–0.69; ovdje 0.18–0.19. Razlika je root: tamo NLLB (slab start, mnogo prostora), ovdje mistral@0.1 (jak start, malo prostora). **Kalibracija r=0.10 rađena je na NLLB krivoj, a kaskada4 trči na mistral rootu — prag je postavljen na drugoj krivoj nego što se primjenjuje.**

**2. Nemonotonost je pravilo, ne izuzetak.** nl pada na 0.065 pa se vraća na 0.098; es pada na 0.067 pa se vraća na 0.072. Oba jezika u istom runu. Tolerancija=2 nije fina korekcija za rijedak slučaj `sl` — ona nosi mehanizam.

**3. X=25% se ne dostiže nijednom.** es završava na 30,8%, nl na 25,8% — nakon četiri runde. Parametar postavljen kao "cilj" nikad ne aktivira zaustavljanje na ovom tekstu. Kao osigurač je bezopasan, kao mjera napretka ne radi ništa.

Simulacija r=0.10 s tolerancijom 2: **es bi stao nakon k3** (ušteda 323 poziva, gubitak 15 rečenica preko praga), **nl bi odradio sve četiri** (0.103 prolazi za tri hiljaditinke). Ista pravila, suprotan ishod na dva jezika.

---

## 4. Analiza vremena — es/nl 3001–4000

| | ukupno | korak 1 | r1 | r2 | r3 | r4 |
|---|---|---|---|---|---|---|
| es | 4:26:20 | 2:46:46 | 32:26 | 22:23 | 23:08 | 21:37 |
| nl | 4:54:26 | 2:44:31 | 60:05 | 25:41 | 21:52 | 22:17 |

Korak 1 nosi ~62% (es) i ~56% (nl) ukupnog vremena — i bio je jedini blok bez instrumentacije, pa je izveden oduzimanjem, ne mjeren.

Interpretacija `time` izlaza (es 3001–4000):
- **4:26:20** wall clock
- 13.748 s user + 158 s system = **13.906 s ≈ 3:51:46** CPU
- **87% CPU**, 3,57 GB maxresident, 0 swaps, 0 disk inputa

**Flaviova ispravka o CPU procentu (usvojena):** 87% ne opisuje trošak nego iskorišćenost. OS raspoređuje resurse; ako se ukloni potrošač, resurs ne prestaje da se koristi nego ga drugi koristi više. Cilj je da resursi budu iskorišćeni, ne da zvrje prazni. Ono što iz broja ostaje korisno je uže: proces ima lokalnog posla (embedder), dakle nije čist mrežni čekač kako je opisan u s165 — što je relevantno samo zato što određuje ponašanje pod paralelizmom.

---

## 5. Diskusija: 1×1000 naspram 2×500

**Flaviovo pitanje:** ima li razlike za analizu ako se pokrene jedan skript za 1–1000 ili dva za 1–500 i 501–1000. Motiv: naći grešku rano umjesto čekati sate pa krenuti ispočetka.

**Odgovor: za ocjenu nema razlike.** Jedinica svega je rečenica, ne poziv — gate gleda pojedinačnu rečenicu, `already_done()` isto, seed isto. Prinos se sabira korektno jer su brojnik i imenilac aditivni: prinos spojenog bloka = (prešlo_A + prešlo_B) / (obrađeno_A + obrađeno_B). Baza pamti rundu po rečenici, pa je rekonstrukcija uvijek moguća.

Dva uslova:
- **Oba bloka moraju proći isti broj rundi.** Ako A stane na 3 a B ode do 4, korak 4 spojene krive ima pola uzorka i nije uporediv.
- **Za vrijeme ne važi.** Različito doba dana, različito opterećenje, različit broj paralelnih procesa = različiti uslovi mjerenja. Ocjena se spaja, sekunde ne.

**Dublji nalaz:** problem u s165 nije bio veličina bloka nego to što je kaskada4 istovremeno bila **prvi run nove skripte i mjerni run**. Te dvije stvari imaju suprotne zahtjeve — test hoće da pukne što prije i jeftinije, mjerenje hoće neprekinut uzorak. Kad su spojene, svaki pad kvari mjerenje a svaki popravak traži novi start.

**Flaviova odluka (usvojena kao praksa):** za nove ili modifikovane skripte prvo 100 rečenica, pa 1000. Za provjerene skripte 1000 odmah.

---

## 6. Urađene izmjene

### 6.1 `bb_03_prevod.py` — ispis `ts`/`bts`/`komp` (commit `a49ca42`)

**Problem:** log je ispisivao `score=0.9169 ts=0.8675` — dvije vrijednosti pod imenima koja ne kažu šta su, i bez kompozitnog.

Provjereno u kodu: `score` = cosine(EN, back-translation) = back_score; `ts` = translation_score = cosine(EN, prevod). Kompozitni **ne postoji kao varijabla u `bb_03`** — izvodi se tek u bazi (`v_prevodi_full.kompozitni`) i u `bb_04_pobjednik.py` (inline SQL, samo u docstringu imenovan). Zato ga nije bilo šta ispisati.

Prije:
```python
print(f"    s{poz}: score={score:.4f} ts={translation_score:.4f}")
```
Poslije:
```python
komp = (score + translation_score) / 2
print(f"    s{poz}: ts={translation_score:.4f} bts={score:.4f} komp={komp:.4f}")
```

Imena varijabli `score`/`translation_score` ostala netaknuta (idu u `upisi_prevod()` i u bazu) — mijenjan samo ispis.

**Vrijednost:** kompozitni je ono što ulazi u finalni score i u gate. Sada se iz loga direktno vidi koja rečenica ide u sljedeću rundu, bez računanja u glavi i bez SQL upita.

### 6.2 `run_kaskada4.sh` — `time` na korak 1 (commit `a49ca42`)

**Nalaz koji je korigovao raniju pretpostavku:** `run_faza.sh` **već ima** `time` na sva tri poziva. Neinstrumentiran je bio samo korak 1 u kaskada skriptama, gdje se `bb_03`/`bb_08`/`bb_04` zovu direktno. Zato su runde imale trajanja a root blok ne.

Dodat `time` prefiks na sva tri poziva u koraku 1.

### 6.3 `run_kaskada4.sh` — header o okolini (commit `aaf9808`)

```bash
okolina() {
    echo ">>> OKOLINA ($1): $(date)"
    echo "    bb_03 procesa vec aktivno: $(pgrep -fc bb_03_prevod.py || :)"
    echo "    load average:$(uptime | sed 's/.*load average://')"
    echo "    RAM: $(free -m | awk '/^Mem:/{print $7" MB dostupno od "$2" MB"}')"
}
```
Pozvana kao `okolina start` na početku i `okolina kraj` prije `ZAVRSENO`.

**Zatvara konfaund otvoren od s132** — "paralelni vs sekvencijalni nisu razdvojeni od doba dana", koji se ponovio u s164 i s165. Bez ovog podatka nijedno izmjereno trajanje nije bilo uporedivo s drugim.

**Bug uhvaćen u prvom testu:** `pgrep -fc` uvijek ispiše broj **i** vrati exit 1 kad nema pogodaka, pa je `|| echo 0` dodavao drugu nulu u zasebnom redu. Ispravljeno u `|| :` (čuva `set -e`, ne dodaje izlaz).

**Zamka zabilježena:** `pgrep -f` matchuje vlastiti command line. Provjera `pgrep -fc run_kaskada4.sh` vratila je 2 iako ništa nije trčalo — hvatala je sam upit. Zato header broji `bb_03_prevod.py`, ne skriptu. Za provjeru koristiti `ps -eo pid,etime,cmd | grep ... | grep -v grep`.

**Odbijena varijanta:** izlazni gate broj u `bb_04_pobjednik.py`. Zahtijevao bi da `bb_04` zna prag 0.95, a prosljeđivanje kroz `run_faza.sh` je veza između skripti koju je Flavio isključio; konstanta u `bb_04` bila bi četvrto mjesto gdje 0.95 živi kao broj. **Flaviova odluka: prag se rješava sistemski ili nikako.** Ne dirano.

---

## 7. Testovi (k22 hr, Hound of the Baskervilles)

Sva tri testa na praznim opsezima iznad zadnje prevedene pozicije (1009):

| opseg | trajanje | CPU | šta je provjeravano |
|---|---|---|---|
| 1010–1029 | 3:22 | 89% | `ts`/`bts`/`komp` + `time` na koraku 1 |
| 1030–1049 | 3:15 | 93% | header (otkrivena dvostruka nula) |
| 1050–1069 | 2:53 | 99% | header poslije popravke, start + kraj |

Razlaganje koraka 1 (1010–1029, 20 rečenica, sam na sistemu):

| blok | trajanje |
|---|---|
| root (prevod) | **53,9 s** |
| sudija | **25,3 s** |
| pobjednik | 0,9 s |

Gated runde: 20–28 s po prevodu, sudija u njima 5 s.

Header poslije popravke (1050–1069):
```
>>> OKOLINA (start): Sat Aug  8 03:10:51 UTC 2026
    bb_03 procesa vec aktivno: 0
    load average: 0.08, 0.13, 0.10
    RAM: 23225 MB dostupno od 23974 MB
...
>>> OKOLINA (kraj): Sat Aug  8 03:13:44 UTC 2026
    bb_03 procesa vec aktivno: 0
    load average: 1.09, 0.59, 0.29
    RAM: 23155 MB dostupno od 23974 MB
```

Sva tri testa su legitimni prevodi (60 rečenica hr u k22), ne otpad.

---

## 8. Prvi run s novom instrumentacijom — k12 4001–4100, četiri jezika

Sva četiri startovala **u istoj sekundi** (03:28:59), load 0.01, prazan sistem.

| | elapsed | CPU | load na kraju | aktivnih bb_03 na kraju |
|---|---|---|---|---|
| es | 27:53 | 96% | **8.88** | 3 |
| nl | 28:54 | 84% | 4.75 | 2 |
| ro | 38:43 | 100% | 1.98 | 1 |
| sl | 43:52 | 93% | 0.78 | 0 |

**Load 8.88 na četiri jezgra = 2,2× overcommit.** Redoslijed završavanja i load na kraju čitaju se kao jedna priča: es završava prvi u najgorem opterećenju, sl posljednji u praznom sistemu. Zadnjih ~15 minuta ro i sl trčali su sami — to je bio njihov najbrži dio. **Bez headera bi se zaključilo da su ro/sl sporiji jezici — tačno onaj konfaund iz s132.**

### 8.1 Blok trajanja

| | root | sudija | pobjednik | r1 |
|---|---|---|---|---|
| es | 11:34 | 1:16 | 3,6 s | 2:40 |
| nl | 13:32 | 1:18 | 3,1 s | 4:19 |
| ro | 13:11 | 1:12 | 3,3 s | 7:09 |
| sl | 13:33 | 1:18 | 3,2 s | 8:42 |

**Root nosi ~90% koraka 1**, ne 2/3 kako je procijenjeno iz malog uzorka. Petnaest `real` linija po logu (3 + 4×3) — instrumentacija kompletna.

**Nezavisna potvrda usporenja pod paralelizmom:** u testu 1010–1029 (sam na sistemu) root je išao 2,7 s/rečenica; ovdje pod četiri procesa 7,9 s/rečenica = **2,9× sporije**. Flaviovo mjerenje u s165 dalo je 3,1× za isti skok. Dva nezavisna mjerenja, isti broj.

### 8.2 Gate brojevi i puna kriva

Iz logova (ulaz u svaku rundu) — **izlaz iz r4 ne postoji u logu**, jer nema faze poslije nje da ga pročita. To je tačno rupa koju je Flavio identifikovao. Dopunjeno iz baze:

| | k0 | k1 | k2 | k3 | k4 |
|---|---|---|---|---|---|
| es | 44 | 33 | 27 | 26 | 25 |
| nl | 37 | 33 | 23 | 17 | 16 |
| ro | 64 | 56 | 52 | 49 | 45 |
| sl | 73 | 62 | 55 | 55 | 54 |

Prosjeci: es 0.9234→0.9485, nl 0.9325→0.9559, ro 0.9006→0.9291, sl 0.8810→0.9273.

Prinos:

| | r1 | r2 | r3 | r4 |
|---|---|---|---|---|
| es | 0.250 | 0.182 | 0.037 | 0.038 |
| nl | **0.108** | **0.303** | **0.261** | 0.059 |
| ro | 0.125 | 0.071 | 0.058 | 0.082 |
| sl | 0.151 | 0.113 | **0.000** | 0.018 |

**Ograda:** 100 rečenica po jeziku — jedna rečenica je 1 postotni poen. Test opsega, ne mjerni run. Obrasci vrijede, decimale ne.

**nl je kontraprimjer pravilu zaustavljanja.** Najslabiji korak mu je prvi (0.108), dva najbolja dolaze poslije (0.303, 0.261). Pravilo r=0.10 preživi za osam hiljaditinki. Da je root bio malo bolji, stalo bi se tačno prije najproduktivnijeg dijela lanca. Isti obrazac i u velikom runu 3001–4000.

**sl i ro nisu problem broja rundi nego roota.** sl kreće od 0.8810, završava na 0.9273, poslije četiri runde još 54% ispod praga; treći korak dao **nulu**. Nijedno pravilo zaustavljanja tu ne pomaže — problem nije kad stati nego odakle se kreće.

---

## 9. Poređenje root modela — uparen uzorak

Otkriveno da u bazi već postoji preklapanje: **iste rečenice, isti jezici, tri različita roota** na opsegu 201–1100 (900 rečenica). Kontrolna grupa nastala usput, bez ijednog novog prevoda.

Procenat ispod praga poslije roota (manje je bolje):

| jezik | mistral@0.8 | mistral@0.1 | nllb |
|---|---|---|---|
| es | **31.7%** | 34.8% | 85.6% |
| nl | **37.1%** | 37.9% | 89.7% |
| ro | 51.8% | **48.8%** | 89.2% |
| sl | **57.0%** | 61.7% | 92.7% |

Prosjeci: es 0.9484/0.9465/0.7653 · nl 0.9374/0.9351/0.7214 · ro 0.9123/0.9176/0.7085 · sl 0.9038/0.8997/0.6749

### Tri nalaza

**1. NLLB kao root je bio pogrešan izbor.** 85–93% ispod praga naspram 32–62%. Odluka da se izbaci iz kaskade4 nije bila stvar ušteda — ostavljao je trostruko više posla refineu. Retroaktivna potvrda.

**2. `mistral@0.8` je bolji root od `@0.1` na tri od četiri jezika.** sl 4,7 pp, es 3,1 pp, nl 0,8 pp; jedino ro voli `@0.1` (3,0 pp). **Kaskada4 kao root koristi `@0.1` — dakle vozi lošiju varijantu na tri jezika.** n=900, pa 4,7 pp = 42 rečenice, iznad šuma. Kontraintuitivno: očekivanje je da niska temperatura daje bolji anchor, a ispada da veća raznovrsnost bolje pogađa iz prve. Isti obrazac koji je u s165 nađen za refine runde, sad i za root.

**3. Rangiranje jezika je stabilno kroz sve rootove:** es < nl < ro < sl, istim redom, kroz sva tri modela. **sl nije žrtva pogrešnog modela — sl je teži jezik za sve.** Promjena roota mu daje nekoliko poena, a treba mu dvadeset. Posljedica: **"treći svijet" (glm@0.1 → glm@0.8) ne bi riješio sl.**

**Ograda:** poredi samo root fazu, ne pun lanac. Moguće je da slabiji root ostavi više prostora refineu pa se kroz četiri runde razlika smanji — iz ovih brojeva se ne vidi. Neprovjereno.

---

## 10. Ideje i diskusija — šta bi pomoglo prevođenju

Flaviovo pitanje: koje informacije, direktno ili indirektno, pomažu kaskadnom prevođenju — posebno one koje se ne mogu naknadno ponoviti.

### 10.1 Neponovljivo (nestaje kad proces završi)

| ideja | status |
|---|---|
| **Broj istovremenih kaskada procesa + load + RAM** | **URAĐENO** (§6.3) |
| **Latencija i tokeni po Ollama pozivu** — odgovor sadrži `eval_count`, `eval_duration`, `load_duration`, mi ih bacamo. Bez njih se ne razdvaja "mreža je sporija" od "naš posao je veći" — pitanje otvoreno od s151, s159, s164 | otvoreno |
| **Brojač retry/timeout po runu** — postoje u logu kao pojedinačni redovi, broje se ručno grepom; sumarni red na kraju bloka pretvorio bi ih u mjeru umjesto anegdote (s159 je cijeli nalaz o batch=20 izveo ručnim prebrojavanjem) | otvoreno |

### 10.2 Već imamo, ne koristimo

| ideja | status |
|---|---|
| **Pozicija u knjizi kao kovarijata** — s165 pokazao da varijacija po dijelu knjige (es: 8.6 → 26.4 kroz 4000 rečenica) nadmašuje varijaciju po tretmanu; svako poređenje metoda na različitim opsezima mjeri tekst koliko i metodu | otvoreno |
| **Dužina rečenice kao prediktor** — `LENGTH(recenica_tekst)`, besplatno; nikad provjereno da li tvrdi pod ispod praga ima strukturu (vrlo duge? vrlo kratke bez konteksta?) | otvoreno |
| **Semantic search nad `prevod_vektor`** — 1024D vektor postoji na svakom prevodu; "slične rečenice u korpusu prevedene različitim metodama" je izvediv upit nad postojećim korpusom, bez ijednog novog prevoda. Nedostaje upit, ne podatak | otvoreno, Flaviova ideja |

**Flaviova primjedba (zabilježena):** najviše boli "bacanje" informacija — ponavljanje istih ideja koje nisu ili nisu potpuno implementirane.

---

## 11. Lekcije

**1. "Nula grešaka" nije rezultat analize.** Prva verzija odgovora na forenziku stala je na "nema štete" i to prikazala kao nalaz. Flaviova primjedba: skripte se puštaju da bi se približili cilju (ocjena prevoda), a ne da bi prošle bez greške; ako je rezultat analize 0 grešaka, onda je posao gotov i projekat se može zatvoriti. Analiza mora odgovoriti **da li se približavamo cilju i kako su se novi parametri pokazali** — ne samo da li je nešto puklo.

**2. Mjerenje vremena nije opcija nego zahtjev.** Flavio: "gdje god je moguće izmjeriti vrijeme". Rekonstrukcija trajanja iz `created_at` u bazi odbijena kao zaobilaženje — instrumentacija ide u skriptu.

**3. Prikaži → OK → izvrši drži i za višekratne izmjene.** Svaka izmjena fajla praćena verifikacijom stvarnog sadržaja (`sed -n`, `bash -n`, `py_compile`), ne pretpostavkom da je `str.replace` uspio.

**4. Ne mijenjati skriptu dok trči.** Bash čita skriptu inkrementalno; izmjena usred izvršavanja može pokvariti run. Čekati završetak.

**5. Ne pisati imena kolona napamet.** Upit je pao na `temperatura` umjesto `model_temperatura`. Pravilo iz s164 (`\d` prije upita) važi i kad je view već jednom pogledan u istoj sesiji.

**6. `pgrep -f` matchuje sam sebe.** Provjera "trči li skripta X" preko `pgrep -fc X` vraća lažno pozitivan rezultat jer i sama komanda sadrži string X.

**7. Odvojiti prvi run nove skripte od mjernog runa.** Suprotni zahtjevi; spojeni, svaki pad kvari mjerenje.

---

## 12. Završno stanje

**Commitovi (`buchenberg`, grana `main`):**
- `a49ca42` — `bb_03` ispisuje `ts`/`bts`/`komp`; `run_kaskada4.sh` korak 1 dobio `time` na sva tri poziva
- `aaf9808` — header o okolini (funkcija `okolina`) na startu i kraju; popravka dvostruke nule

Oba pushovana, working tree čist, `main...origin/main` bez razlike.

`buchenweb` nedirano — i dalje s152, 14 sesija iza.

**Prevedeno u sesiji:** k22 hr 1010–1069 (60 rečenica, testovi), k12 es/nl/ro/sl 4001–4100 (Flaviov run).

---

## 13. Sljedeći koraci

**Instrumentacija (dogovoreno, čeka):**
1. **Po-fazni header u `run_faza.sh`** — dogovoreno kao zaseban korak, namjerno odvojen od izmjena u kaskadi4 da se zna koja je izmjena šta pokvarila. Pokriva sve četiri kaskade i svaki ručni poziv odjednom. Samo `echo`, ne dira nijedan poziv ni izlazni kod.
2. **`time` u kaskade 1/2/3** — isti obrazac kao §6.2, identična izmjena. Flavio: "time bi trebao da ide u sve skripte uopšte", ali sada samo kaskada4 da se ne pokvari ono što radi.

**Analiza (podaci već u bazi, nula novih prevoda):**
3. **Prekalibracija `r` na mistral krivu** — postojeća vrijednost 0.10 izvedena je iz NLLB roota; nl je kontraprimjer koji preživljava za 8 hiljaditinki.
4. **Provjera ograde iz §9** — uporediti gdje lanci završe, ne samo gdje počnu (opseg 201–1100 ima i gated faze).
5. **Dužina rečenice kao prediktor** ostatka ispod praga.
6. **Semantic search** nad `prevod_vektor` — slične rečenice prevedene različitim metodama.

**Otvoreno od ranije:**
7. **Sinhronizacija dokumenata i weba** — Flaviov redoslijed iz s165; `buchenweb` 14 sesija iza; NER export + `nlp.html` idu zajedno.
8. **Prag 0.95** — živi kao CLI default u `bb_03` koji `run_faza.sh` ne prosljeđuje; nigdje deklarisan. Flaviova odluka: rješava se sistemski ili nikako.
9. Rupe nl/fr 1601–1700 (OOM iz s165), nesklad `v_prevodi_full` vs `bb_04`, `N/A` za nulu, `intra_threads`.
10. Bug iz s162 (gated-bez-seeda tiho preskače rečenice bez pobjednika) — Flaviova odluka: ostaje neispravljen.

**Otvoreno pitanje bez odgovora:** ako je `mistral@0.8` bolji root na tri od četiri jezika (§9), treba li kaskada4 mijenjati root — i da li se ta prednost održi kroz pun lanac ili se kroz četiri runde izgubi.

---

*Flavio & Claude · Buchenberg · session 166 · 8. avgust 2026.*
