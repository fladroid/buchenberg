# Session 106 — bb_04 sam puni faznog pobjednika (horizont #1 iz s105)

**Datum:** 1. jul 2026.
**Fokus:** Fazna struktura postaje živa kroz sesije. bb_04 sad SAM računa i upisuje faznog pobjednika u bb_prev_recenica_faza pri svakom runu — kraj ručne rekonstrukcije. Provjera read-path skripti (web/xray export). Novi brojači pobjednika po fazi, sad kad tabela postoji.

## Health snapshot (početak)
- bb_recenice: 38.333 · bb_prevodi_recenica: 1.049.545 · bb_prev_recenica: 204.793
- Git ulaz: buchenberg fc7105c (s105), buchenweb ab83475 (s102). BB_VERSION s102.
- 4 potpune knjige svih 14: Alice, Flatland, J&H, Hound.

## Zadatak (Flaviova formulacija)
s105 je bio jednokratni ručni popravak podataka. Sad: gdje modifikovati skripte na koje utiče multisession fazni pristup + izvještaji. Kandidati: pobjednik, refine, web_exp, xray_exp.

## Podjela write/read (dogovoreno)
- **Write path = bb_04 (pobjednik).** Jedini koji ODRŽAVA faza tabelu. Prioritet #1.
- **Read path = web_exp, xray_exp.** PRIKAZUJU. Feature, ne nužnost — poslije write patha.
- **refine (bb_03) = izvan priče.** Producer kandidata uzvodno; faznog pobjednika bira bb_04 nizvodno. Flaviova "skripta previše" — potvrđeno, ne dira se.

## 1. bb_04 faza-blok (glavni posao)
Fazu vodimo isključivo preko bb_modeli.faza_id (faza = svojstvo modela), BEZ pozicijske granice "100" — pozicijska ≤100/>100 logika bila je skela za s105 jednokratni popravak, sad prošlost.

Novi blok (dodat ISPOD postojećeg, postojeći ukupni-pobjednik dio NETAKNUT):
- SELECT DISTINCT ON (r.pozicija, m.faza_id), filter m.faza_id IS NOT NULL (sudija/mrtvi van), povlači m.temperatura (postojeći upit je ne vadi, tie-break je traži).
- Tie-break kao s105: fs DESC, naziv ASC, temperatura DESC, pr.id ASC.
- DELETE opsega + INSERT (isti obrazac kao za bb_prev_recenica, simetrično, idempotentno).
- Rečenica >100 (samo faza-1 kandidati) → samo faza-1 pobjednik; rečenica s refineom → obje faze. Prirodno preko faza_id.
- Backup: bb_04_pobjednik.py.bak_s106.

Verifikacija (Hound af 1–200):
- Referentni snimak prije: faza1=200, faza2=100.
- Run: Upisano 200 (ukupni) / Upisano faza 300 (200 faza1 + 100 faza2).
- Poslije: faza1=200, faza2=100 — poklapa snimak.
- Bez dupla: redova=distinct_prevoda=distinct(rečenica,faza)=300.
- Idempotentno: re-run → Upisano faza 300 opet, bez rasta.
- bb_prev_recenica dio netaknut.

**Rezultat: horizont #1 iz s105 RIJEŠEN.** Rekonstrukcija se ne ponavlja ručno; svaki pipeline run osvježi faznog pobjednika za svoj opseg.

## 2. Read-path provjera (Flaviova molba: startuju li bez poteškoća)
- web_export i xray_export: pokreću se bez greške, regenerisan produkcijski JSON u /var/www/buchenberg/data.
- Reader s X-Ray switch: 7 kandidata na refine opsegu (5 baznih + 2 refine), 5 van njega. Ispravno.
- VAŽNO: Reader X-Ray prikazuje SVE KANDIDATE (bb_xray_export čita bb_prevodi_recenica direktno), NE faznog pobjednika. bb_prev_recenica_faza zasad NEMA prikaz nigdje na webu. To je posao za sutra.

## 3. Novi brojači (sad kad tabela postoji)
Brojač A — ukupni pobjednici po fazi (cijela bb_prev_recenica, kojoj fazi pripada model pobjednika):
  base 200.841 / refine 3.952 (zbir 204.793)
Brojač B — apsolutni pobjednici po fazi na refine opsegu (poz 1–100, 9×14=12.600):
  base 8.648 / refine 3.952 (zbir 12.600)
Brojač C — Hound sr 1–200 (poslije proširenja refinea):
  1–100: base 74 / refine 26 · 101–200: base 63 / refine 37 · ukupno base 137 / refine 63

Refine je jači na 101–200 (37%) nego 1–100 (26%) — u skladu s hipotezom "refine ima headroom na slabijim seedovima" (s100/s103). Opservacija za Flaviovu osu, ne zaključak.

## 4. Hound refine proširen na 101–200 (Flavio pustio)
Hound (id 1) sad ima refine na 1–200, svih 14 jezika — PRVI izuzetak od "refine samo na prvih 100". Zato brojači tipa "poz 1–100" od sada potcjenjuju Hound refine. bb_04 preko faza_id ovo podnosi prirodno (bez hardcoded granice).

## 5. Memorija olabavljena
"KONFLIKT = STOP" se pojavljivao trostruko (custom instructions + mem 20 + mem 23) → preterana korekcija: proizvodio nesklade gdje ih nema, pitao za očito, tražio OK za razmišljanje. Skinut duplikat iz mem 20 i 23 (ostaje u custom instructions). Mem 23 dobila konstruktivnu formulaciju: sirovi formatirani rezultat PRVO pa komentar; konflikt=stop samo za stvaran nesklad.

## Stanje na izlazu
- Kod: src/bb_04_pobjednik.py (faza-blok) → commit.
- Baza: bb_prev_recenica_faza osvježena za Hound af 1–200 novom procedurom (ostatak i dalje s105 rekonstrukcija — brojevi identični); Hound refine 101–200 (Flavio) + bb_04 preračun tamo gdje je pušten.
- Web JSON regenerisan (produkcija). buchenweb NEDIRNUT → BB_VERSION ostaje s102.
- Backup: bb_04_pobjednik.py.bak_s106.

## Sljedeće — SUTRA: web prezentacija + brojači (Flaviov plan)
1. **Self-refine dobro dokumentovati na webu** — Flaviu VAŽNO. Refine zaslužuje pun prikaz (anchored mutation, evolucija nad jezikom, dvije ose/dvije istine).
2. **Fazni pobjednik → prikaz na webu.** bb_prev_recenica_faza sad živa i tačna, ali je nijedan izvještaj ne čita. Dizajn: "base vs base+refine" prikaz (Reader? Stats?).
3. **Stats dvije tabele** (dizajn dogovoren s104): Tabela 1 by-engine (3 reda, % od totala), Tabela 2 by-configuration (7 redova, win-rate zasebne stope).
4. Home mini-vodič, about i18n, art.html v1, NLP Relation Extraction — širi web horizont.
