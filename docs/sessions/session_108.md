# Session 108 — Web prezentacija self-refine na Home + i18n raskrivanje

**Datum:** 2. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** artikulisati fazu 2 (self-refinement) na prvoj stranici portala, prevesti na svih 5 UI jezika, i dodati mutaciju u Key Concepts. Uz to: X-Ray higijena dokumentacije (memorija ↔ README ↔ session ↔ baza).

---

## Health snapshot (početak)
- bb_recenice: 38.333
- bb_prevodi_recenica: 1.122.010 (živo — Flaviovi procesi prevođenja trče; rast od s107 ~1.116M je očekivan, ne nesklad)
- bb_prev_recenica: 215.990
- Git ulaz: buchenberg f004df7 (s107), buchenweb ab83475 (s102). BB_VERSION s102.
- Alice, Flatland, J&H, Hound potpune svih 14 jezika.

## 1. X-Ray higijena dokumentacije (početak sesije)
Provjera slojeva; razdvojen živi rast (nije nesklad) od stvarnih nesklada:
- README header s104 → **s107** (footer je već bio s107; header zaostajao 3 sesije).
- README §1 authorship „more than 70" → **100** documented sessions.
- README §9 dobio **s107 snapshot red** (§5 i footer su bili ažurirani za s107, §9 nije — nekonzistentan isti commit).
- Obrisano **10 `.bak_*`** netracked fajlova (git ls-files prazno = nijedan .bak nije praćen; 2 ignorisana — run_ga.py.bak, bb_02_insert_knjiga.py.bak — poštedjena). „Bak u gitu" = ono što `git status` vidi (untracked, ne-ignorisano).

## 2. Home „How it works" — faza 2 artikulisana (s108.1)
Stara sekcija opisivala JEDNOFAZNI pipeline; činjenice faze 1 tačne ali nepotpune. Tri izmjene (index.html hardkod):
- `#how-desc` prvi pasus završava „first phase"; dodat drugi pasus (self-refinement, anchored mutation, hibrid ne samo modela nego faza).
- Nova kartica **🧬 Self-refinement** (`#pillar-refine`), umetnuta između LLM judge i winner.
- Winner kartica: „no single model — **or phase**", „**across both phases**".
`.bak` kopija index.html napravljena prije diranja.

## 3. Grid 2+2 (s108.2)
Grid je bio `repeat(auto-fill, minmax(260px,1fr))` = „koliko stane" (kod Flavija 3+1). Za uravnoteženo → `repeat(2, 1fr)`. (Pojašnjeno: „grid = 4" značilo je broj kartica, ne kolona; auto-fill je responzivan, ne forsira red.)

## 4. i18n prevod novog teksta na 5 jezika (s108.3) — KLJUČNO RASKRIVANJE
X-Ray otkrio da s108.1 hardkod izmjene NISU dovoljne: **izvor teksta je i18n rječnik u `nav.js`**, a JS na svakom jeziku (uklj. EN) prepisuje hardkod (`getElementById(...).innerHTML = t(...)`). Hardkod u `index.html` je samo no-JS fallback.
- Posljedica: s108.1 izmjene prvog pasusa i winnera bile su **na EN pregažene** starim rječnikom (nisi primijetio jer si gledao lokalni jezik gdje je stari prijevod za fazu 1 ionako tačan); novi pasus + pillar-refine ostali EN (nemaju ključ → fallback).
- **Apply-kod je u `index.html`** (inline script, `getElementById`), **rječnik u `nav.js`** (5 blokova en/de/it/hr/sr, ključevi `index_*`). Dva fajla. (Prva verzija skripta pala jer sam apply anchore stavio u nav.js — assert count=0, ništa upisano.)
- Urađeno: `index_how_desc` ažuriran (first phase) ×5; novi `index_how_desc2` ×5; novi `index_pillar_refine` ×5; `index_pillar_winner` ažuriran ×5; 2 apply-linije u index.html; drugi `<p>` dobio `id="how-desc2"`.
- Termini (Flavio odobrio): self-refinement → Selbstverfeinerung / auto-raffinamento / samo-dorada; anchored mutation → verankerte Mutation / mutazione ancorata / usidrena mutacija.

## 5. Key Concepts — mutacija (s108.4)
- **self-refinement NEMA Wikipedia članak** (Madaan 2023 — arxiv/NeurIPS/blogovi, nijedan wiki). Flaviova odluka: Key Concepts sadrži SAMO postojeće engleske Wikipedia članke → self-refine ispada.
- **mutation IMA** — „Mutation (evolutionary algorithm)". Dodata kartica u `index`: 🎲, name „Mutation", wiki `Mutation_(evolutionary_algorithm)`, opis povezuje s self-refine kao anchored mutation. JSON validiran (json.load), index 11 → 12 kartica.

## 6. README how-to blok (Flaviova molba)
Dva „ponavljajuća" mjesta gdje uvijek zastanemo dobila trajnu referencu u README §10: (a) i18n UI prevod (rječnik nav.js + apply u stranici + hardkod=fallback), (b) Key Concepts kartica (concepts.json, wiki slug pun, name kratko, samo postojeći EN wiki).

## Ključne lekcije
- **i18n arhitektura (durable):** tekst = rječnik u `nav.js` (blokovi po jeziku, ključevi `index_*` / `<page>_*`); primjena = inline script u `<page>.html` (`t('kljuc')` → `getElementById('id').innerHTML|textContent`). Hardkod u HTML-u je no-JS fallback — JS ga prepisuje NA SVAKOM jeziku, uključujući EN. Novi tekst = ključ u SVIM jezičkim blokovima + apply-linija u stranici + id na elementu.
- **Key Concepts (durable):** `data/concepts.json` po stranici; `name` kratko bez zagrada, `wiki` pun slug; link `en.wikipedia.org/wiki/{wiki}`. Samo članci koji STVARNO postoje na engleskoj Wikipediji (Flaviova odluka).
- Grid `auto-fill` = responzivno „koliko stane"; `repeat(2,1fr)` = fiksno 2 kolone.
- Provjeri STVARNI mehanizam prije pisanja (grep rekao apply u index.html; pretpostavka nav.js bila pogrešna) — X-Ray „consult src before writing".

## Stanje na izlazu
- buchenweb **DIRNUT prvi put od s102** → BB_VERSION **s108.4** (sub-verzije s108.1–.4 pratile korake browser testa).
- index.html: 3 sadržajne izmjene + how-desc2 id + 2 apply linije. nav.js: 11 rječničkih zamjena (bump + 5 how_desc + 5 pillar). concepts.json: mutacija u index. `index.html.bak` = original prije s108.
- buchenberg README: higijena (header/authorship/§9 s107 red) + novi §10 how-to blok. 10 `.bak` obrisano.
- Korpus živ (procesi trče): ~1,122M prevoda / ~216k pobjednika.

## Sljedeće
1. **Brojači nad view slojem** (iz s107): doprinos faze 2 na pravom nazivniku po knjizi/jeziku — otvoreno: po fazi ukupno i/ili po modelu unutar faze.
2. **Web prezentacija — dublji sloj** (iz s106): fazni pobjednik prikaz (base vs base+refine), stats dvije tabele. Home self-refine uvod je sad postavljen; ovo je nastavak dublje.
