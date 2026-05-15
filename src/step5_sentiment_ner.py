#!/usr/bin/env python3
"""
Buchenberg · step5_sentiment_ner.py
Sentiment analiza (VADER/NLTK) + NER (spaCy) za sve rečenice u bazi.
Popunjava:
  - sentences.sentiment_label, sentences.sentiment_score
  - named_entities tabelu
Pokretanje: venv/bin/python src/step5_sentiment_ner.py
"""

import os
import psycopg2
from dotenv import load_dotenv
import spacy
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from tqdm import tqdm
from loguru import logger

# ── Setup ────────────────────────────────────────────────────────────────────

load_dotenv()

LOG_FILE = os.path.join(os.getenv("BUCH_LOG", "logs"), "step5_sentiment_ner.log")
logger.add(LOG_FILE, rotation="10 MB", encoding="utf-8")

BATCH_SIZE = 500  # rečenica po batch-u

# ── VADER threshold-i ─────────────────────────────────────────────────────────

VADER_POS =  0.05
VADER_NEG = -0.05


def compound_to_label(compound: float) -> str:
    if compound >= VADER_POS:
        return "positive"
    elif compound <= VADER_NEG:
        return "negative"
    else:
        return "neutral"


# ── DB konekcija ──────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


# ── Učitavanje rečenica ───────────────────────────────────────────────────────

def load_sentences(conn):
    """Vraća sve rečenice koje još nemaju sentiment."""
    cur = conn.cursor()
    cur.execute("""
        SELECT id, text
        FROM sentences
        WHERE sentiment_label IS NULL
        ORDER BY id
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


# ── Sentiment ─────────────────────────────────────────────────────────────────

def update_sentiment_batch(conn, batch: list):
    """
    batch: lista (sentence_id, label, score)
    """
    cur = conn.cursor()
    cur.executemany("""
        UPDATE sentences
        SET sentiment_label = %s,
            sentiment_score = %s
        WHERE id = %s
    """, [(label, score, sid) for sid, label, score in batch])
    conn.commit()
    cur.close()


# ── NER ───────────────────────────────────────────────────────────────────────

def insert_entities_batch(conn, entities: list):
    """
    entities: lista (sentence_id, text, label, start_char, end_char)
    """
    if not entities:
        return
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO named_entities (sentence_id, text, label, start_char, end_char)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, entities)
    conn.commit()
    cur.close()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    logger.info("step5_sentiment_ner START")

    # Inicijalizacija alata
    logger.info("Učitavanje spaCy modela...")
    nlp = spacy.load("en_core_web_sm")

    logger.info("Učitavanje VADER lexicona...")
    nltk.download("vader_lexicon", quiet=True)
    sia = SentimentIntensityAnalyzer()

    conn = get_conn()
    sentences = load_sentences(conn)
    total = len(sentences)
    logger.info(f"Rečenica za obradu: {total}")

    if total == 0:
        logger.info("Sve rečenice već imaju sentiment. Izlaz.")
        conn.close()
        return

    sentiment_batch = []
    entities_batch  = []
    processed       = 0
    ner_total       = 0

    for sid, text in tqdm(sentences, desc="Obrada", unit="rec"):
        # ── Sentiment ────────────────────────────────────────────
        scores   = sia.polarity_scores(text)
        compound = scores["compound"]
        label    = compound_to_label(compound)
        score    = round(abs(compound), 4)
        sentiment_batch.append((sid, label, score))

        # ── NER ──────────────────────────────────────────────────
        doc = nlp(text)
        for ent in doc.ents:
            entities_batch.append((
                sid,
                ent.text[:300],
                ent.label_[:10],
                ent.start_char,
                ent.end_char,
            ))

        processed += 1

        # Flush po batch-u
        if processed % BATCH_SIZE == 0:
            update_sentiment_batch(conn, sentiment_batch)
            insert_entities_batch(conn, entities_batch)
            ner_total += len(entities_batch)
            logger.info(f"  {processed}/{total} obrađeno | entiteta u batchu: {len(entities_batch)}")
            sentiment_batch = []
            entities_batch  = []

    # Ostatak
    if sentiment_batch:
        update_sentiment_batch(conn, sentiment_batch)
        insert_entities_batch(conn, entities_batch)
        ner_total += len(entities_batch)

    conn.close()

    logger.info(f"step5_sentiment_ner DONE — {processed} rečenica, {ner_total} entiteta")
    print(f"\n✓ Obrađeno: {processed} rečenica | Entiteta: {ner_total}")


if __name__ == "__main__":
    main()
