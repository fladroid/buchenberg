# Session 06 — Buchenberg

**Datum:** 16. maj 2026.  
**Učesnici:** Flavio & Claude

---

## Šta smo radili

Jedna od najproduktivnijih sesija do sada. Obuhvata: bug fix, istraživanje novih jezika, veliki arhitekturalni refaktor `run_test.py`, uvođenje temperature varijanti metoda, novu `translation_score` metriku, prelaz na LaBSE multilingualni embedding, i čisti restart testova sa standardizovanim pristupom.

---

## Korak 1 — Log bug fix

Ispravljen poznati bug iz session_05:

**Fajl:** `src/run_test.py`, linija 357  
**Promjena:** `text[:50]` → `translated[:50]`

Log sada prikazuje prevedeni tekst umjesto originala — potvrđeno u `run20_de_nl_af.log`.

---

## Korak 2 — Istraživanje jezika (zapadnogermanska grupa)

Prije pokretanja testova provedeno istraživanje podrške za potencijalne nove jezike.

### Jidiš vs. Hebrejski

Dva potpuno različita jezika:
- **Hebrejski** (`he`, `heb_Hebr`) — moderni jezik, govornici u Izraelu
- **Jidiš** (`yi`, `ydd_Hebr`) — jezik jevrejske dijaspore, germansko-hebrejska mješavina

NLLB podržava Eastern Yiddish (`ydd_Hebr`). Gemma 3 slabo podržava oba.

### Frizijski (`fy`, `fry_Latn`)

Zapadnogermanski, ~470k govornika u Nizozemskoj. NLLB podrška ograničena. Odgođeno za kasnije.

### Luksemburški (`lb`, `ltz_Latn`)

Iznenađenje — NLLB-200 eksplicitno pokriva luksemburški. ~400k govornika. Odgođeno za kasnije.

**Odluka:** Ostajemo na `de`, `nl`, `af`. Egzotični jezici identificirani i dokumentirani za buduće sesije.

---

## Korak 3 — Veliki refaktor `run_test.py`

### Motivacija

Potreba za testiranjem različitih temperatura otvorila je šire pitanje: kako generički podržati bilo koju kombinaciju modela i parametara. Odlučeno je da se jednom napravi ispravna arhitektura.

### Nove metode

| Method string | Opis |
|---------------|------|
| `nllb`        | NLLB-200 beam search, deterministički (`do_sample=False`, `repetition_penalty=1.3`) |
| `nllb_t05`    | NLLB-200 sampling, `do_sample=True`, `temperature=0.5` |
| `gemma`       | Gemma 3 12b via Ollama Cloud, default temperatura |
| `gemma_t05`   | Gemma 3 12b via Ollama Cloud, `temperature=0.5` |

**`VALID_METHODS`** konstanta je jedini izvor istine — program se odmah gasi pri nepoznatoj metodi.

### Kako dodati novu metodu — minimalni zahvat

Baza: **ništa** — kolona `method` je `VARCHAR`, prima bilo koji string.

U `run_test.py` — samo 3 mjesta:
1. `VALID_METHODS` — dodati novi string
2. `dispatch_translate()` — dodati `elif` granu
3. `dispatch_back_translate()` — dodati `elif` granu

Sve ostalo (`clear_test`, `insert_result`, `update_winners`, `LANG_MAP`) je generičko.

### Ključne arhitekturalne izmjene

- `translate_nllb(... temperature=None)` — `None` = beam search, `float` = sampling
- `translate_gemma(... temperature=None)` — `None` = Ollama default, `float` = `options.temperature`
- `dispatch_translate()` i `dispatch_back_translate()` — centralno routing mjesto, `main()` je čist
- `LANG_NAMES` i `LANG_NAMES_BACK` — izvučeni kao module-level konstante
- `clear_test(conn, test_id, langs, methods)` — briše samo kombinaciju `langs + methods`
- NLLB model se učitava jednom za obje NLLB metode

---

## Korak 4 — translation_score nova metrika

### Problem

Postojeći `score` = `cosine(RE, RFE)` — mjeri kvalitet back-translationa, ne samog prevoda.

Nedostajao je `cosine(RE, RF)` — direktna semantička sličnost originala i prevoda.

### Rješenje

```sql
ALTER TABLE test_results ADD COLUMN translation_score REAL;
```

U `run_test.py`:
```python
sc    = compute_score(text, back, embedder)       # cosine(RE, RFE)
tr_sc = compute_score(text, translated, embedder) # cosine(RE, RF)
insert_result(..., sc, tr_sc)
```

### Problem sa engleskim embedderom

Sa `all-MiniLM-L6-v2` (engleski model):
- `cosine(RE, RFE)` = 0.888 — visok (engleski vs engleski)
- `cosine(RE, RF)` = 0.405 — nizak (engleski vs francuski)

Razlog: engleski i francuski su u različitim dijelovima vektorskog prostora. `translation_score` nije bio upotrebljiv.

---

## Korak 5 — Prelaz na LaBSE multilingualni embedding

### Istraživanje

Tri kandidata u porodici sentence-transformers:

| Model | Dim | Jezici | Napomena |
|-------|-----|--------|---------|
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 50+ | Brz, lagan, poznat |
| `paraphrase-multilingual-mpnet-base-v2` | 768 | 50+ | Bolji kvalitet |
| `LaBSE` | 768 | 109 | Najbolji za pronalaženje prevedenih parova — tačno naš use case |

### Odluka: LaBSE

Jedan model za sve — i `score` i `translation_score`. Čistije, konzistentnije.

```python
EMBED_MODEL = "sentence-transformers/LaBSE"
```

### Validacija

```python
# Test EN-FR:
cosine("The dog is barking.", "Le chien aboie.") = 0.9142  # LaBSE
# Vs. all-MiniLM-L6-v2: ~0.40
```

### Retroaktivno reračunavanje

Svih 639 postojećih redova reračunato sa LaBSE za obje metrike.

### Rezultati sa LaBSE — test_002 (fr, it, es)

| lang | method | tr_score | back_score | delta |
|------|--------|----------|------------|-------|
| es | gemma | 0.899 | 0.953 | 0.055 |
| es | nllb | 0.889 | 0.925 | 0.036 |
| fr | gemma | 0.888 | 0.931 | 0.043 |
| fr | nllb_t05 | 0.884 | 0.806 | **-0.078** |
| it | gemma | 0.907 | 0.958 | 0.051 |
| it | nllb | 0.902 | 0.897 | -0.004 |

**Ključni uvid — negativan delta:**
`nllb_t05` za `fr` ima `back_score` 0.806 ali `tr_score` 0.884 — prevod je semantički bolji nego što back-translation pokazuje. NLLB gubi informaciju pri povratku na engleski. Naš originalni `score` je **podcjenjivao** kvalitet NLLB prevoda.

---

## Korak 6 — Standard i čisti restart

### Usvojen standard

> Svaki jezik u svakom testu uvijek ima sve 4 metode.  
> Ako dodajemo novi jezik — sve 4 metode.  
> Ako dodajemo novu metodu — retroaktivno za sve jezike.

### Registry ažuriran

Dodan komentar sa listom validnih metoda direktno u `test_registry.yaml` — analogno listi jezika. Registry je sada i dokumentacija:

```yaml
# Validne metode (VALID_METHODS u run_test.py):
#   nllb       — NLLB-200 beam search, deterministički
#   nllb_t05   — NLLB-200 sampling, temperature=0.5
#   gemma      — Gemma 3 12b Ollama Cloud, default temperatura
#   gemma_t05  — Gemma 3 12b Ollama Cloud, temperature=0.5
```

### Čisti restart baze

```sql
TRUNCATE test_results RESTART IDENTITY;
```

### Novi test_001 — čisti start

```
Jezici:   hr, sr, de, nl, fr, it  (6 jezika)
Metode:   nllb, nllb_t05, gemma, gemma_t05  (4 metode)
Rečenice: 1–20
Ukupno:   480 prevoda
```

Komanda:
```bash
cd /home/balsam/buchenberg && nohup bash run20.sh --test_id test_001 > logs/run20_clean_start.log 2>&1 &
```

---

## Otvoreno za sljedeću sesiju

1. **Logging standardizacija** — jedan log po runu sa timestamp u imenu, dodati `time` u `run20.sh`, ukloniti dupli logging
2. **Protokol prikazivanja komandi** — Claude uvijek prikazuje komandu prije izvršavanja
3. **Analiza čistog test_001** — uporedna analiza svih 6 jezika i 4 metode sa LaBSE
4. **Ostali jezici** — `bs`, `sl`, `mk`, `bg`, `af`, `es`, `pt`, `ro` čekaju
5. **README ažuriranje** — LaBSE, translation_score, novi standard metoda

---

## Izmjene fajlova u ovoj sesiji

| Fajl | Izmjena |
|------|---------|
| `src/run_test.py` | Bug fix, refaktor metoda/temperatura/dispatch, LaBSE, translation_score |
| `tests/test_registry.yaml` | Novi format sa komentarom metoda, čisti test_001 |
| `docs/sessions/session_06.md` | Ovaj dokument |

---

## Trajanja runova

| Run | Jezici | Metode | Prevoda | Trajanje | Greške |
|-----|--------|--------|---------|----------|--------|
| run20_de_nl_af | de, nl, af | nllb, gemma | 120/120 | ~4.5 min | 0 |
| run20_t05 | de, nl, af | nllb_t05, gemma_t05 | 119/120 | ~5.5 min | 1 timeout |
| run20_sl | sl | sve 4 | 80/80 | ~3 min | 0 |
| run20_hr_mk_t05 | hr, mk | nllb_t05, gemma_t05 | 80/80 | ~3.5 min | 0 |
| run20_clean_start | hr, sr, de, nl, fr, it | sve 4 | 480 | u toku | — |

---

*Flavio & Claude · Session 06 · 16. maj 2026.*

---

## Korak 8 — GA implementacija i testiranje

### Nove skripte

| Fajl | Opis |
|------|------|
| `src/step7_create_ga_table.py` | Kreira `ga_results` tabelu |
| `src/run_ga.py` | GA runner (528 linija) |
| `src/ga_snapshot.py` | Snapshot stanja prije GA |
| `src/ram_monitor.sh` | Monitor RAM/swap tokom runa |
| `run30.sh` | Orchestrator (sa `time`) |

### Nova tabela `ga_results`

```sql
CREATE TABLE ga_results (
    id, sentence_id, target_lang, generation, individua_id,
    tekst, fitness, pivot_lang, metoda,
    je_elita, je_pobjednik, created_at
);
```

### GA parametri

| Parametar | Default | Opis |
|-----------|---------|------|
| `--pop_size` | 8 | Maksimalna veličina populacije |
| `--elite_n` | 2 | Uvijek preživljava N najboljih |
| `--max_gen` | 20 | Maksimalan broj generacija |
| `--conv_thresh` | 0.005 | Prag konvergencije |
| `--conv_gens` | 3 | Generacija bez poboljšanja → stop |
| `--quality_stop` | 0.95 | Fitness > ovo → stop |
| `--mutate_rate` | 0.15 | Stopa mutacije |
| `--dup_thresh` | 0.99 | Cosine > ovo → duplikat |
| `--green_thresh` | 0.90 | Zelene rečenice → preskači GA |

### Filter zelene/žute/crvene

GA se pokreće samo za žute i crvene rečenice:
- 🟢 **Zelene** (tr_score ≥ 0.90) → preskačemo
- 🟡 **Žute** (0.80–0.89) → GA
- 🔴 **Crvene** (< 0.80) → GA

Za IT, 40 rečenica: **34 zelene (85%), 6 žutih (15%), 0 crvenih**.

### Benchmark rezultati — paralelizam

Testirano na 6 žutih IT rečenica:

| Run | Konfiguracija | Trajanje | RAM peak |
|-----|--------------|----------|----------|
| Run 1 | 1×40 serijski | ~5 min | ~738 MB |
| Run 2 | 2×20 paralelno | ~7 min | ~738 MB |
| Run 3 | 4×10 paralelno | ~3 min | ~1.7 GB |

**Zaključci:**
- OS dijeli model stranice — 4 procesa troše samo 1.7 GB, ne 4×4.5 GB
- CPU contention smanjuje korist paralelizma za NLLB (CPU-bound)
- Pravi benchmark zahtijeva više žutih/crvenih rečenica

### GA rezultati — IT, 6 žutih rečenica

| s | prije GA | nakon GA | delta | pivot |
|---|---------|---------|-------|-------|
| s1 | 0.8525 | 0.8525 | 0.000 | — |
| s6 | 0.9000 | 0.9000 | 0.000 | — |
| s9 | 0.8698 | **0.8724** | **+0.0026** ↑ | af |
| s17 | 0.8336 | 0.8336 | 0.000 | — |
| s24 | 0.8616 | 0.8616 | 0.000 | — |
| s38 | 0.8299 | 0.8299 | 0.000 | — |

**1/6 poboljšano** — s9 kroz Afrikaans pivot + gemma+gemma.

### Otvorene stavke za GA tuning

1. Povećati `conv_gens` na 5-7
2. Smanjiti `conv_thresh` na 0.002
3. Dodati `--crossover_rate` parametar (tipično 0.85)
4. Dodati `--max_children` (do 3 djece po crossoveru)
5. Batch processing za Gemma i NLLB
6. Retry logika za Ollama timeouts

---

## Ažurirana lista otvorenog za sljedeću sesiju

1. GA tuning — conv_gens, conv_thresh, crossover_rate, max_children
2. Batch processing — Gemma i NLLB
3. Retry logika — exponential backoff za Ollama timeouts
4. Logging standardizacija — timestamp u imenu loga, ukloniti dupli logging
5. Protokol prikazivanja komandi — uvijek prikazati komandu prije izvršavanja ✅ (usvojeno)
6. README ažuriranje — LaBSE, translation_score, GA, novi standard

---

---

## Korak 9 — Batch processing i optimizacije

### Motivacija

Single mode: jedan LLM/NLLB poziv po rečenici — sporo i rate-limit neprijateljski.
Batch mode: N rečenica u jednom pozivu — drastično ubrzanje.

### Nove batch funkcije (`run_test.py`)

| Funkcija | Opis |
|----------|------|
| `translate_nllb_batch(texts, ...)` | NLLB batch — `tokenizer(texts, padding=True)` + `batch_decode` |
| `translate_gemma_batch(texts, ...)` | Gemma batch — numerisana lista u promptu, JSON array odgovor |
| `back_translate_gemma_batch(texts, ...)` | Gemma back-translation batch |
| `parse_gemma_batch_response(raw, n)` | Robusni parser — 4 strategije |

### Novi parametar

```bash
bash run20.sh --test_id test_001 --batch_size 20
```

Default: `--batch_size 20`

### Robusni JSON parser — 4 strategije

Gemma ponekad ne vrati čist JSON (pogrešan zarez, prelom linije, markdown blok). Parser pokušava redom:

1. **Direktni `json.loads`** nakon čišćenja markdown blokova
2. **Regex ekstrakcija** `[...]` bloka iz teksta
3. **Regex quoted strings** — svi `"..."` u odgovoru
4. **Numbered list** — `1. tekst`, `2. tekst`...

Tek ako sve strategije ne uspiju → fallback na single mode.

### Benchmark rezultati

| batch_size | Trajanje (40 rec, 2 metode) | Fallbacki | Prevoda/min |
|-----------|----------------------------|-----------|-------------|
| single (stari) | ~20 min | 0 | ~8 |
| 20 | ~1 min 43 sec | 2* | ~47 |
| 50 (stari parser) | ~2 min 48 sec | 3 | ~29 |
| 50 (novi parser) | ~1 min 51 sec | **0** | **~43** |

*Eliminisano novim parserom

**Zaključak:** batch=20 i batch=50 su podjednako brzi (~43-47 prevoda/min). **~6x ubrzanje** u odnosu na single mode.

### LaBSE `local_files_only`

```python
# Prije — upozorenje o HF Hub pri svakom startu:
SentenceTransformer(EMBED_MODEL)

# Poslije — čisto, bez mrežnog poziva:
SentenceTransformer(EMBED_MODEL, local_files_only=True)
```

Primijenjeno u `run_test.py` i `run_ga.py`.

---
