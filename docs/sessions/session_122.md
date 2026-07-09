# Session 122 — RUNOVI analiza: 8 paralelnih grupa (dnevni + noćni run), verifikacija s121

**Datum:** 9. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Standardni onboarding proširen provjerom sporne s121 (Windows Cowork app
sesija bez pristupa memoriji/kontekstu — poznat bug u sinhronizaciji uređaja, star
više nedelja). Analiza 48 log fajlova iz dva Flaviova pozadinska paralelna runa
(4+4 grupe) preko `parse_run_logs.py` — upisano u `docs/RUNOVI.md` kao dva nova
unosa. Nula izmjena na pipeline/web kodu ili bazi — isključivo analiza i
dokumentacija (prevođenje ostaje Flaviov samostalan posao).

## Health snapshot
Na početku sesije: bb_recenice 50.624, bb_prevodi_recenica 1.513.610+ (raste u
pozadini), bb_prev_recenica 294.978+. Git na početku: buchenberg HEAD a1a9437
(s121), buchenweb HEAD 5d2f470 (s120) — oba čista, 8 `.bak_*` fajlova (buchenberg)
netaknuto van gita.

## Urađeno

### 1. Verifikacija s121 (Windows Cowork app sesija)
Flavio upozorio na kraju prošle sesije da je Windows desktop app dan ranije
ažuriran i da tamošnji Claude nije imao pristup memoriji/kontekstu iz 100+ sesija.
session_121.md nezavisno provjeren kroz git hronologiju (commitovi 6f6bb0f 15:57 →
a1a9437 16:14, oba 8. jul, redoslijed dosljedan sa sadržajem dokumenta) — sadržaj
legitiman, bez destruktivnih izmjena na kodu/bazi, ispravno je popravio checklist
proceduru (dodao čitanje KONCEPT.md/ANALIZA.md/KAKO-*/STRANICE.md/WEB-FAZA*.md
prije README-a). Prihvaćen kao pouzdan.

### 2. Analiza dnevnog runa (4 grupe, 8. jul ~07:42–19:47 UTC)
24 log fajla: k23_dehritsr nastavak (1501–2000, core-4 de/hr/it/sr) + prvi prevod
(svih 5 modela — Copy knjige uvijek idu direktno kroz pun set) za es/fr/pt/ro na
opsegu 1–500 na k22/k23/k24 (te rečenice ranije nisu imale nikakav prevod).
Upisano u RUNOVI.md (110 novih linija, čisto dodavanje). Commit `e297d07`.

Ključni nalazi: k24 (Frankenstein Copy) obrazac potvrđen treći put zaredom
(glm-5.2/mistral-large-3 skoro izjednačeni, 48.5%/47.8%, naspram ~2:1 kod ostale
tri grupe) — potkrepljuje s119 hipotezu da je uzrok sadržaj knjige (Šelijeva
proza), ne slučajnost. Agregatna brzina ~3.27 rec/min, u rasponu s119 (~3.47).
Kvalitet dosljedan (avg final 0.9652–0.9669) i na novoaktiviranim jezicima.

### 3. Analiza noćnog runa (4 grupe, 8–9. jul ~21:18 UTC–06:55 UTC, preko ponoći)
24 log fajla: k23_dehritsr nastavak (2001–2500) + prvi bazni prevod za af/nl na
k22/k23/k24. Upisano u RUNOVI.md kao drugi novi unos.

Ključni nalazi: k24 obrazac četvrti put zaredom — PRVI PUT mistral-large-3 stvarno
ispred glm-5.2 (48.1% vs 47.9%), trend se produbljuje. Metodološka korekcija:
afnl grupe imaju 2 jezika (ne 4) pa je pozicijska "rečenica/min" viša ali NIJE
direktno uporediva preko grupa — prava throughput metrika (prevoda/min =
upisano/vrijeme) pokazuje da nema stvarne noć/dan razlike u brzini (2.45–3.47 vs
prethodnih 2.76–3.76).

### 4. Alat: /tmp/aggregate_runs.py (privremena skripta, van repoa)
Pomoćna Python skripta koja čita JSON izlaz `parse_run_logs.py`, agregira preko
jezika (težinski prosjek final/komp/sudija po broju upisanih, sabira model_counts)
i generiše RUNOVI.md tabele u ustaljenom formatu. Živi samo u `/tmp` na serveru
za ovu sesiju — nije dio repoa.

## Lekcije
1. **Claude sandbox `/tmp` ≠ foxuno `/tmp`** — prvi pokušaj pisanja agregacione
   skripte preko `create_file` (Claude-ov lokalni alat) umjesto heredoc-a preko
   `foxuno:run_command` bio bi promašaj (JSON fajl je na foxuno-u). Uhvaćeno i
   ispravljeno prije izvršavanja — potvrda da ovaj stari ledger unos i dalje
   vrijedi provjeravati svaki put.
2. **Pozicijska "rečenica/min" nije uporediva preko grupa s različitim brojem
   jezika** (2 vs 4) — throughput treba mjeriti kao prevoda/min (upisano/vrijeme)
   za fer poređenje. Vrijedi za buduće RUNOVI.md unose kad se mijenja broj jezika
   po grupi.
3. **Sadržaj s121 (Windows app, bez memorije) pokazao se pouzdan** nakon
   nezavisne provjere kroz git — potvrđuje da je server/repo izvor istine (ne
   memorija), pa čak i sesija bez punog konteksta može dati validan rezultat ako
   prati protokol (prikaži→OK→izvrši, bez destruktivnih akcija).
4. **NLLB pre-fetch napomena (README, originalne knjige) pogrešno pripisana Copy knjigama** — Copy knjige (22/23/24) NIKAD nemaju NLLB-only fazu, uvijek idu direktno kroz svih 5 modela od prve rečenice. Pogrešna formulacija u RUNOVI.md i ovom dokumentu (implicirala da su es/fr/pt/ro na k22/k23/k24 "nadograđeni" sa NLLB-only na puni set) uočena i ispravljena post-sesije (Flaviova provjera). NLLB-only taktika postoji isključivo na originalnim knjigama (id 1/5/8/12/17-21), nikad na Copy (id 22/23/24).

## Otvoreno / sljedeći koraci
1. WEB-FAZA3.md — i dalje čeka Flaviovu odluku (Nivo A/B), nedirano ova sesija.
2. Prevođenje/refine ostaje Flaviov samostalan posao — očekivane dalje grupe runova.
3. `.bak_*` fajlovi (8 buchenberg) — brisanje i dalje odgođeno.
4. Razmotriti da li `/tmp/aggregate_runs.py` postane trajni `src/` alat — koristi
   se treći put (s117, s119 ručno/drugačije, sad automatizovano) — Flaviova odluka.
5. README changelog blok: s118, s119, s121 nemaju "snapshot" unos (samo u
   session_NN.md) — razmotriti kasnije da li popuniti ili nije potrebno.
6. Sitni nedirani bugovi iz s120: SR `geo_c4_p1` miješanje pisma, word cloud
   ćirilica.

## Git
- buchenberg: RUNOVI.md dnevni run — commit `e297d07` (tokom sesije). RUNOVI.md
  noćni run + README (snapshot+datumi) + session_122.md — commit slijedi.
- buchenweb: netaknuto.
- Baza: netaknuta (Flaviovi pozadinski runovi i dalje traju nezavisno).

---
*Flavio & Claude · Buchenberg · sesija 122 · 9. jul 2026.*
