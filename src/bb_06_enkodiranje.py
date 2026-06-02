"""
bb_06_enkodiranje.py
Enkodira prevode i upisuje prevod_vektor u bb_prevodi_recenica
za redove gdje je prevod_vektor IS NULL.

Primjer:
    venv/bin/python src/bb_06_enkodiranje.py \
        --embedder "multilingual-e5-large"
"""

import os
import argparse
import psycopg2
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

BATCH_SIZE = 256


def main():
    import functools
    global print
    print = functools.partial(print, flush=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--embedder", type=str, default="multilingual-e5-large")
    args = parser.parse_args()

    embedder_path = EMBEDDER_PATH_MAP.get(args.embedder, args.embedder)
    print(f"Učitavam embedder: {args.embedder} ({embedder_path})")
    embedder = SentenceTransformer(embedder_path)

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    # Dohvati redove gdje prevod_vektor IS NULL i embedder odgovara
    cur.execute("""
        SELECT r.id, r.prevod
        FROM bb_prevodi_recenica r
        JOIN bb_prevodi_knjige pk ON r.prevodi_knjige_id = pk.id
        JOIN bb_embeddings e ON pk.embeddings_id = e.id
        WHERE r.prevod_vektor IS NULL
          AND e.naziv = %s
        ORDER BY r.id
    """, (args.embedder,))
    rows = cur.fetchall()

    print(f"Redova za enkodiranje: {len(rows)}")
    if not rows:
        print("Nema posla. Izlazim.")
        cur.close()
        conn.close()
        return

    updated = 0
    for i in range(0, len(rows), BATCH_SIZE):
        chunk   = rows[i:i + BATCH_SIZE]
        ids     = [r[0] for r in chunk]
        prevodi = [r[1] for r in chunk]

        vektori = embedder.encode(prevodi, show_progress_bar=False)

        cur.executemany(
            "UPDATE bb_prevodi_recenica SET prevod_vektor = %s WHERE id = %s",
            [(v.tolist(), rid) for v, rid in zip(vektori, ids)]
        )
        conn.commit()

        updated += len(chunk)
        print(f"  Enkodiran: {updated}/{len(rows)}")

    cur.close()
    conn.close()
    print(f"\nGotovo. Ukupno enkodiranih prevoda: {updated}")


if __name__ == "__main__":
    main()
