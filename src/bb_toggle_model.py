#!/usr/bin/env python3
"""
bb_toggle_model.py — uključuje/isključuje jedan model (a1) za zadanu fazu preko bb_faze_a1.aktivan.
Koristi se za privremeno suženje root faze (npr. "gated root" wrapper — vidi run_root_gated.sh).
Upotreba: venv/bin/python src/bb_toggle_model.py --faza 1 --model glm-5.2 --aktivan false
Exit 1 ako faza+model kombinacija ne postoji u bb_faze_a1.
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
    p.add_argument("--model", type=str, required=True, help="naziv iz bb_modeli")
    p.add_argument("--aktivan", type=str, required=True, choices=["true", "false"])
    args = p.parse_args()
    aktivan = args.aktivan == "true"

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute("""
        UPDATE bb_faze_a1 a1
        SET aktivan = %s
        FROM bb_modeli m
        WHERE a1.model_id = m.id
          AND a1.faza_id = %s
          AND m.naziv = %s
        RETURNING a1.faza_id
    """, (aktivan, args.faza, args.model))
    row = cur.fetchone()
    conn.commit()
    conn.close()

    if not row:
        print(f"Kombinacija faza={args.faza} model={args.model} ne postoji u bb_faze_a1!", file=sys.stderr)
        sys.exit(1)

    print(f"bb_faze_a1: faza={args.faza} model={args.model} aktivan={aktivan}")

if __name__ == "__main__":
    main()
