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
