#!/usr/bin/env python3
"""
Buchenberg · run_ga.py
Genetski algoritam za optimizaciju prevoda jedne ili više rečenica.

Pokretanje:
  # Jedna rečenica, jedan jezik:
  venv/bin/python src/run_ga.py --test_id test_012 --sentence_id 5 --lang it

  # Raspon rečenica:
  venv/bin/python src/run_ga.py --test_id test_012 --sent_from 1 --sent_to 10 --lang it

  # Više jezika:
  venv/bin/python src/run_ga.py --test_id test_012 --sent_from 1 --sent_to 5 --lang it fr de

GA parametri (mogu se mijenjati):
  --pop_size      8      Maksimalna veličina populacije
  --elite_n       2      Broj elitnih individua
  --max_gen       20     Maksimalan broj generacija
  --conv_thresh   0.005  Prag konvergencije
  --conv_gens     3      Generacija bez poboljšanja → stop
  --quality_stop  0.95   Fitness > ovo → stop
  --mutate_rate   0.15   Stopa mutacije (0.0–1.0)
  --dup_thresh    0.99   Cosine > ovo → duplikat
"""

import os
import sys
import random
import argparse
import psycopg2
from dotenv import load_dotenv
from loguru import logger
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import requests

# ── Setup ────────────────────────────────────────────────────────────────────

load_dotenv()

LOG_DIR      = os.getenv("BUCH_LOG", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

NLLB_MODEL   = "facebook/nllb-200-distilled-600M"
EMBED_MODEL  = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_URL   = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:12b")
OLLAMA_KEY   = os.getenv("OLLAMA_API_KEY", "")

# NLLB jezik kodovi
LANG_MAP = {
    "sr": "srp_Cyrl", "hr": "hrv_Latn", "bs": "bos_Latn",
    "sl": "slv_Latn", "mk": "mkd_Cyrl", "bg": "bul_Cyrl",
    "de": "deu_Latn", "nl": "nld_Latn", "af": "afr_Latn",
    "fr": "fra_Latn", "it": "ita_Latn", "es": "spa_Latn",
    "pt": "por_Latn", "ro": "ron_Latn", "en": "eng_Latn",
}

# Gemma jezik nazivi
LANG_NAMES = {
    "sr": "Serbian (Cyrillic)", "hr": "Croatian",  "bs": "Bosnian",
    "sl": "Slovenian",          "mk": "Macedonian", "bg": "Bulgarian",
    "de": "German",             "nl": "Dutch",      "af": "Afrikaans",
    "fr": "French",             "it": "Italian",    "es": "Spanish",
    "pt": "Portuguese",         "ro": "Romanian",
}


# ── DB ───────────────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def load_sentence(conn, sentence_id):
    cur = conn.cursor()
    cur.execute("SELECT id, text FROM sentences WHERE id = %s", (sentence_id,))
    row = cur.fetchone()
    cur.close()
    return row


def load_sentences_range(conn, sent_from, sent_to):
    cur = conn.cursor()
    cur.execute(
        "SELECT id, text FROM sentences WHERE id BETWEEN %s AND %s ORDER BY id",
        (sent_from, sent_to)
    )
    rows = cur.fetchall()
    cur.close()
    return rows


def get_existing_translation(conn, sentence_id, lang, test_id):
    """Dohvati postojeći prevod iz test_results za konkretan test_id."""
    cur = conn.cursor()
    cur.execute("""
        SELECT translated_text, method
        FROM test_results
        WHERE sentence_id = %s AND target_lang = %s AND test_id = %s
        ORDER BY translation_score DESC NULLS LAST
        LIMIT 1
    """, (sentence_id, lang, test_id))
    row = cur.fetchone()
    cur.close()
    return row


def save_individua(conn, test_id, sentence_id, lang, generation, individua_id,
                   tekst, fitness, pivot_lang, metoda, je_elita, je_pobjednik):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ga_results
            (test_id, sentence_id, target_lang, generation, individua_id,
             tekst, fitness, pivot_lang, metoda, je_elita, je_pobjednik)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (test_id, sentence_id, lang, generation, individua_id,
          tekst, fitness, pivot_lang, metoda, je_elita, je_pobjednik))
    conn.commit()
    cur.close()


def clear_ga(conn, test_id, sentence_id, lang):
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM ga_results WHERE test_id = %s AND sentence_id = %s AND target_lang = %s",
        (test_id, sentence_id, lang)
    )
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    logger.info(f"Obrisano {deleted} starih GA rezultata za {test_id} s{sentence_id} {lang}")


# ── Modeli ───────────────────────────────────────────────────────────────────

def load_nllb():
    logger.info(f"Učitavanje NLLB: {NLLB_MODEL}")
    tok = AutoTokenizer.from_pretrained(NLLB_MODEL)
    mod = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)
    return tok, mod


def load_embedder():
    logger.info(f"Učitavanje embeddera: {EMBED_MODEL}")
    return SentenceTransformer(EMBED_MODEL, local_files_only=True)


# ── Prevod ───────────────────────────────────────────────────────────────────

def translate_nllb(text, tok, mod, src_lang, tgt_lang):
    tok.src_lang = src_lang
    inputs = tok(text, return_tensors="pt", truncation=True, max_length=512)
    out = mod.generate(
        **inputs,
        forced_bos_token_id=tok.convert_tokens_to_ids(tgt_lang),
        max_length=512,
        repetition_penalty=1.3,
        do_sample=False,
    )
    return tok.decode(out[0], skip_special_tokens=True)


def translate_gemma(text, src_lang_name, tgt_lang_name):
    prompt = (
        f"Translate the following {src_lang_name} text to {tgt_lang_name}. "
        f"Return only the translation, no explanation.\n\nText: {text}"
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


def translate(text, src_lang, tgt_lang, metoda, nllb_tok, nllb_mod):
    """Generički prevod — dispatcher po metodi."""
    src_nllb = LANG_MAP.get(src_lang, "eng_Latn")
    tgt_nllb = LANG_MAP.get(tgt_lang, "eng_Latn")
    src_name = LANG_NAMES.get(src_lang, "English")
    tgt_name = LANG_NAMES.get(tgt_lang, src_lang)

    if metoda == "nllb":
        return translate_nllb(text, nllb_tok, nllb_mod, src_nllb, tgt_nllb)
    elif metoda == "gemma":
        return translate_gemma(text, src_name, tgt_name)
    else:
        raise ValueError(f"Nepoznata metoda: {metoda}")


# ── Fitness ──────────────────────────────────────────────────────────────────

def fitness(original, kandidat, embedder):
    vecs = embedder.encode([original, kandidat])
    return float(cosine_similarity([vecs[0]], [vecs[1]])[0][0])


def cosine_pair(tekst1, tekst2, embedder):
    vecs = embedder.encode([tekst1, tekst2])
    return float(cosine_similarity([vecs[0]], [vecs[1]])[0][0])


# ── GA operatori ─────────────────────────────────────────────────────────────

def inicijalizacija(original, lang, test_id, conn, nllb_tok, nllb_mod, embedder):
    """
    Početna populacija — individue iz test_results za konkretan test_id,
    ili svježe generirane sa nllb i gemma ako nema dovoljno.
    """
    populacija = []

    # Uzmi sve prevode za ovu rečenicu iz zadanog testa
    cur = conn.cursor()
    cur.execute("""
        SELECT translated_text, method, translation_score
        FROM test_results
        WHERE sentence_id = (
            SELECT id FROM sentences WHERE text = %s LIMIT 1
        ) AND target_lang = %s AND test_id = %s
        ORDER BY translation_score DESC NULLS LAST
    """, (original, lang, test_id))
    rows = cur.fetchall()
    cur.close()

    for tekst, metoda, sc in rows:
        if tekst:
            sc = sc if sc else fitness(original, tekst, embedder)
            populacija.append({
                "tekst":   tekst,
                "fitness": sc,
                "metoda":  metoda,
                "pivot":   None,
            })

    # Ako nema dovoljno — generiši svježe
    if len(populacija) < 2:
        for metoda in ["nllb", "gemma"]:
            try:
                tekst = translate(original, "en", lang, metoda, nllb_tok, nllb_mod)
                sc = fitness(original, tekst, embedder)
                populacija.append({"tekst": tekst, "fitness": sc,
                                   "metoda": metoda, "pivot": None})
            except Exception as e:
                logger.warning(f"Init {metoda} greška: {e}")

    populacija.sort(key=lambda x: x["fitness"], reverse=True)
    return populacija


def crossover(original, lang, test_id, dostupni_jezici, conn, nllb_tok, nllb_mod, embedder):
    """
    Crossover: EN → pivot → lang
    Pivot prevod se uzima iz baze (za isti test_id) ako postoji, inače se generira.
    """
    pivot = random.choice([j for j in dostupni_jezici if j not in ("en", lang)])
    metoda = random.choice(["nllb", "gemma"])

    # Uzmi pivot prevod iz baze (filtrirano po test_id)
    sid = _get_sentence_id(conn, original)
    row = get_existing_translation(conn, sid, pivot, test_id)

    if row:
        rf_pivot = row[0]
    else:
        # Generiši pivot prevod
        rf_pivot = translate(original, "en", pivot, metoda, nllb_tok, nllb_mod)

    # Pivot → ciljni jezik
    metoda2 = random.choice(["nllb", "gemma"])
    rf_novi = translate(rf_pivot, pivot, lang, metoda2, nllb_tok, nllb_mod)

    sc = fitness(original, rf_novi, embedder)
    return {
        "tekst":   rf_novi,
        "fitness": sc,
        "metoda":  f"{metoda}+{metoda2}",
        "pivot":   pivot,
    }


def mutacija(individua, original, lang, dostupni_jezici, nllb_tok, nllb_mod, embedder):
    """
    Mutacija: individua.tekst → pivot → lang
    Polazi od postojećeg individue, ne od originala.
    """
    pivot = random.choice([j for j in dostupni_jezici if j not in ("en", lang)])
    metoda1 = random.choice(["nllb", "gemma"])
    metoda2 = random.choice(["nllb", "gemma"])

    # individua → pivot
    rf_pivot = translate(individua["tekst"], lang, pivot, metoda1, nllb_tok, nllb_mod)

    # pivot → lang
    rf_mutirani = translate(rf_pivot, pivot, lang, metoda2, nllb_tok, nllb_mod)

    sc = fitness(original, rf_mutirani, embedder)
    return {
        "tekst":   rf_mutirani,
        "fitness": sc,
        "metoda":  f"mut:{metoda1}+{metoda2}",
        "pivot":   pivot,
    }


def selekcija(populacija, novi_kandidati, pop_size, elite_n, dup_thresh, embedder):
    """
    Elitizam + raznolikost.
    Odbacuje duplikate (cosine > dup_thresh).
    """
    svi = populacija + novi_kandidati
    svi.sort(key=lambda x: x["fitness"], reverse=True)

    # Ukloni duplikate
    filtrirani = []
    for kandidat in svi:
        je_dup = False
        for odabran in filtrirani:
            if cosine_pair(kandidat["tekst"], odabran["tekst"], embedder) > dup_thresh:
                je_dup = True
                break
        if not je_dup:
            filtrirani.append(kandidat)

    # Elita
    nova_pop = filtrirani[:elite_n]

    # Popuni do pop_size po raznolikosti
    preostali = filtrirani[elite_n:]
    while len(nova_pop) < pop_size and preostali:
        najbolji = max(preostali, key=lambda k: min(
            cosine_pair(k["tekst"], o["tekst"], embedder) for o in nova_pop
        ) if nova_pop else k["fitness"])
        nova_pop.append(preostali.pop(preostali.index(najbolji)))

    return nova_pop


def stop_kriterij(historija, trenutni_best, quality_stop, conv_thresh, conv_gens):
    if trenutni_best["fitness"] > quality_stop:
        return True, "kvalitet dostignut"
    if len(historija) >= conv_gens:
        zadnji = historija[-conv_gens:]
        if max(zadnji) - min(zadnji) < conv_thresh:
            return True, "konvergencija"
    return False, ""


def _get_sentence_id(conn, text):
    cur = conn.cursor()
    cur.execute("SELECT id FROM sentences WHERE text = %s LIMIT 1", (text,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


# ── Glavni GA loop ────────────────────────────────────────────────────────────

def ga_optimizacija(test_id, sentence_id, original, lang, dostupni_jezici, conn,
                    nllb_tok, nllb_mod, embedder, args):

    logger.info(f"=== GA START {test_id} s{sentence_id} {lang} ===")
    logger.info(f"Original: {original[:80]}")

    clear_ga(conn, test_id, sentence_id, lang)

    # Inicijalizacija
    populacija = inicijalizacija(original, lang, test_id, conn, nllb_tok, nllb_mod, embedder)
    logger.info(f"Init populacija: {len(populacija)} individua, "
                f"best={populacija[0]['fitness']:.4f}")

    # Snimi generaciju 0
    for i, ind in enumerate(populacija):
        save_individua(conn, test_id, sentence_id, lang, 0, i,
                       ind["tekst"], ind["fitness"],
                       ind.get("pivot"), ind.get("metoda"),
                       i < args.elite_n, False)

    historija = [populacija[0]["fitness"]]

    for gen in range(1, args.max_gen + 1):
        novi = []

        # Crossover
        for _ in range(args.pop_size // 2):
            try:
                kandidat = crossover(original, lang, test_id, dostupni_jezici,
                                     conn, nllb_tok, nllb_mod, embedder)
                novi.append(kandidat)
            except Exception as e:
                logger.warning(f"Crossover greška gen{gen}: {e}")

        # Mutacija
        for ind in populacija:
            if random.random() < args.mutate_rate:
                try:
                    mut = mutacija(ind, original, lang, dostupni_jezici,
                                   nllb_tok, nllb_mod, embedder)
                    novi.append(mut)
                except Exception as e:
                    logger.warning(f"Mutacija greška gen{gen}: {e}")

        # Selekcija
        populacija = selekcija(populacija, novi, args.pop_size,
                               args.elite_n, args.dup_thresh, embedder)

        trenutni_best = populacija[0]
        historija.append(trenutni_best["fitness"])

        logger.info(f"Gen {gen:02d}: best={trenutni_best['fitness']:.4f} "
                    f"pop={len(populacija)} | {trenutni_best['tekst'][:60]}...")

        # Snimi generaciju
        for i, ind in enumerate(populacija):
            save_individua(conn, test_id, sentence_id, lang, gen, i,
                           ind["tekst"], ind["fitness"],
                           ind.get("pivot"), ind.get("metoda"),
                           i < args.elite_n, False)

        # Stop kriterij
        stop, razlog = stop_kriterij(historija, trenutni_best,
                                     args.quality_stop, args.conv_thresh,
                                     args.conv_gens)
        if stop:
            logger.info(f"Stop: {razlog} nakon {gen} generacija")
            break

    # Označi pobjednika
    pobjednik = populacija[0]
    cur = conn.cursor()
    cur.execute("""
        UPDATE ga_results SET je_pobjednik = TRUE
        WHERE test_id = %s AND sentence_id = %s AND target_lang = %s
          AND tekst = %s AND generation = (
              SELECT MAX(generation) FROM ga_results
              WHERE test_id = %s AND sentence_id = %s AND target_lang = %s
          )
    """, (test_id, sentence_id, lang, pobjednik["tekst"],
          test_id, sentence_id, lang))
    conn.commit()
    cur.close()

    logger.info(f"=== GA DONE {test_id} s{sentence_id} {lang} | "
                f"fitness={pobjednik['fitness']:.4f} | {pobjednik['tekst'][:60]} ===")
    return pobjednik


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Buchenberg GA runner")
    # Test ID — obavezan
    parser.add_argument("--test_id", type=str, required=True,
                        help="Test ID (npr. test_012) — koristi se za filtriranje inicijalne populacije")
    # Rečenice
    parser.add_argument("--sentence_id", type=int, default=None)
    parser.add_argument("--sent_from",   type=int, default=None)
    parser.add_argument("--sent_to",     type=int, default=None)
    # Jezici
    parser.add_argument("--lang", nargs="+", required=True)
    # GA parametri
    parser.add_argument("--pop_size",     type=int,   default=8)
    parser.add_argument("--elite_n",      type=int,   default=2)
    parser.add_argument("--max_gen",      type=int,   default=20)
    parser.add_argument("--conv_thresh",  type=float, default=0.005)
    parser.add_argument("--conv_gens",    type=int,   default=3)
    parser.add_argument("--quality_stop", type=float, default=0.95)
    parser.add_argument("--mutate_rate",  type=float, default=0.15)
    parser.add_argument("--dup_thresh",   type=float, default=0.99)
    parser.add_argument("--green_thresh", type=float, default=0.90,
                        help="Rečenice sa tr_score >= ovo se preskačaju (zelene)")
    args = parser.parse_args()

    # Dostupni pivot jezici (svi osim EN)
    dostupni_jezici = list(LANG_MAP.keys())
    dostupni_jezici.remove("en")

    log_file = os.path.join(LOG_DIR, f"{args.test_id}_ga.log")
    logger.add(log_file, rotation="10 MB", encoding="utf-8", enqueue=True)

    logger.info(f"GA pokrenut za test_id={args.test_id}")

    # Učitaj modele
    embedder = load_embedder()
    nllb_tok, nllb_mod = load_nllb()

    conn = get_conn()

    # Odredi rečenice
    if args.sentence_id:
        row = load_sentence(conn, args.sentence_id)
        sentences = [row] if row else []
    elif args.sent_from and args.sent_to:
        sentences = load_sentences_range(conn, args.sent_from, args.sent_to)
    else:
        logger.error("Treba --sentence_id ili --sent_from + --sent_to")
        sys.exit(1)

    logger.info(f"Rečenica: {len(sentences)}, Jezici: {args.lang}, Test: {args.test_id}")

    GREEN_THRESH = args.green_thresh

    ukupno = 0
    preskoceno = 0
    for sid, original in sentences:
        for lang in args.lang:
            if lang not in LANG_MAP:
                logger.warning(f"Nepoznat jezik: {lang}, preskačem")
                continue

            # Provjeri best translation_score iz test_results — samo za ovaj test_id
            cur = conn.cursor()
            cur.execute("""
                SELECT MAX(translation_score)
                FROM test_results
                WHERE sentence_id = %s AND target_lang = %s AND test_id = %s
            """, (sid, lang, args.test_id))
            row = cur.fetchone()
            cur.close()
            best_tr = row[0] if row and row[0] else None

            if best_tr is not None and best_tr >= GREEN_THRESH:
                logger.info(f"s{sid} {lang} zelena ({best_tr:.4f} ≥ {GREEN_THRESH}) — preskačem GA")
                preskoceno += 1
                continue

            tier = "crvena" if (best_tr or 0) < 0.80 else "žuta"
            logger.info(f"s{sid} {lang} {tier} ({best_tr if best_tr is None else f'{best_tr:.4f}'}) — pokrećem GA")

            pobjednik = ga_optimizacija(
                args.test_id, sid, original, lang, dostupni_jezici,
                conn, nllb_tok, nllb_mod, embedder, args
            )
            ukupno += 1
            print(f"\n✓ s{sid} {lang}: fitness={pobjednik['fitness']:.4f}")
            print(f"  {pobjednik['tekst']}")

    conn.close()
    logger.info(f"GA završen: {ukupno} optimizacija, {preskoceno} preskočeno")
    print(f"\n✓ GA završen: {ukupno} optimizacija, {preskoceno} preskočeno (zelene)")


if __name__ == "__main__":
    main()
