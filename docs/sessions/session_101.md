# Session 101 — 29. jun 2026.

**Fokus:** Web prezentacija — iskrenost brojeva. Razriješen konfaund "prevod rečenice" vs "rečenica": korpus je 38.333 izvorne rečenice, ne ~186k. Uveden corpus funnel, cijeli "Current status" preseljen Home → X-Ray Stats, dodana definiciona nota. Pipeline nedirnut (Flavio vodi prevode u pozadini).

## Onboarding snapshot (ulaz s101)
- Korpus: 38.333 rečenice, 945.610 prevoda, 185.870 pobjednika. Health 0:24, 89% CPU (s97 DB-fix se drži).
- Knjige prev=pobj na svih 14 jezika: Alice, Flatland, Jekyll & Hyde.
- Git: buchenberg 1b54dd5 (s100), buchenweb 7dc6863 (s99). BB_VERSION s99.

## Problem (Flavio)
- Nigdje nije rečeno koliko EN rečenica imamo u 9 knjiga. Svuda se provlači "~186k prevedeno" — što se lako čita kao "186k rečenica", a to su rečenica-jezik parovi.
- Tri različita broja koja se brkaju: **38.333** izvorne rečenice / **~947k** kandidata (5 konfig × temp × 14 jezika) / **~186k** izabranih prevoda (rečenica-jezik parovi).
- Odluka: NE ignorisati. X-Ray projekat — površinski broj ne smije lagati. Ali ni pretjerivati objašnjenjem.

## Riješeno — corpus funnel
- **Lijevak umjesto jednog broja:** `38.333 rečenice → 947k kandidata → 186k izabranih prevoda`, podnožje `9.633 rečenice potpuno na svih 14 jezika`. Bolji pitch nego prije — veliki broj (947k) postaje dokaz mehanizma, ne zbunjujuća brojka.
- **full_all_langs = 9.633** (NE 4.033 kako sam pretpostavio iz Alice+Flatland+J&H). Baza demantovala pretpostavku — druge knjige (Hound/Frankenstein/Big Four gornji dijelovi) imaju rečenice u svih 14 jezika. Dinamički upit hvata što oko ne vidi. **Pouka: ne hardkodirati brojeve iz health-tabele.**

## Arhitektonska odluka — seoba Home → Stats (Flavio)
- Cijeli "Current status" (stat kartice + funnel + 3 CTA dugmeta) seli s Home na X-Ray Stats. **Brojevi pripadaju stranici koja postoji zbog brojeva.** Home ostaje čist pitch.
- Flaviova odluka bolja od Claudeovog prijedloga (dupliranje funnela na obje stranice). Nema dupliranja jer nema dvije lokacije.
- Uklonjena i 3 CTA dugmeta (Browse/About/Stats) — nav header ionako vodi svuda; redundantna.

## Backend (bb_web_export.py, get_stats)
- +4 polja u summary: `total_sentences` (COUNT bb_recenice), `total_candidates` (COUNT bb_prevodi_recenica), `total_languages` (COUNT DISTINCT jezik), `full_all_langs` (rečenice s pobjednikom u SVIM jezicima — dinamički `COUNT(*) FROM bb_jezik`, ne konstanta 14).
- Trošak mjeren prije implementacije (s97/s99 navika): 6ms+77ms+283ms ≈ 370ms. Export nepromijenjen ~25s.

## Frontend
- **Home:** uklonjen lažni "Sentences translated" (zbrajao `l.sentences` preko svih jezika = ~186k pod etiketom "rečenice"). Uklonjen Current status + CTA. JS sveden na i18n. Stranica laganija (ne treba više stats.json ni books.json fetch).
- **Stats:** funnel + definiciona nota + nova "Target languages" (14) kartica. Razjašnjen id-konfaund: kartica `stat-total-langs` zapravo nosi `total_booklangs` (126); nova `stat-target-langs` nosi 14.
- **Broj modela 4 → 3** (engine-i: gemma3/ministral/NLLB, NE konfiguracije).
- **CSS:** `.bb-funnel*` klase (light/high-contrast tokeni, mobilni: strelice rotiraju u vertikalni funnel).

## Definiciona nota (Stats)
- "Kako čitati ove brojeve" — zakuca tri pojma: (1) "prevod" = rečenica-jezik par, ne nova rečenica → zato prevodi > rečenice; (2) 3 engine-a → 5 konfiguracija (model × temp); (3) NLLB = dedicated/specialized MT model (encoder-decoder, deterministički temp 0) nasuprot gemma3/ministral = general-purpose LLM nagovoreni promptom.
- Suptilan format (bb-box, sivi tekst) — referenca koju potražiš, ne teza koju guramo.
- **Refine (7 vs 5) namjerno NIJE spomenut** — čeka svoj okvir (tema 2, negativan-nalaz eksponat).

## i18n
- `index_funnel_*` (8 ključeva × 5 jezika) — reupotrijebljeni na Stats (bez dupliranja; prefiks "index_" istorijska mrlja, čisti se pri budućoj nav centralizaciji).
- `stats_total_langs` + `stats_reading_note` × 5 jezika. SR ćirilica/ekavica, quote parity verifikovan po liniji.

## Greška uhvaćena u letu
- HTML funnel blok (korak 2) koristio `&ndash;` entitet, ali fajl ima literalni – (en-dash). `assert count==1` pukao tiho (bash bez `set -e` nastavio na echo, bez vidljivog tracebacka). Fajl ostao netaknut → bez štete. Ispravka: `DASH = "\u2013"` literalni znak. **Pouka: provjeriti stvarne bajtove fajla prije str.replace s posebnim znakovima.**

## Stanje na izlazu
- Funnel i seoba potvrđeni uživo: DuckDuckGo + Edge OK. Chrome cache zeza (poznato, ne kod).
- stats.json regenerisan: 38.333 / 954.010 / 186.670 / 9.633 / 14 jezika / 126 kombinacija — sve živo iz baze.
- Commit + push: buchenweb 7dc6863→62a992c, buchenberg 1b54dd5→23fa0b0. BB_VERSION s101 (čisto).

## Sljedeće
1. **Tema 2 — self-refine prikaz:** segregacija 2 refine pseudo-modela (J&H hr s1-100) iz glavnih agregata (winner-distribution sad pokazuje "7 modela"; 36/100 ne smije curiti kao "pobjede"). Negativan-nalaz X-Ray eksponat — 7 kandidata po rečenici, head-to-head 0/100 kao izložba ("failure modes kao filozofija").
2. **Home page-opisi (horizont):** proširiti Home kratkim opisom svake stranice (about/stats/books/reader/nlp/learn/geometry/art) — mini-vodič, Home kao raskršće.
3. **Stats grafike (Potez B, odgođeno):** winner-distribution kao pita (5-7 kriški = udjeli cjeline, pravi slučaj); coverage kao bar/heatmap (NE pita — previše kriški).

---
*Flavio & Claude · Buchenberg · Session 101 · 29. jun 2026.*
