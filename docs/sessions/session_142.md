# Session 142 — Plan konfiguracija: Dio A izvršen

**Datum:** 18. jul 2026.
**Fokus:** Izvršenje Dijela A iz `docs/PLAN-KONFIGURACIJA.md` (s141) — redefinicija
faze kao konfiguracije preko tri nezavisne ose (a1=model, a2=temperatura,
a3=prompt). Svih 9 koraka (0–8) izvršeno, verifikovano, kraj-do-kraja testirano.

## Zdravlje na početku
50.624 rečenice · 1.608.260 prevoda · 302.168 pobjednika. BB_VERSION s138.
Git: 18 `.bak` fajlova (backlog), buchenberg čist osim toga.

## Zdravlje na kraju
50.624 rečenice · 1.608.271 prevoda (+11, namjerni test-prevodi) · 302.168
pobjednika (nepromijenjeno — test-prevodi nisu ušli u takmičenje za pobjednika).
BB_VERSION ostaje s138 (buchenweb netaknut; export skripte popravljene ali
NIJE pokrenut export na živi `/var/www/buchenberg/data`, samo u `/tmp` test).

---

## Izvršeni koraci (Dio A, plan §3.2)

**Korak 0 — Backup.** Prvi pokušaj pao tiho u alatu (MCP timeout, poznat
obrazac iz s134 — pronađeno tek pretragom `docs/sessions/` na Flaviov
izričit zahtjev nakon što je backup preskočen bez provjere prakse).
Ispravljena komanda (`docker exec pgdb pg_dump ... > host-fajl`, jer
kontejner nema `/tmp` mapiran na host). `bb_backup_pre_konfiguracija_20260718.dump`
(1.5G, 190 TOC, 19 tabela — verifikovano `pg_restore -l` + poklapanje sa `\dt`).

**Korak 1 — Kataloške tabele.** `bb_temperature` (id, vrijednost REAL UNIQUE),
`bb_promptovi` (id, naziv UNIQUE, 4 TEXT kolone za batch/single × prevod/back).
`real` umjesto plana-navedenog `NUMERIC` — usklađeno s postojećom `bb_modeli.temperatura`
konvencijom (Flaviova odluka).

**Korak 2 — Punjenje kataloga.** `bb_temperature` ← DISTINCT iz starog `bb_modeli`
(5 vrijednosti). `bb_promptovi` ← 2 reda (`base`, `refine`), tekstovi doslovno
prepisani iz `bb_03_prevod.py` (6 f-string funkcija → 4 kolone × 2 reda; back-translation
prompt identičan u oba reda). Verifikovano `SELECT` na sadržaj — poklapa se slovo po slovo.

**Korak 3 — Tabele-veze.** `bb_faze_a1/a2/a3` (svaka: `faza_id` FK + izbor FK +
`aktivan`, `UNIQUE(faza_id, izbor)`). Napomena: `bb_faze_a1.model_id` privremeno
pokazuje na STARI (slijepljeni) `bb_modeli` — Korak 6 to remapira (najavljeno unaprijed).

**Korak 4 — Punjenje veza.** `bb_faze_a1`: 15 redova (DISTINCT po faza+naziv,
`aktivan` dosljedan pa se prenosi direktno). `bb_faze_a2`: 7 redova (`aktivan` =
OR agregacija jer ista temperatura može biti uz aktivan i neaktivan model u istoj
fazi). `bb_faze_a3`: 3 reda (faza→prompt po `metod_id`). Svi brojevi verifikovani
naspram README §3 aktivnih modela.

**Korak 5 — Trag na `bb_prevodi_knjige`.** Dodane 4 nove kolone
(`faza_id, model_id_novi, temperatura_id, prompt_id`), popunjene UPDATE-om iz
starog `model_id` (1.268/1.268, 0 NULL, grupe pred/posle identične 21=21,
uzorkom potvrđen mapping).

**Korak 6 — Čist `bb_modeli` katalog.** Prvi pokušaj (jedna velika `BEGIN...COMMIT`
transakcija) pukao — MCP timeout usred izvršenja. **Potpun rollback potvrđen**
(0 aktivnih transakcija, `\d` pokazao netaknuto stanje, `model_id=model_id_novi`
na uzorku) prije ponovnog pokušaja — ista lekcija kao s134. Ponovljeno kroz manje
pod-korake:
- `DROP COLUMN model_id` prvo odbijen — **10 zavisnih pogleda** (`v_prevodi`,
  `v_pobjednici`, `v_prevodi_po_modelu`, `v_prevodi_full` direktno; 6 dalje
  izvedenih). Nije korišten `CASCADE` (uništilo bi `v_status_faza_model` na kome
  stoji `health_check.py` 2b). Umjesto toga: 4 bazna pogleda prepisana
  (`CREATE OR REPLACE VIEW`, isti nazivi/tipovi kolona; source `m.temperatura`→
  `t.vrijednost`, `m.faza_id`→`pk.faza_id`); 6 izvedenih nastavilo raditi bez
  izmjene. Svi brojevi verifikovani (1.608.260/302.168 svuda).
- Remap `bb_faze_a1.model_id` i `bb_prevodi_knjige.model_id_novi` na GLOBALNI
  kanonski ID (MIN po nazivu, preko svih faza — ne per-faza).
- `bb_modeli`: 25→9 redova (DELETE duplikata), `DROP COLUMN temperatura, faza_id`,
  `ADD UNIQUE(naziv)`.
- `RENAME model_id_novi TO model_id` — Postgres automatski ažurirao definicije
  pogleda (zavisnost prati broj kolone, ne ime) — verifikovano `pg_get_viewdef`.
- Novi `UNIQUE` na sve 4 ose + `embeddings_id`; `NOT NULL` na sve.

**Korak 7 — Kod čita iz baze.**
- `bb_aktivni_modeli.py`: DIZAJNERSKA ODLUKA (Flavio, nakon Claudeove analize
  rizika) — zadržati TAČNE istorijske (model,temp) parove (čitanjem iz
  `bb_prevodi_knjige`), ne pun unakrsni proizvod a1×a2 (koji bi uveo nikad-testirane
  kombinacije poput NLLB@0.1). Prvi pokušaj pukao (`SELECT DISTINCT` + `ORDER BY`
  van select liste), ispravljeno aliasom. Testirano na sve 3 faze — poklapa se
  tačno sa README §3.
- `bb_03_prevod.py`: 6 prompt-funkcija sad prima `tpl` i radi `.format()`
  umjesto hardkodovanog f-stringa; `get_or_create_prevodi_knjige` proširen na
  pun UNIQUE (7 kolona); model-lookup provjerava a1/a2/a3 aktivnost; header
  loga dobija `prompt:` polje. Prikazan pun `diff` prije zamjene fajla.
- `bb_web_export.py` + `bb_xray_export.py`: OTKRIVENO polomljeno (direktno
  čitaju `m.temperatura`/`m.faza_id`) — nije bilo u eksplicitnom Koraku 7 popisu,
  ali je unutar Koraka 8 obaveze ("stats/web export usklađeni"). 4 mjesta u
  `bb_web_export.py`, 1 u `bb_xray_export.py` popravljeno (temperatura preko
  `bb_temperature` JOIN-a, faza direktno iz `bb_prevodi_knjige`, bez dodatnog
  join-a). Testirano u `/tmp` (NE na živi `/var/www/buchenberg/data`).

**Korak 8 — Puna verifikacija.**
- End-to-end test na knjizi 22 (test knjiga): baza (pozicije 401–405,
  glm-5.2@0.8, faza 1) i refine (195–200, faza 2) — oba stvarni Ollama pozivi.
  `get_or_create_prevodi_knjige` ispravno prepoznao postojeću konfiguraciju
  (prevodi_knjige_id=12008 nastavio niz od 400 postojećih prevoda). Refine
  tekst potvrđeno stilski zavisan od seed-a (ne identičan, ne nezavisan).
- `health_check.py` puno pokrenut — EXIT 0, 2b sekcija radi na novoj šemi.
  Broj poznatih rupa 231→236 (+5, objašnjeno test-prevodima koji su namjerno
  koristili necontiguous opsege — mehanika MAX-baziranog view-a ispravno
  detektovala, nije migracioni defekt).
- NER export (classic/LLM/DocRE) potvrđeno NEPOGOĐEN — strukturno (0 poklapanja
  `bb_modeli`/`model_id` u `get_ner*` funkcijama) i empirijski (svi `ner_*.json`
  generisani bez greške u test-exportu, uključujući knjigu 22).

---

## Odluke (Flavio)
- Backup naming/obrazac: nastaviti postojeću konvenciju (`/tmp/bb_backup_pre_<opis>_<datum>.dump`).
- `bb_aktivni_modeli.py`: tačni istorijski parovi, ne pun unakrsni proizvod (za sada).
- Nastaviti "korak po korak, bez žurbe" kroz cijeli Dio A bez pauze.
- Paralelno s izvršenjem, dokumentovati komande za session doc (ova napomena).

## Lekcije
1. **Provjeri dokumentaciju PRIJE improvizacije, čak i za rutinske komande.**
   Backup je izveden pogrešno prvi put jer nisam prvo pretražio postojeću praksu
   (s123/s126/s131/s134) — sve je bilo već zapisano, uključujući TAČNO ovaj
   scenario (s134: "pg_dump kroz balsam:run_command puca u alatu, fajl svejedno
   nastane"). Flaviova oštra reakcija bila je opravdana i ispravna.
2. **MCP timeout nasred transakcije ≠ SQL greška.** Kad se izlaz alata prekine
   usred izvršenja, prvo provjeriti pravo stanje baze (aktivne transakcije,
   `\d`, brojevi) prije ponovnog pokušaja ili zaključka o uzroku.
3. **Nezavisne ose (a1/a2/a3) razotkrivaju skrivenu spregu koju je stara shema
   nosila implicitno.** Prelaz s "tačnih parova" na "nezavisne kataloge" gubi
   informaciju o TAČNIM istorijski korišćenim kombinacijama — mora se svjesno
   odlučiti gdje ta informacija sad živi (u ovom slučaju: u `bb_prevodi_knjige`
   fact-tabeli, ne u posebnoj junction tabeli).
4. **`CREATE OR REPLACE VIEW` s identičnim izlaznim kolonama ne kida downstream
   pogledi; `RENAME COLUMN` ne kida view definicije koje je koriste** (Postgres
   prati zavisnost preko broja kolone, ne imena) — obje činjenice omogućile
   migraciju view sloja bez ijednog `CASCADE` brisanja.
5. **Plan koji kaže "orkestratori se usklađuju" ne pokriva sve dodirne tačke.**
   `bb_web_export.py`/`bb_xray_export.py` nisu bili eksplicitno pobrojani u
   Koraku 7, ali su bili jednako polomljeni — otkriveno tek probnim pokretanjem
   u Koraku 8, ne unaprijed predviđanjem. Health check + probni export na
   pravim skriptama > oslanjanje na tekst plana kao potpun popis.
6. **Alat za uređivanje fajlova (`str_replace`/`view`/`create_file`) radi na
   Claude-ovom lokalnom sandbox-u, NE na udaljenom serveru** — za izmjene na
   foxuno/balsam serverima uvijek koristiti heredoc + Python `str.replace()`
   preko `foxuno:run_command`/`balsam:run_command`.

## Otvoreno / za sljedeću sesiju
- **Dio B (random selekcija)** sada stoji na završenom temelju — dizajn iz
  s139/s140/s141 spreman za izvršenje kad Flavio odluči.
- Stari backup `bb_backup_pre_massey_20260712.dump` još na `/tmp` — higijena
  (s131 pravilo: obrisati prethodni pri svakom novom) nije urađena, čeka odluku.
- Export skripte popravljene ali NIJE pokrenut pravi export na
  `/var/www/buchenberg/data` — živi JSON i dalje odražava pred-migracijsko
  stanje (funkcionalno ispravno, samo zastarjelo od 11 test-prevoda). Odvojena
  buduća odluka.
- `bb_faze_a1_fkey`/`bb_prevodi_knjige_model_id_novi_fkey` nose zaostala imena
  ograničenja od privremenih kolona (kozmetičko, ne funkcionalno).
- Git: 18 starih `.bak` fajlova (backlog, više sesija) + tajanstveni `x.x` —
  vrijedi počistiti kad se nađe vremena.
- Test-prevodi (k22/hr, pozicije 401–405 i 195–200) ostaju u bazi kao stvarni
  podaci (nisu obrisani) — mala, bezopasna proširenja korpusa.

---
*Flavio & Claude · Buchenberg · Sesija 142 · 18. jul 2026.*
