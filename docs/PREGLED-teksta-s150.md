# Pregled teksta — s150 (23. jul 2026)

## Svrha
Ulazni materijal za buduću sesiju "generalni predlog" — izmjena web teksta nakon
finalne kontrole projekta (s150). Ovaj dokument samo popisuje nalaze, ništa nije
mijenjano na osnovu njega u ovoj sesiji.

## Vodeći kriterijum za reviziju (Flavio, s150)
Čitalac web teksta je pametan, ali nema naš kontekst iz projekta — ne Claudeov
nivo znanja, ne Flaviov. Svaki pojam koji se prvi put pojavi na stranici mora biti
objašnjen na licu mjesta, u samom tekstu. Key Concepts kartice pomažu, ali nisu
zamjena za objašnjenje u tekstu.

## Nalazi koji traže akciju

### 1. Zamrznuta pretpostavka "tačno 2 faze" u web tekstu
Mjesta: `about.html` (L53 kod-dijagram), `index.html` (proza L49-92), `nav.js`
(`index_how_desc2`, `index_pillar_refine`, `index_pillar_winner`,
`about_p_refine1/4` × 5 jezika), `reader.html` X-Ray legenda (L392-393, EN-only).
Stvarno stanje: sistem sad ima do 6 faza (1 root + gated 4/5/6, plus istorijske
2/3). Mehanika prikaza (`reader.html` fazaNums regex) je N-faza-safe od s135 —
problem je isključivo u statičnom proznom tekstu.
Dodatno: `about_p_refine4` opisuje pre-s144 refine dizajn ("dva modela, samo
najviša temperatura") — ne pominje tri gated faze, različite promptove po fazi,
ni prag `seed_score<0.95`.

### 2. NER/DocRE nema top-level README sekciju
Dokumentovan raspršeno kroz tabele skripti/baze i hronologiju sesija (§5, §7, §9),
za razliku od Pipeline (§4) i Weba (§10) koji imaju svoje naslove. Nije greška po
sebi, strukturna asimetrija — vrijedi razmotriti dodavanje sekcije.

### 3. limits.html — "236 coverage gaps"
Tačan broj fluktuira (bio 252 u s136, sad 236) — traži ručno ažuriranje svaki put.
Predlog (Flavio): ukloniti tačan broj, ostaviti opisnu tvrdnju.

### 4. limits.html — "two generations... measurably different stylistic signature"
Izvor: s137, analiza Flaviovih noćnih prevoda (stari model par neočekivano jak na
Moby Dick/Romeo&Juliet — gušći književni stil). Session dokument eksplicitno kaže:
"korelacija zabilježena, uzrok nije dokazan (nema mjerenja stila samog)" i
Flaviov tadašnji zaključak: "izbor modela je nametnut (Ollama retirement), ne
strateška odluka — ne traži se dalja akcija." Riječ "measurably" tvrdi više nego
što je ikad izmjereno. Ne ugrožava koncept "svejedno koji model" (to je o
pipeline-arhitekturi, ne o identičnosti stila).

## Nalazi koji su provjereni i NE traže akciju
(zapisano da se ne ponavlja ista istraga)

- **index.html "Model patterns are book-dependent"** — tačno, zasnovano na README
  tabeli "Temperatura pattern po jezičnoj grupi". README eksplicitno kaže
  "statistički trend, ne pravilo — uvijek koristi sve 4 kombinacije". Ne
  protivriječi principu da se postavke ne mijenjaju ručno po knjizi/jeziku —
  naprotiv, objašnjava zašto je uvijek-sve-4-kombinacije ispravna strategija.
- **index.html "Batch processing requires careful fallback"** — temeljno i dobro
  dokumentovano (README §4, posebna sekcija), nije izolovan nalaz.
- **index.html "Metric ≠ quality" (DeepL/MiniLM primjer)** — stvaran nalaz iz
  s28-31 (maj 2026); direktan uzrok prelaska sa MiniLM na e5-large kao embedder.
  DeepL nikad nije ušao u produkciju, bio je referentna tačka za taj test.
- **"Sudija je i igrač i mjerni instrument" (limits.html)** — sudija ostaje
  doslovno SAMO sudija (nikad ne prevodi, invarijanta). Formulacija je
  metaforička: sudijina ocjena direktno određuje pobjednika (stvarno ~92% po
  s146 auditu), pa nije neutralni posmatrač; istovremeno je jedini instrument
  kojim mjerimo kvalitet, bez nezavisne provjere. Tvrdnja je tačna, formulacija
  u tekstu možda treba pojednostaviti za čitaoca bez konteksta.

## Napomena o self-refine (Flavio, s150)
Suština self-refine za web tekst je jednostavna: **prompt sa pivot rečenicom** —
trenutni pobjednik se daje modelu kao nagovještaj/sidro, model pokušava da ga
poboljša ostajući gramatički unutar prostora. Istorija dolaska do ovog rješenja
(uključujući napuštenu "random" fazu) je nevažna za prezentaciju.

---
*Flavio & Claude · Buchenberg · pregled teksta s150 · 23. jul 2026.*
