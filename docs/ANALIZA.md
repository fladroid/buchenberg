# Pristup analizi rezultata (refine / pipeline)

Pred svaku analizu refine ili pipeline rezultata — pročitati ovo prvo.

## Refine = anchored mutation
LLM kao gramatički-siguran operator mutacije; jedini operator koji čuva sintaksu
pri "evoluciji nad jezikom". To je most koji je nedostajao da se GA primijeni na
prevod. Refine NIJE diverzifikacija (to je zaseban okvir — drugi glas iz druge
familije).

## Dvije mjere, dvije istine
Refine se može mjeriti na dvije ose koje daju suprotne nalaze, i obje su tačne:

- **Head-to-head vs svoj seed** → 0/100 na jakim seedovima (s100, J&H hr). Tačno.
  Jak seed = pejsmejker, nema headroom-a; "popravi ovo" perturbuje optimalni anchor.
- **Gramatičan ostanak u prostoru** → uspjeh. Vođena varijacija nad jezikom ostaje
  smislena i gramatična (gemma3-refine sudija 0.851). To je Flaviova svrha.

**Pravilo:** pitaj ŠTA se mjeri prije nego proglasiš (ne)uspjeh. Ne kreni od
win-rate kao da je jedina istina. Pitaj Flavija koju osu analiza treba osvijetliti
prije prvog upita.

**Refine je Flaviu top tema — tehnički i emotivno.** Pristupi joj kao partner koji
zna njen značaj u projektu, ne kao SQL-poznavalac pred nepoznatom tabelom.

## Tehnički podsjetnici za upite
- Ne JOIN-ovati `bb_recenice` na `v_prevodi` (view već sadrži rečenicu) → fan-out,
  naduvani COUNT. Sirovi izlaz prvo; ako broj djeluje nemoguće, sumnjaj u svoj JOIN
  prije u podatak.
- Model nije na `bb_prevodi_recenica` — ide preko
  `prevodi_knjige_id → bb_prevodi_knjige (model_id, jezik_id)`.
- **s142:** `bb_prevodi_knjige` UNIQUE je sad 7 kolona:
  `(knjiga_id, jezik_id, faza_id, model_id, temperatura_id, prompt_id, embeddings_id)`
  — a1/a2/a3 su nezavisne ose (a1=model, a2=temperatura, a3=prompt), svaka sa svojim
  katalogom (`bb_modeli`, `bb_temperature`, `bb_promptovi`). `v_prevodi_full` i
  `v_pobjednici_full` već nose `faza_id`/`faza_naziv` direktno — koristiti njih, ne
  ručni JOIN.

## Kanonski upiti — obim i efekat po fazi

Koliko prostora faza zauzima (svi kandidati) naspram koliko stvarno pobjeđuje
(apsolutni pobjednici). Oba iz view sloja, bez ručnog JOIN-a.

**Obim (svi prevodi):**
```sql
SELECT faza_id, faza_naziv, COUNT(*) AS broj_prevoda,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS udio_pct
FROM v_prevodi_full
GROUP BY faza_id, faza_naziv
ORDER BY faza_id;
```

**Efekat (apsolutni pobjednici, `v_pobjednici_full`):**
```sql
SELECT faza_id, faza_naziv, COUNT(*) AS broj_pobjednika,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS udio_pct
FROM v_pobjednici_full
GROUP BY faza_id, faza_naziv
ORDER BY faza_id;
```

**Snimak (s143, 18. jul 2026):**

| Faza | Obim | Efekat (pobjede) |
|---|---|---|
| 1 base | 97.55% (1.568.905) | 98.27% (296.946) |
| 2 refine | 2.44% (39.286) | 1.73% (5.217) |
| 3 refine-2 | 0.00% (80) | 0.00% (5) |

Refine je 2.44% obima ali samo 1.73% pobjeda — gubi agregatno na cijelom korpusu,
konzistentno s malim kontrolisanim uzorcima (s134-138).

⚠️ **Tabela je PRIJE-GATE snimak.** Gated faze 4/5/6 (`refine-gated`,
`refine-lenient-gated`, `refine-strict-gated`) uvedene su u s144 i ne pojavljuju se
gore. Agregatni gubitak iznad odnosi se na NE-gated refine — mjeren nad svim
rečenicama, uključujući one bez headroom-a. Uz gate slika je obrnuta (93.4% pobjeda
kad je gate otvoren, vidi sekciju "Pouzdanost mjernih instrumenata" niže). To nije
kontradikcija nego potvrda pravila iz "Dvije mjere, dvije istine": ista mašinerija,
drugo pitanje — "koja konfiguracija" vs "ima li ova rečenica prostora".

---

## Pouzdanost mjernih instrumenata (s146, 20. jul 2026.)

Prije bilo kakve tvrdnje o "poboljšanju" — znati rezoluciju instrumenta koji to mjeri.

### Prag šuma sudije ≈ 0.003

Kroz korpus postoje rečenice gdje su različiti modeli/faze proizveli **doslovno
identičan tekst**, a sudija ih ocjenjivao odvojeno. Svaka razlika u ocjeni tu je
čist šum, jer isti tekst ne može biti bolji od sebe.

```sql
WITH klonovi AS (
  SELECT knjiga_id, jezik_kod, recenica_id, btrim(prevod) AS tekst,
         COUNT(*) AS n_kopija,
         MAX(sudija_avg) - MIN(sudija_avg) AS raspon_sudija
  FROM v_prevodi_full
  WHERE sudija_avg IS NOT NULL AND prevod IS NOT NULL AND btrim(prevod) <> ''
  GROUP BY knjiga_id, jezik_kod, recenica_id, btrim(prevod)
  HAVING COUNT(*) > 1
)
SELECT COUNT(*) AS grupa, ROUND(AVG(raspon_sudija)::numeric,4) AS avg_raspon,
       COUNT(*) FILTER (WHERE raspon_sudija = 0) AS identican_score
FROM klonovi;
```

**Snimak s146:** 212.443 klon-grupe / 498.843 prevoda. Prosječan raspon **0.0029**,
medijan **0.0000**, **98.74% dobilo identičnu ocjenu**.

**Posljedica:** sudija je precizan instrument. Rasipanje ocjena unutar bilo koje
grupe kandidata (tipično 0.19–0.29) je STVARNA razlika, ne šum.
⚠️ Ovo obara s137 nalaz ("17/30 klonova različit score") — n=30 bio je premali.

### Rasipanje komponenti — težine ≠ stvarni uticaj

```sql
SELECT COUNT(*) AS n,
       ROUND(corr(sudija_avg, kompozitni::double precision)::numeric,3) AS korel,
       ROUND(STDDEV(sudija_avg)::numeric,4) AS sd_sudija,
       ROUND(STDDEV(kompozitni)::numeric,4) AS sd_cosinus
FROM v_prevodi_full
WHERE faza_id = 1 AND sudija_avg IS NOT NULL AND kompozitni IS NOT NULL;
```

**Snimak s146 (1.561.907 prevoda):** korelacija 0.171, sd sudija **0.2065**,
sd cosinus **0.0277**.

Težina vrijedi samo srazmjerno rasipanju komponente:
- sudija: 0.6 × 0.207 = **0.124**
- cosinus: 0.4 × 0.028 = **0.011**

**Formula `0.4 × kompozitni + 0.6 × sudija_avg` u praksi rangira ~8% cosinusom,
~92% sudijom** — ne 40/60.

⚠️ **NE standardizovati komponente** (z-score/rank) da bi cosinus dobio "stvarnih 40%".
Izmjereno: promijenilo bi 24.98% pobjednika (k20/k21, 8.000 rečenica) — ali u smjeru
slijepih tačaka ispod. Nesklad između deklarisane i stvarne težine trenutno ŠTITI izbor.

### Cosinusove slijepe tačke (zašto ne pojačavati njegov glas)

Embedder je namjerno višejezičan → ne može primijetiti da prevod nije napravljen.

```sql
SELECT CASE
    WHEN btrim(lower(prevod)) = btrim(lower(recenica_tekst)) THEN 'neprevedeno'
    WHEN length(btrim(prevod)) = 0 THEN 'prazno'
    WHEN kompozitni >= 0.97 THEN 'cosinus vrlo visok'
    WHEN kompozitni >= 0.90 THEN 'cosinus normalan'
    ELSE 'cosinus nizak' END AS klasa,
  COUNT(*) AS n, ROUND(AVG(kompozitni),4) AS avg_cosinus
FROM v_prevodi_full WHERE sudija_avg = 0 AND prevod IS NOT NULL
GROUP BY klasa ORDER BY klasa;
```

Tri klase kvara koje cosinus ne vidi, a sudija hvata pouzdano (daje 0.000):
1. **Neprevedeno** — strani fragment ostavljen netaknut → cosinus **0.99** (2.784 sl., 0.17%)
2. **Slomljeno pismo** — latinično `w/y` u ćirilici → cosinus **0.95** (1.466 sr prevoda, 0.92%)
3. **Slomljena gramatika uz očuvane ključne riječi** → cosinus **0.97**

**Sudijine nule NISU kvar.** Provjereno u kodu: `parse_ocjene()` vraća `None` →
`continue` (bez upisa); `call_sudija()` na iscrpljenim pokušajima radi `raise`.
Nijedna nula nije sentinel — sve dolaze od modela. ~30% ih je na neprevedenom,
~33% na stvarno lošem, ostatak na tekstu s pokvarenim pismom/gramatikom.

### Gated refine — mjerenje efekta

Gate (`seed_score < prag`, default 0.95, s144) mijenja pitanje s "koja konfiguracija"
na "ima li ova rečenica prostora za poboljšanje". Mjeri se u dva koraka: koliko se
gate otvorio (obim) i ko pobjeđuje kad je otvoren (efekat).

**Snimak s146 (k20+k21, de/hr/it/sr, poz. 1–1000):**

| mjera | vrijednost |
|---|---|
| gate otvoren | 2.337 / 8.000 (29.2%) |
| gated refine pobjeđuje kad je otvoren | **93.4%** |
| prosječna delta vs seed | **+0.047** (16× iznad praga šuma) |
| klon-stopa (identičan tekst kao seed) | **0.7%** (bilo 16.25% prije s135 fix-a) |
| Δ sudija / Δ cosinus | +0.0597 / **−0.0038** |

⚠️ **Cijeli dobitak nosi sudija; cosinus lagano PADA.** Dosljedno s nalazom o
rasipanju — nije kontradikcija nego ista pojava.

**Po osama:** naturalness raste najbrže (+0.061…+0.078), iznad grammar i fidelity.
`refine-strict` ima najviši grammar ali najniži fidelity (+0.029) i najgori cosinus
(−0.010) — potpis "uljepšavanja". `refine-gated` (originalni, najblaži prompt) drži
najbolji balans.

### Granica koju mjera ne pokriva

Sudija mjeri tečnost; književnost tečnost namjerno krši. Izmjereni slučaj: Abbott
*Flatland* de, autorova namjerna složenica `SOMETHING-WHICH-YOU-DO-NOT-AS-YET-KNOW-...`
izbrisana refine-om i nagrađena s **+0.157 — najvećom deltom u uzorku**.

> **Ne mjerimo vjernost autoru. Mjerimo vjernost normi jezika.**

Publikovano na `limits.html` (s146). Sve iznad rečenice (prelom stiha, strofa,
vizuelni raspored, ilustracije) ne postoji u pipeline-u — jedinica je rečenica.
