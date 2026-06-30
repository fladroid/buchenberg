# Session 104 — 30. jun 2026.

**Fokus:** Self-refine, dubinski. Jučerašnji timeout na refine putu → retry fix. Dijagnoza "5 čudnih slogova" (R&J es) otkrila da svih 8 nepotpunih ćelija iz s103 NIJE seed-missing nego **seed-is-refine** (skrivena pretpostavka u kodu). Seed-fix → sve refine rupe zatvorene (252/252). Win-rate agregat za stats. MiniLM legacy obrisan iz baze. Temelj za **pobjednika po fazama**: `bb_faze` + `bb_modeli.faza_id` (faza = svojstvo modela).

## Onboarding snapshot (ulaz s104)
- Korpus (health): 38.333 rečenice, 1.007.457 prevoda, 195.070 pobjednika. Health brz (s97 DB-fix se drži).
- Git: buchenberg b43461b (s103), buchenweb ab83475 (s102). BB_VERSION s102.
- Stanje prevoda naraslo od s103 (Flavio dopunjavao između sesija): Frankenstein/Big Four non-core puni (2000/3000), core-4 niži (1000) — namjerno sekvenciranje. Dracula/Moby/R&J core-4 puni, non-core pre-fetch. Alice/Flatland/J&H bazno kompletni svih 14.
- Ollama Cloud: nove familije dostupne (deepseek-v4, glm-5.x, kimi-k2.x, qwen3.5, mistral-large-3, nemotron-3) — za diverzifikaciju (horizont).

## 1. Retry fix u bb_03 (jučerašnji timeout)
- **Greška (Flavio pokazao log):** `prevedi_refine_single` → `ollama_chat` (linija 176) radio goli `requests.post(timeout=120)` BEZ retry. ReadTimeout na Ollama Cloud (Batch 2, R&J) ubio cijeli proces.
- **Nalaz (grep):** retry NE postoji nigdje u bb_03 (ni base ni refine put). README §13 ga pripisuje s38, ali u ovom fajlu ga nema. Postoji u `bb_08_sudija.py:69` i `bb_09_ner.py:54` — Flaviovo pamćenje ("vidio sam 30s retry, uvijek uz Ollama") bilo tačno, samo u drugom fajlu.
- **Fix:** retry petlja u `ollama_chat` (jedna funkcija kroz koju prolaze SVI cloud pozivi — prevedi_batch/single/refine_single). Identičan obrazac kao sudija: `max_retries=3, wait=30`, hvata (HTTPError, ReadTimeout, ConnectionError), lokalni `import time`, `flush=True` za nohup log. Backup: `bb_03_prevod.py.bak_s104_retry`.
- **Lekcija:** retry je bio u sudiji/NER ali NE u prevodu — istorijski, dodavan gdje je timeout prvo zabolio. Refine je prvi natjerao bb_03 na dovoljno dugu seriju da timeout iskoči.

## 2. Dijagnoza "5 čudnih slogova" → seed-is-refine (glavni nalaz)
Flaviov prijedlog: koncentrisati se na jedan jezik × knjigu. R&J es gemma3-refine = 95/100.
- **Rupe:** pozicije 62,68,72,74,78 — razbacane po sredini (ne blok na kraju → ne timeout-prekid).
- **Original tih 5 = najteže Shakespeare rečenice** (idiomi, "maidenheads" igra riječi, arhaizmi "'Tis"). Stratifikuj-ne-filtriraj princip: rupe su tačno gdje se greške kriju.
- **Hipoteza seed-missing (s103) OBORENA:** svih 5 IMA seed.
- **Pravi uzrok:** sve 5 imaju za trenutnog pobjednika `ministral-3:14b-refine`. `get_seed_map` filtrira `NOT LIKE '%-refine'` → kad je trenutni pobjednik refine, rečenica ispadne iz seed_map → ispadne iz todo → gemma3-refine je NIKAD ne pokuša. Tiha rupa, bez NULL-a, bez traga.
- **X-Ray uvid:** rupa nije greška u podacima nego **sjenka pretpostavke u kodu** ("seed je uvijek bazni"). Pretpostavka vrijedila dok je refine bio izuzetak (s100); pukla čim je refine postao punopravan takmičar (full run s103), tačno na rečenicama gdje je refine najjači.

## 3. Seed-fix (Flaviova odluka: anchoraj na trenutnog pobjednika, ma koji bio)
- Skinut `AND m.naziv NOT LIKE %s` iz `get_seed_map` (+ treći %s argument). Seed = trenutni pobjednik, uključujući refine. Refine-na-refine = sljedeća iteracija mutacije nad mutiranim. Backup: `bb_03_prevod.py.bak_s104_seedfix`.
- **Verifikovano uživo (R&J es run):** `Refine: 5 rečenica sa seedom` (prije fixa = 0), pokupio tačno 62–78, svih 5 prevedeno (score 0.92–0.94), bez timeouta. **s74 pobjeda:** gemma3-refine anchorao na ministral-refine seed, proizveo varijantu na temp 0.8 (drugačija leksika: interpretarlo→entenderlo), i POBIJEDIO. Anchored mutation u djelu, Flaviova osa "gramatičan ostanak u prostoru" — ne win-rate. (Flaviov tip "barem promijeni red riječi" se obistinio i premašio.)
- **Svih 6 preostalih rupa iz s103 = isti uzrok** (seed=refine, potvrđeno upitom): Dracula nl (23), Frankenstein af (5)/nl (30), J&H mk (12)/ro (10)/sl (28). Flavio pustio popravne runove → sve zatvorene.
- **Završno: 252/252 refine ćelije pune (100 svaka).** gemma3-refine 12.600 / ministral-refine 12.600 kandidata. Refine pobjede: gemma3-refine 2.487, ministral-refine 1.465 = 3.952 (bilo 3.826 u s103, +126 iz popunjenih rupa). Win-rate 15.7% — i dalje SELEKCIJSKI ARTEFAKT (ANALIZA.md osa).

## 4. Win-rate agregat (bb_web_export, stats.json)
- Flaviova zamjerka starom `%`: "% od čega? Kako uporediti 100 sa 3800?" Stari procenat (count/total) dijelio refine (12.600) i base (~195.000) istim nazivnikom → refine izgleda kao šum (1.3%) iako je 19.7% tamo gdje se takmiči.
- **Fix:** `get_stats` dobio drugi agregat (kandidati po model×temp iz `bb_prevodi_recenica`) → `winners` red sad nosi `candidates` + `win_rate` = count/candidates. Dva nezavisna agregata spojena u Pythonu (anti-fan-out, s97 obrazac). Backup: `bb_web_export.py.bak_s104`.
- Win-rate po konfiguraciji: gemma@0.8=29.6, gemma@0.1=21.9, ministral@0.8=20.5, ministral@0.1=17.9, nllb=7.9, gemma-refine=19.7, ministral-refine=11.6. Refine sad pošteno uporediv (jači od nllb, blizu ministral@0.1).

## 5. MiniLM legacy obrisan iz baze
- Win-rate otkrio NLLB candidates=203.310 > total winners. Flaviova invarijanta ("nijedan prevod > broj originalnih rečenica") poslužila kao detektor: Hound kand_po_jeziku=3.861 > 3.852 original.
- **Uzrok:** de/hr/it imali po DVA `bb_prevodi_knjige` reda za NLLB/Hound — jedan e5-large (3.852), jedan MiniLM (40). UNIQUE(knjiga,jezik,model,embedder) → oba legalna. Legacy trag iz vremena prije nego je e5-large postao jedini embedder.
- **Cijela baza:** MiniLM = 22 ćelije, 120 kandidata (0.012%). e5-large = 884 ćelije, 1.007.450. MiniLM "odavno napušten" (Flavio).
- **Odluka (Flavio): obrisati** ("inače će nas uvijek zezati"). Provjera: 0 MiniLM pobjednika → bezbjedno. FK-safe transakcija (djeca pa roditelj): DELETE 120 prevodi_recenica + 22 prevodi_knjige. COMMIT. Baza sad: distinct_embeddera=1.

## 6. Pobjednik po fazama — KONCEPTUALNI PREOKRET (Flavio)
**Problem (Flavio):** "Izgubili smo istoriju pobjednika." `bb_prev_recenica` čuva JEDAN pobjednik (trenutni). Kad je refine prepisao bazni pobjednik, **pobjednik-od-5 je izgubljen**. Ne možemo prikazati "base nasuprot base+refine" jer base-pobjednici više ne postoje. Tabela nad osakaćenim podatkom ostaje osakaćena — anti-X-Ray (prepisali smo što reader pošteno prikazuje). Rješenje nije pametnija tabela nego da baza **pamti faze**.

**Novi pojmovi:**
- **Fazni pobjednik** = najbolji kandidat unutar te faze.
- **Pobjednik rečenice** = najbolji od svih faznih pobjednika = ono što danas živi u `bb_prev_recenica`.

**Arhitektonska odluka (Flavio, durable): faza = svojstvo MODELA, ne broja kandidata ni imena.** Proširivost na fazu 3+ (diverzifikacija) zahtijeva da model eksplicitno nosi svoj korak — `-refine` sufiks trik se lomi na fazi 3 (deepseek nije "-refine"). Princip "atribut samo ako nosi informaciju" (Flaviova analogija: pol se ne čita iz težine): `redoslijed` zadržan jer može biti 100/50/400 nad id 1/5/17 (sort nezavisan od id-a).

**Urađeno (DDL, transakcija):**
- `bb_faze` (id, naziv, redoslijed UNIQUE NOT NULL, opis). 2 reda: base (red=1), refine (red=2).
- `bb_modeli.faza_id` FK → bb_faze. 7 živih modela: 1,3,5,10,11→base; 12,13→refine. 6 mrtvih (2,4,6,7,8,9 = napušteni eksperimenti temp0.5/claude-sonnet + sudija gemma4) ostaju faza_id NULL (semantički tačno: ne učestvuju u fazi prevoda; NULL kao slab proxy "neaktivan").

## Stanje na izlazu
- Kod (uncommitted, idu u commit): `bb_03_prevod.py` (retry + seed-fix), `bb_web_export.py` (win-rate).
- Baza: MiniLM obrisan; `bb_faze` kreirana; `bb_modeli.faza_id` dodata i popunjena. Pobjednici NEDIRNUTI (195.070).
- stats.json regenerisan (win-rate u JSON-u, MiniLM van nazivnika).
- Backupi: bb_03 .bak_s104_retry/.bak_s104_seedfix, bb_web_export .bak_s104.

## Sljedeće (po prioritetu) — VAŽNO, dosta otvoreno
1. **Redizajn `bb_prev_recenica` za faznog pobjednika** (temelj postavljen, nadgradnja ostaje). Materijalizovati faznog pobjednika po (rečenica, faza).
2. **Rekonstrukcija faze 1** za refine-pokriveni opseg (Flaviova napomena, NE ZABORAVITI): za 9 knjiga × 14 jezika × prvih 100, trenutni pobjednik je pobjednik-od-7. Faza-1 pobjednik (argmax nad faza_id=1 kandidatima) treba EKSPLICITNO izračunati. Razlikuje se od pobjednika rečenice samo na 3.952 mjesta (gdje je refine pobijedio); ostalo identično. Svi bazni kandidati + scoreovi još u bazi → izračunljivo.
3. **OTVORENO arhitektonsko pitanje (riješiti pri redizajnu):** faza-N pobjednik = kumulativno (argmax nad faza ≤ N) ili izolovano (samo faza N)? Claude naginje kumulativno (faza = populacija nakon koraka, ne samo novi modeli) — Flaviova odluka.
4. **Stats dvije tabele** (dizajn dogovoren, čeka implementaciju): Tabela 1 "by model" (3 reda engine: gemma 102.788 / ministral 76.282 / nllb 16.000, Total 195.070, % od totala — zbraja se u 100). Tabela 2 "by configuration" (7 redova: model/temp/role/wins/win-rate, BEZ total i BEZ 100% jer win-rate su odvojene stope, ne kriške). Role vrijednosti goli EN (base/refine), naslovi kolona i18n. Legenda: definisati count (pobjede) vs candidates (puta u igri). Bar = win-rate skaliran na max.
5. Indikator aktivno/neaktivno za modele (i faze) — Flavio spomenuo (kao MiniLM), zasad odgođeno. Mrtvi modeli (2,4,6,7,9) možda za brisanje, ali NE bez provjere.
6. Ranije (s102/s103 horizont): 60/40 sensitivity, diverzifikacija (faza 3, druge familije), head-to-head refine vs seed na cijelom korpusu.

## Lekcije
- **Konflikt = STOP radi.** Više puta stao na nesklad (s103 brojevi vs sad = Flaviove dopune; "5 nedostaje" vs 7 ćelija; `recenica_id` ne postoji → pogledao šemu; suma % ≠ 100 objašnjeno; NLLB candidates > original → otkrio MiniLM). Svaki put pretpostavka greške u vlastitom pristupu prije baze/Flavia — i svaki put bilo tačno.
- **Flaviova invarijanta kao detektor:** "nijedan prevod > broj originalnih" uhvatio MiniLM duplikat. Domensko pravilo > slijepi upit.
- **Šema je izvor istine prije prvog SELECT-a:** `bb_prev_recenica` nema recenica_id/jezik_id (čista veza-tabela); `\d` prije pisanja spasio od pogađanja.
- **Faza = svojstvo modela, ne imena/broja** — jedini dizajn koji preživi fazu 3.

---
*Flavio & Claude · Buchenberg · Session 104 · 30. jun 2026.*
