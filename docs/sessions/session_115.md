# Session 115 — Korak 4 (web): čišćenje imena modela iz web prezentacije

**Datum:** 6. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Prvi dio Koraka 4 iz implementacione mape — reader legenda faza prikaz + Home (index.html) proza usklađena s KONCEPT-om. **Trajni princip usvojen: nijedan model se ne imenuje NIGDJE u web prezentaciji — opiši ulogu i proces, ne komponente.** Konkretne vrijednosti iz baze su izuzetak (podatak, ne opis).

---

## Health snapshot (početak)
- bb_recenice: 50.624 · bb_prevodi_recenica: 1.393.170 · bb_prev_recenica: 271.578 (blagi rast od s114, živa baza)
- Git ulaz: buchenberg d40cb0c (s114), buchenweb e1278f7 (s108.4). BB_VERSION s108.4.
- Novi par aktivan i funkcionalan (glm-5.2 + mistral-large-3:675b), sudija gemma4:31b OK, Hound Copy k22 test 10/10.

## Princip usvojen (trajno, cijela web prezentacija)
**Ne imenovati nijedan model — ni prevodioce, ni namjenski MT, ni sudiju.** Razlog (Flaviov argument + KONCEPT.md): modeli se mijenjaju često i iz nebitnih razloga (dva retirement talasa za nedjelju dana). Legenda/proza koja imenuje komponente zastari pri svakoj zamjeni; koja opisuje proces preživljava. Stari i novi prevodi trajno koegzistiraju u bazi (Copy knjige) → ista stranica prikazuje kandidate raznih modela kroz vrijeme. Sudija: "LLM odabran samo za tu ulogu, ne koristi se u prevođenju" → opisati po ulozi ("a separate LLM, chosen only to judge, never to translate"), bez imena.
- Izuzetak: kad se prikazuju konkretne vrijednosti IZ BAZE (stats brojevi) — to je podatak, ne opis.

## Urađeno

### A) Reader legenda (reader.html, statični HTML, 3 izmjene)
- **Model red:** uklonjena imena (gemma3/ministral/nllb-600M) + `-refine` pojam → "translation model behind this candidate... general-purpose cloud LLMs and one dedicated machine-translation model. Models are swapped over time... what matters is the score, not the name."
- **NOVI Phase red:** ubačen između Model i Self-Refine — objašnjava fazu korisnički ("Phase 1 = first pass, Phase 2 = self-refinement... the phase is what tells them apart"). Rješava lekciju 5 iz s114 (kandidati iste trojke vizuelno nerazlučivi bez prikaza faze).
- **Self-Refine red:** vezan za "Phase 2 in action", uklonjena implicitna veza sa `-refine` sufiksom; anchored mutation tekst zadržan.
- `t=` red netaknut (temp shema 0.8/0.1 čuva se — potvrđeno `temp=0.8` u JSON-u).
- Backup: `reader.html.bak_s115`.

### B) Home proza (nav.js i18n, 4 ključa × 5 jezika = 20 zamjena)
Ključevi koje index.html STVARNO renderuje (provjereno: index.html l.121–130 poziva samo tagline/hero_desc/sec_how/how_desc/how_desc2/pillar_bt/pillar_judge/pillar_refine/pillar_winner/opensource):
- **index_how_desc:** imenovao 3 modela + sudiju ("Gemma 3 12B, Ministral 3 14B, NLLB-600M... A fourth model, Gemma 4 31B") → "pool of models — several general-purpose LLMs... plus a dedicated machine-translation model. A separate LLM, chosen only to judge and never to translate..."
- **index_how_desc2:** "Two refine models" → "The pipeline re-translates..." (proces, ne broj)
- **index_pillar_judge:** "Gemma 4 31B evaluates..." → "A dedicated LLM, used only for judging..."
- **index_pillar_refine:** "fed back to two refine models" → "fed back as a hint and re-translated..."
- Netaknuti (provjereno da ne imenuju): tagline, hero_desc, pillar_bt, pillar_winner, opensource.
- Backup: `nav.js.bak_s115`.

### Mrtvi ključevi (otkriveno, NISU dirani)
`index_funnel_*`, `index_lbl_*`, `index_sec_status`, `index_cta_*` postoje u nav.js rječniku ali ih index.html NE poziva (grep u index.html prazan). Ostatak stare verzije Home stranice. Kandidat za čist-up u zasebnom prolazu. Zato "9 books"/"14 languages"/"5 configs" na Home NE postoje (Flavio to primijetio — natjeralo na provjeru umjesto pretpostavke).

## Verifikacija
- grep: nula imena modela / brojeva u renderovanim index ključevima, svih 5 jezika.
- Statička provjera nav.js: backtickovi parni (46), vitičaste balansirane (72/72), navodnici u pillar ključevima parni.
- Browser test (Flavio): s115 (6 Jul 2026) — sve korekcije teksta OK, svi jezici rade, reader legenda OK.
- Procedura: README §"Web how-to: i18n" — izmjena postojećeg ključa = korak 1 (svih 5 blokova) + korak 2 (apply-linija u HTML, već postoji) + korak 3 (id, već postoji). Korak 2/3 zadovoljeni od ranije.

## Lekcije (ova sesija — ponovljene greške, moraju prestati)
- **NAJVAŽNIJE: koristiti dokumentaciju koju IMAM prije improvizacije.** Postoji README §"Web how-to: i18n prevod" s tačnim checklistom za UI izmjenu — nisam ga pročitao prije početka, nego grep-po-grep improvizovao. Tri sloja (README + session docs + memorija) pročitana na početku sesije pa nekorištena kad zatreba = ritual bez posljedice. Ovo se ponavlja i mora prestati.
- Izmišljena verifikacija: `node -c nav.js` — node nije instaliran na serveru; kanonska verifikacija je JSON `json.load` (za concepts) i browser test (za nav.js), NE node. Ne izmišljati alate; provjeriti šta postoji.
- BB_VERSION prati SESSION broj (s102, s99, s96...), goli `sNN` na commitu (ne `sNN.0`); sub-verzije `.1/.2` samo za browser-test korake unutar sesije. Potvrđeno iz `git log -- nav.js`.
- Ne pisati str.replace zamjene naslijepo za jezike čiji tačan sadržaj (prelomi, tagovi) nije pročitan — multiline blokovi (how_desc) razlikuju se po jeziku. Prvo pročitati doslovan sadržaj, pa zamjena.

## Završno stanje
- buchenweb: nav.js + reader.html izmijenjeni, BB_VERSION s115 (6 Jul 2026). Backup `.bak_s115` van gita.
- buchenberg: samo docs (ova sesija). Baza netaknuta.
- Git izlaz: buchenweb → commit s115 (slijedi).

## Sljedeće (Korak 4 nastavak + otvoreno)
1. **Korak 4 nastavak — Stats stranica (stats.html):** `stats_reading_note` (5 jezika) imenuje mrtve modele (gemma3/ministral) — treba isti tretman (opiši ulogu). Miješa imena modela + brojeve strukture (38.333, "3 engines", "5 configs") → brojevi vezani za otvoreni zadatak "stats dvije tabele" (s107/s108). Odlučiti obim tad.
2. **Mrtvi i18n ključevi** — čist-up index_funnel_*/lbl_*/cta_* ako se potvrdi da su neiskorišteni svugdje.
3. **Copy knjige puni runovi** novim parom (id 22/23/24) → staro-vs-novo na 12.291 rečenici po jeziku.
4. **Otvoreno s107/s108:** brojači faze 2 nad view slojem, stats dvije tabele (by engine / by configuration) — sad s čistom fazom u shemi.
