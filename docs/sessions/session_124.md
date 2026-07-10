# Session 124 — Noćni razgovor: autonomija, kontekst-injection i granice prevođenja

**Datum:** 10. jul 2026.
**Učesnici:** Flavio & Claude
**Tip:** Noćni razgovor (bistrenje ideje, ne implementacija). Nula izmjena na
pipeline/web kodu ili bazi. Onboarding checklist odrađen normalno (KONCEPT/ANALIZA/
KAKO-*/STRANICE + WEB-FAZA3 provjera → README → s121–s123 → health check, sve zeleno).

## Kontekst
Flavio otvorio seriju "malih noćnih razgovora" — neformalan, opušten format za
ideje koje se motaju danima prije nego se formalizuju. Web Faza 3 ostaje dnevni
prioritet; ovo je paralelan konceptualni tok. Flavio izložio ideju u više koraka,
tražio oštru kritiku ("nađi sve negativno"), uključujući opciju potpunog odbacivanja.

## Ideja (Flaviova, kako je izložena)
Dvije povezane linije pod jednim krovom:
1. **Zamjena/automatizacija Flaviove uloge** samostalnim softverom ("agentski", ali
   sekundarno je jedan ili više agenata — bitne su uloge/funkcije u sistemu).
   Naglasak uvijek na atributu **samostalno**.
2. **Kontekst-injection u prevođenje** — po uzoru na self-refine seed, snabdjeti
   prevodioca informacijama o knjizi: NER iz originala, glavne ličnosti i njihovi
   odnosi, kratak sadržaj, žanr. Cilj: riješiti ti/vi oslovljavanje i skriveni rod
   (teško s engleskog). Prvobitna zamisao: dati kontekst i prevodiocu I sudiji.

## Kritika (Claude) i kako je ideja preživjela
Ideja NIJE odbačena — jezgro je jako, ali se suzila i izoštrila kroz prigovore:

- **Kontekst i sudiji = ruši slijepog sudiju.** Dijeljeni prior korelira prevodioca
  i sudiju; sudija prestaje ocjenjivati kvalitet, počinje nagrađivati slaganje s
  kontekstom (samoispunjavajuće); zajednička greška konteksta prolazi nedetektovana
  jer je uklonjen jedini nezavisni glas. → **Odluka: sudija ostaje slijep i fiksan.
  Kontekst SAMO prevodiocu.**
- **Isti kontekst svim modelima = konvergencija kandidata** (X-Ray: konvergencija
  izgleda kao uspjeh, ponekad je elegantniji zastoj) → manje varijacije, takmičenje
  manje informativno. Držati na umu pri dizajnu prompta.
- **Autonomija = nova crna kutija.** Ko X-zrači orkestratora? Rizik death spirala
  (DQN poglavlje): agent koji lokalno optimizuje, stabilan a funkcionalno mrtav
  (npr. uvijek najlakši/najjeftiniji run). Runaway Ollama trošak realan.
- **Ground truth konteksta.** NER iz originala = legitiman (grounding-by-evidence,
  s90). Ali odnosi/žanr/oslovljavanje = interpretacija, traži još jedan LLM (novi
  neprozirni sloj) ili internet (spojleri, pogrešno izdanje, netačno). s90 princip:
  ne vjeruj LLM tumačenju, provjeri kroz embedding evidenciju.
- **ti/vi je dinamično, ne statično** — mijenja se unutar knjige kako odnos raste
  (per-scena, ne per-knjiga). Statični prior to promašuje. Ovo je ujedno NAJVREDNIJI
  dio ideje (stvaran, dokazan MT problem na naše jezike).

## Konvergencija dvije linije (ključni nalaz razgovora)
NER+relacije preko LLM-a (već na horizontu, s90 koncept "leži") NIJE odvojen
neprimarni zadatak — to je **infrastruktura za kontekst-injection**. Relacije između
entiteta ("Holmes–Watson: bliski" → neformalno; "gospodar–sluga" → formalno) su
tačno ono što treba za ti/vi i skriveni rod. Dvije linije koje je Flavio vodio
odvojeno su jedna stvar.

## Flaviova uloga — razlaganje (rješava "izduvani balon" nesigurnost)
Flavio bira runove kao **eksperimentator**, ne raspoređivač: uvijek ima cilj
(performanse vs kvalitet), varira interval/jezik/autora, indirektno mjeri težinu
teksta, čita rezultat pa oblikuje sljedeću hipotezu. To je X-Ray meta-učenje petlja.
k24/Frankenstein anomalija uhvaćena baš zato što je gledao kroz hipotezu o težini.

Dva sloja pod "moja uloga":
- **Sloj 1 — izvršenje** (sastavi komandu, pokreni, gledaj log, prijavi): mehaničko,
  automatizabilno danas, bezopasno.
- **Sloj 2 — koji eksperiment i zašto** (hipoteza → izbor runa → čitanje protiv
  očekivanja → značenje za sljedeći): istraživanje, NE zamjenjuje se nego naoružava.

## Okvir do kojeg smo došli (za nastavak)
**Automatizuj izvršenje i tuning resursa; pojači sebe kao eksperimentatora; hrani
takmičenje boljim kandidatima, ali ne diraj mjerilo.**

Granica autonomije (oštra):
- **Autonomija nad rasporedom i resursima = DA.** 3 vs 4 procesa, 150 vs 200
  rečenica — zatvoren prostor, niska cijena greške, isti prevod bez obzira na
  putanju. Sistem smije sam predložiti I izvršiti. X-Ray kriterij mutacije ispunjen.
- **Autonomija nad kriterijem kvaliteta = NE.** Kod performansi loš izbor košta
  minute; kod kvaliteta loš izbor ulazi u bazu kao pobjednik i ostaje. "Biće ionako
  prevedeno" NE važi čim agent utiče na to ŠTA pobjeđuje.

Poboljšanje kvaliteta uz FIKSNO ocjenjivanje = poboljšaj kandidate, ne mjerilo.
Fiksni sudija nije prepreka nego zaštita (garantuje da je poboljšanje stvarno).
Tri poluge po rastućem riziku:
- **A** — kontekst prevodiocu (ti/vi + rod iz relacija); sudija slijep pošteno
  presudi. Najčišći potez. **Preduslov: izmjeriti koliko ti/vi grije SADA (baseline
  prije gradnje, isti potez kao k24).**
- **B** — refine selektivno, samo kandidati ispod praga (finalni < 0.85);
  neistestirana stavka (a) iz s100/ANALIZA.
- **C** — nova familija modela (diverzifikacija); dekorelira bazen, najskuplje ali
  najčišće naspram "ne diram ocjenjivanje".

## Otvoreno / sljedeći koraci
1. Serija noćnih razgovora se nastavlja kad Flavio ima nove ideje/pitanja u ovoj
   oblasti. Namjerno stali prije konkretne implementacije.
2. Ako se krene na polugu A: baseline mjerenje ti/vi kvaliteta PRIJE gradnje.
3. Autonomija-nad-resursima (performansni tuning agent) — zaseban, bezopasan
   pravac kad se poželi.
4. Web Faza 3 budući spisak (iz s123) i dalje stoji nezavisno.

---
*Flavio & Claude · Buchenberg · Session 124 · 10. jul 2026.*
