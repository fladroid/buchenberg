#!/usr/bin/env python3
"""
Buchenberg · step7_create_ga_table.py
Kreira ga_results tabelu i indekse.
Idempotentno — može se pokrenuti više puta (DROP IF EXISTS + CREATE).
"""

import os
import psycopg2
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

SQL = """
DROP TABLE IF EXISTS ga_results;

CREATE TABLE ga_results (
    id            SERIAL PRIMARY KEY,
    sentence_id   INTEGER REFERENCES sentences(id),
    target_lang   CHAR(2) NOT NULL,
    generation    INTEGER NOT NULL,
    individua_id  INTEGER NOT NULL,
    tekst         TEXT NOT NULL,
    fitness       REAL NOT NULL,
    pivot_lang    CHAR(2),
    metoda        VARCHAR(20),
    je_elita      BOOLEAN DEFAULT FALSE,
    je_pobjednik  BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ga_sentence   ON ga_results(sentence_id, target_lang);
CREATE INDEX idx_ga_generation ON ga_results(sentence_id, target_lang, generation);
"""

def main():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()
    cur.execute(SQL)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("ga_results tabela kreirana.")

if __name__ == "__main__":
    main()
