# Session 35 — Kompozitni score, translation_score i Jezički RAG

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
- Temperatura za NLLB = 0 je ispravan i jedini smisleni izbor

### 3. Prvi NLLB run u bb pipeline-u (MiniLM)

```bash
venv/bin/python src/bb_03_prevod.py \
    --knjiga 1 --od 1 --do 40 \
    --model "nllb-600M" \
    --embedder "paraphrase-multilingual-MiniLM-L12-v2" \
    --jezici hr fr it
```

**Trajanje:** 3:56 min | **Log:** `logs/bb_03_nllb_hr_fr_it.log`

| Jezik | avg_score (MiniLM) |
|-------|-------------------|
| IT | 0.8926 |
| FR | 0.8803 |
| HR | 0.8624 |

### 4. NLLB run s e5-large

```bash
venv/bin/python src/bb_03_prevod.py \
    --knjiga 1 --od 1 --do 40 \
    --model "nllb-600M" \
    --embedder "multilingual-e5-large" \
    --jezici hr fr it
```

**Trajanje:** 4:55 min | **Log:** `logs/bb_03_nllb_e5_hr_fr_it.log`

| Jezik | MiniLM | e5-large | Δ |
|-------|--------|----------|---|
| FR | 0.8803 | 0.9583 | +0.0780 |
| HR | 0.8624 | 0.9510 | +0.0886 |
| IT | 0.8926 | 0.9614 | +0.0688 |

**Zaključak:** prevodi su identični (NLLB deterministički), samo embedder mjeri drugačije. e5-large daje realističniju sliku semantičke ekvivalentnosti.

### 5. Fer usporedba svih modela s e5-large

Pokrenuti svi Ollama modeli s e5-large da bi usporedba bila pod istim scorerom:

```bash
# gemma3, ministral, gemma4 — serijski
logs/bb_03_ollama_e5_hr_fr_it.log
```

**Rezultati (e5-large, avg_score):**

| Model | FR | HR | IT |
|-------|----|----|-----|
| gemma4:31b | **0.9780** | **0.9702** | **0.9749** |
| ministral-3:14b | 0.9669 | 0.9610 | 0.9673 |
| gemma3:12b | 0.9660 | 0.9635 | 0.9671 |
| nllb-600M | 0.9583 | 0.9510 | 0.9614 |

### 6. Kompozitni score — translation_score

**Flaviova ideja:** kombinovati dva scorea:
- `score` = `cosine(EN, back_EN)` — informacijska stabilnost (back-translation)
- `translation_score` = `cosine(EN, prevod)` — direktna semantička blizina

```
composite = (score + translation_score) / 2
```

**Implementacija:**
- `ALTER TABLE bb_prevodi_recenica ADD COLUMN translation_score REAL`
- `bb_03_prevod.py` — dodani `prevod_vektori` i izračun `translation_score` u petlji
- Nova skripta `bb_calc_translation_score.py` — UPDATE za postojeće redove

**Run:**
```bash
venv/bin/python src/bb_calc_translation_score.py --embedder "multilingual-e5-large"
venv/bin/python src/bb_calc_translation_score.py --embedder "paraphrase-multilingual-MiniLM-L12-v2"
```
960 redova ažurirano (480 po embedderu). | **Log:** `logs/bb_calc_ts.log`

**Kompozitni rezultati (e5-large):**

| Model | FR composite | HR composite | IT composite |
|-------|-------------|-------------|-------------|
| gemma4:31b | 0.9448 | **0.9489** | **0.9463** |
| gemma3:12b | **0.9461** | 0.9460 | 0.9421 |
| nllb-600M | 0.9458 | 0.9395 | 0.9422 |
| ministral-3:14b | 0.9412 | 0.9435 | 0.9446 |

**Ključna observacija:** `avg_direct` konzistentno niži od `avg_back` za LLM modele. Za NLLB su gotovo izjednačeni — e5-large razotkriva razliku između bukvalne i kreativne stabilnosti. MiniLM tu razliku ne vidi.

### 7. Jezički RAG — koncept

**Flaviova ideja:** "duh jezika" — prirodnost prevoda u ciljnom jeziku, ne samo semantička blizina originalu.

**Arhitektura:**
```
Korpus prirodnog teksta (Tatoeba/OPUS/Gutenberg po jeziku)
    → parsiranje → rečenice
    → e5-large embeddings
    → pohrana u pgvector

Za ocjenu prevoda:
    prevod_vektor → k-NN upit u pgvector → avg cosine k susjeda
    = naturalness_score

final_score = α × semantic_score + β × naturalness_score
```

`α` i `β` kao kontrolni mehanizam između vjernosti i prirodnosti prevoda.

**Izvori po jezicima:**
- Romanski/germanski: Project Gutenberg (FR, IT, DE, NL dobro zastupljeni)
- Južnoslavenski: **Tatoeba** i **OPUS** (HR, SR, BS, SL, MK, BG) — Gutenberg nije dovoljan
- pgvector već postoji u infrastrukturi — prirodna ekstenzija

---

## Ključni uvidi

- **Ne možemo utjecati na prevod, ali možemo na ocjenu prevoda** — scorer je naša odgovornost
- **Kompozitni score** (`score + translation_score) / 2`) bogatija metrika od jednog scorea
- **e5-large vs MiniLM:** e5-large razlikuje bukvalni vs kreativni prevod, MiniLM ne
- **Jezički RAG** — sljedeći korak prema "duhu jezika", prirodnosti prevoda u ciljnom jeziku
- **Apsolutne vrijednosti nisu bitne, relativne jesu** — poređenje modela pod istim scorerom

---

## Otvoreno za sljedeću sesiju

1. Implementacija Jezičkog RAG-a — odabir izvora i prvog jezika
2. `bb_04_pobjednik.py` — pokrenuti s kompozitnim scoreom
3. NLLB run za preostale jezike (de, nl, es, pt, sr, bg, bs, sl, mk, af, ro)
4. Git commit i push izmjena (`bb_03_prevod.py`, `bb_calc_translation_score.py`)

---

*Flavio & Claude · Buchenberg · Session 35 · 1. jun 2026.*
