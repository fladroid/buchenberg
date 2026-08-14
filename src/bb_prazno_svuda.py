"""
bb_prazno_svuda.py
Report "prazno svuda" — kompaktni intervali (od-do) po KNJIZI (agregirano
preko skupa jezika): "prazno" = NIJEDAN jezik iz skupa nema pobjednika na toj
poziciji, "dotaknuto" = BAR JEDAN jezik iz skupa ima pobjednika na toj poziciji.

Skup jezika je po defaultu SVI registrovani jezici; --jezik ga suzava na
zadatu listu (npr. "af mk ja" — samo ta tri jezika ulaze u OR).

Razlika prema bb_rupe_pobjednika.py: onaj report je po (knjiga, jezik) paru,
jedan jezik odjednom; ovaj je po knjizi, presjek zadatog skupa jezika u jedno.

Primjer:
    venv/bin/python src/bb_prazno_svuda.py
    venv/bin/python src/bb_prazno_svuda.py --knjiga 12
    venv/bin/python src/bb_prazno_svuda.py --knjiga 12 --jezik af mk ja
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

KNJIGE_SQL = """
    SELECT id, naziv
    FROM bb_knjige
    WHERE (%(knjiga)s IS NULL OR id = %(knjiga)s)
    ORDER BY id
"""

GAPS_SQL = """
    WITH dotaknuto AS (
        SELECT DISTINCT recenica_pozicija AS pozicija
        FROM v_pobjednici_full
        WHERE knjiga_id = %(knjiga)s
          AND (%(jezici)s IS NULL OR jezik_kod = ANY(%(jezici)s))
    ),
    domen AS (
        SELECT r.pozicija,
               (d.pozicija IS NOT NULL) AS ima_pobjednika
        FROM bb_recenice r
        LEFT JOIN dotaknuto d ON d.pozicija = r.pozicija
        WHERE r.knjiga_id = %(knjiga)s
    ),
    grupisano AS (
        SELECT pozicija, ima_pobjednika,
               pozicija - ROW_NUMBER() OVER (
                   PARTITION BY ima_pobjednika ORDER BY pozicija
               ) AS grp
        FROM domen
    )
    SELECT ima_pobjednika, MIN(pozicija) AS od, MAX(pozicija) AS do, COUNT(*) AS broj
    FROM grupisano
    GROUP BY ima_pobjednika, grp
    ORDER BY od
"""


def main():
    parser = argparse.ArgumentParser(
        description="Report 'prazno svuda' — pozicije bez ijednog pobjednika u zadatom skupu jezika, po knjizi."
    )
    parser.add_argument("--knjiga", type=int, default=None,
                         help="knjiga_id (default: sve knjige)")
    parser.add_argument("--jezik", type=str, nargs="+", default=None,
                         help="lista kodova jezika razdvojena razmakom, npr. af mk ja "
                              "(default: svi registrovani jezici)")
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    cur.execute(KNJIGE_SQL, {"knjiga": args.knjiga})
    knjige = cur.fetchall()

    if not knjige:
        print("Nema knjige koja odgovara filteru.")
        cur.close()
        conn.close()
        return

    opseg_jezika = ", ".join(args.jezik) if args.jezik else "svi registrovani jezici"
    print(f"Skup jezika (OR): {opseg_jezika}")
    print(f"{'knjiga_id':<10} {'knjiga':<38} {'tip':<12} {'od':>6} {'do':>6} {'broj':>6}")
    print("-" * 84)

    ukupno_prazno = 0
    ukupno_dotaknuto = 0
    broj_praznih_intervala = 0

    for knjiga_id, knjiga_naziv in knjige:
        cur.execute(GAPS_SQL, {"knjiga": knjiga_id, "jezici": args.jezik})
        redovi = cur.fetchall()
        naziv_kratak = (knjiga_naziv[:36] + "\u2026") if len(knjiga_naziv) > 37 else knjiga_naziv

        if not redovi:
            # knjiga bez ijedne rečenice u bb_recenice — teoretski, prijaviti i to
            print(f"{knjiga_id:<10} {naziv_kratak:<38} {'(bez recenica)':<12} {'':>6} {'':>6} {'':>6}")
            continue

        for ima_pobjednika, od, do, broj in redovi:
            tip = "dotaknuto" if ima_pobjednika else "prazno"
            if ima_pobjednika:
                ukupno_dotaknuto += broj
            else:
                ukupno_prazno += broj
                broj_praznih_intervala += 1
            print(f"{knjiga_id:<10} {naziv_kratak:<38} {tip:<12} {od:>6} {do:>6} {broj:>6}")

    print("-" * 84)
    print(f"UKUPNO: dotaknuto={ukupno_dotaknuto}  prazno={ukupno_prazno}  "
          f"(broj praznih-intervala={broj_praznih_intervala}, broj knjiga={len(knjige)})")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
