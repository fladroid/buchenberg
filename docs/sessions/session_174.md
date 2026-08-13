# Sesija 174 — BPT: koncept paralelnog prevođenja

**Datum:** 13. avgust 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Konceptualni rad — BPT (Buchenberg Parallel Translate), dinamička podjela posla
**Tip sesije:** čisto konceptualna — nijedan prevod, nijedna izmjena baze, nijedna izmjena skripti

---

## 1. Onboarding

Prošao po §12, koraci 0–4:

- **Korak 0** — referentni dokumenti: `KONCEPT.md`, `ANALIZA.md`, `KAKO-JeziciUI.md`,
  `KAKO-KeyConcepts.md`, `KAKO-BrisanjePrevoda.md`, `KAKO-NovaFaza.md`, `STRANICE.md`
  (1.023 linije, jedan poziv)
- **Korak 1** — project files (napomene v1/v2, METHOD, ANALIZA, X-Ray v3b SR/EN)
- **Korak 2** — README, **cijeli** (2.435 linija)
- **Korak 3** — `session_171.md`, `session_172.md`, `session_173.md`
- **Korak 4** — `health_check.py` preko `nohup`

### Greška na startu (ponovljena iz s173)

README sam počeo čitati u opsezima `sed -n '1,900p'` + `sed -n '901,1706p'` — **brojevi
iz memorije, ne iz fajla.** To je tačno ona greška koju je s173 §8 zapisao i zbog koje je
§12 dopunjen pravilom "prvo `wc -l`, pa tri bloka". Fajl ima 2.435 linija; nedostajalo je
~730 (§10–§15, uključujući sam protokol i sljedeće korake).

Uhvaćeno tek pri čitanju `session_173.md` — dakle **ledger je proradio, ali sa zakašnjenjem
od tri koraka.** Ispravljeno u istoj sesiji (`sed -n '1707,$p'`), i korak 0 je poslije toga
odrađen kako §12 nalaže.

**Pouka koja ide dalje:** pravilo zapisano u README-u ne pomaže ako se README čita po
zapamćenim brojevima. Jedina odbrana je `wc -l` **prije** prvog `sed`-a, mehanički, bez
izuzetka.

---

## 2. Snimak zdravlja (početak sesije)

| Mjera | Vrijednost | Naspram kraja s173 |
|-------|-----------|--------------------|
| Rečenice | 50.624 | = |
| Prevodi | 2.073.330 | **+4.683** |
| Pobjednici | 405.812 | **+800** |
| Rupe | 357 | = |

Rast je iz Flaviovih runova između sesija. **Rupe nepromijenjene** — dakle nema novih
qwen-potpisa; rast dolazi iz konfiguracija koje su po modelu već kompletne.

Sve zeleno osim dvije poznate stavke: rupe (gotovo sve faza 1 / penzionisani modeli,
prio-2 odluka iz s136) i buchenweb koji zaostaje 5 sesija (BB_VERSION s168).

Dvije nove rupe malog reda, vrijedne imenovanja jer nisu iz retired ere:
- k12/de faza 10 `glm-5.2@0.1` — 875/882 (rupa 7)
- k22/hr faza 2 `mistral@0.8` — 150/156 (rupa 6)

Obje su rep prekinutog poziva, ne struktura.

Ollama: sva 4 modela odgovaraju. Git `main` na `2a03c0b`, radno stablo čisto osim 16
`.bak`/sandbox fajlova (namjerno necommitovani).

---

## 3. Šta je urađeno

Jedan nastali dokument: **`docs/KONCEPT-BPT.md`** (182 linije), nastao u pet prolaza kroz
razgovor. Nema koda, nema izvršavanja, nema brojeva u produkciji.

### 3.1 Problem

Flavio danas pušta više paralelnih procesa prevoda i ručno dopunjava kad neki završi.
Smeta mu da neki dijelovi traju znatno duže od drugih.

Formalno: kod **statičke** podjele ukupno trajanje je `max(dijelova)`, ne prosjek — jedan
spor dio drži ostale kao taoce. Kod **dinamičke** podjele (više dijelova nego radnika,
mjesto se popunjava čim se oslobodi) trajanje teži prosjeku, a rep se svede na jedan
posljednji dio. Isti princip kao granule u Oracle Parallel Query — odatle i Flaviova
polazna analogija.

**Polazna premisa (Flavio, eksplicitno):** više kraćih paralelnih procesa traje kraće od
jednog dužeg — potvrđeno u praksi. Bez toga cijela vježba nema smisla.

**Dopuna (Claude):** tvrdnja nije linearna nego ima **prevoj**. Do prevoja svaki dodatni
proces skraćuje; poslije njega procesi se otimaju o isti lokalni resurs i ukupno vrijeme
raste — a to se ne primijeti, jer svaki pojedinačni poziv i dalje uredno završi. Granica je
**lokalni RAM na foxunu, ne Ollama** (izmjereno s164/s165).

### 3.2 Uloge

**Koordinator** prima **knjiga + jezik + interval**. Priprema posao, dijeli ga i nadgleda.
Ne prevodi. Posao mu je **neproziran** — ne zna za faze, sidro, prag ni rundu.

**Odluka: dispečer, ne planer.** Koordinator ne bira šta je sljedeći posao iz baze; dobija
ga od Flavija. Time je izbjegnuto cijelo otvoreno pitanje "šta je sljedeće za raditi"
(otvoreno od s149) i koncept se mogao zatvoriti u jednoj sesiji.

### 3.3 Radnik — Flaviova precizacija koja je promijenila nacrt

Claudeov prvi nacrt tretirao je radnika kao **entitet**: `radnik = pokreni(...)`, tabela
aktivnih, radnik se vraća po novi posao. Flavio je to ispravio:

> Radnik je linux proces koji trči u pozadini, identifikovan svojim PID-om. Predstavlja
> izvršenje jedne kaskadne skripte s parametrima. **Radnik ne postoji ukoliko ne radi.**
> Ne tražimo slobodnog radnika — brojimo da li je zadati broj procesa zauzet.

Posljedica je brisanje cijele jedne strukture: koordinator **ne vodi tabelu radnika**, vodi
red dijelova i jedan broj. Nema "slobodnog radnika", ima **slobodnog mjesta**. Korak 4 iz
prvobitnog opisa ("worker ode kod koordinatora i traži još") se okreće — radnik ne ide
nikome, on nestane, a koordinator to vidi kao pad brojača i pokrene **novi** proces.

Isti ishod, ali **bez ijedne linije komunikacije radnik→koordinator.** Mrtav radnik ne može
zaboraviti da se javi.

### 3.4 Usvojeni algoritam (Flaviov, doslovno)

Flavio je opisao šta stvarno radi rukom — i to je ispalo jednostavnije od nacrta:

```
pokreni do N
petlja:
    prebroj aktivne
    ako < N i ima posla → dopuni do N
    ako nema posla     → izađi iz petlje
    čekaj              → nazad na prebroj
čekaj da svi završe
prijavi logove
```

Tri razlike naspram nacrta, sve u smjeru pojednostavljenja:
- **Nema dodjele** — nigdje "daj ovom radniku ovaj dio", samo "dopuni do N"
- **Nema praćenja ko je šta radio** — ispravnost to ne traži jer je upis idempotentan po
  tačnoj 7-kolonskoj konfiguraciji; nepotpun dio se prosto ponovo pusti
- **Pražnjenje je vlastiti korak**, ne uslov petlje

**Flaviova odluka za v0:** ne radimo ni identifikaciju greške ni oporavak. v0 živi u
idealnom svijetu.

### 3.5 Dio = cijela kaskada (ne jedna faza)

Ključno pitanje sesije: je li dio komad **jedne faze** ili **cijele kaskade**?
Flavio: cijela kaskada.

**Dobitak:** barijere nema uopšte. Da je dio bio faza, radnik koji je gotov čekao bi
posljednjeg prije sljedeće faze — rep bi se vratio na višem nivou. Ovako dio ulazi u
kaskadu i izlazi iz nje sam. Zavisnost među fazama je ionako **po rečenici** (sidro faze 16
za rečenicu X je pobjednik faze 12 te iste rečenice), ne po opsegu.

**Drugi dobitak:** teški dio ne kažnjava lake. Danas broj krugova određuje najtvrđa
rečenica u **cijelom** intervalu, pa se lake voze u prazno (prazan hod izmjeren 16–22%,
s172/s173). S dijelom kao kaskadom, broj krugova određuje najtvrđa rečenica **u dijelu**.

**Cijena:** gate-nula postaje tvrdnja o dijelu, ne o opsegu — uže i tačnije, ali mjereno na
manjem uzorku, dakle bučnije. X i procenat iznad praga nisu isti brojevi kao dosad.

**Besplatan nusproizvod:** svaki dio nosi vlastiti broj krugova → **kriva iscrpljenja po
dijelu knjige** ispada iz logova sama. s165 ju je morao mjeriti namjerno.

### 3.6 Računica

Flaviova intuicija: `broj_recenica / (broj_workera × 2)`, dijelova dvostruko više nego
radnika zbog balansiranja; komadi po mogućnosti multipl batch sizea.

Formalizovano (konkretne vrijednosti **nisu** dio koncepta):

```
N_dijelova = N_radnika × M
prag       = N_dijelova × min_komad      # ispod ovoga paralelizam nema smisla
velicina   = broj_recenica / N_dijelova
```

Odluka je jedno poređenje: `broj_recenica >= prag`. Primjer: `min_komad` 60, 4 radnika,
M=2 → prag **480** (Flavio je u razgovoru rekao 490, ispravljeno i prihvaćeno).

**Mjera uspjeha** — jer prag kaže samo *smije li se*, ne *isplati li se*:

```
efikasnost = (serijsko_vrijeme / N_radnika) / stvarno_vrijeme
```

**Referenca postoji:** s132 je izmjerio ~62% na 4 paralelna procesa (statička podjela,
ručno pokretanje). To je jedini broj s kojim se BPT može uporediti na prvom prolazu.
Osjetno više → dinamička podjela je platila. Isto → dobili smo samo održavanje broja
aktivnih bez čovjeka (nije malo, ali je druga tvrdnja).

---

## 4. Nalazi i lekcije

**(1) Sitnjenje ima dvosmjernu cijenu — simetrija praznog hoda.** Više dijelova *štedi*
prazan hod (teška rečenica ne tjera lake u prazne krugove) i istovremeno ga *troši* (svaki
dio plaća vlastitu potvrdu nule — minimum 4 faze, medijana 5). Oba efekta rastu s brojem
dijelova, u suprotnim smjerovima. Koji nadjača je **mjerenje, ne rasuđivanje**, i čita se
iz logova prvog BPT prolaza bez posebnog eksperimenta.

Praktična posljedica: multiplikator M=2 je dobar izbor upravo zato što je **mali**. Kod
M=4 ili M=8 balansiranje bi bilo bolje ali bi se prazni repovi umnožili.

**(2) Poravnanje na batch vrijedi za root, ne za kaskadu.** Sastav batcha mijenja prevod
(s170), pa dio treba biti multipl batcha. Ali gated faze ne obrađuju cijeli dio nego samo
ono ispod praga — od 60 rečenica u prvi krug uđe možda 34, u drugi 21. Ti brojevi nisu
multipl ničega i **ne mogu biti**; gate ih određuje. Root je ~90% posla (s166), pa
poravnanje nije beznačajno — samo treba znati šta garantuje.

**(3) Cijepanje po opsegu je disjunktno na svakoj osi.** Dva dijela iste knjige i jezika ne
dijele nijednu rečenicu, dakle ni sidro, ni gate, ni red u `bb_prevodi_knjige`.
`already_done()` je po rečenici. Rizik nije u koliziji — Flavio potvrdio iz prakse.

**(4) Brojanje procesa mora biti usko.** `pgrep` po imenu kaskade uhvatio bi i ono što je
Flavio pustio rukom, ili procese drugog koordinatora za drugi jezik. Koordinator koji broji
tuđe procese kao svoje sam sebe koči; koji ih ne broji, prekoračuje prevoj. "Svoj proces"
mora biti prepoznatljiv — vlastiti PID ili marker u komandnoj liniji.

**(5) BPT ne dira nijednu postojeću komponentu.** Ne `bb_03`, ne kaskade, ne šemu, ne prag,
sidro ni rundu. Orkestracija, ne logika — ista klasa zahvata kao `run_faza.sh` u odnosu na
`bb_03`. **Zato ne može pokvariti kvalitet prevoda.**

**(6) Pravi dobitak nije vršna brzina nego održana vršna brzina.** Danas broj aktivnih
procesa pada svaki put kad neki završi a Flavio nije za tastaturom. Kod BPT-a ostaje pun
sam od sebe. Paralelizam i dalje **ne štedi Ollamu** (N×X = NX, s173) — štedi Flaviovo
vrijeme.

**(7) Claudeova dvije precijenjene ograde.** Konstruisao sam problem oko "više koordinatora
za više jezika = nekontrolisan zbir radnika", što Flavio u praksi rješava bez muke (i sam
je rekao da mu je svejedno pušta li isti jezik s različitim opsezima ili različite jezike).
Ograda je bila protiv problema koji ne postoji. Slično sam u konceptu držao pojam
"dodjele" duže nego što je trebalo. **Obrazac: gradim strukturu prije nego što provjerim da
li problem koji rješava postoji u Flaviovoj praksi.**

---

## 5. Stanje na kraju

- `docs/KONCEPT-BPT.md` — **182 linije**, nov fajl
- Provjerena interna konzistentnost cijelog fajla nakon svih prolaza; nađene i ispravljene
  tri nesaglasnosti između starijeg i novijeg sloja (sekcija "Uloge" je i dalje govorila o
  "dodjeljuje", "Šta je problem" o "radnik povlači", "Otvoreno" citirao `red.vrati(dio)`
  koje više ne postoji)
- **Baza netaknuta. Skripte netaknute. Web netaknut → BB_VERSION ostaje s168.**
- Nijedan prevod nije pokrenut u ovoj sesiji

---

## 6. Sljedeći koraci (BPT)

1. **Čitanje postojećih logova** — `min_komad` i `M` su za sada procjena od oka, a logovi
   ranijih paralelnih runova već nose stvarna trajanja po opsegu. Ne mjerenje, samo čitanje
   onoga što postoji. Najjeftiniji sljedeći korak.
2. **v0 implementacija** — tanka petlja iznad postojećih kaskadnih skripti; radnik je poziv
   `run_kaskadaN.sh` s uskim `--od/--do`.
3. **Prvi prolaz s mjerenjem efikasnosti** naspram reference 62% (s132).
4. **Šuma problema** (odloženo svjesno): tri ishoda umjesto jednog (završio/pao/visi),
   politika ponovnog pokušaja, prag za "predugo bez znaka života".

Otvoreno iz s173 ostaje netaknuto i ima prednost po Flaviovoj procjeni: rep (ne košta
nijedan poziv), `top_p`/`top_k` kao osa u šemi, sonda skaliranja Ollame, threading u sudiji.

---

*Flavio & Claude · Buchenberg · sesija 174 · 13. avgust 2026.*
