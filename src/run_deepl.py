#!/usr/bin/env python3
"""
run_deepl.py — DeepL prevod za crvene HR rečenice.
Prevodi EN original DeepL-om → HR, skoruje MiniLM-om, loguje usporedbu.
Bez upisa u bazu — samo log.

Upotreba:
    venv/bin/python src/run_deepl.py > logs/deepl_hr_001.log 2>&1
"""

import os
import psycopg2
import deepl
import numpy as np
from dotenv import load_dotenv
from loguru import logger
from sentence_transformers import SentenceTransformer

load_dotenv()

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")
DB_HOST       = os.getenv("DB_HOST")
DB_PORT       = int(os.getenv("DB_PORT", 5432))
DB_NAME       = os.getenv("DB_NAME")
DB_USER       = os.getenv("DB_USER")
DB_PASSWORD   = os.getenv("DB_PASSWORD")

MODEL_EMBED  = "paraphrase-multilingual-MiniLM-L12-v2"
RED_THRESH   = 0.80
SENT_FROM    = 1
SENT_TO      = 40


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )


def fetch_red_hr(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ON (sentence_id)
                sentence_id,
                s.text         AS en_text,
                ts.translation AS hr_text,
                ts.cosine_score AS hr_score
            FROM translation_scores ts
            JOIN sentences s ON s.id = ts.sentence_id
            WHERE ts.target_lang = 'hr'
              AND ts.embedder    = 'minilm'
              AND ts.sentence_id BETWEEN %s AND %s
            ORDER BY sentence_id, cosine_score DESC
        """, (SENT_FROM, SENT_TO))
        rows = cur.fetchall()
    return [(sid, en, hr, float(sc)) for sid, en, hr, sc in rows
            if float(sc) < RED_THRESH]


def cosine(v1, v2):
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def main():
    logger.info("=" * 62)
    logger.info("  run_deepl.py — DeepL prevod crvenih HR rečenica")
    logger.info(f"  Prag: score < {RED_THRESH}")
    logger.info("=" * 62)

    conn = get_conn()
    candidates = fetch_red_hr(conn)
    conn.close()
    logger.info(f"Crvenih HR rečenica: {len(candidates)}\n")

    translator = deepl.Translator(DEEPL_API_KEY)
    usage = translator.get_usage()
    logger.info(f"DeepL usage: {usage.character.count}/{usage.character.limit} znakova\n")

    logger.info("Učitavam MiniLM embedder...")
    embedder = SentenceTransformer(MODEL_EMBED)
    logger.info("MiniLM učitan.\n")

    improved = 0

    for sid, en_text, hr_old, hr_old_score in candidates:
        logger.info(f"── s{sid} ────────────────────────────────────────")
        logger.info(f"  EN:        {en_text[:80]}")
        logger.info(f"  HR stari:  {hr_old[:80]}")
        logger.info(f"             score={hr_old_score:.4f}")

        result = translator.translate_text(en_text, target_lang="HR")
        new_hr = result.text

        vecs = embedder.encode([en_text, new_hr])
        new_score = round(cosine(vecs[0], vecs[1]), 4)
        delta = round(new_score - hr_old_score, 4)
        verdict = "✅ POBOLJŠANJE" if new_score > hr_old_score else "❌ ZADRŽATI STARI"

        logger.info(f"  HR DeepL:  {new_hr[:80]}")
        logger.info(f"             score={new_score:.4f}  delta={delta:+.4f}  {verdict}")

        if new_score > hr_old_score:
            improved += 1

    logger.info("\n" + "=" * 62)
    logger.info(f"  Rezultat: {improved}/{len(candidates)} rečenica poboljšano")
    logger.info("=" * 62)


if __name__ == "__main__":
    main()
