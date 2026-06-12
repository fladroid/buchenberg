"""
bb_web_export.py
Generira JSON fajlove za Buchenberg web stranicu.

Output:
    /var/www/buchenberg/data/books.json         — katalog knjiga i jezika
    /var/www/buchenberg/data/orig_<id>.json     — sve originalne rečenice knjige
    /var/www/buchenberg/data/tr_<id>_<lang>.json — prevod po jeziku (svi pobjednici)

Primjer:
    venv/bin/python src/bb_web_export.py
    venv/bin/python src/bb_web_export.py --output /var/www/buchenberg/data
"""

import os
import time
import json
import argparse
import psycopg2
from dotenv import load_dotenv

load_dotenv("/home/balsam/buchenberg/.env")

DB = {
    "host":     os.getenv("DB_HOST", "balsam.dynu.net"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   "bb",
    "user":     os.getenv("DB_USER", "pgu"),
    "password": os.getenv("DB_PASSWORD"),
}

DEFAULT_OUTPUT = "/var/www/buchenberg/data"


def get_books(cur):
    cur.execute("""
        SELECT
            k.id,
            k.naziv,
            k.autor,
            k.gutenberg_id,
            COUNT(DISTINCT r.id) AS ukupno_recenica
        FROM bb_knjige k
        JOIN bb_recenice r ON r.knjiga_id = k.id
        GROUP BY k.id, k.naziv, k.autor, k.gutenberg_id
        ORDER BY k.id
    """)
    return cur.fetchall()


def get_languages_for_book(cur, knjiga_id):
    cur.execute("""
        SELECT
            j.kod,
            j.naziv,
            COUNT(DISTINCT r.pozicija) AS prevedenih_recenica
        FROM bb_prev_knjige pk
        JOIN bb_jezik j ON j.id = pk.jezik_id
        JOIN bb_prev_recenica pvr ON pvr.prev_knjige_id = pk.id
        JOIN bb_prevodi_recenica pr ON pr.id = pvr.prevodi_recenica_id
        JOIN bb_recenice r ON r.id = pr.recenica_id
        WHERE pk.knjiga_id = %s
        GROUP BY j.kod, j.naziv
        ORDER BY j.kod
    """, (knjiga_id,))
    return cur.fetchall()


def get_all_sentences(cur, knjiga_id):
    cur.execute("""
        SELECT pozicija, tekst
        FROM bb_recenice
        WHERE knjiga_id = %s
        ORDER BY pozicija
    """, (knjiga_id,))
    return cur.fetchall()


def get_translations(cur, knjiga_id, lang_kod):
    cur.execute("""
        SELECT
            r.pozicija,
            r.tekst             AS original,
            pr.prevod           AS translation,
            m.naziv             AS model,
            m.temperatura       AS temperatura,
            ROUND(pr.score::numeric, 4)             AS back_score,
            ROUND(pr.translation_score::numeric, 4) AS ts,
            ROUND(pr.sudija_avg::numeric, 4)        AS judge_avg,
            pr.back_translation,
            ROUND(pr.naturalness_score::numeric, 4) AS naturalness_score,
            ROUND(pr.sudija_grammar::numeric, 4)    AS sudija_grammar,
            ROUND(pr.sudija_naturalness::numeric, 4) AS sudija_naturalness,
            ROUND(pr.sudija_fidelity::numeric, 4)   AS sudija_fidelity
        FROM bb_prev_knjige pk
        JOIN bb_jezik j            ON j.id  = pk.jezik_id
        JOIN bb_prev_recenica pvr  ON pvr.prev_knjige_id = pk.id
        JOIN bb_prevodi_recenica pr ON pr.id = pvr.prevodi_recenica_id
        JOIN bb_prevodi_knjige ppk  ON ppk.id = pr.prevodi_knjige_id
        JOIN bb_modeli m            ON m.id  = ppk.model_id
        JOIN bb_recenice r          ON r.id  = pr.recenica_id
        WHERE pk.knjiga_id = %s AND j.kod = %s
        ORDER BY r.pozicija
    """, (knjiga_id, lang_kod))
    return cur.fetchall()



def get_ner(cur, knjiga_id):
    cur.execute("""
        SELECT tip, ime_norm, pojave
        FROM bb_ner_entiteti
        WHERE knjiga_id = %s
        ORDER BY tip, pojave DESC
    """, (knjiga_id,))
    rows = cur.fetchall()
    entiteti = {}
    for tip, ime_norm, pojave in rows:
        if tip not in entiteti:
            entiteti[tip] = []
        entiteti[tip].append({"ime": ime_norm, "pojave": pojave})
    return entiteti


def get_ner_veze(cur, knjiga_id, min_tezina=2):
    cur.execute("""
        SELECT e1.ime_norm, e1.tip, e2.ime_norm, e2.tip, COUNT(*) AS tezina
        FROM bb_ner_recenica r1
        JOIN bb_ner_recenica r2 ON r2.recenica_id = r1.recenica_id
            AND r2.entitet_id > r1.entitet_id
        JOIN bb_ner_entiteti e1 ON e1.id = r1.entitet_id
        JOIN bb_ner_entiteti e2 ON e2.id = r2.entitet_id
        WHERE e1.knjiga_id = %s AND e2.knjiga_id = %s
        GROUP BY e1.ime_norm, e1.tip, e2.ime_norm, e2.tip
        HAVING COUNT(*) >= %s
        ORDER BY tezina DESC
    """, (knjiga_id, knjiga_id, min_tezina))
    return [{"od": od, "od_tip": od_tip, "do": do, "do_tip": do_tip, "tezina": int(t)}
            for od, od_tip, do, do_tip, t in cur.fetchall()]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT,
                        help=f"Output direktorijum (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    # --- books.json ---
    books_data = []
    books = get_books(cur)

    for book_id, naziv, autor, gutenberg_id, ukupno in books:
        langs = get_languages_for_book(cur, book_id)
        lang_list = [
            {"code": kod, "name": naziv_j, "sentences": prevedenih}
            for kod, naziv_j, prevedenih in langs
        ]
        books_data.append({
            "id":               book_id,
            "title":            naziv,
            "author":           autor,
            "gutenberg_id":     gutenberg_id,
            "total_sentences":  ukupno,
            "languages":        lang_list,
        })

    books_path = os.path.join(args.output, "books.json")
    with open(books_path, "w", encoding="utf-8") as f:
        json.dump(books_data, f, ensure_ascii=False, indent=2)
    print(f"books.json — {len(books_data)} knjiga(e)")

    # --- orig_<id>.json — sve originalne rečenice ---
    for book_id, naziv, autor, gutenberg_id, ukupno in books:
        rows = get_all_sentences(cur, book_id)
        sentences = [{"pos": pos, "text": tekst} for pos, tekst in rows]
        out = {
            "book_id":          book_id,
            "title":            naziv,
            "author":           autor,
            "gutenberg_id":     gutenberg_id,
            "total_sentences":  ukupno,
            "sentences":        sentences,
        }
        fname = f"orig_{book_id}.json"
        fpath = os.path.join(args.output, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"  {fname} — {len(sentences)} rečenica")

    # --- tr_<id>_<lang>.json po knjizi i jeziku ---
    for book_id, naziv, autor, _, _ in books:
        langs = get_languages_for_book(cur, book_id)
        # dict originala za merge
        all_sents = {pos: tekst for pos, tekst in get_all_sentences(cur, book_id)}

        for lang_kod, lang_naziv, prevedenih in langs:
            rows = get_translations(cur, book_id, lang_kod)
            if not rows:
                continue

            # index prevedenih rečenica
            translated = {}
            for pozicija, original, translation, model, temperatura, back_score, ts, judge_avg, back_translation, naturalness_score, sudija_grammar, sudija_naturalness, sudija_fidelity in rows:
                translated[pozicija] = {
                    "pos":         pozicija,
                    "original":    original,
                    "translation": translation,
                    "translated":  True,
                    "model":       model,
                    "temp":        float(temperatura) if temperatura is not None else None,
                    "back_score":  float(back_score)  if back_score  is not None else None,
                    "ts":          float(ts)           if ts          is not None else None,
                    "judge_avg":        float(judge_avg)          if judge_avg          is not None else None,
                    "back_translation": back_translation                       if back_translation    is not None else None,
                    "naturalness":      float(naturalness_score)               if naturalness_score   is not None else None,
                    "sudija_grammar":   float(sudija_grammar)                  if sudija_grammar      is not None else None,
                    "sudija_natural":   float(sudija_naturalness)              if sudija_naturalness  is not None else None,
                    "sudija_fidelity":  float(sudija_fidelity)                 if sudija_fidelity     is not None else None,
                }

            # sve rečenice knjige — prevedene + neprevedene
            sentences = []
            for pos in sorted(all_sents.keys()):
                if pos in translated:
                    sentences.append(translated[pos])
                else:
                    sentences.append({
                        "pos":        pos,
                        "original":   all_sents[pos],
                        "translated": False,
                    })

            out = {
                "book_id":   book_id,
                "title":     naziv,
                "author":    autor,
                "language":  lang_kod,
                "lang_name": lang_naziv,
                "sentences": sentences,
            }

            fname = f"tr_{book_id}_{lang_kod}.json"
            fpath = os.path.join(args.output, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            print(f"  {fname} — {len(rows)} prevedenih / {len(sentences)} ukupno ({lang_naziv})")

    # NER export
    for book in books_data:
        knjiga_id = book["id"]
        ner = get_ner(cur, knjiga_id)
        veze = get_ner_veze(cur, knjiga_id, min_tezina=1)
        ner_out = {"knjiga_id": knjiga_id, "entiteti": ner, "veze": veze}
        ner_path = os.path.join(args.output, f"ner_{knjiga_id}.json")
        with open(ner_path, "w", encoding="utf-8") as f:
            json.dump(ner_out, f, ensure_ascii=False, indent=2)
        total = sum(len(v) for v in ner.values())
        print(f"  ner_{knjiga_id}.json — {total} entiteta")

    cur.close()
    conn.close()
    # version.json — cache busting
    version_path = os.path.join(args.output, "version.json")
    with open(version_path, "w", encoding="utf-8") as f:
        json.dump({"v": int(time.time())}, f)
    print(f"  version.json — cache busting (v={int(time.time())})")

    print("Gotovo.")


if __name__ == "__main__":
    main()
