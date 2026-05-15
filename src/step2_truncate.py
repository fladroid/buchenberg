# Buchenberg · step2_truncate.py
# Tabula raza — briše sve podatke prije novog punjenja.

import os
import sys
from dotenv import load_dotenv
import psycopg2
from loguru import logger

# --- Logging ---
os.makedirs("logs", exist_ok=True)
logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", colorize=True)
logger.add("logs/step2_truncate.log", format="{time} {level} {message}", encoding="utf-8", enqueue=True)

# --- Konfiguracija ---
load_dotenv()

DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT", 5432)
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def main():
    logger.info("step2_truncate START")

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
        cur.execute("TRUNCATE books CASCADE;")
        logger.info("TRUNCATE books CASCADE — urađeno")
    except Exception as e:
        logger.error(f"Greška: {e}")
        cur.close()
        conn.close()
        sys.exit(1)

    cur.close()
    conn.close()
    logger.info("step2_truncate DONE")

if __name__ == "__main__":
    main()
