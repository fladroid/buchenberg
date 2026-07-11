# Session 127 — LLM NER Dio 2: potpun llm sloj, web toggle, preimenovanje stranice

**Datum:** 11. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Nastavak LLM-potpomognute NER analize (Dio 2 od plana iz s126).
Kompletiran llm sloj (nekonfliktni classic entiteti kopirani kao čisti llm redovi).
Web export dobio `method` param i granu-svjesnu strukturu. nlp.html dobio
classic/with-llm toggle. Usput — na Flaviov poticaj — uklonjen word cloud s
nlp.html (redundantan s books.html, bez veze s NER-om) i stranica preimenovana
u "Named Entities & Relations" (fajl ostaje nlp.html). Relacije van rečenice
(DocRE) i prompt-na-stranici ostaju za sljedeću sesiju.

## Health snapshot
Početak: bb_recenice 50.624, bb_prevodi_recenica 1.518.170, bb_prev_recenica
296.578 (nepromijenjeno od s125/s126 — Flavio nije pokretao runove). Git početak:
buchenberg HEAD 912e07d (s126), buchenweb 015efc5 (s125). Sve zeleno, Ollama
Cloud (glm-5.2, mistral-large-3:675b, gemma4:31b) OK. 8 poznatih `.bak` fajlova
+ poznati lažni "buchenweb zaostaje" alarm.

## Kontekst
Plan iz s126 (Dio 2) imao je četiri stavke: (1) kompletiranje llm sloja,
(2) relacije van rečenice, (3) web export + nlp.html toggle, (4) prompt na
stranici. Radili smo planiranim redoslijedom 1 → 3. Stavke 2 i 4 ostaju.

## Urađeno

### 1. Kompletiranje llm sloja (bb_10_ner_llm.py)
Do s126 llm sloj je imao SAMO 18 razriješenih konfliktnih imena; nekonfliktni
(~163) postojali samo u classic. Flavio potvrdio opciju 1 (potpun samostalan llm
sloj): kopirati i nekonfliktne classic entitete kao čiste llm redove, da
"with llm" prikaz stoji sam.

Implementacija: nova logika UNUTAR `upisi_llm` (poslije petlje konflikata, prije
rezimea — dijeli isti DELETE na početku funkcije, jedan koherentan sloj).
Za svaki nekonfliktni classic entitet napravi llm blizanca (isti tip/ime/pojave,
method='llm', novi id), preveže sve njegove `bb_ner_recenica` na novi id.

Pokrenuto na Houndu (id 1). Rezultat:
- 18 konflikata reproducibilno (identično s126 — glm-5.2 temp 0.0 stabilan)
- Kopirano 163 nekonfliktna entiteta + 855 veza
- **llm sloj sad: 181 entitet / 179 imena / 1223 pojave / 1219 veza**
- classic netaknut: 201 entitet / 181 imena / 1239 pojava / 1236 veza

Verifikacija nezavisnim SQL-om: 181 = 163 + 18 ✓; 179 = 181 − 2 odbačena
ne-entiteta ("I.", "Neolithic") ✓. Manji broj veza kod llm-a (1219 vs 1236) je
DOBAR znak — uklonjeni lažni entiteti i pogrešne type-veze čiste mrežu.
Commit buchenberg f4a725a.

### 2. Web export — method param + grana-svjesna struktura (bb_web_export.py)
Nalaz prije izmjene: `get_ner`/`get_ner_veze` NISU imali method filter → za Hound
(koji sad ima oba sloja) miješali bi classic+llm entitete. Nije bila greška
nastala tad, samo otvorena stavka.

Izmjene:
- `get_ner(cur, knjiga_id, method='classic')` — dodat method filter.
- `get_ner_veze(cur, knjiga_id, method='classic', min_tezina=2)` — method filter na
  e1/e2/r1/r2 (veze ostaju unutar istog sloja).
- Pozivno mjesto (NER export): gradi `classic` granu uvijek, `llm` granu SAMO ako
  knjiga ima llm redove. Nova struktura fajla:
  `{knjiga_id, classic:{entiteti,veze}, llm?:{entiteti,veze}}`.

Regeneracija: ner_1.json = classic 201 + llm; sve ostale samo classic; kopije
(22/23/24) = 0 ent (NER nikad pokrenut). Verifikacija JSON strukture:
ner_1 ima obje grane (classic 201/198, llm 181/185), ner_5 samo classic. Jedan
pozivač funkcija (nema drugih) — čisto.

### 3. nlp.html — uklanjanje word clouda
Flaviov poticaj: word cloud na nlp.html je (a) redundantan — postoji u books.html;
(b) bez funkcije — frekvencija riječi ne hrani NER, mrežu ni highlight; (c)
zavaravajuć — NER-bojanje sugeriše da je dio analize, a nije. X-Ray logika:
prikaz koji ne osvjetljava proces je šum. Odluka: ukloniti.

Provjera zavisnosti prije reza: `wordFreq`/`buildNerLookup`/`drawWC` samostalni;
`nerRecMap`/highlight NEZAVISNI (preživljavaju); `TIP_COLOR` dijeljen s mrežom
(ostaje); `STOP_EN` samo cloud (uklonjen); `d3.min.js` ostaje (mreža ga treba),
samo `d3.layout.cloud` uklonjen. Uklonjeno: 2. D3 skript, CSS #nlp-wc-wrap, HTML
panel, 3 funkcije, `nlp-wc-title` (HTML+i18n×5), svi drawWC pozivi. `#nlp-top`
grid 1fr 1fr → 1fr (NER puna širina).

### 4. nlp.html — preimenovanje stranice
Flavio: stranica govori samo o entitetima (i uskoro relacijama), naslov "NLP"
prazno obećava širinu. Diskusija oko naslova: čist "NER" preuzak (relacije iz
Dijela 2 nisu čist NER), pun "NLP" preširok → **"Named Entities & Relations"**
(Flavio: "pravi put, ne srednji"). Fajl ostaje nlp.html (rute netaknute).
- `<title>`, `nlp_title` (h1, ×5 jez), meni `nlp:` (NLP → "Entities" ×5:
  Entities/Entitäten/Entità/Entiteti/Ентитети), `nlp_subtitle` (skinut word-cloud
  dio, ×5). Naslov preveden na sve jezike (konzistentno s ostalima).
- STRANICE.md napomena: meni "Entities" ≠ naslov "Named Entities & Relations"
  (namjerno, isti obrazac kao Geometry→Geometry of Meaning).

### 5. nlp.html — classic/with-llm toggle
Minimalno invazivan dizajn: `nerFull` = cijeli fajl, `nerData` = aktivna grana
(`nerFull.classic` default). Svih ~15 postojećih `nerData.entiteti/.veze`
referenci rade neizmijenjene. Toggle mijenja granu + re-render svega.
- Globalne: `nerFull`, `nerMethod='classic'`.
- HTML: `#nlp-method-bar` (2 dugmeta, `display:none` dok se ne zna ima li llm).
- `updateMethodToggle()`: prikazuje bar SAMO ako `nerFull.llm` postoji.
- Handler: prebaci granu, `buildNerRecMap`, slider max, drawNetwork, renderNerList,
  renderText, renderLinksTable, renderConflictsTable.
Verifikovano u browseru: Hound pokazuje toggle, prebacivanje mijenja listu (Watson
PERSON-only, "I."/Neolithic nestali, Coombe Tracey→GPE), Type Conflicts, mrežu,
Links. Ostale knjige bez toggle-a.

### 6. nlp.html — method intro + dinamični opis
Na Flaviov zahtjev: objašnjenje classic/with-llm da toggle ne bude zagonetka.
Dvoslojno:
- **Statični intro** ispod naslova (`nlp_method_intro` ×5) — objašnjava da
  stranica nudi RAZLIČITE poglede (ne "dva" — Flaviova korekcija da se ne
  zaključamo pred relacijama/budućim slojevima; "more analytical layers as the
  method grows"). Imenuje **spaCy** kao alat automatskog označavanja, UOKVIREN
  (kao about.html modeli): "the tool we chose, not a fixed part of the method —
  it could be replaced". Flaviova odluka: spaCy je odradio velik posao, zaslužuje
  kredit, ali s napomenom o zamjenjivosti.
- **Dinamični red** ispod toggle-a (`nlp_method_desc_classic`/`_llm` ×5) —
  opisuje AKTIVNI sloj, mijenja se s toggle-om. `updateMethodDesc()` pozvan iz
  i18n applya, `updateMethodToggle` i toggle handlera.
Verifikovano u browseru: oba se prevode na svih 5 jezika; dinamični red prati
toggle; skriven na knjigama bez llm-a.

## Lekcije
- **Mjeri prije reza — provjeri zavisnosti.** Prije uklanjanja word clouda
  provjereno da highlight/mreža ne zavise od njega (grep + čitanje), da rez bude
  čist. Nije se pretpostavilo.
- **Naslov opisuje šta stranica JESTE, ne šta bi mogla biti** (word cloud i "NLP"
  isti tip praznog obećanja). Ali ni ne broji ("two views") — formulacija otvorena
  prema rastu. Flaviove dvije korekcije oblikovale dizajn više od početnog plana.
- **Nova struktura fajla i čitač se moraju mijenjati zajedno** — izmjena
  bb_web_export (grane) polomila bi staro `nerData.entiteti` čitanje da nije
  istovremeno uveden `nerFull`/aktivna grana u nlp.html.

## Završno stanje
- Baza: llm sloj Hound (id 1) kompletan — 181 entitet / 1219 veza. classic
  netaknut. Ostale knjige: samo classic. NIJE dirana ova sesija (upis iz
  bb_10 = jedina promjena, verifikovan).
- `src/bb_10_ner_llm.py`: +kopiranje nekonfliktnih (commit f4a725a).
- `src/bb_web_export.py`: get_ner/get_ner_veze +method, grana-svjesni NER export.
- `nlp.html`: word cloud uklonjen, preimenovan, classic/llm toggle, method
  intro + dinamični opis. Toggle labele ("Classic"/"With LLM") ostaju EN hardkod
  — SVJESTAN preostali i18n izuzetak (jedini na stranici; zabilježen za budući
  prolaz ako se poželi).
- `nav.js`: -nlp_wc_title (×5); +nlp_method_intro/_desc_classic/_desc_llm (×5);
  nlp_title/nlp_subtitle/meni nlp izmijenjeni (×5). BB_VERSION s125.5 → s127.
- STRANICE.md ažuriran (nlp red: novi naslov/meni/title).

## Sljedeći koraci (Dio 2 nastavak + Dio 3)
1. **Relacije van rečenice** — DocRE/koreferencija preko LLM-a. Prozor od N
   rečenica (ne cijela knjiga — s90 kombinatorni šum), grounding citatom.
   Novo skladište relacija kao objekta (tip veze + dokaz + izvorne rečenice).
   Oblik se određuje kad vidimo prvi LLM izlaz. NAJKRUPNIJA preostala stavka.
2. **Prompt na stranici** (Flaviov zahtjev, X-Ray prozirnost) — prikaz korištenog
   prompta. Radi se na kraju (poslije relacija).
3. **bb_10 na ostale knjige** kad Dio 2 sazrije.
4. i18n toggle labela (Classic/With LLM) — ako se poželi zatvoriti izuzetak.
5. Nezavisno stoje: noćni razgovori (s124 poluge A/B/C), SR geo_c4_p1 mixed-script,
   8 `.bak` fajlova, DB registar → engleski.

---
*Flavio & Claude · Buchenberg · Session 127 · 11. jul 2026.*
