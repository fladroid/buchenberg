#!/usr/bin/env python3
"""
Buchenberg · ga_save_winners.py
Upisuje GA pobjednike iz ga_results u test_results kao method='ga'.

Pokretanje:
  venv/bin/python src/ga_save_winners.py --test_id test_012 --lang it
  venv/bin/python src/ga_save_winners.py --test_id test_012 --lang it hr de
  venv/bin/python src/ga_save_winners.py --test_id test_012 --lang all

Logica:
  - čita pobjednike iz ga_results (je_pobjednik = TRUE)
  - Upisuje u test_results sa method='ga'
  - Koristi ON CONFLICT DO UPDATE — sigurno za ponovni run
  - score (back_translation) = NULL — GA ne računa back-translation
  - winner = FALSE — pobjednik se određuje zasebno
  - Upisuje samo ako GA fitness > MAX(translation_score) za tu rečenicu
    (opciono, kontrolisano sa --only_better)
"""

import os
import sys
import argparse
import psycopg2
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

LOG_DIR = os.getenv("BUCH_LOG", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

VALID_LANGS = {
    "hr", "sr", "bs", "sl", "mk", "bg",
    "de", "nl", "af", "fr", "it", "es", "pt", "ro"
}


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def get_langs_in_test(conn, test_id):
    """Dohvati sve jezike koji imaju GA pobjednike za ovaj test."""
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT target_lang
        FROM ga_results
        WHERE test_id = %s AND je_pobjednik = TRUE
        ORDER BY target_lang
    """, (test_id,))
    langs = [r[0].strip() for r in cur.fetchall()]
    cur.close()
    return langs


def save_winners(conn, test_id, lang, only_better=False):
    cur = conn.cursor()

    # Dohvati GA pobjednike
    cur.execute("""
        SELECT g.sentence_id, g.tekst, g.fitness, g.metoda, g.pivot_lang
        FROM ga_results g
        WHERE g.test_id = %s AND g.target_lang = %s AND g.je_pobjednik = TRUE
        ORDER BY g.sentence_id
    """, (test_id, lang))
    winners = cur.fetchall()

    if not winners:
        logger.warning(f"Nema GA pobjednika za {test_id} {lang}")
        return 0

    upisano = 0
    preskoceno = 0

    for sentence_id, tekst, fitness, metoda, pivot_lang in winners:

        if only_better:
            # Provjeri da li GA pobjednik zaista bolji od najboljeg u test_results
            cur.execute("""
                SELECT MAX(translation_score)
                FROM test_results
                WHERE test_id = %s AND sentence_id = %s AND target_lang = %s
            """, (test_id, sentence_id, lang))
            row = cur.fetchone()
            best_existing = row[0] if row and row[0] else 0.0
            if fitness <= best_existing:
                logger.info(f"s2{sentence_id} {lang} — GA ({fitness:.4f}) nije bolji od postojećeg ({best_existing:.4f}), preskačem")
                preskoceno += 1
                continue

        # Upiši u test_results
        # method string: 'ga' + pivot info ako postoji
        method_str = f"ga_{pivot_lang}" if pivot_lang else "ga"

        cur.execute("""
            INSERT INTO test_results
                (test_id, sentence_id, target_lang, method,
                 translated_text, back_translation, score, translation_score, winner)
            VALUES (%s, %s, %s, %s, %s, NULL, NULL, %s, FALSE)
            ON CONFLICT (test_id, sentence_id, target_lang, method)
            DO UPDATE SET
                translated_text  = EXCLUDED.translated_text,
                translation_score = EXCLUDED.translation_score,
                winner = FALSE
        """, (test_id, sentence_id, lang, method_str,
              tekst, fitness))

        logger.info(f"s{sentence_id} {lang} — upisano method='{method_str}' fitness={fitness:.4f}")
        upisano += 1

    conn.commit()
    cur.close()

    logger.info(f"Lang {lang}: {upisano} upisano, {preskoceno} preskočeno")
    return upisano


def main():
    parser = argparse.ArgumentParser(description="Buchenberg — upis GA pobjednika u test_results")
    parser.add_argument("--test_id", type=str, required=True)
    parser.add_argument("--lang", nargs="+", required=True,
                        help="Jezici (npr. it hr de) ili 'all' za sve jezike u testu")
    parser.add_argument("--only_better", action="store_true", default=False,
                        help="Upiši samo ako GA pobjednik ima viši score od najboljeg u test_results")
    args = parser.parse_args()

    log_file = os.path.join(LOG_DIR, f"{args.test_id}_ga_save.log")
    logger.add(log_file, rotation="10 MB", encoding="utf-8", enqueue=True)
    logger.info(f"ga_save_winners START: test_id={args.test_id} lang={args.lang} only_better={args.only_better}")

    conn = get_conn()

    # Odredi jezike
    if args.lang == ["all"]:
        langs = get_langs_in_test(conn, args.test_id)
        logger.info(f"Jezici u testu: {langs}")
    else:
        langs = args.lang

    ukupno = 0
    for lang in langs:
        lang = lang.strip()
        if lang not in VALID_LANGS:
            logger.warning(f"Nepoznat jezik: {lang}, preskačem")
            continue
        n = save_winners(conn, args.test_id, lang, args.only_better)
        ukupno += n
        print(f"✓ {lang}: {n} GA pobjednika upisano u test_results")

    conn.close()
    logger.info(f"ga_save_winners DONE: {ukupno} ukupno upisano")
    print(f"\n✓ Ukupno upisano: {ukupno}")


if __name__ == "__main__":
    main()
