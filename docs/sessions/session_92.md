# Session 92 — 22. jun 2026.

**Fokus:** NLLB performance — X-Ray postojećeg puta + istraživanje rješenja, plan za tuning (CTranslate2 int8). Pipeline run u toku (Flavio). Kod/portal nije diran.

## Onboarding
- Project files → README (sadržaj s90, git fbb1474=s91) → posljednje 3 sesije (s89/s90/s91) → health_check.py, sve po protokolu.
- Memorija na ulazu zastarjela za brojeve (s91 snapshot) — usklađeno sa serverom. Potvrda: "server je izvor istine, ne pamćenje".

## Health snapshot (početak s92)
- Korpus: 38.333 rečenice, **444.560 prevoda** (+109.492 od s91), **79.294 pobjednika** (+24.572 od s91). Pipeline jako mleo između sesija.
- Core-4 (de/hr/it/sr) kompletni (prev=pobj): Hound 3852, Dracula 2001, Flatland 1341, Frankenstein 1000, Jekyll 1157, Big Four 1000, Alice 1535. Skoro: Romeo 1500/1200, Moby Dick 1500/1000.
- Ostali jezici (af/bg/bs/es/fr/mk/nl/pt/ro/sl) na 200–400 pobjednika kroz većinu knjiga.
- Infra: PostgreSQL 17.9, Ollama Cloud 35 modela, NLLB keš, venv — sve zeleno.
- Git: buchenberg fbb1474 (s91), buchenweb bd66455 (s90), oba čista.

## Napomena o aktivnom runu
- Flavio je tokom sesije pokrenuo prevod za **3 knjige × 10 jezika (~24h)**. Sistem namjerno opterećen — nije anomalija. Run se prekida prije NLLB tuninga (sljedeća sesija).

## Urađeno — NLLB X-Ray + istraživanje (ništa nije implementirano)
**Dijagnoza (X-Ray `nllb_batch`):** usko grlo je **runtime**, ne model.
- `AutoModelForSeq2SeqLM` = vanilla **FP32** PyTorch, CPU, bez kvantizacije, bez `set_num_threads`.
- Greedy (`do_sample=False`, `num_beams` default 1), `repetition_penalty=1.3`, `max_length=512`.
- NLLB se poziva **dvaput po chunku** (forward en→tgt + back tgt→en) → 2× rada po rečenici.
- `padding=True` bez sortiranja → duga rečenica drži cijeli batch.
- Supstrat: 4 jezgra, 23 GiB RAM (model ~2.4 GB — RAM nije problem), nema GPU.

**Plan (glavna poluga) — CTranslate2 int8:**
- Isti model (`facebook/nllb-200-distilled-600M`), konvertovan u CT2. 2–4× CPU ubrzanje, ~4× manja memorija. CT2 eksplicitno podržava NLLB.
- Konverzija: `ct2-transformers-converter --model facebook/nllb-200-distilled-600M --quantization int8 --output_dir models/nllb-600M-ct2-int8`.
- U kodu: `model.generate` → `Translator.translate_batch`; HF tokenizer ostaje; `forced_bos_token_id` → target-prefix; greedy + `repetition_penalty=1.3` se čuvaju.
- NLLB ide dvaput → ubrzanje se na tom putu praktično udvostručuje.
- X-Ray granica: int8 mijenja numeriku → izlaz *gotovo* identičan, ne bit-for-bit vs postojeći FP32 redovi. Bezopasno (NLLB = 1 od 5 kandidata, sudija+kosinus ocjenjuju). Minimalan drift: `--quantization float32` (i dalje brži od HF).

**Alternativa:** torch dynamic int8 — `quantize_dynamic(model,{nn.Linear},qint8)`, ~1.5–2×, bez nove zavisnosti.
**Besplatno (nula promjene izlaza):** length bucketing — sortirati `todo` po dužini prije batchiranja.
**NE dirati:** dupli back-translation poziv (inherentan scoringu), sam model.

## Lekcije
- X-Ray prije optimizacije — prvo pročitati kako se model poziva, ne optimizovati crnu kutiju.
- Cijena greške niska + izolacija iza flega = eksperiment je imperativ.
- Ne mjeriti performanse pod opterećenjem — benchmark tek kad run stane.

## Stanje na kraju
- BB_VERSION: **s90.1** (portal nije diran — bez bumpa, kao i s91).
- Kod: bez izmjena. README ažuriran: header s92, §9 gross snapshot, §14 NLLB CT2 plan kao primarni korak.
- Memorija: usklađene zastarjele edite (zadnje stanje s66→s92; horizon: NLLB performance kao primarno; web 8→9 stranica).
- Git: commit session_92.md + README (buchenberg); buchenweb bez izmjena.

## Sljedeće (po prioritetu)
1. **NLLB tuning (primarno):** prekinuti runove → CT2 int8 konverzija → `nllb-ct2` put iza flega (FP32 netaknut) → benchmark 100 rečenica FP32 vs int8 (brzina + output drift) → Flaviova odluka.
2. Length bucketing (besplatno, neovisno o motoru).
3. Proširenje prevoda po planu (hr/sr/it/de→s350; mk/bg→s51–100).
4. art.html v1, about.html i18n, learn.html nove igre, bb_web_export refaktor (v_pobjednici), favicon.
5. NLP Relation Extraction (leži od s90 — rasplet detektivskog romana kao ulaz).

---

*Flavio & Claude · Buchenberg · Session 92 · 22. jun 2026.*
