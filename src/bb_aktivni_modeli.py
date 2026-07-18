#!/usr/bin/env python3
"""
bb_aktivni_modeli.py — ispisuje aktivne modele zadane faze iz bb_modeli.
Izlaz: jedna linija po modelu, format: naziv|temperatura
Upotreba: venv/bin/python src/bb_aktivni_modeli.py --faza 1
Koriste ga run_pipeline.sh i run_faza.sh (DB-vodjene petlje, s114/s134).
"""
import os
import sys
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--faza", type=int, default=1)
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT m.naziv, ROUND(t.vrijednost::numeric,4) AS temp
        FROM bb_prevodi_knjige pk
        JOIN bb_modeli m ON pk.model_id = m.id
        JOIN bb_temperature t ON pk.temperatura_id = t.id
        JOIN bb_faze_a1 a1 ON a1.faza_id = pk.faza_id AND a1.model_id = pk.model_id AND a1.aktivan
        JOIN bb_faze_a2 a2 ON a2.faza_id = pk.faza_id AND a2.temperatura_id = pk.temperatura_id AND a2.aktivan
        WHERE pk.faza_id = %s
        ORDER BY m.naziv, temp DESC
    """, (args.faza,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print(f"Nema aktivnih modela za fazu {args.faza}!", file=sys.stderr)
        sys.exit(1)
    for naziv, temp in rows:
        print(f"{naziv}|{temp}")

if __name__ == "__main__":
    main()
