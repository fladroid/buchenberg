"""
bb_05_export.py
Eksportuje finalni prevod knjige u tekstualni fajl.

Primjer:
    venv/bin/python src/bb_05_export.py --knjiga 1 --jezik hr
    venv/bin/python src/bb_05_export.py --knjiga 1 --jezik hr it de
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

OUTPUT_DIR = "output"


def export_jezik(cur, knjiga_id, kod):
    cur.execute("""
        SELECT pk.id, k.naziv
        FROM bb_prev_knjige pk
        JOIN bb_knjige k ON k.id = pk.knjiga_id
        JOIN bb_jezik j  ON j.id = pk.jezik_id
        WHERE pk.knjiga_id = %s AND j.kod = %s
    """, (knjiga_id, kod))
    row = cur.fetchone()
    if not row:
        print(f"Nema finalnog prevoda za jezik '{kod}', preskačem.")
        return

    prev_knjige_id, naziv_knjige = row

    cur.execute("""
        SELECT
            r.pozicija,
            pr.prevod,
            m.naziv  AS model,
            pr.score
        FROM bb_prev_recenica pr_fin
        JOIN bb_prevodi_recenica pr  ON pr.id  = pr_fin.prevodi_recenica_id
        JOIN bb_prevodi_knjige pk    ON pk.id  = pr.prevodi_knjige_id
        JOIN bb_modeli m             ON m.id   = pk.model_id
        JOIN bb_recenice r           ON r.id   = pr.recenica_id
        WHERE pr_fin.prev_knjige_id = %s
        ORDER BY r.pozicija
    """, (prev_knjige_id,))

    redovi = cur.fetchall()
    if not redovi:
        print(f"  Nema redova za {kod}.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    naziv_fajla = naziv_knjige.lower().replace(" ", "_")
    putanja = os.path.join(OUTPUT_DIR, f"{naziv_fajla}_{kod}.txt")

    with open(putanja, "w", encoding="utf-8") as f:
        f.write(f"{naziv_knjige} [{kod.upper()}]\n")
        f.write("=" * 60 + "\n\n")
        for pozicija, prevod, model, score in redovi:
            f.write(f"[s{pozicija}] {prevod}\n")

    print(f"  {kod}: {len(redovi)} rečenica → {putanja}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--knjiga", type=int,  required=True)
    parser.add_argument("--jezik",  type=str,  nargs="+", required=True)
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    for kod in args.jezik:
        export_jezik(cur, args.knjiga, kod)

    cur.close()
    conn.close()
    print("Gotovo.")


if __name__ == "__main__":
    main()
