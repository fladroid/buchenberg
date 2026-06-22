# Session 93 — 22. jun 2026.

**Fokus:** NLLB performance tuning — implementacija i usvajanje CTranslate2 int8 motora (flag-izolovano, default ct2). Nastavak s92 plana.

## Kontekst / okruženje
- Nastavak nakon s92 (research + plan). Flavio prekinuo sve prevode i restartovao foxuno → čisto okruženje.
- Health check nakon restarta: PG 17.9, Ollama 35 modela, NLLB keš, venv — sve gore. Korpus (s93 start): 452.780 prevoda, 82.494 pobjednika. Git čist d1227e4.
- ⚠️ `transformers import` timeout u health checku = cold-start artefakt (warm import radi za par s). Benigno.

## Supstrat (otkriće)
- **CPU = Neoverse-N1 (ARM/aarch64), 4 jezgra, 23 GiB RAM, bez GPU.** Nema AVX (ARM → NEON). CT2 int8 na ARM koristi Ruy backend, ne MKL/AVX — mijenja kalibraciju očekivanja.

## Urađeno

**1. CTranslate2 + konverzija modela.**
- CT2 4.8.0 (aarch64 wheel, bez source builda). Stack netaknut (torch 2.12.0, transformers 5.8.1, numpy 2.4.4).
- `ct2-transformers-converter --model facebook/nllb-200-distilled-600M --quantization int8 --output_dir models/nllb-600M-ct2-int8` → **594 MB** int8 (4× manje od FP32 ~2.4 GB). `models/` gitignored (regenerabilan).

**2. Benchmark (100 EN rečenica, Hound, en→hr).**
- Prvi pokušaj (intra=4/inter=1): samo **1.39×** — artefakt loše thread konfiguracije, NE strop modela.
- Thread sweep: na ARM s kratkim rečenicama ključ je `inter_threads` (paralelizacija PREKO batcha), ne intra. Optimum **inter=4, intra=1, max_batch=14**.
- Produkcijski oblik (chunked): step=20 → 2.63×; step=56 → 4.19×; step=100 → **6.72×**. Što veći chunk CT2 dobije, to bolje (puni 4 radnika).
- Drift: ~50% izlaza se razlikuje na nivou stringa, ali **kozmetički** (red riječi, sinonimi) — jednak kvalitet. int8 numerika, ne stohastika (greedy, deterministički).

**3. Implementacija — flag-izolovano (bb_03_prevod.py, commit 3403c62).**
- `NLLB_ENGINE` env: `ct2` (default) / `fp32` (fallback). Params: `NLLB_CT2_DIR/BATCH(200)/MAXBATCH(14)/INTER(4)/INTRA(1)`.
- `load_nllb()` grana (CT2 Translator vs HF). `nllb_batch()` grana na `_nllb_batch_ct2()`; **FP32 grana bajt-identična**.
- Caller: za CT2-NLLB korak petlje = `NLLB_CT2_BATCH` (200) da puni 4 radnika; FP32 + Ollama ostaju na BATCH_SIZE=20.
- Verifikacija: py_compile OK; smoke test oba motora (isti izlaz na kratkim rečenicama); env passthrough kroz run_pipeline.sh potvrđen (zove python direktno, bez env -i/sudo/ssh).

**4. Produkcijski test + usvajanje.**
- Flavio pustio kompletan run: `NLLB_ENGINE=ct2 run_pipeline.sh --knjiga 21 --jezici "af nl" --od 401 --do 500`. Utisak: znatno brže — NLLB više nije najsporiji u lancu (prije sporiji i od gemme i ministrala). Usvojeno.
- Test slice zadržan kao validni podaci (CT2 prihvaćen, nema čišćenja).
- Default flipnut na **ct2** → run_pipeline.sh se koristi isto kao prije, automatski brz.

## Lekcije (ledger)
- **Konfiguracija > pretpostavka:** prvi benchmark (1.39×) bio je artefakt thread configa. Na ARM-u s kratkim seq `inter_threads` paralelizuje preko batcha — to je poluga. Istestirati config prije suda o "stropu".
- **Hraniti CT2 velikim chunkom** — produkcijski speedup raste s veličinom chunka (20→100 = 2.6×→6.7×).
- **X-Ray iskrenost:** priznata greška u prvom mjerenju; 6.7× je stvarni rezultat tek nakon thread-sweepa.
- Cold-start import timeout ≠ slomljen paket.

## Stanje na kraju
- BB_VERSION: s90.1 (web nije diran).
- Git buchenberg: **3403c62** (CT2 motor) + session/README (ovaj close). buchenweb: bd66455 (s90), nedirnut.
- NLLB: default CT2 int8, ~6–7× brži; FP32 fallback `NLLB_ENGINE=fp32`. Model `models/nllb-600M-ct2-int8/` (gitignored, regenerabilan jednom komandom).

## Sljedeće (po prioritetu)
1. Length bucketing (besplatno, nula drifta) — opciono, sad manje hitno jer je NLLB brz.
2. Proširenje prevoda po planu (hr/sr/it/de→s350; mk/bg→s51–100) — sad mnogo brže s CT2.
3. art.html v1, about.html i18n, learn.html nove igre, bb_web_export refaktor, favicon.
4. NLP Relation Extraction (leži od s90).

---

*Flavio & Claude · Buchenberg · Session 93 · 22. jun 2026.*
