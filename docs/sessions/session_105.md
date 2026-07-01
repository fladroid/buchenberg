# Session 105 — Rekonstrukcija faznog pobjednika (horizont #1)

**Datum:** 1. jul 2026.
**Fokus:** Popraviti izgubljenog faza-1 pobjednika i uspostaviti trajni zapis faznog pobjednika po rečenici.

## Health snapshot (početak)
- bb_recenice: 38.333
- bb_prevodi_recenica: 1.049.545
- bb_prev_recenica: 204.793
- Rast od s104 (Flavio dopunjavao noću): Hound (id 1) potpuno preveden na svih 14 → **četvrta potpuna knjiga** (uz Alice, Flatland, J&H); Big Four (id 5) +~800 rečenica × 4 jezika. Sav rast izvan prvih 100 → refine opseg netaknut.

## Problem
bb_prev_recenica čuva samo jednog (ukupnog) pobjednika po rečenici. Gdje je refine (faza 2) prepisao baznog pobjednika (faza 1) — na 3.952 mjesta — bazni pobjednik-od-5 je izgubljen. Anti-X-Ray: senka ne prati original.

## Rješenje: nova tabela bb_prev_recenica_faza
Odluka (Flavio): nova tabela, NE mijenjati bb_prev_recenica. Izolovana od bb_04 (koji radi DELETE+INSERT po opsegu — dodavanje faza u istu tabelu bi ih obrisalo na sljedećem runu).

Struktura (isti obrazac kao bb_prev_recenica + faza):
- id PK, prev_knjige_id -> bb_prev_knjige, prevodi_recenica_id -> bb_prevodi_recenica, faza_id -> bb_faze
- UNIQUE (prev_knjige_id, prevodi_recenica_id, faza_id) — stara jedinstvenost + faza
- bez CASCADE

## Verifikacija prije upisa (korak-po-korak, Flaviov pristup)
1. faza_id popunjenost: faza 1 = 5 baznih (gemma3@0.8/@0.1, ministral@0.8/@0.1, nllb), faza 2 = 2 refine. NULL = sudija/neupotrijebljeni (NE "mrtvi" — razlika je uloga: prevodilac/sudija).
2. refine prevodi ukupno = 25.200 (12.600 rečenica × 2 modela)
3. po knjizi = 2.800 × 9; po ćeliji = 200 × 126 — ravnomjerno
4. refine strogo unutar poz 1–100 (min=1, max=100, van=0)
5. svih 12.600 rečenica <=100 ima svih 7 modela

## Punjenje
- **Korak 2 (<=100):** za svaku rečenicu argmax finalni_score po fazi. Tie-break: fs DESC, naziv ASC, temperatura DESC, prevodi_recenica_id ASC (determinističan, ponovljiv). -> 25.200 redova (12.600 faza-1 + 12.600 faza-2)
- **Korak 1 (>100):** ukupni pobjednik = faza-1 pobjednik (faze 2 nema). -> 192.193 redova faza-1

## Završno stanje
- bb_prev_recenica_faza: faza 1 = 204.793, faza 2 = 12.600, ukupno = 217.393
- Kontrola: faza 1 = svi pobjednici bb_prev_recenica (12.600 + 192.193) OK; distinct_prevoda = redova (nema dupla) OK
- bb_prev_recenica: netaknut

## Ključne lekcije
- Formula pobjednika = ukupni pobjednik JESTE pobjednik faze kojoj pripada; računa se samo pobjednik druge faze. Nema potrebe za "kontrolom 3.952 razlike" — to je bilo poređenje pogrešne ose.
- Nekoliko puta izmišljen problem gdje ga nema (tie-break faze-1 na refine rečenicama je nebitan jer nije operativan; UNIQUE constraint ne treba recenica_id jer je pobjednik po rečenici×fazi već jedan). Flavio ispravljao svaki put.
- faza = par (model, temperatura), ne samo model — čak i kad faza 2 trenutno ima jednu temp.

## Horizont
- bb_04_pobjednik.py da ubuduće SAM puni bb_prev_recenica_faza pri svakom runu (da se rekonstrukcija ne ponavlja ručno) — Flaviova odluka je li i kada
- Eventualno spajanje bb_prev_recenica + bb_prev_recenica_faza u jednu tabelu s atributom faza (Flavio: "posle mozemo spojiti")
- Otvoreno arhitektonsko pitanje faza-N (kumulativni vs izolovani argmax) — nije se pojavilo jer faza 2 je posljednja; vraća se kad dođe faza 3
