"""
bb_02_insert_knjiga.py
Ubacuje knjgu u bb_knjige i parsira rečenice u bb_recenice.
"""

import os
import re
import sys
import psycopg2
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import spacy

load_dotenv()

DB = {
    "host":     os.getenv("DB_HOST", "balsam.dynu.net"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   "bb",
    "user":     os.getenv("DB_USER", "pgu"),
    "password": os.getenv("DB_PASSWORD"),
}

KNJIGE = [
    {
        "naziv":        "The Hound of the Baskervilles",
        "autor":        "Arthur Conan Doyle",
        "gutenberg_id": "2852",
        "html":         "books/hound_of_the_baskervilles/raw/hound.html",
    },
]

TOC_TITLES = {"CONTENTS", "TABLE OF CONTENTS"}


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def parse_sentences(html_path, nlp):
    """Parsira HTML → lista rečenica (stringovi)."""
    content = open(html_path, encoding="utf-8", errors="ignore").read()
    soup = BeautifulSoup(content, "html.parser")

    for div_id in ("pg-header", "pg-footer"):
        tag = soup.find(id=div_id)
        if tag:
            tag.decompose()

    elementi = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"])

    recenice = []
    toc_skip = False

    for el in elementi:
        tag   = el.name.lower()
        tekst = normalize(el.get_text())

        if not tekst:
            continue

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if tekst.upper() in TOC_TITLES:
                toc_skip = True
                continue
            toc_skip = False
            recenice.append(tekst)
            continue

        if toc_skip:
            continue

        doc = nlp(tekst)
        for sent in doc.sents:
            s = normalize(sent.text)
            if s:
                recenice.append(s)

    return recenice


def main():
    nlp  = spacy.load("en_core_web_sm")
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    for knjiga in KNJIGE:
        # Upiši knjigu
        cur.execute("""
            INSERT INTO bb_knjige (naziv, autor, gutenberg_id)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (knjiga["naziv"], knjiga["autor"], knjiga["gutenberg_id"]))

        row = cur.fetchone()
        if row:
            knjiga_id = row[0]
            print(f"Nova knjiga id={knjiga_id}: {knjiga['naziv']}")
        else:
            cur.execute("SELECT id FROM bb_knjige WHERE gutenberg_id = %s", (knjiga["gutenberg_id"],))
            knjiga_id = cur.fetchone()[0]
            print(f"Knjiga već postoji id={knjiga_id}: {knjiga['naziv']}")

        # Provjeri postoje li već rečenice
        cur.execute("SELECT COUNT(*) FROM bb_recenice WHERE knjiga_id = %s", (knjiga_id,))
        count = cur.fetchone()[0]
        if count > 0:
            print(f"  Rečenice već postoje ({count}), preskačem.")
            continue

        # Parsiraj i upiši
        recenice = parse_sentences(knjiga["html"], nlp)
        print(f"  Parsirano: {len(recenice)} rečenica")

        for pozicija, tekst in enumerate(recenice, start=1):
            cur.execute("""
                INSERT INTO bb_recenice (knjiga_id, pozicija, tekst)
                VALUES (%s, %s, %s)
                ON CONFLICT (knjiga_id, pozicija) DO NOTHING
            """, (knjiga_id, pozicija, tekst))

        conn.commit()
        print(f"  Upisano: {len(recenice)} rečenica")

    cur.close()
    conn.close()
    print("Gotovo.")


if __name__ == "__main__":
    main()
