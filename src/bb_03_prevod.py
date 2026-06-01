"""
bb_03_prevod.py
Prevodi rečenice, radi back-translation i računa cosine score.

Podržani engini:
  - Ollama Cloud (gemma3:12b, ministral-3:14b, gemma4:31b, ...)
  - NLLB-200 lokalno (nllb-600M) — deterministički beam search

Primjer (Ollama):
    venv/bin/python src/bb_03_prevod.py \
        --knjiga 1 --od 1 --do 40 \
        --model "gemma3:12b" --temp 0.8 \
        --embedder "paraphrase-multilingual-MiniLM-L12-v2" \
        --jezici hr it de

Primjer (NLLB):
    venv/bin/python src/bb_03_prevod.py \
        --knjiga 1 --od 1 --do 40 \
        --model "nllb-600M" \
        --embedder "paraphrase-multilingual-MiniLM-L12-v2" \
        --jezici hr fr it
"""

import os
import sys
import argparse
import requests
import psycopg2
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

DB = {
    "host":     os.getenv("DB_HOST", "balsam.dynu.net"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   "bb",
    "user":     os.getenv("DB_USER", "pgu"),
    "password": os.getenv("DB_PASSWORD"),
}

OLLAMA_URL  = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY  = os.getenv("OLLAMA_API_KEY", "")
BATCH_SIZE  = 20

# Mapping: naziv u bb_embeddings → HuggingFace model path
EMBEDDER_PATH_MAP = {
    "multilingual-e5-large": "intfloat/multilingual-e5-large",
    "paraphrase-multilingual-MiniLM-L12-v2": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
}

NLLB_MODEL_NAME = "facebook/nllb-200-distilled-600M"

NLLB_LANG_MAP = {
    "hr": "hrv_Latn",
    "sr": "srp_Cyrl",
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
}

JEZIK_NAZIVI = {
    "hr": "Croatian",
    "sr": "Serbian",
    "bs": "Bosnian",
    "sl": "Slovenian",
    "mk": "Macedonian",
    "bg": "Bulgarian",
    "de": "German",
    "nl": "Dutch",
    "af": "Afrikaans",
    "fr": "French",
    "it": "Italian",
    "es": "Spanish",
    "pt": "Portuguese",
    "ro": "Romanian",
}


# ── NLLB ────────────────────────────────────────────────────────────────────

def load_nllb():
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    print(f"Učitavam NLLB model: {NLLB_MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL_NAME)
    model     = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL_NAME)
    return tokenizer, model


def nllb_batch(texts, tokenizer, model, src_lang, tgt_lang):
    tokenizer.src_lang = src_lang
    inputs = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    )
    generated = model.generate(
        **inputs,
        forced_bos_token_id=tokenizer.convert_tokens_to_ids(tgt_lang),
        max_length=512,
        repetition_penalty=1.3,
        do_sample=False,
    )
    return tokenizer.batch_decode(generated, skip_special_tokens=True)


def nllb_single(text, tokenizer, model, src_lang, tgt_lang):
    return nllb_batch([text], tokenizer, model, src_lang, tgt_lang)[0]


# ── Ollama ──────────────────────────────────────────────────────────────────

def ollama_chat(model, temperature, messages):
    headers = {"Content-Type": "application/json"}
    if OLLAMA_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_KEY}"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, headers=headers, timeout=120)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def prevedi_batch(tekstovi, jezik_naziv, model, temp):
    numerirani = "\n".join(f"{i+1}. {t}" for i, t in enumerate(tekstovi))
    prompt = (
        f"Translate the following English texts to {jezik_naziv}.\n"
        f"Output ONLY the translations as a numbered list, one per line, nothing else.\n\n"
        f"{numerirani}"
    )
    try:
        odgovor = ollama_chat(model, temp, [{"role": "user", "content": prompt}])
        linije = [l.strip() for l in odgovor.splitlines() if l.strip()]
        prevodi = []
        for l in linije:
            if l and l[0].isdigit() and ". " in l:
                prevodi.append(l.split(". ", 1)[1].strip())
            else:
                prevodi.append(l)
        if len(prevodi) == len(tekstovi):
            return prevodi
        return None
    except Exception as e:
        print(f"  [batch error] {e}")
        return None


def prevedi_single(tekst, jezik_naziv, model, temp):
    prompt = (
        f"Translate the following English text to {jezik_naziv}.\n"
        f"Output only the translation, nothing else.\n\n"
        f"{tekst}"
    )
    return ollama_chat(model, temp, [{"role": "user", "content": prompt}])


def back_prevedi_batch(prevodi, jezik_naziv, model, temp):
    numerirani = "\n".join(f"{i+1}. {t}" for i, t in enumerate(prevodi))
    prompt = (
        f"Translate the following {jezik_naziv} texts to English.\n"
        f"Output ONLY the translations as a numbered list, one per line, nothing else.\n\n"
        f"{numerirani}"
    )
    try:
        odgovor = ollama_chat(model, temp, [{"role": "user", "content": prompt}])
        linije = [l.strip() for l in odgovor.splitlines() if l.strip()]
        rezultati = []
        for l in linije:
            if l and l[0].isdigit() and ". " in l:
                rezultati.append(l.split(". ", 1)[1].strip())
            else:
                rezultati.append(l)
        if len(rezultati) == len(prevodi):
            return rezultati
        return None
    except Exception as e:
        print(f"  [batch error] {e}")
        return None


def back_prevedi_single(prevod, jezik_naziv, model, temp):
    prompt = (
        f"Translate the following {jezik_naziv} text to English.\n"
        f"Output only the translation, nothing else.\n\n"
        f"{prevod}"
    )
    return ollama_chat(model, temp, [{"role": "user", "content": prompt}])


# ── Embeddings & score ──────────────────────────────────────────────────────

def cosine(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# ── DB helpers ──────────────────────────────────────────────────────────────

def get_or_create_prevodi_knjige(cur, knjiga_id, jezik_id, model_id, embeddings_id):
    cur.execute("""
        INSERT INTO bb_prevodi_knjige (knjiga_id, jezik_id, model_id, embeddings_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (knjiga_id, jezik_id, model_id, embeddings_id) DO NOTHING
        RETURNING id
    """, (knjiga_id, jezik_id, model_id, embeddings_id))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("""
        SELECT id FROM bb_prevodi_knjige
        WHERE knjiga_id=%s AND jezik_id=%s AND model_id=%s AND embeddings_id=%s
    """, (knjiga_id, jezik_id, model_id, embeddings_id))
    return cur.fetchone()[0]


def get_recenice(cur, knjiga_id, od, do):
    cur.execute("""
        SELECT id, pozicija, tekst FROM bb_recenice
        WHERE knjiga_id = %s AND pozicija BETWEEN %s AND %s
        ORDER BY pozicija
    """, (knjiga_id, od, do))
    return cur.fetchall()


def already_done(cur, prevodi_knjige_id, recenica_id):
    cur.execute("""
        SELECT 1 FROM bb_prevodi_recenica
        WHERE prevodi_knjige_id = %s AND recenica_id = %s
    """, (prevodi_knjige_id, recenica_id))
    return cur.fetchone() is not None


def upisi_prevod(cur, prevodi_knjige_id, recenica_id, prevod, back_translation, score, translation_score):
    cur.execute("""
        INSERT INTO bb_prevodi_recenica
            (prevodi_knjige_id, recenica_id, prevod, back_translation, score, translation_score)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (prevodi_knjige_id, recenica_id) DO NOTHING
    """, (prevodi_knjige_id, recenica_id, prevod, back_translation, score, translation_score))


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    import functools
    global print
    print = functools.partial(print, flush=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--knjiga",   type=int,   required=True)
    parser.add_argument("--od",       type=int,   required=True)
    parser.add_argument("--do",       type=int,   required=True)
    parser.add_argument("--model",    type=str,   required=True)
    parser.add_argument("--temp",     type=float, default=0.0)
    parser.add_argument("--embedder", type=str,   required=True)
    parser.add_argument("--jezici",   type=str,   nargs="+", required=True)
    args = parser.parse_args()

    is_nllb = (args.model == "nllb-600M")

    embedder_path = EMBEDDER_PATH_MAP.get(args.embedder, args.embedder)
    print(f"Učitavam embedder: {args.embedder} ({embedder_path})")
    embedder = SentenceTransformer(embedder_path)

    nllb_tok, nllb_mod = (None, None)
    if is_nllb:
        nllb_tok, nllb_mod = load_nllb()

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    cur.execute(
        "SELECT id FROM bb_modeli WHERE naziv=%s AND ROUND(temperatura::numeric,4)=ROUND(%s::numeric,4)",
        (args.model, args.temp)
    )
    row = cur.fetchone()
    if not row:
        print(f"Model '{args.model}' temp={args.temp} nije u bb_modeli!")
        sys.exit(1)
    model_id = row[0]

    cur.execute("SELECT id FROM bb_embeddings WHERE naziv=%s", (args.embedder,))
    row = cur.fetchone()
    if not row:
        print(f"Embedder '{args.embedder}' nije u bb_embeddings!")
        sys.exit(1)
    embeddings_id = row[0]

    recenice = get_recenice(cur, args.knjiga, args.od, args.do)
    print(f"Rečenica za obradu: {len(recenice)} (pozicije {args.od}–{args.do})")
    print(f"Model: {args.model} | temp: {args.temp} | engine: {'NLLB' if is_nllb else 'Ollama'}")

    for kod in args.jezici:
        jezik_naziv = JEZIK_NAZIVI.get(kod)
        if not jezik_naziv:
            print(f"Nepoznat jezik: {kod}, preskačem.")
            continue

        if is_nllb and kod not in NLLB_LANG_MAP:
            print(f"NLLB ne podržava jezik: {kod}, preskačem.")
            continue

        cur.execute("SELECT id FROM bb_jezik WHERE kod=%s", (kod,))
        jezik_id = cur.fetchone()[0]

        prevodi_knjige_id = get_or_create_prevodi_knjige(
            cur, args.knjiga, jezik_id, model_id, embeddings_id
        )
        conn.commit()

        print(f"\n── Jezik: {kod} ({jezik_naziv}), prevodi_knjige_id={prevodi_knjige_id} ──")

        todo = [(rid, poz, tekst) for rid, poz, tekst in recenice
                if not already_done(cur, prevodi_knjige_id, rid)]
        print(f"  Preostalo: {len(todo)} rečenica")

        for i in range(0, len(todo), BATCH_SIZE):
            chunk = todo[i:i + BATCH_SIZE]
            tekstovi = [t for _, _, t in chunk]

            print(f"  Batch {i//BATCH_SIZE + 1}: pozicije {chunk[0][1]}–{chunk[-1][1]}")

            if is_nllb:
                nllb_tgt = NLLB_LANG_MAP[kod]
                prevodi = nllb_batch(tekstovi, nllb_tok, nllb_mod, "eng_Latn", nllb_tgt)
                backs   = nllb_batch(prevodi,  nllb_tok, nllb_mod, nllb_tgt, "eng_Latn")
            else:
                prevodi = prevedi_batch(tekstovi, jezik_naziv, args.model, args.temp)
                if prevodi is None:
                    print("    Fallback na single prevod...")
                    prevodi = [prevedi_single(t, jezik_naziv, args.model, args.temp)
                               for t in tekstovi]

                backs = back_prevedi_batch(prevodi, jezik_naziv, args.model, args.temp)
                if backs is None:
                    print("    Fallback na single back-translation...")
                    backs = [back_prevedi_single(p, jezik_naziv, args.model, args.temp)
                             for p in prevodi]

            en_vektori     = embedder.encode(tekstovi)
            back_vektori   = embedder.encode(backs)
            prevod_vektori = embedder.encode(prevodi)

            for j, (rid, poz, tekst) in enumerate(chunk):
                score             = cosine(en_vektori[j], back_vektori[j])
                translation_score = cosine(en_vektori[j], prevod_vektori[j])
                upisi_prevod(cur, prevodi_knjige_id, rid,
                             prevodi[j], backs[j], score, translation_score)
                print(f"    s{poz}: score={score:.4f} ts={translation_score:.4f}")

            conn.commit()

        print(f"  Jezik {kod} gotov.")

    cur.close()
    conn.close()
    print("\nGotovo.")


if __name__ == "__main__":
    main()
