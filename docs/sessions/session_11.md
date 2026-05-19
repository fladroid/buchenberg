# Session 11 — Buchenberg

**Datum:** 19. maj 2026.  
**Ucesnici:** Flavio & Claude

---

## Cilj sesije

Fix kriticnog buga u `run_ga.py` (nedostajao `--test_id` filter), implementacija `ga_save_winners.py`, prvi GA run za `it` na test_012, i drugi krug GA za `it` sa obogacenom inicijalnom populacijom.

---

## Korak 1 — Inicijalizacija sesije

Procitani: `buchenberg_napomena.md`, `README.md`, session dokumenti 08/09/10.

Provjera infrastrukture:
- OK PostgreSQL — 660 redova u test_012, konekcija radi
- OK Gemma — `gemma3:12b` radi
- OK Ministral — dostupan kao `ministral-3:14b` (ne `mistral-small3.1:24b` kako je pogresno testirano)

Napomena: Claude koristi psycopg2 kroz `foxuno:run_command` za SVE operacije s bazom ukljucujuci DDL. PostgreSQL je dostupan mrezno na `balsam.dynu.net:5432`. Nema potrebe za `docker exec` sa foxuno.

---

## Korak 2 — Fix run_ga.py

### Bug (dokumentovan u session_10)

`inicijalizacija()` uzimala inicijalne individue iz `test_results` BEZ filtera po `test_id` — GA je mogao kontaminirati rezultate podacima iz starijih testova.

### Izmjene

| Funkcija | Izmjena |
|----------|---------|
| `inicijalizacija()` | dodan `AND test_id = %s` |
| `get_existing_translation()` | dodan `AND test_id = %s` |
| Filter zelenih u main loopu | dodan `AND test_id = %s` |
| `clear_ga()` | dodan `test_id` u WHERE |
| `save_individua()` | prima i upisuje `test_id` |
| UPDATE pobjednik | dodan `test_id` u WHERE |
| `--test_id` | novi obavezni argument |
| Log fajl | `{test_id}_ga.log` umjesto `run_ga.log` |
| `logger.add()` | dodan `enqueue=True` |

### ALTER TABLE

```sql
ALTER TABLE ga_results ADD COLUMN test_id VARCHAR(20);
```

Izvrseno kroz psycopg2 sa foxuno.

### Commit

```
83706c0 fix: run_ga.py — dodan --test_id filter, ga_results.test_id kolona
```

---

## Korak 3 — ga_save_winners.py

Nova skripta za upis GA pobjednika iz `ga_results` u `test_results`.

**Logika:**
- Cita pobjednike (`je_pobjednik = TRUE`) iz `ga_results`
- Upisuje u `test_results` sa `method='ga_{pivot_lang}'` (npr. `ga_hr`, `ga_nl`)
- `ON CONFLICT DO UPDATE` — idempotentno
- `score` i `back_translation` = NULL (GA ne racuna back-translation)
- `--only_better` flag — opciono, upisuje samo ako GA > postojeci MAX
- `--lang all` — upisuje sve jezike koji imaju GA pobjednike u testu

**Commit:**
```
dc67e43 feat: ga_save_winners.py — upis GA pobjednika u test_results
```

---

## Korak 4 — GA run 1 za it (test_012)

```bash
nohup time bash run30.sh --test_id test_012 --sent_from 1 --sent_to 40 --lang it \
  > logs/test_012_ga_it.log 2>&1 &
```

**Trajanje:** 20 min 39 sec  
**Rezultat:** 25 optimizacija, 15 preskoceno (zelene)

### Analiza pobjednika

| Metrika | Vrijednost |
|---------|-----------|
| Avg fitness prije | 0.8190 |
| Avg fitness poslije | 0.8648 |
| Poboljsano | 20/25 (80%) |
| Nije poboljsano | 5/25 |

**Metode pobjednika:** crossover dominira (nllb+nllb: 7, gemma+gemma: 5, gemma+nllb: 5). Mutacija pobjedila samo 2x.

**Pivot jezici:** ravnomjerna raspodjela — hr, pt, fr po 3. Nema dominantnog pivota.

**Generacije:** vecina konvergira na gen 2-4.

### Promjena boja recenica

| | Prije | Poslije | Delta |
|--|-------|---------|-------|
| Zelene | 15 | 22 | +7 |
| Zute | 17 | 13 | -4 |
| Crvene | 8 | 5 | -3 |

### Upis GA pobjednika

```bash
venv/bin/python src/ga_save_winners.py --test_id test_012 --lang it
```

Upisano: 25 GA pobjednika u test_results.

---

## Korak 5 — GA run 2 za it (test_012)

Nakon upisa pobjednika u test_results, pokrenut drugi krug:

```bash
nohup time bash run30.sh --test_id test_012 --sent_from 1 --sent_to 40 --lang it \
  > logs/test_012_ga_it_r2.log 2>&1 &
```

**Efekat obogacene inicijalne populacije:**
- s1 sada zelena (0.9275) — preskocena
- s5 u gen 2 podigla sa 0.7661 -> 0.8225 (u runu 1 nije se poboljsala)
- Inicijalna populacija: 5 individua umjesto 4

---

## Konceptualne diskusije

### Odumiranje u GA

Trenutni GA vec implementira odumiranje kroz `pop_size=8` + `selekcija()` — sve ispod 8. mjesta umire odmah. Nije "postupno" odumiranje ali funkcionalno je ekvivalentno.

Pravo postupno odumiranje (penalizacija fitnessa po starosti) ostaje kao ideja za bududi tuning krug — posebno korisno za 5 crvenih recenica koje GA nije mogao probiti.

### Inspiracija projekta

Dokumentovana u `docs/inspiracija.md`:

Flavio je posjetio Universita di Bologna. Pred kilometarskim redom, pridruzio se grupi Japanaca na turi. Improviziran je zivi pivot prevod: italijanski vodic -> njemacki -> japanski. Svi zadovoljni.

Nekoliko godina kasnije — word2vec, i tehnicka implementacija iste ideje: svaki jezik je drugacija prizma kroz koju original prolazi.

```
7abea61 docs: dodana inspiracija — Bologna pivot prevod
```

---

## Izmjene fajlova u ovoj sesiji

| Fajl | Izmjena |
|------|---------|
| `src/run_ga.py` | fix test_id filter, ALTER TABLE ga_results |
| `src/ga_save_winners.py` | nova skripta |
| `docs/inspiracija.md` | novi fajl |
| `docs/sessions/session_11.md` | ovaj dokument |

---

## Otvoreno za sljedecu sesiju

1. **Zavrsiti GA run 2 za it** — provjeriti rezultate, upisati pobjednike
2. **GA za ostale jezike test_012** — hr, bg, de, nl, pt
3. **GA pobjednici -> test_results** za svaki jezik nakon runa
4. **Novi jezici** — bs, sl, mk, af, es, ro
5. **Pipeline orchestrator** — finalni prevod iz test_results
6. **multilingual-e5-large** — testirati kao alternativu MiniLM

---

## Handoff blok

- **Zadnja mijenjana skripta:** `src/ga_save_winners.py` — nova, radi
- **Aktivni proces:** GA run 2 za `it`, PID 212129, log `logs/test_012_ga_it_r2.log`
- **Stanje baze:** test_012 ima 660 + 25 GA redova za `it`
- **ga_results** tabela ima `test_id` kolonu od ove sesije
- **Kriticno:** nakon zavrsretka run 2, pokrenuti `ga_save_winners.py --lang it` ponovo

---

*Flavio & Claude · Session 11 · 19. maj 2026.*
