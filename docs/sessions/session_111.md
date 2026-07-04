# Session 111 — Mapiranje uticaja zamjene LLM modela (skripte + tabele)

**Datum:** 4. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Nezavisno od finalnog izbora zamjenskih modela — mapirati SVE što zamjena gemma3:12b/ministral-3:14b dotiče (skripte, tabele, konfiguracija) prije implementacije, koja čeka backup baze.

---

## Health snapshot (početak)
- bb_recenice: 38.333 · bb_prevodi_recenica: 1.282.840 · bb_prev_recenica: 248.360
- Git ulaz: buchenberg 9a556ca (s110), buchenweb e1278f7 (s108.4). BB_VERSION s108.4.
- Health check čist, sve provjere zelene (.env, PostgreSQL, Ollama Cloud, NLLB, venv, git).

## Kontekst
Nastavak s109/s110. Flavio je odlučio da uskoro zamjenjuje oba stara LLM-a (gemma3:12b, ministral-3:14b) — bez obzira da li će konačan izbor biti baš testirani par (gemma3:27b+ministral-3:8b, s110, statistički neodlučivo) ili neki drugi. Fokus sesije: identifikacija, ne implementacija.

## 1. Metodologija
Prije provjere na serveru — `conversation_search` kroz prošle sesije (pravilo iz s110). Potvrđeno poznato: `OCJENJIVANI_MODELI` hardkod (s110), stats-tabela dizajn (s104), `run_pipeline.sh` sadržaj (sesija ~52). Tek onda grep na server za stvarno trenutno stanje fajlova — ne osloniti se na pamćenje starih verzija.

## 2. Grep — kompletna mapa hardkodovanih referenci na modele
`grep -rn "gemma3\|ministral" --include="*.py" --include="*.sh" .` (isključen venv šum). Pronađeno tačno 3 kategorije:

**a) Aktivni bb_* pipeline — funkcionalni hardkod, TREBA izmjena:**

| Fajl | Lokacija | Šta |
|---|---|---|
| `run_pipeline.sh` | linija 48 | `for MODEL in "gemma3:12b" "ministral-3:14b"` — glavna petlja standardnog workflow-a |
| `run_refine.sh` | linija 25 | `for MODEL in "gemma3:12b-refine" "ministral-3:14b-refine"` — zavisi od odluke da li refine nastavlja s novim modelima |
| `src/bb_08_sudija.py` | linija 37-38 | `OCJENJIVANI_MODELI` hardkodovana lista (poznato iz s110) |
| `src/health_check.py` | linija ~149-150 | Hardkodovana test-lista ("Modeli koji se koriste u projektu") |
| `src/bb_01_init_lookup.py` | linija 39-42 | Seed lista — VEĆ zastarjela (temp 0.5, napušten davno u korist 0.8/0.1); nizak prioritet, samo ako se ikad ponovo pokrene od nule |

**b) Kozmetičko (nije funkcionalni hardkod):**
`bb_03_prevod.py` linije 6/12 — samo docstring primjeri; model se uvijek prosljeđuje kroz `--model`, nema hardkodovane logike.

**c) Legacy skriptovi (van bb_* pipeline-a) — provjereni u koraku 5.**

## 3. run_pipeline.sh — pun sadržaj provjeren
`EMBEDDER="multilingual-e5-large"` — ISPRAVNO (moja početna sumnja da je ostao MiniLM bila pogrešna, provjereno i odbačena — nije nesklad, samo netačna pretpostavka prije provjere). Jedini problem je model-petlja na liniji 48.

## 4. .env DB_NAME anomalija — istražena
`.env` ima `DB_NAME=buchenberg` dok se aktivno radi na bazi `bb` (README §4, health check). Hipoteza: legacy vrijednost iz ere prije "sesije 34" ("Povratak na osnovu... nova baza bb"). Potvrđena u koraku 5 — nije aktivan nesklad, samo neiskorišten ostatak.

## 5. Legacy skriptovi — provjereni i otpisani
`git log -1` po fajlu + `ls logs/` za tragove pokretanja:

| Fajl | Zadnji commit |
|---|---|
| run_test.py | 2026-05-28 |
| run_test_gemma4.py | 2026-05-25 |
| run_ga.py | 2026-05-21 |
| run_judge.py | 2026-05-29 |
| run_translations.py | 2026-05-29 |
| run_pivot.py | 2026-05-29 |
| run_pivot_llm_fix.py | 2026-05-27 |
| run_context.py | 2026-05-29 |
| ask_llm_hound.py | 2026-05-30 |
| test_embeddings.py | 2026-05-29 |

Svi zadnji put dirani 21.–30. maj — era prije "bb" šeme. Logovi s odgovarajućim imenima (`test_*`, `pivot_*`, `judge_*`, `run20/run30`, `ask_llm_hound.log`) svi stariji od `Jun 1`. Nijedan trag pokretanja u zadnjih mjesec i po, u projektu koji inače commituje gotovo svaki dan. **Potvrđeno mrtvi — van fokusa zamjene modela.** Ovo objašnjava i `.env` DB_NAME (korak 4): vjerovatno legacy vrijednost vezana za istu mrtvu eru (test_results/pivot_results tabele).

## Kompletna mapa — finalni nalaz

**Skripte za izmjenu (kad odluka o modelima padne):**
1. `run_pipeline.sh` (linija 48)
2. `run_refine.sh` (linija 25) — uslovno, zavisi od odluke o refineu
3. `src/bb_08_sudija.py` — `OCJENJIVANI_MODELI`
4. `src/health_check.py` — test-lista
5. `src/bb_01_init_lookup.py` — nizak prioritet

**Tabele:**
- `bb_modeli` — registracija NE zahtijeva schema promjenu (dokazano s110: samo novi red + `faza_id`)
- Nijedna druga tabela ne treba izmjenu (`bb_prevodi_knjige`/`bb_prevodi_recenica`/`bb_prev_recenica_faza` idu preko FK na `bb_modeli.id`)
- OPCIONO (trajni refaktor, Flaviova odluka): nova kolona u `bb_modeli` (npr. `aktivan` boolean) da stavke 3+4 gore čitaju aktivne modele iz baze umjesto iz hardkoda

**Konfiguracija:**
- `.env` `OLLAMA_MODEL=gemma3:12b` — čitaju ga samo legacy skriptovi; `bb_03_prevod.py` uvijek eksplicitni `--model`
- `.env` `DB_NAME=buchenberg` — vjerovatno legacy, ista mrtva era

**Legacy skriptovi — potvrđeno mrtvi, van fokusa:**
`run_test.py`, `run_test_gemma4.py`, `run_ga.py`, `run_judge.py`, `run_translations.py`, `run_pivot.py`, `run_pivot_llm_fix.py`, `run_context.py`, `ask_llm_hound.py`, `test_embeddings.py`

## Stanje na izlazu
- Baza: NETAKNUTA (čisto istraživanje/čitanje, ništa upisano)
- Kod: NETAKNUT
- Web: NETAKNUT → BB_VERSION ostaje s108.4
- README: §9 dobija s111 snapshot red, §14 dobija referencu na ovu sesiju

## Sljedeće
1. **Backup baze** prije bilo kakve izmjene (Flaviov zahtjev — prvi korak implementacije)
2. Finalna odluka o zamjenskim modelima (i dalje otvorena iz s110 — statistički neodlučivo na 42 rečenice)
3. Kad odluka padne: izmjena 5 identifikovanih fajlova + eventualni `bb_modeli.aktivan` refaktor ako se ide na trajno rješenje
4. Otvoreno iz s107/s108/s109/s110 nastavlja se nepromijenjeno (brojači faze 2, web fazni pobjednik, stats dvije tabele)

---

*Flavio & Claude · Buchenberg · session 111 · 4. jul 2026.*
