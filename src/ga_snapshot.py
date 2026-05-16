#!/usr/bin/env python3
"""
Buchenberg · ga_snapshot.py
Snapshot stanja test_results prije GA — za analizu poboljšanja.
Prikazuje distribuciju zelenih/žutih/crvenih po jeziku.

Pokretanje:
  venv/bin/python src/ga_snapshot.py --lang it
  venv/bin/python src/ga_snapshot.py --lang it fr de
  venv/bin/python src/ga_snapshot.py  # svi jezici
"""

import os
import argparse
import psycopg2
from dotenv import load_dotenv

load_dotenv()

GREEN = 0.90
YELLOW = 0.80

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

def snapshot(conn, langs):
    cur = conn.cursor()

    for lang in langs:
        cur.execute("""
            SELECT
                s.id,
                LEFT(s.text, 45) as original,
                ROUND(MAX(t.translation_score)::numeric, 4) as best_tr,
                COUNT(t.id) as metode
            FROM sentences s
            JOIN test_results t ON t.sentence_id = s.id
            WHERE t.target_lang = %s
            GROUP BY s.id, s.text
            ORDER BY s.id
        """, (lang,))
        rows = cur.fetchall()

        if not rows:
            print(f"\n[{lang}] Nema podataka u test_results.")
            continue

        zelene = [r for r in rows if r[2] and r[2] >= GREEN]
        zute   = [r for r in rows if r[2] and YELLOW <= r[2] < GREEN]
        crvene = [r for r in rows if r[2] and r[2] < YELLOW]
        ukupno = len(rows)

        print(f"\n{'='*65}")
        print(f"Jezik: {lang.upper()} — {ukupno} rečenica")
        print(f"  🟢 Zelene (≥ {GREEN}): {len(zelene):3d} ({100*len(zelene)//ukupno}%)")
        print(f"  🟡 Žute   ({YELLOW}–{GREEN}): {len(zute):3d} ({100*len(zute)//ukupno}%)")
        print(f"  🔴 Crvene (< {YELLOW}): {len(crvene):3d} ({100*len(crvene)//ukupno}%)")
        print(f"  GA kandidati (žute+crvene): {len(zute)+len(crvene)}")
        print(f"{'='*65}")

        print(f"\n{'s':<5} {'best_tr':>8}  {'tier':<8}  original")
        print("-" * 65)
        for r in rows:
            sc = r[2]
            if sc is None:
                tier = "N/A"
            elif sc >= GREEN:
                tier = "🟢"
            elif sc >= YELLOW:
                tier = "🟡"
            else:
                tier = "🔴"
            print(f"s{r[0]:<4} {str(sc):>8}  {tier:<8}  {r[1]}")

    cur.close()

def main():
    parser = argparse.ArgumentParser(description="GA snapshot — stanje prije GA")
    parser.add_argument("--lang", nargs="+", default=None)
    args = parser.parse_args()

    conn = get_conn()

    if args.lang:
        langs = args.lang
    else:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT target_lang FROM test_results ORDER BY target_lang")
        langs = [r[0] for r in cur.fetchall()]
        cur.close()

    snapshot(conn, langs)
    conn.close()

if __name__ == "__main__":
    main()
