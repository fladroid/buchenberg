# Session 114 — Implementaciona sesija "jedan dah": refaktor + zamjena modela

**Datum:** 6. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Izvršenje kompletne mape iz s112 — backup, shema, skripte, test. Novi par mistral-large-3:675b + glm-5.2 u produkcijskom lancu. Završeno 9 dana prije retirement roka (15. jul).

---

## Health snapshot (početak)
- bb_recenice: 50.624 · bb_prevodi_recenica: 1.393.100 · bb_prev_recenica: 271.568
- Git ulaz: buchenberg 1e1110d (s113), buchenweb e1278f7 (s108.4). BB_VERSION s108.4.
- Nijedan pipeline proces ne trči (Flavio potvrdio — sve noćas završeno).
- Jedan tranzitorni ❌: transformers import timeout (15s) — ponovljen ručno, prošao za 1.4s. Lažni alarm pod opterećenjem.

## Korak 0 — Backup
- `pg_dump -Fc` cijele bb baze: 1.5G, custom format (selektivni restore moguć)
- Kontejner `/tmp/` + kopija na host: `/home/balsam/bb_backup_20260706_pre_refaktor.dump`

## Korak 1 — Shema (jedna transakcija, sve-ili-ništa)
1. `faza_id` NULL→1 za legacy redove id 2,4,6,7,8,9 (UPDATE 6)
2. `faza_id` SET NOT NULL
3. Nova kolona `aktivan boolean NOT NULL DEFAULT true`
4. `aktivan=false` svi osim nllb (UPDATE 16)
5. DROP UNIQUE(naziv,temperatura) → rename id 12/13 (skidanje `-refine` sufiksa, UPDATE 2) → ADD UNIQUE(naziv,temperatura,faza_id) — trojka je prirodni ključ
6. Registracija novog para (INSERT 6): id 18–21 faza 1 (2×2 temp 0.8/0.1), id 22–23 faza 2 (@0.8, Flaviova odluka — faza 2 nikad prazna, konvencija starog refinea)
- FK-ovi na bb_modeli.id nedirnuti — ~1,39M prevoda netaknuto, rename mijenja samo tekst
- Aktivni: faza 1 = nllb + novi par 2×2 (5); faza 2 = novi par @0.8 (2)

## Korak 2 — Skripte
- **`bb_03_prevod.py`** (4 izmjene): `--faza N` (default 1) ZAMJENJUJE `--refine` flag (Flaviova odluka — jedan izvor istine, `is_refine = faza >= 2`); lookup trojkom (naziv+temp+faza_id); `.replace("-refine","")` nestao; tihi `args.temp=[0.8]` default nestao (temp uvijek eksplicitan); poruka greške +faza
- **NOVI `src/bb_aktivni_modeli.py`**: helper — `--faza N` → linije `naziv|temp` aktivnih modela; jedan izvor logike za oba orchestratora; exit 1 ako faza prazna (fail-fast uz set -e)
- **`run_pipeline.sh`** (prepisan): petlja DB-vođena preko helpera (faza 1); NLLB kroz ISTU petlju (nestaje poseban blok — bb_03 interno prepoznaje nllb); `--temp` i `--faza 1` eksplicitni; modeli u log headeru
- **`run_refine.sh`** (prepisan): isti obrazac, faza 2, eksplicitni temp (fix tihog defaulta iz s112 audita)
- **`bb_08_sudija.py`**: `OCJENJIVANI_MODELI` hardkod OBRISAN → `AND m.aktivan` u upitu. Suptilnost provjerena: zamrznuti kandidati su svi već ocijenjeni (pobjednik ⇒ sudija_avg); NLLB pre-fetch pokriven (nllb aktivan). Bonus renamea: `aktivan` pokriva obje faze bez nabrajanja imena. `bb_08_sudija1.py` OBRISAN (git rm)
- **`health_check.py`**: used_models dict DB-vođen (distinct aktivan naziv bez nllb, sudija gemma4:31b hardkodovan kao i u bb_08); WARN + nastavak ako upit padne
- **`bb_xray_export.py`**: `faza` polje u JSON (SELECT `m.faza_id` + unpack + candidate dict) — bez ovoga kandidati faza 1/2 istog imena nerazlučivi
- **`bb_01_init_lookup.py`**: svjesno ODGOĐEN (nizak prioritet po mapi — samo za rekonstrukciju od nule)

## Korak 3 — Test (Hound Copy id 22, hr, 1–10)
- **Bazni lanac** (`run_pipeline.sh`, 4m31s): 5 konfiguracija × 10 = 50 kandidata; sudija OK; pobjednici 10 + fazni 10. Prvi dojam (n=10!): glm-5.2 7/10, mistral 3/10, NLLB 0; finalni 0.955–0.990
- **Refine lanac** (`run_refine.sh`, 7m29s): +20 kandidata faze 2; fazni pobjednici 10+10; **s4 = prva refine pobjeda novog para** (glm-5.2@0.8 faza 2 preuzeo apsolutnog pobjednika iz bazena od 7) — KONCEPT invarijanta "najbolji preko SVIH faza" radi
- **X-Ray export**: `--knjiga 22 --jezici hr` → JSON verifikovan Pythonom: 10 rečenica, kandidati {1: 50, 2: 20}, s4 pobjednik faza=2
- **Web export** (data-only, Flaviov zahtjev za pregled): tr_22_hr 10/3852, stats 8 modela, 12 knjiga. Flavio pregledao prezentaciju — sve očekivano

## Iznenađenja / lekcije (i pored detaljne pripreme)
1. **`foxuno:run_command` radni dir = `/home/balsam/mcp_foxuno`**, NE projekat — relativne putanje varaju; uvijek apsolutna putanja ili `cd /home/balsam/buchenberg &&`
2. **`.env DB_NAME=buchenberg` je bezopasan legacy** (iznenadilo Flavija): bb skripte HARDKODUJU `dbname="bb"` — misterija s111 zatvorena do kraja
3. **transformers import može tranzitorno timeoutati** pod opterećenjem — ponoviti prije proglašenja kvara
4. **Stats po imenu sada stapa faze** (rename posljedica): gemma3:12b@0.8 faza 1 i faza 2 pod istim imenom — argument više za fazne stats tabele (horizont)
5. Reader X-Ray: kandidati iste trojke bez prikaza faze izgledaju identično (s4: dvije glm-5.2@0.8 kartice) — očekivano do Koraka 4

## Stanje na izlazu
- Baza: nova shema bb_modeli (faza_id NOT NULL, aktivan, UNIQUE trojka, 23 reda) + 70 test kandidata / 10 pobjednika / 20 faznih za k22
- Kod: bb_03, bb_08, health_check, bb_xray_export izmijenjeni; bb_aktivni_modeli NOV; run_pipeline/run_refine prepisani; bb_08_sudija1 obrisan; `.bak_s114` kopije van gita
- Web: kod NETAKNUT → BB_VERSION s108.4; data regenerisan (web export)
- Backup: /home/balsam/bb_backup_20260706_pre_refaktor.dump (1.5G)

## Sljedeće
1. **Korak 4 (web)**: reader legenda — faza prikaz umjesto `-refine` opisa; nav.js proza po KONCEPT-u bez brojeva, svih 5 jezika
2. **Copy knjige puni runovi**: novi par na id 22/23/24 → staro-vs-novo poređenje na 12.291 rečenici
3. bb_01_init_lookup refaktor (nizak prioritet); otvoreno iz s107/s108 (brojači faze 2, stats dvije tabele — sad s čistom fazom u shemi)

---

*Flavio & Claude · Buchenberg · session 114 · 6. jul 2026.*
