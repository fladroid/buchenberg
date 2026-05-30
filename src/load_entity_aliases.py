#!/usr/bin/env python3
"""
load_entity_aliases.py — Puni entity_aliases tabelu iz JSON fajla.

Upotreba:
    venv/bin/python src/load_entity_aliases.py --book_id 1
"""
import os, json, argparse, psycopg2
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book_id", type=int, default=1)
    args = parser.parse_args()

    in_path = f"logs/entity_aliases_book{args.book_id}.json"
    if not os.path.exists(in_path):
        logger.error(f"Fajl ne postoji: {in_path}")
        return

    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)

    # Filtriraj noise
    to_insert = [e for e in data if e.get("role") != "noise"]
    logger.info(f"Za unos: {len(to_insert)} entiteta (noise preskocen)")

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT",5432)),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    cur = conn.cursor()

    inserted = 0
    skipped  = 0
    for e in to_insert:
        try:
            cur.execute("""
                INSERT INTO entity_aliases
                    (book_id, raw_text, raw_label, canonical_name, correct_label, role, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (book_id, raw_text) DO UPDATE SET
                    raw_label      = EXCLUDED.raw_label,
                    canonical_name = EXCLUDED.canonical_name,
                    correct_label  = EXCLUDED.correct_label,
                    role           = EXCLUDED.role,
                    source         = EXCLUDED.source
            """, (
                args.book_id,
                e.get("raw",""),
                e.get("raw_label",""),
                e.get("canonical",""),
                e.get("correct_label",""),
                e.get("role","other"),
                e.get("source","llm")
            ))
            inserted += 1
        except Exception as ex:
            logger.warning(f"Skip '{e.get('raw')}': {ex}")
            skipped += 1

    conn.commit()
    conn.close()
    logger.success(f"Upisano: {inserted} | preskoceno: {skipped}")

    # Kratka provjera
    conn2 = psycopg2.connect(
        host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT",5432)),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    cur2 = conn2.cursor()
    cur2.execute("""
        SELECT role, COUNT(*) as cnt
        FROM entity_aliases WHERE book_id = %s
        GROUP BY role ORDER BY cnt DESC
    """, (args.book_id,))
    rows = cur2.fetchall()
    conn2.close()

    print(f"\n=== entity_aliases — book_id={args.book_id} ===")
    for role, cnt in rows:
        print(f"  {role:20s}: {cnt}")

if __name__ == "__main__":
    main()
