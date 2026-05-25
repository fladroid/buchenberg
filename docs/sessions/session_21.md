# Session 21 — Buchenberg

**Datum:** 25. maj 2026.
**Autor:** Flavio & Claude

---

## Cilj sesije

Dizajn i implementacija nove pivot strategije prevoda — jednog pobjednika po rečenici po jeziku određenog kroz iterativno pivotiranje na najjači dostupni prevod.

---

## Korak 1 — Inicijalizacija

Pročitani: `buchenberg_napomena.md`, `README.md`, session dokumenti 18/19/20. Health check — sve zeleno. Ollama Cloud: 39 modela dostupno.

---

## Korak 2 — Definicija pivot strategije

Konceptualna rasprava i definicija nove strategije prevoda. Ključni principi:

**Osnovni princip:** Svaka originalna EN rečenica ima na svakom jeziku tačno jedan prevod — pobjednik određen maksimalnim `translation_score` (cosine EN↔prevod). Ostali podaci služe za statističke evaluacije.

**Pivot princip:** Kada imamo prevode na >= 2 jezika, pronađi prevod s globalnim maksimalnim scoreom (pivot), prevedi pivot_tekst → svi jezici s nižim scoreom. Ponavlja se dok nema poboljšanja ili do max_iterations.

**Kriteriji zaustavljanja (3 nivoa):**
- Nivo 1 (jezik): novi score ≤ stari → ne updateuj
- Nivo 2 (rečenica): ni jedan jezik poboljšan → konvergirala
- Nivo 3 (test): ni jedna rečenica poboljšana → stop
- Sigurnosni stop: max_iterations

**Konfiguracija:** `langs`, `models` i `temperatures` su sve liste — svaka kombinacija je kandidat, pobjeđuje max score.

---

## Korak 3 — Implementacija

### Nova tabela: `pivot_results`

```sql
CREATE TABLE IF NOT EXISTS pivot_results (
    id                SERIAL PRIMARY KEY,
    test_id           VARCHAR(20) NOT NULL,
    sentence_id       INTEGER REFERENCES sentences(id),
    target_lang       CHAR(2) NOT NULL,
    model             VARCHAR(40),
    temperature       REAL,
    translated_text   TEXT,
    translation_score REAL,
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW(),
    UNIQUE (test_id, sentence_id, target_lang)
);
```

UNIQUE po `(test_id, sentence_id, target_lang)` — uvijek jedan pobjednik. `ON CONFLICT WHERE EXCLUDED.translation_score > pivot_results.translation_score` garantuje da score može samo rasti.

### Novi fajlovi

| Fajl | Opis |
|------|------|
| `src/step_create_pivot_table.py` | Kreira `pivot_results` tabelu |
| `tests/pivot_registry.yaml` | Konfiguracija pivot testova |
| `src/run_pivot_init.py` | Korak 1: inicijalni EN→lang prevodi |
| `src/run_pivot.py` | Korak 2: pivot iteracije do konvergencije |

### Dvostepeni pipeline

```
Korak 1 — run_pivot_init.py:
  Za svaku kombinaciju (lang, model, temperature):
    EN → lang batch prevod → score → upiši/updateuj ako bolji

Korak 2 — run_pivot.py:
  Dok god ima poboljšanja (ili < max_iterations):
    Za svaku rečenicu: pivot = jezik s max scoreom
    Grupiši rečenice po pivot jeziku (batch optimizacija)
    pivot_tekst → svi ostali jezici → updateuj ako score bolji
```

**Zašto dvostepeni:** Preglednost i fleksibilnost — inicijalni prevodi su trajni, pivot se može pokretati više puta bez ponovnog prevođenja.

### `pivot_registry.yaml` format

```yaml
pivot_001:
  book: hound_of_the_baskervilles
  sent_from: 1
  sent_to: 40
  langs: [hr, de, fr, it]
  models: [gemma3:12b, ministral-3:14b]
  temperatures: [0.3, 0.7]
  max_iterations: 10
```

---

## Korak 4 — Testiranje

### pivot_001 — smoke test (5 rečenica, 1 jezik)

Inicijalni test s `de`, `gemma3:12b`, `temp=0.3`, 5 rečenica. Pivot faza odmah stala (samo 1 jezik → nema pivot). Baza: 5 redova. ✅

### pivot_001 — test modela (5 rečenica, 2 modela)

Dodan `ministral-3:14b`. Potvrđeno da `ON CONFLICT WHERE` radi — ministral pobijedio gemma na s1, s4, s5; gemma ostao pobjednik na s2, s3. ✅

### pivot_002 — puni test (40 rečenica, 2 jezika)

`de, hr`, `gemma3:12b`, `temp=0.3`. Konvergiralo na max_iterations=10 s 1 poboljšanjem u zadnjoj iteraciji.

### pivot_002 — proširenje (4 jezika)

Dodani `fr, it`. Run na postojećim podacima — inicijalna faza upisala FR i IT, DE i HR updateovani samo gdje je score bolji. Konvergiralo u iteraciji 8. Trajanje: 9 min 49 sec.

### pivot_003 — čisti test dvostepenog pipeline-a

**Init faza:** `run_pivot_init.py` — 160/160 prevoda, 1 min 51 sec.
**Pivot faza:** `run_pivot.py` — konvergiralo u iteraciji 9, ~8 min 47 sec.

---

## Korak 5 — Analiza rezultata pivot_003

| Lang | 🟢 | 🟡 | 🔴 | avg_score | min | max |
|------|----|----|-----|-----------|-----|-----|
| FR | 22 | 13 | 5 | 0.8906 | 0.6350 | 0.9994 |
| HR | 17 | 17 | 6 | 0.8783 | 0.7330 | 0.9960 |
| IT | 17 | 16 | 7 | 0.8728 | 0.7162 | 0.9872 |
| DE | 18 | 14 | 8 | 0.8672 | 0.5976 | 0.9986 |

### Usporedba s test_018 (isti jezici)

| Lang | pivot_003 🟢 | test_018 🟢 | pivot_003 🔴 | test_018 🔴 |
|------|------------|-----------|------------|-----------|
| FR | 22 | 29 | 5 | 1 |
| HR | 17 | 23 | 6 | 0 |
| IT | 17 | 24 | 7 | 3 |
| DE | 18 | 26 | 8 | 5 |

**Kontekst:** test_018 koristi 6 metoda + 3 faze + višestruke GA runde. pivot_003 koristi samo gemma3:12b, temp=0.3 — minimalna konfiguracija. Pivot strategija s više modela i temperatura vjerovatno bi se primaknula test_018 rezultatima.

---

## Naučene lekcije

- **Dvostepeni pipeline je bolji** — preglednost, init prevodi su trajni, pivot se može ponavljati
- **Grupisanje po pivot jeziku** je ispravna batch optimizacija — jedna rečenica uvijek ima tačno jedan pivot (max score), grupisanje je samo efikasnost
- **`sed -i` opasno za YAML** — iz session_19 pouka: uvijek koristiti Python + yaml parser za izmjene registry fajlova (ovdje smo koristili `cat >>` append i `cat >` za cijeli fajl)
- **Pivot strategija radi** — FR dominira kao pivot jezik (najviše rečenica s max scoreom), poboljšanja se dešavaju kroz više iteracija

---

## Otvoreno za sljedeću sesiju

1. **Pivot s više modela/temperatura** — testirati pivot_001 konfiguraciju (2 modela, 2 temperature) da vidimo koliko se primaknemo test_018
2. **Usporedba pivot vs GA** — koja strategija daje bolje rezultate za iste resurse?
3. **README update** — dodati pivot pipeline dokumentaciju
4. **GA za RO, ES, BS, SR, SL, MK** — iz test_018, još nisu pokrenuti

---

## Handoff blok

- **Novi fajlovi:** `src/step_create_pivot_table.py`, `src/run_pivot_init.py`, `src/run_pivot.py`, `tests/pivot_registry.yaml`
- **Nova tabela:** `pivot_results` u bazi
- **pivot_registry.yaml:** pivot_001, pivot_002, pivot_003
- **Baza:** pivot_results sadrži podatke za pivot_001, pivot_002, pivot_003
- **Zadnji commit:** session_20 — session_21 treba pushati

---

*Flavio & Claude · Session 21 · 25. maj 2026.*
