#!/usr/bin/env python3
"""
run_judge.py — LLM-as-judge, pairwise comparison
3 modela prevode 40 rečenica.
Za svaki par modela, treći model bira pobjednika (A ili B).
Niko ne sudi sebi. Output: head-to-head + ukupne pobjede.
"""

import os
import re
import requests
import psycopg2
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

MODELS = {
    "gemma3":    "gemma3:12b",
    "ministral": "ministral-3:14b",
    "gemma4":    "gemma4:31b",
}

TARGET_LANG = "it"
LANG_NAME   = "Italian"
SENT_FROM   = 1
SENT_TO     = 40
TRANS_TEMP  = 0.5
JUDGE_TEMP  = 0.1
SEP         = "__!!__"

# Parovi: (model_A, model_B, sudija)
PAIRS = [
    ("gemma3",    "ministral", "gemma4"),
    ("gemma3",    "gemma4",    "ministral"),
    ("ministral", "gemma4",    "gemma3"),
]


# ── DB ──────────────────────────────────────────────────
def fetch_sentences(sent_from, sent_to):
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )
    cur = conn.cursor()
    cur.execute(
        "SELECT id, text FROM sentences WHERE id BETWEEN %s AND %s ORDER BY id",
        (sent_from, sent_to)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


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
    """Parsira __!!__ separator format, vraća listu od n stringova ili None."""
    parts = raw.split(SEP)
    cleaned = [re.sub(r"\*+([^*]+)\*+", r"\1", p).strip() for p in parts]
    cleaned = [p for p in cleaned if p]
    if len(cleaned) >= n:
        return cleaned[:n]
    logger.warning(f"parse_sep [{context}]: dobio {len(cleaned)}/{n} | raw={raw[:200]}")
    return None


# ── Faza 1: Prevodi ──────────────────────────────────────
def batch_translate(model_key, model_str, sentences):
    """Vraća dict {sent_id: translation}"""
    n = len(sentences)
    numbered = "\n".join(f"{i+1}. {text}" for i, (sid, text) in enumerate(sentences))

    prompt = (
        f"Translate these {n} sentences to {LANG_NAME}.\n"
        f"Return exactly {n} translations separated by {SEP} — one per sentence.\n"
        f"Do not add numbering, markdown, or explanations.\n"
        f"Example format: First translation{SEP}Second translation{SEP}Third translation\n\n"
        f"{numbered}"
    )

    logger.info(f"  Prevod [{model_key}] ({n} rečenica)...")
    raw = ollama_call(model_str, prompt, TRANS_TEMP)
    parts = parse_sep(raw, n, context=f"translate/{model_key}")
    if parts is None:
        logger.error(f"  [{model_key}] parsiranje prevoda nije uspjelo!")
        return {}
    return {sid: parts[i] for i, (sid, _) in enumerate(sentences)}


# ── Faza 2: Pairwise ocjenjivanje ────────────────────────
def batch_pairwise(judge_key, judge_str, sentences, trans_A, trans_B, key_A, key_B):
    """
    Sudija bira A ili B za svaku rečenicu.
    Vraća dict {sent_id: 'A' ili 'B'}
    """
    n = len(sentences)
    numbered = "\n".join(
        f"{i+1}. Original: {text}\n   A: {trans_A.get(sid, '')}\n   B: {trans_B.get(sid, '')}"
        for i, (sid, text) in enumerate(sentences)
    )

    prompt = (
        f"You are comparing {n} pairs of English-to-{LANG_NAME} translations.\n"
        f"For each pair, choose the better translation: A or B.\n"
        f"Consider accuracy, fluency, and naturalness.\n"
        f"Return ONLY {n} answers separated by {SEP} — each answer must be exactly A or B.\n"
        f"Example for 3 pairs: A{SEP}B{SEP}A\n\n"
        f"{numbered}"
    )

    logger.info(f"  Pairwise [{judge_key}] sudi: {key_A} vs {key_B}...")
    raw = ollama_call(judge_str, prompt, JUDGE_TEMP)
    parts = parse_sep(raw, n, context=f"pairwise/{judge_key}")
    if parts is None:
        logger.error(f"  [{judge_key}] parsiranje pairwise nije uspjelo!")
        return {}

    result = {}
    for i, (sid, _) in enumerate(sentences):
        answer = parts[i].strip().upper()
        if answer in ("A", "B"):
            result[sid] = answer
        else:
            logger.warning(f"  Neočekivan odgovor '{parts[i]}' za S{sid}, postavljam A")
            result[sid] = "A"
    return result


# ── Main ─────────────────────────────────────────────────
def main():
    logger.info("=" * 58)
    logger.info("  LLM-as-judge — Pairwise Comparison")
    logger.info(f"  Rečenice {SENT_FROM}-{SENT_TO} | Jezik: {TARGET_LANG.upper()}")
    logger.info(f"  Modeli: {', '.join(MODELS.keys())}")
    logger.info("=" * 58)

    sentences = fetch_sentences(SENT_FROM, SENT_TO)
    logger.info(f"Učitano {len(sentences)} rečenica iz baze.\n")

    # ── Faza 1: Prevodi ──
    logger.info("--- FAZA 1: PREVODI ---")
    translations = {}
    for model_key, model_str in MODELS.items():
        translations[model_key] = batch_translate(model_key, model_str, sentences)

    # ── Faza 2: Pairwise ──
    logger.info("\n--- FAZA 2: PAIRWISE ---")
    # wins[model] = ukupan broj pobjeda
    wins = {k: 0 for k in MODELS}
    # head2head[A][B] = broj puta A pobijedio B
    h2h = {a: {b: 0 for b in MODELS if b != a} for a in MODELS}
    # results[pair_label][sent_id] = pobjednik
    pair_results = {}

    for key_A, key_B, judge_key in PAIRS:
        judge_str = MODELS[judge_key]
        verdicts = batch_pairwise(
            judge_key, judge_str, sentences,
            translations[key_A], translations[key_B],
            key_A, key_B
        )
        label = f"{key_A} vs {key_B}"
        pair_results[label] = {}
        for sid, verdict in verdicts.items():
            winner = key_A if verdict == "A" else key_B
            pair_results[label][sid] = winner
            wins[winner] += 1
            h2h[winner][key_B if winner == key_A else key_A] += 1

    # ── Output ──
    logger.info("\n--- REZULTATI ---\n")

    # Head-to-head tabela
    print("\n=== HEAD-TO-HEAD (sudija → pobjednik) ===")
    for key_A, key_B, judge_key in PAIRS:
        label = f"{key_A} vs {key_B}"
        verdicts = pair_results[label]
        a_wins = sum(1 for v in verdicts.values() if v == key_A)
        b_wins = sum(1 for v in verdicts.values() if v == key_B)
        print(f"  {key_A:>10} vs {key_B:<10} (sudi {judge_key}): "
              f"{key_A}={a_wins}  {key_B}={b_wins}")

    # Ukupne pobjede
    print("\n=== UKUPNE POBJEDE (od 80 mogućih) ===")
    for model_key in sorted(wins, key=wins.get, reverse=True):
        bar = "█" * wins[model_key]
        print(f"  {model_key:>10}: {wins[model_key]:>3}  {bar}")

    # Po rečenici — samo ako ima zanimljivih razlika
    print("\n=== POBJEDE PO REČENICI (gemma3 vs ministral vs gemma4) ===")
    col = 10
    header = f"{'S':>3} | {'g3 vs min':>{col}} | {'g3 vs g4':>{col}} | {'min vs g4':>{col}}"
    sep_line = "-" * len(header)
    print(sep_line)
    print(header)
    print(sep_line)
    for sid, _ in sentences:
        r1 = pair_results.get("gemma3 vs ministral", {}).get(sid, "?")
        r2 = pair_results.get("gemma3 vs gemma4",    {}).get(sid, "?")
        r3 = pair_results.get("ministral vs gemma4", {}).get(sid, "?")
        print(f"S{sid:>2} | {r1:>{col}} | {r2:>{col}} | {r3:>{col}}")
    print(sep_line)

    logger.info("\nGotovo.")


if __name__ == "__main__":
    main()
