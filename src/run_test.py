#!/usr/bin/env python3
"""
Buchenberg · run_test.py
Glavni test runner — prevod + back-translation + scoring.

Registracija (prvi put):
  venv/bin/python src/run_test.py --test_id test_001 \
    --book hound_of_the_baskervilles --sent_from 1 --sent_to 20 \
    --langs sr --methods nllb gemma

Ponovni run (samo ID):
  venv/bin/python src/run_test.py --test_id test_001
"""

import os
import sys
import argparse
import requests
import psycopg2
import yaml
from dotenv import load_dotenv
from loguru import logger
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ── Setup ────────────────────────────────────────────────────────────────────

load_dotenv()

REGISTRY_PATH = os.path.join(os.getenv("BUCH_HOME", "."), "tests", "test_registry.yaml")
LOG_DIR       = os.getenv("BUCH_LOG", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

NLLB_MODEL   = "facebook/nllb-200-distilled-600M"
EMBED_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_URL   = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:12b")
OLLAMA_KEY   = os.getenv("OLLAMA_API_KEY", "")

# NLLB jezik kodovi (ISO 639-1 → NLLB BCP-47)
LANG_MAP = {
    "sr": "srp_Cyrl",
    "hr": "hrv_Latn",
    "bs": "bos_Latn",
    "sl": "slv_Latn",
    "mk": "mkd_Cyrl",
    "bg": "bul_Cyrl",
    "de": "deu_Latn",
    "nl": "nld_Latn",
    "fr": "fra_Latn",
    "it": "ita_Latn",
    "es": "spa_Latn",
    "pt": "por_Latn",
    "ro": "ron_Latn",
    "en": "eng_Latn",
}


# ── DB ───────────────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


# ── Registry ─────────────────────────────────────────────────────────────────

def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        return {}
    with open(REGISTRY_PATH, "r") as f:
        return yaml.safe_load(f) or {}


def save_registry(registry):
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        yaml.dump(registry, f, default_flow_style=False, allow_unicode=True)


def register_test(test_id, book, sent_from, sent_to, langs, methods):
    registry = load_registry()
    if test_id in registry:
        logger.info(f"Test {test_id} već postoji u registry — koristim postojeće parametre")
        return registry[test_id]
    entry = {
        "book":      book,
        "sent_from": sent_from,
        "sent_to":   sent_to,
        "langs":     langs,
        "methods":   methods,
    }
    registry[test_id] = entry
    save_registry(registry)
    logger.info(f"Test {test_id} registrovan: {entry}")
    return entry


def get_test(test_id):
    registry = load_registry()
    if test_id not in registry:
        logger.error(f"Test {test_id} nije pronađen u registry!")
        sys.exit(1)
    return registry[test_id]


# ── Rečenice ─────────────────────────────────────────────────────────────────

def load_sentences(conn, book_title, sent_from, sent_to):
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.text
        FROM sentences s
        JOIN books b ON s.book_id = b.id
        WHERE b.title ILIKE %s
          AND s.id BETWEEN %s AND %s
        ORDER BY s.id
    """, (f"%{book_title.replace('_', ' ')}%", sent_from, sent_to))
    rows = cur.fetchall()
    cur.close()
    return rows


# ── Prevod — NLLB ─────────────────────────────────────────────────────────────

def load_nllb():
    logger.info(f"Učitavanje NLLB modela: {NLLB_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL)
    model     = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)
    return tokenizer, model


def translate_nllb(text, tokenizer, model, src_lang="eng_Latn", tgt_lang="srp_Cyrl"):
    tokenizer.src_lang = src_lang
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    translated = model.generate(
        **inputs,
        forced_bos_token_id=tokenizer.convert_tokens_to_ids(tgt_lang),
        max_length=512,
        repetition_penalty=1.3,
    )
    return tokenizer.decode(translated[0], skip_special_tokens=True)


# ── Prevod — Gemma (Ollama Cloud) ─────────────────────────────────────────────

def translate_gemma(text, tgt_lang_code):
    lang_names = {
        "sr": "Serbian (Cyrillic)", "hr": "Croatian", "bs": "Bosnian",
        "sl": "Slovenian", "mk": "Macedonian", "bg": "Bulgarian",
        "de": "German", "nl": "Dutch", "fr": "French",
        "it": "Italian", "es": "Spanish", "pt": "Portuguese", "ro": "Romanian",
    }
    lang_name = lang_names.get(tgt_lang_code, tgt_lang_code)
    prompt = (
        f"Translate the following English text to {lang_name}. "
        f"Return only the translation, no explanation.\n\n"
        f"Text: {text}"
    )
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


# ── Back-translation — Gemma ──────────────────────────────────────────────────

def back_translate_gemma(translated_text, src_lang_code):
    lang_names = {
        "sr": "Serbian", "hr": "Croatian", "bs": "Bosnian",
        "sl": "Slovenian", "mk": "Macedonian", "bg": "Bulgarian",
        "de": "German", "nl": "Dutch", "fr": "French",
        "it": "Italian", "es": "Spanish", "pt": "Portuguese", "ro": "Romanian",
    }
    lang_name = lang_names.get(src_lang_code, src_lang_code)
    prompt = (
        f"Translate the following {lang_name} text to English. "
        f"Return only the translation, no explanation.\n\n"
        f"Text: {translated_text}"
    )
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


# ── Scoring ───────────────────────────────────────────────────────────────────

def load_embedder():
    logger.info(f"Učitavanje embedding modela: {EMBED_MODEL}")
    return SentenceTransformer(EMBED_MODEL)


def compute_score(original, back_translation, embedder):
    vecs = embedder.encode([original, back_translation])
    return float(cosine_similarity([vecs[0]], [vecs[1]])[0][0])


# ── DB operacije ──────────────────────────────────────────────────────────────

def clear_test(conn, test_id, langs):
    cur = conn.cursor()
    cur.execute("DELETE FROM test_results WHERE test_id = %s AND target_lang = ANY(%s)", (test_id, langs))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    logger.info(f"Obrisano {deleted} starih rezultata za {test_id} langs={langs}")


def insert_result(conn, test_id, sentence_id, target_lang, method,
                  translated, back_trans, score_val):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO test_results
            (test_id, sentence_id, target_lang, method,
             translated_text, back_translation, score)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (test_id, sentence_id, target_lang, method)
        DO UPDATE SET
            translated_text  = EXCLUDED.translated_text,
            back_translation = EXCLUDED.back_translation,
            score            = EXCLUDED.score,
            created_at       = NOW()
    """, (test_id, sentence_id, target_lang, method,
          translated, back_trans, score_val))
    conn.commit()
    cur.close()


def update_winners(conn, test_id):
    """Za svaki (sentence_id, target_lang) par — označi pobjedničku metodu."""
    cur = conn.cursor()
    cur.execute("UPDATE test_results SET winner = FALSE WHERE test_id = %s", (test_id,))
    cur.execute("""
        UPDATE test_results tr
        SET winner = TRUE
        FROM (
            SELECT DISTINCT ON (sentence_id, target_lang)
                   id
            FROM test_results
            WHERE test_id = %s AND score IS NOT NULL
            ORDER BY sentence_id, target_lang, score DESC
        ) best
        WHERE tr.id = best.id
    """, (test_id,))
    conn.commit()
    cur.close()
    logger.info(f"Winners ažurirani za {test_id}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Buchenberg test runner")
    parser.add_argument("--test_id",   required=True)
    parser.add_argument("--book",      default=None)
    parser.add_argument("--sent_from", type=int, default=None)
    parser.add_argument("--sent_to",   type=int, default=None)
    parser.add_argument("--langs",     nargs="+", default=None)
    parser.add_argument("--methods",   nargs="+", default=None)
    args = parser.parse_args()

    log_file = os.path.join(LOG_DIR, f"{args.test_id}.log")
    logger.add(log_file, rotation="10 MB", encoding="utf-8")
    logger.info(f"=== {args.test_id} START ===")

    # Registry
    if args.book:
        params = register_test(
            args.test_id, args.book, args.sent_from, args.sent_to,
            args.langs, args.methods
        )
    else:
        params = get_test(args.test_id)

    book      = params["book"]
    sent_from = params["sent_from"]
    sent_to   = params["sent_to"]
    langs     = params["langs"]
    methods   = params["methods"]

    logger.info(f"Parametri: book={book}, sent={sent_from}-{sent_to}, "
                f"langs={langs}, methods={methods}")

    # Učitaj alate
    embedder = load_embedder()
    nllb_tok, nllb_mod = (None, None)
    if "nllb" in methods:
        nllb_tok, nllb_mod = load_nllb()

    # DB
    conn = get_conn()
    clear_test(conn, args.test_id, langs)
    sentences = load_sentences(conn, book, sent_from, sent_to)
    logger.info(f"Rečenica učitano: {len(sentences)}")

    total = len(sentences) * len(langs) * len(methods)
    done  = 0

    for sid, text in sentences:
        for lang in langs:
            nllb_lang = LANG_MAP.get(lang)
            if not nllb_lang:
                logger.warning(f"Nepoznat jezik: {lang}, preskačem")
                continue

            for method in methods:
                try:
                    # Prevod EN → lang
                    if method == "nllb":
                        translated = translate_nllb(text, nllb_tok, nllb_mod,
                                                    tgt_lang=nllb_lang)
                    elif method == "gemma":
                        translated = translate_gemma(text, lang)
                    else:
                        logger.warning(f"Nepoznata metoda: {method}")
                        continue

                    # Back-translation lang → EN
                    if method == "nllb":
                        back = translate_nllb(translated, nllb_tok, nllb_mod,
                                              src_lang=nllb_lang,
                                              tgt_lang="eng_Latn")
                    elif method == "gemma":
                        back = back_translate_gemma(translated, lang)

                    # Score
                    sc = compute_score(text, back, embedder)

                    insert_result(conn, args.test_id, sid, lang,
                                  method, translated, back, sc)

                    done += 1
                    logger.info(f"[{done}/{total}] s{sid} {lang} {method} "
                                f"score={sc:.3f} | {text[:50]}...")

                except Exception as e:
                    logger.error(f"Greška s{sid} {lang} {method}: {e}")

    update_winners(conn, args.test_id)
    conn.close()

    logger.info(f"=== {args.test_id} DONE — {done}/{total} ===")
    print(f"\n✓ {args.test_id} završen: {done}/{total} prevoda")


if __name__ == "__main__":
    main()
