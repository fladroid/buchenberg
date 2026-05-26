# Session 22 — Buchenberg

**Datum:** 26. maj 2026.
**Autor:** Flavio & Claude

---

## Cilj sesije

Testiranje pivot strategije s minimalnom konfiguracijom (2 jezika, 1 model, 1 temperatura) radi razjašnjavanja koncepta. Refaktor pivot pipeline-a — uvođenje `pivot.yaml` kao aktivnog config fajla.

---

## Korak 1 — Inicijalizacija

Pročitani: `buchenberg_napomena.md`, `README.md`, session dokumenti 19/20/21. Health check — sve zeleno. 39 modela na Ollama Cloud.

---

## Korak 2 — pivot_004 dizajn i init faza

Dodat `pivot_004` u `pivot_registry.yaml`:
- `langs: [de, hr]`, `models: [gemma3:12b]`, `temperatures: [0.3]`, 40 rečenica

**Init faza** (`run_pivot_init.py`): 80/80 redova upisano (~2 min).

Potvrđena pretpostavka: 40 rečenica × 2 jezika = **80 redova** u `pivot_results`.

**Baseline (samo init, gemma3:12b):**

| Lang | 🟢 | 🟡 | 🔴 | avg |
|------|----|----|-----|-----|
| DE | 14 | 17 | 9 | 0.8487 |
| HR | 16 | 16 | 8 | 0.8535 |

---

## Korak 3 — pivot_004 pivot faza (gemma3:12b)

Konvergiralo u iteraciji 8 (0 poboljšanja → stop). Ukupno 43 poboljšanja kroz 7 iteracija.

**Statistika iz loga:**
- Iter 1: 14 poboljšanja (DE i HR 50/50 pivot na startu)
- Iter 2: 10, Iter 3: 5, Iter 4: 7, Iter 5: 4, Iter 6: 1, Iter 7: 2, Iter 8: 0 → stop
- DE dominira kao pivot od iter 2 nadalje (24-26 od 40)
- Tvrdi orasi (0 poboljšanja kroz cijeli run): s2, s3, s6, s7, s15, s23, s24, s25, s40

**Nakon gemma pivot:**

| Lang | 🟢 | 🟡 | 🔴 | avg |
|------|----|----|-----|-----|
| DE | 16 | 16 | 8 | 0.8692 |
| HR | 18 | 16 | 6 | 0.8747 |

---

## Korak 4 — Refaktor: pivot.yaml kao aktivni config

**Problem:** `pivot_registry.yaml` akumulira sve testove — `sed` opasan, svaka izmjena modela zahtijeva editovanje fajla s više testova.

**Rješenje:** `tests/pivot.yaml` — flat struktura, uvijek sadrži samo tekući test. `pivot_registry.yaml` ostaje kao arhiva.

**Novi format `pivot.yaml`:**
```yaml
test_id: pivot_004
book: hound_of_the_baskervilles
sent_from: 1
sent_to: 40
langs: [de, hr]
models: [ministral-3:14b]
temperatures: [0.3]
max_iterations: 10
```

**Izmjene u skriptama** (`run_pivot_init.py` i `run_pivot.py`):
- `PIVOT_REGISTRY_PATH` → `PIVOT_PATH` (pokazuje na `pivot.yaml`)
- `load_pivot_registry()` + `get_pivot_test(test_id)` → `load_pivot()` (čita direktno)
- `--test_id` argument uklonjen iz argparse — `test_id` se čita iz yaml

**Ključna lekcija:** Kada mijenjamo model, ne trebamo ponovo pokretati init fazu — pivot faza direktno pokušava poboljšati postojeće rezultate kroz `ON CONFLICT WHERE score > postojeći`.

---

## Korak 5 — Višestruke pivot faze s različitim modelima

Svaki model pokrenut kao pivot faza na istom `pivot_004` — akumulativno poboljšanje:

| Faza | Model | Temp | Iter do conv | DE 🟢 | HR 🟢 | DE 🔴 | HR 🔴 |
|------|-------|------|--------------|-------|-------|-------|-------|
| Init | gemma3:12b | 0.3 | — | 14 | 16 | 9 | 8 |
| Pivot 1 | gemma3:12b | 0.3 | 8 | 16 | 18 | 8 | 6 |
| Pivot 2 | ministral-3:14b | 0.3 | 6 | 18 | 19 | 7 | 5 |
| Pivot 3 | gemma4:31b | 0.3 | 6 | 19 | 20 | 7 | 5 |
| Pivot 4 | gemma4:31b | 0.7 | 1 | 19 | 20 | 7 | 5 |

**Zapažanja:**
- Svaki novi model donosi dodatna poboljšanja čak i kada prethodni konvergira
- gemma4:31b t=0.7 nije donio ništa novo — t=0.3 je već "popio" sve dostupno
- Multi-model pivot pristup je efikasan: svaki model vidi rečenice kroz drugačiju prizmu

**Finalno stanje pivot_004:**

| Lang | 🟢 | 🟡 | 🔴 | avg | min | max |
|------|----|----|-----|-----|-----|-----|
| DE | 19 | 14 | 7 | 0.8787 | 0.7008 | 0.9986 |
| HR | 20 | 15 | 5 | 0.8859 | 0.6966 | 0.9960 |

Ukupno od init: DE +5 zelenih, -2 crvene; HR +4 zelene, -3 crvene.

---

## Naučene lekcije

- **pivot.yaml je bolji dizajn** — jedan aktivni config, nema rizika od sed kolizija, mijenjanje modela = editovanje jednog fajla
- **Pivot faza ≠ Init faza** — kada mijenjamo model, pivot faza je dovoljna; init samo za prvi prevod
- **Multi-model akumulacija radi** — gemma → ministral → gemma4 svaki donosi nešto; redoslijed nije bitan
- **Viša temperatura ne pomaže uvijek** — t=0.7 na već konvergiranom skupu = 0 poboljšanja
- **Tvrdi orasi su persistentni** — iste rečenice (s37, s23, s24...) ostaju problematične kroz sve modele

---

## Otvoreno za sljedeću sesiju

1. **Više jezika u pivot testu** — probati pivot_005 s 4+ jezika da vidimo kako pivot dinamika radi s više opcija
2. **Usporedba pivot vs test_018** — isti jezici, isti broj rečenica, koja strategija daje bolje rezultate
3. **multilingual-e5-large** — testirati kao alternativu MiniLM
4. **README update** — dokumentovati pivot.yaml workflow i multi-model akumulaciju

---

## Handoff blok

- **Novi fajl:** `tests/pivot.yaml` — aktivni pivot config
- **Izmijenjeni fajlovi:** `src/run_pivot_init.py`, `src/run_pivot.py` — bez `--test_id`, čitaju `pivot.yaml`
- **pivot_004:** de+hr, 40 rečenica, 3 modela, finalno DE 19🟢 7🔴, HR 20🟢 5🔴
- **Zadnji commit:** `84d4431` — session_22

---

*Flavio & Claude · Session 22 · 26. maj 2026.*
