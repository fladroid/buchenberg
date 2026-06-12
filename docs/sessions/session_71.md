# Session 71 — Mobilna navigacija i dark mode: dijagnoza, popravke, lekcije

**Datum:** 12. jun 2026.
**Autor:** Flavio & Claude

---

## Epizoda 0: Fable 5 pitanje — studija pogrešnog odgovaranja

Flavio je pitao zašto se Fable 5 model sam prebacio na Opus 4.8 i ne da se vratiti.

**Pokušaj 1 (pogrešan):** Claude pretražio web, dobio tačne činjenice, ali složio
pogrešan narativ: "promo period je istekao". Nije uporedio dva datuma koja su mu
bila pred očima (danas 12. jun < rok 22. jun). Sinteza plauzibilne priče umjesto
verifikacije aritmetike.

**Pokušaj 2 (pogrešan):** Nakon Flaviove korekcije, Claude skočio na sljedeću
pogodnu hipotezu (iscrpljen usage limit) — iako je Flavio u PRVOJ poruci napisao
da je imao dovoljno prostora u 5-satnom i sedmičnom intervalu. Nije čitao pažljivo.

**Pokušaj 3 (tačan, tek nakon Flaviovog guranja):** Ponovljena pretraga →
Fable 5 ima sigurnosne klasifikatore koji automatski preusmjeravaju ~5% sesija
(cyber/bio/chem teme) na Opus 4.8. Sadržaj radnog konteksta (serveri, pipeline)
vjerovatno okinuo fallback. By design, ne greška.

**Napomena o modelima (Flavio):** pogrešan odgovor dao je Sonnet, objašnjenje
pogrešnog odgovora dao je Fable. Subjektivno: Opus i Fable superiorniji od
Sonneta (objektivno tačno po benchmarcima) — ali ova epizoda pokazuje da
razlika ne pomaže ako model preskoči verifikaciju. Plan: testirati Sonnet
s većim effort parametrom.

**Zajednički imenitelj sve tri greške:** podaci ili alat su bili dostupni,
a korištena je pretpostavka. Pogrešan odgovor izrečen samouvjereno navodi
na pogrešnu akciju — gori je od "ne znam".

---

## Urađeno

### 1. Checklist (standardni)
- README (s69), sessions 68–70, health check: sve zeleno
- 38.333 rečenica, 118.438 prevoda (+4.108 od s70), 8.452 pobjednika; git čist (65541e8)
- Prevodi bez pobjednika = NLLB pre-fetch sa slobodnim resursima (namjerna strategija,
  N-ti put objašnjeno — vidi Lekcije)
- NLLB keš sada 1.3B (bio 600M)

### 2. Mobilna navigacija — hamburger meni (NOVO)
**Problem:** na telefonu se ne vide menu tačke. Uzrok: `@media (max-width:700px)
{ #bb-nav { display:none; } }` — nav se skriva, zamjena nikad nije napravljena.
- nav.js: ☰ dugme + toggle `open` klase + zatvaranje na klik linka
- CSS: mobile dropdown (apsolutno pozicioniran, vertikalna lista)
- Mobile kompaktnost: manji logo, manja lang dugmad, veći burger tap target
- Radi: portrait → burger, landscape (>700px) → puni nav

### 3. Dark switch — dupli listener (BUG, popravljen)
**Problem:** toggle radio samo na geometry/art. Uzrok: 7 starijih stranica imalo
SOPSTVENI legacy theme listener (iz vremena prije nav.js centralizacije) →
dva listenera na istom dugmetu → tema se prebaci i odmah vrati → neto nula.
- Uklonjen legacy listener sa: index, about, books, learn, nlp, reader, stats
- 3 varijante bloka (learn: function/this; reader: $ helper; nlp: + redraw)
- nlp.html: redraw word clouda/networka sačuvan kroz MutationObserver na data-theme

### 4. Pogrešno urađeno → popravljeno: dupla heredoc egzekucija
**Greška:** prvi nav.js heredoc izvršen DVAPUT (MCP retry?) → `const burger`
deklarisan 2× → SyntaxError → cijeli IIFE pao → header nestao, BB_NAV undefined
→ SVE stranice visile na "Loading" (PC i telefon). Privremeno srušen cijeli portal.
**Popravka:** dedup skripta s assertima; verifikacija grep count-om.
**Nova obavezna praksa:** nakon SVAKE heredoc izmjene odmah `grep -c` verifikacija
na fajlu — `print('OK')` iz skripte NIJE dokaz da je fajl ispravan.

### 5. Mobilni cache — dijagnoza bez trajnog rješenja
- Apache ne šalje Cache-Control za js/css → heuristički keš (agresivan na mobilnom)
- Test po Flaviovoj ideji: bump BB_VERSION u footeru kao indikator svježine — radi
- `.htaccess` rješenje predloženo, NIJE implementirano → otvoreno

### 6. Responsive: reader.html (popravljen) i about.html (djelimično)
- **reader:** `#sidebar { display:none; }` na mobilnom — isti anti-pattern kao nav.
  Uklonjen → sidebar se slaže iznad sadržaja. Radi.
- **about:** inline grid `1fr 280px` bez klase → media query ga nije hvatao.
  Dodano `#about-layout` + media override + overflow-x za pre/tabele.
  Djelimično bolje (infoboxi vidljivi), ali sadržaj i dalje preširok —
  vjerovatno lineage SVG dimenzionira grid ćeliju. Flavio: "ne bih više dirao."

### 7. nav.js → s71 (12 Jun 2026)

---

## Pogrešno urađeno — sažetak

| # | Greška | Posljedica | Popravka |
|---|--------|-----------|----------|
| 1 | Fable odgovor: sinteza bez verifikacije datuma | Pogrešan savjet korisniku | Ponovna pretraga (nakon 2 guranja) |
| 2 | Druga hipoteza bez čitanja korisnikovog inputa | Drugi pogrešan savjet | Korekcija od Flavija |
| 3 | Heredoc izvršen 2×, bez verifikacije fajla | Portal srušen ("Loading") | Dedup + nova praksa verifikacije |

## Lekcije (za buduće sesije)

1. **Verifikacija prije sinteze:** datum, broj ili provjerljiva tvrdnja se
   verifikuje PRIJE formulisanja odgovora, ne poslije prigovora.
2. **Čitati korisnikov input:** Flavio je informaciju o limitima dao u prvoj
   poruci; ignorisana je u korist pogodne hipoteze.
3. **`grep -c` poslije svakog heredoca** — fajl je istina, ne output skripte.
4. **NLLB pre-fetch podsjetnik:** višak prevoda bez pobjednika = namjerno
   korištenje slobodnih resursa; ne objašnjavati ponovo, piše ovdje.
5. **Flaviov zaključak:** portal NIJE "mobile first" — desktop-first dizajn,
   mobilno koristiv uz poznate nedostatke. Greške su bile u konceptima starim
   deceniju+ (navigacija, responsive) — otkrivene tek pri prvoj stvarnoj
   mobilnoj upotrebi, ne pri razvoju.

---

## Planirano u ovoj sesiji, NIJE urađeno

- **Sentence Fingerprints** (zadnji art.html eksponat) — sesija potrošena na mobile fixeve
- **Cache-Control / `.htaccess`** za js/css — dijagnoza gotova, implementacija otvorena
- **about.html mobile** — potpuni fix (SVG/grid širina) svjesno odgođen

## Sljedeće (kumulativno)

- art.html: Sentence Fingerprints; Sound v2 (model→timbre, chord indikator)
- Cache-Control za js/css (.htaccess ili Apache config)
- Mobile-first redizajn — opcija, ne obaveza
- Prijevodi: hr/sr/it/de → s350; mk/bg → s51–100
- about.html i18n; learn.html nove igre; web fajlovi u git
- Eksperiment: Sonnet s većim effort parametrom (Flavio)

---

## Git

commit s71
