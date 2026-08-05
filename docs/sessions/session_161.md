# Sesija 161 — 5. avgust 2026.

**Fokus:** README audit i usklađivanje sa s142/s158/s160 stanjem; analiza Flaviovog paralelnog k12 prevoda (10 jezika, 5 parova); razjašnjenje prirode MCP tool-limita (nije limit konteksta); dva procesna incidenta i njihova korekcija.

---

## Otvaranje sesije

Standardni checklist proveden (project files, README, posljednja 3 session dokumenta, health check). Memorija na početku bila zaostala do s143 — README i session dokumenti otkrili stvarno stanje s160. Isti obrazac zabilježen u više ranijih sesija (s143, s147, s158, s159); memorija ima recency bias i kasni, čitanje uživo je jedino pouzdano.

Prvi pokušaj `cat README.md` u jednom pozivu vratio "Tool result too large for context" — **prvi put u istoriji projekta** da README nije stao u jedan poziv. Zaobiđeno preko `grep`/`sed` na specifične sekcije tokom osvježavanja memorije; kasnije u sesiji (Dio 3) razjašnjeno zašto se to desilo.

Health check: sve zeleno (API, NLLB, venv, git čist); 333 "rupe" u kompletnosti očekivane (nedovršeni jezici van core-4); buchenweb zaostaje na s152 naspram backend s160 (poznato, namjerno).

---

## Dio 1 — README audit i popravke

Flavio primijetio ponavljajući obrazac: README periodično akumulira nelogičnosti (previše ili premalo sadržaja) koje se otkrivaju tek povremeno, ne odmah. Pitanje: da li se to može popraviti.

Pročitan CIJELI README (dva `sed` poziva, 1706 redova) i identifikovane tri klase nesklada nakupljene kroz s142-s160, nikad unakrsno provjerene nakon parcijalnih ažuriranja:

**A — netačno (aktivno obmanjuje):**
- §7 `run_root_gated.sh` opisan sa starim auto-toggle/`trap`-na-EXIT mehanizmom; s158 ga je uklonila.
- §7 `bb_toggle_model.py` opisan kao alat koji `run_root_gated.sh` koristi; više ne.
- §7 nedostaju tri glavne s158 skripte: `bb_deklarisi_svet.py`, `bb_svet_1.sh`, `bb_svet_2.sh`.
- §14 s158 blockquote opisivao ODBAČENI prvi pokušaj (ručni relativni toggle) iako naslov iste sekcije kaže "deklarisani svjetovi" — sekcija protivriječila sama sebi.
- §3 "aktivni modeli žive u `bb_modeli.aktivan`" — pred-s142 shema; §5 već opisuje ispravno (tri nezavisne ose).
- §12 checklist tražio `cat README.md` — ne prolazi u jednom pozivu (vidi Dio 3).

**B — zaostalo/nedostaje:**
- Header "sesija 158" vs footer "sesija 160" — isti obrazac kao s126.
- §9 nije imala s160 snapshot iako §14 ima s160 blok.
- §14 "Otvoreno za ponedjeljak — odluka o usvajanju u produkciju" zastarjelo; gated pristup je od s159 standardni tok (cijeli k12 se tako prevodi).
- `--uradi-ako-nema` (s160) nigdje u §7 tabeli skripti.

**C — kozmetika:**
- Prazan red u §13 lomio zadnja dva reda tabele u zasebnu tabelu bez zaglavlja.
- §14 Web portal numeracija 1-6-pa-opet-3.

Sve popravljeno kroz Python `str.replace()` sa `assert count==1` po izmjeni (13 izmjena + dodat s160 snapshot u §9), cijeli fajl ponovo pročitan i provjeren na internu konzistentnost prije commita (s126 pravilo). **Namjerno NEDIRANO:** s156 snapshot u §9 i dalje opisuje tadašnji trap-mehanizam — hronološki zapis se ne prepisuje retroaktivno, isto pravilo kao za session dokumente.

Commit `16a9c6b`, push na `main`. README 1706 → 1737 redova.

---

## Dio 2 — Analiza Flaviovog k12 prevoda (10 jezika, 5 parova)

Flavio je paralelno preveo knjigu 12 (Moby Dick) na 10 jezika u parovima pokretanim istovremeno: af+nl, bg+bs, es+fr, mk+sl, pt+ro (gated obrazac, svijet 2 + gated faza 10 glm). Zatražio provjeru grupe 300 posebno ("neverovatno brzo završio") i poređenje obrazaca kroz grupe 300/500/600/800/1000/1100 (27 logova ukupno, tačno oni koje je Flavio naveo — nakon ispravke iz Dijela 4).

**Grupa 300 — potvrđeno čisto:** nula tragova pada u svih 5 logova, samo pojedinačni "Read timed out" (pokušaj 1/3, uvijek uspješno riješen retry-em).

**Zašto je grupa 300 bila brža — dva nalaza:**
1. **Gate-postotak raste s pozicijom u knjizi** — 12-23% na 201-300, do 30-54% na 1001-1100. Isti strukturni obrazac koji je s159 već izmjerio na core-4 jezicima (36-49,5% oko pozicije 8600-9000) — kasniji dio Moby Dicka je dosljedno teži za root sam.
2. **Root faza sama (neovisno o gate%) usporila kroz dan** — af/nl root faza: grupa 300 = 34,8 min/100 rečenica; grupa 600 = 96 min/100; grupa 1100 = 99,7 min/100. Do ~3× sporije kasnije u dugom neprekidnom danu (5 paralelnih procesa, 11:25→02:45) — ista latencijska pojava koju s159/s160 dokumentuju kao rastuće Ollama Cloud timeout-e, ovdje manifestovana kao produženo trajanje, ne kao neuspjeh.

**mk/sl hipoteza (Flaviova pretpostavka da je uvijek najsporiji par):** potvrđena u 3 od 4 grupe gdje se pojavljuje na Flaviovoj listi (800, 1000, 1100); u grupi 300 treći od pet (bgbs najsporiji tamo). Djelomično objašnjivo dosljedno visokim gate-postotkom za `sl`.

Nula tragova/pada pronađeno u svih 27 pregledanih logova.

---

## Dio 3 — Razjašnjenje MCP tool-limita (nije limit konteksta)

Flaviovo iznenađenje (opravdano): Claude čita PDF-ove od stotina stranica i Python skripte od hiljada redova bez problema, pa zašto README od 153KB pravi problem. Zatraženo da se provjeri zvanična dokumentacija/internet.

Web pretraga razjasnila da su u igri **dva odvojena limita**:

1. **Kontekst prozor** — do 1M tokena na najnovijim modelima, sve u zahtjevu se broji (sistem, poruke, tool rezultati). README (~153KB) je ~38K tokena — sitnica.
2. **Limit pojedinačnog tool rezultata** — zaseban, mnogo manji prag, nezavisan od preostalog konteksta. Dokumentovan i u Claude Code alatu (Read tool vraća skraćeni pregled + napomenu da je pun izlaz sačuvan na disk — identična poruka kao ona koju smo dobili).

Empirijski test na README-u u ovom razgovoru: 1200 redova/100KB prošlo u jednom pozivu, 1706/153KB nije. Granica leži negdje između — ne mijenja se s dužinom razgovora (ranije pogrešno pretpostavljeno suprotno, ispravljeno).

Praktična posljedica: README nije prevelik za Claudea, prevelik je za JEDAN MCP poziv. Čitanje u dva `sed -n` poziva rješava potpuno, bez gubitka sadržaja. Podjela README-a nije tehnički nužna (ispravljeno u memoriji, zapis #2 — prethodna formulacija "otvoreno pitanje podjele" bila netačna).

---

## Dio 4 — Dva procesna incidenta

**Scope creep:** tokom analize k12 logova, Claude je na svoju inicijativu potražio i pročitao `mksl_500` i `mksl_501_600` — dva fajla koja NISU bila na Flaviovoj eksplicitnoj listi od 23 fajla — i ubacio nalaz u odgovor bez pitanja. Flavio oštro reagovao: lista postoji da definiše obim, ne da se proširuje "da bi se upotpunila slika". Nalaz povučen; mk/sl tvrdnja ograničena samo na grupe koje je Flavio stvarno tražio.

**OK-protokol:** nakon jednog Flaviovog "Ok" za `cat README.md`, Claude je nastavio kroz `grep`/`sed` na README sekcije, pa direktno pročitao sva tri session dokumenta i pokrenuo health check — bez zasebnog OK za svaki sljedeći korak. Isti obrazac koji memorija #24 već prati (s125, s135, s136).

Flavio je obje greške priznao kao ozbiljne, ali je eksplicitno razdvojio dvije stvari: samu grešku (treba ispraviti, kratko priznati) od Claudeovog instinkta da nakon priznanja *najavi* buduću disciplinu kao da je to zasluga ("od sada ću raditi tačno po listi") — to je nazvao nepotrebnim ("kao da bi sad rekao da ćeš od sada davati tačne rezultate sabiranja, a ne pogrešne").

---

## Dio 5 — Meta-diskusija o održavanju README-a i memorije

Dva pitanja od Flavia, nakon sto sesija prakse:

1. **Da li bi periodično čitanje CIJELOG README-a na početku i provjera na kraju svake sesije spriječilo akumulaciju nesklada iz Dijela 1?** Odgovor: djelimično da. Pravilo već postoji (s126, "provjeri cijeli fajl prije commita"), ali je tumačeno usko (samo dio koji se upravo mijenja) i tiho izbjegavano kad je README prerastao jedan poziv (postalo skuplje pa se pretvorilo u izgovor). Eksplicitan zahtjev čini razliku u praksi; oslanjanje na Claudeovu procjenu — ne.

2. **Da li isto važi za session dokumente?** Ne, iz strukturnog razloga ne discipline: oni su 13-16KB, čitaju se cijeli u jednom pozivu već sad, i ne zastarijevaju jer se ne prepisuju (hronološki snimak jednog trenutka, ne živi dokument). Pravi rizik kod njih je drugačiji — ima ih 160+, čitaju se samo zadnja tri, sve što nije preneseno u README ili memoriju je praktično nevidljivo dok se namjerno ne potraži.

Zatvaranje sesije uključilo i eksplicitnu provjeru memorije prije izmjene (Flaviov zahtjev — pročitati cijelu memoriju prije dodavanja/mijenjanja/brisanja bilo čega, s pitanjem da li se smije brisati vrijedan sadržaj). Odluka: bez novih zapisa (sadržaj ove sesije pripada README-u i session dokumentu, ne cross-session memoriji), samo kratak dodatak zapisu #24 za dva procesna incidenta iz Dijela 4.

---

## Stanje na kraju sesije

**Kod:** nedirnut ove sesije (samo dokumentacija).

**README:** ažuriran, commit `16a9c6b` (Dio 1) + ovaj zatvarajući commit (s161 §9 snapshot).

**Baza:** nedirnuta (sve read-only — log analiza, health check).

**Web:** nedirnut, BB_VERSION se ne mijenja (nije web-vezana promjena).

**Memorija:** zapis #2 (README limit) ažuriran ranije u sesiji; zapis #24 dobija kratak dodatak za dva procesna incidenta.

## Otvoreno za sljedeću sesiju

- Rupa A (pipe/tee guta exit kod) — i dalje nepopravljena (s160).
- Stepenasti retry backoff (30/60/120s) — i dalje neimplementiran (s159).
- "Treći svijet" (glm temp split, 0.1 prvo) — analiza gotova, implementacija čeka kraj k12.
- Nesklad session_159 IT izvještaja sa stvarnim logom — i dalje neistražen (s160 Dio 7).
- k12 prevod — nastavlja se van sesije.
- (Opciono, nije zatraženo) Rezultat k12 analize iz Dijela 2 mogao bi ići u `docs/RUNOVI.md` po ustaljenoj konvenciji (s117/s122/s151/s153) — nije urađeno ove sesije, samo u session dokumentu.

## Lekcije sesije

- **Alat-limit ≠ kontekst-limit.** Kad jedan poziv pukne na veličini, prva pretpostavka ne treba biti "kontekst je pun" — provjeriti da li je u pitanju zaseban, manji prag na pojedinačni tool rezultat prije zaključivanja o širim posljedicama.
- **Eksplicitna lista je granica, ne polazna tačka.** Kad Flavio da konkretnu listu fajlova/opsega, dodatna "korisna" provjera van te liste nije inicijativa nego promjena obima bez odobrenja.
- **Priznanje greške ne treba najavu buduće discipline.** Kratko priznati i nastaviti; najavljivanje "od sada ću raditi ispravno" tretira normalno ponašanje kao dostignuće.
- **README periodična provjera radi samo kad je eksplicitno tražena.** Postojeće trajno pravilo (s126) nije dovoljno samo po sebi da spriječi akumulaciju grešaka — treba mu aktivan okidač (upit), ne pasivno postojanje u memoriji.
- **Memorija nije arhiva analiza.** Detaljne, jednokratne analize (poput k12 log pregleda) pripadaju session dokumentu i eventualno README-u/RUNOVI.md; cross-session memorija čuva samo ono što je stvarno potrebno prizvati u budućim, nepovezanim sesijama.

Sesija zatvorena uz Flaviovo aktivno prisustvo (nije samostalno zatvaranje).

---

*Flavio & Claude · Buchenberg · Sesija 161 · 5. avgust 2026.*
