# WEB-FAZA3-KORACI — Detaljan plan implementacije

**Status:** NACRT ZA PREGLED — nijedna komanda nije izvršena, ništa nije na serveru.
Pandan `WEB-FAZA1.md` (koji je pripremio Fazu 2), ali za DB-upit / export / reader sloj.
Kad Flavio odobri (uz eventualne izmjene), ovaj fajl se upisuje kao
`docs/WEB-FAZA3-KORACI.md` na server.

**Putanja:** jedna, neprekinuta (Flaviova odluka). A i B se razvijaju zajedno da se
format izlaza odluči **jednom**, ne dvaput. Svaka komanda i dalje ide kroz
prikaz → OK → izvršenje; BB_VERSION step-marker po koraku; bez grupisanja (lekcija s120).

---

## 0. Zaključane odluke (s Flaviom) vs otvorena pitanja

### Zaključano
- **D1 — Jedna putanja.** Nivo A (faza kroz postojeći JOIN) + tanki rez Nivoa B
  (`bb_prev_recenica_faza`) za reader "prije/poslije". Format izlaza biramo jednom.
- **D2 — Tabela 1 (by-engine): i engine I faza.** Svaki engine-red nosi razlaganje po
  fazi + ukupno. Flaviov primjer: `engine x: faza1 100, faza2 20, ukupno 120`. Nije
  jedan stopljeni win-rate — faza se vidi.
- **D3 — Stats broji APSOLUTNE pobjede razložene po fazi** (Flavio potvrdio), ne fazne
  pobjede iz `bb_prev_recenica_faza`. Sumira se čisto (100+20=120).

### Otvoreno (treba Flaviova odluka PRIJE relevantnog koraka; ne nagađam)
- **O1 — Definicija "engine" = `m.naziv`** (Flavio potvrdio). Tri aktivna engine-a =
  glm-5.2 / mistral-large-3:675b / nllb-600M, razlaganje po fazi unutar reda.
- **O2 — Tabela 1 prikazuje SVE istorijske engine-e** (Flavio potvrdio) — živa istina
  baze, uključujući zamrznuti par (gemma3:12b, ministral-3:14b). Do 5 redova po imenu.
  *(Ako se predomisliš za filter na aktivne — reci prije Koraka 4.)*
- **O3 — Obim re-exporta.** Test na jednoj knjizi/jeziku je fiksan (dole). Puni
  re-export = sve knjige, ili samo pogođene? Tvoja odluka poslije testa (WEB-FAZA3 §4).

---

## 1. Model podataka — šta je "pobjeda" (temelj cijele faze)

Dvije tabele pobjednika, dva različita posla (KONCEPT §4):

| Tabela | Šta čuva | Redova po rečenici×jezik |
|---|---|---|
| `bb_prev_recenica` | **apsolutni** pobjednik (najbolji kroz sve faze) | tačno 1 |
| `bb_prev_recenica_faza` | pobjednik **unutar svake faze** posebno | 1 po odigranoj fazi |

**Faza modela** živi na `bb_modeli.faza_id` (potvrđeno u `bb_xray_export.py`:
`JOIN bb_modeli m ... m.faza_id`). Isti bazni model na istoj temp ali drugoj fazi =
drugi `bb_modeli` red (trojka model×temp×faza, KONCEPT §3/§5). **Faza dolazi besplatno
svugdje gdje već JOIN-ujemo `bb_modeli`.**

### Ključna dizajnerska posljedica za stats
Obje tabele (1 i 2) broje **apsolutne** pobjede (`bb_prev_recenica`), razložene po
fazi pobjedničkog kandidata. To se čisto sumira (Flaviov primjer daje ukupno 120) i
Nivo A je dovoljan za oba (WEB-FAZA3 §3).

`bb_prev_recenica_faza` (Nivo B) hrani **isključivo reader "prije/poslije"** —
head-to-head uvid po rečenici, ne stats win-rate. Time izbjegavamo grešku na koju
ANALIZA.md upozorava: refine win-rate iz šireg bazena = selekcijska pristranost.
Stats mjeri "koliko finalnih odgovora je iz koje faze" (pošten, sumirajući broj);
head-to-head "je li refine pobijedio svoj seed" ostaje u reader before/after.

### Nazivnik win-rate-a (pošten po fazi)
Postojeći `get_stats()` već računa nazivnik odvojenim agregatom (`cand_map` = broj
kandidata po model×temp, bez fan-outa). Dodavanjem `faza_id` u ključ na **obje** strane
(brojnik i nazivnik), win-rate za faza-2 konfiguraciju dijeli faza-2 pobjede sa
faza-2 kandidatima — koji postoje samo gdje je faza 2 uopšte igrala (~18k). Nazivnik se
sam skalira ispravno; kod je već strukturiran da to podrži.
*(Napomena, ne akcija: NLLB pre-fetch bez pobjednika napuhuje NLLB nazivnik i spušta mu
win-rate — to je već slučaj u postojećem kodu i tačno je, NLLB jeste proizveo te
kandidate. Ostaje kako jest.)*

---

## KORAK 0 — Verifikacija šeme (prije ijedne izmjene koda)

Cilj: potvrditi kolone `bb_prev_recenica_faza` i JOIN put PRIJE nego finaliziram Nivo B
upit, i uhvatiti jednu stvarnu "prije/poslije" rečenicu za test. Sve read-only, svaka
prikazana i čeka OK.

**0a — kolone tabele:**
```sql
\d bb_prev_recenica_faza
```
**0b — raspodjela faza + potvrda brojeva iz WEB-FAZA3:**
```sql
SELECT faza_id, COUNT(*) FROM bb_prev_recenica_faza GROUP BY faza_id ORDER BY faza_id;
```
**0c — jedna konkretna rečenica koja IMA i faza-1 i faza-2 pobjednika** (test-meta za
kasniji reader before/after; knjiga/jezik biramo iz rezultata):
```sql
SELECT prev_knjige_id, prevodi_recenica_id, faza_id
FROM bb_prev_recenica_faza
WHERE prev_knjige_id IN (
  SELECT prev_knjige_id FROM bb_prev_recenica_faza
  GROUP BY prev_knjige_id, prevodi_recenica_id
  HAVING COUNT(DISTINCT faza_id) >= 2
)
LIMIT 10;
```
**0d — faza_id aktivnih modela** (za O1/O2 sanity):
```sql
SELECT id, naziv, temperatura, faza_id, aktivan
FROM bb_modeli ORDER BY aktivan DESC, naziv, faza_id, temperatura;
```

→ Poslije 0a–0d finaliziram Nivo B SQL (Korak 5) s tačnim imenima kolona.

---

## KORAK 1 — `bb_web_export.py :: get_translations()` — dodati fazu (Nivo A)

Faza je već dostupna kroz postojeći `JOIN bb_modeli m`, samo nije u SELECT-u.
Dodaje se kao **posljednji** SELECT element da se ne pomjera postojeći unpack.

**1a — SELECT dopuna** (anchor = posljednji red SELECT-a):
```python
# staro:
        ROUND(pr.sudija_fidelity::numeric, 4)   AS sudija_fidelity
# novo:
        ROUND(pr.sudija_fidelity::numeric, 4)   AS sudija_fidelity,
        m.faza_id                                AS faza
```

**1b — unpack + dict u main()** (anchor = duga `for ... in rows:` linija):
```python
# dodati 'faza' na kraj unpack tuple-a i u translated[pozicija] dict:
        "faza": faza,
```

**Metoda:** Python heredoc, `str.replace` + `assert s.count(old)==1` (KAKO-JeziciUI §7).
**Verifikacija:** `grep -n "faza" src/bb_web_export.py` + Python `compile()` sanity.

---

## KORAK 2 — `bb_web_export.py :: get_stats()` — faza u brojnik I nazivnik

**2a — win_rows: dodati faza_id:**
```python
        SELECT m.naziv, m.temperatura, m.faza_id, COUNT(*) AS cnt
    """ + base_from + """
        GROUP BY m.naziv, m.temperatura, m.faza_id
        ORDER BY cnt DESC
```
**2b — cand_map: dodati faza_id (simetrično nazivniku):**
```python
        SELECT m.naziv, m.temperatura, m.faza_id, COUNT(*) AS cnt
        FROM bb_prevodi_recenica pvr
        JOIN bb_prevodi_knjige pk ON pvr.prevodi_knjige_id = pk.id
        JOIN bb_modeli m ON pk.model_id = m.id
        GROUP BY m.naziv, m.temperatura, m.faza_id
```
```python
    cand_map = {(model, float(temp) if temp is not None else None, faza): int(cnt)
                for model, temp, faza, cnt in cur.fetchall()}
```
**2c — winners_by_config (Tabela 2):** red po (naziv, temp, faza):
```python
    winners_by_config = []
    for model, temp, faza, cnt in win_rows:
        tkey = float(temp) if temp is not None else None
        cand = cand_map.get((model, tkey, faza), 0)
        winners_by_config.append({
            "model": model, "temp": tkey, "faza": faza,
            "count": int(cnt), "candidates": cand,
            "win_rate": round(100.0 * int(cnt) / cand, 1) if cand else None,
        })
```
**2d — winners_by_engine (Tabela 1):** Python roll-up po (naziv, faza) + ukupno:
```python
    from collections import defaultdict
    eng_win  = defaultdict(lambda: defaultdict(int))   # naziv -> faza -> wins
    eng_cand = defaultdict(lambda: defaultdict(int))   # naziv -> faza -> candidates
    for model, temp, faza, cnt in win_rows:
        eng_win[model][faza] += int(cnt)
    for (model, temp, faza), cnt in cand_map.items():
        eng_cand[model][faza] += cnt

    winners_by_engine = []
    for model in sorted(eng_win, key=lambda m: -sum(eng_win[m].values())):
        phases = {}
        for faza in sorted(set(eng_win[model]) | set(eng_cand[model])):
            w = eng_win[model].get(faza, 0)
            c = eng_cand[model].get(faza, 0)
            phases[str(faza)] = {"count": w, "candidates": c,
                                 "win_rate": round(100.0*w/c, 1) if c else None}
        tot_w = sum(eng_win[model].values())
        tot_c = sum(eng_cand[model].values())
        winners_by_engine.append({
            "engine": model, "phases": phases,
            "total_count": tot_w, "total_candidates": tot_c,
            "total_win_rate": round(100.0*tot_w/tot_c, 1) if tot_c else None,
        })
```
**2e — return dict:** dodati `"winners_by_config"` i `"winners_by_engine"`.
Zadržati `"winners"` (stari ključ) **privremeno** dok stats.html JS ne pređe na nove —
uklanja se na kraju Koraka 4 da stara tabela ne pukne u međuvremenu.

**Verifikacija:** poslije re-generisanja `stats.json` → `python -c "import json; ..."`
provjera da `winners_by_engine` sumira (faza1+faza2 == ukupno po engine-u).

---

## KORAK 3 — Test re-export na JEDNOJ knjizi + globalni stats

Problem: `main()` radi sve (books/orig/tr/ner/stats) bez filtera. Da testiramo tr_*
format bez punog exporta, predlažem **malu, reverzibilnu dopunu**: `--knjiga ID`
filter na `get_books()` u `main()` (isti obrazac kao `bb_xray_export.py` koji ga već
ima). stats.json je globalan (agregati) — brz, generiše se svaki put.

- **Odluka za tebe (mini-O):** dodati `--knjiga` filter u `bb_web_export.py`? (Da =
  čist test na jednoj knjizi; Ne = idemo odmah na puni export.) Preporuka: Da.
- Test: `venv/bin/python src/bb_web_export.py --knjiga 22` → provjeri `tr_22_*.json`
  ima `"faza"` polje; `stats.json` ima nove ključeve.
- `json.load` na izlazima + spot-check jedne rečenice iz faze 2.

---

## KORAK 4 — `stats.html` — dvije tabele + JS + CSS + i18n

Referenca: KAKO-JeziciUI.md (i18n), KAKO-KeyConcepts.md (ne dira se ovdje).

**4a — HTML:** drugi kontejner tabele uz postojeći `winner-table-wrap`
(`config-table-wrap`; `renderConfigTable` i `renderEngineTable` ne postoje danas —
potvrđeno u WEB-FAZA3 §3).
**4b — JS render:**
- `renderEngineTable(winners_by_engine)` → red po engine-u, kolone faza1 / faza2 /
  ukupno (svaka: count + win_rate).
- `renderConfigTable(winners_by_config)` → red po model×temp×faza.
**4c — name-independence (dug iz WEB-FAZA1 stats):** `modelShortName()` / `modelClass()`
/ CSS `.model-gem3/.min3/.nllb` prepoznaju samo stari par → novi pada na sirovo ime /
bez boje. Ovo je trenutak da se preradi da bude nezavisno od imena (WEB-FAZA1 zadatak).
**4d — i18n:** novi ključevi × 5 jezika (naslovi obje tabele, "Phase 1/2", "Total",
"Win rate") — svih 5 blokova u `nav.js`, apply u `stats.html` inline scriptu, strukturni
trap `" },` (KAKO-JeziciUI §7).
**4e — ukloniti stari `"winners"` ključ** iz `get_stats()` return + stari
`renderWinnerTable` poziv (tek sad, kad nove tabele rade).
**4f — BB_VERSION step-bump; browser test svih 5 jezika (Flavio potvrđuje).**

---

## KORAK 5 — Nivo B: `bb_prev_recenica_faza` → `phases_<id>_<lang>.json`

**Finalizuje se tek poslije Koraka 0.** Provizorni oblik (kolone se potvrđuju u 0a):
```python
def get_phase_winners(cur, knjiga_id, lang_kod):
    """Za rečenice s faza-2 pobjednikom: faza-1 I faza-2 pobjednik odvojeno."""
    cur.execute("""
        SELECT r.pozicija, prf.faza_id, pr.prevod,
               ROUND(pr.translation_score::numeric,4) AS ts,
               ROUND(pr.sudija_avg::numeric,4)        AS judge_avg
        FROM bb_prev_recenica_faza prf
        JOIN bb_prev_knjige pk      ON pk.id = prf.prev_knjige_id
        JOIN bb_jezik j             ON j.id = pk.jezik_id
        JOIN bb_prevodi_recenica pr ON pr.id = prf.prevodi_recenica_id
        JOIN bb_recenice r          ON r.id = pr.recenica_id
        WHERE pk.knjiga_id = %s AND j.kod = %s
        ORDER BY r.pozicija, prf.faza_id
    """, (knjiga_id, lang_kod))
    # pivot po poziciji; emituj SAMO pozicije koje imaju faza_id=2
```
- Izlaz: `phases_<id>_<lang>.json` — **rijedak** (samo rečenice s fazom 2, ~18k ukupno,
  94% korpusa nema faza 2). Reader ga lazy-loaduje samo kad zatreba.
- Dodati u `main()` petlju uz graceful preskok kad nema faza-2 rečenica (ne piše prazan
  fajl).
- **Test:** knjiga/jezik iz Koraka 0c → provjeri da before/after par postoji i da se
  score-ovi poklapaju s bazom.

---

## KORAK 6 — `reader.html` — faza oznaka (A) + prije/poslije (B)

**6a — Nivo A oznaka (default prikaz, van X-Ray):** kad je apsolutni pobjednik iz
faze 2 (`sentence.faza === 2` iz `tr_*.json`) → mala oznaka ("refined" / "faza 2").
Ništa kad je faza 1 (94%).
**6b — Nivo B prije/poslije:** lazy-load `phases_<id>_<lang>.json`; za rečenice s
unosom prikaži "Faza 1: … (score) → Faza 2: … (score, POBJEDNIK)".
**6c — i18n:** oznaka + before/after labele = **default** prikaz → prevode se, svih 5
jezika (nav.js `reader_` prefiks). **X-Ray legenda ostaje EN hardkod** (navedeni
izuzetak, KAKO-JeziciUI §2) — before/after NIJE dio legende, pa se prevodi normalno.
**6d — BB_VERSION step-bump; browser test 5 jezika + potvrda da legenda ostaje EN.**

---

## KORAK 7 — Puni re-export + finalna verifikacija

- `venv/bin/python src/bb_web_export.py` (obim = O3 odluka).
- `bb_xray_export.py` **se ne dira** (faza već unutra) — po potrebi re-run radi
  svježine, ne zbog izmjene.
- `json.load` sanity na reprezentativnim izlazima; spot-check jedne faza-2 rečenice
  kroz cijeli lanac (stats → tr_ → phases_ → reader prikaz).

---

## KORAK 8 — Zatvaranje sesije

- `session_NNN.md` (fokus, health snapshot, urađeno, lekcije, sljedeće).
- README update (novi izlazi, `phases_*.json`, faza u stats/tr).
- Git — **odvojeno, pazi na grane:**
  - `bb_web_export.py` + `docs/` → **buchenberg** (grana **main**).
  - `stats.html` / `reader.html` / `nav.js` → **buchenweb** (grana **master**).
  - `data/*.json` je generisan / gitignore (osim `concepts.json`) → **ne** commituje se.
  - Push verifikacija: `git log -1 origin/<grana> --oneline` (output push-a zna izostati).
- Memorija.

---

## Šta ovaj dokument NE pokriva
- Pokretanje pipeline/refine runova (Flaviov posao, van plana).
- Diverzifikacija / nova familija modela (poseban budući okvir).
- SR `geo_c4_p1` miješanje pisama, word cloud ćirilica — sitni nevezani zadaci.
- learn.html hardkod EN stringovi — zaseban i18n prolaz (nizak prioritet).

---

*Nacrt za Flaviovu reviziju — 9. jul 2026. Nijedna komanda nije izvršena na server/bazu.*
