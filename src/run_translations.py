#!/usr/bin/env python3
"""
run_translations.py — Punjenje tabele translations
Prevodi rečenice s više modela i temperatura, upisuje u bazu.
ON CONFLICT DO NOTHING — sigurno ponavljanje.

Upotreba:
    venv/bin/python src/run_translations.py \
        --lang it --sent_from 1 --sent_to 40 \
        --models gemma3 ministral gemma4 nllb \
        --temps 0.1 0.5 --batch_size 20
"""

import os
import re
import argparse
import requests
import psycopg2
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# ── Config ──────────────────────────────────────────────
OLLAMA_URL  = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY  = os.getenv("OLLAMA_API_KEY", "")
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = int(os.getenv("DB_PORT", 5432))
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

NLLB_MODEL_NAME = "facebook/nllb-200-distilled-600M"
SEP = "__!!__"

MODEL_STRINGS = {
    "gemma3":    "gemma3:12b",
    "ministral": "ministral-3:14b",
    "gemma4":    "gemma4:31b",
}

LANG_NAMES = {
    "it": "Italian", "hr": "Croatian", "de": "German",
    "fr": "French",  "pt": "Portuguese", "es": "Spanish",
    "nl": "Dutch",   "bg": "Bulgarian",  "sr": "Serbian",
    "bs": "Bosnian", "sl": "Slovenian",  "mk": "Macedonian",
    "ro": "Romanian","af": "Afrikaans",
}

NLLB_CODES = {
    "it": "ita_Latn", "hr": "hrv_Latn", "de": "deu_Latn",
    "fr": "fra_Latn", "pt": "por_Latn", "es": "spa_Latn",
    "nl": "nld_Latn", "bg": "bul_Cyrl", "sr": "srp_Cyrl",
    "bs": "bos_Latn", "sl": "slv_Latn", "mk": "mkd_Cyrl",
    "ro": "ron_Latn", "af": "afr_Latn",
}


# ── DB ──────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )

def fetch_sentences(sent_from, sent_to):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT s.id, s.text, s.book_id FROM sentences s "
        "WHERE s.id BETWEEN %s AND %s ORDER BY s.id",
        (sent_from, sent_to)
    )
    rows = cur.fetchall()
    conn.close()
    return rows  # [(id, text, book_id), ...]

def insert_batch(conn, rows):
    """rows = [(sentence_id, book_id, target_lang, model, temperature, translation), ...]"""
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO translations
            (sentence_id, book_id, target_lang, model, temperature, translation)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (sentence_id, target_lang, model, temperature) DO NOTHING
    """, rows)
    conn.commit()


# ── Ollama ───────────────────────────────────────────────
def ollama_call(model, prompt, temperature):
    payload = {
        "model":    model,
        "messages": [{"role": "user", "content": prompt}],
        "stream":   False,
        "options":  {"temperature": temperature},
    }
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()

def parse_sep(raw, n, context=""):
    parts = raw.split(SEP)
    cleaned = [re.sub(r"\*+([^*]+)\*+", r"\1", p).strip() for p in parts]
    cleaned = [p for p in cleaned if p]
    if len(cleaned) >= n:
        return cleaned[:n]
    logger.warning(f"parse_sep [{context}]: {len(cleaned)}/{n} | raw={raw[:150]}")
    return None


# ── LLM batch prevod (jedan chunk) ───────────────────────
def translate_llm_chunk(model_str, chunk, lang_name, temperature, context=""):
    n = len(chunk)
    numbered = "\n".join(f"{i+1}. {text}" for i, (_, text, _) in enumerate(chunk))
    prompt = (
        f"Translate these {n} sentences to {lang_name}.\n"
        f"Return exactly {n} translations separated by {SEP} — one per sentence.\n"
        f"Do not add numbering, markdown, or explanations.\n"
        f"Example: First translation{SEP}Second translation{SEP}Third translation\n\n"
        f"{numbered}"
    )
    raw = ollama_call(model_str, prompt, temperature)
    return parse_sep(raw, n, context=context)


# ── NLLB batch prevod ────────────────────────────────────
_nllb_tokenizer = None
_nllb_model     = None

def load_nllb():
    global _nllb_tokenizer, _nllb_model
    if _nllb_tokenizer is None:
        logger.info("  Učitavam NLLB model...")
        _nllb_tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL_NAME)
        _nllb_model     = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL_NAME)
        logger.info("  NLLB učitan.")

def translate_nllb_chunk(chunk, tgt_lang_code, temperature):
    load_nllb()
    texts = [text for _, text, _ in chunk]
    _nllb_tokenizer.src_lang = "eng_Latn"
    inputs = _nllb_tokenizer(
        texts, return_tensors="pt", padding=True,
        truncation=True, max_length=512
    )
    gen_kwargs = dict(
        forced_bos_token_id=_nllb_tokenizer.convert_tokens_to_ids(tgt_lang_code),
        max_length=512,
        repetition_penalty=1.3,
    )
    if temperature > 0.05:
        gen_kwargs["do_sample"]   = True
        gen_kwargs["temperature"] = temperature
    else:
        gen_kwargs["do_sample"] = False

    translated = _nllb_model.generate(**inputs, **gen_kwargs)
    return _nllb_tokenizer.batch_decode(translated, skip_special_tokens=True)


# ── Main ─────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang",       default="it")
    parser.add_argument("--sent_from",  type=int,   default=1)
    parser.add_argument("--sent_to",    type=int,   default=40)
    parser.add_argument("--models",     nargs="+",
                        default=["gemma3", "ministral", "gemma4", "nllb"])
    parser.add_argument("--temps",      nargs="+", type=float,
                        default=[0.1, 0.5])
    parser.add_argument("--batch_size", type=int,   default=20)
    args = parser.parse_args()

    lang_name     = LANG_NAMES.get(args.lang, args.lang)
    nllb_tgt_code = NLLB_CODES.get(args.lang, "ita_Latn")

    logger.info("=" * 58)
    logger.info(f"  run_translations.py")
    logger.info(f"  Lang: {args.lang.upper()} ({lang_name})")
    logger.info(f"  Rečenice: {args.sent_from}–{args.sent_to}")
    logger.info(f"  Modeli: {args.models}")
    logger.info(f"  Temperature: {args.temps}")
    logger.info(f"  Batch size: {args.batch_size}")
    logger.info("=" * 58)

    sentences = fetch_sentences(args.sent_from, args.sent_to)
    logger.info(f"Učitano {len(sentences)} rečenica.\n")

    # Chunking
    chunks = [
        sentences[i:i + args.batch_size]
        for i in range(0, len(sentences), args.batch_size)
    ]
    logger.info(f"Chunkovi: {len(chunks)} × {args.batch_size}\n")

    conn = get_conn()
    total_inserted = 0

    for model_key in args.models:
        for temp in args.temps:
            logger.info(f"--- [{model_key}] temperatura={temp} ---")
            inserted = 0

            for ci, chunk in enumerate(chunks):
                context = f"{model_key}/t{temp}/chunk{ci+1}"

                if model_key == "nllb":
                    parts = translate_nllb_chunk(chunk, nllb_tgt_code, temp)
                    model_label = "nllb-600M"
                else:
                    model_str = MODEL_STRINGS.get(model_key)
                    if not model_str:
                        logger.warning(f"Nepoznat model: {model_key}")
                        continue
                    parts = translate_llm_chunk(model_str, chunk, lang_name, temp, context)
                    model_label = model_str

                if parts is None:
                    logger.error(f"  Chunk {ci+1} nije uspio, preskačem.")
                    continue

                rows = [
                    (sid, book_id, args.lang, model_label, temp, parts[i])
                    for i, (sid, _, book_id) in enumerate(chunk)
                    if i < len(parts) and parts[i]
                ]
                insert_batch(conn, rows)
                inserted += len(rows)
                logger.info(f"  Chunk {ci+1}/{len(chunks)}: {len(rows)} upisano")

            total_inserted += inserted
            logger.info(f"  [{model_key}] t={temp} ukupno: {inserted}/{len(sentences)}\n")

    conn.close()
    logger.info(f"Ukupno upisano: {total_inserted} prevoda.")
    logger.info("Gotovo.")


if __name__ == "__main__":
    main()
