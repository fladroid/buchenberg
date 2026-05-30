# Session 33 — 30. maj 2026.

## Fokus sesije
Exploracija novih analitičkih alata za analizu teksta — Cellular Automaton, Ant Colony Optimization i Heat Mapa. Izgradnja `entity_aliases` infrastrukture za NER normalizaciju.

---

## Što je urađeno

### 1. Cellular Automaton (CA) vizualizacija
- Implementiran CA nad 100 rečenica Hounda koristeći e5 UMAP koordinate i sentiment
- Svaka ćelija = rečenica, stanje = sentiment (positive/neutral/negative)
- Pravila evolucije: semantičko glasanje (top-6 UMAP susjedi), entitetska zaraza (shared entity × 2.5), kombinirano
- Dodana mutacija (klizač 0–40%), inercija za jake sentimente, ⚡ perturbacija dugme
- History graf (zadnjih 120 generacija) — vizualizacija konvergencije
- Filter po liku (Holmes/Watson/Mortimer/Mjesta) — blijedi neoznačene ćelije
- Klik na ćeliju zamrzava je (žuta bordura)

### 2. Ant Colony Optimization (ACO) vizualizacija
- UMAP scatter plot + feromonske linije + animirani mravi
- Tri modusa:
  - **Modus 1**: Rečenica → Rečenica (direktni put između dva čvora)
  - **Modus 2**: Rečenica → Pojam (start = rečenica, cilj = zona entiteta)
  - **Modus 3**: Pojam → Pojam (npr. Holmes zona → London zona)
- Hover tooltipovi: čvor pokazuje stvarni tekst iz knjige + sentiment + entiteti
- Hover na feromonsku liniju: cosinus sličnost + feromon % od max
- Uvid: s4→s90 nema semantički koridor (cosinus samo 0.785) — to je nalaz, ne bug

### 3. Heat Mapa narativa
- 100 rečenica × 7 dimenzija: sentiment, Holmes, Watson, Mortimer, London/Dartmoor, dužina, semantički tok
- Hover po koloni prikazuje sve detalje + tekst rečenice
- Filteri: Sve dimenzije / Samo sentiment / Samo entiteti / Samo tok
- Jasno vidljivi: Holmes/Watson klasteri, Mortimer dva vala (s8,s18 + s64,s77,s79), semantički skokovi

### 4. entity_aliases tabela + pipeline
- Nova tabela: `entity_aliases(book_id, raw_text, raw_label, canonical_name, correct_label, role, source)`
- Pipeline:
  1. `ask_llm_entities.py` — Gemma4:31b normalizira 268 entiteta (77 sek)
  2. `build_entity_aliases.py` — primjenjuje moje korekcije (27 korekcija)
  3. `load_entity_aliases.py` — puni bazu (164 entiteta, noise preskočen)
- Ključne korekcije: Vandeleur/Rodger Baskerville/Jack → Stapleton (villain_alias), Miss Stapleton/Beryl Garcia → Beryl Stapleton (accomplice), Laura Lyons (accomplice ne red_herring), Frankland (red_herring ne helper)
- Uvid: za poznate knjige (Gutenberg kanon) korekcije pišemo direktno — preciznije od LLM prompta

### 5. v_sentence_features VIEW
- Jedan SELECT koji daje sve NLP karakteristike po rečenici
- Kolone: sentence_id, book_id, text, word_count, sentiment_label, sentiment_score, persons[], places[], has_holmes, has_watson, has_mortimer, has_stapleton, has_henry, has_charles, has_barrymore, has_selden, has_lyons, has_beryl, has_dartmoor, has_baskerville_hall, has_london, has_grimpen_mire, has_baker_street, has_villain_ref, cos_prev_e5
- Koristi entity_aliases za normalizaciju — Vandeleur/Rodger → Stapleton automatski
- Skalabilno na više knjiga (book_id)

---

## Ključni uvidi

- **CA konvergencija**: glasanje većine bez mutacije → lokalni optimum za ~50 generacija. Isti princip kao GA bez mutacije. Perturbacija = izlaz iz lokalnog optimuma.
- **ACO i semantička distanca**: s4 (Holmes/štap) → s90 (London) cosinus = 0.785, nema puta. London u s90 je samo jedna rječ u dugačkoj rečenici — e5 to ispravno prepoznaje.
- **NER šum**: spaCy klasificira Barrymore, Stapleton, Watson kao GPE; Dartmoor kao PERSON. LLM normalizacija + moje korekcije rješavaju problem.
- **LLM granice**: Gemma4 nije spojio Vandeleur = Stapleton automatski. Za poznate knjige: ručne korekcije su preciznije od prompta.
- **Heat mapa potencijal**: sa v_sentence_features i svim 3852 rečenica cijeli roman postaje X-Ray slika — Stapleton arc vidljiv, napetost mjerljiva.

---

## Otvoreno za sljedeću sesiju

1. **sentence_umap tabela** — pohraniti UMAP koordinate u bazu (scope: book/corpus, embedder, n_neighbors, min_dist)
2. **Heat mapa cijele knjige** — svih 3852 rečenica iz v_sentence_features
3. **cos_prev_minilm** — dodati u view za MiniLM embedder
4. **Pipeline za drugu knjigu** — testirati entity_aliases workflow na novom naslovu
5. **ACO poboljšanje** — gušći graf (top-20 susjedi) za bolje pokrivanje semantičkog prostora

---

## Git
- Commit: `feat: entity_aliases — NER normalizacija pipeline za Hound (book_id=1)`
- Commit: `feat: v_sentence_features view — sve NLP karakteristike po recenici`
- Push: main → github.com:fladroid/buchenberg.git

---

*Flavio & Claude · Buchenberg · Session 33 · 30. maj 2026.*
