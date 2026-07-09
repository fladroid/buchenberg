# Session 123 — Web Faza 3: registar modela, stats tri tabele, before/after reader

**Datum:** 9. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Kompletna implementacija Web Faze 3 — od detaljnog plana do gotovog
reader before/after prikaza. Prva izmjena šeme baze u fazi (nova referentna tabela
`bb_model_registar` s atributima vrsta+uloge). Faza kroz cijeli lanac: DB → export →
stats tri tabele → reader oznaka + before/after panel. Sve kroz protokol
prikaži→OK→izvrši, bez izuzetka.

## Health snapshot
Početak: bb_recenice 50.624, bb_prevodi_recenica 1.518.170, bb_prev_recenica 296.578
(raste u pozadini od Flaviovih runova). Git početak: buchenberg HEAD 439393f→caaecb6
(s122 NLLB fix), buchenweb HEAD 5d2f470 (s120). Sve zeleno, Ollama Cloud (glm-5.2,
mistral-large-3:675b, gemma4:31b) OK.

## Urađeno

### 1. Detaljan plan Faze 3 (docs/WEB-FAZA3-KORACI.md)
Flavio tražio da Claude iz konceptualnih dokumenata napiše detaljan izvršni plan
(podjela rada: Flavio konceptualni pogled, Claude → konkretni koraci). Kreiran
`docs/WEB-FAZA3-KORACI.md` (commit 39856c8, pa dopunjen Korakom 0.5 → c67b8ec).
Odluke zaključane s Flaviom:
- **Jedna putanja** (A+B zajedno, format izlaza biran jednom).
- **Tabela 1 (by-engine): i engine I faza** — razlaganje faza1/faza2/ukupno
  (Flaviov primjer: engine x = faza1 100 + faza2 20 = ukupno 120).
- **Stats broji APSOLUTNE pobjede razložene po fazi** (ne fazne pobjede iz
  `bb_prev_recenica_faza`) → čisto sumira. Fazna tabela hrani samo reader before/after.
- **engine = m.naziv**, Tabela 1 pokazuje sve istorijske engine-e (živa istina baze).

### 2. Korak 0 — verifikacija šeme (read-only)
- `bb_prev_recenica_faza` kolone potvrđene: id, prev_knjige_id, prevodi_recenica_id,
  faza_id (faza_id FK na bb_faze).
- Raspodjela: faza 1 = 296.578, faza 2 = 18.210 (faza 2 = 6.1% faze 1 → phases_
  sparse, potvrđuje lazy-load dizajn).
- **Ključni nalaz:** faza-1 i faza-2 pobjednik su RAZLIČITI prevodi_recenica_id
  (različiti modeli/faze), vezani preko iste rečenice (recenica_id). Prvi upit
  (grupisan po prevodi_recenica_id) vratio 0 — ispravljen na grupisanje po
  recenica_id. Bitno za Nivo B pivot.
- Test-slučaj: knjiga 1 (Hound) hr, pozicije 1–2 imaju obje faze.
- **Nalaz o starim knjigama** (Flavio potvrdio): knjige id 1–22 imaju prvih ~100–200
  rečenica u fazi 2, prevedene starim (neaktivnim) parom ali suđene AKTUELNOM
  sudijom. before/after je većinom istorijski snimak starog para, ne novi par.

### 3. Korak 0.5 — bb_model_registar (PRVA izmjena šeme u fazi)
Uzak registar (Flaviova odluka), ključ = ime modela. Atributi vrsta+uloge pripadaju
IDENTITETU (imenu), ne instanci (trojci). `uloge TEXT[]` jer je uloga 1:N (jedan
model može više uloga — Flaviov "ekstremni slučaj"). bb_modeli NE diran.
- **Backup baze prije DDL** (pg_dump -Fc, 1.5G, verifikovan pg_restore -l, 148 TOC,
  14 tabela) → `/tmp/bb_backup_pre_registar_20260709_113119.dump` u pgdb kontejneru.
- `CREATE TABLE bb_model_registar (naziv TEXT PK, vrsta TEXT, uloge TEXT[])` — bez
  DEFAULT (novi model mora svjesno dobiti ulogu).
- Provjera prije INSERT: gemma4:31b = 0 prevoda → čisto {sudija} potvrđeno.
- INSERT 10 redova: 7 opšti LLM/{prevodilac}, gemma4:31b opšti LLM/{sudija},
  nllb-600M namenski MT model/{prevodilac}, multilingual-e5-large embeder/{vektorizacija}.

**Razgovor o principu (zabilježeno):** Flavio želi dugoročno DB vrijednosti na
engleskom (kao Key Concepts / X-Ray legenda — namjerni izuzetak). Za sada vrijednosti
ostaju kako jesu (srpske, neprevedene, podatak ne UI). Engleska-DB = zaseban budući
korak. Takođe zabilježeno: uloga na nivou INSTANCE (model×config čas jedno čas drugo)
= budući redizajn ako "ekstremni slučaj" postane stvaran; za sada registar-po-imenu
dovoljan. Normalizacija konfiguracije (temperatura) = takođe budući, temperatura je
1:1 s redom pa denormalizacija legitiman trade-off (KONCEPT §3), ne isti 1:N problem.

### 4. Koraci 1–2 — bb_web_export.py (faza + stats strukture)
- **get_translations:** dodato `m.faza_id AS faza` → tr_*.json nosi faza po rečenici.
- **get_stats:** win_rows + cand_map dobili faza_id (brojnik I nazivnik simetrično).
  Novi ključevi: `winners_by_config` (Tabela 2, model×temp×faza), `winners_by_engine`
  (Tabela 1, roll-up po naziv/faza + ukupno). Stari `winners` uklonjen (Korak 4e).
- **get_model_registry:** registar LEFT JOIN broj prevoda (kandidati iz
  bb_prevodi_recenica) → `models` ključ (Tabela 0). Sudija/embeder/neupotrijebljeni
  pokazuju 0 (X-Ray potpunost).
- Verifikacija: winners_by_engine sumira (faza1+faza2=ukupno) na svim engine-ima.
  Nalaz: faza-2 win-rate svuda NIŽI od faza-1 (ANALIZA.md pejsmejker efekat, brojkom).

### 5. Korak 4 — stats.html tri tabele + i18n
- Otkriveno: modelShortName/modelColor VEĆ name-independent (WEB-FAZA1 dug riješen ranije).
- HTML: models/engine/config-table-wrap (redoslijed 0→1→2).
- JS: renderModelsTable/renderEngineTable/renderConfigTable; renderWinnerTable uklonjen.
- nav.js: 16 novih stats ključeva × 5 jezika (naslovi + kolone). Strukturna
  verifikacija string-aware parserom (NAV_I18N balansiran, 5 blokova) — s79 bag izbjegnut.
- Browser test svih 5 jezika: OK (Flavio potvrdio).

### 6. Korak 5 — phases_*.json (Nivo B before/after)
- get_phase_winners: pivot po poziciji, emituje samo rečenice s fazom 2. Po fazi:
  model, prevod, ts, judge_avg, finalni_score (0.4×kompozit+0.6×sudija) + apsolutna_faza.
- 127 phases fajlova. Test knjiga 1 hr: poz 1 → faza 2 pobjeđuje (refine uspio),
  poz 2 → faza 1 pobjeđuje (refine pogoršao — ANALIZA.md jak seed). Pošteno pokazuje
  i uspjeh i neuspjeh refine-a.

### 7. Korak 6 — reader before/after + faza badge
- 6a: "refined" badge-dugme kad s.faza===2 (default prikaz).
- 6b: togglePhases lazy-load phases_*.json, Faza1→Faza2 panel s "winner" oznakom.
- nav.js: reader_refined/phase1/phase2/winner × 5 jezika. CSS phase-badge+phase-panel.
- escHtml prikazuje prevod kao čist tekst → `**Baskervilski pas**` (ministral Markdown
  artefakt) vidi se doslovno. Odluka (Flavio): ostaviti kako jest (server=istina, ne
  uljepšavaj; isti tip pitanja kao NLLB pre-fetch — artefakt je podatak, ne bug).
- Browser test svih 5 jezika + X-Ray Full netaknut: OK (Flavio potvrdio).

## Lekcije
- **Pri uklanjanju ključa/varijable: grep SVE upotrebe prije brisanja, ne samo
  definiciju.** Uklonjen stari `winners` ključ ali propušten završni print koji ga
  koristi → export pao s KeyError na kraju (JSON ipak ispravan jer se piše prije
  print-a). Popravljeno, ali skripta koja izlazi s greškom je pokvarena skripta.
- Prvi upit za "rečenice s obje faze" logički pogrešan (grupisan po prevodi_recenica_id
  umjesto recenica_id) → 0 redova. Nula redova = signal za provjeru premise upita, ne
  nužno prazan podatak.
- `--knjiga` filter za bb_web_export izbjegnut kao nepotrebno krpljenje — biblioteka
  je ~10 knjiga, pun export je 31s. Rješenje u potrazi za problemom.

## Završno stanje
- bb_model_registar: nova tabela, 10 redova (vrsta+uloge).
- bb_web_export.py: faza kroz get_translations/get_stats, +get_model_registry,
  +get_phase_winners. buchenberg/main.
- stats.html: tri tabele (models/engine/config). reader.html: badge + before/after.
  nav.js: 20 novih ključeva × 5 jezika. BB_VERSION s123.2. buchenweb/master.
- Data: 127 phases_*.json, svi tr_*.json s faza poljem, stats.json bez starog winners.
- Git: buchenberg b014ed5, buchenweb 26e34c3 (+ ovaj closing commit).

## Sljedeći koraci (budući, zabilježeni)
- DB vrijednosti registra → engleski (namjerni izuzetak kao Key Concepts). Mali izolovan UPDATE.
- Uloga na nivou instance (model×config) — ako "ekstremni slučaj" postane stvaran.
- Normalizacija konfiguracije (temperatura) — zaseban zahvat s backupom.
- bb_08 čita sudiju iz registra (WHERE 'sudija'=ANY(uloge)) umjesto hardkoda — registar
  operativan, ne samo deskriptivan (isti potez kao KONCEPT §6).
- Markdown artefakt čišćenje u prevodima (`**`) — ako se ikad poželi, zaseban prolaz.

---
*Flavio & Claude · Buchenberg · Session 123 · 9. jul 2026.*
