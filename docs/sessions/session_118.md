# Session 118 — Web Faza 1: tekstualne odluke za svih 9 stranica + reader plan

**Datum:** 7. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Nastavak web modifikacije (Korak 4) po s117 pristupu "prvo priprema, pa
implementacija u jednom dahu". Faza 1 = SVE tekstualne/i18n odluke, stranica po
stranica, zapisane u `docs/WEB-FAZA1.md`. Nula izmjena na web kodu — samo odluke.

---

## Health snapshot (početak)
- bb_recenice: 50.624 · bb_prevodi_recenica: 1.407.350 · bb_prev_recenica: 274.378
- k23 (Big Four Copy) napreduje: de 800/700, hr 780/700 (faza 2 refine u toku),
  it/sr 700/700 (bazna). k22 test 10/10 hr. k24 još 0.
- health: glm-5.2 test poziv pao na read timeout (30s) — mistral-large-3 i
  gemma4:31b OK. Prolazno cloud opterećenje, ne kvar.
- Git ulaz: buchenberg 1135410 (s117), buchenweb cd1e82e (s115). BB_VERSION s115.

## Urađeno — Faza 1 kompletna (9/9 stranica)

Sve odluke u `docs/WEB-FAZA1.md` (samodovoljan — pun tekst about + reader plan
unutra, bez zavisnosti od sandbox artefakata). 7 commitova (buchenberg):
00bddaf about · d30df0c stats · 3cdd303 books · 4907aba nlp · 30aad17 learn ·
7a512a0 geometry · 066b85f art+reader+zatvaranje.

### Trajni principi (učvršćeni/novi)
- **s115 princip** (nijedno ime PROLAZNOG modela u prezentaciji) primijenjen kroz
  sve stranice.
- **about = SVJESNI IZUZETAK** (Flaviova odluka): zadržava imena PRVIH modela, ali
  uokvirena novim ključem `about_p_models_note` ("ovo su prvi modeli, zamjenjivi;
  trajno je minimum/konfiguracija/uloga"). Ne krši KONCEPT — kvalitet definisan
  minimumom dozvoljava konkretnu ilustraciju iznad njega. Imena lakše shvate koncept.
- **Embedder e5-large = INVARIJANTA** — uvijek ostaje imenovan (geometry/art): browser
  ga stvarno pokreće (Transformers.js) + KONCEPT §2 "tačno 1 embedder".
- **Sudija (gemma4:31b) = zamjenjiv, ali AKTIVAN** — izbacuje se iz prezentacije zbog
  zamjenjivosti (s115), NE zastarjelosti. (Claude pogriješio rekavši "zastario";
  Flavio ispravio — gemma4:31b je jedan od najnovijih, aktivan sudija.)
- **X-Ray legenda (reader) + Key Concepts kartice = navedeni EN izuzetci** — namjerno
  samo engleski od početka X-Ray implementacije, ne prevode se.
- **Princip protiv izuzetaka** (Flavio): izuzeci su teški za održavanje; sve što je
  dosljedno ide na standard, izuzetci se izričito navode.

### Po stranici (sažetak; puni opis + plan u WEB-FAZA1.md)
- **index.html:** rječnik čist (s115). F2: G1 hardkod sync (imena u HTML fallbacku).
- **about.html:** NAJVEĆI posao. Okvir o imenima + NOVA sekcija "Self-refinement — a
  further round of the same pipeline" (naslov rješava "sve je pipeline"). Tekst EN +
  DE/IT/HR/SR gotov (5 ključeva: models_note, h_refine, refine1-4) + ASCII dijagram
  (Phase1|Phase2 → zajednički bazen). Suštinske tačke iz dijaloga: faza se NE ponavlja
  (ide unaprijed 2→3→4); seed=apsolutni pobjednik je suština refinea i razlog zašto ne
  može prije bazne; "self-" istaknut (sistem hrani sopstveni koncept+rezultate u sebe);
  2 modela na najvišoj temp (mutacija), MT model izostavljen (determinizam bi se ponavljao).
- **stats.html:** title/menu/naslov X-Ray Stats→Stats, X-Ray Statistics→Statistics
  (rješava G2). reading_note Home-put (bez imena+bez hardkod brojeva — živi funnel
  nosi brojeve). Key Concepts −2 kartice (X-ray style art, Rock Art X-Ray Style).
  Hardkod popis za F2 (funnel/modelShortName/modelClass/CSS). "Stats dvije tabele"
  ostaje ODVOJEN zadatak.
- **books.html:** `<title>`→"Library — Buchenberg"; `books_title` ujednačen na
  "Library" 5 jezika (bio "Translated Books" na DE/IT/HR/SR — nesklad s EN i konceptom
  "sve knjige su knjige"). DE Bibliothek/IT Biblioteca/HR Knjižnica/SR Библиотека.
- **nlp.html:** BEZ IZMJENE (najčistija).
- **learn.html:** BEZ IZMJENE; zabilježen i18n propust (hardkod EN stringovi u JS —
  toast/badge/placeholder) za eventualni budući zaseban prolaz.
- **geometry.html:** izbaciti "(Gemma4:31b)" iz geo_c4_p1 (5 jezika); e5-large ostaje;
  "Five models" i formula blok NE dirati.
- **art.html:** standardizovati naslov — novi `art_title` × 5 jezika + h1 id/apply
  (bila jedina stranica bez _title ključa); e5-large ostaje; MODEL_COLORS (stara imena
  u Tapestry legendi) = F2 tehnika.
- **reader.html:** ukloniti kao POTPUNI i18n izuzetak — migrirati nav+kontrole na
  centralni nav.js (14 reader_ ključeva × 5 jezika, preseljenje iz lokalnog I18N);
  obrisati lokalni I18N + ručno punjenje nav labela (nav.js to sam radi — uzrok zašto
  reader "ispada"). Legenda ostaje EN (navedeni izuzetak). A1: izbaci gemma4:31b iz
  Judge reda. SR author/language latinica→ćirilica (Аутор/Језик).

### Proaktivnost: uhvaćen preskočeni reader
Prvi "9/9 završeno" sažetak bio PREURANJEN — reader preskočen u prvom prolazu.
Uhvaćeno provjerom broja `## STRANICA:` zaglavlja (8≠9). Dopunjeno. Flavio pohvalio.

## Redoslijed Faze 2 (ODLUKA): "u jednom dahu"
Kao s114. Backup → stranice po redu (index G1 → about → stats → books → geometry →
art → reader) → JEDAN browser test svih × 5 jezika → JEDAN commit set (buchenweb) +
BB_VERSION bump + push verifikacija. Koristiti KAKO-JeziciUI.md (i18n) i
KAKO-KeyConcepts.md (kartice). Poslije: ažurirati KAKO-JeziciUI §2/§10 + STRANICE.md
(reader više nije potpuni izuzetak).

## Stanje na izlazu
- buchenberg: 7 commitova (00bddaf → 066b85f), sve u docs/WEB-FAZA1.md
- buchenweb: NETAKNUT, BB_VERSION s115 (Faza 2 dira web kod)
- Baza: netaknuta (živ rast k23 tokom sesije — Flaviovi procesi)

## Horizont (nepromijenjeno + novo)
1. **Web Faza 2** — implementacija svih 9 stranica "u jednom dahu" (plan: WEB-FAZA1.md)
2. Stats dvije tabele (by engine / by configuration, s107/s108) — odvojeno od F2
3. learn.html i18n propust (hardkod EN u JS) — zaseban prolaz
4. Copy knjige puni runovi (k22/k24) → staro-vs-novo poređenje
5. Brojači faze 2, phase winner web prikaz (s107/s108)
6. Dead i18n ključevi cleanup (index_funnel_* itd.)

---
*Flavio & Claude · Buchenberg · session 118 · 7. jul 2026.*
