#!/usr/bin/env python3
"""
Buchenberg · run_test.py
Glavni test runner — prevod + back-translation + scoring.

Podržane metode:
  nllb          — NLLB-200 beam search (deterministički, repetition_penalty=1.3)
  nllb_t05      — NLLB-200 sampling, temperature=0.5 (kreativniji, stohastičan)
  gemma         — Gemma 3 12b (Ollama Cloud), default temperatura
  gemma_t05     — Gemma 3 12b (Ollama Cloud), temperature=0.5 (konzervativniji)
  ministral     — Ministral 3 14b (Ollama Cloud), default temperatura
  ministral_t05 — Ministral 3 14b (Ollama Cloud), temperature=0.5 (konzervativniji)

Registracija (prvi put):
  venv/bin/python src/run_test.py --test_id test_001 \
    --book hound_of_the_baskervilles --sent_from 1 --sent_to 20 \
    --score_from 0.0 --score_to 0.899 \
    --langs sr --methods nllb gemma nllb_t05 gemma_t05

Batch processing (default batch_size=20):
  venv/bin/python src/run_test.py --test_id test_001 --batch_size 20

Ponovni run (samo ID, koristi parametre iz registry):
  venv/bin/python src/run_test.py --test_id test_001

Napomena o NLLB metodama:
  nllb     koristi beam search (do_sample=False) — deterministički output.
  nllb_t05 koristi do_sample=True + temperature=0.5 — stohastičan, ali
           konzervativniji od temperature=1.0. Oba dijele isti učitani model.

Napomena o Gemma metodama:
  gemma     ne šalje temperature parametar (Ollama koristi default).
  gemma_t05 šalje temperature=0.5 u API poziv.
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
EMBED_MODEL  = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_URL   = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_MODEL     = os.getenv("OLLAMA_MODEL", "gemma3:12b")
MINISTRAL_MODEL  = os.getenv("MINISTRAL_MODEL", "ministral-3:14b")
GEMMA4_MODEL     = "gemma4:31b-cloud"
OLLAMA_KEY   = os.getenv("OLLAMA_API_KEY", "")

# Validne metode — jedini izvor istine
VALID_METHODS = {"nllb", "nllb_t05", "gemma", "gemma_t05", "ministral", "ministral_t05", "gemma4", "gemma4_t05"}

# NLLB jezik kodovi (ISO 639-1 → NLLB BCP-47 / FLORES-200)
LANG_MAP = {
    "sr": "srp_Cyrl",
    "hr": "hrv_Latn",
    "bs": "bos_Latn",
    "sl": "slv_Latn",
    "mk": "mkd_Cyrl",
    "bg": "bul_Cyrl",
    "de": "deu_Latn",
    "nl": "nld_Latn",
    "af": "afr_Latn",
    "fr": "fra_Latn",
    "it": "ita_Latn",
    "es": "spa_Latn",
    "pt": "por_Latn",
    "ro": "ron_Latn",
    "en": "eng_Latn",
}

# Gemma jezik nazivi (ISO 639-1 → puni naziv za prompt)
LANG_NAMES = {
    "sr": "Serbian (Cyrillic)", "hr": "Croatian",  "bs": "Bosnian",
    "sl": "Slovenian",          "mk": "Macedonian", "bg": "Bulgarian",
    "de": "German",             "nl": "Dutch",      "af": "Afrikaans",
    "fr": "French",             "it": "Italian",    "es": "Spanish",
    "pt": "Portuguese",         "ro": "Romanian",
}

# Gemma back-translation jezik nazivi
LANG_NAMES_BACK = {
    "sr": "Serbian", "hr": "Croatian",  "bs": "Bosnian",
    "sl": "Slovenian", "mk": "Macedonian", "bg": "Bulgarian",
    "de": "German",  "nl": "Dutch",      "af": "Afrikaans",
    "fr": "French",  "it": "Italian",    "es": "Spanish",
    "pt": "Portuguese", "ro": "Romanian",
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


def filter_sentences_by_score(conn, sentences, test_id, lang, score_from, score_to):
    """
    Filtrira rečenice čiji MAX translation_score (za dati test_id I target_lang)
    pada u interval [score_from, score_to].
    Ako score_from=0.0 i score_to=1.0 — vraća sve (bez filtera).
    Rečenice koje nemaju nijedan skor u bazi uvijek se uključuju.
    """
    if score_from == 0.0 and score_to == 1.0:
        return sentences

    cur = conn.cursor()
    cur.execute("""
        SELECT sentence_id, MAX(translation_score) as best
        FROM test_results
        WHERE test_id = %s AND target_lang = %s
        GROUP BY sentence_id
    """, (test_id, lang))
    rows = cur.fetchall()
    scored = {row[0]: row[1] for row in rows}

    filtered = []
    for sent_id, text in sentences:
        best = scored.get(sent_id)
        if best is None:
            filtered.append((sent_id, text))
        elif score_from <= best <= score_to:
            filtered.append((sent_id, text))

    return filtered


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
    return rows  # lista (id, text)


# ── Prevod — NLLB ─────────────────────────────────────────────────────────────

def load_nllb():
    logger.info(f"Učitavanje NLLB modela: {NLLB_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL)
    model     = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)
    return tokenizer, model


def translate_nllb(text, tokenizer, model, src_lang="eng_Latn", tgt_lang="srp_Cyrl",
                   temperature=None):
    """
    Prevod koristeći NLLB-200.

    temperature=None  → beam search (deterministički) — metoda 'nllb'
    temperature=float → sampling (do_sample=True)     — metoda 'nllb_t05'
    """
    tokenizer.src_lang = src_lang
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

    gen_kwargs = dict(
        forced_bos_token_id=tokenizer.convert_tokens_to_ids(tgt_lang),
        max_length=512,
        repetition_penalty=1.3,
    )
    if temperature is not None:
        gen_kwargs["do_sample"]   = True
        gen_kwargs["temperature"] = temperature
    else:
        gen_kwargs["do_sample"] = False  # beam search (default, eksplicitno)

    translated = model.generate(**inputs, **gen_kwargs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)


# ── Prevod — Gemma (Ollama Cloud) ─────────────────────────────────────────────

def translate_gemma(text, tgt_lang_code, temperature=None, model=None):
    """
    Prevod koristeći Gemma 3 12b via Ollama Cloud.

    temperature=None  → API poziv bez temperature parametra (Ollama default)
    temperature=float → eksplicitna temperatura u API pozivu
    """
    lang_name = LANG_NAMES.get(tgt_lang_code, tgt_lang_code)
    prompt = (
        f"Translate the following English text to {lang_name}. "
        f"Return only the translation, no explanation.\n\n"
        f"Text: {text}"
    )
    payload = {
        "model":    model or OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream":   False,
    }
    if temperature is not None:
        payload["options"] = {"temperature": temperature}

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


# ── Back-translation — Gemma ──────────────────────────────────────────────────

def back_translate_gemma(translated_text, src_lang_code, temperature=None, model=None):
    """
    Back-translation koristeći Gemma 3 12b via Ollama Cloud.

    temperature=None  → API poziv bez temperature parametra (Ollama default)
    temperature=float → eksplicitna temperatura u API pozivu
    """
    lang_name = LANG_NAMES_BACK.get(src_lang_code, src_lang_code)
    prompt = (
        f"Translate the following {lang_name} text to English. "
        f"Return only the translation, no explanation.\n\n"
        f"Text: {translated_text}"
    )
    payload = {
        "model":    model or OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream":   False,
    }
    if temperature is not None:
        payload["options"] = {"temperature": temperature}

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()




# ── Robusno parsiranje Gemma batch odgovora ───────────────────────────────────

def parse_separator_response(raw, n, context="batch"):
    """
    Parsiranje separator-format odgovora (__!!__ kao separator između prijevoda).
    Nema navodnika, zareza, zagrada — nema JSON sintaksnih problema.

    Očekivani format:
        Prijevod rečenice 1__!!__Prijevod rečenice 2__!!__...

    Vraća listu od n stringova ili None ako parsiranje ne uspije.
    """
    import re
    SEP = "__!!__"
    parts = raw.split(SEP)
    cleaned = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # Ukloni markdown bold/italic (*tekst*, **tekst**)
        p = re.sub(r"\*+([^*]+)\*+", r"\1", p)
        p = p.strip()
        if p:
            cleaned.append(p)
    if len(cleaned) >= n:
        return cleaned[:n]
    logger.warning(f"Gemma {context}: separator parser vratio {len(cleaned)}/{n}, raw={raw[:300]}")
    return None


# ── Batch prevod — NLLB ───────────────────────────────────────────────────────

def translate_nllb_batch(texts, tokenizer, model, src_lang="eng_Latn",
                         tgt_lang="srp_Cyrl", temperature=None):
    """
    Batch prevod koristeći NLLB-200.
    Prima listu tekstova, vraća listu prevoda istog reda.

    temperature=None  → beam search (deterministički)
    temperature=float → sampling (do_sample=True)
    """
    tokenizer.src_lang = src_lang
    inputs = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    )

    gen_kwargs = dict(
        forced_bos_token_id=tokenizer.convert_tokens_to_ids(tgt_lang),
        max_length=512,
        repetition_penalty=1.3,
    )
    if temperature is not None:
        gen_kwargs["do_sample"]   = True
        gen_kwargs["temperature"] = temperature
    else:
        gen_kwargs["do_sample"] = False

    translated = model.generate(**inputs, **gen_kwargs)
    return tokenizer.batch_decode(translated, skip_special_tokens=True)


# ── Batch prevod — Gemma (Ollama Cloud) ───────────────────────────────────────

def translate_gemma_batch(texts, tgt_lang_code, temperature=None, model=None):
    """
    Batch prevod koristeći Gemma/Ministral via Ollama Cloud.
    Prima listu tekstova, vraća listu prevoda istog reda.
    Jedan API poziv za cijeli batch.

    Prompt traži __!!__ separator format — bez JSON sintaksnih problema.
    Fallback: ako parsiranje ne uspije, prevodi jednu po jednu.
    """
    lang_name = LANG_NAMES.get(tgt_lang_code, tgt_lang_code)
    n = len(texts)

    numbered = "\n".join(f'{i+1}. {t}' for i, t in enumerate(texts))
    prompt = (
        f"Translate these {n} sentences to {lang_name}.\n"
        f"You MUST return exactly {n} translations separated by __!!__ — one per input sentence.\n"
        f"Even if a sentence is very short (one word, a title, a name) — it still gets its own translation.\n"
        f"Do not merge sentences. Do not add numbering, markdown, or explanations.\n"
        f"Example format: First translation__!!__Second translation__!!__Third translation\n\n"
        f"{numbered}"
    )

    payload = {
        "model":    model or OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream":   False,
    }
    if temperature is not None:
        payload["options"] = {"temperature": temperature}

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    raw = response.json()["message"]["content"].strip()

    result = parse_separator_response(raw, n, context=f"translate\u2192{tgt_lang_code}")
    if result:
        return result
    logger.warning(f"Gemma batch translate\u2192{tgt_lang_code}: fallback na single ({n} rečenica)")
    return [translate_gemma(t, tgt_lang_code, temperature, model=model) for t in texts]


def back_translate_gemma_batch(texts, src_lang_code, temperature=None, model=None):
    """
    Batch back-translation koristeći Gemma/Ministral via Ollama Cloud.
    Prima listu tekstova na src_lang_code, vraća listu engleskih prevoda.

    Prompt traži __!!__ separator format — bez JSON sintaksnih problema.
    Fallback: ako parsiranje ne uspije, prevodi jednu po jednu.
    """
    lang_name = LANG_NAMES_BACK.get(src_lang_code, src_lang_code)
    n = len(texts)

    numbered = "\n".join(f'{i+1}. {t}' for i, t in enumerate(texts))
    prompt = (
        f"Translate these {n} {lang_name} sentences to English.\n"
        f"You MUST return exactly {n} translations separated by __!!__ — one per input sentence.\n"
        f"Even if a sentence is very short (one word, a title, a name) — it still gets its own translation.\n"
        f"Do not merge sentences. Do not add numbering, markdown, or explanations.\n"
        f"Example format: First translation__!!__Second translation__!!__Third translation\n\n"
        f"{numbered}"
    )

    payload = {
        "model":    model or OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream":   False,
    }
    if temperature is not None:
        payload["options"] = {"temperature": temperature}

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    raw = response.json()["message"]["content"].strip()

    result = parse_separator_response(raw, n, context=f"back\u2192{src_lang_code}")
    if result:
        return result
    logger.warning(f"Gemma back-batch\u2192{src_lang_code}: fallback na single ({n} rečenica)")
    return [back_translate_gemma(t, src_lang_code, temperature, model=model) for t in texts]


# ── Scoring ───────────────────────────────────────────────────────────────────

def load_embedder():
    logger.info(f"Učitavanje embedding modela: {EMBED_MODEL}")
    return SentenceTransformer(EMBED_MODEL, local_files_only=True)


def compute_score(original, back_translation, embedder):
    vecs = embedder.encode([original, back_translation])
    return float(cosine_similarity([vecs[0]], [vecs[1]])[0][0])


# ── DB operacije ──────────────────────────────────────────────────────────────

def clear_test(conn, test_id, langs, methods):
    """Briše rezultate samo za kombinaciju test_id + langs + methods."""
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM test_results WHERE test_id = %s AND target_lang = ANY(%s) AND method = ANY(%s)",
        (test_id, langs, methods)
    )
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    logger.info(f"Obrisano {deleted} starih rezultata za {test_id} langs={langs} methods={methods}")


def insert_result(conn, test_id, sentence_id, target_lang, method,
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


# ── Method dispatch ───────────────────────────────────────────────────────────

def dispatch_translate(method, text, lang, nllb_lang, nllb_tok, nllb_mod):
    """Prevod EN → lang za datu metodu. Vraća translated string."""
    if method == "nllb":
        return translate_nllb(text, nllb_tok, nllb_mod,
                              tgt_lang=nllb_lang, temperature=None)
    elif method == "nllb_t05":
        return translate_nllb(text, nllb_tok, nllb_mod,
                              tgt_lang=nllb_lang, temperature=0.5)
    elif method == "gemma":
        return translate_gemma(text, lang, temperature=None)
    elif method == "gemma_t05":
        return translate_gemma(text, lang, temperature=0.5)
    elif method == "ministral":
        return translate_gemma(text, lang, temperature=None, model=MINISTRAL_MODEL)
    elif method == "ministral_t05":
        return translate_gemma(text, lang, temperature=0.5, model=MINISTRAL_MODEL)
    elif method == "gemma4":
        return translate_gemma(text, lang, temperature=None, model=GEMMA4_MODEL)
    elif method == "gemma4_t05":
        return translate_gemma(text, lang, temperature=0.5, model=GEMMA4_MODEL)
    else:
        raise ValueError(f"Nepoznata metoda: {method}")


def dispatch_back_translate(method, translated, lang, nllb_lang, nllb_tok, nllb_mod):
    """Back-translation lang → EN za datu metodu. Vraća back string."""
    if method in ("nllb", "nllb_t05"):
        return translate_nllb(translated, nllb_tok, nllb_mod,
                              src_lang=nllb_lang, tgt_lang="eng_Latn",
                              temperature=None if method == "nllb" else 0.5)
    elif method in ("gemma", "gemma_t05"):
        temp = None if method == "gemma" else 0.5
        return back_translate_gemma(translated, lang, temperature=temp)
    elif method in ("ministral", "ministral_t05"):
        temp = None if method == "ministral" else 0.5
        return back_translate_gemma(translated, lang, temperature=temp, model=MINISTRAL_MODEL)
    elif method in ("gemma4", "gemma4_t05"):
        temp = None if method == "gemma4" else 0.5
        return back_translate_gemma(translated, lang, temperature=temp, model=GEMMA4_MODEL)
    else:
        raise ValueError(f"Nepoznata metoda: {method}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Buchenberg test runner")
    parser.add_argument("--test_id",    required=True)
    parser.add_argument("--book",       default=None)
    parser.add_argument("--sent_from",  type=int, default=None)
    parser.add_argument("--sent_to",    type=int, default=None)
    parser.add_argument("--score_from", type=float, default=0.0,
                        help="Minimalni MAX translation_score (default: 0.0)")
    parser.add_argument("--score_to",   type=float, default=1.0,
                        help="Maksimalni MAX translation_score (default: 1.0)")
    parser.add_argument("--langs",      nargs="+", default=None)
    parser.add_argument("--methods",    nargs="+", default=None)
    parser.add_argument("--batch_size", type=int, default=20,
                        help="Broj rečenica po batchu (default: 20)")
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

    # Command line override — ako su --langs ili --methods zadani, koriste se umjesto registry
    if args.langs:
        langs   = args.langs
        logger.info(f"Override langs: {langs}")
    if args.methods:
        methods = args.methods
        logger.info(f"Override methods: {methods}")

    # Validacija metoda
    unknown = set(methods) - VALID_METHODS
    if unknown:
        logger.error(f"Nepoznate metode: {unknown}. Validne: {VALID_METHODS}")
        sys.exit(1)

    logger.info(f"Parametri: book={book}, sent={sent_from}-{sent_to}, "
                f"langs={langs}, methods={methods}")

    # Učitaj alate
    embedder = load_embedder()

    # NLLB — učitaj jednom, koriste ga i nllb i nllb_t05
    nllb_tok, nllb_mod = (None, None)
    if any(m in methods for m in ("nllb", "nllb_t05")):
        nllb_tok, nllb_mod = load_nllb()

    # DB
    conn = get_conn()
    sentences = load_sentences(conn, book, sent_from, sent_to)
    logger.info(f"Rečenica učitano: {len(sentences)}")

    total = len(sentences) * len(langs) * len(methods)
    done  = 0
    batch_size = args.batch_size

    for lang in langs:
        nllb_lang = LANG_MAP.get(lang)
        if not nllb_lang:
            logger.warning(f"Nepoznat jezik: {lang} — preskačem")
            continue

        sentences_for_lang = filter_sentences_by_score(
            conn, sentences, args.test_id, lang,
            args.score_from, args.score_to)
        logger.info(f"Rečenica nakon score filtera [{args.score_from}-{args.score_to}] za {lang}: {len(sentences_for_lang)}")

        for method in methods:
            logger.info(f"--- {lang} {method} | batch_size={batch_size} ---")

            for batch_start in range(0, len(sentences_for_lang), batch_size):
                batch = sentences_for_lang[batch_start:batch_start + batch_size]
                sids  = [s[0] for s in batch]
                texts = [s[1] for s in batch]

                try:
                    # Batch prevod EN → lang
                    if method in ("nllb", "nllb_t05"):
                        temp = 0.5 if method == "nllb_t05" else None
                        translateds = translate_nllb_batch(
                            texts, nllb_tok, nllb_mod,
                            tgt_lang=nllb_lang, temperature=temp
                        )
                    elif method in ("gemma", "gemma_t05"):
                        temp = 0.5 if method == "gemma_t05" else None
                        translateds = translate_gemma_batch(texts, lang, temperature=temp)
                    elif method in ("ministral", "ministral_t05"):
                        temp = 0.5 if method == "ministral_t05" else None
                        translateds = translate_gemma_batch(texts, lang, temperature=temp,
                                                            model=MINISTRAL_MODEL)
                    elif method in ("gemma4", "gemma4_t05"):
                        temp = 0.5 if method == "gemma4_t05" else None
                        translateds = translate_gemma_batch(texts, lang, temperature=temp,
                                                            model=GEMMA4_MODEL)

                    # Batch back-translation lang → EN
                    if method in ("nllb", "nllb_t05"):
                        temp = 0.5 if method == "nllb_t05" else None
                        backs = translate_nllb_batch(
                            translateds, nllb_tok, nllb_mod,
                            src_lang=nllb_lang, tgt_lang="eng_Latn",
                            temperature=temp
                        )
                    elif method in ("gemma", "gemma_t05"):
                        temp = 0.5 if method == "gemma_t05" else None
                        backs = back_translate_gemma_batch(translateds, lang, temperature=temp)
                    elif method in ("ministral", "ministral_t05"):
                        temp = 0.5 if method == "ministral_t05" else None
                        backs = back_translate_gemma_batch(translateds, lang, temperature=temp,
                                                           model=MINISTRAL_MODEL)
                    elif method in ("gemma4", "gemma4_t05"):
                        temp = 0.5 if method == "gemma4_t05" else None
                        backs = back_translate_gemma_batch(translateds, lang, temperature=temp,
                                                           model=GEMMA4_MODEL)

                    # Score i insert
                    for i, (sid, text) in enumerate(zip(sids, texts)):
                        translated = translateds[i]
                        back       = backs[i]
                        sc    = compute_score(text, back, embedder)
                        tr_sc = compute_score(text, translated, embedder)
                        insert_result(conn, args.test_id, sid, lang,
                                      method, translated, back, sc, tr_sc)
                        done += 1
                        logger.info(f"[{done}/{total}] s{sid} {lang} {method} "
                                    f"score={sc:.3f} | {translated[:50]}...")

                except Exception as e:
                    logger.error(f"Greška batch {lang} {method} s{sids[0]}-s{sids[-1]}: {e}")
                    logger.info("Fallback na single mode...")
                    for sid, text in zip(sids, texts):
                        try:
                            translated = dispatch_translate(
                                method, text, lang, nllb_lang, nllb_tok, nllb_mod)
                            back = dispatch_back_translate(
                                method, translated, lang, nllb_lang, nllb_tok, nllb_mod)
                            sc    = compute_score(text, back, embedder)
                            tr_sc = compute_score(text, translated, embedder)
                            insert_result(conn, args.test_id, sid, lang,
                                          method, translated, back, sc, tr_sc)
                            done += 1
                            logger.info(f"[{done}/{total}] s{sid} {lang} {method} "
                                        f"score={sc:.3f} | {translated[:50]}...")
                        except Exception as e2:
                            logger.error(f"Greška single s{sid} {lang} {method}: {e2}")

    update_winners(conn, args.test_id)
    conn.close()

    logger.info(f"=== {args.test_id} DONE — {done}/{total} ===")
    print(f"\n✓ {args.test_id} završen: {done}/{total} prevoda")


if __name__ == "__main__":
    main()
