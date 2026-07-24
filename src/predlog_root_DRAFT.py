#!/usr/bin/env python3
"""
Predlog sledeceg ROOT koraka (faza=1) — vraca (knjiga, jezik, od, do).
Ne pokrece nista, samo predlaze. Prati hijerarhiju grupa jezika.
Knjiga+jezik je pokrivena do pozicije N ako JE BILO KOJI model (root fazi)
preveo tu poziciju - nezavisno od toga koji je model u pitanju.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB = {
    "host": os.getenv("DB_HOST", "balsam.dynu.net"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": "bb",
    "user": os.getenv("DB_USER", "pgu"),
    "password": os.getenv("DB_PASSWORD"),
}

GRUPE = [
    ["de", "hr", "it", "sr"],
    ["bg", "bs", "mk", "sl"],
    ["es", "fr", "pt", "ro"],
    ["af", "nl"],
]
MAX_OPSEG = 200
FAZA = 1

def frontier(cur, knjiga_id, jezik_id, faza, total):
    cur.execute("""
        SELECT COALESCE(MIN(gs) - 1, %s)
        FROM generate_series(1, %s) gs
        LEFT JOIN (
            SELECT DISTINCT r.pozicija
            FROM bb_recenice r
            JOIN bb_prevodi_recenica pr ON pr.recenica_id = r.id
            JOIN bb_prevodi_knjige pk ON pk.id = pr.prevodi_knjige_id
            WHERE r.knjiga_id = %s AND pk.jezik_id = %s AND pk.faza_id = %s
        ) p ON p.pozicija = gs
        WHERE p.pozicija IS NULL
    """, (total, total, knjiga_id, jezik_id, faza))
    return cur.fetchone()[0]

def main():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute("SELECT id, naziv FROM bb_knjige ORDER BY id")
    knjige = cur.fetchall()
    cur.execute("SELECT id, kod FROM bb_jezik")
    jezik_map = {kod: jid for jid, kod in cur.fetchall()}
    cur.execute("SELECT knjiga_id, COUNT(*) FROM bb_recenice GROUP BY knjiga_id")
    ukupno_map = dict(cur.fetchall())

    for grupa in GRUPE:
        for knjiga_id, knjiga_naziv in knjige:
            total = ukupno_map.get(knjiga_id, 0)
            if total == 0:
                continue
            for jezik_kod in grupa:
                jezik_id = jezik_map.get(jezik_kod)
                if jezik_id is None:
                    continue
                n = frontier(cur, knjiga_id, jezik_id, FAZA, total)
                if n < total:
                    od, do = n + 1, min(n + MAX_OPSEG, total)
                    print(f"KK={knjiga_id} ({knjiga_naziv!r}) JJ={jezik_kod} "
                          f"OD={od} DO={do}  [frontier={n}/{total}]")
                    conn.close()
                    return
    conn.close()
    print("Nema predloga — sve grupe kompletne.")

if __name__ == "__main__":
    main()
