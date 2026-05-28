#!/usr/bin/env python3
"""
Buchenberg · run_claude_test.py
Referentni test — prevod direktno Claude Sonnet 4.6 modelom.

Koristi Anthropic API za prevod EN → ciljni jezik i back-translation → EN.
Scoruje MiniLM-om i upisuje u test_results kao method='claude'.

Pokretanje:
  venv/bin/python src/run_claude_test.py --test_id test_claude_001 \
    --sent_from 1 --sent_to 40 --langs fr it pt
"""

import os
import sys
import argparse
import psycopg2
import anthropic
from dotenv import load_dotenv
from loguru import logger
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

EMBED_MODEL    = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CLAUDE_MODEL   = "claude-sonnet-4-6"
METHOD         = "claude"

LANG_NAMES = {
    "fr": "French",
    "it": "Italian",
    "pt": "Portuguese",
    "hr": "Croatian",
    "sr": "Serbian",
    "bs": "Bosnian",
    "sl": "Slovenian",
    "mk": "Macedonian",
    "bg": "Bulgarian",
    "de": "German",
    "nl": "Dutch",
    "af": "Afrikaans",
    "es": "Spanish",
    "ro": "Romanian",
}

def get_db_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

def load_sentences(conn, sent_from, sent_to, book_title="hound of the baskervilles"):
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.text
        FROM sentences s
        JOIN books b ON s.book_id = b.id
        WHERE b.title ILIKE %s AND s.id BETWEEN %s AND %s
        ORDER BY s.id
    """, (f"%{book_title}%", sent_from, sent_to))
    rows = cur.fetchall()
    cur.close()
    return rows

def translate_claude(client, text, tgt_lang_name):
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"Translate the following English text to {tgt_lang_name}. Output only the translation, nothing else.\n\n{text}"
        }]
    )
    return msg.content[0].text.strip()

def back_translate_claude(client, text, src_lang_name):
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"Translate the following {src_lang_name} text to English. Output only the translation, nothing else.\n\n{text}"
        }]
    )
    return msg.content[0].text.strip()

def upsert_result(conn, test_id, sentence_id, target_lang, method,
                  translated, back_trans, score_val, translation_score_val):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO test_results
            (test_id, sentence_id, target_lang, method,
             translated_text, back_translation, score, translation_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (test_id, sentence_id, target_lang, method)
        DO UPDATE SET
            translated_text   = EXCLUDED.translated_text,
            back_translation  = EXCLUDED.back_translation,
            score             = EXCLUDED.score,
            translation_score = EXCLUDED.translation_score,
            created_at        = NOW()
        WHERE EXCLUDED.translation_score > test_results.translation_score
    """, (test_id, sentence_id, target_lang, method,
          translated, back_trans, score_val, translation_score_val))
    conn.commit()
    cur.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_id",   required=True)
    parser.add_argument("--sent_from", type=int, default=1)
    parser.add_argument("--sent_to",   type=int, default=40)
    parser.add_argument("--langs",     nargs="+", required=True)
    args = parser.parse_args()

    logger.info(f"=== {args.test_id} CLAUDE TEST START ===")
    logger.info(f"langs={args.langs}, sent={args.sent_from}-{args.sent_to}, model={CLAUDE_MODEL}")

    client   = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    embedder = SentenceTransformer(EMBED_MODEL)
    conn     = get_db_conn()

    sentences = load_sentences(conn, args.sent_from, args.sent_to)
    logger.info(f"Rečenica učitano: {len(sentences)}")

    total = len(sentences) * len(args.langs)
    done  = 0

    for lang in args.langs:
        lang_name = LANG_NAMES.get(lang, lang)
        logger.info(f"--- {lang} ({lang_name}) ---")

        for sid, original in sentences:
            done += 1

            translated  = translate_claude(client, original, lang_name)
            back_trans  = back_translate_claude(client, translated, lang_name)

            emb_orig  = embedder.encode([original])
            emb_back  = embedder.encode([back_trans])
            emb_trans = embedder.encode([translated])

            score            = float(cosine_similarity(emb_orig, emb_back)[0][0])
            translation_score = float(cosine_similarity(emb_orig, emb_trans)[0][0])

            upsert_result(conn, args.test_id, sid, lang, METHOD,
                          translated, back_trans, score, translation_score)

            marker = "✓" if translation_score >= 0.90 else ("-" if translation_score >= 0.80 else "✗")
            logger.info(f"[{done}/{total}] {marker} s{sid} {lang} score={translation_score:.4f}")

    conn.close()
    logger.info(f"=== {args.test_id} CLAUDE TEST DONE ===")

if __name__ == "__main__":
    main()
