#!/usr/bin/env python3
"""
run_embeddings.py — Punjenje sentence_embeddings i translation_embeddings.
Enkodira EN rečenice i sve prevode za dati range.
ON CONFLICT DO NOTHING — sigurno ponavljanje.

Upotreba:
    venv/bin/python src/run_embeddings.py --embedder minilm --sent_from 1 --sent_to 40
    venv/bin/python src/run_embeddings.py --embedder e5     --sent_from 1 --sent_to 40
"""
import os
import argparse
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = int(os.getenv("DB_PORT", 5432))
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

EMBEDDER_CONFIG = {
    "minilm": {
        "model":      "paraphrase-multilingual-MiniLM-L12-v2",
        "dim":        384,
        "batch_size": 64,
    },
    "e5": {
        "model":      "intfloat/multilingual-e5-large",
        "dim":        1024,
        "batch_size": 32,
    },
}


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--embedder",  required=True, choices=list(EMBEDDER_CONFIG.keys()))
    parser.add_argument("--sent_from", type=int, default=1)
    parser.add_argument("--sent_to",   type=int, default=40)
    args = parser.parse_args()

    cfg        = EMBEDDER_CONFIG[args.embedder]
    model_name = cfg["model"]
    dim        = cfg["dim"]
    batch_size = cfg["batch_size"]

    logger.info(f"Embedder: {args.embedder} | model: {model_name} | dim: {dim}")
    logger.info("Učitavam model ...")
    model = SentenceTransformer(model_name)

    conn = get_conn()
    register_vector(conn)
    cur = conn.cursor()

    # ── EN originali ──────────────────────────────────────────────────────
    cur.execute(
        "SELECT id, text FROM sentences WHERE id BETWEEN %s AND %s ORDER BY id",
        (args.sent_from, args.sent_to)
    )
    sentences = cur.fetchall()
    sent_ids  = [r[0] for r in sentences]
    en_texts  = [r[1] for r in sentences]
    logger.info(f"EN rečenica: {len(sentences)}")

    logger.info("Enkodiram EN originale ...")
    en_vecs = model.encode(en_texts, batch_size=batch_size,
                           normalize_embeddings=True, show_progress_bar=False)

    inserted_en = 0
    for (sid, _), vec in zip(sentences, en_vecs):
        cur.execute(
            """INSERT INTO sentence_embeddings (sentence_id, embedder, dim, vec)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (sentence_id, embedder) DO NOTHING""",
            (sid, args.embedder, dim, vec.tolist())
        )
        inserted_en += cur.rowcount
    conn.commit()
    logger.info(f"sentence_embeddings: {inserted_en} novih, {len(sentences) - inserted_en} već postojalo.")

    # ── Prevodi ───────────────────────────────────────────────────────────
    cur.execute(
        """SELECT id, translation FROM translations
           WHERE sentence_id = ANY(%s)
           ORDER BY sentence_id, target_lang, model, temperature""",
        (sent_ids,)
    )
    trans_rows  = cur.fetchall()
    trans_ids   = [r[0] for r in trans_rows]
    trans_texts = [r[1] for r in trans_rows]
    logger.info(f"Prevoda: {len(trans_rows)}")

    logger.info("Enkodiram prevode ...")
    trans_vecs = model.encode(trans_texts, batch_size=batch_size,
                              normalize_embeddings=True, show_progress_bar=False)

    inserted_tr = 0
    for tid, vec in zip(trans_ids, trans_vecs):
        cur.execute(
            """INSERT INTO translation_embeddings (translation_id, embedder, dim, vec)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (translation_id, embedder) DO NOTHING""",
            (tid, args.embedder, dim, vec.tolist())
        )
        inserted_tr += cur.rowcount

    conn.commit()
    logger.info(f"translation_embeddings: {inserted_tr} novih, "
                f"{len(trans_rows) - inserted_tr} već postojalo.")
    logger.info("Gotovo.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
