"""
bb_web_export.py
Generira JSON fajlove za Buchenberg web stranicu.

Output:
    /var/www/buchenberg/data/books.json       — katalog knjiga i jezika
    /var/www/buchenberg/data/tr_<lang>.json   — prevod po jeziku (svi pobjednici)

Primjer:
    venv/bin/python src/bb_web_export.py
    venv/bin/python src/bb_web_export.py --output /var/www/buchenberg/data
"""

import os
import json
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

DEFAULT_OUTPUT = "/var/www/buchenberg/data"


def get_books(cur):
    cur.execute("""
        SELECT
            k.id,
            k.naziv,
            k.autor,
            k.gutenberg_id,
            COUNT(DISTINCT r.id) AS ukupno_recenica
        FROM bb_knjige k
        JOIN bb_recenice r ON r.knjiga_id = k.id
        GROUP BY k.id, k.naziv, k.autor, k.gutenberg_id
        ORDER BY k.id
    """)
    return cur.fetchall()


def get_languages_for_book(cur, knjiga_id):
    cur.execute("""
        SELECT
            j.kod,
            j.naziv,
            COUNT(DISTINCT r.pozicija) AS prevedenih_recenica
        FROM bb_prev_knjige pk
        JOIN bb_jezik j ON j.id = pk.jezik_id
        JOIN bb_prev_recenica pvr ON pvr.prev_knjige_id = pk.id
        JOIN bb_prevodi_recenica pr ON pr.id = pvr.prevodi_recenica_id
        JOIN bb_recenice r ON r.id = pr.recenica_id
        WHERE pk.knjiga_id = %s
        GROUP BY j.kod, j.naziv
        ORDER BY prevedenih_recenica DESC, j.kod
    """, (knjiga_id,))
    return cur.fetchall()


def get_translations(cur, knjiga_id, lang_kod):
    cur.execute("""
        SELECT
            r.pozicija,
            r.tekst             AS original,
            pr.prevod           AS translation,
            m.naziv             AS model,
            m.temperatura       AS temperatura,
            ROUND(pr.score::numeric, 4)             AS back_score,
            ROUND(pr.translation_score::numeric, 4) AS ts,
            ROUND(pr.sudija_avg::numeric, 4)        AS judge_avg
        FROM bb_prev_knjige pk
        JOIN bb_jezik j         ON j.id  = pk.jezik_id
        JOIN bb_prev_recenica pvr ON pvr.prev_knjige_id = pk.id
        JOIN bb_prevodi_recenica pr ON pr.id = pvr.prevodi_recenica_id
        JOIN bb_prevodi_knjige ppk  ON ppk.id = pr.prevodi_knjige_id
        JOIN bb_modeli m            ON m.id  = ppk.model_id
        JOIN bb_recenice r          ON r.id  = pr.recenica_id
        WHERE pk.knjiga_id = %s AND j.kod = %s
        ORDER BY r.pozicija
    """, (knjiga_id, lang_kod))
    return cur.fetchall()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT,
                        help=f"Output direktorijum (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    # --- books.json ---
    books_data = []
    books = get_books(cur)

    for book_id, naziv, autor, gutenberg_id, ukupno in books:
        langs = get_languages_for_book(cur, book_id)
        lang_list = [
            {"code": kod, "name": naziv_j, "sentences": prevedenih}
            for kod, naziv_j, prevedenih in langs
        ]
        books_data.append({
            "id":               book_id,
            "title":            naziv,
            "author":           autor,
            "gutenberg_id":     gutenberg_id,
            "total_sentences":  ukupno,
            "languages":        lang_list,
        })

    books_path = os.path.join(args.output, "books.json")
    with open(books_path, "w", encoding="utf-8") as f:
        json.dump(books_data, f, ensure_ascii=False, indent=2)
    print(f"books.json — {len(books_data)} knjiga(e)")

    # --- tr_<lang>.json po knjizi i jeziku ---
    for book_id, naziv, autor, _, _ in books:
        langs = get_languages_for_book(cur, book_id)
        for lang_kod, lang_naziv, prevedenih in langs:
            rows = get_translations(cur, book_id, lang_kod)
            if not rows:
                continue

            sentences = []
            for pozicija, original, translation, model, temperatura, back_score, ts, judge_avg in rows:
                sentences.append({
                    "pos":         pozicija,
                    "original":    original,
                    "translation": translation,
                    "model":       model,
                    "temp":        float(temperatura) if temperatura is not None else None,
                    "back_score":  float(back_score)  if back_score  is not None else None,
                    "ts":          float(ts)           if ts          is not None else None,
                    "judge_avg":   float(judge_avg)    if judge_avg   is not None else None,
                })

            out = {
                "book_id":   book_id,
                "title":     naziv,
                "author":    autor,
                "language":  lang_kod,
                "lang_name": lang_naziv,
                "sentences": sentences,
            }

            fname = f"tr_{book_id}_{lang_kod}.json"
            fpath = os.path.join(args.output, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            print(f"  {fname} — {len(sentences)} rečenica ({lang_naziv})")

    cur.close()
    conn.close()
    print("Gotovo.")


if __name__ == "__main__":
    main()
