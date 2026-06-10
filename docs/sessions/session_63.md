# Session 63 — Fable 5, Borgesova biblioteka i kompas

**Datum:** 10. jun 2026.
**Autor:** Flavio & Claude

---

## Urađeno

### 1. Checklist (standardni)
- Memorija osvježena (s60→s62 stanje)
- README pročitan (V3, ažuriran do s61)
- Session dokumenti 60, 61, 62 pročitani
- Health check: sve zeleno — 38.333 rečenica, 97.486 prevoda, 8.352 pobjednika
- Flatland it/de: 500/500 pobjednika (kompletno za s1–s500)
- Moby Dick i Romeo: 200 prev / 50 pobj — NLLB pre-fetch, nije anomalija

### 2. Prelazak na Claude Fable 5
- Flavio prebacio model sa Sonnet 4.6 na Fable 5 (Mythos-klasa, izašao 9.6.2026)
- Potvrđeno: promjena modela NE gubi kontekst — kontekst je vezan za konverzaciju
- Relevantno za Buchenberg: 1M token context window, bolji fokus u dugim
  sesijama s puno tool outputa, #1 na coding/agentic benchmarcima
- Memorijski gap između sesija: arhitekturalno nepromijenjen — checklist
  ostaje neophodan. Ali: Fable 5 bolje koristi eksterne bilješke (3x veći
  benefit od file-based memorije nego Opus 4.8) → session_NN.md dokumenti
  i napomena sada vrijede VIŠE nego prije
- Protokol komandi ostaje nepregovoriv bez obzira na sposobnosti modela

### 3. Diskusija: Borgesova Babelska biblioteka i Buchenberg

**Tehnička interpretacija:** Basile (libraryofbabel.info, 2015) ne skladišti
knjige — invertibilni PRNG, adresa=seed, tekst se deterministički računa.
Biblioteka postoji samo kao funkcija. Beskonačna struktura u konačnom prostoru.

**Veza s Buchenbergom (Claudeovo mišljenje):**
- Embedding prostor (e5-large, 1024D) JESTE Babelska biblioteka, kontinuirana:
  svaka moguća rečenica na svakom jeziku ima koordinate u tom prostoru
- Razlika: Borgesova biblioteka je ~100% šum, bibliotekari umiru tražeći
  Katalog kataloga. Buchenberg radi obrnuto — 5 modela generiše kandidate
  BLIZU tačke značenja, cosinus+sudija mjere ko je najbliži
- **Buchenberg = bibliotekar s kompasom** — ono što Borgesovi likovi nikad
  nisu imali

**X-Ray veza:**
- Najvrednija pouka biblioteke je negativna: u njoj postoji SVE i zato ne
  vrijedi NIŠTA. Informacija bez selekcije je šum
- Vrijednost nije u sadržaju nego u indeksu — funkciji koja razlikuje smisao
  od besmisla
- Zato sudija nosi 60% težine: scoring funkcija je vredniji artefakt od
  samih prevoda
- Ovo je srž principa "važniji je put od cilja" — gradimo kompas, ne biblioteku
- Abbott (Flatland, već u korpusu) i Borges su intelektualni rođaci — obojica
  o zatvoru referentnog okvira

**Odluka:** implementacija biblioteke prevazilazi okvire projekta, ali kao
teorijska kartica na geometry.html savršeno sjeda → novi TODO

---

## Sljedeće

- **geometry.html: kartica "The Library and the Compass"** — embedding prostor
  kao Borgesova biblioteka s navigacijom; veza s Flatlandom (Abbott u korpusu)
- Transformers.js integracija za pravi 1024D cosinus (iz s62)
- Proširenje prijevoda: hr/sr/it/de → s350, mk/bg → s51–100
- README sekcija 9 zastarjela (s54) — osvježiti pri sljedećoj većoj izmjeni

---

## Git

(commit nakon snimanja)

---

## Dopuna: Wittgenstein, Chomsky, Borges — lineage

### Dvije teorije značenja = dvije istorije MT
- Rani Wittgenstein (Tractatus 1921): značenje = forma/korespondencija →
  Chomsky (1957, univerzalna gramatika) → rule-based MT (Georgetown 1954,
  interlingva) → krah: ALPAC 1966
- Kasni Wittgenstein (Istraživanja 1953): značenje = upotreba, jezičke igre,
  porodična sličnost → Firth 1957 ("company it keeps") → distribuciona
  semantika → word2vec 2013 → Attention 2017 → NLLB 2022

### Buchenberg = kasni Wittgenstein kao mjerni instrument
- cosinus = kvantifikovana porodična sličnost
- back-translation testira preživljavanje ZNAČENJA, ne forme
- sudija/naturalness = kompetencija u jezičkoj igri ciljnog jezika
- Ironija: NLLB cross-lingual transfer je slaba potvrda Chomskog (duboka
  zajednička struktura), mehanizam je čisto distribucioni (Wittgenstein) —
  obojica djelimično u pravu, Buchenberg radi na presjeku

### Borges u timelineu (1939–1944, procjep između ranog i kasnog W.)
- "Pierre Menard" (1939): identična forma, različito značenje po kontekstu —
  značenje=upotreba 14 godina PRIJE Istraživanja; definicija problema prevođenja
- "Babelska biblioteka" (1941): informacija bez selekcije je šum (v. gore)
- "Funes pamtilac" (1942): savršeno pamćenje bez apstrakcije = overfitting;
  embedding je vrijedan jer je KOMPRESIJA
- Poenta: Buchenberg prevodi književnost tehnologijom čije je probleme
  najpreciznije formulisao književnik. Abbott daje geometriju, Borges
  semantiku, Wittgenstein most.

### Odluke (implementacija)
- **about.html: sekcija "Lineage — od Tractatusa do Buchenberga"** — D3
  timeline: 1921 Tractatus → 1939-44 Borges → 1953 Istraživanja → 1954
  Georgetown / 1957 Chomsky+Firth → 1966 ALPAC → 1990 IBM stat. MT →
  2013 word2vec → 2017 Attention → 2022 NLLB → 2026 Buchenberg;
  horizontalan, na mobilnom vertikalan
- **geometry.html: kartica "Meaning as Use"** — veza teorije s UMAP
  scatterom (klasteri = porodične sličnosti); kartica "Library and the
  Compass" spominje i Menarda
