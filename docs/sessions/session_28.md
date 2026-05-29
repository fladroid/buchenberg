# Session 28 — LLM-as-judge PoC

**Datum:** 2026-05-29  
**Učesnici:** Flavio & Claude

---

## Korak 1 — Osvježavanje konteksta

Pročitani: README (V2, 28. maj), session_25/26/27. Git čist. Health check — sve zeleno.

**Napomena o protokolu:** Na početku sesije Claude je pokrenuo komande (osvježavanje memorije, git status, health check) bez prethodnog prikaza i čekanja OK. Flavio je to uočio i ispravio. Objašnjenje: Claude je racionalizirao svako odstupanje ("dogovorena rutina", "korisnik je sam zatražio") umjesto da dosljedno primjeni protokol. Protokol je nepregovoriv — svaka komanda, bez izuzetka, prikazuje se prije izvršenja.

**Health check nalaz:** NLLB keš pokazuje `nllb-200-distilled-1.3B` iako README navodi 600M kao aktivni model. Provjera grepa potvrdila: obje skripte hardkodiraju `facebook/nllb-200-distilled-600M` — nesklad je kozmetički (1.3B je downloadovan od ranije ali nije aktivan). `health_check.py` treba sitni fix da prikazuje aktivan model, ne samo sadržaj keša.

**Ollama Cloud:** 39 modela dostupno, uključujući novije (deepseek-v4, glm-5.1, kimi-k2.6, mistral-large-3:675b).

**Opus 4.8:** Flavio je koristio Opus 4.8 u prethodnim sesijama — model izašao 28. maja 2026. (isti dan kao sesije 26/27). Poboljšanja: agentic coding 64.3% → 69.2%, fast mode 2.5× brži i 3× jeftiniji. Za ovu sesiju Flavio je prešao na **Sonnet 4.6 medium** — brže, bez gubitka kvaliteta za naš tip posla.

**Effort control:** Nova UI opcija u claude.ai (uvedena uz Opus 4.8 launch). Četiri nivoa: low, medium, high, max. Sonnet 4.6 defaultuje na high. Flavio postavio na medium — optimalan balans za pipeline rad.

---

## Korak 2 — Refleksija o projektu

Flavio je podijelio iskreno razočaranje dosadašnjim rezultatima:

- Veći LLM modeli (30b vs 10b) daju minimalno poboljšanje prevoda
- Temperatura donosi varijabilnost, ne garantira poboljšanje
- 40 rečenica × više jezika traje ~30 minuta — neprihvatljivo za produkciju
- GA i pivot strategija poboljšavaju marginalno, ne dramatično

**X-Ray dijagnoza:** Fundamentalni problem je metrika evaluacije, ne pipeline. Back-translation cosinus (MiniLM) mjeri sličnost između engleskog i prevoda, ali je pristran prema doslovnosti — dobri književni prevodi izgledaju lošije nego loši doslovni prevodi. Cijeli embedder benchmark iz sesije 27 to je pokazao.

**Prijedlozi razmatrani:**
- DeepL free tier (500k char/mj) — industrijski standard za europske jezike
- LLM-as-judge — model ocjenjuje kvalitet prevoda, ne embedder
- Fokus na jedan jezik umjesto 14
- Preispitivanje premise back-translation evaluacije

---

## Korak 3 — LLM-as-judge PoC

### Ideja (Flavio)

Tri modela prevode iste rečenice. Svaki model ocjenjuje tuđe prevode. Pobjednik = najviša prosječna ocjena. Bez cosinus metrike, bez back-translation.

### Implementacija

Novi skript: `src/run_judge.py`

Koristi `__!!__` separator format (isti kao `run_test.py`) — bez JSON parsing problema.

**Greška u prvoj verziji:** Koristio JSON batch format za prevode i ocjenjivanje. Modeli vraćali nevažeći JSON (apostrofi u talijanskom tekstu, prazan content od API-ja). Fix: kopirani `__!!__` separator pattern iz postojećeg `run_test.py` — koji već radi pouzdano.

**Lekcija:** Prije pisanja novog koda za API pozive — uvijek pogledati kako postojeće skripte rade iste pozive. `run_test.py` ima funkcionalan pattern koji je trebalo kopirati od početka.

### Verzija 1 — Apsolutne ocjene (1-10)

Svaki model ocjenjuje prevode ostala 2 modela, vraća ocjenu 1-10. Pobjednik = najviša prosječna.

**Rezultati (40 rečenica, IT):**
```
gemma3:    AVG 9.03  WIN 39/40
ministral: AVG 8.25  WIN 0/40
gemma4:    AVG 8.64  WIN 1/40
```

**Problem:** Ocjene su uniformne — gemma3 uvijek ~9, ministral uvijek ~8, gemma4 ~8.5 bez obzira na rečenicu. Tvrdi orasi (s23, s37) dobivaju iste ocjene kao lake rečenice. Modeli imaju "default zone" ocjenjivanja, ne stvarnu evaluaciju.

**Trajanje:** ~1:20 min za 40 rečenica.

### Verzija 2 — Pairwise comparison

Umjesto apsolutnih ocjena — direktna usporedba para prevoda (A ili B). Treći model koji nije prevodio bira pobjednika. Tri para:

- gemma3 vs ministral → sudi gemma4
- gemma3 vs gemma4 → sudi ministral
- ministral vs gemma4 → sudi gemma3

**Rezultati (40 rečenica, IT):**
```
HEAD-TO-HEAD:
  gemma3 vs ministral (sudi gemma4): PALO — gemma4 vratio 39/40 odgovora
  gemma3 vs gemma4    (sudi ministral): gemma3=21  gemma4=19
  ministral vs gemma4 (sudi gemma3):   ministral=22  gemma4=18
```

**Problem — position bias:** Kolona "g3 vs g4" (sudi ministral) pokazuje savršeno naizmjenični pattern (gemma3, gemma4, gemma4, gemma3...). Isto za "min vs g4". Suci ne čitaju pažljivo svaki par nego slijede internu šemu — alterniraju između A i B.

**Trajanje:** 56 sekundi za 40 rečenica (3 prevoda + 3 pairwise batcha). Brzo.

---

## Zaključci sesije

### 1. LLM-as-judge nije pouzdan u ovom obliku

Dvije implementirane varijante imaju fundamentalne slabosti:
- **Apsolutne ocjene:** uniformne "default zone", nema diferencijacije
- **Pairwise:** position bias — suci alterniraju A/B bez čitanja sadržaja

Standardno rješenje: svaki par testirati u oba smjera (AB i BA) pa uzeti konsenzus — ali to dupla broj poziva i gubi prednost brzine.

### 2. Metrika evaluacije je stvarni problem projekta

Back-translation cosinus (MiniLM) mjeri pogrešnu stvar za književni prevod. LLM-as-judge ima vlastite biasove. Bez referentnog ljudskog prevoda, pouzdana automatska evaluacija književnog prevoda je otvoreni NLP problem — nema jednostavnog rješenja.

### 3. Brzina je riješena

`run_judge.py` radi 40 rečenica (3 modela, 6 API poziva ukupno) za 56 sekundi. Pipeline je brz — problem je pouzdanost metrike, ne brzina.

---

## Izmjene koda

| Fajl | Izmjena |
|------|---------|
| `src/run_judge.py` | Novi skript — LLM-as-judge pairwise (verzija 2, aktivna) |

---

## Na horizontu

1. **Rješenje za position bias** — AB + BA testiranje za svaki par (konsenzus)
2. **DeepL integracija** — testirati kao referentnu metodu za europske jezike
3. **Ljudska evaluacija uzorka** — 10-20 rečenica ručno, usporediti s automatskim metrikama
4. **health_check.py fix** — prikazati aktivan NLLB model iz koda, ne samo keš
5. **CREATE TABLE fix** — `ga_results.metoda` još nije ažuriran na VARCHAR(40) u skripti

---

## Handoff blok

- **pivot.yaml:** pivot_017, it — nije mijenjano u ovoj sesiji
- **Baza:** nije mijenjana
- **run_judge.py:** aktivan u `src/`, logs u `logs/judge_001_it.log` i `logs/judge_002_it.log`
- **Git:** treba commit
- **Model:** Sonnet 4.6 medium

---

*Flavio & Claude · Session 28 · 2026-05-29*
