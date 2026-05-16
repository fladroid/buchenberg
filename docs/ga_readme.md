# Buchenberg — Genetski Algoritam za Optimizaciju Prevoda

**Datum nastanka ideje:** 16. maj 2026. (Session 06)  
**Status:** Dizajn završen — implementacija planirana

---

## 1. Motivacija i filozofija

Centralni cilj projekta Buchenberg je kvalitetan prevod knjiga sa Project Gutenberg na više jezika, koristeći isključivo open source i besplatne alate. Pipeline već koristi dvije metode prevoda (NLLB i Gemma) i mjeri kvalitet putem LaBSE cosine similarity.

Prirodno pitanje koje se nameće: **može li se kvalitet prevoda poboljšati bez fine-tuninga ili razvoja novog NMT modela?**

Odgovor je — da. Ideja je inspirirana genetskim algoritmima i kombinatoričkom optimizacijom (analogno ruksak problemu): umjesto da biramo jedan prevod, **evoluiramo populaciju prevoda** dok ne dobijemo optimalni rezultat.

Ključna prednost: pipeline koji gradimo je generički. GA nije specifičan za prevod knjiga — primenljiv je na bilo koji NLP zadatak gdje postoji:
- Više kandidatnih rješenja (prevoda)
- Jasna fitness funkcija (LaBSE cosine)
- Mehanizam generisanja novih kandidata (pivot prevod)

---

## 2. Konceptualni okvir

### Populacija

Svaka rečenica RE (na engleskom) ima populaciju prevoda na ciljni jezik L:

```
RE: "Mr. Sherlock Holmes was very late in the mornings."

Populacija (IT):
  individua_1: "Il signor Sherlock Holmes era molto tardi la mattina."  [nllb,     fitness=0.917]
  individua_2: "Sherlock Holmes era solito alzarsi molto tardi."        [gemma,    fitness=0.923]
  individua_3: "Il signor Holmes, di solito molto tardi la mattina..."  [nllb_t05, fitness=0.899]
  individua_4: "Sherlock Holmes si alzava sempre molto tardi."          [gemma_t05,fitness=0.882]
```

### Fitness funkcija

```
fitness(individua) = LaBSE_cosine(RE, individua.tekst)
```

LaBSE je multilingualni embedding model (109 jezika, 768 dimenzija) koji stavlja semantički ekvivalentne rečenice u različitim jezicima na isto mjesto u vektorskom prostoru. Rezultat je broj između 0 i 1 — viši znači semantički bliži originalu.

### Pivot crossover — srž algoritma

Crossover operator koristi **treći jezik kao most** između originala i ciljnog prevoda:

```
RE (EN) → pivot jezik (npr. MK) → ciljni jezik (IT)
```

Svaki jezik "vidi" originalnu misao kroz drugačiju morfološku i sintaktičku prizmu. Makedonski će drugačije strukturirati rečenicu nego italijanski — kad se to prevede u IT, dobijamo IT rečenicu sa "makedonskom perspektivom" koja može uhvatiti nijanse koje direktan EN→IT prevod propusti.

Sa 10 dostupnih pivot jezika i 2 metode prevoda, svaki crossover korak ima **20 mogućih kombinacija** — bogata raznolikost kandidata.

### Mutacija

Mutacija je isti mehanizam kao crossover, ali **polazi od postojećeg individue** umjesto od originala RE:

```
individua.tekst (IT) → nasumični pivot → IT (novi individua)
```

Ovo unosi varijaciju u već dobra rješenja, sprječavajući zaglavljivanje u lokalnom optimumu.

---

## 3. Algoritam — korak po korak

### Konstante

| Parametar | Vrijednost | Obrazloženje |
|-----------|-----------|--------------|
| `POP_SIZE` | 8 | Maksimalna veličina populacije |
| `ELITE_N` | 2 | Uvijek preživljava N najboljih |
| `MAX_GEN` | 20 | Maksimalan broj generacija |
| `CONV_THRESH` | 0.005 | Prag konvergencije fitnesса |
| `CONV_GENS` | 3 | Generacija bez poboljšanja → stop |
| `QUALITY_STOP` | 0.95 | Fitness > ovo → stop |
| `MUTATE_RATE` | 0.15 | 15% šansa mutacije po individui |
| `DUP_THRESH` | 0.99 | Cosine > ovo → duplikat, odbaci |

### Pseudokod

```
# ═══════════════════════════════════════════════════════
# BUCHENBERG GENETIC ALGORITHM
# Cilj: optimizirati prevod jedne rečenice RE na jezik L
# ═══════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────
# KORAK 1 — INICIJALIZACIJA POPULACIJE
# ───────────────────────────────────────────────────────

funkcija INICIJALIZACIJA(RE, L):
  populacija = []

  za svaku metodu u [nllb, nllb_t05, gemma, gemma_t05]:
    RF = prevedi(RE, EN → L, metoda)
    fitness = LaBSE_cosine(RE, RF)
    dodaj {tekst: RF, fitness: fitness, metoda: metoda} u populacija

  sortiraj populacija po fitness DESC
  vrati populacija


# ───────────────────────────────────────────────────────
# KORAK 2 — FITNESS
# ───────────────────────────────────────────────────────

funkcija FITNESS(RE, RF):
  vrati LaBSE_cosine(RE, RF)
  # RE = originalna EN rečenica
  # RF = kandidat prevod na jezik L
  # Rezultat: 0.0 – 1.0, viši = bolji


# ───────────────────────────────────────────────────────
# KORAK 3 — CROSSOVER (pivot jezik)
# ───────────────────────────────────────────────────────

funkcija CROSSOVER(RE, L, dostupni_jezici):
  # Odaberi nasumični pivot jezik (ne EN, ne L)
  pivot = nasumično iz (dostupni_jezici - {EN, L})

  # Uzmi postojeći prevod na pivot jeziku (iz baze ako postoji)
  RF_pivot = dohvati_prevod(RE, pivot)

  # Ako ne postoji — generiši ga
  ako RF_pivot ne postoji:
    metoda = nasumično iz [nllb, gemma]
    RF_pivot = prevedi(RE, EN → pivot, metoda)

  # Crossover korak: pivot → ciljni jezik
  metoda = nasumično iz [nllb, gemma]
  RF_novi = prevedi(RF_pivot, pivot → L, metoda)

  fitness = LaBSE_cosine(RE, RF_novi)
  vrati {tekst: RF_novi, fitness: fitness, pivot: pivot, metoda: metoda}


# ───────────────────────────────────────────────────────
# KORAK 4 — MUTACIJA
# ───────────────────────────────────────────────────────

funkcija MUTACIJA(individua, RE, L, dostupni_jezici):
  # Polazi od teksta individue, ne od RE
  pivot = nasumično iz (dostupni_jezici - {EN, L})

  # individua.tekst (L) → pivot
  RF_pivot = prevedi(individua.tekst, L → pivot, nasumična_metoda)

  # pivot → L (mutirani individua)
  RF_mutirani = prevedi(RF_pivot, pivot → L, nasumična_metoda)

  fitness = LaBSE_cosine(RE, RF_mutirani)
  vrati {tekst: RF_mutirani, fitness: fitness}


# ───────────────────────────────────────────────────────
# KORAK 5 — SELEKCIJA (elitizam + raznolikost)
# ───────────────────────────────────────────────────────

funkcija SELEKCIJA(populacija, novi_kandidati):
  svi = populacija + novi_kandidati

  # Ukloni duplikate (cosine > DUP_THRESH)
  filtrirani = []
  za svakog kandidata u svi (sortirano po fitness DESC):
    je_duplikat = False
    za svakog vec_odabranog u filtrirani:
      ako LaBSE_cosine(kandidat.tekst, vec_odabrani.tekst) > DUP_THRESH:
        je_duplikat = True
        prekini
    ako nije je_duplikat:
      dodaj kandidata u filtrirani

  # Elita — uvijek preživljava
  nova_pop = filtrirani[:ELITE_N]

  # Popuni do POP_SIZE po raznolikosti
  preostali = filtrirani[ELITE_N:]
  dok len(nova_pop) < POP_SIZE i preostali nije prazan:
    najbolji_raznolik = max(preostali,
                            po: min_cosine_prema_vec_odabranim(nova_pop))
    dodaj u nova_pop
    ukloni iz preostali

  vrati nova_pop


# ───────────────────────────────────────────────────────
# KORAK 6 — KRITERIJ ZAUSTAVLJANJA
# ───────────────────────────────────────────────────────

funkcija STOP(historija_fitness, trenutni_best):

  # Uvjet 1 — kvalitet dostignut
  ako trenutni_best.fitness > QUALITY_STOP:
    vrati True, "kvalitet dostignut"

  # Uvjet 2 — konvergencija (nema poboljšanja)
  ako len(historija_fitness) >= CONV_GENS:
    zadnji_N = historija_fitness[-CONV_GENS:]
    ako max(zadnji_N) - min(zadnji_N) < CONV_THRESH:
      vrati True, "konvergencija"

  vrati False, ""


# ───────────────────────────────────────────────────────
# GLAVNI LOOP
# ───────────────────────────────────────────────────────

funkcija GA_OPTIMIZACIJA(RE, L, dostupni_jezici):

  populacija = INICIJALIZACIJA(RE, L)
  historija_fitness = [populacija[0].fitness]

  za gen = 1 do MAX_GEN:
    novi_kandidati = []

    # Crossover
    za i = 1 do (POP_SIZE / 2):
      kandidat = CROSSOVER(RE, L, dostupni_jezici)
      dodaj u novi_kandidati

    # Mutacija
    za svakog individuu u populacija:
      ako nasumično() < MUTATE_RATE:
        mutirani = MUTACIJA(individua, RE, L, dostupni_jezici)
        dodaj mutirani u novi_kandidati

    # Selekcija
    populacija = SELEKCIJA(populacija, novi_kandidati)

    trenutni_best = populacija[0]
    dodaj trenutni_best.fitness u historija_fitness

    logiraj(f"Gen {gen}: best={trenutni_best.fitness:.4f} | {trenutni_best.tekst[:60]}")

    stop, razlog = STOP(historija_fitness, trenutni_best)
    ako stop:
      logiraj(f"Stop: {razlog} nakon {gen} generacija")
      prekini

  vrati populacija[0]


# ───────────────────────────────────────────────────────
# POKRETANJE
# ───────────────────────────────────────────────────────

RE = "Mr. Sherlock Holmes, who was usually very late in the mornings..."
L  = "it"
dostupni_jezici = [hr, sr, de, nl, fr, bs, sl, mk, bg, af]

rezultat = GA_OPTIMIZACIJA(RE, L, dostupni_jezici)
print(f"Optimalni prevod: {rezultat.tekst}")
print(f"Fitness: {rezultat.fitness:.4f}")
```

---

## 4. Integracija sa postojećim pipelineom

### Što GA koristi iz postojećeg sistema

| Komponenta | Uloga u GA |
|-----------|-----------|
| `test_results` tabela | Izvor inicijalne populacije i postojećih pivot prevoda |
| `translate_nllb()` | Crossover i mutacija operator |
| `translate_gemma()` | Crossover i mutacija operator |
| `compute_score()` sa LaBSE | Fitness funkcija |
| `LANG_MAP` | Mapiranje pivot jezičnih kodova |

### Nova tabela — `ga_results`

```sql
CREATE TABLE ga_results (
    id            SERIAL PRIMARY KEY,
    sentence_id   INTEGER REFERENCES sentences(id),
    target_lang   CHAR(2) NOT NULL,
    generation    INTEGER NOT NULL,
    individua_id  INTEGER NOT NULL,
    tekst         TEXT NOT NULL,
    fitness       REAL NOT NULL,
    pivot_lang    CHAR(2),
    metoda        VARCHAR(20),
    je_elita      BOOLEAN DEFAULT FALSE,
    je_pobjednik  BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT NOW()
);
```

### Nova skripta — `src/run_ga.py`

Analogna `run_test.py` — orchestrira GA za jednu ili više rečenica.

---

## 5. Očekivanja i otvorena pitanja

### Što očekujemo

- GA će konvergirati — potvrđeno intuicijom i analogijom s numeričkim GA
- Pivot jezici iz različitih porodica (slavenski, germanski, romanski) će davati različitije potomke
- Broj generacija do konvergencije: procjena 5-15 za većinu rečenica

### Otvorena pitanja

1. **Adaptivna stopa mutacije** — smanjivati kroz generacije (npr. 20% → 5%)?
2. **Veličina populacije** — POP_SIZE=8 dovoljno ili premalo za kratke rečenice?
3. **Pivot selekcija** — nasumična ili weighted (preferirati jezike koji su dali dobre rezultate)?
4. **Multi-jezik GA** — optimizirati prevod na više jezika simultano ili serijski?
5. **Konvergencija vs. oscilacija** — treba empirijski potvrditi na testnim rečenicama

---

## 6. Plan implementacije

1. `src/step7_create_ga_table.py` — kreiranje `ga_results` tabele
2. `src/run_ga.py` — glavni GA runner
3. `run30.sh` — orchestrator (analogno `run20.sh`)
4. Testiranje na 5-10 rečenica iz Hound of the Baskervilles
5. Analiza konvergencije i poređenje s najboljim `test_results` scoreom

---

*Buchenberg · GA dizajn · Session 06 · 16. maj 2026.*
*Ideja: Flavio · Pseudokod i arhitektura: Flavio & Claude*
