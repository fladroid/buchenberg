# Session 97 — 26. jun 2026.

**Fokus:** DB optimizacija (prioritet #1 iz s96) — health_check.py "Stanje prevoda" query. Dijagnoza → uzrok → popravka → dvostruka verifikacija. Query 7 min → 1.26s; cijeli health check 7:02 → 0:23. Pipeline/web nedirnut (Flavio vodi 3 paralelna prevodilačka procesa).

## Onboarding
- Project files → README (s96 stanje) → posljednje 3 sesije (s96/s95/s94) → health_check.py, sve po protokolu.
- Health check kroz nohup→log (s94 navika, Anthropic proxy stream timeout). Cold-start: **7:02 elapsed, 5% CPU** — odmah vidljiv potpis DB uskog grla (čeka, ne računa).

## Health snapshot (početak s97)
- Korpus: 38.333 rečenice, **701.730 prevoda** (+78.020 od s96), **133.074 pobjednika** (+16.400 od s96). Pipeline melje (3 paralelna procesa, Flaviova taktika).
- Novo kompletno na svih 14 jezika (prev=pobj): uz Alice/Flatland/Jekyll&Hyde sad i **Big Four** pobj=1000 svuda.
- Asimetrija namjerna (NIJE anomalija): Hound de/hr/it/sr=3852 pobj, ostali 1400; Dracula/Moby/Romeo core-4 puni, ostali ~200.
- Infra: PG 17.9, Ollama 35 modela (gemma3/ministral/gemma4 OK), NLLB keš + transformers OK, venv kompletan.
- Git na ulazu: buchenberg a0e787d (s96), buchenweb f2b94b4 (s96), oba sinhronizovana. Sitnica: README.md.bak_s96 neuračunat (*.bak u .gitignore bez _sNN sufiksa).

## Urađeno — DB optimizacija health_check query

### Dijagnoza (X-Ray, sve mjereno)
1. **time na health checku:** 7:02.16 elapsed, **5% CPU** → proces čeka bazu, ne računa. Da je CPU usko grlo, user≈elapsed; umjesto toga 19s user + ~422s čekanja.
2. **EXPLAIN starog query-ja:** Nested Loop Left Join rows=753.023.732 (750M!), cost 17.2M, JIT se pali (43 funkcije). Dijagnoza potvrđena: **baza, ne CPU, ne promet, ne autovacuum** (procjene kardinalnosti zdrave).
3. **Uzrok:** fan-out — prevod (pr) × pobjednik (po) po knjiga×jezik grupi u istom SELECT-u → djelimični kartezijanski produkt (~700k × ~1073 = 750M redova). COUNT(DISTINCT) onda mora deduplikovati tih 750M. To je razlog što DISTINCT uopće postoji (poništava fan-out double-counting). Klasičan anti-pattern.

### Popravka — razdvojene agregacije
Dvije nezavisne pod-agregacije (CTE), spojene po knjiga×jezik:
- **prev CTE:** COUNT(DISTINCT pr.recenica_id) nad bb_prevodi_knjige ⋈ bb_prevodi_recenica. DISTINCT legitiman (1 rečenica × 5 modela), jeftin (~700k, ne 750M).
- **pobj CTE:** goli COUNT(*) nad bb_prev_knjige ⋈ bb_prev_recenica (već 1 red po pobjedniku, nema fan-outa).
- Glavni SELECT: prev LEFT JOIN pobj, COALESCE(...,0). Vraća iste 4 kolone u istom redoslijedu → Python sloj (raspakivanje for naziv, kod, prev_rec, pobjednici) nedirnut.

### Verifikacija (dvostruka — tačnost pa brzina)
- **EXPLAIN ANALYZE novog:** 1259ms, krajnji join 126 redova (9 knjiga × 14), JIT se gasi (Inlining/Optimization false). Jedini preostali teret: external merge sort 15MB na disk (work_mem; fino podešavanje, neobavezno).
- **diff stari vs novi izlaz:** **bit-identično** (oba 126 redova, 5044 bajta). Tačnost dokazana prije slavlja.
- **Pravi test (cijeli health check):** **0:23.56 elapsed, 88% CPU** (vs 7:02, 5%). user vrijeme nepromijenjeno (18.74s) → CPU posao nikad nije bio problem; nestalo ~400s čistog čekanja na bazu. Preostalih 23s = transformers import + 3 Ollama round-tripa.

### Primjena u kodu
- Backup: src/health_check.py.bak_s97.
- Izmjena: Python str.replace() s assert s.count(old)==1 guard (ne sed). Samo SQL string između cur.execute("""..."""); ostatak netaknut.
- Verifikacija: grep -c 'WITH prev AS'=1, grep -c stari fan-out join=0, ast.parse sintaksa OK.

## Lekcije
- **90% loših DB performansi = korisnički SQL** (Flaviovo iskustvo, ova sesija to udžbenički potvrđuje). Ne baza, ne hardver, ne promet od 3 paralelna procesa (~3–30 upisa/s = šum za PG).
- **time na sumnjivo sporom procesu = prva dijagnoza.** Wall-clock vs CPU% odmah razdvaja "čeka I/O" od "računa". 5% CPU = čeka; 88% = radi.
- **Fan-out + COUNT(DISTINCT) anti-pattern:** kad COUNT(DISTINCT) postoji da poništi double-counting iz joina, to je signal da agregacije treba razdvojiti, ne deduplikovati naduvani rezultat.
- **Stream timeout na dugom upitu = proxy-side** (Anthropic infra, ne foxuno/balsam). Komanda nastavlja na serveru; provjeriti rezultat zasebno (fajl postoji?), ne ponavljati slijepo.
- Verifikacija prije brzine: brz pogrešan upit je gori od sporog tačnog. diff identičan je uslov, ne bonus.

## Stanje na kraju
- **BB_VERSION: nepromijenjen (s96)** — sesija nije dirala web; cache-busting nepotreban (svjesna odluka).
- Git: buchenberg (health_check.py + session_97.md + README §9 snapshot/§14 DB-opt URAĐENO). Selektivni git add (ne -A) zbog .bak fajlova. buchenweb nedirnut.
- Kod: health_check.py query optimizovan i verifikovan. Pipeline nedirnut.
- Backup: src/health_check.py.bak_s97.

## Sljedeće (po prioritetu)
1. ~~DB optimizacija health_check~~ ✅ URAĐENO (s97). Opciono dalje: work_mem bump da prev-sort stane u RAM (sad 15MB na disk) — palo bi <1s; fino podešavanje.
2. Isti fan-out pattern provjeriti u drugim agregacijama/reportovima (stats.html backend, bb_web_export) — ako negdje COUNT(DISTINCT) poništava join double-counting, isti refaktor.
3. Length bucketing za NLLB (opciono, nula drifta).
4. Proširenje prevoda (Flaviova taktička odluka — vodi sam).
5. art.html v1, about.html i18n, learn.html nove igre, bb_web_export refaktor (v_pobjednici).
6. NLP Relation Extraction — rasplet kao ulaz (leži od s90).

---

*Flavio & Claude · Buchenberg · Session 97 · 26. jun 2026.*
