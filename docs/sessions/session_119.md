# Session 119 — 4 paralelne grupe: analiza brzine/kvaliteta + Ollama Pro tier ispravka

**Datum:** 8. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Flavio je pustio 4 paralelna pipeline toka (k23-dehritsr nastavak 1001–1500,
k22/k23/k24-bgbsmksl 1–500) da testira performanse i kvalitet novog para
(mistral-large-3:675b + glm-5.2) uz novi Ollama Pro nalog. Claude analizirao logove,
upisao u `docs/RUNOVI.md`, i ispravio zastarjelu README pretpostavku o serijskom
izvršavanju.

---

## Health snapshot

| | Početak sesije | Kraj sesije |
|---|---|---|
| bb_recenice | 50.624 | 50.624 |
| bb_prevodi_recenica | 1.451.830 | 1.461.410 |
| bb_prev_recenica | 282.778 | 284.538 |

Git ulaz: buchenberg e70fb49 (s118 zatvaranje), buchenweb cd1e82e (s115, nepromijenjeno
ovaj session — web Faza 2 i dalje čeka). Uncommitted: 8 `.bak_*` fajlova, namjerno van
gita (poznato).

## Urađeno

**Analiza 4 paralelne grupe** (log fajlovi iz `logs/`, parsirani `parse_run_logs.py`):
- Grupa 1: k23 (Big Four Copy) de/hr/it/sr, opseg 1001–1500 (nastavak s117/s118 baze)
- Grupa 2: k22 (Hound Copy) bg/bs/mk/sl, opseg 1–500
- Grupa 3: k23 (Big Four Copy) bg/bs/mk/sl, opseg 1–500
- Grupa 4: k24 (Frankenstein Copy) bg/bs/mk/sl, opseg 1–500

Prije toga, poseban solo segment k23-dehritsr 501–1000 (bez konkurencije) analiziran
zasebno — poslužio kao baseline za poređenje brzine solo vs. paralelno.

**RUNOVI.md** — dva upisa: (1) solo segment 501–1000, (2) puni izvještaj sve četiri
paralelne grupe s tabelama identifikacije/vremena i kvaliteta/pobjeda po grupi, plus
cross-grupa zapažanja.

**README — tri ispravke:**
- §Paralelno izvršavanje: uklonjena zastarjela tvrdnja "jedna sesija u isto vrijeme,
  striktno serijski" — Flavio je prije 2+ sedmice nadogradio Ollama nalog na Pro tier,
  paralelni pozivi su odavno norma (i sa starim i sa novim modelima, do 5 paralelnih
  tokova sa starim).
- §10: novi blok "Backup raspored" (foxuno 01:00–03:00, balsam 03:00–08:00 CET/CEST).
- §15: nova sekcija "Radni ritam" (Flaviovo zapažanje o degradaciji 16–18h CEST).
- §13 Poznati bugovi: dodan red — base64 nepouzdan za prenos teksta na foxuno, uvijek
  heredoc.

## Ključni nalazi

- **Agregatna brzina paralelizma:** 4 konkurentna toka ≈3.47 rečenica/min zbirno,
  naspram ≈0.924 rečenica/min solo (k23-dehritsr, mjeren prije/poslije početka
  paralelnih grupa) → faktor ≈3.77×, blizu linearnog skaliranja. Per-model vremena po
  rečenici ne pokazuju usporavanje zbog konkurencije. **Ovo NIJE otkriće** — Flavio je
  Pro tier upgrade i paralelizam već koristio 2+ sedmice; brojka samo potvrđuje ono što
  je već znao.
- **k24 (Frankenstein Copy) odstupa u distribuciji pobjeda:** mistral-large-3 42.45%
  naspram glm-5.2 55.5% (u ostale tri grupe odnos je dosljedno ~2:1 u korist glm).
  Avg_final za k24 i najniži od četiri grupe (0.9599). Vjerovatno sadržaj (Šelijeva
  gotska proza 1818), ne efekat paralelizma.
- **Veličina batcha naspram brzine** (Flaviovo pitanje): samo n=20 dosljedno sporiji
  (fiksni trošak po pozivu `bb_03` amortizovan preko manje rečenica). Od 40 naviše nema
  monotonog trenda — 100 NIJE sweet spot; varijacija (0.83–1.33 rec/min) dominantno
  dolazi od Ollama Cloud opterećenja u datom trenutku.

## Lekcije (greške ispravljene tokom sesije)

1. **Neprecizna formulacija** — nazvao k23-dehritsr tok "sekvencijalnim" na način koji
   je zvučao kao da tvrdim da ne trči paralelno s ostale tri grupe, iako je upravo taj
   segment (1001–1500) trčao konkurentno. Greška u izražavanju, ne u analizi — brojevi
   su bili tačni.
2. **Paralelizam pogrešno predstavljen kao "otkriće"** — trebalo je prvo provjeriti da
   li je Flavio već znao/namjeravao paralelno izvršavanje (nadogradio je na Pro tier
   prije 2+ sedmice), umjesto da ga predstavim kao novi nalaz. `conversation_search`
   je pokazao da je ista greška napravljena i u sesiji od 29. juna (Claude tada
   tretirao paralelne procese kao grešku za ispravljanje, oslanjajući se na zastarjeli
   README).
3. **UTC/CEST konfuzija** u prvom draftu RUNOVI.md unosa (pisao "17:20 CET" za UTC
   vrijeme) — uočeno i ispravljeno prije upisa na server.
4. **Base64 refleks** umjesto heredoc-a pri pokušaju prenosa teksta na foxuno — pravilo
   je postojalo u memoriji, ali nije primijenjeno na vrijeme; sad zapisano trajno u
   README §13.
5. **Nisam prepoznao Flaviovo "hvala, javljam se" kao signal za zatvaranje sesije** —
   odgovorio razgovorno umjesto da primijenim zatvaranje-ritual (METHOD.md §3) odmah.
   Svih pet grešaka dijeli isti obrazac: primjena zapisanog pravila kasni za trenutkom
   kad treba da se primijeni.

## Otvoreno / sledeći koraci

1. Refine faza (2) za k22/k23/k24 copy knjige
2. Puni runovi preostalih jezika (af/es/fr/nl/pt/ro) za copy knjige, ako se žele
   kompletne na svih 14 jezika
3. Web Faza 2 — implementacija svih 9 stranica (s118 priprema, još nedirnuto)
4. `.bak_s114`/`.bak_s118` fajlovi i dalje namjerno van gita (8 fajlova)

## Git

- **buchenberg:** 4 nova commita ovaj session — `5133250` (RUNOVI solo segment),
  `ae766b5` (README Pro tier), `0a8f1b2` (RUNOVI 4 grupe + README backup/ritam),
  `8124a19` (README base64 bug). HEAD: `8124a19`.
- **buchenweb:** bez izmjena ovaj session — HEAD i dalje `cd1e82e` (s115).

---

*Flavio & Claude · Buchenberg · sesija 119 · 8. jul 2026.*
