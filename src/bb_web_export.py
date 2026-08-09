"""
bb_web_export.py
Generira JSON fajlove za Buchenberg web stranicu.

Output:
    /var/www/buchenberg/data/books.json         — katalog knjiga i jezika
    /var/www/buchenberg/data/orig_<id>.json     — sve originalne rečenice knjige
    /var/www/buchenberg/data/tr_<id>_<lang>.json — prevod po jeziku (svi pobjednici)
    /var/www/buchenberg/data/langs.js           — rjecnik imena jezika (native + en) iz bb_jezik

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
            j.naziv_native,
            j.naziv_en,
            COUNT(DISTINCT r.pozicija) AS prevedenih_recenica
        FROM bb_prev_knjige pk
        JOIN bb_jezik j ON j.id = pk.jezik_id
        JOIN bb_prev_recenica pvr ON pvr.prev_knjige_id = pk.id
        JOIN bb_prevodi_recenica pr ON pr.id = pvr.prevodi_recenica_id
        JOIN bb_recenice r ON r.id = pr.recenica_id
        WHERE pk.knjiga_id = %s
        GROUP BY j.kod, j.naziv_native, j.naziv_en
        ORDER BY j.kod
    """, (knjiga_id,))
    return cur.fetchall()


def get_all_languages(cur):
    """Svi jezici iz bb_jezik — izvor za generisani rjecnik imena na webu."""
    cur.execute("""
        SELECT btrim(kod), naziv_native, naziv_en
        FROM bb_jezik
        ORDER BY kod
    """)
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
            t.vrijednost        AS temperatura,
            ROUND(pr.score::numeric, 4)             AS back_score,
            ROUND(pr.translation_score::numeric, 4) AS ts,
            ROUND(pr.sudija_avg::numeric, 4)        AS judge_avg,
            pr.back_translation,
            ROUND(pr.naturalness_score::numeric, 4) AS naturalness_score,
            ROUND(pr.sudija_grammar::numeric, 4)    AS sudija_grammar,
            ROUND(pr.sudija_naturalness::numeric, 4) AS sudija_naturalness,
            ROUND(pr.sudija_fidelity::numeric, 4)   AS sudija_fidelity,
            ppk.faza_id                              AS faza
        FROM bb_prev_knjige pk
        JOIN bb_jezik j            ON j.id  = pk.jezik_id
        JOIN bb_prev_recenica pvr  ON pvr.prev_knjige_id = pk.id
        JOIN bb_prevodi_recenica pr ON pr.id = pvr.prevodi_recenica_id
        JOIN bb_prevodi_knjige ppk  ON ppk.id = pr.prevodi_knjige_id
        JOIN bb_modeli m            ON m.id  = ppk.model_id
        JOIN bb_temperature t       ON t.id  = ppk.temperatura_id
        JOIN bb_recenice r          ON r.id  = pr.recenica_id
        WHERE pk.knjiga_id = %s AND j.kod = %s
        ORDER BY r.pozicija
    """, (knjiga_id, lang_kod))
    return cur.fetchall()



def get_ner(cur, knjiga_id, method='classic'):
    cur.execute("""
        SELECT tip, ime_norm, pojave
        FROM bb_ner_entiteti
        WHERE knjiga_id = %s AND method = %s
        ORDER BY tip, pojave DESC
    """, (knjiga_id, method))
    rows = cur.fetchall()
    entiteti = {}
    for tip, ime_norm, pojave in rows:
        if tip not in entiteti:
            entiteti[tip] = []
        entiteti[tip].append({"ime": ime_norm, "pojave": pojave})
    return entiteti


def get_ner_veze(cur, knjiga_id, method='classic', min_tezina=2):
    # s129: cita iz materijalizovane bb_ner_veze (web-export read-only, s128).
    # method implicitan preko entitet_id (JOIN na bb_ner_entiteti). Format izlaza
    # identican starom self-joinu (od/od_tip/do/do_tip/tezina) -> nlp.html netaknut.
    cur.execute("""
        SELECT e1.ime_norm, e1.tip, e2.ime_norm, e2.tip, v.tezina
        FROM bb_ner_veze v
        JOIN bb_ner_entiteti e1 ON e1.id = v.entitet1_id
        JOIN bb_ner_entiteti e2 ON e2.id = v.entitet2_id
        WHERE v.knjiga_id = %s
          AND e1.method = %s AND e2.method = %s
          AND v.tezina >= %s
        ORDER BY v.tezina DESC
    """, (knjiga_id, method, method, min_tezina))
    return [{"od": od, "od_tip": od_tip, "do": do, "do_tip": do_tip, "tezina": int(t)}
            for od, od_tip, do, do_tip, t in cur.fetchall()]


def get_ner_relacije(cur, knjiga_id):
    # s131: Massey taksonomija (fine/coarse/afinitet + audit_kosinus).
    # LEFT JOIN na bb_ner_massey — fine moze biti NULL (ventil/osoba-mjesto),
    # te relacije MORAJU ostati u izlazu (mapa kretanja na grafu).
    cur.execute("""
        SELECT ei.ime_norm, ei.tip, ec.ime_norm, ec.tip,
               r.fine, m.coarse, r.afinitet, r.audit_kosinus,
               r.smjer, r.opis, r.dokaz, r.pouzdanost
        FROM bb_ner_relacije r
        JOIN bb_ner_entiteti ei ON ei.id = r.izvor_id
        JOIN bb_ner_entiteti ec ON ec.id = r.cilj_id
        LEFT JOIN bb_ner_massey m ON m.fine = r.fine
        WHERE r.knjiga_id = %s
        ORDER BY m.coarse NULLS LAST, r.fine, ei.ime_norm
    """, (knjiga_id,))
    return [{"izvor": iz, "izvor_tip": izt, "cilj": ci, "cilj_tip": cit,
             "fine": fn, "coarse": co, "afinitet": af, "audit": au,
             "smjer": sm, "opis": op, "dokaz": dk, "pouzdanost": pz}
            for iz, izt, ci, cit, fn, co, af, au, sm, op, dk, pz in cur.fetchall()]

def get_model_registry(cur):
    """Tabela 0 — inventar: svi modeli iz registra + broj prevoda (kandidata).
    LEFT JOIN po imenu -> sudija/embeder/neupotrijebljeni modeli pokazuju 0
    (X-Ray potpunost: nula je informacija, ne rupa). 'broj prevoda' = svi
    kandidati koje je model ikad proizveo (bb_prevodi_recenica), ne parovi
    knjiga x jezik i ne samo pobjede."""
    cur.execute("""
        SELECT reg.naziv, reg.vrsta, reg.uloge,
               COALESCE(cnt.n, 0) AS broj_prevoda
        FROM bb_model_registar reg
        LEFT JOIN (
            SELECT m.naziv, COUNT(*) AS n
            FROM bb_prevodi_recenica pvr
            JOIN bb_prevodi_knjige pk ON pvr.prevodi_knjige_id = pk.id
            JOIN bb_modeli m ON pk.model_id = m.id
            GROUP BY m.naziv
        ) cnt ON cnt.naziv = reg.naziv
        ORDER BY broj_prevoda DESC, reg.naziv
    """)
    return [{"naziv": naziv, "vrsta": vrsta, "uloge": list(uloge) if uloge else [],
             "broj_prevoda": int(n)}
            for naziv, vrsta, uloge, n in cur.fetchall()]


def get_phase_winners(cur, knjiga_id, lang_kod):
    """Nivo B: za rečenice koje imaju BAR JEDNU fazu iznad bazne, vrati fazno-pobjednički
    prevod za SVAKU fazu (svaka faza = RAZLIČIT prevodi_recenica_id — različiti
    modeli/faze — vezani preko iste rečenice). N faza, bez hardkoda (s134).
    finalni_score = 0.4*kompozit + 0.6*sudija (ista formula kao bb_xray_export)."""
    cur.execute("""
        SELECT r.pozicija,
               prf.faza_id,
               m.naziv AS model,
               pr.prevod,
               ROUND(pr.translation_score::numeric, 4) AS ts,
               ROUND(pr.sudija_avg::numeric, 4)        AS judge_avg,
               ROUND(
                 (0.4 * ((COALESCE(pr.translation_score,0) + COALESCE(pr.score,0)) / 2.0)
                 + 0.6 * COALESCE(pr.sudija_avg, 0))::numeric
               , 4) AS finalni_score,
               EXISTS (
                 SELECT 1 FROM bb_prev_recenica ap
                 WHERE ap.prev_knjige_id = prf.prev_knjige_id
                   AND ap.prevodi_recenica_id = pr.id
               ) AS je_apsolutni
        FROM bb_prev_recenica_faza prf
        JOIN bb_prev_knjige pk       ON pk.id = prf.prev_knjige_id
        JOIN bb_jezik j              ON j.id = pk.jezik_id
        JOIN bb_prevodi_recenica pr  ON pr.id = prf.prevodi_recenica_id
        JOIN bb_prevodi_knjige ppk   ON ppk.id = pr.prevodi_knjige_id
        JOIN bb_modeli m             ON m.id = ppk.model_id
        JOIN bb_recenice r           ON r.id = pr.recenica_id
        WHERE pk.knjiga_id = %s AND j.kod = %s
        ORDER BY r.pozicija, prf.faza_id
    """, (knjiga_id, lang_kod))

    # Pivot po poziciji; emituj SAMO pozicije koje imaju bar jednu fazu iznad bazne.
    po_poziciji = {}
    for pozicija, faza, model, prevod, ts, judge_avg, finalni, je_aps in cur.fetchall():
        d = po_poziciji.setdefault(pozicija, {"pos": pozicija})
        d[f"faza{faza}"] = {
            "model":         model,
            "prevod":        prevod,
            "ts":            float(ts)       if ts       is not None else None,
            "judge_avg":     float(judge_avg) if judge_avg is not None else None,
            "finalni_score": float(finalni)  if finalni  is not None else None,
        }
        if je_aps:
            d["apsolutna_faza"] = faza

    return [po_poziciji[p] for p in sorted(po_poziciji)
            if any(k.startswith("faza") and k != "faza1" for k in po_poziciji[p])]


def get_stats(cur):
    """Agregati za stats.html — izracunati u bazi (jednom pri exportu), ne u browseru.
    Zamjena za stari client-side obracun nad 126 tr_*.json fajlova (~165 MB)."""
    base_from = """
        FROM bb_prev_recenica pr
        JOIN bb_prevodi_recenica pvr ON pr.prevodi_recenica_id = pvr.id
        JOIN bb_prevodi_knjige pk ON pvr.prevodi_knjige_id = pk.id
        JOIN bb_jezik j ON pk.jezik_id = j.id
        JOIN bb_modeli m ON pk.model_id = m.id
        JOIN bb_temperature t ON pk.temperatura_id = t.id
        JOIN bb_recenice r ON pvr.recenica_id = r.id
        JOIN bb_knjige kn ON r.knjiga_id = kn.id
    """

    cur.execute("""
        SELECT COUNT(*) AS pobj,
               COUNT(DISTINCT kn.id) AS knjige,
               COUNT(DISTINCT j.kod) AS jezici,
               COUNT(DISTINCT (kn.id, j.kod)) AS knjlang,
               ROUND(AVG(pvr.translation_score)::numeric, 4) AS avg_ts
    """ + base_from)
    pobj, knjige, jezici, knjlang, avg_ts = cur.fetchone()

    # Lijevak korpusa: izvorne recenice -> kandidati -> izabrani prevodi.
    # Brojevi su zivi (server = izvor istine); generisu se pri exportu.
    cur.execute("SELECT COUNT(*) FROM bb_recenice")
    total_sentences = int(cur.fetchone()[0])

    cur.execute("SELECT COUNT(*) FROM bb_prevodi_recenica")
    total_candidates = int(cur.fetchone()[0])

    # Recenice s pobjednikom u SVIM jezicima (dinamicki broj jezika, ne konstanta 14).
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT pvr.recenica_id
            FROM bb_prev_recenica pr
            JOIN bb_prevodi_recenica pvr ON pr.prevodi_recenica_id = pvr.id
            JOIN bb_prevodi_knjige pk ON pvr.prevodi_knjige_id = pk.id
            GROUP BY pvr.recenica_id
            HAVING COUNT(DISTINCT pk.jezik_id) = (SELECT COUNT(*) FROM bb_jezik)
        ) t
    """)
    full_all_langs = int(cur.fetchone()[0])

    summary = {
        "total_sentences":  total_sentences,
        "total_candidates": total_candidates,
        "total_winners":    int(pobj),
        "full_all_langs":   full_all_langs,
        "total_books":      int(knjige),
        "total_languages":  int(jezici),
        "total_booklangs":  int(knjlang),
        "avg_ts":           float(avg_ts) if avg_ts is not None else None,
    }

    cur.execute("""
        SELECT m.naziv, t.vrijednost, pk.faza_id, COUNT(*) AS cnt
    """ + base_from + """
        GROUP BY m.naziv, t.vrijednost, pk.faza_id
        ORDER BY cnt DESC
    """)
    win_rows = cur.fetchall()

    # Nazivnik za win-rate: koliko je puta svaki (model, temp) bio KANDIDAT
    # (svi prevodi, ne samo pobjednici). Odvojen izvor od base_from (koji ide
    # kroz pobjednike) -> nema fan-outa, dva nezavisna agregata spojena u Pythonu.
    cur.execute("""
        SELECT m.naziv, t.vrijednost, pk.faza_id, COUNT(*) AS cnt
        FROM bb_prevodi_recenica pvr
        JOIN bb_prevodi_knjige pk ON pvr.prevodi_knjige_id = pk.id
        JOIN bb_modeli m ON pk.model_id = m.id
        JOIN bb_temperature t ON pk.temperatura_id = t.id
        GROUP BY m.naziv, t.vrijednost, pk.faza_id
    """)
    cand_map = {(model, float(temp) if temp is not None else None, faza): int(cnt)
                for model, temp, faza, cnt in cur.fetchall()}

    # Tabela 2 (by-configuration): red po (naziv, temp, faza)
    winners_by_config = []
    for model, temp, faza, cnt in win_rows:
        tkey = float(temp) if temp is not None else None
        cand = cand_map.get((model, tkey, faza), 0)
        winners_by_config.append({
            "model": model,
            "temp": tkey,
            "faza": faza,
            "count": int(cnt),
            "candidates": cand,
            "win_rate": round(100.0 * int(cnt) / cand, 1) if cand else None,
        })

    # Tabela 1 (by-engine): roll-up po (naziv, faza) + ukupno. Apsolutne pobjede
    # razlozene po fazi (Flavio D3). Nazivnik po fazi -> posten win-rate (ANALIZA.md).
    from collections import defaultdict
    eng_win  = defaultdict(lambda: defaultdict(int))   # naziv -> faza -> wins
    eng_cand = defaultdict(lambda: defaultdict(int))   # naziv -> faza -> candidates
    for model, temp, faza, cnt in win_rows:
        eng_win[model][faza] += int(cnt)
    for (model, temp, faza), cnt in cand_map.items():
        eng_cand[model][faza] += cnt

    winners_by_engine = []
    for model in sorted(eng_win, key=lambda mm: -sum(eng_win[mm].values())):
        phases = {}
        for faza in sorted(set(eng_win[model]) | set(eng_cand[model])):
            w = eng_win[model].get(faza, 0)
            c = eng_cand[model].get(faza, 0)
            phases[str(faza)] = {
                "count": w,
                "candidates": c,
                "win_rate": round(100.0 * w / c, 1) if c else None,
            }
        tot_w = sum(eng_win[model].values())
        tot_c = sum(eng_cand[model].values())
        winners_by_engine.append({
            "engine": model,
            "phases": phases,
            "total_count": tot_w,
            "total_candidates": tot_c,
            "total_win_rate": round(100.0 * tot_w / tot_c, 1) if tot_c else None,
        })


    cur.execute("""
        SELECT kn.id, kn.naziv, j.kod, COUNT(*) AS cnt
    """ + base_from + """
        GROUP BY kn.id, kn.naziv, j.kod
        ORDER BY kn.naziv, j.kod
    """)
    coverage_raw = cur.fetchall()
    book_totals = {bid: ukupno for bid, _, _, _, ukupno in get_books(cur)}
    coverage = [{"book": book, "lang": lang, "translated": int(cnt),
                 "total": book_totals.get(bid)}
                for bid, book, lang, cnt in coverage_raw]

    cur.execute("""
        SELECT j.kod,
               COUNT(*) AS n,
               ROUND(AVG(pvr.translation_score)::numeric, 4) AS avg_ts,
               ROUND(AVG(pvr.sudija_avg)::numeric, 4) AS avg_judge
    """ + base_from + """
        GROUP BY j.kod
        ORDER BY j.kod
    """)
    scores = [{"lang": lang, "n": int(n),
               "avg_ts": float(avg_ts) if avg_ts is not None else None,
               "avg_judge": float(avg_j) if avg_j is not None else None}
              for lang, n, avg_ts, avg_j in cur.fetchall()]

    models = get_model_registry(cur)

    return {
        "summary":  summary,
        "models":   models,
        "winners_by_config": winners_by_config,
        "winners_by_engine": winners_by_engine,
        "coverage": coverage,
        "scores":   scores,
    }

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
            {"code": kod, "name": naziv_nat, "name_en": naziv_en, "sentences": prevedenih}
            for kod, naziv_nat, naziv_en, prevedenih in langs
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

        for lang_kod, lang_naziv, lang_naziv_en, prevedenih in langs:
            rows = get_translations(cur, book_id, lang_kod)
            if not rows:
                continue

            # index prevedenih rečenica
            translated = {}
            for pozicija, original, translation, model, temperatura, back_score, ts, judge_avg, back_translation, naturalness_score, sudija_grammar, sudija_naturalness, sudija_fidelity, faza in rows:
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
                    "faza":             faza,
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

            # phases_<id>_<lang>.json — Nivo B (before/after), rijedak: samo rečenice
            # s fazom 2. Ne piše prazan fajl (94% korpusa nema fazu 2).
            phases = get_phase_winners(cur, book_id, lang_kod)
            if phases:
                pout = {
                    "book_id":   book_id,
                    "title":     naziv,
                    "language":  lang_kod,
                    "lang_name": lang_naziv,
                    "sentences": phases,
                }
                pfname = f"phases_{book_id}_{lang_kod}.json"
                with open(os.path.join(args.output, pfname), "w", encoding="utf-8") as pf:
                    json.dump(pout, pf, ensure_ascii=False, indent=2)
                print(f"  {pfname} — {len(phases)} rečenica s fazom 2")

    # NER export
    for book in books_data:
        knjiga_id = book["id"]
        ner_out = {"knjiga_id": knjiga_id}
        ner_c = get_ner(cur, knjiga_id, method='classic')
        veze_c = get_ner_veze(cur, knjiga_id, method='classic', min_tezina=1)
        ner_out["classic"] = {"entiteti": ner_c, "veze": veze_c}
        cur.execute("SELECT 1 FROM bb_ner_entiteti WHERE knjiga_id=%s AND method='llm' LIMIT 1", (knjiga_id,))
        ima_llm = cur.fetchone() is not None
        if ima_llm:
            ner_l = get_ner(cur, knjiga_id, method='llm')
            veze_l = get_ner_veze(cur, knjiga_id, method='llm', min_tezina=1)
            ner_out["llm"] = {"entiteti": ner_l, "veze": veze_l, "relacije": get_ner_relacije(cur, knjiga_id)}
        ner_path = os.path.join(args.output, f"ner_{knjiga_id}.json")
        with open(ner_path, "w", encoding="utf-8") as f:
            json.dump(ner_out, f, ensure_ascii=False, indent=2)
        total_c = sum(len(v) for v in ner_c.values())
        print(f"  ner_{knjiga_id}.json — classic {total_c} ent" + (" + llm" if ima_llm else ""))

    # --- stats.json — agregati za stats.html (DB-side, zamjena za 165 MB client-side) ---
    stats_data = get_stats(cur)
    stats_path = os.path.join(args.output, "stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats_data, f, ensure_ascii=False, indent=2)
    print(f"  stats.json — {stats_data['summary']['total_winners']} pobjednika agregirano "
          f"({len(stats_data['models'])} modela u registru, "
          f"{len(stats_data['winners_by_engine'])} engine-a, "
          f"{len(stats_data['winners_by_config'])} konfiguracija, "
          f"{len(stats_data['coverage'])} knjiga×jezik, "
          f"{len(stats_data['scores'])} jezika)")

    # --- langs.js — generisani rjecnik imena jezika (IZ BAZE, ne hardkod na webu) ---
    langs = get_all_languages(cur)
    lang_map = {kod: {"native": nat, "en": en} for kod, nat, en in langs}
    # 'en' je IZVORNI jezik korpusa (invarijanta projekta), ne ciljni — nema ga u bb_jezik
    lang_map["en"] = {"native": "English", "en": "English"}
    langs_path = os.path.join(args.output, "langs.js")
    with open(langs_path, "w", encoding="utf-8") as f:
        f.write("// Generisano od bb_web_export.py iz bb_jezik — NE mijenjati rucno.\n")
        f.write("window.BB_LANGS = ")
        json.dump(lang_map, f, ensure_ascii=False, indent=2)
        f.write(";\n")
    print(f"  langs.js — {len(lang_map)} jezika (rjecnik imena iz baze)")

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
