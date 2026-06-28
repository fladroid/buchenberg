# Session 100 — 28. jun 2026. (u toku)

**Fokus:** Konceptualna diskusija (inteligencija roja → mudrost gomile → self-refine) destilovana u dizajn refine-eksperimenta. Mid-session checkpoint prije pisanja koda. Pipeline nedirnut (Flavio vodi prevode u pozadini).

## Onboarding snapshot (ulaz s100)
- Korpus: 38.333 rečenice, 868.910 prevoda, 170.270 pobjednika. Health 0:28, 74% CPU (s97 DB-fix se drži).
- Git: buchenberg 23fcb31 (s99), buchenweb 7dc6863 (s99). BB_VERSION s99.

## Diskusija — od roja do self-refinea
- **Buchenberg NIJE roj** (agenti ne interaguju). Jeste **mudrost gomile + best-of-N selekcija**: raznoliki nezavisni kandidati, sudija bira. Lineage iz pamfleta ide kroz GA (Pong: populacija→turnir→evolucija), ne kroz svarm.
- **Više modela/sudija pomaže samo kroz RAZNOLIKOST, ne broj.** Korelisane greške → varijansni pod rho*sigma^2. 50 varijanti gemme ~ ništa; 5 različitih familija = mnogo.
- **Interakcija = self-refine** (Madaan 2023): pobjednik kao hint pri prevođenju. To je dimenzija koja je nedostajala (Flatland).
- **Nezavisnost != interakcija** (ne mogu na istom kandidatu): seed-ovan kandidat je korelisan (refine-dobitak); slijep kandidat je nezavisan (šira gomila). Uticaj na IZBOR != uticaj na GENERISANJE.

## Dizajn refine-eksperimenta (dogovoreno)
- **Grana:** seed = postojeći pobjednik ubačen u prompt kao referenca. JEDINA razlika prema base = hint; sve nizvodno (back-trans, kosinus, sudija, finalni_score) identično. Čist eksperiment s jednom promjenljivom.
- **Nalepnice (NE nov model):** pseudo-modeli `gemma3:12b-refine` / `ministral-3:14b-refine` @0.8 — administrativna etiketa u bb_modeli da base i refine ostanu razdvojivi u podacima. Pozivaju pravu gemmu3/ministral. ("pseudo" = nalepnica, ne pseudo-random.)
- **Modeli:** po jedan iz svake familije @0.8 (dekorelisane grane; 0.8 garantuje novu varijaciju, det. grane bi vratile duplikat).
- **Test = single** (`prevedi_refine_single`, per-rečenica, poravnanje hint<->rečenica garantovano). ~100 rečenica kompletne knjige; kandidat Jekyll&Hyde hr.
- **Sudija:** za RELATIVNO poređenje base vs refine 1 sudija dovoljan (konstantna pristrasnost se poništava u razlici). Median-3 sudije RAZLIČITIH familija = zaseban PRODUKCIONI upgrade za apsolutni kvalitet (gemma4 sudi gemmi3 -> self-preference; treba tuđa krv).
- **Cilj = POREĐENJE, ne novi pobjednik.** Vidljivo kao X-Ray mod. Mjere: win-rate refine vs seed, delta sudija_avg, BROJ REGRESIJA (refine gori od seeda = self-bias), cosine(refine,seed) kao detektor kolapsa (visok = prazno parafraziranje).
- **Analiza stratifikovana** po seed-scoreu i tipu rečenice — NE filtrirati ulaz.

## PRISTUPAČNOST = tvrdo ograničenje (faza 2)
- **Produkcija refinea: batch OBAVEZAN** (10 ili 5), ne opcija. Single = 20x više Ollama poziva -> isključuje "manje sretne finansijski" i one koji su udarili u Ollama limite. Batch nije optimizacija nego uslov da rezultat bude u duhu projekta. Ako batch-refine ne uspijemo pouzdano -> funkcija se NE objavljuje.
- Plan: faza 1 dokazuje VRIJEDNOST jeftino (single); faza 2 gradi PRISTUPAČNU verziju (batch s poravnanjem N rečenica<->N hintova).

## Filozofija testiranja (Flavio — durable)
- Testirati pod REALNIM uslovima: ne gasiti bazu/server ni zabranjivati korištenje radi testa (integritet dozvoljavajući). Test na idealizovanim uslovima = senka koja laže.
- NE cherry-pickati rečenice (kratke/duge/loše/beznačajne) — baš tu žive problemi. Pun opseg na ulazu, stratifikacija u analizi.

## Urađeno (konkretno)
- `bb_modeli`: +2 reda — `gemma3:12b-refine` (id 12), `ministral-3:14b-refine` (id 13) @0.8. ON CONFLICT DO NOTHING. Verifikovano.
- Seed-dohvat iz `v_pobjednici` verifikovan na živim podacima (J&H hr s1–5): JOIN `prev_recenica_id -> pvr.recenica_id -> r.knjiga_id` + filter jezik/opseg. Radi.
- **Šema netaknuta. Kod NIJE diran** (bb_03 nepromijenjen). Procesi u pozadini sigurni.

## Sljedeće
1. Napisati `--refine` granu u `bb_03_prevod.py`: flag + `prevedi_refine_single` + seed-dohvat u main (umjesto prevedi_batch).
2. Pokrenuti test (~100 rečenica, J&H hr), pun pipeline za oba refine-kandidata -> bb_04 bira iz bazena od 7.
3. Analiza (win-rate, delta sudija, regresije, cosine-kolaps, stratifikovano).
4. Ako prođe: batch-refine (faza 2, pristupačnost) -> web prezentacija self-refinea.

---
*Flavio & Claude · Buchenberg · Session 100 (u toku) · 28. jun 2026.*

## REZULTAT TESTA — self-refine (J&H hr, s1–100)

**Nalaz: dirigovani self-refine na jakim seedovima NE radi. Čist negativan rezultat.**

Tri mjere:
- **Win-rate: 36/100** refine pobjeda (gemma3-refine 23, ministral-refine 13). IZGLEDA kao uspjeh — ali je artefakt selekcije iz šireg bazena.
- **Head-to-head refine vs SVOJ seed: 0/100.** Refine NIKAD ne nadmaši seed koji je dobio. avg delta -0.076, najgori pad -0.30, najbolji slučaj i dalje -0.005. Nijedna pobjeda nad seedom.
- **Apsolutni kvalitet refine kandidata solidan** (gemma3-refine sudija 0.851 / komp 0.918; ministral-refine 0.821 / 0.917) — ali ispod base pobjednika (0.95+).

**Interpretacija (X-Ray):** seed je već bio pobjednik od 5 modela (blizu plafona). Instrukcija "popravi ovo" perturbuje već-optimalni anchor → self-bias + regresija ka prosjeku → skoro svaka prerada je korak unazad. Naša mudrost-gomile je toliko dobra da je sama sebi odsjekla prostor za refine.

**Metodološka pouka:** da smo gledali SAMO win-rate (36/100), poslali bismo ovo u produkciju kao "poboljšanje". Head-to-head (0/100) nas je spasio. 36/100 je bila SENKA, 0/100 je ORIGINAL. Atribucijski konfaund na koji smo se pazili od početka — potvrđen.

**Izmjereni trošak single moda:** gemma3-refine 97 rečenica = 9m35s (uz 4 paralelna Flavijeva procesa, bez Ollama grešaka). Potvrđuje da je batch obavezan za produkciju (faza 2) — ali faza 2 je sad upitna jer sama funkcija ne radi na jakim seedovima.

## NOVE HIPOTEZE (horizont — iz diskusije nakon nalaza)
1. **Selektivni re-translate na SLABIM seedovima** (apsolutni prag, npr. seed < 0.85, NE relativna medijana). Jedini netestiran režim — tamo ima headroom. Jak seed dokazano nema prostora.
2. **Slijepo ponavljanje != self-refine** — to je šira gomila / best-of-N (nepristrasno, ne škodi sistematski, ali slabo pomaže na jakom seedu). Razlikovati od dirigovanog (pristrasno ka gorem).
3. **Petlja "dok ne poraste za deltu" = ZAMKA** — selekcija na šumu metrike (winner's curse / Goodhart na varijansi). Broj raste, prevod ne. Fiksno-X "zadrži najbolji" je sigurno ali diminishing.
4. **Prava poluga grupne inteligencije = RAZNOLIKOST, ne broj prolaza.** Šesti model iz DRUGE familije (van gemma/ministral/nllb loze) > N prolaza istih modela (kopije+šum, korelisani).

## STANJE PIPELINE (izmjene s100)
- `bb_03_prevod.py`: +`--refine` (flag, prevedi_refine_single, get_seed_map, ollama_naziv). Backup `.bak_s100_refine`.
- `bb_08_sudija.py`: OCJENJIVANI_MODELI +2 refine; `len(prevodi) < 5` -> `< 1` (petica je bila redundantan gejt, postao bug u inkrementalnom režimu; sudija_avg IS NULL već štiti od dvostrukog ocjenjivanja). Backup `.bak_s100_refine`.
- `bb_04`/export: NETAKNUTI (nema hard-kod liste ni gejta po broju kandidata — argmax po finalni_score).
- Novi: `run_refine.sh`, `fla_refine19.sh`.
- DB: bb_modeli +2 reda (id 12 gemma3-refine, 13 ministral-refine @0.8). Refine prevodi+ocjene za J&H hr s1-100 OSTAJU u bazi (dokaz nalaza; ne čistiti).
- **Refaktor na horizontu:** OCJENJIVANI_MODELI hard-kod -> kolona `grupa` u bb_modeli + `--grupe` arg (Flavijeva ideja; izmjena šeme, kad se gase procesi).

## SNAPSHOT (izlaz s100)
- Korpus: 38.333 rečenice, 888.390 prevoda, 174.270 pobjednika (health 0:25, 85% CPU).
- Uključuje ~400 refine prevoda/ocjena (J&H hr s1-100, gemma3-refine + ministral-refine) — ostaju kao dokaz nalaza.
- Git ulaz: buchenberg 23fcb31, buchenweb 7dc6863. Izlaz: +s100 commit (bb_03, bb_08, run_refine.sh, fla_refine19.sh, session_100.md).
- BB_VERSION: ostaje s99 (web NIJE mijenjan u s100).

## SLJEDEĆE (s101+)
1. Web prezentacija self-refinea kao NEGATIVAN nalaz ("failure modes kao filozofija") — probali, evo zašto ne radi na jakom korpusu. Iskreniji X-Ray od "nove funkcije".
2. Selektivni re-translate na slabim seedovima (apsolutni prag <0.85) — jedini netestiran režim.
3. Refaktor OCJENJIVANI_MODELI -> kolona `grupa` u bb_modeli (kad se gase procesi za ALTER TABLE).
4. Ranije s99 horizont: length bucketing, proširenje prijevoda, art.html v1, NLP relation extraction.

---
*Flavio & Claude · Buchenberg · Session 100 ZATVOREN · 28. jun 2026.*
