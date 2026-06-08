# Session 60

**Datum:** 8. jun 2026.

---

## Urađeno

### Infrastruktura
- Serveri balsam i foxuno rebootirani (rutinski, update/upgrade)
- Potvrđeno: server restart nikad nije uzrok grešaka u skriptama

### Pipeline milestone
- HR prijevod Hounda kompletiran: **3852/3852 pobjednika**
- Web export za HR urađen (Flavio)
- Prva knjiga s kompletnim prijevodom na jedan jezik

### run_pipeline.sh
- Kreiran bash skript koji izvršava kompletan pipeline u jednoj komandi
- Redosljed: 4x Ollama serijski (gemma3:12b@0.8, gemma3:12b@0.1, ministral-3:14b@0.8, ministral-3:14b@0.1) + NLLB → sudija → pobjednik
- Web export namjerno isključen — radi se zasebno za više knjiga/jezika odjednom
- Embedder: **multilingual-e5-large** (ispravka nakon greške u prvoj verziji)
- Log fajl: `logs/pipeline_k{knjiga}_{timestamp}.log`
- Upotreba: `bash run_pipeline.sh --knjiga ID --jezici "lang1 lang2" --od N --do M`
- Za nohup: `nohup time bash run_pipeline.sh ... > logs/ime.log 2>&1 &`

### Čišćenje greške
- Prva verzija skripte imala pogrešan embedder (paraphrase-multilingual-MiniLM-L12-v2)
- Test pokrenut na knjiga=21, hr/sr, 1-20 s pogrešnim embedderom
- 200 redova obrisano iz bb_prevodi_recenica
- Skript ispravljen i ponovo testiran uspješno

---

## Istraživanje: WebLLM i Transformers.js

- WebLLM: open-source JS framework za LLM inferensu u browseru putem WebGPU
- Transformers.js: Hugging Face library za embedding modele u browseru
- EmbeddingGemma (308M, 100+ jezika) dostupna kroz Transformers.js
- Zaključak: realtime pristup moguć ali nije prikladan za prosječne mobilne korisnike
- Plan: statični JSON (bb_web_export.py) ostaje primarni pristup; realtime kao buduća "Experimental" stranica s capability detection

---

## Planiranje: geometry.html

- Nova stranica: **Geometry of Meaning**
- Menu tačka: `Geometry`
- Arhitektura: bb_web_export.py → data/geometry.json → Apache2 statički → browser renderuje
- Sadržaj: matematička teorija embeddings i cosine similarity, Buchenberg rečenice kao primjeri
- Capability detection utility (WebGPU, RAM, CPU jezgre) — zajednički za sve buduće advanced stranice
- "Beta" / "Experimental" badge za WebGPU funkcionalnosti

---

## Greške koje se ne smiju ponoviti

- **Embedder je UVIJEK `multilingual-e5-large`** — nigdje drugdje, ni u skriptama ni u primjerima ni u dokumentaciji

---

## Git

```
05f6ce5 session_60: run_pipeline.sh — kompletan pipeline u jednoj komandi
16b1e40 session_60: fix embedder → multilingual-e5-large
```
