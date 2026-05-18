# Session 10 — Buchenberg

**Datum:** 18. maj 2026.  
**Učesnici:** Flavio & Claude

---

## Cilj sesije

Priprema za GA run na test_012 — provjera stanja baze, infrastrukture i koda prije pokretanja `run30.sh`. Otkriveni i dokumentovani kritični bugovi.

---

## Korak 1 — Inicijalizacija sesije (protokol)

Sesija je počela čitanjem tri ključna dokumenta:

1. `buchenberg_napomena.md` — napomena iz prethodne nedjelje
2. README.md — kanonska dokumentacija projekta
3. Session dokumenti 07, 08, 09 — detalji prethodnih sesija

**Osvježena memorija** u Claude memory sistemu: dodan entry o test_012 stanju i sljedećim koracima.

**Lekcija:** Trostepeni protokol inicijalizacije (memorija → napomena → session dokumenti) radi odlično — od nule do pune operativnosti za manje od 5 minuta.

---

## Korak 2 — Greška: pogrešna pretpostavka o docker exec

Claude je inicijalno predložio:
```bash
docker exec pgdb psql -U pgu -d buchenberg -c "..."
```

**Problem:** Ova komanda radi samo ako si fizički na balsam serveru. Sa foxuno se bazi pristupa isključivo kroz **psycopg2** (network konekcija na `balsam.dynu.net:5432`).

**Lekcija:** README jasno kaže da se `docker exec` izvršava ručno na balsam serveru. Claude ima `balsam:run_command` MCP tool ali i `foxuno:run_command`. Pravi pristup bazi sa foxuno je uvijek psycopg2, ne docker exec.

**Fix:** Minimalni test konekcije kroz Python:
```python
import psycopg2
conn = psycopg2.connect(
    host='balsam.dynu.net', port=5432,
    dbname='buchenberg', user='pgu', password='Pgu1234.1234'
)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM test_results WHERE test_id = %s', ('test_012',))
print('Redova u test_012:', cur.fetchone()[0])
conn.close()
```
Rezultat: **660 redova** — konekcija radi.

---

## Korak 3 — Stanje test_012 u bazi

### Provjera ispravnosti upita

Ključna distinkcija (potvrđena):
- **Red** = jedan prevod jedne rečenice jednom metodom za jedan jezik
- **Rečenica** = entitet čija boja = MAX(translation_score) svih redova za tu kombinaciju (sentence_id, target_lang, test_id)

Upit grupira po `(test_id, sentence_id, target_lang)` i uzima MAX — `book_id` ne treba u GROUP BY jer je `sentence_id` globalno jedinstven.

Provjera: svaki jezik = tačno 40 rečenica ✅

### Rezultati

| Jezik | 🟢 Zelene | 🟡 Žute | 🔴 Crvene |
|-------|-----------|---------|-----------|
| BG | 11 | 21 | 8 |
| DE | 19 | 12 | 9 |
| HR | 18 | 15 | 7 |
| IT | 15 | 17 | 8 |
| NL | 20 | 16 | 4 |
| PT | 15 | 20 | 5 |
| **Ukupno** | **98** | **101** | **41** |

GA ima **142 rečenice** (žute + crvene) × 6 jezika da obradi.

### Napomena o razlici od session_09

Session_09 napomena bilježila je drugačije brojeve. Trenutni brojevi su stvarno stanje baze i njima vjerujemo.

---

## Korak 4 — Kritični bug u run_ga.py: nedostaje test_id filter

### Opis buga

Funkcija `inicijalizacija()` u `run_ga.py` uzima inicijalne individue iz `test_results` **bez filtera po test_id**:

```python
cur.execute("""
    SELECT translated_text, method, translation_score
    FROM test_results
    WHERE sentence_id = (
        SELECT id FROM sentences WHERE text = %s LIMIT 1
    ) AND target_lang = %s
    ORDER BY translation_score DESC NULLS LAST
""", (original, lang))
```

### Zašto je ovo problem

Svaki test je **nezavisna cjelina**. GA za test_012 ne smije koristiti prevode iz test_001, test_006 ili bilo kojeg drugog testa kao inicijalne individue. Bez `WHERE test_id = 'test_012'` GA može:
- Uzeti inicijalne individue iz potpuno drugog eksperimenta
- Kontaminirati rezultate test_012 podacima iz starijih testova
- Onemogućiti reproducibilnost rezultata

### Fix (za sljedeću sesiju)

Dodati `--test_id` parametar u `run_ga.py` i proslijediti ga u `inicijalizacija()`:

```python
# argparse
parser.add_argument("--test_id", type=str, required=True)

# inicijalizacija() — dodati test_id filter
cur.execute("""
    SELECT translated_text, method, translation_score
    FROM test_results
    WHERE sentence_id = (
        SELECT id FROM sentences WHERE text = %s LIMIT 1
    ) AND target_lang = %s
    AND test_id = %s
    ORDER BY translation_score DESC NULLS LAST
""", (original, lang, test_id))
```

Isti fix treba primijeniti na **sve** SQL upite u `run_ga.py` koji čitaju iz `test_results`.

### Napomena o ga_results

Provjeriti da li `ga_results` tabela ima `test_id` kolonu — ako nema, dodati je da GA rezultati budu vezani za konkretan test.

---

## Konceptualne diskusije

### Protokol pristupa bazi

| Lokacija | Metoda pristupa | Napomena |
|----------|----------------|---------|
| foxuno | psycopg2 → `balsam.dynu.net:5432` | Jedini ispravan način |
| balsam | `docker exec pgdb psql` | Ručno, direktno na serveru |
| Claude MCP | `foxuno:run_command` + Python/psycopg2 | Claude koristi ovo |

### Terminologija — rečenica vs red

Uvijek koristiti preciznu terminologiju:
- **Rečenica** — entitet iz `sentences` tabele, ima `id`, `text`, `book_id`
- **Red** — jedan prevod u `test_results`, ima `sentence_id`, `target_lang`, `method`, `test_id`
- **Boja rečenice** — izvedena vrijednost: MAX(translation_score) GROUP BY (test_id, sentence_id, target_lang)

### Inicijalizacija sesije kao arhitektura

Trostepeni protokol (memorija → napomena → session dokumenti) je dokazano efikasan. Preporuka: dodati kratki "handoff blok" na kraju svake sesije koji opisuje tačno stanje koda.

---

## Izmjene fajlova u ovoj sesiji

| Fajl | Izmjena |
|------|---------|
| `docs/sessions/session_10.md` | Ovaj dokument |

**Nije mijenjano:** `run_ga.py` — bug dokumentovan, fix za sljedeću sesiju.

---

## Otvoreno za sljedeću sesiju

1. **Fix run_ga.py** — dodati `--test_id` parametar, filtrirati inicijalne individue i sve SQL upite po test_id; provjeriti ga_results tabelu
2. **GA za žute+crvene test_012** — pokrenuti `run30.sh` po jeziku (početi sa `it`)
3. **GA pobjednici kao `method = 'ga'`** — upisati u test_results
4. **Novi jezici** — bs, sl, mk, af, es, ro
5. **Pipeline orchestrator** — finalni prevod iz test_results
6. **multilingual-e5-large** — testirati kao alternativu MiniLM

---

## Handoff blok

- **Zadnja mijenjana skripta:** `run_ga.py` — nije mijenjana, bug samo dokumentovan
- **Zadnji test:** test_012 završen (faza 1+2+3), stanje u bazi provjereno
- **Kritično:** `run_ga.py` ima bug — ne smije se pokretati dok se ne doda `--test_id` filter
- **Stanje baze:** 660 redova u test_012, konekcija radi

---

*Flavio & Claude · Session 10 · 18. maj 2026.*
