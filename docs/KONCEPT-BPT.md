# BPT — Buchenberg Parallel Translate

*Konceptualni nacrt (s174). Nema koda, nema brojeva.*

## Šta je problem

Kad se zadani interval podijeli **statički** na onoliko dijelova koliko ima procesa,
ukupno trajanje je `max(dijelova)`, ne prosjek — jedan spor dio drži sve ostale kao
taoce. Dijelovi gotovo nikad ne traju jednako, i nije važno zašto.

**Dinamička podjela** to rješava: dijelova ima više nego radnika, i čim se neko mjesto
oslobodi koordinator ga popuni sljedećim dijelom. Ukupno trajanje teži prosjeku, a rep se svede na trajanje
jednog posljednjeg dijela. Isti princip kao granule u Oracle Parallel Query.

## Uloge

**Koordinator** — prima knjigu, jezik i interval. Priprema posao, dijeli ga na dijelove
i nadgleda koliko ih se izvršava. Ne prevodi.

**Posao je za koordinatora neproziran:** ne zna za faze, sidro, prag ni rundu. To je
stvar kaskade unutar dijela. Zato BPT ne može pokvariti kvalitet prevoda.

## Radnik

**Radnik nije entitet — radnik je uloga.** Linux proces koji trči u pozadini,
identifikovan svojim PID-om, i predstavlja izvršenje jedne kaskadne skripte s
parametrima. **Radnik ne postoji ukoliko ne radi.**

Posljedica: koordinator ne traži slobodnog radnika i ne komunicira s njim. On samo
**broji koliko procesa trči** i dopunjava do zadanog broja. Radnik nastaje
pokretanjem, prestaje postojati završetkom — i nema nijedne linije komunikacije nazad
prema koordinatoru. (Mrtav radnik ne može zaboraviti da se javi.)

## Pseudokod

```
KOORDINATOR(knjiga, jezik, interval, N_radnika, N_dijelova):

    red = podijeli(interval, N_dijelova)     # N_dijelova > N_radnika

    pokreni do N_radnika procesa iz reda

    petlja:
        prebroj aktivne
        ako aktivnih < N_radnika i red nije prazan:
            dopuni do N_radnika              # radnik nastaje pokretanjem
        ako je red prazan:
            izađi iz petlje
        čekaj

    pražnjenje: čekaj da svi aktivni završe
    prijavi listu log fajlova
```

Radnik je poziv postojeće kaskadne skripte s uskim `--od/--do`, nedirnut.

**Šta u ovome namjerno NE postoji:**

- **Dodjela.** Nigdje ne stoji "daj ovom radniku ovaj dio" — stoji samo "dopuni do N".
  Posao se uzima iz reda u trenutku pokretanja, ne dodjeljuje nekome ko čeka.
- **Praćenje ko je šta radio.** Koordinator ne pamti koji je proces nosio koji dio.
  Ispravnost to ne traži: upis je idempotentan po tačnoj konfiguraciji, pa se nepotpun
  dio prosto ponovo pusti, a već upisano se preskoči.
- **Identifikacija greške i oporavak** — odloženo svjesno (v0 radi u idealnom svijetu).

**Faza pražnjenja je vlastiti korak,** ne uslov petlje: kad posla nestane, koordinator
ne gasi se nego čeka da posljednji procesi završe, pa tek onda prijavljuje.

### Šta se broji

Ako se broji **broj procesa**, brojanje mora biti dovoljno usko da uhvati samo vlastite
radnike. `pgrep` po imenu kaskade uhvatio bi i ono što je Flavio pustio rukom, ili
procese drugog koordinatora za drugi jezik. Koordinator koji broji tuđe procese kao
svoje sam sebe koči; koji ih ne broji, prekoračuje prevoj. Dakle "svoj proces" mora
biti prepoznatljiv — PID koji je sam pokrenuo, ili vlastiti marker u komandnoj liniji.

## Računica

Tri ulaza, jedan izvod:

```
min_komad   — najmanji dio koji ima smisla dati radniku
N_radnika   — stepen paralelnosti
M           — multiplikator (dijelova po radniku)

N_dijelova  = N_radnika × M
prag        = N_dijelova × min_komad       # ispod ovoga paralelizam nema smisla
velicina    = broj_recenica / N_dijelova   # zaokruženo na multipl batcha
```

**Odluka je jedno poređenje:** `broj_recenica >= prag`? Ako nije — smanji `N_radnika`,
smanji `M`, ili radi serijski. Primjer: `min_komad` 60, 4 radnika, M=2 → prag **480**.

Konkretne vrijednosti nisu dio koncepta. Bitno je da postoji računica koja daje
**odluku** prije rada i **osnovu za provjeru** poslije njega.

### Mjera uspjeha

Prag kaže samo *smije li se*, ne *isplati li se*. Za to:

```
idealno    = serijsko_vrijeme / N_radnika   # savršena podjela, nula režije
stvarno    = izmjereno ukupno vrijeme
efikasnost = idealno / stvarno
```

**Referenca postoji:** s132 je izmjerio ~62% na 4 paralelna procesa (statička podjela,
ručno pokretanje). To je jedini broj s kojim se BPT može uporediti na prvom prolazu.
Osjetno više od 62% → dinamička podjela je platila. Isto → dobili smo samo to da se
broj aktivnih radnika drži bez čovjeka (nije malo, ali je druga tvrdnja).

### Dvije nezavisne ose

`efikasnost = f(N_radnika, N_dijelova)`

- **`N_radnika`** ograničen je **prevojem** — lokalni resurs na foxunu.
- **`N_dijelova`** balansira opterećenje, ali **množi prazan hod**: svaki dio sa
  vlastitom kaskadom plaća vlastiti prazan rep (minimum 4 faze, medijana 5).

**Simetrija:** sitnjenje istovremeno štedi prazan hod (teška rečenica više ne tjera
lake u prazne krugove) i troši ga (svaki dio plaća vlastitu potvrdu nule). Oba efekta
rastu s brojem dijelova, u suprotnim smjerovima. Koji nadjača — mjerenje, ne
rasuđivanje; čita se iz logova prvog BPT prolaza, bez posebnog eksperimenta.

Mjeri se fiksiranjem jedne ose i mijenjanjem druge.

## Šta BPT NE dira

`bb_03`, kaskade, šemu, prag, sidro, rundu. Orkestracija, ne logika — ista klasa
zahvata kao `run_faza.sh` u odnosu na `bb_03`. Zato ne može pokvariti kvalitet.

## Poznate granice

**Donja granica dijela.** Ispod dijela leži batch, a sastav batcha mijenja prevod
(s170). Dio smije biti sitan do te granice; ispod nje ne radimo isti posao brže nego
**drugi posao**.

⚠️ **Poravnanje na multipl batcha vrijedi za root, ne za kaskadu.** Gated faze ne
obrađuju cijeli dio nego samo ono što je ispod praga — od 60 rečenica u prvi krug uđe
možda 34, u drugi 21. Ti brojevi nisu multipl ničega i ne mogu biti; gate ih određuje.
Root je ipak ~90% posla (s166), pa poravnanje nije beznačajno — samo treba znati šta
garantuje.

**Prevoj krive.** Više radnika skraćuje ukupno vrijeme do tačke, poslije nje ga
produžava — granica je lokalni resurs na foxunu, ne Ollama (s164/s165). BPT ne zna
gdje je prevoj i ne traži ga; `N_radnika` je ulazni parametar, ista procjena kao danas.

**Paralelizam ne štedi Ollamu.** N radnika × X zahtjeva je NX bez obzira na način
pokretanja (s173). Štedi vrijeme, ne budžet.

## Šta se dobija

Ne vršna brzina — **održana** vršna brzina. Danas broj aktivnih procesa pada svaki put
kad neki završi a Flavio nije za tastaturom; kod BPT-a ostaje pun sam od sebe.

Posljedice koje dolaze besplatno, jer je dio **cijela kaskada** a ne jedna faza:

- Nema barijere među fazama — dio ulazi u kaskadu i izlazi iz nje sam.
- Teški dio ne kažnjava lake: broj krugova određuje najtvrđa rečenica **u dijelu**, ne
  u cijelom intervalu. Prazan hod (izmjeren 16–22%, s172/s173) se time smanjuje.
- Nusproizvod: svaki dio nosi vlastiti broj krugova → **kriva iscrpljenja po dijelu
  knjige** ispada iz logova sama, umjesto kao poseban eksperiment (s165 ju je mjerio
  namjerno).

## Otvoreno

- **Politika ponovnog pokušaja.** v0 ne vraća nepotpun dio u red. Kad se to uvede:
  odmah, na kraj reda, ograničen broj puta, ili nikad (samo prijava) — otvoreno.
- **Tri ishoda umjesto jednog.** v0 broji samo *trči / ne trči*. U stvarnosti proces
  može: **završiti** (posao potpun), **pasti** (nestao, posao nepotpun — lanac tiho
  nastavlja jer izlazni kod dolazi od `tee`, ne od Pythona; s160), ili **visjeti**
  (proces postoji, log ne raste; s172: dva procesa visila 16 i 19 min, 9 s CPU za 2h+).
  Prva dva koordinator ionako tretira isto — mjesto se oslobađa. **Visjenje je jedini
  slučaj gdje je automat lošiji od čovjeka:** zaglavljen proces se broji kao aktivan i
  drži mjesto zauvijek, pa broj stvarno aktivnih radnika tiho pada. Traži pojam
  "predugo bez znaka života"; vrijednost praga nije stvar koncepta.
- Više jezika = više koordinatora, svaki sa svojim plafonom. Ukupan broj radnika
  ostaje Flaviova procjena, kao danas.

---

*Flavio & Claude · Buchenberg · KONCEPT-BPT.md · sesija 174 · 13. avgust 2026.*
