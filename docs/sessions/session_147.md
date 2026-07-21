# Sesija 147 — 21. jul 2026.

**Autori:** Flavio & Claude
**Fokus:** tri niti — permutacijski eksperiment (redoslijed refine koraka),
provjera NER exporta, implementacija "runde" (§4.9 PLAN-KONFIGURACIJA.md)

---

## Zdravlje na početku sesije

Checklist proveden (project files → README → session_144/145/146 → health_check).
Korpus na početku: 50.624 rečenice / 1.647.361 prevoda / 307.768 pobjednika
(raslo od s146 snapshot-a preko Flaviovih pozadinskih runova). Sve zeleno,
252 poznate rupe (nepromijenjeno), git 26 necommitovanih fajlova (poznat
`.bak_*` backlog + nov `x.x` fajl, neobjašnjen, ostaje otvoreno pitanje).

---

## Nit 1 — Permutacijski eksperiment (redoslijed refine koraka)

Flavio je ručno preveo k20 (Dracula) rečenice 2801–3400 (600 rečenica,
hr/de/it/sr) i pustio refine faze 4/5/6 u šest različitih redoslijeda,
po 100 rečenica po bloku:

| Blok | Redoslijed |
|---|---|
| 2801–2900 | 4,5,6 |
| 2901–3000 | 4,6,5 |
| 3001–3100 | 5,4,6 |
| 3101–3200 | 5,6,4 |
| 3201–3300 | 6,4,5 |
| 3301–3400 | 6,5,4 |

**Verifikacija prije analize (X-Ray princip):** `bb_prevodi_recenica.created_at`
po bloku potvrdio Flaviov navedeni redoslijed TAČNO na svih 6 blokova × 4
jezika — simulacija lanca sigurna.

**Metod:** Python skripta (`analiza_s147_permutacije.py`, ostaje necommitovana,
analitička, ne dio pipeline-a) simulirala sekvencijalni lanac po stvarnom
redoslijedu svakog bloka — seed = trenutni najbolji rezultat prije tog koraka
(root ∪ prethodni koraci u istom bloku), jer `bb_04_pobjednik.py` (koji
`run_faza.sh` uvijek pokreće na kraju) ažurira apsolutnog pobjednika prije
sljedećeg koraka lanca.

**Nalazi (2.400 rečenica-jezik parova):**

1. **Pozicija u lancu — jasan, monoton efekat.** Gate otvoren 21,0% (korak 1)
   → 13,9% (korak 2) → 11,3% (korak 3). Prosječan pomak ocjene kad je gate
   otvoren: +0,0237 → +0,0077 → +0,0080. Samo-sužavajući lijevak radi tačno
   kako je dizajniran (s144) — prvi korak pokupi najviše popravljivih
   rečenica, ostatak je već prosijan.
2. **Konkretna faza (4 vs 5 vs 6), kontrolisano za poziciju** (uravnotežen
   dizajn — svaka faza 2× na svakoj poziciji): gate open rate slična (14,9-
   15,8%), win-rate slabo favorizuje fazu 4 (53,2%) nad fazom 6 (47,3%), ali
   prosječan pomak kad pobijedi favorizuje fazu 5 (0,0164) nad fazom 4
   (0,0138). Nema faze koja dominira na obje mjere — slab, nekonzistentan
   signal.
3. **Redoslijed (blok)** — ukupan pomak po bloku varira (0,0037–0,0138), ali
   OVO NE MOŽE biti pripisano redoslijedu: svaki blok su drugačije rečenice
   (Flavio eksplicitno: "broj rečenica nije reprezentativan"), pa je efekat
   konfaundiran sa sadržajem — between-block, ne within-sentence dizajn.

**Zaključak koji je vodio u nit 3:** da bi se stvarno testirala komutativnost
redoslijeda, treba ISTE rečenice provučene kroz više redoslijeda. Flavio je
pitao da li bi različit JEZIK mogao poslužiti kao "iste rečenice, drugi
redoslijed" (npr. de=4,5,6, hr=5,4,6, it=6,5,4) — odgovoreno NE: jezik je
sam po sebi ogroman izvor varijacije (s145 Hound nalaz: gated refine win-rate
raspon 65-100% SAMO od jezika, bez promjene redoslijeda), pa bi bio potpuno
aliasiran s redoslijedom, ne samo konfaundiran. Prava rješenja: (a) više
blokova s ponovljenim istim redoslijedom (smanjuje šum, ne rješava sadržajni
konfaund), (b) "runda" mehanizam s izolovanim seed-om po rundi (jedini pravi
put do ISTE rečenice/jezika kroz više redoslijeda bez klon-trika), (c) klon-
trik (faza 7/8/9), dokazano radi ali gomila `bb_faze` redove.

Nula izmjena baze/koda u ovoj niti — čisto analitička (SQL + Python, sve
READ-ONLY).

---

## Nit 2 — NER export provjera

Flavio je pitao da li NER export odražava stvarno stanje (pokretao je
web_export/xray_export više puta, vjeruje da rade po dogovoru, ali NER
export odavno nije provjerio).

**Provjereno:** `ner_*.json` na `/var/www/buchenberg/data/` sadržajno TAČNO
odgovara bazi na svih 12 knjiga (classic + llm entiteti po tipu, DocRE
relacije) — export mehanizam radi ispravno, ništa zastarjelo.

**Ono što JESTE nepotpuno je sam NER pipeline (baza), ne export:**
- Classic+LLM sloj: 10/12 knjiga (sve osim Copy knjiga 23/24)
- DocRE relacije: samo 5/12 knjiga (Hound, Alice, J&H, Flatland, Hound Copy)
- **The Big Four Copy (23) i Frankenstein Copy (24): NULA — nijedan sloj**,
  `run_ner.sh` nikad pokrenut na njima
- Preostalih 5 knjiga (Big Four, Frankenstein, Moby Dick, Romeo&Juliet,
  Dracula) imaju classic+llm ali ne DocRE — otvoreno od s133 odluke
  ("velike knjige idu sekvencijalno kad bude resursa — pokretanje, ne
  razvoj")

Flavio pokreće `run_ner.sh` samostalno, javlja rezultate. Nula izmjena u
ovoj niti.

---

## Nit 3 — Implementacija "runde" (§4.9)

### Rasprava prije implementacije

Flavio je tražio podsjetnik na "rundu" (dizajnirana i testirana u s145,
NEimplementirana) kao mogući put ka mjerenju uticaja redoslijeda refine
koraka (nit 1). Kroz razgovor razjašnjeno:

- Sama runda (kako je dizajnirana u s145) NE rješava problem mjerenja
  redoslijeda, jer seed uvijek čita GLOBALNOG apsolutnog pobjednika
  (`v_pobjednici_full`) — druga runda bi se nastavljala na rezultat prve
  runde umjesto da kreće ispočetka, pretvarajući "dvije runde od 3 koraka"
  u jedan produženi lanac od 6 koraka.
- Predložen **seed-lock** mehanizam: `get_seed_map()` bi umjesto globalnog
  pobjednika čitao `(faza=1) OR (runda=N)` — svaka runda kreće od root-a,
  gradi se samo unutar sebe, rundе se međusobno ne dodiruju. `bb_04_pobjednik.py`
  bi se tokom eksperimenta uopšte ne pokretao (da eksperimentalne runde ne
  kontaminiraju pravog pobjednika).
- Razjašnjeno kroz konkretne primjere (Flaviovo pitanje: "šta ako pokrenem
  rundu 1 sa seed-lockom na rečenicama koje već imaju stariju refine
  istoriju?") — rizik: `runda=1` default vrijednost znači "sve što je ikad
  urađeno prije uvođenja runde", ne "prazno stanje". Pravilo: nikad koristiti
  `runda=1` + seed-lock na rečenicama sa starijom istorijom, uvijek početi
  od svježeg broja runde.
- Razjašnjeno mehanika automatskog "aktiviranja" boljeg rezultata: `bb_04`
  radi argmax preko SVEGA uključujući `runda` kao običan atribut — bolji
  rezultat iz bilo koje runde automatski postaje pobjednik ČIM se `bb_04`
  pokrene, bez posebne logike.

**Flaviova odluka:** implementirati u dva koraka. Prvo samo "runda" (njena
originalna svrha — izbjegavanje klon-trika), seed-lock ostaje za kasnije.

### Implementacija (5 koraka + test, prema §4.9 planu)

**Korak 0 — Backup:** `pg_dump -Fc` prije DDL-a →
`/tmp/bb_backup_pre_runda_20260721.dump` (1,5 GB).

**Korak 1 — DDL** (umotano u transakciju):
```sql
ALTER TABLE bb_prevodi_knjige ADD COLUMN runda INTEGER NOT NULL DEFAULT 1;
ALTER TABLE bb_prevodi_knjige DROP CONSTRAINT bb_prevodi_knjige_full_key;
ALTER TABLE bb_prevodi_knjige ADD CONSTRAINT bb_prevodi_knjige_full_key
  UNIQUE (knjiga_id, jezik_id, faza_id, model_id, temperatura_id, prompt_id, embeddings_id, runda);
```
Svi postojeći redovi dobili `runda=1` automatski. Ime ograničenja provjereno
prije DROP-a (X-Ray — ne pretpostavljati).

**Korak 2 — View:** `CREATE OR REPLACE VIEW v_prevodi_full` — `pk.runda AS runda`
dodan na kraj SELECT liste (additive, isti obrazac kao s142). Svi izvedeni
pogledi provjereni poslije (`v_pobjednici_full`, `v_pobjednici_faza_full`,
`v_status_faza_model`) — brojevi netaknuti.

**Korak 3 — `bb_03_prevod.py`:** nov `--runda` CLI (default 1);
`get_or_create_prevodi_knjige()` dobio `runda` parametar (INSERT, ON CONFLICT,
fallback SELECT); poziv proslijeđuje `args.runda`; log header dobio `runda:`
polje. `already_done()` NIJE mijenjan — automatski postaje runda-svjestan jer
`prevodi_knjige_id` već jedinstveno kodira rundu.

**Korak 4 — `run_faza.sh`:** nov `--runda` (default "1"), proslijeđen samo u
`bb_03_prevod.py` poziv, vidljiv u log liniji.

**Korak 5 — Test na k22 (test knjiga), faza 4, hr, pozicija 109:**
- Test A (runda=1, default): `already_done()` ispravno prepoznao postojeće
  redove (14728/14729), "Preostalo: 0 rečenica" za oba modela — nula
  regresije.
- Test B (runda=2, eksplicitno): nov, nezavisan `prevodi_knjige_id`
  (15320/15321), `already_done()` NIJE prepoznao kao urađeno, refine se
  stvarno izvršio, sudija ocijenila, `bb_04` argmax ispravno odabrao bolji
  rezultat (glm-5.2 runda=2, final=0,9344) nad prethodnim pobjednikom
  (mistral-large-3 runda=1, final=0,9326) — potvrđeno upitom nad
  `v_prevodi_full` da je 0,9344 stvarno globalni maksimum od svih 15
  kandidata za tu rečenicu (nije bila pogrešna pretpostavka — provjereno
  prije upisa u dokumentaciju, X-Ray disciplina).

**Health check poslije:** sve zeleno. Web/xray export skripte provjerene
kodom (grep) da ne koriste `SELECT *` ni `v_prevodi_full` — nova kolona ih
ne dotiče, export ostaje ispravan bez ponovnog pokretanja.

**Flaviova odluka o test podacima:** ostaju u bazi kakvi jesu (legitiman
bolji prevod pronađen kroz refine, ne artefakt za brisanje).

### Dokumentacija

`docs/PLAN-KONFIGURACIJA.md` ažuriran na 4 mjesta (header/status pasus,
§4.9 naslov, §4.9 Status pasus, §6) — pri prvom prolazu propušten §4.9
naslov+status (s126 pravilo o provjeri CIJELOG dokumenta uhvatilo grešku
prije commit-a). README §9 nov s147 snapshot, umetnut na vrh descending
bloka (odmah poslije s107 ascending repa, prije s146 — otkriveno da
sekcija 9 NIJE striktno hronološka: rani zapisi s100-s107 ascending, pa
prelom, pa s146→s108 descending).

---

## Lekcije

- **Runda bez seed-locka ne rješava problem mjerenja redoslijeda** — bitna
  razlika koju je Flavio sam ispravno intuitivno posumnjao pitanjem
  "kako da mjerim uspjeh redoslijeda ako druga runda nastavlja na prvu?".
- **Jezik nije jeftina zamjena za pravu repeticiju** — aliasing (ne samo
  konfaund) kad bi se jedan redoslijed vezao za tačno jedan jezik.
- **"Runda 1" ≠ "prazno stanje"** kad rečenice imaju stariju refine istoriju
  prije uvođenja kolone — rizik za buduće seed-locked eksperimente na
  starim opsezima.
- **Provjera cijelog dokumenta prije commit-a uhvatila stvarnu grešku** —
  §4.9 naslov/status ostali "NIJE implementirano" poslije prvog prolaza
  kroz §6/header; s126 pravilo opravdano ponovo.
- **"Upisano faza: N" u bb_04 izlazu = broj upisanih faznih redova, NE
  faza_id pobjednika** — kratkotrajna zabuna razriješena provjerom sirovih
  podataka prije nego je ušla u dokumentaciju.

---

## Završno stanje

Korpus: 50.624 / 1.647.363(+2 test) / 307.768(+1 test, runda=2 postao
pobjednik). BB_VERSION ostaje s146 (web nedirnut). Git: necommitovano na
kraju sesije (Flaviov redovan ritual) — `run_faza.sh`, `src/bb_03_prevod.py`,
`docs/PLAN-KONFIGURACIJA.md`, `README.md`, novi `analiza_s147_permutacije.py`,
`session_147.md`, plus `.bak_s147` fajlovi.

## Sljedeći koraci

- Flavio: `run_ner.sh` na preostalih 7 knjiga (posebno Copy knjige 23/24
  koje nemaju ništa) — javlja rezultate.
- Seed-lock (§4.9 dio) — dizajn razjašnjen ovom sesijom kroz detaljnu
  raspravu, nije implementiran, čeka Flaviovu odluku.
- Permutacijski eksperiment (nit 1) ostaje otvoren dok seed-lock ne postoji
  — bez njega redoslijed-efekat i dalje nerazdvojiv od sadržaja rečenica.
- `x.x` fajl na `foxuno` — neobjašnjen, otvoreno pitanje za Flavija.
- Git commit (ova sesija zaključena bez commit-a — Flaviov redovan ritual,
  kao i uvijek).

---

*Flavio & Claude · Buchenberg · Sesija 147 · 21. jul 2026.*
