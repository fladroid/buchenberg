# Session 35 — NLLB, kompozitni score, Jezički RAG

**Datum:** 1. jun 2026.
**Učesnici:** Flavio & Claude
**Nastavlja:** Session 34 (bb pipeline, back to the root)

---

## Kontekst

Sesija je počela osvježavanjem memorije. Claude nije pročitao project files na početku — propust koji je Flavio ispravno uočio i korigovao. Analiza propusta: utabani put (automatski protokol README → sessions) bez X-Ray provjere cijelog konteksta.

---

## Što je urađeno

### 1. Provjera stanja infrastrukture

- README V2 pročitan (poslednje ažuriranje: 30. maj 2026, sesija 32)
- Session dokumenti pročitani: session_32, session_33, session_34
- `health_check.py` pokrenut — sve zeleno ✅
- Aktuelno stanje: bb pipeline operativan, stara baza `buchenberg` netaknuta

### 2. NLLB podrška u `bb_03_prevod.py`

Originalna skripta podržavala je samo Ollama Cloud modele. Dodana je NLLB podrška direktno u postojeću skriptu (ne nova skripta — čišće rješenje).

**Ključne izmjene:**

| Komponenta | Opis |
|------------|------|
| `NLLB_MODEL_NAME` | `facebook/nllb-200-distilled-600M` |
| `NLLB_LANG_MAP` | ISO 639-1 → NLLB BCP-47/FLORES-200 kodovi (14 jezika) |
| `load_nllb()` | Učitava tokenizer i model jednom, prije petlje po jezicima |
| `nllb_batch()` | Batch prevod, beam search, `repetition_penalty=1.3` |
| `nllb_single()` | Wrapper oko `nllb_batch()` za jedan tekst |
| `is_nllb` flag | Branch u `main()` — ako `--model nllb-600M`, koristi NLLB engine, inače Ollama |
| `--temp` | Sada opcionalan (default=0.0), nije potreban za NLLB |
| `EMBEDDER_PATH_MAP` | Mapping naziv u bb_embeddings → HuggingFace path |

**Važne odluke:**
- NLLB uvijek koristi beam search (`do_sample=False`) — temperatura nema smisla za specijalizirani MT model
- NLLB nema batch fallback jer `tokenizer(texts, padding=True)` je inherentno robustan
- `--temp` je opcionalan (default=0.0) — kompatibilno s NLLB i Ollama

### 3. Prvi NLLB run u bb pipeline-u

```bash
venv/bin/python src/bb_03_prevod.py \
    --knjiga 1 --od 1 --do 40 \
    --model "nllb-600M" \
    --embedder "paraphrase-multilingual-MiniLM-L12-v2" \
    --jezici hr fr it
```

**Rezultati (MiniLM):**

| Jezik | avg_score | n |
|-------|-----------|---|
| 🇮🇹 IT | 0.8926 | 40 |
| 🇫🇷 FR | 0.8803 | 40 |
| 🇭🇷 HR | 0.8624 | 40 |

**Trajanje:** 3:56 min za 3 jezika × 40 rečenica (CPU, lokalni model).

### 4. Analiza temperature kod NLLB

- NLLB je treniran i optimiziran za beam search — to je njegov prirodni način rada
- Sampling s temperaturom donosi malo raznolikosti — NLLB je specijalizirani MT model bez "kreativnog" prostora
- Empirijski potvrđeno u starom pipeline-u: `nllb_t05` rijetko pobjeđivao `nllb`
- Temperatura=0 (beam search) je ispravan i jedini smisleni izbor za NLLB

### 5. Usporedba embeddera — MiniLM vs e5-large za NLLB

```bash
venv/bin/python src/bb_03_prevod.py \
    --knjiga 1 --od 1 --do 40 \
    --model "nllb-600M" \
    --embedder "multilingual-e5-large" \
    --jezici hr fr it
```

| Jezik | MiniLM | e5-large | Δ |
|-------|--------|----------|---|
| 🇫🇷 FR | 0.8803 | 0.9583 | +0.0780 |
| 🇭🇷 HR | 0.8624 | 0.9510 | +0.0886 |
| 🇮🇹 IT | 0.8926 | 0.9614 | +0.0688 |

**Ključni zaključak:** prevodi su identični (NLLB deterministički), samo embedder mjeri drugačije. e5-large daje realističniju sliku semantičke ekvivalentnosti.

**Trajanje e5-large run:** 4:55 min (+59s vs MiniLM). e5-large učitan iz lokalnog keša.

### 6. Fer usporedba svih modela pod e5-large

```bash
# Gemma3, Ministral, Gemma4 — svi s e5-large
nohup bash -c '
venv/bin/python src/bb_03_prevod.py --knjiga 1 --od 1 --do 40 \
    --model "gemma3:12b" --temp 0.8 --embedder "multilingual-e5-large" --jezici hr fr it &&
venv/bin/python src/bb_03_prevod.py --knjiga 1 --od 1 --do 40 \
    --model "ministral-3:14b" --temp 0.8 --embedder "multilingual-e5-large" --jezici hr fr it &&
venv/bin/python src/bb_03_prevod.py --knjiga 1 --od 1 --do 40 \
    --model "gemma4:31b" --temp 0.8 --embedder "multilingual-e5-large" --jezici hr fr it
'
```

**Rezultati (e5-large, avg_score):**

| Model | FR | HR | IT |
|-------|----|----|-----|
| gemma4:31b | **0.9780** | **0.9702** | **0.9749** |
| ministral-3:14b | 0.9669 | 0.9610 | 0.9673 |
| gemma3:12b | 0.9660 | 0.9635 | 0.9671 |
| nllb-600M | 0.9583 | 0.9510 | 0.9614 |

Svi modeli iznad 0.95 — zelena zona po e5-large pragovima (≥0.93).

### 7. Kompozitni score — nova metrika

**Ideja (Flavio):** kombinirati back-translation score i direktni translation score:
```
composite = (score(EN, back_EN) + score(EN, prevod)) / 2
```

**Implementacija:**
- Nova kolona `translation_score REAL` dodana u `bb_prevodi_recenica`
- `bb_03_prevod.py` — dodan izračun `prevod_vektori` i `translation_score` u petlji
- Nova skripta `bb_calc_translation_score.py` — UPDATE postojećih redova

```bash
venv/bin/python src/bb_calc_translation_score.py --embedder "multilingual-e5-large"
venv/bin/python src/bb_calc_translation_score.py --embedder "paraphrase-multilingual-MiniLM-L12-v2"
# Ukupno ažurirano: 960 redova
```

**Kompozitni score rezultati (e5-large):**

| Model | FR composite | HR composite | IT composite |
|-------|-------------|-------------|-------------|
| gemma3:12b | **0.9461** | 0.9460 | 0.9421 |
| nllb-600M | 0.9458 | 0.9395 | 0.9422 |
| gemma4:31b | 0.9448 | **0.9489** | **0.9463** |
| ministral-3:14b | 0.9412 | 0.9435 | **0.9446** |

**Ključna observacija:** `avg_direct` konzistentno niži od `avg_back` za LLM modele. Za NLLB su gotovo izjednačeni — kompozitni score razotkriva razliku između bukvalne i kreativne stabilnosti. Relativne vrijednosti su bitnije od apsolutnih.

### 8. Jezički RAG — konceptualni prijedlog

**Ideja (Flavio):** "Jezički RAG" — mjeriti prirodnost prevoda u prostoru ciljnog jezika, ne samo blizinu originalu.

**Arhitektura:**
```
Korpus prirodnog teksta na ciljnom jeziku (Tatoeba/OPUS/Gutenberg)
    → parsiranje → rečenice
    → e5-large embeddings
    → pohrana u pgvector

Za ocjenu prevoda:
    prevod_vektor → k-NN upit u pgvector → avg cosine k susjeda
    = naturalness_score

final_score = α × semantic_score + β × naturalness_score
```

**Izvori po jeziku:**
- Romanski i germanski (FR, IT, DE, NL): Project Gutenberg — dobra pokrivenost
- Južnoslavenski (HR, SR, BS, SL, MK, BG): **Tatoeba** i **OPUS** — Gutenberg nije dovoljan
- α i β parametri kontrolišu omjer vjernost vs. prirodnost (bukvalan vs. kreativan prevod)

**pgvector već postoji** u infrastrukturi — prirodna ekstenzija bez novih komponenti.

---

## Ključni uvidi sesije

- **bb_03_prevod.py je sada generički** — jedan ulazni punkt za sve modele (Ollama + NLLB)
- **e5-large je ispravan embedder** — odluka potvrđena fer usporedbom svih modela
- **Kompozitni score** je bogatija metrika od jednog scorea — mjeri i semantičku blizinu i informacijsku stabilnost
- **Apsolutne vrijednosti nisu bitne, nego relativne** — ključni princip za sve analize
- **Jezički RAG** je sljedeći logički korak prema ocjeni prirodnosti prevoda

---

## Otvoreno za sljedeću sesiju

1. Implementacija Jezičkog RAG-a — odabir jezika i izvora (Tatoeba/OPUS/Gutenberg)
2. Izgradnja pgvector indeksa za ciljne jezike
3. `naturalness_score` kao treća komponenta metrike
4. Definisanje α i β parametara (vjernost vs. prirodnost)
5. `bb_04_pobjednik.py` — ažurirati za kompozitni score
6. NLLB run za preostale jezike (de, nl, es, pt, sr, bg, bs, sl, mk, af, ro)
7. Git commit i push

---

*Flavio & Claude · Buchenberg · Session 35 · 1. jun 2026.*
