# Session 139 — 16. jul 2026.

## Fokus
KONCEPTUALNA sesija — nula izmjena koda/baze/weba. Dva bloka:
(1) potvrda kako self-refine radi mehanički (Flavio provjerava razumijevanje
sistema, korak po korak); (2) Flaviova nova ideja — prompt kao neregistrovan
parametar, pa random selekcija (model × temperatura × prompt × redovi) s
preferencama koje evoluiraju, uz jumping-genes analogiju (McClintock).

## Zdravlje na početku
50.624 rečenice · 1.595.460 prevoda · 302.168 pobjednika. BB_VERSION s138
(buchenberg 41d6139, buchenweb 771bc44). Health check: sve zeleno.
231 poznatih rupa (2b) — sve faza 1, obrazac nepromijenjen: retired modeli +
novi par na djelomično prevedenim knjigama (Flaviovi f1 runovi u toku). Broj
narastao sa 167 (s137→s138) jer je korpus rastao; pobjednici nepromijenjeni
(302.168) → runovi punili f1 kandidate, ne nove pobjede. Prihvaćeno, prio 2.

## Zdravlje na kraju
Nepromijenjeno — nijedan prevod nije upisan, nijedna DDL/DML operacija.
Samo READ-ONLY provjere baze i koda. Web netaknut do dokumentacijskog dijela.

---

## 1. Potvrda mehanike self-refine (Flaviova provjera razumijevanja)

Flavio je vodio kroz niz tvrdnji, svaku potvrđivali čitanjem koda/baze
(ne pamćenja). Redom:

### 1.1 Preduslov i priroda faza
- **Svaki refine korak zahtijeva samo da faza 1 (base) ima pobjednika.** TAČNO.
  `get_seed_map()` (bb_03, l.352) čita sidro iz `bb_prev_recenica JOIN
  bb_prevodi_recenica` — nema filtera po fazi/modelu, samo recenica_id + jezik.
- **Faza 1 = bazna, svaka sljedeća = refine.** TAČNO. `bb_metode`: metod_id=1
  (base, root=t) samo faza 1; metod_id=2 (self-refine, root=f) faze 2 i 3.

### 1.2 Refine faze ne zavise jedna od druge (ISPRAVKA moje ranije formulacije)
Flaviova tvrdnja: **pobjednik je pobjednik, bez obzira ko/kako/kada ga je
proglasio; bilo koja faza se može pokrenuti ako pobjednik postoji.** TAČNO.
- Ranije sam se zbunio praveći razliku "rezultat nije isti po redoslijedu" —
  Flavio ispravno prigovorio: SELEKCIJA pobjednika je uvijek ispravna i
  nezavisna od redoslijeda (argmax je argmax). Ono što zavisi od redoslijeda je
  samo SADRŽAJ SIDRA za budući, još-neizvršeni refine poziv (sidro = trenutni
  apsolutni pobjednik u trenutku pokretanja). To ne čini nijedan ishod
  "pogrešnim" — samo mijenja koji tekst ulazi kao sirovina u sljedeći poziv.
- LEKCIJA (moja greška): ne miješati "da li je selekcija ispravna" (uvijek jest)
  sa "koji skup kandidata nastaje" (zavisi od redoslijeda). Prva je invarijanta,
  druga nije, i ne treba drugu prikazivati kao manu prve.

### 1.3 Garancija jednog pobjednika
`bb_04_pobjednik.py`: apsolutni pobjednik `DISTINCT ON (r.pozicija) ... ORDER BY
r.pozicija, m.naziv` nad kandidatima gdje finalni_score = MAX; fazni pobjednik
`DISTINCT ON (r.pozicija, m.faza_id)` s punim tie-break lancem (finalni DESC,
m.naziv ASC, m.temperatura DESC, pr.id ASC). **Argmax + deterministički
tie-break → uvijek tačno jedan pobjednik** (kad postoji ≥1 kandidat s
translation_score IS NOT NULL), nezavisno od odigranih faza i redoslijeda.

### 1.4 Idempotentnost po (model, temp, faza)
`already_done()` (l.294) + `INSERT ... ON CONFLICT (prevodi_knjige_id,
recenica_id) DO NOTHING`. faza je ugrađena u identitet modela preko
`bb_modeli UNIQUE(naziv, temperatura, faza_id)` → isti model+temp u fazi 2
(id 22/23) i fazi 3 (id 26/27) su RAZLIČITI redovi → različit prevodi_knjige_id.
**Jedna rečenica se datim modelom+temperaturom, U DATOJ FAZI, prevodi tačno
jednom** — garantovano constraint-om, ne samo logikom skripte.

### 1.5 Faza mora biti registrovana
`run_faza.sh` guard 1: `bb_faza_info.py --faza N` → exit 1 ako faza ne postoji
u `bb_faze`. Uz `set -euo pipefail`, skripta staje odmah. **Faza 999 se ne može
pokrenuti (ne postoji), faze 2/3 mogu (postoje + imaju aktivne modele).**

### 1.6 Faze 2 i 3 su tehnički identične
Potvrđeno čitanjem baze: obje metod_id=2 (self-refine); modeli iste trojke
naziv+temp (glm-5.2@0.8, mistral-large-3:675b@0.8), samo odvojeni redovi zbog
UNIQUE(naziv,temp,faza_id). Flavio (iz sjećanja, historijski razlog — nije
tehnički provjeravan): faza 3 uvedena isključivo zbog ograničenja da se ista
trojka ne može pokrenuti dvaput → nova faza_id je bila jedini način da isti
model+temp prevede po drugi put (drugi self-refine prolaz). Tehnički su
identične; razlikuje ih samo redni broj izvršavanja.

---

## 2. NALAZ — prompt je neregistrovan parametar (Flaviova identifikacija)

**Flaviova greška koju je sam identifikovao (i moja — nisam je uočio ranije):**
u definiciju faze/metoda trebalo bi da uđe i PROMPT s kojim se prevodi. Prompt
je parametar prevoda jednako kao model i temperatura, a shema ga ne bilježi
NIGDJE — živi samo kao string-literal u `bb_03_prevod.py`
(`prevedi_refine_single`, `prevedi_refine_batch`).

**Konkretna posljedica (s135 klon-fix):** uklonili smo rečenicu "Keep the
reference only if it is already optimal" iz refine prompta zbog klonova. Ali:
isti model+temp+faza → isti prevodi_knjige_id → `already_done()` preskače
rečenicu koju je stari prompt već preveo. Znači **ne možemo ni uporediti ni
koegzistirati** stari-prompt vs novi-prompt prevod. Idempotentnost (koja nas
štiti od dupliranja) ovdje AKTIVNO SAKRIVA efekat promjene prompta. Nemamo
mehanizam da izmjerimo uticaj promjene prompta na prevod.

Konceptualno: §3 KONCEPT ("model = model + konfiguracija") dosljedno primijenjen
glasio bi **prevod → (model, konfiguracija, prompt, faza)**. Prompt je danas
implicitno vezan za metod_id, ali unutar metoda može tiho mutirati bez traga.

### 2.1 Tri mjesta gdje prompt može živjeti (analiza, bez odluke)
- **A — prompt na `bb_faze`** ("faza 2 = prompt a, faza 3 = prompt b"). Jeftino,
  rješava primjer. Mana: prompt je SADRŽAJ, a faza je po s134 dizajnu namjerno
  TANKA (redni broj + identifikator); sadržaj pripada metodu, ne fazi.
- **B — prompt na `bb_metode`** (konceptualno najčišće). Metod = "šta se radi",
  prompt = tekstualna realizacija toga. "self-refine s promptom A" i "s promptom
  B" postaju DVA metoda — tačno hvata s135 (promijenili smo metod, ne redoslijed).
  Faza samo pokazuje na metod (FK već postoji). Cijena: prompt mora biti template
  s placeholderima ({tekst},{jezik},{seed}) u koloni, `bb_03` ga čita iz baze i
  `.format()`-uje umjesto da gradi literal u kodu. Stvarni posao, ne samo ADD COL.
- **C — prompt na `bb_modeli`** (kao temp, po §3). Maksimalna granularnost i
  sloboda poređenja, najveća denormalizacija/najviše redova.

**Claudeov stav (zabilježen, ne odluka):** B je najkonzistentniji s Flaviovim
vlastitim s134 razdvajanjem "metod=sadržaj / faza=redoslijed". Prompt je
nedvosmisleno sadržaj. Promjena prompta = nov red u bb_metode = svjesno
registrovan metod (ista disciplina kao "nova faza = dva INSERT-a"); klon-fix bi
bio "self-refine-v2" umjesto tihe izmjene literala; base metod bi takođe dobio
svoj prompt zapisan.

**Flavio:** sve je posao; nije radio baš ovaj slučaj ali sličan jest — osim posla
nema tehničkih problema. Ovo je glasno razmišljanje, ne odluka o akciji.

---

## 3. IDEJA — random selekcija s evoluirajućim preferencama (jumping genes)

Flaviova ideja (glasno razmišljanje, konceptualni horizont — NE plan akcije):

### 3.1 Osnovna zamisao
Zamisliti skup modela, skup temperatura, skup promptova. Prije starta bilo koje
faze **random** se biraju: dva modela, jedna temperatura, jedan prompt — i
**random se biraju redovi (rečenice) za prevod**. Ako faza s tim atributima
postoji, radi se; ako ne, kreira se nova pa se radi ("traži-ili-kreiraj po
atributima" — idempotentnost na nivou faze). Rezultat: "šarolik" prevod (kao
što je Moby Dick već šarolik jer nije dovršen starim modelima).

### 3.2 Cilj — preference iz šarolikosti
Iz analize šarolikog korpusa izvući PREFERENCE koje bi se koristile za sljedeći
"dirigovani random prevod". Projekat već ima FRAGMENTE preferenci, nesistematične
(README §3 temp-pattern po jezičnoj grupi; s137 stari modeli jaki na arhaičnoj
prozi). Ideja ih pretvara iz anegdote u mjerenje.

### 3.3 Mehanizam preference (Flaviova precizacija — ključno)
Da se izbjegne ELITIZAM (da dalje idu samo najbolji): interval slučajnih brojeva
koji pokriva bolji element JE ŠIRI, ali NE APSOLUTAN. Primjer: na početku 0.1 i
0.8 imaju po 50% šanse. Nakon ~500 rečenica otkrije se da 0.8 pobjeđuje 70% →
interval 0.8 postaje 70%, 0.1 postaje 30%. Vjerovatnoća 0.8 mnogo veća, ali
slabiji NIKAD ne ispada (nenulti interval).

### 3.4 Jumping genes (McClintock) — konceptualni okvir
Flaviova analogija: Barbara McClintock, "jumping genes" (transpozoni), prvo na
kukuruzu; desetljećima osporavano, Nobel 1983 (jedina žena s nepodijeljenim
Nobelom u fiziologiji/medicini do danas). Web-provjereno u sesiji:
- Šarena boja zrna kukuruza = posljedica sistema od 4 gena, uključujući
  "skačuće gene" koji mijenjaju poziciju na hromozomu.
- KLJUČNO za analogiju: McClintock je čitala ŠARU kao PODATAK o mehanizmu —
  nije postavila hipotezu pa testirala, nego promatrala šarolikost i iz nje
  izvela pravilo. To je tačno Flaviova zamisao: pusti da nastane šarolik prevod,
  pa iz šare čitaj mehanizam (preference).

### 3.5 Claudeova analiza — ime, teorija, zamke
Ono što je Flavio opisao ima kanonsko ime: **fitness-proportionate selection**
(roulette-wheel selection), jezgro GA (John Holland). Vjerovatnoća izbora ∝
relativni uspjeh, ali svaki kandidat zadržava NENULTU vjerovatnoću — tačno
Flaviovo "širi interval ali ne apsolutan". Instinkt pogodio kanonski alat I
motiv (anti-elitizam je razlog zašto mehanizam postoji).

Dvije poznate zamke (web-provjereno) direktno pogađaju ovaj slučaj:
- **Prerana konvergencija:** povratna sprega (0.8 dobija → bira se češće → još
  pobjeda → interval raste) može zaključati 0.8 prije nego što je 0.1 pošteno
  uzorkovan na svim jezicima → lokalni optimum. Ironično, baš protiv čega je
  X-Ray poglavlje VI.
- **Nekonzistentan pritisak selekcije:** prejak na početku (velike razlike u
  fitnessu), PRESLAB na kraju (kad su svi kandidati zbijeni blizu plafona).
  Ovo je projektov s134 pejsmejker-nalaz pod drugim imenom — na korpusu gdje su
  scoreovi već 0.95+, proporcionalna selekcija gubi moć razlikovanja.

Popravke iz literature (paleta, ne recept):
- **Rank selection** — interval ∝ RANG (1./2./3. mjesto), ne sirovi score →
  radi i blizu plafona (rješava zamku 2). Claudeova preporuka AKO se ikad gradi:
  rank-verzija Flaviove iste ideje daje sve što želi (slabiji ostaju, jači šire)
  ali je imuna na vlastiti pejsmejker.
- **Fitness scaling** — reskaliranje protiv ranih "super-individualaca" (zamka 1).
- **Tournament selection** — K random → najbolji; otporniji na preranu
  konvergenciju, već u projektovom vokabularu (X-Ray VI, Pong TOURNAMENT).

### 3.6 TRAJNA OGRAĐA (prožima cijeli razgovor)
Interval koji se dodjeljuje kandidatu dolazi od POBJEDA PO NAŠEM SUDIJI. "0.8
pobjeđuje 70%" = "0.8 osvaja 70% po onome što naš sudija voli". Dakle dirigovani
random ne uči "koja je temperatura bolja" nego "koju temperaturu naš ocjenjivač
nagrađuje". Preferenca-mapa je X-Ray VLASTITOG SISTEMA OCJENJIVANJA, ne
objektivna istina o jeziku. McClintock je imala nezavisnu istinu (boja zrna je
boja zrna); mi imamo sudiju koji je i igrač i mjerni instrument (s134 ograda:
"ocjenjivač mjeri sam sebe"). Ne kvari ideju — ali određuje kako se čita rezultat.

### 3.7 Flaviov zaključni okvir
- Genetski algoritmi su mu poznati, ali ugradnja OVDJE nije jednostavna.
- Populacija je tolika da bilo koji način selekcije ima podjednako pozitivnog i
  negativnog — za KONCEPT je važno samo DA SELEKCIJA POSTOJI (ne koja tačno).
- Ovo ostaje konceptualni horizont, glasno razmišljanje. Nije plan akcije.

---

## Odluke i status
- **Nijedna izmjena koda/baze.** Sve READ-ONLY provjere.
- Prompt-kao-parametar (§2) i random-selekcija-s-preferencama (§3) su
  ZABILJEŽENI KONCEPTI/HORIZONT, ne zadaci. Bez obaveze implementacije.
- s138 Odluka 2 (web stabilizacija/estetsko glačanje sljedećih sesija) i dalje
  važi — ova sesija je bila konceptualni predah, ne skretanje s tog pravca.

## Lekcije
1. **Ne miješati "selekcija je ispravna" (invarijanta) sa "koji skup kandidata
   nastaje" (zavisi od redoslijeda).** Moja ranija formulacija prikazala je drugo
   kao manu prvog — Flavio ispravio. Pobjednik je pobjednik, uvijek.
2. **Idempotentnost može sakriti efekat promjene parametra koji nije u ključu.**
   Prompt nije u (model,temp,faza) trojci → promjena prompta je nevidljiva jer
   `already_done()` preskače rečenicu. Parametar koji utiče na izlaz a nije u
   identitetu = slijepa tačka mjerenja.
3. **Flaviov instinkt za GA-selekciju pogodio kanonski mehanizam
   (fitness-proportionate) I njegov motiv (anti-elitizam) bez formalnog GA
   aparata.** Vrijednost partnerstva: imenovati mu teoriju iza intuicije +
   upozoriti na dvije poznate zamke (prerana konvergencija, pejsmejker blizu
   plafona) + ponuditi rank-verziju kao imunu varijantu iste ideje.
4. **Jumping genes analogija je dublja nego dekoracija:** McClintock je čitala
   ŠARU kao podatak o mehanizmu — tačno Flaviov "iz šarolikog prevoda čitaj
   preference". Ali njena mjera je bila nezavisna (boja zrna), naša nije (sudija).

## Sljedeći koraci
- Nastavak web stabilizacije/estetskog glačanja (s138 Odluka 2).
- AKO se prompt-kao-parametar ikad gradi: Claudeov stav je opcija B (prompt na
  bb_metode), po s134 disciplini "sadržaj u metod, redoslijed u faza".
- AKO se random-selekcija ikad gradi: rank-bazirana verzija (ne sirovi
  proporcionalni score) zbog pejsmejkera blizu plafona; i eksplicitno tretirati
  preferencu kao X-Ray sudije, ne kao istinu o jeziku.

---
*Flavio & Claude · Buchenberg · Sesija 139 · 16. jul 2026.*
