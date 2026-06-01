# Session 35 — NLLB u bb pipeline-u

**Datum:** 1. jun 2026.
**Učesnici:** Flavio & Claude
**Nastavlja:** Session 34 (bb pipeline, back to the root)

---

## Kontekst

Sesija je počela osvježavanjem memorije. Claude nije pročitao project files na početku — propust koji je Flavio ispravno uočio i korigovao. Analiza propusta: utabani put (automatski protokol README → sessions) bez X-Ray provjere cijelog konteksta.

---

## Što je urađeno

### 1. Provjera stanja infrastrukture

- README V2 pročitan (poslednje ažuriranje: 30. maj 2026, sesija 32)
- Session dokumenti pročitani: session_32, session_33, session_34
- `health_check.py` pokrenut — sve zeleno ✅
- Aktuelno stanje: bb pipeline operativan, stara baza `buchenberg` netaknuta

### 2. NLLB podrška u `bb_03_prevod.py`

Originalna skripta podržavala je samo Ollama Cloud modele. Dodana je NLLB podrška direktno u postojeću skriptu (ne nova skripta — čišće rješenje).

**Ključne izmjene:**

| Komponenta | Opis |
|------------|------|
| `NLLB_MODEL_NAME` | `facebook/nllb-200-distilled-600M` |
| `NLLB_LANG_MAP` | ISO 639-1 → NLLB BCP-47/FLORES-200 kodovi (14 jezika) |
| `load_nllb()` | Učitava tokenizer i model jednom, prije petlje po jezicima |
| `nllb_batch()` | Batch prevod, beam search, `repetition_penalty=1.3` |
| `nllb_single()` | Wrapper oko `nllb_batch()` za jedan tekst |
| `is_nllb` flag | Branch u `main()` — ako `--model nllb-600M`, koristi NLLB engine, inače Ollama |
| `--temp` | Sada opcionalan (default=0.0), nije potreban za NLLB |

**Važne odluke:**
- NLLB uvijek koristi beam search (`do_sample=False`) — temperatura nema smisla za specijalizirani MT model
- NLLB nema batch fallback (za razliku od Ollame) jer `tokenizer(texts, padding=True)` je inherentno robustan
- Provjera `OLLAMA_BASE_URL` umjesto `OLLAMA_URL` — usklađeno s `.env` fajlom

### 3. Prvi NLLB run u bb pipeline-u

```bash
venv/bin/python src/bb_03_prevod.py \
  --knjiga 1 --od 1 --do 40 \
  --model "nllb-600M" \
  --embedder "paraphrase-multilingual-MiniLM-L12-v2" \
  --jezici hr fr it
```

**Rezultati:**

| Jezik | avg_score | n |
|-------|-----------|---|
| 🇮🇹 IT | 0.8926 | 40 |
| 🇫🇷 FR | 0.8803 | 40 |
| 🇭🇷 HR | 0.8624 | 40 |

**Trajanje:** 3 minute 56 sekundi za 3 jezika × 40 rečenica (CPU, lokalni model).

**Primjer prevoda (s1, s2):**

| Jezik | s1 | s2 |
|-------|----|----|
| FR | Le chien des Baskervilles. | par Sir Arthur Conan Doyle . |
| HR | Pas Baskervilsa. | Sir Arthur Conan Doyle. |
| IT | Il cane dei Baskerville. | di Sir Arthur Conan Doyle. |

### 4. Analiza temperature kod NLLB

Flavio je zatražio objašnjenje utjecaja temperature na NLLB rezultate. Zaključci:

- NLLB je treniran i optimiziran za beam search — to je njegov prirodni način rada
- Sampling s temperaturom tehnički radi ali donosi malo raznolikosti u odnosu na LLM-ove — NLLB je specijalizirani MT model bez "kreativnog" prostora
- Literatura potvrđuje: kombiniranje više sampling kandidata (QE-fusion) može poboljšati kvalitet, ali zahtijeva dodatni QE model — za bb pipeline beam search je optimalan
- Empirijski potvrđeno i u starom pipeline-u: `nllb_t05` rijetko pobjeđivao `nllb`

---

## Ključni uvidi

- **bb_03_prevod.py je sada generički** — jedan ulazni punkt za sve modele (Ollama + NLLB), razlika samo u `--model` argumentu
- **NLLB performanse u bb kontekstu** — avg 0.86–0.89, usporedivo s Gemma3/Ministral iz session_34 (0.86–0.91), ali lokalno i bez API troškova
- **Temperatura za NLLB = 0** je ispravan i jedini smisleni izbor za beam search MT model

---

## Otvoreno za nastavak sesije / sljedeću sesiju

1. `bb_04_pobjednik.py` — pokrenuti za hr/fr/it NLLB run
2. Usporedba modela — NLLB vs gemma3 vs ministral vs gemma4 za iste jezike i rečenice
3. NLLB run za preostale jezike (de, nl, es, pt, sr, bg, bs, sl, mk, af, ro)
4. e5-large kao embedder — testirati umjesto MiniLM
5. Git commit i push

---

*Flavio & Claude · Buchenberg · Session 35 · 1. jun 2026.*
