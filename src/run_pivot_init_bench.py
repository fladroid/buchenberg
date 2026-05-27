#!/usr/bin/env python3
"""
Buchenberg · run_pivot_init_bench.py
Benchmark verzija init skripte — bez upisa u bazu i bez score provjere.
Mjeri čisto vrijeme NLLB inference + scoring za N prevoda.
"""

import os
import sys
import time
import argparse

import yaml
from dotenv import load_dotenv
from loguru import logger
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

PIVOT_PATH = os.path.join(os.getenv("BUCH_HOME", "."), "tests", "pivot.yaml")
NLLB_MODEL  = "facebook/nllb-200-distilled-1.3B"
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE  = 20

LANG_MAP = {
    "sr": "srp_Cyrl", "hr": "hrv_Latn", "bs": "bos_Latn",
    "sl": "slv_Latn", "mk": "mkd_Cyrl", "bg": "bul_Cyrl",
    "de": "deu_Latn", "nl": "nld_Latn", "af": "afr_Latn",
    "fr": "fra_Latn", "it": "ita_Latn", "es": "spa_Latn",
    "pt": "por_Latn", "ro": "ron_Latn", "en": "eng_Latn",
}

def load_pivot():
    with open(PIVOT_PATH, "r") as f:
        return yaml.safe_load(f) or {}

def load_sentences_dummy(sent_from, sent_to):
    # Dummy rečenice bez DB konekcije
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv()
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.text FROM sentences s
        JOIN books b ON s.book_id = b.id
        WHERE b.title ILIKE %s AND s.id BETWEEN %s AND %s
        ORDER BY s.id
    """, ("%hound%", sent_from, sent_to))
    rows = cur.fetchall()
    conn.close()
    return rows

def translate_nllb_batch(texts, tokenizer, model, src_lang="eng_Latn",
                          tgt_lang="srp_Cyrl", temperature=None):
    tokenizer.src_lang = src_lang
    inputs = tokenizer(texts, return_tensors="pt", padding=True,
                       truncation=True, max_length=512)
    gen_kwargs = dict(
        forced_bos_token_id=tokenizer.convert_tokens_to_ids(tgt_lang),
        max_length=512, repetition_penalty=1.3,
    )
    if temperature is not None:
        gen_kwargs["do_sample"]   = True
        gen_kwargs["temperature"] = temperature
    else:
        gen_kwargs["do_sample"] = False
    translated = model.generate(**inputs, **gen_kwargs)
    return tokenizer.batch_decode(translated, skip_special_tokens=True)

def score_batch(originals, translations, embedder):
    enc_orig  = embedder.encode(originals)
    enc_trans = embedder.encode(translations)
    return [float(cosine_similarity([o], [t])[0][0])
            for o, t in zip(enc_orig, enc_trans)]

def main():
    params    = load_pivot()
    sent_from = params["sent_from"]
    sent_to   = params["sent_to"]
    langs     = params["langs"]
    models    = params["models"]

    print(f"Učitavanje rečenica {sent_from}-{sent_to}...")
    sentences = load_sentences_dummy(sent_from, sent_to)
    print(f"Rečenica: {len(sentences)}")

    print(f"Učitavanje NLLB modela: {NLLB_MODEL}")
    nllb_tok = AutoTokenizer.from_pretrained(NLLB_MODEL)
    nllb_mod = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)

    print(f"Učitavanje embeddera: {EMBED_MODEL}")
    embedder = SentenceTransformer(EMBED_MODEL, local_files_only=True)

    total = len(sentences) * len(langs) * len(models)
    done  = 0

    t_translate = 0.0
    t_score     = 0.0

    for lang in langs:
        for model in models:
            nllb_temp = 0.5 if "t05" in model else None
            for batch_start in range(0, len(sentences), BATCH_SIZE):
                batch      = sentences[batch_start:batch_start + BATCH_SIZE]
                batch_txts = [s[1] for s in batch]

                t0 = time.time()
                translations = translate_nllb_batch(
                    batch_txts, nllb_tok, nllb_mod,
                    src_lang="eng_Latn", tgt_lang=LANG_MAP[lang],
                    temperature=nllb_temp
                )
                t_translate += time.time() - t0

                t0 = time.time()
                scores = score_batch(batch_txts, translations, embedder)
                t_score += time.time() - t0

                done += len(batch)
                print(f"  [{done}/{total}] {lang} {model} batch done")

    print(f"\n=== BENCHMARK REZULTATI ===")
    print(f"Ukupno prevoda:       {done}")
    print(f"Translate vrijeme:    {t_translate:.2f} sec")
    print(f"Scoring vrijeme:      {t_score:.2f} sec")
    print(f"Ukupno:               {t_translate + t_score:.2f} sec")
    print(f"Prosječno/prevod:     {(t_translate + t_score) / done * 1000:.1f} ms")

if __name__ == "__main__":
    main()
