# Buchenberg · step1_create_tables.py
# Kreira tabele u PostgreSQL bazi. Bezbjedan za ponovljeni run.

import os
import sys
from dotenv import load_dotenv
import psycopg2
from loguru import logger

# --- Logging ---
os.makedirs("logs", exist_ok=True)
logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", colorize=True)
logger.add("logs/step1_create_tables.log", format="{time} {level} {message}", encoding="utf-8", enqueue=True)

# --- Konfiguracija ---
load_dotenv()

DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT", 5432)
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS books (
    id            SERIAL PRIMARY KEY,
    gutenberg_id  INTEGER UNIQUE NOT NULL,
    title         VARCHAR(500) NOT NULL,
    author        VARCHAR(300) NOT NULL,
    language      CHAR(2) NOT NULL DEFAULT 'en',
    html_path     TEXT,
    downloaded_at TIMESTAMP DEFAULT NOW(),
    status        VARCHAR(20) DEFAULT 'downloaded'
);

CREATE TABLE IF NOT EXISTS sentences (
    id              SERIAL PRIMARY KEY,
    book_id         INTEGER NOT NULL REFERENCES books(id),
    block_no        INTEGER NOT NULL,
    sentence_no     INTEGER NOT NULL,
    text            TEXT NOT NULL,
    word_count      SMALLINT NOT NULL,
    sentence_type   VARCHAR(10) NOT NULL DEFAULT 'text',
    sentiment_label VARCHAR(10),
    sentiment_score REAL,
    UNIQUE (book_id, block_no, sentence_no)
);

CREATE TABLE IF NOT EXISTS translations (
    id               SERIAL PRIMARY KEY,
    sentence_id      INTEGER NOT NULL REFERENCES sentences(id),
    target_lang      CHAR(2) NOT NULL,
    method           VARCHAR(10) NOT NULL,
    translated_text  TEXT NOT NULL,
    back_translation TEXT,
    score            REAL,
    winner           BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE (sentence_id, target_lang, method)
);

CREATE TABLE IF NOT EXISTS embeddings (
    id          SERIAL PRIMARY KEY,
    sentence_id INTEGER NOT NULL REFERENCES sentences(id),
    vector      vector(384) NOT NULL,
    model       VARCHAR(100) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (sentence_id, model)
);

CREATE TABLE IF NOT EXISTS named_entities (
    id          SERIAL PRIMARY KEY,
    sentence_id INTEGER NOT NULL REFERENCES sentences(id),
    text        VARCHAR(300) NOT NULL,
    label       VARCHAR(10) NOT NULL,
    start_char  SMALLINT NOT NULL,
    end_char    SMALLINT NOT NULL
);
"""

def main():
    logger.info("step1_create_tables START")

    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD
        )
        conn.autocommit = True
        cur = conn.cursor()
        logger.info(f"Konekcija: {DB_HOST}/{DB_NAME}")
    except Exception as e:
        logger.error(f"Konekcija neuspješna: {e}")
        sys.exit(1)

    try:
        cur.execute(SQL)
        logger.info("Tabele kreirane (IF NOT EXISTS)")
    except Exception as e:
        logger.error(f"Greška: {e}")
        cur.close()
        conn.close()
        sys.exit(1)

    cur.close()
    conn.close()
    logger.info("step1_create_tables DONE")

if __name__ == "__main__":
    main()
