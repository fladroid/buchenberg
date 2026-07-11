# Session 129 — DocRE: od provjere pretpostavki do kompletne implementacije (baza+web)

**Datum:** 11. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Dovršavanje DocRE (Dio 2 #1 iz s127/s128). Sesija je počela kao read-only
provjera pretpostavki iz s128, a završila kompletnom implementacijom: rječnik grupa,
tri nove tabele, produkcijski upis relacija (Hound), materijalizacija co-occurrence,
web-export relacija, i nlp.html treći ravnopravan pogled (DocRE) s tri infoboxa i
i18n na 5 jezika. DocRE je time zaokružen kraj-do-kraja.

## Health snapshot
Početak: bb_recenice 50.624, bb_prevodi_recenica 1.518.170, bb_prev_recenica
296.578 (nepromijenjeno od s125–s128). Git početak: buchenberg 1a776f5 (s128),
buchenweb 4c3e2d5 (s127). Sve zeleno, Ollama Cloud (glm-5.2, mistral-large-3:675b,
gemma4:31b) OK. 8 poznatih `.bak` + `bb_10b_docre_probe.py` (s128 proba) + poznati
lažni "buchenweb zaostaje". Kraj: korpus nepromijenjen; +3 NER tabele; +74 relacije
Hound; +3820 co-occ veza materijalizovano.

## Kontekst i tok
Flavio otvorio dan tražeći nastavak DocRE razvoja. Prva faza bila provjera s128
pretpostavki preko read-only upita:
- **Šema:** `pozicija` NIJE na `bb_ner_recenica` nego na `bb_recenice` (JOIN preko
  `recenica_id`). Ime entiteta = "Sherlock Holmes", ne "Holmes" (llm sloj).
- **Razriješeno razilaženje s126 vs s128 (#6):** stari co-occ = ista rečenica
  (Holmes–Watson 4×), novo mjerenje = pozicijski prozor ±10 (127×). DVIJE MJERE,
  ne kontradikcija. Materijalizovana `bb_ner_veze` čuva staru "ista rečenica" mjeru;
  DocRE `bb_ner_relacije` nosi par-vođenu.

## Urađeno

### 1. Sirovina za rječnik — puna proba (83 para)
`bb_10b_docre_probe.py --prag 5` na Houndu: 83 para ≥5 susreta → 75 opisa.
Distribucija susreta: 84 para na 3-4 (šum, izostavljeni pragom 5), 44 na 5-9,
23 na 10-19, 11 na 20-49, 5 na 50+. Puna lista opisa = sirovina za grupe.

### 2. Kristalisan rječnik `tip_veze` — 12 grupa + ventil
Iz 75 opisa, dvije klase: **P** (osoba–osoba, 8 grupa: srodstvo, prijateljstvo,
angazman, sluzba, istraga, zastita, prevara, susjedstvo) + **M** (osoba–mjesto,
4: kretanje, prebivaliste, posjed, radnja) + **O** (ostalo=ventil).
Flaviove odluke: (a) `klasa` = zasebna kolona (ne prefiks u tip_veze); (b) 12 je
prava granularnost; (c) lookup tabela (ne obične kolone) — obrazac kao
bb_model_registar.

### 3. Tri tabele — DDL (backup + kreiranje)
Backup prije DDL (pravilo s123): 1.5G → `/tmp/bb_backup_pre_docre_20260711_113342.dump`
(verifikovan pg_restore -l = 30 TABLE).
- `bb_ner_tip_veze` (tip_veze PK, klasa CHECK P/M/O, opis_grupe) — 13 redova.
- `bb_ner_veze` (co-occurrence: entitet1<entitet2, tezina; UNIQUE par).
- `bb_ner_relacije` (docre: izvor→cilj usmjeren, tip_veze FK, opis, smjer
  directed/mutual, dokaz, dokaz_pozicije int[], pouzdanost; UNIQUE izvor+cilj+tip).
- `method` NIJE u novim tabelama — implicitan preko entitet_id (s128).

### 4. `bb_10c_docre.py` — produkcijska skripta (commit 39ae0b1)
Prvi prolaz = par-vođena logika iz probe (nedirana). Drugi prolaz (NOVO): e5-large
embedduje slobodni opis → kosinus prema 12 CENTROIDA (varijanta b: centroid iz
SEED_OPISI, 75 opisa grupisanih). Argmax grupa; ispod praga → 'ostalo'.
- e5-large GOLIM `.encode()` (bez query:/passage: prefiksa) — konzistentno s
  bb_06_enkodiranje (uporedivi vektori).
- `--dry-run`: prvi+drugi prolaz, ISPIS kosinus-rastojanja (kalibracija), 0 upisa.
- Idempotentno DELETE knjiga + INSERT; `--knjiga N|all`.

### 5. Kalibracija praga + A/B bug fix + produkcijski upis
- **Dry-run (69 opisa):** svi kosinusi u pojasu 0.858–0.976 — prag 0.55 predaleko
  nizak. Odluka (Flavio): konzervativno **0.85** (subota, rano; ventil čeka druge
  knjige). "Mjeri pa definiši" (s90 obrazac).
- **A/B bug:** LLM povremeno vrati "izvor":"B"/"A" (slova iz prompta) ili "Ime
  (TIP)" — moja produkcijska provjera preskakala validne relacije (4 gubitka u
  dry-runu). Fix: `_norm()` mapira A/B→imena, skida " (TIP)" sufiks.
- **Produkcijski upis:** 74 relacije Hound (>69 dry-run, A/B fix vratio preskočene).
  Sve 12 grupa korištene; kvalitet visok golim okom (Holmes→istraga→Charles;
  Holmes↔Watson mutual; Stapleton→istraga→Baskerville "deceiving"). Granični:
  Barrymore→istraga→London (trebalo M/kretanje) — curjenje rječnika, za tjuning
  na drugim knjigama.

### 6. Materijalizacija co-occurrence (bb_ner_veze)
INSERT...SELECT svih parova/metoda/knjiga (ista-rečenica self-join → tabela):
3820 parova. `r2.method=r1.method` (co-occ unutar sloja). Verifikacija: stari
self-join vs nova tabela za Hound classic prag≥2 = BIT-IDENTIČNO (27 parova, suma
83). `get_ner_veze` prepisan da ČITA iz bb_ner_veze (s128: web-export read-only) —
format izlaza identičan → nlp.html netaknut.

### 7. Web export relacija (bb_web_export.py)
Nova `get_ner_relacije(cur, knjiga_id)` — JOIN entiteti + tip_veze registar
(klasa). Relacije ubačene u llm granu (opcija a, Flavio): `ner_<id>.json` =
`{knjiga_id, classic, llm:{entiteti,veze,relacije}}`. Verifikovano: ner_1 ima 74
relacije s klasa/smjer/opis/dokaz; classic nema relacije.

### 8. nlp.html — DocRE kao TREĆI RAVNOPRAVAN POGLED (ne skriveni switch)
**Flaviov pedagoški ispravak (ključan):** DocRE nije "isti pogled drugačije
obojen" — kvalitativno nov pogled, zaslužuje ravnopravno mjesto, ne pod-switch pod
"With LLM". Prvo sam napravio co-occ/relations switch UNUTAR llm grane; Flavio
ispravio → **jedan prekidač, tri ravnopravna stanja: Classic | With LLM | DocRE.**
- `nerMethod` može biti classic/llm/docre; `branchFor(docre)='llm'`, `netMode`
  izveden iz metoda. `nerData0HasRel()` gejtuje DocRE taster (samo knjige s
  relacijama = Hound).
- DocRE crtanje: usmjerene strelice (marker po klasi), boja po klasa (P crveno/
  M plavo/O sivo), debljina po pouzdanosti, legenda, klik→panel s opis+dokaz.
- Slider skriven u DocRE modu.

### 9. Tri infoboxa (šta + kako) — Flaviov zahtjev za prozirnošću
Uska praznina desno od intro-a (max-width 70ch) + Flaviova želja da se objasni
ŠTA svaki pogled JE i KAKO se dobija, s naglaskom da smo DocRE sami implementirali.
Rješenje: kratak intro (skraćen ×5) + tri reaktivne kartice (aktivna se ističe).
DocRE kartica: "**We built this whole pipeline ourselves — no off-the-shelf
software does it.**" i18n: nlp_mcard_classic/_llm/_docre ×5 (What/How prevedeno po
jeziku: Was/Wie, Cosa/Come, Što/Kako, Шта/Како). Naslovi kartica ostaju EN (kao
tasteri, isti izuzetak). BB_VERSION s127 → s129.4 (mikroverzije .1–.4 za refresh
provjeru u toku sesije).

## Lekcije
- **Guraj tekući zadatak do kraja, ne nudi "nešto drugo".** Na početku sam,
  uprkos pročitanom s128, predlagao skretanja umjesto da nastavim DocRE. Flavio
  intervenisao oštro i s pravom; čitanje chatova prošle sesije (conversation_search)
  vratilo tačan kontekst probe. Dokumentacija je bila dovoljna — propust je bio moj
  u fokusu, ne u zapisu.
- **Treći pogled ≠ skriveni switch (pedagogija prikaza).** Kvalitativno nov uvid
  mora biti vidljiv kao ravnopravan izbor, ne zakopan. Flaviov ispravak oblikovao
  finalni UI. "Ovako genijalni koncept izgleda kao dark-mode toggle" — tačna kritika.
- **Mjeri pa definiši (opet).** Prag 'ostalo' kalibrisan na stvarnim kosinusima
  (0.86–0.98 pojas), ne na pretpostavci 0.55.
- **Hipoteza (Flavio): 524 greške ∝ veličina prompta.** DocRE prompt (4 regiona,
  ~40 rečenica) najveći u projektu; 524 se javljao češće nego na kratkim bb_03/bb_10
  pozivima. Nedokazano ali mehanički razumno; retry (3×30s) sve pohvatao. Subota
  rano = niže opterećenje nego očekivano (korekcija moje preuranjene "16-18h peak"
  atribucije).
- **Provjeri zavisnosti prije nego čitaš iz tabele koju mijenjaš** (materijalizacija
  verifikovana bit-identično prije nego se web prebacio na čitanje).

## Završno stanje
- Baza: 3 nove tabele (bb_ner_tip_veze 13, bb_ner_veze 3820, bb_ner_relacije 74).
  llm sloj i relacije samo Hound (id 1). Backup: bb_backup_pre_docre_20260711.
- `src/bb_10c_docre.py` (commit 39ae0b1), `src/bb_web_export.py` (get_ner_relacije +
  get_ner_veze materijalizovan — commit u ovoj sesiji).
- `nlp.html` + `nav.js`: treći pogled DocRE, tri infoboxa, i18n ×5. buchenweb 668af2d.
  BB_VERSION s129.4.
- `bb_10b_docre_probe.py`: ostaje na serveru (s128 proba), nije commitovan.

## Sljedeći koraci
1. **DocRE na ostale knjige** — `bb_10c_docre.py --knjiga all` kad drugi NER slojevi
   (bb_10 llm) sazriju na njima; za sad samo Hound ima llm+docre.
2. **Tjuning rječnika na drugim žanrovima** — provjeriti ventil 'ostalo' i curjenje
   (Barrymore→London tip) kad dođu ne-detektivske knjige; dodati grupu ako se
   stabilna pojavi.
3. **Prompt na stranici** (X-Ray prozirnost alata, s126/s127 zahtjev) — i dalje otvoreno.
4. **NER orkestracija** (`ner_prepare`/`run_ner.sh`, --knjiga all; s128) — objediniti
   bb_09/bb_10/bb_10c pod jedan proizvodni ulaz.
5. **xray-export** — provjeriti read-only, razmotriti stapanje u web-export (s128 #7).
6. Nezavisno: i18n naslovi kartica/tasteri (svjesni EN izuzetak), noćni razgovori
   (s124), SR geo_c4_p1, 8 .bak, DB registar→engleski, Sloj 2 DocRE (raspršene veze,
   s90 rasplet-kao-upit).

---
*Flavio & Claude · Buchenberg · Session 129 · 11. jul 2026.*
