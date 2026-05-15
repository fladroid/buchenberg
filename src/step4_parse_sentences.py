# Buchenberg · step4_parse_sentences.py
# Parsira HTML knjiga → INSERT u sentences tabelu.

import os
import sys
import re
from dotenv import load_dotenv
import psycopg2
from bs4 import BeautifulSoup
import spacy
from loguru import logger
from tqdm import tqdm

# --- Logging ---
os.makedirs("logs", exist_ok=True)
logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", colorize=True)
logger.add("logs/step4_parse_sentences.log", format="{time} {level} {message}", encoding="utf-8", enqueue=True)

# --- Konfiguracija ---
load_dotenv()

DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT", 5432)
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

TOC_TITLES = {'CONTENTS', 'TABLE OF CONTENTS'}

# --- Helpers ---

def normalize(text):
    """Strip višestrukih razmaka i newlineova."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_book(html_path, book_id, cur, nlp):
    """Parsira jedan HTML fajl i upisuje rečenice u bazu."""
    logger.info(f"Parsiranje: {html_path}")

    content = open(html_path, encoding='utf-8', errors='ignore').read()
    soup = BeautifulSoup(content, 'html.parser')

    # Ukloni pg-header i pg-footer
    for div_id in ('pg-header', 'pg-footer'):
        tag = soup.find(id=div_id)
        if tag:
            tag.decompose()
            logger.info(f"  Uklonjen: #{div_id}")

    # Izvuci sve H i P elemente redom
    elementi = soup.find_all(['h1','h2','h3','h4','h5','h6','p'])
    logger.info(f"  Elemenata za obradu: {len(elementi)}")

    block_no  = 0
    skipped   = 0
    toc_skip  = False
    rows      = []

    for el in elementi:
        tag   = el.name.lower()
        tekst = normalize(el.get_text())

        if not tekst:
            skipped += 1
            continue

        # H tag
        if tag in ('h1','h2','h3','h4','h5','h6'):

            # TOC — preskoči i aktiviraj skip mod
            if tekst.upper() in TOC_TITLES:
                toc_skip = True
                skipped += 1
                logger.debug(f"  TOC heading preskočen: '{tekst}'")
                continue

            toc_skip = False
            block_no += 1
            rows.append((
                book_id, block_no, 1, tekst,
                len(tekst.split()), 'heading'
            ))

        # P tag
        elif tag == 'p':

            if toc_skip:
                skipped += 1
                continue

            recenice = [s.text.strip() for s in nlp(tekst).sents]
            recenice = [r for r in recenice if r]

            if not recenice:
                skipped += 1
                continue

            block_no += 1
            for sent_no, recenica in enumerate(recenice, start=1):
                recenica = normalize(recenica)
                if not recenica:
                    continue
                rows.append((
                    book_id, block_no, sent_no, recenica,
                    len(recenica.split()), 'text'
                ))

    # Batch insert
    logger.info(f"  Batch insert: {len(rows)} rečenica...")
    cur.executemany("""
        INSERT INTO sentences (book_id, block_no, sentence_no, text, word_count, sentence_type)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, rows)

    logger.info(f"  Upisano: {len(rows)} | Preskočeno elemenata: {skipped}")
    return len(rows)

# --- Main ---
def main():
    logger.info("step4_parse_sentences START")

    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD
        )
        conn.autocommit = False
        cur = conn.cursor()
        logger.info(f"Konekcija: {DB_HOST}/{DB_NAME}")
    except Exception as e:
        logger.error(f"Konekcija neuspješna: {e}")
        sys.exit(1)

    logger.info("Učitavanje spaCy modela...")
    nlp = spacy.load('en_core_web_sm')
    logger.info("spaCy ok")

    cur.execute("SELECT id, title, html_path FROM books WHERE status = 'downloaded' ORDER BY id")
    books = cur.fetchall()
    logger.info(f"Knjiga za parsiranje: {len(books)}")

    if not books:
        logger.warning("Nema knjiga sa statusom 'downloaded'. Izlaz.")
        cur.close()
        conn.close()
        sys.exit(0)

    total = 0
    for book_id, title, html_path in tqdm(books, desc="Knjige"):
        logger.info(f"--- [{book_id}] {title} ---")
        try:
            n = parse_book(html_path, book_id, cur, nlp)
            cur.execute("UPDATE books SET status = 'parsed' WHERE id = %s", (book_id,))
            conn.commit()
            total += n
            logger.info(f"  [{book_id}] {title} → DONE ({n} rečenica)")
        except Exception as e:
            logger.error(f"  [{book_id}] {title} → GREŠKA: {e}")
            conn.rollback()
            cur.close()
            conn.close()
            sys.exit(1)

    cur.close()
    conn.close()
    logger.info(f"step4_parse_sentences DONE — ukupno rečenica: {total}")

if __name__ == "__main__":
    main()
