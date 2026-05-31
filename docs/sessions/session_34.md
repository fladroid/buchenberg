# Session 34 — bb pipeline: back to the root

**Datum:** 2026-05-31
**Učesnici:** Flavio & Claude
**Nastavlja:** Session 33 (eksperimentalni alati, entity_aliases, v_sentence_features)

---

## Kontekst — filozofski zaokret

Flavio je izrazio želju za povratkom na originalnu ideju projekta:

> Imam knjigu na engleskom. Prevodim je mašinski na drugi jezik. Sa tog drugog jezika prevodim nazad na engleski i računam cosinus sličnosti. Taj prevod i prevod unazad uradim sa nekoliko mašinskih modela i najbolji prevod koristeći cosinus sličnosti pobjeđuje.

Odluka: nova baza `bb`, čista shema, minimalistički pristup. Stara baza `buchenberg` ostaje netaknuta.

---

## Što je urađeno

### 1. Nova baza `bb`

Kreirana PostgreSQL baza `bb` sa 9 tabela i `bb_` prefiksom:

**Lookup tabele:**
- `bb_jezik` — 14 jezika
- `bb_modeli` — 9 modela (gemma3, ministral, nllb, claude, gemma4 × temperature)
- `bb_embeddings` — 2 embeddera

**Original:**
- `bb_knjige` — knjige
- `bb_recenice` — rečenice (pozicija, tekst)

**Prevodi:**
- `bb_prevodi_knjige` — UNIQUE(knjiga, jezik, model, embedder)
- `bb_prevodi_recenica` — prevod + back_translation + score

**Finalni prevod:**
- `bb_prev_knjige` — UNIQUE(knjiga, jezik)
- `bb_prev_recenica` — FK na pobjednika u bb_prevodi_recenica

### 2. Pet skripti

| Skripta | Opis |
|---------|------|
| `bb_01_init_lookup.py` | Puni bb_jezik, bb_modeli, bb_embeddings |
| `bb_02_insert_knjiga.py` | Ubacuje knjigu i parsira rečenice (spaCy) |
| `bb_03_prevod.py` | Prevod + back-translation + cosine score (batch+fallback) |
| `bb_04_pobjednik.py` | Bira pobjednika po max score, tiebreak po abecedi modela |
| `bb_05_export.py` | Export finalnog prevoda u `output/naziv_knjige_lang.txt` |

### 3. Prvi run

- **Knjiga:** The Hound of the Baskervilles, rečenice 1–40
- **Modeli:** gemma3:12b (t=0.8), ministral-3:14b (t=0.8), gemma4:31b (t=0.8)
- **Embedder:** paraphrase-multilingual-MiniLM-L12-v2
- **Jezici:** hr, it, de

**Rezultati (avg score po modelu i jeziku):**

| Model | hr | it | de |
|-------|----|----|-----|
| gemma3:12b | 0.8605 | 0.8938 | 0.8851 |
| gemma4:31b | 0.8842 | 0.9085 | 0.8957 |
| ministral-3:14b | 0.8978 | 0.9136 | 0.9007 |

Ministral konzistentno prvi, gemma4 drugi, gemma3 treći.

**Trajanje runova:** gemma3 ~4:20 min, ministral ~1:53 min, gemma4 ~2:37 min.

### 4. Konvencije

- Prefix: `bb_`
- FK nazivi: `{tabela_bez_prefiksa}_id`
- Skripte: `bb_NN_naziv.py`
- Temperatura za Ollama default: `0.8`
- Pobjednik tiebreak: abecedni redoslijed modela
- Output fajlovi: `output/{naziv_knjige}_{lang}.txt` sa `[sN]` oznakama

---

## Ključni uvidi

- **Minimalistički pipeline radi** — 5 skripti, čista shema, bez GA, bez boja, bez NLP enrichmenta
- **Pobjednik po cosinus scoreu** je dovoljno kao kriterij za prve testove
- **"Pseći pas Baskervila"** — doslovan prevod naslova pokazuje limit bez konteksta; pipeline je ispravan, problem je u modelu
- **Float poređenje u PostgreSQL** — `ROUND(temperatura::numeric, 4)` umjesto direktnog `=` za REAL kolone
- **Log flushing** — `functools.partial(print, flush=True)` na početku `main()`

---

## Otvoreno za sljedeću sesiju

1. **NLLB run** — dodati kao četvrtu metodu
2. **Analiza pobjednika** — koji model pobjeđuje najčešće po jeziku
3. **Proširenje** — više rečenica (1–100 ili cijela knjiga)
4. **Novi jezici** — fr, es, sr
5. **e5-large** — testirati kao embedder umjesto MiniLM
6. **`bb_` skripte u README** — dokumentirati novi pipeline

---

## Git

- Commit: `feat: bb pipeline — nova baza, 5 skripti (init, insert, prevod, pobjednik, export)`
- Push: main → github.com:fladroid/buchenberg.git

---

*Flavio & Claude · Buchenberg · Session 34 · 2026-05-31*
