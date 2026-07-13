#!/usr/bin/env python3
"""
bb_faza_info.py — ispisuje metod zadane faze iz bb_faze JOIN bb_metode.
Izlaz: metod_id|metod_naziv|root   (root: t/f)
Exit 1 ako faza ne postoji.
Upotreba: venv/bin/python src/bb_faza_info.py --faza 2
"""
import os, sys, argparse, psycopg2
from dotenv import load_dotenv

load_dotenv()

DB = {
    "host":     os.getenv("DB_HOST", "balsam.dynu.net"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   "bb",
    "user":     os.getenv("DB_USER", "pgu"),
    "password": os.getenv("DB_PASSWORD"),
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--faza", type=int, required=True)
    args = p.parse_args()

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT m.id, m.naziv, m.root
        FROM bb_faze f JOIN bb_metode m ON m.id = f.metod_id
        WHERE f.id = %s
    """, (args.faza,))
    row = cur.fetchone()
    conn.close()

    if not row:
        print(f"Faza {args.faza} ne postoji u bb_faze!", file=sys.stderr)
        sys.exit(1)

    mid, mnaziv, mroot = row
    print(f"{mid}|{mnaziv}|{'t' if mroot else 'f'}")

if __name__ == "__main__":
    main()
