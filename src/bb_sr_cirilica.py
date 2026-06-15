"""
bb_sr_cirilica.py
Transliterira sve srpske prevode u bb_prevodi_recenica iz latinice u ćirilicu.
Idempotentna — tekst koji je već ćirilica ostaje nepromijenjen.

Primjer:
    venv/bin/python src/bb_sr_cirilica.py --dry-run   # samo provjera, bez upisa
    venv/bin/python src/bb_sr_cirilica.py              # upis u bazu
"""

import os
import re
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

# Srpska latinica → ćirilica
# Digrame prvo (redosljed je bitan!)
LAT_CIR = [
    ("lj", "љ"), ("Lj", "Љ"), ("LJ", "Љ"),
    ("nj", "њ"), ("Nj", "Њ"), ("NJ", "Њ"),
    ("dž", "џ"), ("Dž", "Џ"), ("DŽ", "Џ"),
    ("dj", "ђ"), ("Dj", "Ђ"), ("DJ", "Ђ"),
    ("đ",  "ђ"), ("Đ",  "Ђ"),
    ("š",  "ш"), ("Š",  "Ш"),
    ("ž",  "ж"), ("Ž",  "Ж"),
    ("č",  "ч"), ("Č",  "Ч"),
    ("ć",  "ћ"), ("Ć",  "Ћ"),
    ("a",  "а"), ("A",  "А"),
    ("b",  "б"), ("B",  "Б"),
    ("c",  "ц"), ("C",  "Ц"),
    ("d",  "д"), ("D",  "Д"),
    ("e",  "е"), ("E",  "Е"),
    ("f",  "ф"), ("F",  "Ф"),
    ("g",  "г"), ("G",  "Г"),
    ("h",  "х"), ("H",  "Х"),
    ("i",  "и"), ("I",  "И"),
    ("j",  "ј"), ("J",  "Ј"),
    ("k",  "к"), ("K",  "К"),
    ("l",  "л"), ("L",  "Л"),
    ("m",  "м"), ("M",  "М"),
    ("n",  "н"), ("N",  "Н"),
    ("o",  "о"), ("O",  "О"),
    ("p",  "п"), ("P",  "П"),
    ("r",  "р"), ("R",  "Р"),
    ("s",  "с"), ("S",  "С"),
    ("t",  "т"), ("T",  "Т"),
    ("u",  "у"), ("U",  "У"),
    ("v",  "в"), ("V",  "В"),
    ("z",  "з"), ("Z",  "З"),
]

# Ćirilični Unicode raspon — za detekciju je li tekst već ćirilica
CIR_PATTERN = re.compile(r'[\u0400-\u04FF]')
LAT_ALPHA    = re.compile(r'[a-zA-ZšŠžŽčČćĆđĐ]')


def is_cirilica(text):
    """Vraća True ako tekst ima više ćiriličnih nego latiničnih slova."""
    cir = len(CIR_PATTERN.findall(text))
    lat = len(LAT_ALPHA.findall(text))
    return cir >= lat


def transliteriraj(text):
    """Konvertira srpsku latinicu u ćirilicu. Tekst već u ćirilici ostaje."""
    if not text:
        return text
    if is_cirilica(text):
        return text  # već ćirilica, ne diraj

    result = text
    for lat, cir in LAT_CIR:
        result = result.replace(lat, cir)
    return result


def main():
    import functools
    global print
    print = functools.partial(print, flush=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Samo prikaži prvih 10 primjera, ne upisuj u bazu")
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    # Dohvati sve srpske prevode (samo prevod — back_translation se ne dira)
    cur.execute("""
        SELECT pr.id, pr.prevod
        FROM bb_prevodi_recenica pr
        JOIN bb_prevodi_knjige ppk ON ppk.id = pr.prevodi_knjige_id
        JOIN bb_jezik j ON j.id = ppk.jezik_id
        WHERE j.kod = 'sr'
          AND pr.prevod IS NOT NULL
        ORDER BY pr.id
    """)
    rows = cur.fetchall()
    print(f"Pronađeno {len(rows)} srpskih prevoda.")

    izmjena = 0
    primjeri = 0

    for row_id, prevod in rows:
        novi_prevod = transliteriraj(prevod)

        if novi_prevod == prevod:
            continue  # nije se promijenilo

        izmjena += 1

        if args.dry_run and primjeri < 10:
            print(f"\n  ID {row_id}:")
            print(f"    PRIJE: {prevod[:80]}")
            print(f"    POSLJE: {novi_prevod[:80]}")
            primjeri += 1
            continue

        if not args.dry_run:
            cur.execute("""
                UPDATE bb_prevodi_recenica
                SET prevod = %s
                WHERE id = %s
            """, (novi_prevod, row_id))

    if args.dry_run:
        print(f"\nDry-run: {izmjena} prevoda bi bilo izmijenjeno.")
        print("Pokreni bez --dry-run da upišeš u bazu.")
    else:
        conn.commit()
        print(f"Ažurirano: {izmjena} prevoda → ćirilica.")

    cur.close()
    conn.close()
    print("Gotovo.")


if __name__ == "__main__":
    main()
