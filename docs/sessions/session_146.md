# Session 146 — Audit mjernog aparata; nova stranica "Limits"

**Datum:** 20. jul 2026.
**Fokus:** Analiza Flaviovog noćnog gated refine runa (k20/k21) prerasla u X-Ray
samog sistema ocjenjivanja — rezolucija instrumenata, stvarni uticaj komponenti,
slijepe tačke cosinusa. Rezultat objavljen kao nova stranica portala `limits.html`.

## Zdravlje na početku
50.624 rečenice · 1.617.141 prevoda · 302.168 pobjednika. BB_VERSION s140 (web),
buchenberg na s145 (commit 0cdf363). 236 poznatih rupa, 26 `.bak` fajlova (backlog).

## Zdravlje na kraju
Korpus NEPROMIJENJEN (nula pipeline poziva ove sesije — sve READ-ONLY).
Web: nova stranica + nav.js, BB_VERSION s140 → **s146** (buchenweb 921efe6, grana master).
Dokumenti: `docs/ANALIZA.md` (nova sekcija), `docs/STRANICE.md`, `session_146.md`.

---

## 1. Analiza gated refine runa (k20 Dracula, k21 Flatland, de/hr/it/sr, 1–1000, faze 4/5/6)

**Flaviova uvodna sumnja** — da stara faza 2 (stari par, k20 poz. 1–100, k21 poz. 1–200)
iskrivljuje rezultate ranih rečenica — **provjerena i uglavnom oborena**: stari refine
prebacio je preko praga samo 6 (k20) + 21 (k21) rečenicu od 1.200. Niže gate-otvaranje
u ranim poglavljima (5,5–11,8% vs 33% dalje) dolazi od toga što su rane rečenice same
po sebi lakše (93% / 83,5% već iznad 0,95 BEZ refine-a), ne od kontaminacije.

⚠️ **PROCESNI PROPUST (Flaviova kritika, opravdana):** Claude je od te usputne ograde
napravio 90% analize umjesto da analizira ono što je Flavio tražio — rezultate novih
gated faza. Ograda spomenuta u prolazu NIJE predmet analize.

**Glavni rezultat (nakon preusmjeravanja):**

| mjera | vrijednost |
|---|---|
| gate otvoren | 2.337 / 8.000 (29,2%) |
| gated refine pobjeđuje kad je otvoren | 93,4% |
| prosječna delta vs seed | +0,047 |
| klon-stopa | 0,7% (bilo 16,25% prije s135) |

Snažnija potvrda gate dizajna nego s145 Hound uzorak (79%).

## 2. Audit mjernog aparata — glavna nit sesije

Nit je krenula iz jednog pitanja: je li +0,047 stvaran pomak ili kretanje kroz šum.
Odgovor je tražio mjerenje samih instrumenata, što do sada nikad nije rađeno.

**(a) Dobitak nosi isključivo sudija.** Po fazi: Δsudija +0,047…+0,060,
Δcosinus **−0,004…−0,010** (cosinus PADA u sve tri gated faze).

**(b) Cosinus u praksi ne glasa.** sd sudija 0,2065 vs sd cosinus 0,0277 na 1,56M
prevoda → formula `0,4×kompozitni + 0,6×sudija` rangira **~8% cosinusom, ~92% sudijom**.
Korelacija instrumenata 0,171.

**(c) Instrumenti su PRECIZNI — prag šuma 0,003.** Mjereno na prirodnom eksperimentu
u bazi: 212.443 grupe gdje su različiti modeli/faze dali doslovno identičan tekst,
ocjenjivan odvojeno. 98,74% dobilo identičnu ocjenu, medijan raspona 0,0000.
⚠️ **Obara s137 nalaz** ("17/30 klonova različit score") — n=30 bio premali.
Posljedica: rasipanje unutar grupe kandidata (0,19–0,29) je STVARNA razlika, ne šum.
+0,047 je 16× iznad praga šuma.

**(d) Cosinus ima strukturne slijepe tačke.** Embedder je namjerno višejezičan →
ne može vidjeti da prevod nije napravljen. Neprevedeni fragment: cosinus **0,99**
(2.784 sl., 0,17%). Latinično `w/y` u ćirilici: **0,95** (1.466 sr prevoda, 0,92%).
Slomljena gramatika uz očuvane ključne riječi: **0,97**.

**(e) Sudijine nule NISU kvar.** Provjereno u `bb_08_sudija.py`: `parse_ocjene()`
vraća `None` → `continue` bez upisa; `call_sudija()` radi `raise`. Nijedna nula nije
sentinel. Provjera na uzorku (de/hr/it/sr): nule padaju na neprevedeni francuski/engleski,
pokvarenu transliteraciju, i besmislen hrvatski ("Ne zatežete li ga zanimljivim?").
Sudija je bio u pravu, cosinus u krivu.

**(f) ZATO NE STANDARDIZOVATI KOMPONENTE.** Claude je predlagao z-score/rank
normalizaciju da cosinus dobije "stvarnih 40%". Izmjereno: promijenilo bi 24,98%
pobjednika — u smjeru slijepih tačaka iz (d). Nesklad 8/92 trenutno ŠTITI izbor.
Prijedlog povučen prije bilo kakve izmjene.

**(g) Granica koju mjera ne pokriva — jedini pravi negativan nalaz.**
Sudija mjeri tečnost; književnost je namjerno krši. Abbott *Flatland* de:
autorova namjerna složenica `SOMETHING-WHICH-YOU-DO-NOT-AS-YET-KNOW-A-NAME-FOR-...`
izbrisana refine-om i zamijenjena glatkom rečenicom — **nagrađena s +0,157, najvećom
deltom u uzorku**. Naturalness raste najbrže od tri ose (+0,061…+0,078).
Flaviov doprinos: kineska pjesma 5×4 kao oštriji primjer — struktura IZNAD rečenice
ne postoji u pipeline-u jer je jedinica rečenica (pogađa Romea i Juliju, Flatland,
svaku ilustrovanu knjigu).

**Čitanje 24 refine para očima (de/hr/it/sr):** refine ne uljepšava — popravlja
stvarne greške (izgubljen subjekat, pogrešno značenje "move"≠"preseliti se",
slomljeno slaganje roda, izostavljeno "grown into manhood"). Sudija u pravu u
velikoj većini.

## 3. Nova stranica portala — `limits.html`

Flaviova odluka: publikovati sve negativno. Ostvarenje "Failure modes kao filozofija"
stavke iz X-Ray dokumenta.

- **`limits.html`** (EN-only tijelo, svjestan izuzetak): I. šta aparat ne vidi (4 tačke),
  II. šta sistematski kažnjavamo (Abbott slučaj), III. šta ne postoji u našem svijetu
  (sve iznad rečenice, kontekst), IV. šta znamo da je nepotpuno (236 rupa, dvije
  generacije modela, sudija kao igrač i instrument).
- **`nav.js`**: stavka "Limits" iza "Stats", ključevi `limits`/`limits_title` ×5 jezika,
  BB_VERSION s140→s146.
- Nijedan model se ne imenuje (s115 princip poštovan — sve po ulozi).
- Scoped `<style>` blok u stranici (infoboxovi kao sidebar na about.html) da se ne
  dira dijeljeni `buchenberg.css` (nlp.html ima infoboxove, nisu provjereni).
- Tri iteracije nakon Flaviovog browser testa: dodan `<div id="bb-footer">`,
  infoboxovi premješteni iz toka teksta u desnu kolonu (float je propadao kroz footer),
  širina/razmak usklađeni s about.html.

---

## Odluke (Flavio)
- Publikovati negativne nalaze kao zasebnu stranicu, ne kao sekciju u about.
- Zadržati sav sadržaj drafta bez skraćivanja.
- EN-only tijelo, meni i naslov prevedeni.
- Infoboxovi u desnoj koloni, složeni jedan ispod drugog.
- Kanonski nalazi trajno u `docs/ANALIZA.md`.

## Lekcije
1. **Usputna ograda korisnika nije predmet analize.** Flavio je spomenuo moguć uticaj
   stare faze 2 kao ogradu; Claude je od toga napravio 90% odgovora i propustio
   analizirati ono što je traženo. Čitati ŠTA je pitano, ne za šta se ima podatak.
2. **Pet uzastopnih hipoteza predstavljenih kao nalazi = loš metod.** Podaci se
   cijeli dan nisu mijenjali; mijenjala se Claudeova priča o njima (veto → otkaz
   sudije → sentinel nule → prepisan šablon → sve oboreno). Flavio je s pravom rekao
   da je nesigurniji nego na početku. **Razdvojiti hipotezu od nalaza PRIJE iznošenja,
   ne poslije obaranja.**
3. **Mali uzorak može trajno pogrešno usmjeriti projekat.** s137 nalaz o
   nedeterminizmu sudije (n=30) stajao je devet sesija kao "poznata činjenica";
   n=212.443 pokazao suprotno.
4. **Provjeriti stvarne rečenice prije predlaganja izmjene formule.** Prijedlog
   standardizacije komponenti djelovao je matematički besprijekorno i bio bi štetan.
   Otkriveno tek gledanjem konkretnih prevoda, ne agregata.
5. **Sudija je pouzdaniji nego što je Claude pretpostavljao u svakom koraku.**
   Sve sumnje na njegov otkaz — oborene podacima.
6. **`float:right` element bez kontejnera propada kroz footer** — infoboxovi u toku
   teksta rade samo ako ih nešto zaustavi; about.html ih drži u grid koloni.
7. **Claude je poslao nedovršenu/pogrešnu komandu** (kirurške zamjene s `display:none`
   trikom, poruka odsječena). Uhvaćeno prije izvršenja i povučeno — ali dokaz da
   "prikaži pa čekaj OK" hvata i Claudeove greške, ne samo rizične operacije.

## Otvoreno / za sljedeću sesiju
- **`bb_sr_cirilica.py`** — `w/y/q/x` nisu u preslikavanju (nisu u srpskoj latinici),
  ostaju usred ćirilice. Pogađa 1.466 prevoda (0,92% srpskog). Popravka mala, nije urađena.
- **Key Concepts kartice za `limits.html`** — stranica nije u `CONCEPT_PAGES`.
  Prijedlog: *Goodhart's law* (doslovno ova stranica u jednoj rečenici),
  *Untranslatability*, *Construct validity*.
- **Flaviov permutacijski eksperiment** (4/5/6 u svih 6 redoslijeda na istim rečenicama)
  — traži rundu ili klon-trik (s145 §4.9); mjerio bi je li lanac refine-na-refine
  komutativan. Nije pokrenut.
- **it/2524** — jedini slučaj gdje sudija djeluje pogrešno (nulu dobio ispravan oblik,
  0,900 nepostojeći "corrisponduto"). Neprovjeren.
- **ANALIZA.md treba ponovo uploadovati u project knowledge** da izmjene budu vidljive
  na početku sljedeće sesije.
- Export skripte (s142) i dalje nisu pokrenute na živi `/var/www/buchenberg/data`.
- Git: `.bak_*` backlog nepromijenjen (26 fajlova).

---
*Flavio & Claude · Buchenberg · Sesija 146 · 20. jul 2026.*
