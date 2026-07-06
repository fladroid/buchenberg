# Session 116 — Tri referentna dokumenta: STRANICE, i18n procedura, Key Concepts procedura

**Datum:** 6. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Flaviovo opažanje nakon 100+ sesija — Claude, kao tekstualni AI bez pristupa vizuelnom prikazu, ne može pouzdano znati mapiranje stranica/menija/naslova niti kompletnu i18n/Key Concepts proceduru bez eksplicitne provjere svaki put. Tri konsolidovana dokumenta nastala direktno iz tog uvida. Uz to: verifikacija `run_pipeline.sh`/`run_refine.sh` poziva za knjigu 23.

---

## Health snapshot (početak)
- bb_recenice: 50.624 · bb_prevodi_recenica: 1.393.170 · bb_prev_recenica: 271.578
- Git ulaz: buchenberg 49eabd2 (s115), buchenweb cd1e82e (s115). BB_VERSION s115.
- Health check čist. 7 necommitovanih `.bak_s114` fajlova (namjerno van gita).

## Šta je urađeno

### 1. STRANICE.md
Tabela HTML stranica × menu tačka × naslov, generisana iz stvarnog stanja servera (`nav.js` NAV_LINKS + NAV_I18N, `<title>` tagovi, `<h1>` pretraga po svih 9 stranica) — ne iz pamćenja. **4 otkrivena nesklada:** `art.html` naslov "Art" hardkodovan, nema `_title` i18n ključ (jedina stranica bez prevoda naslova); `books.html` `<title>` i dalje "Books" iako je `<h1>` "Library" (nedovršen rename iz s72); `stats.html` menu "X-Ray Stats" ≠ naslov "X-Ray Statistics"; `index.html`/`reader.html` nemaju fiksan naslov (hero brend+tagline / dinamički po knjizi). Commit buchenberg `40c90b7`.

### 2. KAKO-JeziciUI.md
Konsolidovana referenca za i18n tekst iz README §"Web how-to" + sesija 61, 77–82, 108, 114, 115. Pokriva: arhitekturu (NAV_I18N = izvor istine, HTML hardkod = no-JS fallback koji JS uvijek pregazi, uključujući EN), `reader.html` kao namjerni izuzetak, checkliste za dodavanje/izmjenu/brisanje ključa, proceduru za potpuno novu stranicu, tehničku metodu (Python heredoc + `assert s.count(old)==1` + pravila za anchor, uključujući strukturnu zamku unutar `NAV_I18N` bloka koja je u s79 slomila cijeli sajt), verifikaciju (nema `node` na serveru — browser test je jedina prava potvrda), i ledger od 10 poznatih bagova s uzrocima i fixovima (s61→s115). Commit buchenberg `0233015`.

### 3. KAKO-KeyConcepts.md
Ista vrsta reference za Key Concepts/Wikipedia kartice. Prije pisanja, mehanizam verifikovan direktno iz `nav.js` koda (ne iz sažetaka prošlih sesija) — otkriveno: renderovanje centralizovano u `nav.js` (`CONCEPT_PAGES` niz, `CONCEPT_TITLES` override mapa, `#bb-footer` insertion point), kartice su jednojezične (EN, bez i18n), naslov sekcije hardkodovan string koji se nikad ne prevodi. **Najvažniji nalaz:** `.catch(function(){})` tiho guta svaku grešku — slomljen `concepts.json` briše Key Concepts kartice na SVIM stranicama, svim jezicima, bez ikakve vidljive greške. Dokumentovano: struktura JSON-a, Flaviovo pravilo (samo postojeći EN wiki članci), checkliste, obavezna JSON validacija (`json.load`) nakon svake izmjene, ledger 4 slučaja. **Usput ispravljena netačna pretpostavka** iz sažetka prošle sesije — `books.html` NIJE poseban kod, ide kroz isti mehanizam kao ostale stranice, samo sa override naslovom i knjigama umjesto pojmova. Commit buchenberg `de88c89`.

### 4. Verifikacija run_pipeline.sh / run_refine.sh poziva (knjiga 23)
Flavio predložio pozive za k23 (Big Four Copy, de/hr/it/sr, 1–100) bez `nohup`/pozadinskog izvršavanja. Oba skripta pročitana u cjelini (prepisana u s114, pamćenje nepouzdano). Potvrđeno: sintaksa argumenata ispravna (`--knjiga/--jezici/--od/--do`, bez `--faza` — hardkodovano interno). **Nedostaje `nohup ... &`** — bez toga poziv blokira, nerealno za dužinu posla (100×4×5 modela). Imenovana nijansa iz s102: vanjski `time` ispred `nohup bash ./run_refine.sh` eksplicitno identifikovan kao suvišan/krhak za ove skripte (skripte već imaju `time` interno) — protivriječi opštem README pravilu "uvijek time u nohup", ali ta nijansa je specifična i dokumentovana. Predložen ispravljen poziv (`PYTHONUNBUFFERED=1 nohup ./run_pipeline.sh ... > log 2>&1 & echo "PID: $!"`), bez izvršavanja — čeka Flaviovu potvrdu. Naglašen redoslijed: refine tek nakon pipeline (seed zavisnost — k23 trenutno 0 prevoda; Ollama Cloud serial ograničenje).

## Sljedeće
1. Pokrenuti ispravljeni pipeline poziv za k23 (de/hr/it/sr, 1–100) kad Flavio potvrdi, refine poslije
2. `stats.html` `stats_reading_note` (isti tretman kao Home/reader) — otvoreno iz s115
3. Mrtvi i18n ključevi cleanup (`index_funnel_*`/`lbl_*`/`cta_*`) — otvoreno iz s115
4. Copy knjige puni runovi (id 22/23/24) — otvoreno
5. s107/s108 otvoreno (brojači faze 2, stats dvije tabele)

## Stanje na izlazu
- buchenberg: 3 nova commit-a (`40c90b7`, `0233015`, `de88c89`) — `docs/STRANICE.md`, `docs/KAKO-JeziciUI.md`, `docs/KAKO-KeyConcepts.md`
- buchenweb: netaknut, BB_VERSION ostaje s115
- Baza: netaknuta

---

*Flavio & Claude · Buchenberg · session 116 · 6. jul 2026.*
