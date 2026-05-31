"""
bb_01_init_lookup.py
Puni lookup tabele: bb_jezik, bb_modeli, bb_embeddings
"""

import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB = {
    "host": os.getenv("DB_HOST", "balsam.dynu.net"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": "bb",
    "user": os.getenv("DB_USER", "pgu"),
    "password": os.getenv("DB_PASSWORD"),
}

JEZICI = [
    ("hrvatski",    "hr"),
    ("srpski",      "sr"),
    ("bosanski",    "bs"),
    ("slovenački",  "sl"),
    ("makedonski",  "mk"),
    ("bugarski",    "bg"),
    ("nemački",     "de"),
    ("holandski",   "nl"),
    ("afrikaans",   "af"),
    ("francuski",   "fr"),
    ("italijanski", "it"),
    ("španski",     "es"),
    ("portugalski", "pt"),
    ("rumunski",    "ro"),
]

MODELI = [
    ("gemma3:12b",         0.8),
    ("gemma3:12b",         0.5),
    ("ministral-3:14b",    0.8),
    ("ministral-3:14b",    0.5),
    ("nllb-600M",          0.0),
    ("claude-sonnet-4-6",  1.0),
    ("claude-sonnet-4-6",  0.5),
]

EMBEDDINGS = [
    "multilingual-e5-large",
    "paraphrase-multilingual-MiniLM-L12-v2",
]


def main():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    execute_values(cur,
        "INSERT INTO bb_jezik (naziv, kod) VALUES %s ON CONFLICT (kod) DO NOTHING",
        JEZICI
    )
    print(f"bb_jezik: {cur.rowcount} redova upisano")

    execute_values(cur,
        "INSERT INTO bb_modeli (naziv, temperatura) VALUES %s ON CONFLICT (naziv, temperatura) DO NOTHING",
        MODELI
    )
    print(f"bb_modeli: {cur.rowcount} redova upisano")

    execute_values(cur,
        "INSERT INTO bb_embeddings (naziv) VALUES %s ON CONFLICT (naziv) DO NOTHING",
        [(e,) for e in EMBEDDINGS]
    )
    print(f"bb_embeddings: {cur.rowcount} redova upisano")

    conn.commit()
    cur.close()
    conn.close()
    print("Gotovo.")


if __name__ == "__main__":
    main()
