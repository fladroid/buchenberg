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
- UNIQUE(knjiga_id, jezik_id, model_id, embeddings_id) garantuje jedan
  `prevodi_knjige` red po kombinaciji → duplikati u PK su nemogući po šemi koju smo
  sami dizajnirali.
