# Session 134 — Faza ≠ Metod: strukturno razdvajanje + N-faza pipeline

**Datum:** 13. jul 2026.
**Fokus:** Povratak na self-refine ("korijeni"). Refine k22/23/24 + analiza. Zatim strukturni zahvat: **faza degradirana na redni broj + identifikator izvršavanja, metod izdvojen u zasebnu tabelu**. Rezultat: faza 3 pokrenuta bez ijedne linije novog koda.

---

## Snimak zdravlja (početak)

- Korpus: 50.624 rečenice · 1.546.120 prevoda · 302.168 pobjednika
- Sve zeleno (baza, Ollama Cloud, NLLB, venv)
- `buchenweb zaostaje` — poznat lažni pozitiv
- BB_VERSION s133 (web kod nije diran ni u ovoj sesiji → **ostaje s133**)

---

## 1. Refine run (faza 2) — k22/k23/k24

`run_refine.sh` (tada još postojao) ulančan `&&`, knjige 22 → 23 → 24, jezici de/hr/it/sr, rečenice 1–20.
Log: `logs/refine_s134_k22_23_24.log`.

**Potvrđeno u kodu (bb_03, l.415–423):** `already_done()` filtrira **prije** LLM poziva; `get_seed_map()` odbacuje rečenice bez seeda. Skripta sama preskače urađeno — bez trošenja poziva. k22/hr 1–10 (iz s114) uredno preskočeno.

## 2. Analiza faze 2 — dvije mjere, dvije istine (ANALIZA.md)

Uzorak: 3 knjige × 4 jezika × 20 rečenica = 240 rečenica. Bazen 7 kandidata (5 base + 2 refine).

| mjera | rezultat | baseline |
|---|---|---|
| **win-rate** (apsolutni pobjednik) | 72/240 = **30,0 %** | 2/7 = 28,6 % |
| **head-to-head** (refine vs vlastiti seed) | 60/240 = **25,0 %** strogo bolji; 40 izjednačeno; 140 gore | — |

Stari par je davao 0/100 (s100). Novi par daje 25 % — refine **nije mrtav**, ali agregatno i dalje gubi.

**Struktura je zanimljivija od prosjeka — headroom gradijent:**

| ćelija | avg_seed | delta | refine bolji |
|---|---|---|---|
| k23/sr | **0,9267** | **+0,0178** | 11/20 |
| k23/it | 0,9535 | **+0,0226** | 6/20 |
| k23/de | 0,9681 | +0,0072 | 8/20 |
| k23/hr | 0,9714 | +0,0029 | 6/20 |
| k22 (sve) | ~0,969 | −0,001 … −0,016 | 5/20 svaka |
| k24/de | **0,9777** | −0,0093 | 2/20 |
| k24/it | 0,9683 | −0,0078 | 1/20 |

**k23 je jedina knjiga s pozitivnom deltom — na sva četiri jezika, i ima najslabije seedove.** Najslabiji seed u setu (k23/sr) daje najveću pobjedu refine-a; najjači (k24/de) najmanju. To je headroom-hipoteza iz ANALIZA.md, sada **izmjerena**, ne pretpostavljena.

**Metodološka ograda (Flaviova, usvojena):** ne "refine kvari jak prevod" nego **"naš sudija i embedder ne vide poboljšanje na jakom seedu"**. Mjera je jedina koju imamo i mjeri samu sebe. Pravi X-Ray potez: izmjeriti **gdje sudija prestaje da razlikuje**, i tu povući granicu poboljšavanja.

**ANOMALIJA — OTVORENO:** 40/240 (17 %) refine prevoda ima **identičan `finalni_score`** kao seed na 4 decimale. Sumnja: refine vratio **doslovno isti tekst** (no-op) → trošen LLM poziv, lažni kandidat u bazenu. **Nije provjereno — prvi zadatak nastavka.**

---

## 3. Strukturni zahvat — FAZA ≠ METOD

**Flaviova formulacija (usvojena kao dizajn):**
- Preduslov za bilo koju fazu: **faza 1** (ROOT).
- Dovoljan uslov za sve ostale: **postojanje pobjednika**.
- Zajedničko svima: ocjenjivanje i suđenje.
- **Metod** = tip operacije (šta se radi, koji seed, koji prompt). **Ponovljiv M puta.**
- **Faza** = jedno izvršavanje metoda. Degradirana na **redni broj + jedinstveni identifikator**.
- **1 metod : M faza.**
- Seed je **uvijek trenutni apsolutni pobjednik**, iz bilo koje prethodne faze.

### Shema (backup: `bb_s134_pre_metode.dump`, kontejner + host)

```sql
CREATE TABLE bb_metode (id serial PK, naziv text UNIQUE, opis text, root boolean);
  1 = base         root=true    -- izvršiv tačno jednom
  2 = self-refine  root=false   -- izvršiv M puta

ALTER TABLE bb_faze ADD COLUMN metod_id integer NOT NULL REFERENCES bb_metode(id);
CREATE UNIQUE INDEX bb_faze_root_jednom ON bb_faze (metod_id) WHERE metod_id = 1;
```

- `bb_modeli.faza_id` **netaknut**. UNIQUE `(naziv, temperatura, faza_id)` je već dozvoljavao isti model u svakoj fazi — shema je N faza predvidjela od s114.
- **ROOT-invarijanta je sada u shemi, ne u kodu.** Verifikovano da puca: `INSERT ... metod_id=1` → `duplicate key value violates unique constraint "bb_faze_root_jednom"`.
- `bb_faze.opis` za fazu 1 ažuriran (pisao je o retiriranom gemma3/ministral paru).

### Nalaz o bazi (Flaviova bojazan da je "zeznuo strukturu")
**Nije.** Baza je N faza podržavala i prije ovog zahvata: nema `CHECK (id IN (1,2))`, nema binarnog polja, `bb_prev_recenica_faza` ima FK na `bb_faze(id)`. Uskost je bila **isključivo u orkestratoru**.

---

## 4. Orkestrator — `run_faza.sh` zamijenio `run_refine.sh`

**Novo:**
- `src/bb_faza_info.py` — faza → metod (`metod_id|naziv|root`); **exit 1 ako faza ne postoji**
- `run_faza.sh --faza N --knjiga ID --jezici "..." --od N --do M [--force]`

**Dizajnerske odluke (Flaviove):**
- `--faza` je **obavezan, ne auto-inkrementira se**. Auto-inkrement bi bio tiha odluka koja piše u bazu. *"Vidi se šta radiš."*
- `--force` ide **samo sudiji** (`bb_08` ga jedini ima; `bb_03` ga nema — `already_done()` je namjerna idempotentnost). Obrazac preuzet iz `run_ner.sh`.
- Guard 1: faza mora postojati u `bb_faze`. Guard 2: faza mora imati aktivne modele.
- Metod se čita iz baze, ali **još ne grana ponašanje** (base i self-refine zovu iste tri skripte; razliku pravi `bb_03 --faza`). Kad dođe novi metod (kontekst/NER), grananje ide u `case $METOD_NAZIV`.

**`run_refine.sh` obrisan** (`git rm`). Devet `fla_refine*.sh` pokretača ga zove — Flavio ih eksplicitno stavio van opsega ("ignoriši fla* skripte").

**Testirano:** `run_faza.sh --faza 2 --knjiga 22 --jezici hr --od 1 --do 20` na već urađenom opsegu → lanac prošao, sve preskočeno, pobjednik reizračunat identično. Idempotentno, bez LLM troška.

---

## 5. FAZA 3 — prvi run nove strukture

**Registracija (dva INSERT-a, nula linija koda):**
```sql
INSERT INTO bb_faze (naziv, redoslijed, metod_id, opis)
  VALUES ('refine-2', 3, 2, 'Drugi prolaz self-refine metoda.');       -- faza id=3
INSERT INTO bb_modeli (naziv, temperatura, faza_id, aktivan)
  VALUES ('mistral-large-3:675b', 0.8, 3, true), ('glm-5.2', 0.8, 3, true);  -- id 26, 27
```

**Kvar usput:** prvi kombinovani INSERT je pao (uzrok nepoznat — izlaz odsječen prije poruke o grešci). `BEGIN/COMMIT` spriječio pola posla. Ali `nextval` **nije transakcijski** → sekvenca odmakla, faza dobila `id=5` umjesto 3. Popravljeno: DELETE + `setval('bb_faze_id_seq', 2)` + ponovni INSERT. **Pravilo: poslije pale transakcije s `serial` PK — provjeriti sekvencu prije ponovnog upisa.**

**Run:** `run_faza.sh --faza 3 --knjiga 22 --jezici "hr" --od 1 --do 40` → 80 novih prevoda.

**Nijansa (imenovana, ne mana):** rečenice 1–20 su refine **nad refine-om** (seed može biti faza 2); rečenice 21–40 su **prvi** refine (seed = faza 1, jer faze 2 tamo nema). Dva eksperimenta pod jednom oznakom. Za prevod je ispravno (svaka rečenica sidrena na svog najboljeg); za **analizu** je konfaund koji treba pamtiti.

**Faze nisu komutativne:** ako seed uvijek uzima trenutnog pobjednika, self-refine → kontekst-refine ≠ kontekst-refine → self-refine. Put je dio rezultata. Vrijedno, ali samo ako je imenovano.

---

## 6. Viewovi

- **`v_status_faza`** (novi, long): `knjiga_id, knjiga_naziv, knjiga_recenica, jezik_kod, faza_id, faza_naziv, prevedeno`. Broji **distinct rečenice s bar jednim prevodom u toj fazi**. Deriviran iz `v_prevodi_full` (majka). **N-faza-safe bez izmjena.**
- **`v_status_faza_matrica`** (privremeni pivot): `f1, f2, f3` — **hardkodovane kolone, ne skalira**. Flavio: *"to se rješava analitičkim funkcijama, 999999 faza bez altera — pokazaću ti."* → **odgođeno, njegova demonstracija.**

**Lekcija (Flaviov prigovor, usvojena):** tražen je *"rezultat upita nad cijelim viewom, formatirano"* — Claude je umjesto toga pokrenuo **drugi upit** (pivot) i prikazao ga **kao da je izlaz viewa**, uz vlastitu podjelu na "originalne" i "Copy" knjige. Podmetnut vlastiti izlaz pod imenom tuđeg objekta. **Prikaz se ne smije razići od izvora istine; teza ide ispod tabele, ne u njenu strukturu.**

---

## 7. NER + exporti (k22)

- `run_ner.sh --knjiga 22`: bb_09 (spaCy) → bb_10 (LLM normalizacija, glm-5.2: 165 nekonfliktnih + 15 LLM entiteta, 191 co-occurrence veza; ispravio `Stapleton` ORG→PERSON, `Selden`, `"I."`→ne_entitet) → bb_10c (DocRE: 178 entiteta, 85 parova, **85 relacija upisano**).
- `bb_xray_export.py --knjiga 22` (po-fajlu izlaz `xray_<id>_<lang>.json` → siguran za filter).
- `bb_web_export.py` (nema filter po knjizi → cijeli korpus). Stats: 302.168 pobjednika, 10 modela, 15 konfiguracija.

---

## 8. Faza 3 otkrila hardkod "refine = faza 2" u web sloju

Faza 3 je natjerala kod da prizna gdje je i dalje binaran:

| sloj | stanje |
|---|---|
| baza, `bb_03`, `run_faza.sh`, `bb_faza_info.py` | ✓ N faza |
| `bb_xray_export.py` (`get_all_candidates` — bez filtera po fazi) | ✓ N faza |
| frontend X-Ray Full Mode (`candidates.forEach`, bez limita) | ✓ N faza |
| `bb_web_export.py` stats (`phases[str(faza)]`) | ✓ N faza |
| **`bb_web_export.py` l.235** | ✗ **POPRAVLJENO** |
| **`reader.html` l.746** | ✗ **DUG** |
| **`nav.js` i18n** | ✗ **DUG** |
| **`stats.html` kolone** | ✗ **DUG** |

**Popravljeno danas** — `bb_web_export.py :: get_phase_winners()`:
```python
# bilo:  if "faza2" in po_poziciji[p]
# sada:  if any(k.startswith("faza") and k != "faza1" for k in po_poziciji[p])
```
(+ docstring). Ključ `d[f"faza{faza}"]` je već bio dinamički.

**NIJE re-exportovano namjerno:** novi backend bi slao `faza3` u JSON koji `reader.html` ne zna prikazati. Backend i frontend idu **zajedno**, sljedeću sesiju. Web data ostaje konzistentna sa starim (dvofaznim) prikazom.

---

## DUG ZA SLJEDEĆU SESIJU (prioritet, ovim redom)

1. **`reader.html` l.746** — `panel.innerHTML = row(1,'faza1') + row(2,'faza2')` → dinamička petlja preko svih `faza{N}` ključeva.
2. **`nav.js` i18n — dvije familije hardkoda po fazi:**
   - l.171 `reader_phase1`, `reader_phase2`
   - l.30 `stats_col_phase1`, `stats_col_phase2`
   → **jedan parametrizovan ključ** (`reader_phase_n: "Phase {n}"`), × 5 jezika. **Prvo pročitati `docs/KAKO-JeziciUI.md`** (Flaviovo pravilo: nikad improvizovati i18n).
3. **`stats.html`** — kolone tabele "Wins by engine and phase" su dvije fiksne → moraju postati dinamične. Najveći dio, nije ni pogledan.
4. Poslije 1–3: **BB_VERSION bump PRIJE browser testa**, pa re-export (`bb_web_export` + `bb_xray_export`), pa Flaviova vizuelna provjera, pa commit buchenweb.
5. **Faza-2 analiza — OTVORENA:** no-op refine (40/240 identičnih scoreova) + granica gdje sudija prestaje da razlikuje.
6. **`v_status_faza_matrica`** — Flavio demonstrira analitičke funkcije (N faza bez altera).

---

## Lekcije

- **`pg_dump` kroz `balsam:run_command` "pukne" u alatu, a fajl svejedno nastane** (timeout MCP sloja, ne pad `pg_dump`-a). Isto se desilo 9. jula. **Provjeri `ls /tmp/*.dump` prije nego ponoviš.**
- **`nextval` nije transakcijski** — pala transakcija ostavlja rupu u sekvenci. Poslije neuspjelog INSERT-a sa `serial` PK: provjeri `id` prije nego se osloniš na njega.
- **Prikaz ≠ view.** Ne prikazivati rezultat drugog upita pod imenom postojećeg objekta.
- **Pivot s kolonom po fazi ne skalira.** Long format je izvor istine; pivot je prezentacija.
- Sudija i embedder su **jedina mjera koju imamo, i mjere sami sebe.** Blizu plafona "poboljšanje" i "kvarenje" gube sadržaj — postoji prag iznad kojeg mjera prestaje da razlikuje, i taj prag treba naći, ne pretpostaviti.

---

## Završno stanje

- **Baza:** `bb_metode` (2 metoda), `bb_faze` (3 faze: base, refine, refine-2), `bb_modeli` (+id 26, 27 za fazu 3). Backup `bb_s134_pre_metode.dump` (kontejner + host). Stari dumpovi obrisani (~7 GB).
- **Skripte:** `run_faza.sh` + `src/bb_faza_info.py` (novi), `run_refine.sh` (obrisan), `bb_web_export.py` (N-faza filter), `bb_aktivni_modeli.py` (docstring).
- **Viewovi:** `v_status_faza`, `v_status_faza_matrica`.
- **Podaci:** k22/hr faza 3 = 40 rečenica; k22/23/24 × de/hr/it/sr faza 2 = 20 rečenica; NER k22 (85 relacija).
- **Web:** kod netaknut → **BB_VERSION ostaje s133**, buchenweb bez commita.

---

*Flavio & Claude · Buchenberg · sesija 134 · 13. jul 2026.*
