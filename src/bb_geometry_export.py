"""
bb_geometry_export.py
Generira data/geometry.json za geometry.html stranicu.

Ucitava s1-s200 iz The Hound of the Baskervilles (knjiga_id=1),
enkodira EN originale + pobjednicke prevode (hr, it, de) via
multilingual-e5-large, projicira u 2D via UMAP, sprema JSON.

Primjer:
    venv/bin/python src/bb_geometry_export.py
    venv/bin/python src/bb_geometry_export.py --od 1 --do 200
    venv/bin/python src/bb_geometry_export.py --output /var/www/buchenberg/data
"""

import os, json, argparse, time
from datetime import datetime
import psycopg2
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from umap import UMAP

load_dotenv("/home/balsam/buchenberg/.env")

DB = {
    "host":     os.getenv("DB_HOST"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   "bb",
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

KNJIGA_ID  = 1
JEZICI     = ["hr", "it", "de"]
EMBEDDER   = "multilingual-e5-large"
EMBEDDER_PATH_MAP = {
    "multilingual-e5-large": "intfloat/multilingual-e5-large",
}
UMAP_SEED  = 42
OUTPUT_DIR = "/var/www/buchenberg/data"


def get_conn():
    return psycopg2.connect(**DB)


def fetch_originali(conn, od, do):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT pozicija, tekst
            FROM bb_recenice
            WHERE knjiga_id = %s AND pozicija BETWEEN %s AND %s
            ORDER BY pozicija
        """, (KNJIGA_ID, od, do))
        return {row[0]: row[1] for row in cur.fetchall()}


def fetch_pobjednici(conn, od, do):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                j.kod                                                        AS jezik,
                r.pozicija                                                   AS s_id,
                pvr.prevod,
                pvr.score,
                pvr.translation_score,
                ROUND(((pvr.score + pvr.translation_score) / 2.0)::numeric, 4) AS kompozitni,
                pvr.sudija_avg,
                ROUND((0.4 * ((pvr.score + pvr.translation_score) / 2.0)
                       + 0.6 * pvr.sudija_avg)::numeric, 4)                 AS finalni_score
            FROM bb_prev_recenica bpr
            JOIN bb_prev_knjige      bpk ON bpk.id  = bpr.prev_knjige_id
            JOIN bb_jezik             j  ON j.id    = bpk.jezik_id
            JOIN bb_prevodi_recenica pvr ON pvr.id  = bpr.prevodi_recenica_id
            JOIN bb_recenice          r  ON r.id    = pvr.recenica_id
            WHERE bpk.knjiga_id = %s
              AND j.kod = ANY(%s)
              AND r.pozicija BETWEEN %s AND %s
            ORDER BY j.kod, r.pozicija
        """, (KNJIGA_ID, JEZICI, od, do))

        result = {}
        for jezik, s_id, prevod, score, ts, komp, sudija, finalni in cur.fetchall():
            jezik = jezik.strip()
            if jezik not in result:
                result[jezik] = {}
            result[jezik][s_id] = {
                "prevod":            prevod,
                "score":             round(float(score), 4) if score else None,
                "translation_score": round(float(ts), 4) if ts else None,
                "kompozitni":        round(float(komp), 4) if komp else None,
                "sudija_avg":        round(float(sudija), 4) if sudija else None,
                "finalni_score":     round(float(finalni), 4) if finalni else None,
            }
        return result


def encode(model, texts):
    return model.encode(
        ["query: " + t for t in texts],
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--od",     type=int, default=1)
    parser.add_argument("--do",     type=int, default=200)
    parser.add_argument("--output", type=str, default=OUTPUT_DIR)
    args = parser.parse_args()

    print(f"[geometry] knjiga={KNJIGA_ID} s{args.od}-s{args.do} jezici={JEZICI}")
    t0 = time.time()

    conn = get_conn()
    originali  = fetch_originali(conn, args.od, args.do)
    pobjednici = fetch_pobjednici(conn, args.od, args.do)
    conn.close()

    pozicije = sorted(originali.keys())
    print(f"[geometry] {len(pozicije)} EN originala, "
          + ", ".join(f"{j}={len(pobjednici.get(j, {}))} prev" for j in JEZICI))

    embedder_path = EMBEDDER_PATH_MAP.get(EMBEDDER, EMBEDDER)
    print(f"[geometry] Ucitavam {EMBEDDER} ({embedder_path})...")
    model = SentenceTransformer(embedder_path)

    print("[geometry] Enkodiranje EN originala...")
    en_texts = [originali[p] for p in pozicije]
    en_vecs  = encode(model, en_texts)

    lang_vecs = {}
    for jezik in JEZICI:
        prev_map = pobjednici.get(jezik, {})
        poz_lang = [p for p in pozicije if p in prev_map]
        if not poz_lang:
            print(f"[geometry] {jezik}: nema pobjednika, preskacemo")
            continue
        texts = [prev_map[p]["prevod"] for p in poz_lang]
        print(f"[geometry] Enkodiranje {jezik} ({len(texts)} recenica)...")
        lang_vecs[jezik] = (poz_lang, encode(model, texts))

    # Zajednicki UMAP na svim vektorima
    all_vecs   = [en_vecs]
    all_labels = [("en", p) for p in pozicije]
    for jezik, (poz_lang, vecs) in lang_vecs.items():
        all_vecs.append(vecs)
        all_labels += [(jezik, p) for p in poz_lang]

    all_matrix = np.vstack(all_vecs)
    print(f"[geometry] UMAP na {len(all_matrix)} vektora...")

    reducer = UMAP(
        n_components=2,
        n_neighbors=15,
        min_dist=0.1,
        metric="cosine",
        random_state=UMAP_SEED,
    )
    coords_2d = reducer.fit_transform(all_matrix)

    xy_min = coords_2d.min(axis=0)
    xy_max = coords_2d.max(axis=0)
    coords_norm = (coords_2d - xy_min) / (xy_max - xy_min)

    coord_map = {}
    for i, (jezik, poz) in enumerate(all_labels):
        coord_map[(jezik, poz)] = (
            round(float(coords_norm[i, 0]), 4),
            round(float(coords_norm[i, 1]), 4),
        )

    sentences = []
    for poz in pozicije:
        en_x, en_y = coord_map[("en", poz)]
        entry = {
            "id":   poz,
            "en":   originali[poz],
            "umap": {"x": en_x, "y": en_y},
            "translations": {},
        }
        for jezik in JEZICI:
            prev_map = pobjednici.get(jezik, {})
            if poz not in prev_map:
                continue
            lx, ly = coord_map.get((jezik, poz), (None, None))
            d = prev_map[poz]
            entry["translations"][jezik] = {
                "prevod":        d["prevod"],
                "finalni_score": d["finalni_score"],
                "kompozitni":    d["kompozitni"],
                "sudija_avg":    d["sudija_avg"],
                "umap":          {"x": lx, "y": ly},
            }
        sentences.append(entry)

    payload = {
        "meta": {
            "knjiga_id":    KNJIGA_ID,
            "knjiga":       "The Hound of the Baskervilles",
            "embedder":     EMBEDDER,
            "n_sentences":  len(sentences),
            "jezici":       ["en"] + JEZICI,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        },
        "sentences": sentences,
    }

    out_path = os.path.join(args.output, "geometry.json")
    os.makedirs(args.output, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - t0
    print(f"[geometry] Saved -> {out_path}  ({len(sentences)} recenica, {elapsed:.1f}s)")


if __name__ == "__main__":
    main()
