# Session 135 — N-faza web sloj zatvoren, no-op refine: uzrok pronađen i ispravljen

**Datum:** 13. jul 2026.
**Fokus:** Nastavak s134 DUG liste (prekinute sesije). Web sloj postao N-faza-safe (stavke 1–4). Istraga i ispravka no-op refine anomalije (stavka 5). Pokušaj modifikacije `v_status_faza_matrica` (stavka 6) — spušten na nizak prioritet, Flaviova odluka.
**Ishod:** Stavke 1–5 sa DUG liste zatvorene. Stavka 6 svjesno odgođena. Novi horizont imenovan (NER kao kontekst za refine). Baza netaknuta osim eksperimenta koji je obrisan (DROP FUNCTION, bez traga).

---

## 0. Onboarding

Project files, README, posljednja 3 session dokumenta (132, 133, 134), health check — svi prikazani i odobreni po protokolu. Flavio je eksplicitno upozorio da je s134 prekinuta usred posla ("dosta dugačku da je završimo") — DUG lista iz session_134.md je bila jasan vodič za nastavak, korištena redom.

**Snimak zdravlja (početak i kraj sesije, nepromijenjeno):** 50.624 rečenice · 1.546.660 prevoda · 302.168 pobjednika. Bez pipeline runova ovom sesijom.

---

## 1–4. N-faza-safe web sloj (DUG stavke 1–4)

Sve četiri stavke iz session_134.md "DUG ZA SLJEDEĆU SESIJU" riješene redom, kako je Flavio tražio.

**Stavka 1 — `reader.html` l.746:** `togglePhases()` hardkod `panel.innerHTML = row(1,'faza1') + row(2,'faza2')` zamijenjen dinamičkom petljom:
```js
const fazaNums = Object.keys(data)
  .filter(k => /^faza\d+$/.test(k))
  .map(k => parseInt(k.slice(4), 10))
  .sort((a, b) => a - b);
panel.innerHTML = fazaNums.map(n => row(n, 'faza' + n)).join('');
```

**Stavka 2 — nav.js i18n, dvije porodice hardkoda:**
- `reader_phase1`/`reader_phase2` → jedan parametrizovan ključ `reader_phase_n: "Phase {n}"` (×5 jezika: EN/DE "Phase {n}", IT "Fase {n}", HR "Faza {n}", SR "Фаза {n}"). Stari ključevi obrisani (verifikovano grep-om da se nigdje ne pozivaju prije brisanja).
- `stats_col_phase1`/`stats_col_phase2` → isti obrazac, `stats_col_phase_n` ×5 jezika. Dodato prvo (uz stare ključeve), stari obrisani tek nakon što je stats.html prepravljen (stavka 3) i verifikovano da su mrtvi.
- Strukturna provjera nakon svake izmjene (§8 KAKO-JeziciUI.md): broj backtick-ova paran, `grep -c` tačan broj pojavljivanja.

**Stavka 3 — `stats.html` renderEngineTable():** kolone tabele "Wins by engine and phase" bile hardkodovane na `stats_col_phase1`/`stats_col_phase2`. Prepravljeno da gradi kolone dinamički iz unije faza prisutnih u `window._engineRows`:
```js
const phaseNums = [...new Set(rows.flatMap(r => Object.keys(r.phases)))]
  .map(Number).sort((a, b) => a - b);
```
Backend (`bb_web_export.py :: get_stats()`) je već bio N-faza-safe od s134 (`phases[str(faza)]` dinamički) — uskost je bila isključivo u frontend renderu.

**Stavka 4 — verzija, export, verifikacija, commit:**
- `BB_VERSION` bump **prije** browser testa: `s133` → `s135.1`.
- Re-export: `bb_web_export.py` (stats.json, svi tr_/phases_ fajlovi) + `bb_xray_export.py` (168 fajlova, uklj. k22 sa fazom 3).
- **Browser test (Flavio):** `reader.html?book=22` (hr) — tri reda (Faza 1/2/3) umjesto dva; drugi jezici (de/it/sr) — dva reda kako i treba (samo 2 faze postoje za te kombinacije); originalni Hound (book=1) — i dalje radi (2 faze); svih 5 UI jezika provjereno. Sve prošlo.
- Usput: screenshot pokazao sirove ključeve `stats_col_phase1`/`stats_col_phase2` na stats.html — ispostavilo se stara keširana stranica u browseru (server je imao ispravan kod, potvrđeno grep-om), ne live bug.
- Commit buchenweb `a3d203c`: "feat(reader,stats): N-faza-safe phase display — dynamic phase panel + engine table columns, parametrized i18n (reader_phase_n, stats_col_phase_n); BB_VERSION s135.1". Push potvrđen.

---

## 5. No-op refine — uzrok pronađen i ispravljen (DUG stavka 5)

### Podsjetnik na anomaliju (iz s134)
40/240 refine prevoda (faza 2, s134 batch: k22/23/24 × de/hr/it/sr × 1–20) imalo je `finalni_score` identičan seedu na 4 decimale — sumnja na "no-op": model vratio doslovno isti tekst.

### Provjera (SQL, read-only)
Upit koji uparuje faza-1 pobjednika (seed, preko `bb_prev_recenica_faza`) sa najboljim faza-2 kandidatom po istoj rečenici, i poredi i score i tekst:

| ukupno uporedjeno | score jednak | tekst identičan | tekst različit, isti score |
|---|---|---|---|
| 240 | 40 | **39** | 1 |

**39/40 (97,5%) "izjednačenih" slučajeva su pravi klonovi** — doslovno isti string kao seed, ne koincidencija scorea. Samo 1/40 je stvarna slučajnost (različit tekst, score se poklopio do 4. decimale — pravi slučaj blizu plafona gdje mjera prestaje da razlikuje). Na nivou cijelog batcha: **16,25% od 240 refine pokušaja** = potrošen Ollama Cloud poziv koji nije proizveo ništa novo.

Sva tri konkretna primjera izvučena za dalji test bila su **kratke rečenice** (naslov "Frankenstein;", adresa "To Mrs. Saville, England.", uzvik `"Good!" said Holmes.`) — vrijedna nijansa: kratke/trivijalne rečenice imaju mali prostor za legitimnu varijaciju, pa je model možda subjektivno "u pravu" da nema šta da promijeni.

### Uzrok — pronađen u kodu
`bb_03_prevod.py :: prevedi_refine_single()` prompt je sadržavao rečenicu:
> "Keep the reference only if it is already optimal."

Ovo je eksplicitna dozvola modelu da vrati klon — pita se model da *sudi* je li seed optimalan, a to je posao sudije (gemma4:31b), ne prevodioca u refine fazi.

### Test uživo (izvan baze, ništa upisano)
Standalone skripta (obrisana nakon testa) pozvala je Ollama Cloud direktno sa istim modelima/temp kao produkcija, na ista 3 primjera, tri varijante prompta:

| primjer | stari prompt | puni novi prompt (uklonjena dozvola + dodata eksplicitna zabrana) | varijanta A (samo uklonjena dozvola) |
|---|---|---|---|
| "Frankenstein;" (hr) | KLON | različit ("Čudovište Frankensteina" — **promjena značenja**) | različit ("Frankenštajn") |
| "To Mrs. Saville, England." (it) | KLON | različit | **KLON** |
| `"Good!" said Holmes.` (it) | KLON | različit | različit |

Stari prompt reprodukovao klon uživo 3/3 (dobra potvrda da je uzrok tačno pogođen). Puna nova verzija riješila 3/3, ali uz cijenu: agresivna zabrana ponekad gurne model da promijeni ZNAČENJE kratke/trivijalne rečenice, ne samo formu. Varijanta A (samo uklonjena dozvola, bez dodate zabrane) riješila 2/3 — nepotpuno, ali bez rizika prisilne promjene značenja.

### Flaviova odluka
Nakon razmatranja (Flaviova formulacija: *"ni jedan lijek nije bezopasan, ni jedan nema kontraindikacije"* — svaka izmjena prompta nosi trade-off, ne postoji čisto rješenje bez rizika negdje drugdje) — **usvojena minimalna izmjena**: samo ukloniti "Keep the reference only if it is already optimal.", **bez** dodavanja eksplicitne zabrane klona. Izbjegnut rizik "NER-scale" projekta (Flaviova paralela — pokušaj potpunog, robusnog rješenja bez ijednog nuspojava bi mogao potrajati neproporcionalno dugo za relativno mali dobitak).

**Primijenjeno** u `src/bb_03_prevod.py :: prevedi_refine_single()`. Testirano (verifikovan sadržaj fajla nakon izmjene). **Necommitovano do kraja sesije** — buchenberg repo se po dosadašnjem obrascu commituje jednom, na kraju sesije, za razliku od buchenweb koji ide odmah po browser verifikaciji.

---

## 6. `v_status_faza_matrica` — pokušaj i odustajanje (DUG stavka 6)

Flavio je predložio PL/pgSQL funkciju sa dinamičkim `EXECUTE` (`RETURNS SETOF record`) da izbjegne hardkodovane `f1/f2/f3` COALESCE/FILTER kolone u postojećem privremenom pivot viewu:

```sql
CREATE OR REPLACE FUNCTION get_status_faza_matrica()
RETURNS SETOF record AS $$
DECLARE v_sql text; v_columns text;
BEGIN
  SELECT string_agg(DISTINCT format('COALESCE(max(prevedeno) FILTER (WHERE faza_id = %1$s), 0) AS f%1$s', faza_id), ', ' ...)
  INTO v_columns FROM v_status_faza;
  v_sql := 'SELECT knjiga_id, ..., ' || v_columns || ' FROM v_status_faza GROUP BY ...';
  RETURN QUERY EXECUTE v_sql;
END; $$ LANGUAGE plpgsql;
```

Poziv sa `AS (knjiga_id int, knjiga_naziv text, ..., f4 bigint)` pukao je na:
```
ERROR: structure of query does not match function result type
DETAIL: Returned type character varying(200) does not match expected type text in column 2.
```

**Nalaz:** `RETURNS SETOF record` sa dinamičkim `EXECUTE` traži **tačno poklapanje tipa** u caller-ovom `AS(...)`, ne samo castable tip (za razliku od običnog upita gdje `varchar`→`text` prolazi bez problema). Poznato ograničenje Postgresa za polimorfne record-funkcije. Nije ni stiglo do provjere `f4` (koja bi vjerovatno isto pukla — trenutno postoje samo faze 1–3).

Ponuđene dvije popravke (caller koristi tačne tipove, ili funkcija eksplicitno kastuje u `v_sql`). **Flavio je odlučio da ne nastavlja** — princip: pristup (dinamički generisane kolone iz analitičkih funkcija) je dobra ideja, ali robusno rješenje "za svaki broj faza bez ikad ponovnog diranja" nosi disproporcionalan trošak u odnosu na to koliko je knjiga/faza projekat realno ikad imaće (9 knjiga od >75.000 na Gutenbergu — svjestna, trajna granica obima projekta). Funkcija obrisana (`DROP FUNCTION`), baza vraćena u prethodno stanje. **Modifikacija `v_status_faza_matrica` spuštena na nizak prioritet.**

---

## 7. Novi horizont — NER kao kontekst za refine

Flavio je imenovao (konceptualno mu bitno): koristiti postojeće NER+relacije rezultate (classic/llm/DocRE slojevi, zatvoreni u s133) kao kontekst-injection za **refine kvalitet** — ne samo za ti/vi baseline mjerenje kako je zamišljeno u s124 poluzi A. Ovo je logičan nastavak linije "NER+relacije = infrastruktura za kontekst-injection" iz s124, ali sad eksplicitno vezano za refine, ne samo gramatičku ispravnost (ti/vi/rod). **Zaseban budući session** — nedirano ovom sesijom, samo zabilježeno.

---

## Lekcije

1. **No-op ≠ loša mutacija.** Loša mutacija (nova, gora varijanta) je legitiman, informativan ishod pretrage prostora — genetski algoritam to i očekuje. No-op (bukvalni klon) nije mutacija uopšte — to je trošenje resursa bez ikakvog istraživanja. Razlika je bitna za odluku da li nešto "popravljati": Flavio je prvo mislio da diranje refine ponašanja krši princip "priroda ne zna unaprijed šta je bolje" — razlikovanje klona od loše mutacije je razriješilo prividni sukob.
2. **Konfaund u testu = konfaund, čak i kad ga sam praviš.** Prvi test novog prompta mijenjao je DVIJE stvari odjednom (uklonjena dozvola + dodata zabrana) — Flavio je to uočio i tražio izolovan test (varijanta A) prije donošenja odluke. Dobra praksa da se primijeni i na vlastite eksperimente, ne samo tuđe.
3. **Nema rješenja bez trade-offa.** Agresivnija verzija prompta (0/3 klonova) je uvela novu vrstu greške (promjena značenja na kratkim rečenicama) koju stari prompt nije imao. "Bolje" na jednoj osi može značiti "gore" na drugoj — svaka izmjena prompta zaslužuje eksplicitno imenovanje šta se dobija i šta se rizikuje, ne samo mjerenje jedne metrike.
4. **RETURNS SETOF record zahtijeva tačan tip, ne castable tip** — različito od ponašanja u običnom SELECT-u. Vrijedi znati prije sljedećeg pokušaja dinamičke pivot funkcije.
5. **"OK?" disciplina — ponovljen propust.** Claude je u ovoj sesiji ponovo (drugi put, prvi put s125) izvršio komandu u istoj poruci u kojoj je tražio "OK?", ovaj put pri brisanju memory zapisa. Flavio je preuzeo odgovornost na sebe iako greška nije bila njegova — dobra ilustracija principa "ne distancirati se", ali propust ostaje Claudeov i sad je zabilježen kao PONOVLJEN, aktivan rizik (memorija #25 ažurirana).
6. **Screenshot ≠ live stanje.** Stara keširana stranica u browseru izgledala je kao regresija (sirovi i18n ključevi umjesto prevoda); server je imao ispravan kod cijelo vrijeme. Prije zaključka o bugu iz screenshota, provjeriti server-side izvor.

---

## Memorija — čišćenje

Na Flaviov zahtjev, pregledana su sva 28 tadašnjih memory zapisa. Tri uklonjena kao zastarjela/redundantna (s102 horizont — sadržaj već u README §14; s114 i s123 "ZATVOREN" narativi — bitne činjenice već sažete u drugim, kraćim zapisima, SLJEDEĆE liste duplirale README backlog). Jedan dopunjen (OK-protokol, s135 recidiv). Jedan nov dodat (ovaj sažetak). Neto: 28 → 26.

---

## Završno stanje

- **Baza:** netaknuta osim eksperimenta (funkcija kreirana pa obrisana, bez traga).
- **Kod (buchenberg):** `src/bb_03_prevod.py` izmijenjen (uklonjena "keep if optimal" iz refine prompta) — **necommitovano do kraja sesije**.
- **Web (buchenweb):** `reader.html`, `stats.html`, `nav.js` izmijenjeni i commitovani (`a3d203c`) → **BB_VERSION s135** (sufiks skinut pred finalni commit sesije).
- **Memorija:** 26 zapisa (bilo 28) — 3 obrisana, 1 dopunjen, 1 nov.
- Session doc: ovaj fajl.

---
*Flavio & Claude · Buchenberg · Sesija 135 · 13. jul 2026.*
