#!/usr/bin/env python3
"""
run_context.py — Kontekstualni prevod za žute i crvene HR rečenice.
Prozor od 3 uzastopne rečenice — prevodi ciljnu s kontekstom via gemma3.
Bez upisa u bazu — samo log.

Upotreba:
    venv/bin/python src/run_context.py > logs/context_hr_001.log 2>&1
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
GREEN_THRESH    = 0.90
SENT_FROM       = 1
SENT_TO         = 40


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )


def fetch_all_sentences(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, text FROM sentences WHERE id BETWEEN %s AND %s ORDER BY id",
            (SENT_FROM, SENT_TO)
        )
        return {row[0]: row[1] for row in cur.fetchall()}


def fetch_yellow_red_hr(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ON (sentence_id)
                sentence_id,
                translation  AS hr_text,
                cosine_score AS hr_score
            FROM translation_scores
            WHERE target_lang = 'hr'
              AND embedder = 'minilm'
              AND sentence_id BETWEEN %s AND %s
            ORDER BY sentence_id, cosine_score DESC
        """, (SENT_FROM, SENT_TO))
        rows = cur.fetchall()
    return [(sid, text, float(score)) for sid, text, score in rows
            if float(score) < GREEN_THRESH]


def build_context_window(sid, sentences):
    ids = sorted(sentences.keys())
    min_id, max_id = ids[0], ids[-1]

    if sid == min_id:
        ctx, target_pos = [sid, sid+1, sid+2], 0
    elif sid == max_id:
        ctx, target_pos = [sid-2, sid-1, sid], 2
    else:
        ctx, target_pos = [sid-1, sid, sid+1], 1

    return ctx, target_pos


def build_prompt(ctx_ids, target_pos, sentences):
    lines = "\n".join(
        f"[{i+1}] {sentences.get(cid, '')}" for i, cid in enumerate(ctx_ids)
    )
    target_num   = target_pos + 1
    context_nums = [i+1 for i in range(3) if i != target_pos]

    return (
        "You are translating a book from English to Croatian.\n"
        "Here are three consecutive sentences for context:\n\n"
        f"{lines}\n\n"
        f"Translate sentence [{target_num}] to Croatian. "
        f"Use sentences {context_nums} as context to ensure an accurate "
        "and natural translation.\n"
        "Return ONLY the Croatian translation of the target sentence, nothing else."
    )


def ollama_call(prompt):
    r = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        json={
            "model":    MODEL_TRANSLATE,
            "messages": [{"role": "user", "content": prompt}],
            "stream":   False,
            "options":  {"temperature": TEMPERATURE},
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def cosine(v1, v2):
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def main():
    logger.info("=" * 62)
    logger.info("  run_context.py — Kontekstualni prevod HR")
    logger.info(f"  Model: {MODEL_TRANSLATE}  |  temp={TEMPERATURE}")
    logger.info(f"  Prozor: 3 rečenice  |  Prag: <{GREEN_THRESH}")
    logger.info("=" * 62)

    conn = get_conn()
    sentences = fetch_all_sentences(conn)
    candidates = fetch_yellow_red_hr(conn)
    conn.close()

    logger.info(f"Žutih + crvenih HR: {len(candidates)}\n")

    logger.info("Učitavam MiniLM embedder...")
    embedder = SentenceTransformer(MODEL_EMBED)
    logger.info("MiniLM učitan.\n")

    improved = 0

    for sid, hr_old, hr_old_score in candidates:
        en_text = sentences[sid]
        ctx_ids, target_pos = build_context_window(sid, sentences)
        prompt = build_prompt(ctx_ids, target_pos, sentences)

        logger.info(f"── s{sid} ────────────────────────────────────────")
        logger.info(f"  EN:       {en_text[:80]}")
        logger.info(f"  Kontekst: {ctx_ids}  [cilj={ctx_ids[target_pos]}]")
        logger.info(f"  HR stari: {hr_old[:80]}")
        logger.info(f"            score={hr_old_score:.4f}")

        try:
            new_hr = ollama_call(prompt)
        except Exception as e:
            logger.error(f"  Greška: {e}")
            continue

        vecs = embedder.encode([en_text, new_hr])
        new_score = round(cosine(vecs[0], vecs[1]), 4)
        delta = round(new_score - hr_old_score, 4)
        verdict = "✅ POBOLJŠANJE" if new_score > hr_old_score else "❌ ZADRŽATI STARI"

        logger.info(f"  HR novi:  {new_hr[:80]}")
        logger.info(f"            score={new_score:.4f}  delta={delta:+.4f}  {verdict}")

        if new_score > hr_old_score:
            improved += 1

    logger.info("\n" + "=" * 62)
    logger.info(f"  Rezultat: {improved}/{len(candidates)} rečenica poboljšano")
    logger.info("=" * 62)


if __name__ == "__main__":
    main()
