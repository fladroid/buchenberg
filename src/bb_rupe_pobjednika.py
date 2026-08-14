"""
bb_rupe_pobjednika.py
Report "rupa pobjednika" — kompaktni intervali (od-do) gdje pobjednik POSTOJI
("prevedeno") i gdje NE POSTOJI ("rupa"), po (knjiga, jezik).

Domen = sve pozicije u bb_recenice za tu knjigu.
Pokriva se samo (knjiga, jezik) par koji ima red u bb_prev_knjige (bar jednom
je pokretan bb_04_pobjednik.py za tu kombinaciju) — bez toga bi "rupa" za
kombinaciju koja nikad nije ni dotaknuta bila samo šum, ne signal.

Primjer:
    venv/bin/python src/bb_rupe_pobjednika.py
    venv/bin/python src/bb_rupe_pobjednika.py --knjiga 12
    venv/bin/python src/bb_rupe_pobjednika.py --knjiga 12 --jezik ja
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

PAIRS_SQL = """
    SELECT pk.knjiga_id, k.naziv AS knjiga_naziv, j.kod AS jezik_kod
    FROM bb_prev_knjige pk
    JOIN bb_knjige k ON k.id = pk.knjiga_id
    JOIN bb_jezik j  ON j.id = pk.jezik_id
    WHERE (%(knjiga)s IS NULL OR pk.knjiga_id = %(knjiga)s)
      AND (%(jezik)s  IS NULL OR j.kod = %(jezik)s)
    ORDER BY pk.knjiga_id, j.kod
"""

GAPS_SQL = """
    WITH winners AS (
        SELECT recenica_pozicija AS pozicija
        FROM v_pobjednici_full
        WHERE knjiga_id = %(knjiga)s AND jezik_kod = %(jezik)s
    ),
    domen AS (
        SELECT r.pozicija,
               (w.pozicija IS NOT NULL) AS ima_pobjednika
        FROM bb_recenice r
        LEFT JOIN winners w ON w.pozicija = r.pozicija
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
        description="Report rupa pobjednika (kompaktni intervali) po (knjiga, jezik)."
    )
    parser.add_argument("--knjiga", type=int, default=None,
                         help="knjiga_id (default: sve knjige koje imaju bb_prev_knjige red)")
    parser.add_argument("--jezik", type=str, default=None,
                         help="kod jezika, npr. hr (default: svi jezici)")
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    cur.execute(PAIRS_SQL, {"knjiga": args.knjiga, "jezik": args.jezik})
    parovi = cur.fetchall()

    if not parovi:
        print("Nema (knjiga, jezik) parova koji odgovaraju filteru "
              "(provjeri da li bb_prev_knjige uopste ima red za tu kombinaciju).")
        cur.close()
        conn.close()
        return

    print(f"{'knjiga_id':<10} {'knjiga':<38} {'jezik':<6} {'tip':<10} {'od':>6} {'do':>6} {'broj':>6}")
    print("-" * 90)

    ukupno_rupa = 0
    ukupno_prevedeno = 0
    broj_rupa_intervala = 0

    for knjiga_id, knjiga_naziv, jezik_kod in parovi:
        cur.execute(GAPS_SQL, {"knjiga": knjiga_id, "jezik": jezik_kod})
        redovi = cur.fetchall()
        naziv_kratak = (knjiga_naziv[:36] + "\u2026") if len(knjiga_naziv) > 37 else knjiga_naziv

        for ima_pobjednika, od, do, broj in redovi:
            tip = "prevedeno" if ima_pobjednika else "rupa"
            if ima_pobjednika:
                ukupno_prevedeno += broj
            else:
                ukupno_rupa += broj
                broj_rupa_intervala += 1
            print(f"{knjiga_id:<10} {naziv_kratak:<38} {jezik_kod:<6} {tip:<10} {od:>6} {do:>6} {broj:>6}")

    print("-" * 90)
    print(f"UKUPNO: prevedeno={ukupno_prevedeno}  rupa={ukupno_rupa}  "
          f"(broj rupa-intervala={broj_rupa_intervala}, broj (knjiga,jezik) parova={len(parovi)})")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
