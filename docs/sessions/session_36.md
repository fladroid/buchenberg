# Session 36 — RAG scorer: implementacija i evaluacija

**Datum:** 2. jun 2026.
**Učesnici:** Flavio & Claude
**Nastavlja:** Session 35 (bb pipeline, Jezički RAG — bb_rag_init.py pokrenut)

---

## Kontekst

Sesija je počela provjerom završetka RAG runa pokrenutog u sesiji 35. Run je završen uspješno. Implementiran pun RAG scorer pipeline i donesen zaključak o njegovoj upotrebljivosti.

---

## Što je urađeno

### 1. Provjera RAG runa (sesija 35)

```
tail -30 logs/bb_rag_init_hr_it_de.log
```

- **Status:** ✅ Završen — 3 jezika × 50.000 rečenica = 150.000 redova u `bb_rag_korpus`
- **Trajanje:** 3h 43min (serijski, jedan jezik za drugim)
- **ANALYZE** pokrenut ručno nakon bulk loada — statistike osvježene za IVFFlat index

### 2. Izmjene sheme

```sql
ALTER TABLE bb_prevodi_recenica ADD COLUMN prevod_vektor vector;
ALTER TABLE bb_prevodi_recenica ADD COLUMN naturalness_score real;
```

Napomena: `vector` bez dužine — fleksibilno za promjenu embeddera.

### 3. bb_06_enkodiranje.py

Enkodira prevode i upisuje `prevod_vektor` u `bb_prevodi_recenica` gdje je NULL.

- Idempotentno — preskače redove gdje vektor već postoji
- Filtrira po embedderu iz `bb_embeddings`
- `executemany` umjesto red-po-red UPDATE
- BATCH_SIZE=256

**Run:** 480 redova (e5-large), trajanje: 2:17 min ✅

### 4. bb_07_rag_score.py

k-NN upit u `bb_rag_korpus`, računa `naturalness_score` = prosječni cosinus k najbližih susjeda u ciljnom jeziku.

- `--k 10` default
- Idempotentno — samo redovi gdje `naturalness_score IS NULL`

**Run:** 480 redova, trajanje: ~4 min ✅

### 5. Rezultati

| jezik | model | avg_naturalness | avg_semantic | avg_composite |
|-------|-------|----------------|--------------|---------------|
| hr | nllb-600M | 0.8517 | 0.9280 | 0.8898 |
| hr | ministral-3:14b | 0.8535 | 0.9260 | 0.8897 |
| hr | gemma3:12b | 0.8491 | 0.9285 | 0.8888 |
| hr | gemma4:31b | 0.8475 | 0.9275 | 0.8875 |
| it | nllb-600M | 0.8691 | 0.9230 | 0.8961 |
| it | ministral-3:14b | 0.8671 | 0.9220 | 0.8946 |
| it | gemma4:31b | 0.8678 | 0.9176 | 0.8927 |
| it | gemma3:12b | 0.8682 | 0.9172 | 0.8927 |

---

## Ključni zaključci

### RAG scorer — ograničena upotrebljivost u trenutnoj formi

- **Korpus problem:** OpenSubtitles je filmski dijalog — mjeri "sličnost filmskom dijalogu", ne književnu prirodnost
- **NLLB paradoks:** NLLB pobjeđuje na kompozitnom scoreu zbog visokog `naturalness_score` — bukvalni prevodi su bliži kolokvijalnom korpusu, ali to nije signal kvaliteta
- **LLM modeli:** viši `semantic_score`, niži `naturalness_score` — kreativniji, semantički vjerniji, ali "netipičniji" za filmski dijalog
- **Zaključak:** RAG scorer ne koristiti kao primary signal u `bb_04_pobjednik.py`

### Što imamo i što radi

- `translation_score` (cosine EN→prevod) ostaje naša najjača i najčišća metrika
- RAG infrastruktura ostaje u bazi — 150k rečenica, 2GB, prostor nije problem (309GB slobodno)
- Vrijednost RAG-a se može realizovati s boljim korpusom (književna proza na ciljnom jeziku)

### Potencijalni bolji korpusi

| Korpus | Prednost | Problem |
|--------|----------|---------|
| Project Gutenberg (ciljni jezik) | Književni registar | Mali jezici slabo pokriveni |
| Wikipedia | Informativni, neutralan | Enciklopedijski, bez emocija — nije književna proza |
| OpenSubtitles | Dostupan za sve jezike | Filmski dijalog — pogrešan registar |

**Odluka:** Ne forsirati. RAG kao scorer odgođen dok ne nađemo žanrovski konzistentan korpus.

---

## Napomene o performansama

- `bb_rag_init.py` — bulk load bez optimizacije: INSERT red-po-red + commit svakih 256 redova + aktivan IVFFlat index tokom loada
- **Za buduće runove (novi jezici):** drop index → bulk load → rebuild index → ANALYZE

---

## Otvoreno za sljedeću sesiju

1. **`bb_04_pobjednik.py`** — trenutno koristi `score` (back-translation); razmotriti prelaz na `translation_score` kao primary signal
2. **Proširenje modela** — de korpus ima samo 3 modela; dodati nllb za de
3. **Novi jezici** — fr, es, sr (RAG korpus nije preduvjet)
4. **Evaluacija pobjednika** — analiza koji model pobjeđuje najčešće po jeziku
5. **RAG korpus** — istraživanje književnih izvora za ciljne jezike (Gutenberg HR/IT/DE)

---

## Git

- Commit: `feat: RAG scorer pipeline — bb_06_enkodiranje, bb_07_rag_score, prevod_vektor, naturalness_score`

---

*Flavio & Claude · Buchenberg · Session 36 · 2. jun 2026.*
