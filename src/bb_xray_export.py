"""
bb_xray_export.py
Generira X-Ray JSON fajlove za Buchenberg web stranicu.
Za svaku rečenicu exporta SVIH 5 kandidata (ne samo pobjednika).

Output:
    /var/www/buchenberg/data/xray_<id>_<lang>.json

Primjer:
    venv/bin/python src/bb_xray_export.py
    venv/bin/python src/bb_xray_export.py --knjiga 1 --jezici hr sr
    venv/bin/python src/bb_xray_export.py --output /var/www/buchenberg/data
"""

import os
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


def get_books(cur, knjiga_filter=None):
    sql = """
        SELECT k.id, k.naziv, k.autor
        FROM bb_knjige k
        ORDER BY k.id
    """
    cur.execute(sql)
    rows = cur.fetchall()
    if knjiga_filter:
        rows = [r for r in rows if r[0] in knjiga_filter]
    return rows


def get_languages_for_book(cur, knjiga_id, lang_filter=None):
    """Samo jezici koji imaju pobjednike za ovu knjigu."""
    cur.execute("""
        SELECT DISTINCT j.kod, j.naziv
        FROM bb_prev_knjige pk
        JOIN bb_jezik j ON j.id = pk.jezik_id
        JOIN bb_prev_recenica pvr ON pvr.prev_knjige_id = pk.id
        WHERE pk.knjiga_id = %s
        ORDER BY j.kod
    """, (knjiga_id,))
    rows = cur.fetchall()
    if lang_filter:
        rows = [r for r in rows if r[0] in lang_filter]
    return rows


def get_winner_ids(cur, knjiga_id, lang_kod):
    """Vrati set prevodi_recenica_id koji su pobjednici za ovu knjigu i jezik."""
    cur.execute("""
        SELECT pvr.prevodi_recenica_id
        FROM bb_prev_recenica pvr
        JOIN bb_prev_knjige pk ON pk.id = pvr.prev_knjige_id
        JOIN bb_jezik j ON j.id = pk.jezik_id
        WHERE pk.knjiga_id = %s AND j.kod = %s
    """, (knjiga_id, lang_kod))
    return set(row[0] for row in cur.fetchall())


def get_all_candidates(cur, knjiga_id, lang_kod):
    """Svi prijevodi za ovu knjigu i jezik, grupirani po poziciji rečenice."""
    cur.execute("""
        SELECT
            r.pozicija,
            r.tekst AS original,
            pr.id AS prevod_id,
            m.naziv AS model,
            ROUND(m.temperatura::numeric, 4) AS temperatura,
            pr.prevod,
            pr.back_translation,
            ROUND(pr.translation_score::numeric, 4) AS ts,
            ROUND(pr.score::numeric, 4) AS back_score,
            ROUND(pr.sudija_avg::numeric, 4) AS judge_avg,
            pr.sudija_grammar,
            pr.sudija_naturalness,
            pr.sudija_fidelity,
            ROUND(
                (0.4 * ((COALESCE(pr.translation_score,0) + COALESCE(pr.score,0)) / 2.0)
                + 0.6 * COALESCE(pr.sudija_avg, 0))::numeric
            , 4) AS finalni_score
        FROM bb_prevodi_recenica pr
        JOIN bb_prevodi_knjige pk ON pk.id = pr.prevodi_knjige_id
        JOIN bb_jezik j ON j.id = pk.jezik_id
        JOIN bb_modeli m ON m.id = pk.model_id
        JOIN bb_recenice r ON r.id = pr.recenica_id
        WHERE pk.knjiga_id = %s AND j.kod = %s
        ORDER BY r.pozicija, finalni_score DESC NULLS LAST
    """, (knjiga_id, lang_kod))
    return cur.fetchall()


def build_xray_json(cur, knjiga_id, naziv, autor, lang_kod, lang_naziv):
    winner_ids = get_winner_ids(cur, knjiga_id, lang_kod)
    rows = get_all_candidates(cur, knjiga_id, lang_kod)

    # Grupiraj po poziciji
    sentences = {}
    for (pozicija, original, prevod_id, model, temperatura,
         prevod, back_translation, ts, back_score,
         judge_avg, sudija_grammar, sudija_naturalness, sudija_fidelity,
         finalni_score) in rows:

        if pozicija not in sentences:
            sentences[pozicija] = {
                "pos": pozicija,
                "original": original,
                "candidates": []
            }

        candidate = {
            "model":            model,
            "temp":             float(temperatura) if temperatura is not None else None,
            "prevod":           prevod,
            "back_translation": back_translation,
            "ts":               float(ts)               if ts               is not None else None,
            "back_score":       float(back_score)       if back_score       is not None else None,
            "judge_avg":        float(judge_avg)        if judge_avg        is not None else None,
            "sudija_grammar":   float(sudija_grammar)   if sudija_grammar   is not None else None,
            "sudija_natural":   float(sudija_naturalness) if sudija_naturalness is not None else None,
            "sudija_fidelity":  float(sudija_fidelity)  if sudija_fidelity  is not None else None,
            "finalni_score":    float(finalni_score)    if finalni_score    is not None else None,
            "is_winner":        prevod_id in winner_ids,
        }
        sentences[pozicija]["candidates"].append(candidate)

    return {
        "book_id":   knjiga_id,
        "title":     naziv,
        "author":    autor,
        "language":  lang_kod,
        "lang_name": lang_naziv,
        "sentences": [sentences[p] for p in sorted(sentences.keys())],
    }


def main():
    parser = argparse.ArgumentParser(description="Buchenberg X-Ray JSON export")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--knjiga", type=int, nargs="+", help="Filter po knjiga ID")
    parser.add_argument("--jezici", nargs="+", help="Filter po jezicima (npr. hr sr de)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    books = get_books(cur, knjiga_filter=args.knjiga)
    print(f"Knjige: {[b[0] for b in books]}")

    total_files = 0
    for knjiga_id, naziv, autor in books:
        langs = get_languages_for_book(cur, knjiga_id, lang_filter=args.jezici)
        for lang_kod, lang_naziv in langs:
            data = build_xray_json(cur, knjiga_id, naziv, autor, lang_kod, lang_naziv)
            n_sent = len(data["sentences"])
            n_cand = sum(len(s["candidates"]) for s in data["sentences"])
            fname = f"xray_{knjiga_id}_{lang_kod}.json"
            fpath = os.path.join(args.output, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  {fname} — {n_sent} rečenica, {n_cand} kandidata")
            total_files += 1

    cur.close()
    conn.close()
    print(f"Gotovo — {total_files} fajl(ova).")


if __name__ == "__main__":
    main()
