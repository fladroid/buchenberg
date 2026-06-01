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
- Temperatura za NLLB = 0 je ispravan i jedini smisleni izbor

### 3. NLLB runovi — MiniLM vs e5-large

```bash
# MiniLM
venv/bin/python src/bb_03_prevod.py --knjiga 1 --od 1 --do 40 \
    --model "nllb-600M" --embedder "paraphrase-multilingual-MiniLM-L12-v2" \
    --jezici hr fr it   # log: bb_03_nllb_hr_fr_it.log — 3:56 min

# e5-large
venv/bin/python src/bb_03_prevod.py --knjiga 1 --od 1 --do 40 \
    --model "nllb-600M" --embedder "multilingual-e5-large" \
    --jezici hr fr it   # log: bb_03_nllb_e5_hr_fr_it.log — 4:55 min
```

| Jezik | MiniLM | e5-large | Δ |
|-------|--------|----------|---|
| FR | 0.8803 | 0.9583 | +0.0780 |
| HR | 0.8624 | 0.9510 | +0.0886 |
| IT | 0.8926 | 0.9614 | +0.0688 |

**Zaključak:** prevodi identični (NLLB deterministički), samo embedder mjeri drugačije. e5-large realnija slika.

### 4. Fer usporedba svih modela s e5-large

```bash
# gemma3, ministral, gemma4 — serijski, e5-large
# log: bb_03_ollama_e5_hr_fr_it.log
```

**Rezultati (e5-large, avg_back_score):**

| Model | FR | HR | IT |
|-------|----|----|-----|
| gemma4:31b | **0.9780** | **0.9702** | **0.9749** |
| ministral-3:14b | 0.9669 | 0.9610 | 0.9673 |
| gemma3:12b | 0.9660 | 0.9635 | 0.9671 |
| nllb-600M | 0.9583 | 0.9510 | 0.9614 |

### 5. Kompozitni score — translation_score

**Flaviova ideja:** kombinovati dva scorea:
- `score` = `cosine(EN, back_EN)` — informacijska stabilnost
- `translation_score` = `cosine(EN, prevod)` — direktna semantička blizina

```
composite = (score + translation_score) / 2
```

**Implementacija:**
- `ALTER TABLE bb_prevodi_recenica ADD COLUMN translation_score REAL`
- `bb_03_prevod.py` — dodani `prevod_vektori` i izračun `translation_score`
- Nova skripta `src/bb_calc_translation_score.py` — UPDATE za postojeće redove

```bash
venv/bin/python src/bb_calc_translation_score.py --embedder "multilingual-e5-large"
venv/bin/python src/bb_calc_translation_score.py --embedder "paraphrase-multilingual-MiniLM-L12-v2"
# log: bb_calc_ts.log — 960 redova ažurirano (480 po embedderu)
```

**Kompozitni rezultati (e5-large):**

| Model | FR | HR | IT |
|-------|----|----|-----|
| gemma3:12b | **0.9461** | 0.9460 | 0.9421 |
| gemma4:31b | 0.9448 | **0.9489** | **0.9463** |
| nllb-600M | 0.9458 | 0.9395 | 0.9422 |
| ministral-3:14b | 0.9412 | 0.9435 | 0.9446 |

**Ključna observacija:** `avg_direct` konzistentno niži od `avg_back` za LLM modele. Za NLLB gotovo izjednačeni — e5-large razotkriva razliku između bukvalne i kreativne stabilnosti.

### 6. Jezički RAG — koncept i implementacija

**Flaviova ideja ("Jezički RAG"):** mjeriti prirodnost prevoda u ciljnom jeziku, ne samo semantičku blizinu originalu.

```
naturalness_score = avg cosine(prevod_vektor, k-NN iz korpusa ciljnog jezika)
final_score = α × semantic_score + β × naturalness_score
```

**Napomena o modelima:**
- Jezički RAG kao **scorer** vrijedi za sve modele (NLLB + LLM)
- Jezički RAG kao **vodič za reprevod** (few-shot) — samo LLM modeli, ne NLLB

**Istraživanje izvora:**

| Izvor | HR | IT | DE |
|-------|----|----|-----|
| Tatoeba direktni | 83 KB | 9.3 MB | 11.9 MB |
| OPUS/Tatoeba | 70 KB | 7.6 MB | 11.2 MB |
| **OPUS/OpenSubtitles** | **1.05 GB** | **0.98 GB** | **0.48 GB** |

Odabran **OPUS OpenSubtitles v2018** — isti izvor za sve jezike, konzistentan registar.

**Infrastruktura:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;  -- pgvector u bb bazi
CREATE TABLE bb_rag_korpus (
    id       SERIAL PRIMARY KEY,
    jezik_id INTEGER REFERENCES bb_jezik(id),
    tekst    TEXT NOT NULL,
    vektor   vector(1024)
);
CREATE INDEX ON bb_rag_korpus USING ivfflat (vektor vector_cosine_ops) WITH (lists = 100);
```

**Nova skripta `src/bb_rag_init.py`:**
- Stream download (ne skida cijeli GB)
- Filtriranje: dužina 10–200 znakova, min 60% alfa znakova
- Enkodiranje batch po batch s e5-large (BATCH_SIZE=256)
- Idempotentno — preskače već upisane rečenice

**Test run (1000 HR rečenica):** ✅ 2 minute, 1000 rečenica upisano

**Produkcijski run — pokrenut u backgroundu:**
```bash
nohup time venv/bin/python src/bb_rag_init.py \
  --jezici hr it de \
  --max_recenica 50000 \
  --embedder "multilingual-e5-large" \
  > logs/bb_rag_init_hr_it_de.log 2>&1 &
# PID: 78991 — procjena trajanja: ~100 min
```

---

## Ključni uvidi sesije

- **Ne možemo utjecati na prevod, ali možemo na ocjenu prevoda** — scorer je naša odgovornost
- **Kompozitni score** `(score + translation_score) / 2` bogatija metrika od jednog scorea
- **e5-large vs MiniLM:** e5-large razlikuje bukvalni vs kreativni prevod, MiniLM ne
- **Jezički RAG** — prirodnost prevoda u ciljnom jeziku kao dodatna dimenzija ocjene
- **OPUS OpenSubtitles** jedini izvor koji pokriva sve naše jezike ravnomjerno
- **Apsolutne vrijednosti nisu bitne, relativne jesu**

---

## Otvoreno za sljedeću sesiju

1. **Provjeriti završetak RAG runa** — `tail logs/bb_rag_init_hr_it_de.log`
2. **Implementirati `bb_rag_score.py`** — k-NN upit u pgvector, naturalness_score
3. **Testirati kompozitnu metriku** — `α × semantic_score + β × naturalness_score`
4. **Odlučiti α i β** — omjer vjernosti vs prirodnosti
5. **`bb_04_pobjednik.py`** — ažurirati da koristi kompozitni score
6. **Git commit** — `bb_rag_init.py`, `bb_03_prevod.py`, `bb_calc_translation_score.py`
7. **Proširiti RAG** na ostale jezike (fr, es, pt, ro, bs, sr, sl, mk, bg, nl, af)

---

*Flavio & Claude · Buchenberg · Session 35 · 1. jun 2026.*
