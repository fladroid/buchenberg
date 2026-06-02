"""
bb_07_rag_score.py
Računa naturalness_score za prevode koristeći k-NN upit u bb_rag_korpus.
naturalness_score = prosječni cosinus između prevod_vektor i k najbližih susjeda.

Primjer:
    venv/bin/python src/bb_07_rag_score.py \
        --embedder "multilingual-e5-large" \
        --k 10
"""

import os
import argparse
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB = {
    "host":     os.getenv("DB_HOST", "balsam.dynu.net"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   "bb",
    "user":     os.getenv("DB_USER", "pgu"),
    "password": os.getenv("DB_PASSWORD"),
}

BATCH_SIZE = 100


def main():
    import functools
    global print
    print = functools.partial(print, flush=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--embedder", type=str, default="multilingual-e5-large")
    parser.add_argument("--k",        type=int, default=10)
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    # Dohvati redove gdje prevod_vektor postoji ali naturalness_score IS NULL
    cur.execute("""
        SELECT r.id, r.prevod_vektor, j.kod
        FROM bb_prevodi_recenica r
        JOIN bb_prevodi_knjige pk ON r.prevodi_knjige_id = pk.id
        JOIN bb_embeddings e ON pk.embeddings_id = e.id
        JOIN bb_jezik j ON pk.jezik_id = j.id
        WHERE r.prevod_vektor IS NOT NULL
          AND r.naturalness_score IS NULL
          AND e.naziv = %s
        ORDER BY r.id
    """, (args.embedder,))
    rows = cur.fetchall()

    print(f"Redova za naturalness_score: {len(rows)}")
    if not rows:
        print("Nema posla. Izlazim.")
        cur.close()
        conn.close()
        return

    updated = 0
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i:i + BATCH_SIZE]

        for rid, vektor, jezik_kod in chunk:
            # k-NN upit u bb_rag_korpus za odgovarajući jezik
            cur.execute("""
                SELECT 1 - (rk.vektor <=> %s::vector) AS cosinus
                FROM bb_rag_korpus rk
                JOIN bb_jezik j ON rk.jezik_id = j.id
                WHERE j.kod = %s
                ORDER BY rk.vektor <=> %s::vector
                LIMIT %s
            """, (vektor, jezik_kod, vektor, args.k))
            susjedi = cur.fetchall()

            if not susjedi:
                continue

            naturalness = sum(r[0] for r in susjedi) / len(susjedi)

            cur.execute(
                "UPDATE bb_prevodi_recenica SET naturalness_score = %s WHERE id = %s",
                (naturalness, rid)
            )

        conn.commit()
        updated += len(chunk)
        print(f"  Obrađeno: {updated}/{len(rows)}")

    cur.close()
    conn.close()
    print(f"\nGotovo. Ukupno ažurirano: {updated} redova.")


if __name__ == "__main__":
    main()
