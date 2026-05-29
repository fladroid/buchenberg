#!/usr/bin/env python3
"""
run_pivot.py — Cross-lingual pivot za poboljšanje HR prevoda.
Za svaku rečenicu gdje globalni pobjednik premašuje HR best score:
  1. Prevede EN→HR via gemma3, koristeći pobjednički prevod kao hint
  2. Izračuna novi HR score (MiniLM cosine EN vs novi HR)
  3. Loguje: stari score | novi score | poboljšanje?
  Bez upisa u bazu — samo log.

Upotreba:
    venv/bin/python src/run_pivot.py > logs/pivot_hr_002.log 2>&1
"""

import os
import psycopg2
import requests
import numpy as np
from dotenv import load_dotenv
from loguru import logger
from sentence_transformers import SentenceTransformer

load_dotenv()

OLLAMA_URL  = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY  = os.getenv("OLLAMA_API_KEY", "")
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = int(os.getenv("DB_PORT", 5432))
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

MODEL_TRANSLATE = "gemma3:12b"
MODEL_EMBED     = "paraphrase-multilingual-MiniLM-L12-v2"
TEMPERATURE     = 0.1

LANG_NAMES = {
    "it": "Italian",  "hr": "Croatian",   "de": "German",
    "fr": "French",   "pt": "Portuguese", "es": "Spanish",
    "nl": "Dutch",    "bg": "Bulgarian",  "sr": "Serbian",
    "bs": "Bosnian",  "sl": "Slovenian",  "mk": "Macedonian",
    "ro": "Romanian", "af": "Afrikaans",
}


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )


def fetch_pivot_candidates(conn):
    with conn.cursor() as cur:
        cur.execute("""
            WITH hr_best AS (
                SELECT DISTINCT ON (sentence_id)
                    sentence_id,
                    translation  AS hr_translation,
                    cosine_score AS hr_score
                FROM translation_scores
                WHERE target_lang = 'hr' AND embedder = 'minilm'
                ORDER BY sentence_id, cosine_score DESC
            )
            SELECT
                bt.sentence_id,
                bt.source_text,
                bt.target_lang   AS winner_lang,
                bt.translation   AS winner_text,
                bt.cosine_score  AS winner_score,
                h.hr_translation,
                h.hr_score
            FROM best_translation bt
            JOIN hr_best h ON h.sentence_id = bt.sentence_id
            WHERE bt.cosine_score > h.hr_score
            ORDER BY bt.sentence_id
        """)
        return cur.fetchall()


def ollama_call(prompt):
    payload = {
        "model":    MODEL_TRANSLATE,
        "messages": [{"role": "user", "content": prompt}],
        "stream":   False,
        "options":  {"temperature": TEMPERATURE},
    }
    r = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        json=payload,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def translate_to_hr(en_text, winner_text, winner_lang):
    winner_name = LANG_NAMES.get(winner_lang, winner_lang)
    prompt = (
        f"Translate the following English text to Croatian.\n"
        f"For reference, here is a high-quality {winner_name} translation: {winner_text}\n"
        f"Return ONLY the Croatian translation, nothing else.\n\n"
        f"English: {en_text}"
    )
    return ollama_call(prompt)


def cosine(v1, v2):
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def main():
    logger.info("=" * 62)
    logger.info("  run_pivot.py — Cross-lingual hint pivot HR")
    logger.info(f"  Model: {MODEL_TRANSLATE}  |  temp={TEMPERATURE}")
    logger.info("  Metoda: EN→HR + hint iz pobjedničkog prevoda")
    logger.info("=" * 62)

    conn = get_conn()
    candidates = fetch_pivot_candidates(conn)
    conn.close()
    logger.info(f"Kandidata: {len(candidates)} rečenica\n")

    logger.info("Učitavam MiniLM embedder...")
    embedder = SentenceTransformer(MODEL_EMBED)
    logger.info("MiniLM učitan.\n")

    improved = 0

    for row in candidates:
        sid, en_text, winner_lang, winner_text, winner_score, hr_old, hr_old_score = row

        logger.info(f"── s{sid} ────────────────────────────────────────")
        logger.info(f"  EN:          {en_text[:80]}")
        logger.info(f"  Hint [{winner_lang.upper()}]:   {winner_text[:80]}")
        logger.info(f"               score={float(winner_score):.4f}")
        logger.info(f"  HR stari:    {hr_old[:80]}")
        logger.info(f"               score={float(hr_old_score):.4f}")

        try:
            new_hr = translate_to_hr(en_text, winner_text, winner_lang)
        except Exception as e:
            logger.error(f"  Greška pri prevodu: {e}")
            continue

        vecs = embedder.encode([en_text, new_hr])
        new_score = round(cosine(vecs[0], vecs[1]), 4)
        delta = round(new_score - float(hr_old_score), 4)
        verdict = "✅ POBOLJŠANJE" if new_score > float(hr_old_score) else "❌ ZADRŽATI STARI"

        logger.info(f"  HR novi:     {new_hr[:80]}")
        logger.info(f"               score={new_score:.4f}  delta={delta:+.4f}  {verdict}")

        if new_score > float(hr_old_score):
            improved += 1

    logger.info("\n" + "=" * 62)
    logger.info(f"  Rezultat: {improved}/{len(candidates)} rečenica poboljšano")
    logger.info("=" * 62)


if __name__ == "__main__":
    main()
