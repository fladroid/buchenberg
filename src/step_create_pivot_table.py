import os
import psycopg2
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

SQL = """
CREATE TABLE IF NOT EXISTS pivot_results (
    id                SERIAL PRIMARY KEY,
    test_id           VARCHAR(20) NOT NULL,
    sentence_id       INTEGER REFERENCES sentences(id),
    target_lang       CHAR(2) NOT NULL,
    model             VARCHAR(40),
    temperature       REAL,
    translated_text   TEXT,
    translation_score REAL,
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW(),
    UNIQUE (test_id, sentence_id, target_lang)
);
"""

def main():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute(SQL)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Tabela pivot_results kreirana (ili već postoji).")

if __name__ == "__main__":
    main()
