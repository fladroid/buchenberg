# Buchenberg · step3_insert_book.py
# INSERT knjiga u books tabelu.

import os
import sys
from dotenv import load_dotenv
import psycopg2
from loguru import logger

# --- Logging ---
os.makedirs("logs", exist_ok=True)
logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", colorize=True)
logger.add("logs/step3_insert_book.log", format="{time} {level} {message}", encoding="utf-8", enqueue=True)

# --- Konfiguracija ---
load_dotenv()

DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT", 5432)
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# --- Knjige za insert ---
BOOKS = [
    {
        "gutenberg_id": 3070,
        "title":        "The Hound of the Baskervilles",
        "author":       "Arthur Conan Doyle",
        "language":     "en",
        "html_path":    "/home/balsam/buchenberg/books/hound_of_the_baskervilles/raw/hound.html",
    },
    {
        "gutenberg_id": 84,
        "title":        "Frankenstein",
        "author":       "Mary Wollstonecraft Shelley",
        "language":     "en",
        "html_path":    "/home/balsam/buchenberg/books/frankenstein/raw/frankenstein.html",
    },
    {
        "gutenberg_id": 61262,
        "title":        "Poirot Investigates",
        "author":       "Agatha Christie",
        "language":     "en",
        "html_path":    "/home/balsam/buchenberg/books/poirot_investigates/raw/poirot_investigates.html",
    },
]

# --- Main ---
def main():
    logger.info("step3_insert_book START")

    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD
        )
        conn.autocommit = False
        cur = conn.cursor()
        logger.info(f"Konekcija na bazu: {DB_HOST}/{DB_NAME}")
    except Exception as e:
        logger.error(f"Konekcija neuspješna: {e}")
        sys.exit(1)

    inserted = 0
    for book in BOOKS:
        try:
            cur.execute("""
                INSERT INTO books (gutenberg_id, title, author, language, html_path, status)
                VALUES (%s, %s, %s, %s, %s, 'downloaded')
            """, (
                book["gutenberg_id"],
                book["title"],
                book["author"],
                book["language"],
                book["html_path"],
            ))
            logger.info(f"INSERT: [{book['gutenberg_id']}] {book['title']}")
            inserted += 1
        except Exception as e:
            logger.error(f"Greška pri insertu [{book['gutenberg_id']}]: {e}")
            conn.rollback()
            cur.close()
            conn.close()
            sys.exit(1)

    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"step3_insert_book DONE — upisano knjiga: {inserted}")

if __name__ == "__main__":
    main()
