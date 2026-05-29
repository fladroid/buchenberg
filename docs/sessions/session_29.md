# Session 29 — Tabela translations, punjenje 4480 prevoda

**Datum:** 2026-05-29  
**Učesnici:** Flavio & Claude  
**Nastavlja:** Session 28 (LLM-as-judge PoC)

---

## Kontekst — gdje smo stali

Session 28 je završila s jasnim zaključkom: metrika evaluacije je fundamentalni problem projekta. Back-translation cosinus (MiniLM) je pristran prema doslovnosti. LLM-as-judge ima position bias i default zone. Bez referentnog prevoda, pouzdana automatska evaluacija književnog prevoda je otvoreni NLP problem.

---

## Korak 1 — Nova paradigma: odvajanje prevoda od evaluacije

**Ideja (Flavio):** Kreirati centralnu tabelu prevoda — jednom prevesti, slobodno evaluirati koliko puta hoćeš. Eliminacija stalnog pozivanja Ollame kao izvora stresa i nepouzdanosti.

**Tabela `translations`:**

```sql
CREATE TABLE translations (
    id            SERIAL PRIMARY KEY,
    sentence_id   INTEGER REFERENCES sentences(id),
    book_id       INTEGER REFERENCES books(id),
    target_lang   CHAR(2)      NOT NULL,
    model         VARCHAR(30)  NOT NULL,
    temperature   REAL         NOT NULL,
    translation   TEXT,
    created_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE (sentence_id, target_lang, model, temperature)
);
```

Stara prazna tabela `translations` (drugačija struktura) dropovana i kreirana nova.

---

## Korak 2 — `run_translations.py`

Nova skripta za punjenje tabele. Parametrizovana:

```bash
venv/bin/python src/run_translations.py \
    --lang it --sent_from 1 --sent_to 40 \
    --models gemma3 ministral gemma4 nllb \
    --temps 0.1 0.5 --batch_size 20
```

**Greška u prvoj verziji:** JSON batch format za API pozive — modeli vraćaju nevažeći JSON (apostrofi, prazan content). Fix: `__!!__` separator pattern kopiran iz `run_test.py`.

**Greška u drugoj verziji:** Nema fallback na single mode — isti propust koji je izazvao probleme u ranim verzijama `run_test.py`. Fix: dodan `translate_llm_single()` + fallback u `translate_llm_chunk()` kada `parse_sep()` ne vrati očekivan broj dijelova.

**Ključna lekcija sesije:** Prije pisanja novog koda za API pozive — uvijek pogledati kako postojeće skripte koje zadovoljavajuće rade implementiraju iste pozive. Nakon višenedeljnog rada na Buchengergu i višemjesečnog rada na srodnim projektima, iskustvo je u kodu koji već postoji. Ne ponavljati iste greške iz početka.

---

## Korak 3 — Punjenje

**Parametri:** 4 modela (`gemma3:12b`, `ministral-3:14b`, `gemma4:31b`, `nllb-600M`), 2 temperature (0.1 i 0.5), `batch_size=20`, rečenice 1–40.

**Jezici punjeni:**

| Grupa | Jezici | Prevoda |
|-------|--------|---------|
| Romanski | it, fr, pt, es, ro | 5 × 320 = 1600 |
| Germanski | de, nl, af | 3 × 320 = 960 |
| Južnoslavenski | hr, bg, sr, bs, sl, mk | 6 × 320 = 1920 |
| **Ukupno** | **14 jezika** | **4480** |

Svaka kombinacija `(sentence_id, target_lang, model, temperature)` je jedinstvena — `ON CONFLICT DO NOTHING` omogućuje sigurno ponavljanje.

**Trajanje po grupi:** ~5 min/jezik → 14 jezika serijski (Ollama Cloud: jedan model odjednom) = ~70 min ukupno.

**Napomena o RO:** Inicijalni run dao 300/320. Umjesto dopune, Flavio odlučio obrisati RO redove i pokrenuti ponovo s ispravljenom skriptom. Rezultat: 320/320.

---

## Korak 4 — Analiza fallback padova

Grep svih logova (`translations_*.log`) za WARNING/fallback.

**Dominantni pattern: `19/20` na chunk 1**

Uzrok je strukturalni, ne tehnički. Rečenice s1, s2, s3 su metadata knjige:
- s1: `"The Hound of the Baskervilles"` (naslov)
- s2: `"by Sir Arthur Conan Doyle"` (autor)
- s3: `"Chapter 1 Mr. Sherlock Holmes"` (naslov poglavlja)

Modeli ih spajaju u jedan output (kratke su i tematski vezane) i vraćaju 19 umjesto 20 separatora. Fallback na single ih sve spašava.

**chunk 2 pad (gemma4/DE):** Dugačka rečenica s citiranim govorom uzrokovala parsing grešku. Fallback spasio.

**Statistika padova po modelu:**

| Model | Broj padova | Najčešće |
|-------|-------------|---------|
| ministral | ~15 | chunk 1, gotovo svaki jezik |
| gemma3 | ~8 | de, nl, af, mk |
| gemma4 | 2 | de chunk 2 |
| nllb | 0 | — |

**Zaključak:** Fallback radi savršeno — svi prevodi spašeni. Pravi fix za budućnost: tretirati s1-s3 posebno (metadata, ne prose).

---

## Izmjene koda

| Fajl | Izmjena |
|------|---------|
| `src/run_translations.py` | Nova skripta — batch prevod s fallback na single |

---

## Stanje baze

```
SELECT target_lang, COUNT(*) FROM translations GROUP BY target_lang;
-- 14 jezici × 320 = 4480 redova, svi kompletni
```

---

## Na horizontu

1. **Evaluacija iz tabele `translations`** — osmisliti metodu koja čita iz tabele umjesto pozivanja Ollame
2. **DeepL integracija** — dodati kao petu metodu prevoda u `translations`
3. **Metadata rečenice fix** — s1-s3 tretirati posebno u batch logici
4. **Proširenje na rečenice 41–100** — kada se utvrdi stabilan evaluacijski pristup
5. **LLM-as-judge v3** — AB+BA testiranje za eliminaciju position biasa

---

## Handoff blok

- **`translations` tabela:** 4480 redova, 14 jezika, potpuna
- **`run_translations.py`:** aktivan u `src/`
- **Baza:** `test_results` i GA tabele nisu mijenjane
- **Git:** commiti `session_28b`, `session_28c`, `session_28d` + ovaj
- **Model:** Sonnet 4.6 medium

---

*Flavio & Claude · Session 29 · 2026-05-29*
