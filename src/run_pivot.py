#!/usr/bin/env python3
"""
Buchenberg · run_pivot.py
Pivot faza — optimizacija prevoda kroz pivot jezike.

Pretpostavka: pivot_results već sadrži inicijalne prevode
(pokrenuti run_pivot_init.py prije ovoga).

Logika po iteraciji:
  - Za svaku rečenicu pronađi jezik s max translation_score (pivot)
  - Prevedi pivot_tekst → svi ostali jezici (sve kombinacije model/temp)
  - Updateuj samo ako novi score > postojeći
  - Stop ako nema poboljšanja ili dostignuti max_iterations

Pokretanje:
  venv/bin/python src/run_pivot.py
  venv/bin/python src/run_pivot.py --sent_from 1 --sent_to 10
"""

import os
import sys
import argparse
from collections import defaultdict

import psycopg2
import requests
import yaml
from dotenv import load_dotenv
from loguru import logger
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ── Setup ────────────────────────────────────────────────────────────────────

load_dotenv()

PIVOT_PATH = os.path.join(os.getenv("BUCH_HOME", "."), "tests", "pivot.yaml")
LOG_DIR    = os.getenv("BUCH_LOG", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

NLLB_MODEL  = "facebook/nllb-200-distilled-600M"
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_URL  = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY  = os.getenv("OLLAMA_API_KEY", "")

LANG_MAP = {
    "sr": "srp_Cyrl", "hr": "hrv_Latn", "bs": "bos_Latn",
    "sl": "slv_Latn", "mk": "mkd_Cyrl", "bg": "bul_Cyrl",
    "de": "deu_Latn", "nl": "nld_Latn", "af": "afr_Latn",
    "fr": "fra_Latn", "it": "ita_Latn", "es": "spa_Latn",
    "pt": "por_Latn", "ro": "ron_Latn", "en": "eng_Latn",
}

LANG_NAMES = {
    "sr": "Serbian (Cyrillic)", "hr": "Croatian",  "bs": "Bosnian",
    "sl": "Slovenian",          "mk": "Macedonian", "bg": "Bulgarian",
    "de": "German",             "nl": "Dutch",      "af": "Afrikaans",
    "fr": "French",             "it": "Italian",    "es": "Spanish",
    "pt": "Portuguese",         "ro": "Romanian",
}

BATCH_SIZE = 20

# ── Pivot config ──────────────────────────────────────────────────────────────

def load_pivot():
    if not os.path.exists(PIVOT_PATH):
        logger.error(f"pivot.yaml nije pronađen: {PIVOT_PATH}")
        sys.exit(1)
    with open(PIVOT_PATH, "r") as f:
        return yaml.safe_load(f) or {}

# ── DB ───────────────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

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

def upsert_pivot(conn, test_id, sentence_id, target_lang, model,
                 temperature, translated_text, translation_score):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pivot_results
            (test_id, sentence_id, target_lang, model, temperature,
             translated_text, translation_score, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (test_id, sentence_id, target_lang)
        DO UPDATE SET
            model             = EXCLUDED.model,
            temperature       = EXCLUDED.temperature,
            translated_text   = EXCLUDED.translated_text,
            translation_score = EXCLUDED.translation_score,
            updated_at        = NOW()
        WHERE EXCLUDED.translation_score > pivot_results.translation_score
        RETURNING id
    """, (test_id, sentence_id, target_lang, model, temperature,
          translated_text, translation_score))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    return row is not None

def load_pivot_state(conn, test_id, sent_ids):
    if not sent_ids:
        return {}
    cur = conn.cursor()
    cur.execute("""
        SELECT sentence_id, target_lang, translation_score, translated_text
        FROM pivot_results
        WHERE test_id = %s AND sentence_id = ANY(%s)
    """, (test_id, list(sent_ids)))
    rows = cur.fetchall()
    cur.close()
    state = defaultdict(dict)
    for sid, lang, score, text in rows:
        state[sid][lang] = (score, text)
    return state

# ── NLLB ─────────────────────────────────────────────────────────────────────

def load_nllb():
    logger.info(f"Učitavanje NLLB modela: {NLLB_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL)
    model     = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)
    return tokenizer, model

def translate_nllb_batch(texts, tokenizer, model,
                         src_lang="eng_Latn", tgt_lang="srp_Cyrl",
                         temperature=None):
    tokenizer.src_lang = src_lang
    inputs = tokenizer(texts, return_tensors="pt", padding=True,
                       truncation=True, max_length=512)
    gen_kwargs = dict(
        forced_bos_token_id=tokenizer.convert_tokens_to_ids(tgt_lang),
        max_length=512, repetition_penalty=1.3,
    )
    if temperature is not None:
        gen_kwargs["do_sample"]   = True
        gen_kwargs["temperature"] = temperature
    else:
        gen_kwargs["do_sample"] = False
    translated = model.generate(**inputs, **gen_kwargs)
    return tokenizer.batch_decode(translated, skip_special_tokens=True)

# ── Ollama Cloud ──────────────────────────────────────────────────────────────

def parse_separator_response(raw, n, context="batch"):
    import re
    SEP = "__!!__"
    parts = raw.split(SEP)
    cleaned = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        p = re.sub(r"\*+([^*]+)\*+", r"\1", p)
        p = p.strip()
        if p:
            cleaned.append(p)
    if len(cleaned) >= n:
        return cleaned[:n]
    logger.warning(f"{context}: separator parser vratio {len(cleaned)}/{n}")
    return None

def translate_ollama_single(text, src_lang_code, tgt_lang_code, model, temperature):
    src_name = "English" if src_lang_code == "en" else LANG_NAMES.get(src_lang_code, src_lang_code)
    tgt_name = LANG_NAMES.get(tgt_lang_code, tgt_lang_code)
    prompt = (
        f"Translate the following {src_name} text to {tgt_name}. "
        f"Return only the translation, no explanation.\n\nText: {text}"
    )
    payload = {
        "model":    model,
        "messages": [{"role": "user", "content": prompt}],
        "stream":   False,
    }
    if temperature is not None:
        payload["options"] = {"temperature": temperature}
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        json=payload, timeout=60,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()

def translate_ollama_batch(texts, src_lang_code, tgt_lang_code, model, temperature):
    src_name = "English" if src_lang_code == "en" else LANG_NAMES.get(src_lang_code, src_lang_code)
    tgt_name = LANG_NAMES.get(tgt_lang_code, tgt_lang_code)
    n = len(texts)
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    prompt = (
        f"Translate these {n} sentences from {src_name} to {tgt_name}.\n"
        f"Return exactly {n} translations separated by __!!__ — one per sentence.\n"
        f"Do not add numbering, markdown, or explanations.\n"
        f"Example: First translation__!!__Second translation__!!__Third translation\n\n"
        f"{numbered}"
    )
    payload = {
        "model":    model,
        "messages": [{"role": "user", "content": prompt}],
        "stream":   False,
    }
    if temperature is not None:
        payload["options"] = {"temperature": temperature}
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        json=payload, timeout=120,
    )
    response.raise_for_status()
    raw = response.json()["message"]["content"].strip()
    result = parse_separator_response(raw, n, context=f"{src_lang_code}→{tgt_lang_code}")
    if result:
        return result
    logger.warning(f"Batch fallback na single: {src_lang_code}→{tgt_lang_code}")
    return [translate_ollama_single(t, src_lang_code, tgt_lang_code, model, temperature)
            for t in texts]

# ── Scoring ───────────────────────────────────────────────────────────────────

def load_embedder():
    logger.info(f"Učitavanje embedding modela: {EMBED_MODEL}")
    return SentenceTransformer(EMBED_MODEL, local_files_only=True)

def score_batch(originals, translations, embedder):
    enc_orig  = embedder.encode(originals)
    enc_trans = embedder.encode(translations)
    return [float(cosine_similarity([o], [t])[0][0])
            for o, t in zip(enc_orig, enc_trans)]

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Buchenberg pivot runner")
    parser.add_argument("--sent_from", type=int, default=None)
    parser.add_argument("--sent_to",   type=int, default=None)
    args = parser.parse_args()

    params  = load_pivot()
    test_id = params["test_id"]

    log_file = os.path.join(LOG_DIR, f"{test_id}_pivot.log")
    logger.add(log_file, rotation="10 MB", encoding="utf-8", enqueue=True)
    logger.info(f"=== {test_id} PIVOT START ===")

    book           = params["book"]
    sent_from      = args.sent_from or params["sent_from"]
    sent_to        = args.sent_to   or params["sent_to"]
    langs          = params["langs"]
    models         = params["models"]
    temperatures   = params["temperatures"]
    max_iterations = params.get("max_iterations", 10)

    logger.info(f"Parametri: book={book}, sent={sent_from}-{sent_to}")
    logger.info(f"langs={langs}, models={models}, temperatures={temperatures}")
    logger.info(f"max_iterations={max_iterations}")

    embedder = load_embedder()
    nllb_tok, nllb_mod = (None, None)
    if any("nllb" in m for m in models):
        nllb_tok, nllb_mod = load_nllb()

    conn      = get_conn()
    sentences = load_sentences(conn, book, sent_from, sent_to)
    sent_ids  = [s[0] for s in sentences]
    sent_map  = {s[0]: s[1] for s in sentences}
    logger.info(f"Rečenica učitano: {len(sentences)}")

    for iteration in range(1, max_iterations + 1):
        logger.info(f"=== Iteracija {iteration}/{max_iterations} ===")

        state    = load_pivot_state(conn, test_id, sent_ids)
        eligible = [sid for sid in sent_ids if len(state.get(sid, {})) >= 2]
        if not eligible:
            logger.info("Nema rečenica s >= 2 prevoda — kraj pivot faze")
            break

        pivot_groups = defaultdict(list)
        for sid in eligible:
            pivot_lang = max(state[sid], key=lambda l: state[sid][l][0])
            pivot_groups[pivot_lang].append(sid)

        logger.info(f"Pivot grupe: { {k: len(v) for k, v in pivot_groups.items()} }")

        test_improved = 0

        for pivot_lang, group_sids in pivot_groups.items():
            target_langs = [l for l in langs if l != pivot_lang and l in LANG_MAP]

            for tgt_lang in target_langs:
                for model in models:
                    for temp in temperatures:
                        logger.info(
                            f"  {pivot_lang}→{tgt_lang} | {model} | temp={temp} "
                            f"({len(group_sids)} rečenica)")

                        for batch_start in range(0, len(group_sids), BATCH_SIZE):
                            b_sids  = group_sids[batch_start:batch_start + BATCH_SIZE]
                            b_pivot = [state[sid][pivot_lang][1] for sid in b_sids]
                            b_en    = [sent_map[sid] for sid in b_sids]

                            try:
                                if "nllb" in model:
                                    nllb_temp = 0.5 if "t05" in model else None
                                    translations = translate_nllb_batch(
                                        b_pivot, nllb_tok, nllb_mod,
                                        src_lang=LANG_MAP.get(pivot_lang, "eng_Latn"),
                                        tgt_lang=LANG_MAP[tgt_lang],
                                        temperature=nllb_temp
                                    )
                                    db_temp = nllb_temp
                                else:
                                    translations = translate_ollama_batch(
                                        b_pivot, pivot_lang, tgt_lang, model, temp)
                                    db_temp = temp

                                scores = score_batch(b_en, translations, embedder)

                                for sid, translation, sc in zip(b_sids, translations, scores):
                                    changed = upsert_pivot(
                                        conn, test_id, sid, tgt_lang,
                                        model, db_temp, translation, sc)
                                    if changed:
                                        test_improved += 1
                                        logger.info(
                                            f"    ✓ s{sid} {tgt_lang} "
                                            f"score={sc:.4f} (pivot={pivot_lang})")
                                    else:
                                        logger.debug(
                                            f"    - s{sid} {tgt_lang} "
                                            f"score={sc:.4f} nije poboljšanje")

                            except Exception as e:
                                logger.error(
                                    f"Greška {pivot_lang}→{tgt_lang} "
                                    f"{model} temp={temp}: {e}")

        logger.info(f"Iteracija {iteration}: {test_improved} poboljšanja")
        if test_improved == 0:
            logger.info("Nema poboljšanja — konvergencija")
            break

    conn.close()
    logger.info(f"=== {test_id} PIVOT DONE ===")
    print(f"\n✓ {test_id} pivot završen")

if __name__ == "__main__":
    main()
