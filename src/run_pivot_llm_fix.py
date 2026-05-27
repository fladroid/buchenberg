#!/usr/bin/env python3
"""
Buchenberg · run_pivot_llm_fix.py
LLM "kritički" popravak crvenih rečenica iz pivot_results.

Za svaku crvenu rečenicu (score < 0.80) poziva Ollama LLM s promptom
koji sadrži EN original + postojeći loš prevod. Ako novi prevod ima
bolji score — upisuje u pivot_results.

Pokretanje:
  venv/bin/python src/run_pivot_llm_fix.py
"""

import os
import time
import requests
import psycopg2
import yaml
from dotenv import load_dotenv
from loguru import logger
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

PIVOT_PATH  = os.path.join(os.getenv("BUCH_HOME", "."), "tests", "pivot.yaml")
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_URL  = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY  = os.getenv("OLLAMA_API_KEY", "")
TEMPERATURE = 0.5
RED_THRESHOLD = 0.80

LANG_NAMES = {
    "sr": "Serbian", "hr": "Croatian", "sl": "Slovenian",
    "bs": "Bosnian", "mk": "Macedonian", "bg": "Bulgarian",
    "de": "German", "nl": "Dutch", "af": "Afrikaans",
    "fr": "French", "it": "Italian", "es": "Spanish",
    "pt": "Portuguese", "ro": "Romanian",
}

def load_pivot():
    with open(PIVOT_PATH, "r") as f:
        return yaml.safe_load(f) or {}

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

def load_embedder():
    logger.info(f"Učitavanje embedding modela: {EMBED_MODEL}")
    return SentenceTransformer(EMBED_MODEL, local_files_only=True)

def score_translation(original, translation, embedder):
    enc_orig  = embedder.encode([original])
    enc_trans = embedder.encode([translation])
    return float(cosine_similarity(enc_orig, enc_trans)[0][0])

def ollama_translate(model, prompt):
    resp = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": TEMPERATURE},
            "stream": False,
        },
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()

def build_prompt(en_text, bad_translation, lang_name):
    return (
        f"You are a professional translator.\n"
        f"Translate the following English sentence to {lang_name}.\n\n"
        f"Original: \"{en_text}\"\n"
        f"Previous translation (poor quality): \"{bad_translation}\"\n\n"
        f"Provide only the translation, no explanation."
    )

def get_red_sentences(conn, test_id, langs):
    cur = conn.cursor()
    cur.execute("""
        SELECT pr.sentence_id, pr.target_lang, pr.model,
               pr.translated_text, pr.translation_score,
               s.text
        FROM pivot_results pr
        JOIN sentences s ON s.id = pr.sentence_id
        WHERE pr.test_id = %s
          AND pr.target_lang = ANY(%s)
          AND pr.translation_score < %s
        ORDER BY pr.target_lang, pr.sentence_id
    """, (test_id, langs, RED_THRESHOLD))
    return cur.fetchall()

def upsert_result(conn, test_id, sentence_id, target_lang, model,
                  translated_text, score):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pivot_results
            (test_id, sentence_id, target_lang, model, temperature,
             translated_text, translation_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (test_id, sentence_id, target_lang)
        DO UPDATE SET
            translated_text  = EXCLUDED.translated_text,
            translation_score = EXCLUDED.translation_score,
            model            = EXCLUDED.model,
            temperature      = EXCLUDED.temperature,
            updated_at       = NOW()
        WHERE EXCLUDED.translation_score > pivot_results.translation_score
    """, (test_id, sentence_id, target_lang, model, TEMPERATURE,
          translated_text, score))
    conn.commit()

def main():
    params   = load_pivot()
    test_id  = params["test_id"]
    langs    = params["langs"]
    models   = params.get("llm_models", ["gemma3:12b", "ministral-3:14b", "gemma4:31b"])

    logger.info(f"=== {test_id} LLM FIX START ===")
    logger.info(f"langs={langs}, models={models}, temp={TEMPERATURE}")

    embedder = load_embedder()
    conn     = get_conn()

    red_sentences = get_red_sentences(conn, test_id, langs)
    logger.info(f"Crvenih rečenica: {len(red_sentences)}")

    total    = len(red_sentences) * len(models)
    done     = 0
    improved = 0

    for model in models:
        logger.info(f"--- Model: {model} ---")
        for sent_id, lang, old_model, old_trans, old_score, en_text in red_sentences:
            done += 1
            lang_name = LANG_NAMES.get(lang, lang)
            prompt    = build_prompt(en_text, old_trans, lang_name)

            try:
                new_trans = ollama_translate(model, prompt)
                new_score = score_translation(en_text, new_trans, embedder)

                status = "✓" if new_score > old_score else "-"
                logger.info(
                    f"[{done}/{total}] {status} s{sent_id} {lang} "
                    f"old={old_score:.4f} new={new_score:.4f} [{model}]"
                )

                upsert_result(conn, test_id, sent_id, lang, model,
                              new_trans, new_score)
                if new_score > old_score:
                    improved += 1

            except Exception as e:
                logger.error(f"[{done}/{total}] GREŠKA s{sent_id} {lang} {model}: {e}")

    logger.info(f"=== {test_id} LLM FIX DONE — poboljšano {improved}/{len(red_sentences)*len(models)} ===")
    conn.close()

if __name__ == "__main__":
    main()
