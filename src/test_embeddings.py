#!/usr/bin/env python3
"""
test_embeddings.py — test: encode 5 rečenica (EN + IT) s e5-large,
upiši u sentence_embeddings i translation_embeddings, izračunaj cosinus.

Upotreba:
    venv/bin/python src/test_embeddings.py
"""
import os
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

EMBEDDER   = "e5"
DIM        = 1024
MODEL_NAME = "intfloat/multilingual-e5-large"
SENT_FROM  = 4
SENT_TO    = 8
IT_MODEL   = "gemma3:12b"
IT_TEMP    = 0.5


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def main():
    logger.info(f"Učitavam {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    conn = get_conn()
    register_vector(conn)
    cur = conn.cursor()

    # 1. EN originali
    cur.execute(
        "SELECT id, text FROM sentences WHERE id BETWEEN %s AND %s ORDER BY id",
        (SENT_FROM, SENT_TO)
    )
    sentences = cur.fetchall()
    logger.info(f"Učitano {len(sentences)} EN rečenica.")

    # 2. IT prevodi
    sent_ids = [r[0] for r in sentences]
    cur.execute(
        """SELECT id, sentence_id, translation FROM translations
           WHERE sentence_id = ANY(%s)
             AND target_lang = 'it'
             AND model = %s AND temperature = %s
           ORDER BY sentence_id""",
        (sent_ids, IT_MODEL, IT_TEMP)
    )
    trans_rows = cur.fetchall()
    trans_by_sid = {r[1]: (r[0], r[2]) for r in trans_rows}
    logger.info(f"Učitano {len(trans_rows)} IT prevoda.")

    # 3. Enkodiranje
    en_texts = [r[1] for r in sentences]
    it_sids  = [sid for sid in sent_ids if sid in trans_by_sid]
    it_texts = [trans_by_sid[sid][1] for sid in it_sids]

    logger.info("Enkodiram EN originale ...")
    en_vecs = model.encode(en_texts, normalize_embeddings=True)
    logger.info("Enkodiram IT prevode ...")
    it_vecs = model.encode(it_texts, normalize_embeddings=True)

    # 4. Upisivanje — sentence_embeddings (EN)
    cur.execute(
        "DELETE FROM sentence_embeddings WHERE sentence_id = ANY(%s) AND embedder = %s",
        (sent_ids, EMBEDDER)
    )
    for (sid, _), vec in zip(sentences, en_vecs):
        cur.execute(
            """INSERT INTO sentence_embeddings (sentence_id, embedder, dim, vec)
               VALUES (%s, %s, %s, %s)""",
            (sid, EMBEDDER, DIM, vec.tolist())
        )
    logger.info(f"Upisano {len(sentences)} EN vektora u sentence_embeddings.")

    # 5. Upisivanje — translation_embeddings (IT)
    it_trans_ids = [trans_by_sid[sid][0] for sid in it_sids]
    cur.execute(
        "DELETE FROM translation_embeddings WHERE translation_id = ANY(%s) AND embedder = %s",
        (it_trans_ids, EMBEDDER)
    )
    for sid, vec in zip(it_sids, it_vecs):
        tid = trans_by_sid[sid][0]
        cur.execute(
            """INSERT INTO translation_embeddings (translation_id, embedder, dim, vec)
               VALUES (%s, %s, %s, %s)""",
            (tid, EMBEDDER, DIM, vec.tolist())
        )
    logger.info(f"Upisano {len(it_sids)} IT vektora u translation_embeddings.")

    conn.commit()

    # 6. Cosinus query — JOIN između dvije tabele
    cur.execute("""
        SELECT
            se.sentence_id,
            LEFT(s.text, 55)        AS en_original,
            LEFT(t.translation, 55) AS it_prevod,
            ROUND((1 - (se.vec <=> te.vec))::numeric, 4) AS cosine
        FROM sentence_embeddings se
        JOIN translations t        ON t.sentence_id = se.sentence_id
                                   AND t.target_lang = 'it'
                                   AND t.model = %s
                                   AND t.temperature = %s
        JOIN translation_embeddings te ON te.translation_id = t.id
                                       AND te.embedder = %s
        JOIN sentences s           ON s.id = se.sentence_id
        WHERE se.embedder = %s
          AND se.sentence_id = ANY(%s)
        ORDER BY se.sentence_id
    """, (IT_MODEL, IT_TEMP, EMBEDDER, EMBEDDER, sent_ids))

    rows = cur.fetchall()

    print("\n" + "="*70)
    print(f"  Cosinus  EN vs IT  |  {IT_MODEL}  t={IT_TEMP}  |  embedder: {EMBEDDER}")
    print("="*70)
    for sid, en, it, cos in rows:
        print(f"\n  s{sid}  cosine = {cos}")
        print(f"    EN: {en}")
        print(f"    IT: {it}")
    print("\n" + "="*70 + "\n")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
