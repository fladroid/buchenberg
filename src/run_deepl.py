#!/usr/bin/env python3
"""
run_deepl.py — DeepL HR prevod svih 40 rečenica.
Upisuje u translations (model='deepl', temperature=0.0).
Loguje usporedbu s trenutnim e5 best scoreom.

Upotreba:
    venv/bin/python src/run_deepl.py > logs/deepl_hr_002.log 2>&1
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

MODEL_EMBED = "intfloat/multilingual-e5-large"
SENT_FROM   = 1
SENT_TO     = 40


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )


def fetch_sentences(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT s.id, s.text, s.book_id,
                   ts.cosine_score AS best_e5_score
            FROM sentences s
            LEFT JOIN (
                SELECT DISTINCT ON (sentence_id)
                    sentence_id, cosine_score
                FROM translation_scores
                WHERE target_lang = 'hr' AND embedder = 'e5'
                ORDER BY sentence_id, cosine_score DESC
            ) ts ON ts.sentence_id = s.id
            WHERE s.id BETWEEN %s AND %s
            ORDER BY s.id
        """, (SENT_FROM, SENT_TO))
        return cur.fetchall()


def insert_translation(conn, sentence_id, book_id, translation):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO translations
                (sentence_id, book_id, target_lang, model, temperature, translation)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (sentence_id, target_lang, model, temperature) DO NOTHING
        """, (sentence_id, book_id, 'hr', 'deepl', 0.0, translation))
    conn.commit()


def cosine(v1, v2):
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def main():
    logger.info("=" * 62)
    logger.info("  run_deepl.py — DeepL HR, sve rečenice")
    logger.info(f"  Rečenice: {SENT_FROM}–{SENT_TO}  |  model=deepl  temp=0.0")
    logger.info("=" * 62)

    conn = get_conn()
    sentences = fetch_sentences(conn)
    logger.info(f"Rečenica: {len(sentences)}\n")

    translator = deepl.Translator(DEEPL_API_KEY)
    usage = translator.get_usage()
    logger.info(f"DeepL usage: {usage.character.count}/{usage.character.limit} znakova\n")

    logger.info("Učitavam e5-large embedder...")
    embedder = SentenceTransformer(MODEL_EMBED)
    logger.info("e5 učitan.\n")

    improved = 0
    inserted = 0

    for sid, en_text, book_id, best_e5 in sentences:
        result = translator.translate_text(en_text, target_lang="HR")
        deepl_text = result.text

        vecs = embedder.encode([en_text, deepl_text], normalize_embeddings=True)
        deepl_score = round(cosine(vecs[0], vecs[1]), 4)

        insert_translation(conn, sid, book_id, deepl_text)
        inserted += 1

        if best_e5 is not None:
            delta = round(deepl_score - float(best_e5), 4)
            icon = "✅" if delta > 0 else ("➖" if delta == 0 else "🔽")
            logger.info(
                f"s{sid:2d}  deepl={deepl_score:.4f}  "
                f"best_e5={float(best_e5):.4f}  "
                f"delta={delta:+.4f}  {icon}  |  {deepl_text[:55]}"
            )
            if delta > 0:
                improved += 1
        else:
            logger.info(f"s{sid:2d}  deepl={deepl_score:.4f}  |  {deepl_text[:55]}")

    conn.close()

    logger.info("\n" + "=" * 62)
    logger.info(f"  Upisano:  {inserted}/40")
    logger.info(f"  DeepL > best_e5: {improved}/40")
    logger.info("=" * 62)


if __name__ == "__main__":
    main()
