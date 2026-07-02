# Session 107 — View sloj: v_prevodi_full kao majka svih upita

**Datum:** 2. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** učenje projekta iznutra + izgradnja denormalizovanog view sloja

---

## Kontekst

Plan iz s106 bio je web prezentacija, ali Flavio je preusmjerio: prvo naučiti
više o projektu poslije multi-faznih promjena, pa tek onda implementirati.
Format: Flavio izlaže principe korak po korak, Claude potvrđuje ili koriguje
prije sljedećeg koraka. Paralelno: Flaviovi noćni procesi prevođenja i
self-refine (sljedećih 100 rečenica, više knjiga) trče u pozadini — razlike
u brojevima tokom sesije su očekivan rast, ne nesklad.

## Flaviovo izlaganje (principi, ne skripte)

1. **Faze:** rečenica je potpuno prevedena kad prođe sve faze; redoslijed
   fiksan; svaka faza (osim prve) zavisi od prethodne (hint = anchored
   mutation). Broj faza namjerno apstraktan — struktura ga ne fiksira.
2. **Takmičenje po fazi:** ≥2 modela → objektivna (mašinska) ocjena →
   subjektivna (sudija koji nije prevodio) → ukupna ocjena (dio objektivne +
   dio subjektivne) → fazni pobjednik. Fazni pobjednik prve faze = apsolutni
   dok drugih nema; kasnije fazni može ali ne mora biti apsolutni.
3. **Doprinos faze:** primjer 100 rečenica / 20 F1 / 10 F2, faza 2 osvoji 3
   apsolutna od 10 → doprinos 30% NA PRAVOM NAZIVNIKU (opseg gdje se F2
   takmičila). Stvarni korpus: 3.952/12.600 = 31,4% — gotovo identično.
   Ključno pitanje uvijek: procenat od čega?

## Izgrađeno — view sloj (arhitektura: Flaviova ideja)

Konvencija: stari view-ovi NETAKNUTI; novi sloj nosi sufiks `_full`
(maksimalna denormalizacija: svaki ID + sve njegove vrijednosti; prefiks
izvora u imenu kolone: knjiga_, recenica_, jezik_, model_, faza_...).

| View | Redova (pri provjeri) | Uloga |
|------|----------------------:|-------|
| v_corpus | 38.333 | domen: knjige + originalne rečenice |
| v_prevodi_full | 1.116.345 | **MAJKA**: svi kandidati, sve ocjene, cijeli lanac |
| v_pobjednici_full | 215.989 | apsolutni pobjednici (pokazivač + pf.*) |
| v_pobjednici_faza_full | 233.789 | fazni pobjednici (+ takmicenje_faza_*) |

- v_prevodi_full: v_corpus + bb_prevodi_recenica + bb_prevodi_knjige +
  bb_jezik + bb_modeli + LEFT bb_faze + bb_embeddings; kompozitni i
  finalni_score po kanonskoj formuli (preuzeto iz starog v_prevodi).
  Izostavljen JEDINO prevod_vektor (1024-dim, praktičnost SELECT *).
- Pobjednički view-ovi: pokazivačka tabela + JOIN na majku (pf.*) — nula
  duplirane logike. Građeni NA view-ovima (Postgres inline-uje, besplatno).
- ODLUKA (durable): v_corpus ostaje iz baznih tabela, NE iz majke — 17.848
  rečenica (46,6%) nema još nijedan prevod; corpus iz majke bi bio krnji i
  pomičan. v_corpus = domen; v_prevodi_full = činjenice; razlika = napredak.

## Verifikacije (sve prošle)

- v_corpus COUNT = bb_recenice (38.333); GROUP BY po knjizi 14,7 ms.
- v_prevodi_full COUNT = bb_prevodi_recenica u istom snapshotu (živa baza!);
  tačkasti upit kroz 6 JOIN-ova 12 ms.
- v_pobjednici_full 1:1; v_pobjednici_faza_full 1:1 + INVARIJANTA
  (takmicenje_faza_id = faza_id modela pobjednika) prekršena 0 puta.

## Lekcije

- `ls | tail` bira leksikografski (session_100 < session_95) → **uvijek
  `ls -v`** za numerisane fajlove.
- PostgreSQL ne kešira REZULTATE upita, samo stranice (shared_buffers/OS);
  mala vruća tabela → identično vrijeme oba runa (~15 ms).
- Kolone u _full view-ovima nose prefiks izvora — porijeklo čitljivo iz imena.
- Analitičke (window) funkcije za procente u istom prolazu:
  ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (), 2).
- Uzgred uočeno: pobjednik Hound sr poz.1 nosi markdown zvjezdice u tekstu
  (`**Баскервиљски пас**`) — kandidat za listu poznatih artefakata.

## Protokol

KONFLIKT=STOP relaksiran (Flaviova korekcija): vrijedi samo za stvarne,
značajne nesklade; bez ponavljanja/najavljivanja; bez aktiviranja na sitnice.
Revizija ili brisanje pravila = zadatak za buduću sesiju, po Flaviovoj procjeni.

## Stanje na kraju

Korpus (živ, procesi trče): ~1,116M prevoda / ~216k pobjednika / 234k faznih.
Alice, Flatland, J&H, Hound potpune (svih 14 jezika). buchenweb NEDIRNUT →
BB_VERSION ostaje s102.

## Sljedeće

1. Brojači nad novim slojem: doprinos faze 2 (pravi nazivnik!) po knjizi/jeziku
   — Flaviovo otvoreno pitanje: prikaz po fazi ukupno i/ili po modelu unutar faze.
2. Web prezentacija (prenijeto iz s106): self-refine dokumentacija (anchored
   mutation, dvije ose), fazni pobjednik prikaz, stats dvije tabele — sad s
   view slojem kao izvorom.

---

*Flavio & Claude · Buchenberg · session 107 · 2. jul 2026.*
