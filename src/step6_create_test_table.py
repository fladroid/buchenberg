#!/usr/bin/env python3
"""
Buchenberg · step6_create_test_table.py
Kreira tabelu test_results u bazi ako ne postoji.
Pokretanje: venv/bin/python src/step6_create_test_table.py
"""

import os
import psycopg2
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

LOG_FILE = os.path.join(os.getenv("BUCH_LOG", "logs"), "step6_create_test_table.log")
logger.add(LOG_FILE, rotation="10 MB", encoding="utf-8")

SQL = """
CREATE TABLE IF NOT EXISTS test_results (
    id               SERIAL PRIMARY KEY,
    test_id          VARCHAR(20) NOT NULL,
    sentence_id      INTEGER REFERENCES sentences(id),
    target_lang      CHAR(2) NOT NULL,
    method           VARCHAR(10) NOT NULL,
    translated_text  TEXT,
    back_translation TEXT,
    score            REAL,
    winner           BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE (test_id, sentence_id, target_lang, method)
);

CREATE INDEX IF NOT EXISTS idx_test_results_test_id
    ON test_results (test_id);

CREATE INDEX IF NOT EXISTS idx_test_results_lang
    ON test_results (test_id, target_lang);
"""


def main():
    logger.info("step6_create_test_table START")
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()
    cur.execute(SQL)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("step6_create_test_table DONE — tabela test_results kreirana")
    print("✓ Tabela test_results kreirana (ili već postoji)")


if __name__ == "__main__":
    main()
