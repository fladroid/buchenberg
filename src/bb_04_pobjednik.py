"""
bb_04_pobjednik.py
Za svaku rečenicu bira pobjednika po finalnom scoreu:
    0.4 × kompozitni + 0.6 × sudija_avg
gdje je kompozitni = (score + translation_score) / 2.
Fallback na kompozitni kada sudija_avg IS NULL.

Primjer:
    venv/bin/python src/bb_04_pobjednik.py \
        --knjiga 1 --od 1 --do 40 --jezici hr it
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

W_KOMPOZITNI = 0.4
W_SUDIJA     = 0.6


def get_or_create_prev_knjige(cur, knjiga_id, jezik_id):
    cur.execute("""
        INSERT INTO bb_prev_knjige (knjiga_id, jezik_id)
        VALUES (%s, %s)
        ON CONFLICT (knjiga_id, jezik_id) DO NOTHING
        RETURNING id
    """, (knjiga_id, jezik_id))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("""
        SELECT id FROM bb_prev_knjige
        WHERE knjiga_id = %s AND jezik_id = %s
    """, (knjiga_id, jezik_id))
    return cur.fetchone()[0]


def main():
    import functools
    global print
    print = functools.partial(print, flush=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--knjiga", type=int, required=True)
    parser.add_argument("--od",     type=int, required=True)
    parser.add_argument("--do",     type=int, required=True)
    parser.add_argument("--jezici", type=str, nargs="+", required=True)
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    for kod in args.jezici:
        cur.execute("SELECT id FROM bb_jezik WHERE kod = %s", (kod,))
        row = cur.fetchone()
        if not row:
            print(f"Nepoznat jezik: {kod}, preskačem.")
            continue
        jezik_id = row[0]

        prev_knjige_id = get_or_create_prev_knjige(cur, args.knjiga, jezik_id)
        conn.commit()

        print(f"\n── Jezik: {kod}, prev_knjige_id={prev_knjige_id} ──")

        cur.execute("""
            SELECT DISTINCT ON (r.pozicija)
                r.id       AS recenica_id,
                r.pozicija,
                pr.id      AS prevodi_recenica_id,
                m.naziv    AS model,
                pr.score,
                pr.translation_score,
                pr.sudija_avg,
                CASE
                    WHEN pr.sudija_avg IS NOT NULL THEN
                        %s * (pr.score + pr.translation_score) / 2.0
                        + %s * pr.sudija_avg
                    ELSE
                        (pr.score + pr.translation_score) / 2.0
                END AS finalni_score,
                pr.prevod
            FROM bb_recenice r
            JOIN bb_prevodi_knjige pk ON pk.knjiga_id = r.knjiga_id
            JOIN bb_prevodi_recenica pr ON pr.prevodi_knjige_id = pk.id
                                      AND pr.recenica_id = r.id
            JOIN bb_modeli m ON pk.model_id = m.id
            JOIN bb_jezik j  ON pk.jezik_id = j.id
            JOIN bb_embeddings e ON pk.embeddings_id = e.id
            WHERE r.knjiga_id = %s
              AND r.pozicija BETWEEN %s AND %s
              AND j.kod = %s
              AND e.naziv = 'multilingual-e5-large'
              AND pr.translation_score IS NOT NULL
              AND CASE
                    WHEN pr.sudija_avg IS NOT NULL THEN
                        %s * (pr.score + pr.translation_score) / 2.0
                        + %s * pr.sudija_avg
                    ELSE
                        (pr.score + pr.translation_score) / 2.0
                  END = (
                      SELECT MAX(
                          CASE
                              WHEN pr2.sudija_avg IS NOT NULL THEN
                                  %s * (pr2.score + pr2.translation_score) / 2.0
                                  + %s * pr2.sudija_avg
                              ELSE
                                  (pr2.score + pr2.translation_score) / 2.0
                          END
                      )
                      FROM bb_prevodi_knjige pk2
                      JOIN bb_prevodi_recenica pr2 ON pr2.prevodi_knjige_id = pk2.id
                      JOIN bb_embeddings e2 ON pk2.embeddings_id = e2.id
                      WHERE pk2.knjiga_id = r.knjiga_id
                        AND pk2.jezik_id  = j.id
                        AND pr2.recenica_id = r.id
                        AND pr2.translation_score IS NOT NULL
                        AND e2.naziv = 'multilingual-e5-large'
                  )
            ORDER BY r.pozicija, m.naziv
        """, (W_KOMPOZITNI, W_SUDIJA,
              args.knjiga, args.od, args.do, kod,
              W_KOMPOZITNI, W_SUDIJA,
              W_KOMPOZITNI, W_SUDIJA))

        pobjednici = cur.fetchall()
        print(f"  Pobjednika: {len(pobjednici)}")

        # Resetuj pobjednike za ovaj jezik
        cur.execute("""
            DELETE FROM bb_prev_recenica
            WHERE prev_knjige_id = %s
        """, (prev_knjige_id,))

        upisano = 0
        for recenica_id, pozicija, prevodi_recenica_id, model, score, ts, sudija, finalni, prevod in pobjednici:
            cur.execute("""
                INSERT INTO bb_prev_recenica (prev_knjige_id, prevodi_recenica_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (prev_knjige_id, prevodi_recenica_id))
            upisano += cur.rowcount
            sudija_str = f"sudija={sudija:.3f}" if sudija else "sudija=N/A"
            print(f"  s{pozicija}: {model} komp={(score+ts)/2:.4f} {sudija_str} final={finalni:.4f} | {prevod[:55]}...")

        conn.commit()
        print(f"  Upisano: {upisano}")

    cur.close()
    conn.close()
    print("\nGotovo.")


if __name__ == "__main__":
    main()
