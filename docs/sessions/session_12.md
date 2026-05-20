# Session 12 — Buchenberg

**Datum:** 20. maj 2026.
**Učesnici:** Flavio & Claude

---

## Cilj sesije

Infrastrukturna provjera, health_check skripta, fix filter_sentences_by_score buga, ponavljanje IT pipeline-a sa ispravnom trofaznom arhitekturom.

---

## Korak 1 — Inicijalizacija sesije

Pročitani: `buchenberg_napomena.md`, `README.md`, session dokumenti 09/10/11.

GA run 2 za `it` (pokrenut prethodne sesije) bio završen — upisani pobjednici.

---

## Korak 2 — health_check.py

Implementirana nova skripta `src/health_check.py` za infrastrukturnu provjeru svih komponenti:

1. `.env` fajl — sve varijable, maskiranje lozinki/ključeva
2. PostgreSQL — konekcija, broj redova po tabeli, boje rečenica za zadnja 3 testa
3. Ollama Cloud — lista dostupnih modela + test poziv za gemma i ministral
4. NLLB — keš na disku + transformers import
5. Python venv — provjera svih paketa
6. test_registry.yaml — pregled svih testova
7. Git — uncommitted promjene + zadnja 3 commita

**Pokretanje:** `venv/bin/python src/health_check.py`

**Otkriće:** Ministral se zove `ministral-3:14b` (ne `mistral-small3.1:24b`).

**Commit:** `978d46c feat: health_check.py — infrastrukturna provjera svih komponenti`

---

## Korak 3 — Analiza s37 i trofazna arhitektura

### Provjera NLLB upotrebe

Utvrđeno da je NLLB korišten samo u test_001 (240+240 redova). U test_012 faza 3 (nllb) nije bila pokrenuta jer je ministral podigao sve crvene — ali s37 je ostala crvena i nikad nije dobila NLLB šansu.

### Analiza s37 po jezicima

s37 (*"There are certainly one or two indications upon the stick."*) je crvena na svim jezicima osim NL i PT (žute). Karakteristike:
- Svi modeli daju score < 0.80 za bg, de, hr, it
- Nema NLLB prevoda ni na jednom jeziku u test_012
- PT paradoks: ministral→0.8064 ("bastão"), gemma→0.4304 ("bengala") — ista značenjska riječ, enormna razlika u scoreu

### Dogovorena trofazna arhitektura (potvrđena)

- **Faza 1** — gemma+gemma_t05 za SVE rečenice
- **Faza 2** — ministral+ministral_t05 za žute+crvene (`--score_to 0.8999`)
- **Faza 3** — nllb+nllb_t05 za crvene (`--score_to 0.7999`)
- **GA** — za žute+crvene nakon faze 3

---

## Korak 4 — Kritični bug: filter_sentences_by_score

### Opis buga

`filter_sentences_by_score()` gledala MAX score across **svih jezika**, ne per `(test_id, target_lang)`. Rezultat: faza 3 za IT vratila 0 rečenica jer je s37 imala MAX=0.8761 (od NL!) što je iznad praga 0.7999.

Bug je bio prisutan od session_09 — tada je fiksiran `test_id` filter, ali `target_lang` filter nije bio dodan.

### Fix

```python
# PRIJE — gledalo MAX across svih jezika
def filter_sentences_by_score(conn, sentences, test_id, score_from, score_to):
    cur.execute("""
        SELECT sentence_id, MAX(translation_score) as best
        FROM test_results
        WHERE test_id = %s
        GROUP BY sentence_id
    """, (test_id,))

# POSLIJE — per (test_id, target_lang)
def filter_sentences_by_score(conn, sentences, test_id, lang, score_from, score_to):
    cur.execute("""
        SELECT sentence_id, MAX(translation_score) as best
        FROM test_results
        WHERE test_id = %s AND target_lang = %s
        GROUP BY sentence_id
    """, (test_id, lang))
```

Filter je pomjeren unutar `for lang in langs` petlje — sada se poziva per jezik.

**Commit:** `d13b94c fix: filter_sentences_by_score — dodati target_lang filter, per (test_id, lang)`

---

## Korak 5 — IT pipeline ponovljen ispravno

### Brisanje IT iz test_012

```sql
DELETE FROM test_results WHERE test_id = 'test_012' AND target_lang = 'it';  -- 158 redova
DELETE FROM ga_results  WHERE test_id = 'test_012' AND target_lang = 'it';  -- 545 redova
```

Izvršeno kroz `balsam:run_command` (docker exec pgdb psql).

### Rezultati po fazama

| Faza | Metode | 🟢 | 🟡 | 🔴 |
|------|--------|:--:|:--:|:--:|
| Faza 1 | gemma+gemma_t05 (sve) | 13 | 18 | 9 |
| Faza 2 | ministral+ministral_t05 (žute+crvene) | 13 | 19 | 8 |
| Faza 3 | nllb+nllb_t05 (crvene) | 15 | 21 | 4 |
| GA | run30.sh | **23** | **13** | **4** |

NLLB u fazi 3 podigao 2 dodatne zelene u odnosu na prethodnu arhitekturu bez faze 3.

### 4 preostale crvene (tvrdi orasi)

| s_id | score | Tekst |
|------|-------|-------|
| s9 | 0.7949 | *"It was just such a stick as the old-fashioned family practitioner..."* |
| s16 | 0.7978 | *"Since we have been so unfortunate as to miss him..."* |
| s23 | 0.7797 | *"Because this stick, though originally a very handsome one..."* |
| s37 | 0.7718 | *"There are certainly one or two indications upon the stick."* |

---

## Naučene lekcije

- **health_check.py je obavezan alat** — pokrenuti na početku svake sesije, odmah otkriva probleme s modelima, bazom, venvom
- **filter_sentences_by_score bug** — prisutan od session_09, uzrokovao pogrešne rezultate. Uvijek filtrirati per `(test_id, target_lang)`
- **Trofazna arhitektura mora biti poštovana** — preskakanje faze 3 ostavlja crvene rečenice bez NLLB šanse
- **balsam:run_command** — Claude može direktno izvršavati `docker exec` komande, nema potrebe za ručnim izvršavanjem

---

## Izmjene fajlova u ovoj sesiji

| Fajl | Izmjena |
|------|---------|
| `src/health_check.py` | nova skripta — infrastrukturna provjera |
| `src/run_test.py` | fix filter_sentences_by_score — dodati target_lang |
| `docs/sessions/session_12.md` | ovaj dokument |

---

## Otvoreno za sljedeću sesiju

1. **Faza 3 + GA za ostale jezike test_012** — bg, de, hr, nl, pt (nllb za crvene, pa GA)
2. **Novi jezici** — bs, sl, mk, af, es, ro
3. **Pipeline orchestrator** — finalni prevod iz test_results
4. **multilingual-e5-large** — testirati kao alternativu MiniLM

---

## Handoff blok

- **Zadnja mijenjana skripta:** `src/run_test.py` — fix filter_sentences_by_score
- **Zadnji test:** test_012 IT završen — faza 1+2+3+GA, 🟢23 🟡13 🔴4
- **Ostali jezici test_012:** bg, de, hr, nl, pt — imaju crvene bez NLLB (faza 3 nije pokrenuta)
- **Kritično:** Pokrenuti fazu 3 (`--score_to 0.7999`) za svaki jezik PRIJE GA

---

*Flavio & Claude · Session 12 · 20. maj 2026.*
