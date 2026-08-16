# Analiza težine segmenata — Moby Dick (knjiga 12)

*Prilog uz session_176.md. Sve mjere iz baze (`v_pobjednici_full`, `bb_recenice`, `bb_prevodi_recenica`), ne iz logova. Sirovi izlaz prvo, tumačenje poslije.*

---

## 0. Prvo otkriće koje mijenja sve ostalo

Prije bilo kakve analize težine, provjerio sam šta se stvarno nalazi na pozicijama koje si naveo kao primjer (100–200). Rezultat:

```
100  CHAPTER 48.
101  The First Lowering.
102  CHAPTER 49.
103  The Hyena.
...
```

**Pozicije 1–488 nisu narativni tekst.** To je naslovna strana, sadržaj (135 poglavlja × 2 reda = ~270 pozicija), i "Etymology"/"Extracts" — Melvilleova zbirka kratkih citata o kitovima iz drugih knjiga. Prava proza ("Call me Ishmael.") počinje tek na **poziciji 489**.

Segment 100–200 koji si naveo kao primjer je zato skoro isključivo sadržaj — kratki naslovi poglavlja (prosjek 16 karaktera, 2.7 riječi po "rečenici"), ne prava proza. Ovo nije greška u tvom rezonovanju — bio je to razuman izbor pozicije bez znanja da tu leži struktura knjige, ne tekst. Svaka buduća analiza "težine po poziciji" za ovu knjigu mora isključiti pozicije < 489, ili će mjeriti strukturu knjige umjesto stvarne prevodilačke težine.

Sva analiza ispod koristi **poziciju > 489** (9.275 rečenica prave proze, od ukupno 9.764).

---

## 1. Tvoj originalni primjer, ispravljen

| segment | avg score | sd score | avg karaktera | avg riječi | broj rečenica |
|---|---|---|---|---|---|
| 100–200 (sadržaj, ne proza) | 0.9671 | 0.0455 | 16.0 | 2.7 | 101 |
| 500–600 (prava proza, početak Pogl. 1) | 0.9548 | 0.0348 | 119.9 | 21.7 | 101 |

Segment 100–200 ima *viši* prosječan skor od 500–600 — ali to je artefakt dužine (kratke naslove je lakše prevesti), ne dokaz da je "lakši" u smislu koji tebe zanima.

---

## 2. Težina naspram dužine rečenice — cijela knjiga (proza, poz. > 489)

| par | korelacija |
|---|---|
| dužina (karakteri) ↔ finalni_score | **−0.211** |
| dužina (riječi) ↔ finalni_score | **−0.208** |
| karakteri ↔ riječi (sanity check) | 0.994 |

Slaba do umjerena, ali stvarna negativna korelacija: duže rečenice imaju nešto niži skor.

---

## 3. Kriva težine kroz knjigu

| segment (pozicije) | avg score | avg karaktera |
|---|---|---|
| 490–952 | 0.9478 | 126.4 |
| 953–1416 | 0.9426 | 129.7 |
| 1417–1880 | 0.9375 | 126.8 |
| 1881–2344 | 0.9478 | 109.5 |
| 2345–2807 | 0.9442 | 121.6 |
| 2808–3271 | 0.9433 | 124.5 |
| 3272–3735 | 0.9440 | 90.6 |
| 3736–4199 | 0.9412 | 146.2 |
| **4200–4663** | **0.9374** | **157.5** |
| 4664–5126 | 0.9433 | 146.9 |
| 5127–5590 | 0.9490 | 133.6 |
| 5591–6054 | 0.9463 | 134.2 |
| 6055–6518 | 0.9478 | 146.0 |
| 6519–6982 | 0.9479 | 154.8 |
| 6983–7445 | 0.9465 | 127.4 |
| 7446–7909 | 0.9471 | 135.8 |
| **7910–8373** | **0.9521** | 127.8 |
| 8374–8837 | 0.9490 | 82.3 |
| 8838–9301 | 0.9499 | 111.7 |
| 9302–9764 | 0.9464 | 102.7 |

Najteži segment: **4200–4663** (najniži skor, i najduže rečenice u prosjeku). Najlakši: **7910–8373**.

---

## 4. Paradoks, testiran po jeziku

| jezik | corr sa konsenzusom | prosj. odstupanje | sd odstupanja | broj upadanja | n |
|---|---|---|---|---|---|
| sr | 0.632 | −0.0113 | 0.0408 | 52 | 4111 |
| hr | 0.622 | −0.0107 | 0.0428 | 69 | 4111 |
| sl | 0.660 | −0.0080 | 0.0373 | 59 | 4051 |
| **ro** | **0.529** | −0.0075 | **0.0523** | **95** | 3691 |
| af | 0.581 | −0.0033 | 0.0419 | 62 | 3591 |
| mk | 0.681 | −0.0031 | 0.0295 | 22 | 4011 |
| de | 0.632 | −0.0018 | 0.0308 | 23 | 4111 |
| it | 0.575 | 0.0011 | 0.0356 | 28 | 4111 |
| ja | 0.537 | 0.0023 | 0.0256 | 8 | 3591 |
| bg | 0.684 | 0.0032 | 0.0253 | 19 | 4051 |
| bs | 0.711 | 0.0042 | 0.0275 | 19 | 3631 |
| pt | 0.664 | 0.0067 | 0.0265 | 11 | 3631 |
| nl | 0.617 | 0.0089 | 0.0270 | 18 | 4111 |
| fr | 0.671 | 0.0089 | 0.0234 | 4 | 4051 |
| es | 0.697 | 0.0109 | 0.0226 | 5 | 4111 |

**ro je jedini pravi izuzetak** — najniža korelacija, najveća varijansa odstupanja, ubjedljivo najviše upadanja. **ja je poseban slučaj**: niska korelacija ali i niska varijansa — dosljedno drugačiji, ne nasumičan. **es/fr/bs/bg/mk** su najstabilniji jezici u projektu.

---

## 5. Vrijeme po rečenici, root faza (faza_id=1)

| jezik | n | prosj. sek/rečenica | korelacija dužina↔vrijeme |
|---|---|---|---|
| it | 4802 | 12.04 | 0.009 |
| sr | 4436 | 10.49 | −0.009 |
| de | 4717 | 10.16 | −0.033 |
| hr | 4856 | 10.01 | 0.001 |
| ja | 5257 | 4.61 | −0.003 |
| nl | 5897 | 4.21 | 0.019 |
| ro | 4429 | 4.05 | 0.001 |
| sl | 4772 | 3.79 | 0.008 |
| es | 5843 | 3.77 | 0.016 |
| bg | 3831 | 3.38 | −0.024 |
| bs | 3408 | 3.30 | −0.019 |
| fr | 3835 | 3.21 | −0.021 |
| pt | 3392 | 3.11 | −0.020 |
| mk | 3761 | 3.06 | −0.016 |
| af | 3420 | 2.92 | −0.024 |

Dužina rečenice skoro uopšte ne utiče na vrijeme root faze (sve korelacije ~0). sr/de/hr/it (puna pokrivenost, najstariji sloj) 2.5–3× sporiji od ostalih — vjerovatno period/uslovi rada, ne sama težina.

---

## 6. Sinteza

- Prije svake buduće analize pozicije u ovoj knjizi: isključi poz. < 489.
- Dužina rečenice objašnjava mali, stvaran dio težine (r≈−0.21), ne većinu.
- Knjiga je relativno ujednačena po težini (0.937–0.952 raspon), najteže oko poz. 4200–4663.
- Paradoks je stvaran i mjerljiv: ro dosljedno "iskače", ja je dosljedno drugačiji ali ne nasumičan, es/fr/bs/bg/mk su najstabilniji.
- Vrijeme root faze ne zavisi od dužine rečenice — zavisi od nečeg drugog (vjerovatno perioda/uslova rada).

## 7. Direktna provjera pozicionog konfaunda (6001–6400 vs 6801–7100)

Motivisano ogradom iz analize logova (parapoc krug 2/3): da li je dio izmjerenog "poboljšanja" pri prelasku na 2 radnika zapravo posljedica lakšeg teksta kasnije u knjizi?

| segment | avg score (svih 15 jezika) | avg karaktera |
|---|---|---|
| A: 6001–6400 | 0.9486 | 142.6 |
| B: 6801–7100 | 0.9506 | 132.4 |

Po svih 6 jezika iz produkcione liste (bg, es, fr, mk, nl, sl) — B je dosljedno viši od A, bez izuzetka. Efekat je stvaran ali mali (0.002 skora, 7% kraće rečenice) — ne dovoljan da objasni veličinu efekta izmjerenu u log-analizi (pad blok-B stope sa 4-7/8 na 1-3/4, pad vremena 15-20%). Broj radnika ostaje vjerovatno dominantno objašnjenje.
