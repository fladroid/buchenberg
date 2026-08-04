# Sesija 160 — 4. avgust 2026.

**Fokus:** Istraga sinoćnjeg (3.avg) pada tokom prevođenja k12 (Moby Dick, glm-5.2@0.1, gated faza 10) — zašto skripta ne oporavlja sama, šta se tačno gubi kad pukne, i zašto ponovno pokretanje ne pokupi automatski sve nedostajuće. Rezultat: nova, minimalna opcija `--uradi-ako-nema` (čist label u logu, bez promjene logike), testirana na stvarnom incidentu, dokumentovana. Dvije strukturne rupe identifikovane i eksplicitno ostavljene NEPOPRAVLJENE (Flaviova odluka o obimu ove sesije).

---

## Otvaranje sesije

Standardni checklist proveden (project files, README uživo pošto je prevelik za direktan prikaz — head/tail umjesto cat, poslednja 3 session dokumenta, health check). Memorija na početku bila zaostala do otprilike s143/s147 (fragment); README/session dokumenti otkrili stvarno stanje **s159** (2. i 3. avgust). Korpus na početku: 50.624 / 1.905.033 / 360.832.

## Dio 1 — Razumijevanje retry mehanizma (diskusija, bez izmjena koda)

Flavio zatražio objašnjenje sinoćnjeg incidenta (Dio 9 iz session_159.md — timeout eskalacija na batch=20). Kroz razgovor, korak po korak:

1. **`ollama_chat(max_retries=3, wait=30)`** — 3 pokušaja, fiksnih 30s, za SVAKI HTTP poziv (batch ili single).
2. **Batch poziv** (`prevedi_batch` i sl.) HVATA izuzetak (try/except), vraća `None`, poziva se fallback na pojedinačne (`prevedi_single`) pozive.
3. **Single fallback NEMA try/except** — ako i tu sva 3 pokušaja propadnu, izuzetak probije neuhvaćen kroz `main()` (koji nema top-level try/except) i **cijeli Python proces se ruši**.

Provjereno na stvarnom logu (`logs/gated_k12_de_9001_9800.log`, oko linije 7850): tačno ovaj scenario, tokom glm-5.2@0.1 za njemački, na "Batch 18" (pozicije 9695–9744). Traceback: `requests.exceptions.ReadTimeout` iz `prevedi_single` → `main()` → neuhvaćeno.

**Flaviov scenario (3 batch-a, batch 2 pukne)** razjašnjen eksplicitno kroz par iteracija dijaloga, do potpune jasnoće:
- **Batch 1** (uspio) → `conn.commit()` izvršen → trajno sačuvano, krah kasnije ga ne dotiče.
- **Batch 2** (pukao) → djelimično prevedeno u RAM-u (lista-comprehension po rečenici, neke uspiju prije nego jedna potroši sva 3 pokušaja) → ali `commit()` se dešava TEK nakon cijelog chunk-a → ništa od toga nije zapisano. Za bazu, kao da batch 2 nikad nije ni pokušan.
- **Batch 3** → **nikad se ne izvrši, nijedan red koda** — proces je mrtav prije nego `for` petlja stigne do te iteracije. Ne "preskače se svjesno" — ponaša se kao da uopšte ne postoji u tom pokretanju.

**Bash orkestracija (Rupa A, otkrivena, NEPOPRAVLJENA ove sesije):** i `run_faza.sh` i `run_root_gated.sh` imaju `set -e`, ali svaki poziv ide kroz `| tee -a "$LOG"` bez `set -o pipefail` — exit kod cijevi je exit kod `tee`-a (skoro uvijek 0), ne pythona. Zato lanac **tiho nastavlja** na Sudiju i Pobjednika i pored pada — potvrđeno u istom logu (`>>> Sudija: gemma4:31b` odmah nakon traceback-a, bez zastoja).

## Dio 2 — Zašto prost rerun ne pokupi sve nedostajuće (Rupa B, dinamičko prera-čunavanje praga)

Flavio postavio hipotezu da rerun ne pokupi "batch 3" pouzdano. Istraženo kroz kod i SQL, bez nagađanja:

- Za faze≥2 (`is_refine=True`), `todo` lista se filtrira NE SAMO kroz `already_done()`, nego i kroz `seed_map`/prag (`finalni_score < 0.95`), **preračunato pri svakom pokretanju na osnovu TRENUTNOG pobjednika**.
- Pošto se (zbog Rupe A) Sudija+Pobjednik automatski pokrenuo odmah nakon pada, mogao je već proglasiti pobjednika preko DRUGOG modela/temperature za neke od "izgubljenih" rečenica.
- SQL provjera (`v_pobjednici_full`, k12/de, pozicije 9695-9800): od 70 rečenica u tom opsegu, **44 su već imale finalni_score≥0.95** (uglavnom preko mistrala, poneka preko glm@0.8) — te NE bi bile ponovo pokušane sa glm@0.1 na prostom rerunu, jer prag to ispravno isključuje.

**Flaviova korekcija terminologije (bitna, primijenjena za ostatak sesije):** ovo NIJE "bug" u smislu skrivene prepreke koja onemogućava predviđenu proceduru — to je odsustvo bilo kakvog planiranog error-handlinga na nivou orkestracije, dizajnerski propust, ne tehnički kvar. Rupa B specifično (dinamički prag) je nakon dalje diskusije okarakterisana kao **namjerno, ispravno ponašanje faze**, ne nešto što treba zaobići.

## Dio 3 — Runda (pitanje sa strane, odgovoreno iz baze)

Flavio pitao šta radi kolona `runda` na `bb_prevodi_knjige` (zaboravio). Provjereno u šemi i podacima:
- `runda` (default 1) je dio UNIQUE ograničenja (`knjiga_id, jezik_id, faza_id, model_id, temperatura_id, prompt_id, embeddings_id, runda`) — omogućava da se ISTA tačna konfiguracija prevede više puta nezavisno, bez sudara sa UNIQUE.
- Iskorišćena samo jednom: 50 redova sa `runda>1`, svi na Dracula (i par Hound Copy), 21. jul 2026, tri gated refine faze — poklapa se sa s147 permutacijskim eksperimentom (pozicija faze u lancu vs stopa otvaranja gate-a). Van tog eksperimenta, sve ide na `runda=1`.

## Dio 4 — Dizajn popravke: tri Flaviove korekcije prije implementacije

Kroz iterativan dijalog, obim zadatka sveden na minimum, uz tri eksplicitne ispravke Claudeovog prvog nagona:

1. **"Zaboravi kako smo stigli do prevođenja"** — Flavio preusmjerio raspravu sa mehanike pada na ČISTO ponašanje koje želi: "prevesti rečenicu sa nekim modelom i temperaturom nezavisno od toga da li postoji pobjednik, ako prevod te rečenice sa tim modelom/temp ne postoji." Claude prvo predložio flag koji ZAOBILAZI prag — POGREŠNO. Flavio ispravio: prag ostaje gdje strukturno pripada (preduslov faze, ne prepreka); "bezuslovno" znači samo akcija (`already_done()` provjera), NE i put do te akcije (koji uključuje prag GDJE faza to traži). Podsjetio i da postoje DVA svijeta (svaki može nezavisno puknuti) i refine koraci sa preduslovima — riješenje mora raditi generalno, ne samo za ovaj incident.
2. **"Kako znaš u kom svijetu je nešto puklo?"** — Claude predložio provjeru "da li je trenutni svijet isti kao kad je puklo". Provjerom šeme (`bb_faze_a1`: samo `id/faza_id/model_id/aktivan`, BEZ timestamp-a ili istorijske tabele) potvrđeno: ta informacija **ne postoji nigdje**, pitanje je neodgovorivo. Ispravljeno na pravo pitanje: da li je model TRENUTNO aktivan SADA (provjerljivo direktno, bez istorije) — relevantno samo za fazu 1 (root), jer gated faze imaju trajnu a1/a2 deklaraciju nezavisnu od "svijeta".
3. **"Sigurnosna ograda" nepotrebna** — Claude predložio da flag `false` (default) ODBIJE rad ako primijeti djelimičan rad (zaštita od pogrešno pokrenutog opsega). Flavio: paternalistički, rješava problem koji ne postoji ("Ovo nije force!"). Uklonjeno. Flag ostaje ČISTO label za log, bez ikakve provjere/ograde.

**Ime parametra:** Flavio predložio `--uradi-ako-nema` ("kao if not exists u SQL-u"), eksplicitno tražeći da bude "glupo" jednostavno. Usvojeno bez izmjene — dosljedno postojećoj srpskoj konvenciji imenovanja (`--knjiga`, `--jezici`, `--gated-faza`...).

## Dio 5 — Implementacija `--uradi-ako-nema`

Tri fajla, sve preko `str.replace()` sa `assert count==1`:

- **`src/bb_03_prevod.py`** — novi `argparse` bool flag (`action="store_true"`, default `False`) + jedan `print()` odmah nakon "Rečenica za obradu": `"REZIM: --uradi-ako-nema (namjeran nastavak/dovrsavanje raspona; logika already_done()+prag nepromijenjena)"`. Nikakva druga logika dirana.
- **`run_faza.sh`** — nova promjenljiva `URADI_AKO_NEMA`, parsira `--uradi-ako-nema`, prosljeđuje kroz poziv `bb_03_prevod.py`.
- **`run_root_gated.sh`** — isto, prosljeđuje flag kroz OBA poziva `run_faza.sh` (root i gated korak), radi dosljednosti sa stvarnim Flaviovim ulazom (uvijek kroz gated-root lanac).

Verifikacija prije commit-a: `py_compile` (OK), `bash -n` oba shell fajla (OK), `--help` ispis potvrđuje flag na argparse nivou. Commit `0f6504a`, push potvrđen (`git log origin/main -1` poklapa se sa lokalnim).

## Dio 6 — Test na stvarnom incidentu (Flavio) + potpuna Claude-ova verifikacija

Flavio preveo sinoćnje problematične rečenice (opseg 9001-9800, k12, core-4 de/hr/it/sr, podijeljeno 9001-9100 + 9101-9800) koristeći novi flag, gledao samo `de` log lično, tražio da Claude provjeri sve detaljno.

**Logovi (8 fajlova):** nula Traceback-a, nula timeout retry-ja ovaj put, `REZIM: --uradi-ako-nema` ispisan tačno 5× po fajlu (3 root modela + 2 glm gated temp — potvrđuje propagaciju kroz oba koraka gated-root lanca).

**Baza — pokrivenost glm-5.2 u 9001-9800, faza 10:**

| jezik | glm@0.8 | glm@0.1 | razlika |
|---|---|---|---|
| hr | 407 | 407 | 0 |
| it | 336 | 336 | 0 |
| sr | 435 | 435 | 0 |
| de | 368 | 361 | 7 |

Simetrična provjera (obje strane, sva 4 jezika) potvrdila: hr/it/sr potpuno poklapanje, de tačno 7 pozicija (9697, 9719, 9720, 9728, 9731, 9744, 9750) gdje glm@0.8 postoji a glm@0.1 ne.

**Objašnjenje 7 de rečenica (potvrđeno, ne pretpostavka):** svih sedam trenutno pobjeđuje glm-5.2@0.8 SAM, finalni_score 0.9541–0.9761 (iznad praga 0.95). Prag ih je ispravno isključio iz `todo` na oporavku — Rupa B iz Dijela 2, potvrđena na stvarnim podacima, ne samo teoretski.

**created_at analiza** potvrdila kompletnu rekonstrukciju priče: de glm@0.1 imao 340 redova zapisanih 3.avg u 17h (batch-evi 1-17 prije pada) + 21 novih 4.avg u 8h (ovaj rerun) = 361 ukupno, tačno poklapanje sa DB brojkom. **340+21(uspjelo)+7(ispravno isključeno) = 368 = ukupan gated bazen za de** — potpuna, zatvorena računica.

**Protokol razjašnjenja (Flavio, strogo pravilo primijenjeno):** kad je Claude prijavio "7 razlika" bez eksplicitno reći da li je to u redu, Flavio zatražio strogo pravilo odgovaranja: "da li je u redu → ako jeste zašto prijavljeno → ako ima/nema zašto → ako urađeno kada/zašto → ako nije urađeno zašto nije." Claude priznao da je iznošenje broja bez odmah reći "ovo je očekivano, ne problem" bilo nejasno, i odgovorio strogo po formatu. Prihvaćeno kao razjašnjeno.

## Dio 7 — Otkriven nesklad sa session_159.md (NEISTRAŽENO DO KRAJA, otvoreno)

Tokom pripreme sesijske dokumentacije, provjera `created_at` timestamp-a za glm-5.2@0.1 (de, it) otkrila anomaliju: **IT log (`gated_k12_it_9001_9800.log`) ne sadrži nijedan Traceback i završava čisto istog dana (3.avg 18:24)**, sa svih 336 redova zapisanih PRIJE 4. avgusta — što znači IT nije trebao NIKAKAV oporavak danas.

Ovo je u suprotnosti sa `session_159.md` Dio 9, koja za isti opseg (9001-9800) prijavljuje **IT: 17 timeout događaja, 2 potpuna neuspjeha (~40 rečenica)**.

Nije dalje istraženo (van obima ove sesije) — mogući uzroci: (a) log fajl `gated_k12_it_9001_9800.log` je prepisan (`>` ne `>>`) naknadnim ručnim rerunom prije kraja s159, brišući trag originalnog pada; (b) s159-ov izvještaj je bio netačan (npr. brojevi zamijenjeni između jezika u tabeli). Zabilježeno kao otvorena stavka, ne kao zaključena istina ni u jednom smjeru.

## Dio 8 — Dokumentacija

- **`docs/KAKO-NovaFaza.md`** — nova sekcija "Oporavak nakon pada usred prevođenja (s160)", između postojećih sekcija "Prag (gate)" i checklist-a. Pokriva: mehanizam pada (bez try/except), Rupa A (pipe/tee), oporavak bez nove logike + `--uradi-ako-nema`, oba poznata ograničenja (dinamički prag za faze≥2; `m.aktivan` filter u Sudiji za fazu 1 specifično), i eksplicitno otvorenu Rupu A kao nepopravljenu. Cijeli fajl pregledan nakon izmjene (internа konzistentnost potvrđena).
- **`README.md` §14** — header sekcije "Gated root" proširen sa "s159 batch/timeout nalaz, s160 oporavak nakon pada"; nov blockquote (✅ s160) sa punim sažetkom uz eksplicitno zabilježen IT/s159 nesklad; footer datum/sesija ažuriran (4. avgust 2026, sesija 160).

## Stanje na kraju sesije

**Kod (buchenberg repo):** čist, zadnji commit `0f6504a` prije docs-a ove sesije (`--uradi-ako-nema` u 3 fajla), plus dodatni commit za dokumentaciju (ispod).

**Baza:** korpus 50.624 / 1.905.054 / 360.832 (+21 prevoda naspram početka sesije — sve de glm-5.2@0.1, oporavak sinoćnjeg pada). Nema DB izmjena van onoga što je Flaviov test prevoda prirodno proizveo.

**Web:** nedirnut, BB_VERSION ostaje nepromijenjen ove sesije.

## Otvoreno za sljedeću sesiju

1. **Rupa A (pipe/tee guta exit kod)** — NEPOPRAVLJENA, eksplicitno ostavljena van obima ove sesije. `set -o pipefail` (ili `${PIPESTATUS[0]}` provjera) u `run_faza.sh`/`run_root_gated.sh` bi zaustavio lanac umjesto tihog nastavka na Sudiju/Pobjednika nakon pada.
2. **IT/session_159 nesklad** — nije istražen do kraja (Dio 7). Ako postane relevantno, provjeriti da li postoji način da se rekonstruiše šta se stvarno desilo (npr. shell istorija, drugi log fajlovi sa bliskim timestamp-om).
3. Stepenasti retry backoff (30/60/120s) iz s159 Dio 9 — i dalje neimplementiran.
4. "Treći svijet" (glm temp split, s157/s159 Dio 3) — i dalje neimplementiran, čeka na k12 da se završi.
5. k12 (Moby Dick) prevod — nastavlja se van sesije.

## Lekcije sesije

- **"Bug" vs "dizajnerski propust" — terminološka razlika koju treba poštovati** (Flavio, Dio 2): bug je skrivena prepreka koja onemogućava PREDVIĐENU proceduru; odsustvo bilo kakvog planiranog error-handlinga (npr. `pipefail`) je nedostatak dizajna, ne bug. Primjenjivo šire od ovog incidenta.
- **Ne predlagati bypass mehanizma preduslova (prag) kao "rješenje" za nedovršen posao** (Flavio, Dio 4) — preduslov je dio definicije zadatka za tu fazu; put do bezuslovne akcije je podjednako dio zadatka koliko i sama akcija.
- **Ne predlagati provjeru istorijskog stanja koje ne postoji u šemi** — prije predlaganja "provjeri da li je X isto kao ranije", provjeriti da li ta informacija uopšte postoji za provjeru (Dio 4, "kako znaš u kom svijetu je puklo").
- **Ne graditi "sigurnosne ograde" koje korisnik nije tražio** — Flavio zna zašto pokreće skriptu; flag koji odbija rad "da zaštiti" od nečega što nije problem je paternalizam, ne dizajn.
- **Strogo pravilo izvještavanja o nalazu:** kad se iznosi brojčani nalaz, odmah reći da li je u redu ili nije, PRIJE detalja — ne ostavljati čitaocu da nagađa da li je nešto problem.
- **created_at timestamp analiza je pouzdan način da se rekonstruiše REDOSLIJED događaja** kad log-analiza sama ne daje potpunu sliku (Dio 7) — direktno je otkrila nesklad koji ne bi bio vidljiv iz same DB brojke ili iz samog teksta prethodne sesije.

Sesija zatvorena SAMOSTALNO od Claudea, na Flaviov eksplicitan zahtjev ("dokumentuj sve uradjeno detaljno... uradi sve samostalno bez moje provere i bez odobrenja") — isti obrazac kao ranije samostalno zatvorene sesije (s143, s147, s149, s153-159).

---

*Flavio & Claude · Buchenberg · Sesija 160 · 4. avgust 2026.*
