# Session 25 — LLM kritički prompt & NLLB benchmark

**Datum:** 2026-05-27  
**Učesnici:** Flavio & Claude

---

## Cilj sesije

Nastavak istraživanja NLLB-only pivot strategije. Uvođenje novog koraka:
**LLM kritički prompt** — popravak crvenih rečenica pomoću LLM-a koji dobija EN original + loš prevod kao kontekst.

---

## NLLB model benchmark (600M vs 1.3B vs 3.3B)

Svi testovi: sr, hr, sl, 40 rečenica, nllb_t05, 3 init runa.

| Model | HR 🟢🔴 | SL 🟢🔴 | SR 🟢🔴 | RAM | Trajanje/120 prevoda |
|-------|---------|---------|---------|-----|---------------------|
| 600M  | 19 / 3  | 18 / 9  | 15 / 6  | ~5.5GB | ~3 min |
| 1.3B  | 19 / 3  | 19 / 6  | 16 / 9  | ~8.9GB | ~4.5 min |
| 3.3B  | 21 / 2  | 17 / 7  | 13 / 7  | ~15GB  | ~10 min |

**Zaključak:** Nema jasnog pobjednika. 600M je najbrži i konzistentan. 3.3B oscilira više u prvim runovima. Za produkciju — 600M ostaje primarni izbor.

---

## Novi alat: run_init3.sh

Bash skript koji pokreće init fazu 3× serijalno. Log ime se automatski čita iz yaml-a.

```bash
# Pokretanje:
cd /home/balsam/buchenberg && nohup bash run_init3.sh > /dev/null 2>&1 &

# Praćenje:
tail -f logs/{test_id}_init3.log
```

**Pravilo:** Koristiti SAMO sa stohastičkim modelima (`nllb_t05`, LLM temp>0).
Deterministički modeli (`nllb`) daju isti rezultat svaki put — ponavljanje nema smisla.

---

## Novi skript: run_pivot_llm_fix.py

LLM "kritički" popravak crvenih rečenica. Za svaku crvenu rečenicu (score < 0.80) poziva LLM s promptom koji sadrži EN original + postojeći loš prevod.

### Konfiguracija u pivot.yaml

```yaml
llm_models: [gemma3:12b]   # jedan model po runu
```

### Kritični detalj — Ollama Cloud autentifikacija

**OBAVEZNO** — svaki Python skript koji poziva Ollama Cloud mora imati Authorization header:

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY = os.getenv("OLLAMA_API_KEY", "")

def ollama_translate(model, prompt, temperature=0.5):
    resp = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": temperature},
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()
```

**Bez `headers={"Authorization": f"Bearer {OLLAMA_KEY}"}` dobijamo 401 Unauthorized.**

### Dostupni LLM modeli na Ollama Cloud

| Model string | Opis |
|---|---|
| `gemma3:12b` | Google Gemma 3 12B — primarni model projekta |
| `ministral-3:14b` | Mistral 3 14B |
| `gemma4:31b` | Google Gemma 4 31B — dostupan na besplatnom tieru |

**Napomena:** `gemma4:31b-cloud` je staro ime — koristiti `gemma4:31b`.

**Temperatura:** uvijek 0.5 za LLM modele u ovom projektu.

---

## pivot_015 rezultati (sr, hr, sl — 600M, nllb_t05)

### Evolucija kroz sve korake

| Lang | Init×3 🟢🔴 | +gemma3 🔴 | +ministral 🔴 | +gemma4 🔴 | +gemma3×2 🔴 | +ministral×2 🔴 | +gemma4×2 🔴 |
|------|------------|-----------|--------------|-----------|-------------|----------------|-------------|
| HR | 19 / 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| SL | 18 / 9 | 8 | 7 | 5 | 4 | 4 | 4 |
| SR | 15 / 6 | 4 | 3 | 3 | 3 | 3 | 3 |

**Finalno:** HR 19🟢3🔴 | SL 18🟢4🔴 | SR 15🟢3🔴

### LLM efikasnost po modelu

| Model | Run 1 poboljšano | Run 2 poboljšano |
|-------|-----------------|-----------------|
| gemma3:12b | 5/18 | 2/11 |
| ministral-3:14b | 2/15 | 0/10 |
| gemma4:31b | 3/13 | 1/10 |

**Zaključak:** gemma3 najefikasniji. Ministral najslabiji za ove jezike.

---

## Tvrdi orasi (neprobojni za sve modele)

| Rečenica | Problem |
|----------|---------|
| **s37** | Parser fragment — "the stick" bez konteksta. Nijedan model ne može popraviti. |
| **s38** | Parser fragment — "deductions" prevodi se kao matematičko oduzimanje umjesto zaključivanje. |
| **s1** (HR/SR) | "by Sir Arthur Conan Doyle" — autorstvo, MiniLM daje nizak score. |

---

## Kriterij konvergencije (dogovoreno)

Init faza se zaustavlja kada **3 uzastopna runa ne donesu smanjenje crvenih ni u jednom jeziku**.

---

## Na horizontu

1. Pivot faza za pivot_015
2. LLM kritički prompt s pozitivnim primjerom (HR prevod kao kontekst za SR/SL)
3. Sistematična usporedba 600M vs 1.3B na više runova
4. `nllb-200-distilled-1.3B` ostaje downloadovan na foxuno (~5GB)
5. Produkcijski run strategija

---

## Tehnički detalji

- `run_init3.sh` — novi bash skript, čita test_id iz yaml-a
- `run_pivot_llm_fix.py` — novi skript za LLM popravak crvenih
- `run_pivot_init.py` — trenutno na **600M** modelu ✅
- `tests/pivot.yaml` — ostaje na pivot_015 / gemma4:31b

