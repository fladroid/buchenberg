"""
bb_sr_fix_backtr.py
Vraća back_translation srpskih prevoda iz ćirilice u latinicu.

back_translation je engleski tekst koji je greškom transliteriran
u ćirilicu od strane bb_sr_cirilica.py. Ovaj skript primjenjuje
reverz tablicu — ćirilica → latinica — isključivo na back_translation kolonu.
prevod kolona se NE dira.

Primjer:
    venv/bin/python src/bb_sr_fix_backtr.py --knjiga 1 --dry-run
    venv/bin/python src/bb_sr_fix_backtr.py --knjiga 1
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

# Reverz tablica: ćirilica → latinica
# Digrame PRVO (redosljed je bitan!)
CIR_LAT = [
    ("љ", "lj"), ("Љ", "Lj"),
    ("њ", "nj"), ("Њ", "Nj"),
    ("џ", "dž"), ("Џ", "Dž"),
    ("ђ", "dj"), ("Ђ", "Dj"),
    ("ш", "š"),  ("Ш", "Š"),
    ("ж", "ž"),  ("Ж", "Ž"),
    ("ч", "č"),  ("Ч", "Č"),
    ("ћ", "ć"),  ("Ћ", "Ć"),
    ("а", "a"),  ("А", "A"),
    ("б", "b"),  ("Б", "B"),
    ("ц", "c"),  ("Ц", "C"),
    ("д", "d"),  ("Д", "D"),
    ("е", "e"),  ("Е", "E"),
    ("ф", "f"),  ("Ф", "F"),
    ("г", "g"),  ("Г", "G"),
    ("х", "h"),  ("Х", "H"),
    ("и", "i"),  ("И", "I"),
    ("ј", "j"),  ("Ј", "J"),
    ("к", "k"),  ("К", "K"),
    ("л", "l"),  ("Л", "L"),
    ("м", "m"),  ("М", "M"),
    ("н", "n"),  ("Н", "N"),
    ("о", "o"),  ("О", "O"),
    ("п", "p"),  ("П", "P"),
    ("р", "r"),  ("Р", "R"),
    ("с", "s"),  ("С", "S"),
    ("т", "t"),  ("Т", "T"),
    ("у", "u"),  ("У", "U"),
    ("в", "v"),  ("В", "V"),
    ("з", "z"),  ("З", "Z"),
]

CIR_PATTERN = re.compile(r'[\u0400-\u04FF]')
LAT_ALPHA   = re.compile(r'[a-zA-ZšŠžŽčČćĆđĐ]')


def is_cirilica(text):
    """Vraća True ako tekst ima više ćiriličnih nego latiničnih slova."""
    cir = len(CIR_PATTERN.findall(text))
    lat = len(LAT_ALPHA.findall(text))
    return cir > lat


def reverziraj(text):
    """Konvertira ćirilicu u latinicu. Tekst koji nije ćirilica ostaje."""
    if not text:
        return text
    if not is_cirilica(text):
        return text  # već latinica, ne diraj
    result = text
    for cir, lat in CIR_LAT:
        result = result.replace(cir, lat)
    return result


def main():
    import functools
    global print
    print = functools.partial(print, flush=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--knjiga", type=int, required=True,
                        help="ID knjige (bb_knjige.id)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Samo prikaži prvih 10 primjera, ne upisuj u bazu")
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    # Provjeri da knjiga postoji
    cur.execute("SELECT naziv FROM bb_knjige WHERE id = %s", (args.knjiga,))
    row = cur.fetchone()
    if not row:
        print(f"Greška: knjiga s ID={args.knjiga} ne postoji u bazi.")
        return
    naziv_knjige = row[0]
    print(f"Knjiga: [{args.knjiga}] {naziv_knjige}")

    # Dohvati sve srpske back_translation za ovu knjigu
    cur.execute("""
        SELECT pr.id, pr.back_translation
        FROM bb_prevodi_recenica pr
        JOIN bb_prevodi_knjige pk ON pk.id = pr.prevodi_knjige_id
        JOIN bb_jezik j ON j.id = pk.jezik_id
        WHERE j.kod = 'sr'
          AND pk.knjiga_id = %s
          AND pr.back_translation IS NOT NULL
        ORDER BY pr.id
    """, (args.knjiga,))
    rows = cur.fetchall()
    print(f"Pronađeno {len(rows)} srpskih back_translation redova.")

    izmjena = 0
    primjeri = 0

    for row_id, back_tr in rows:
        novi_back = reverziraj(back_tr)

        if novi_back == back_tr:
            continue  # nije se promijenilo (već latinica)

        izmjena += 1

        if args.dry_run:
            if primjeri < 10:
                print(f"\n  ID {row_id}:")
                print(f"    PRIJE:  {back_tr[:80]}")
                print(f"    POSLIJE: {novi_back[:80]}")
                primjeri += 1
            continue

        cur.execute("""
            UPDATE bb_prevodi_recenica
            SET back_translation = %s
            WHERE id = %s
        """, (novi_back, row_id))

    if args.dry_run:
        print(f"\nDry-run: {izmjena} redova bi bilo izmijenjeno.")
        print("Pokreni bez --dry-run da upišeš u bazu.")
    else:
        conn.commit()
        print(f"Ažurirano: {izmjena} redova → latinica.")

    cur.close()
    conn.close()
    print("Gotovo.")


if __name__ == "__main__":
    main()
