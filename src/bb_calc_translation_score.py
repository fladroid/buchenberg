"""
bb_calc_translation_score.py
Izračunava translation_score (cosine(EN, prevod)) za postojeće redove
gdje je translation_score IS NULL.

Primjer:
    venv/bin/python src/bb_calc_translation_score.py \
        --embedder "multilingual-e5-large"
"""

import os
import sys
import argparse
import psycopg2
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

DB = {
    "host":     os.getenv("DB_HOST", "balsam.dynu.net"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   "bb",
    "user":     os.getenv("DB_USER", "pgu"),
    "password": os.getenv("DB_PASSWORD"),
}

EMBEDDER_PATH_MAP = {
    "multilingual-e5-large": "intfloat/multilingual-e5-large",
    "paraphrase-multilingual-MiniLM-L12-v2": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
}

BATCH_SIZE = 50


def cosine(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def main():
    import functools
    global print
    print = functools.partial(print, flush=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--embedder", type=str, required=True)
    args = parser.parse_args()

    embedder_path = EMBEDDER_PATH_MAP.get(args.embedder, args.embedder)
    print(f"Učitavam embedder: {args.embedder} ({embedder_path})")
    embedder = SentenceTransformer(embedder_path)

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    # Dohvati sve redove gdje translation_score IS NULL
    # za embedder koji odgovara traženom
    cur.execute("""
        SELECT r.id, s.tekst, r.prevod
        FROM bb_prevodi_recenica r
        JOIN bb_recenice s ON r.recenica_id = s.id
        JOIN bb_prevodi_knjige pk ON r.prevodi_knjige_id = pk.id
        JOIN bb_embeddings e ON pk.embeddings_id = e.id
        WHERE r.translation_score IS NULL
          AND e.naziv = %s
        ORDER BY r.id
    """, (args.embedder,))
    rows = cur.fetchall()

    print(f"Redova za update: {len(rows)}")

    updated = 0
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i:i + BATCH_SIZE]
        ids      = [r[0] for r in chunk]
        originals = [r[1] for r in chunk]
        prevodi  = [r[2] for r in chunk]

        en_vektori     = embedder.encode(originals)
        prevod_vektori = embedder.encode(prevodi)

        for j, rid in enumerate(ids):
            ts = cosine(en_vektori[j], prevod_vektori[j])
            cur.execute(
                "UPDATE bb_prevodi_recenica SET translation_score = %s WHERE id = %s",
                (ts, rid)
            )

        conn.commit()
        updated += len(chunk)
        print(f"  Ažurirano: {updated}/{len(rows)}")

    cur.close()
    conn.close()
    print(f"\nGotovo. Ukupno ažurirano: {updated} redova.")


if __name__ == "__main__":
    main()
