"""
bb_rag_init.py
Stream-download OPUS OpenSubtitles korpusa i upis u bb_rag_korpus.

Primjer:
    venv/bin/python src/bb_rag_init.py \
        --jezici hr it de \
        --max_recenica 50000 \
        --embedder "multilingual-e5-large"
"""

import os
import sys
import gzip
import argparse
import urllib.request
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

EMBEDDER_PATH_MAP = {
    "multilingual-e5-large": "intfloat/multilingual-e5-large",
    "paraphrase-multilingual-MiniLM-L12-v2": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
}

OPUS_URL = "https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2018/mono/{lang}.txt.gz"

BATCH_SIZE = 256
MIN_ZNAKOVA = 10
MAX_ZNAKOVA = 200


def filtriraj(tekst):
    tekst = tekst.strip()
    if len(tekst) < MIN_ZNAKOVA or len(tekst) > MAX_ZNAKOVA:
        return False
    # Preskoči redove s previše brojeva ili specijalnih znakova
    alfa = sum(c.isalpha() for c in tekst)
    if alfa < len(tekst) * 0.6:
        return False
    return True


def stream_recenice(lang, max_n):
    url = OPUS_URL.format(lang=lang)
    print(f"  Stream: {url}")
    recenice = []
    with urllib.request.urlopen(url, timeout=60) as resp:
        with gzip.GzipFile(fileobj=resp) as gz:
            for line in gz:
                tekst = line.decode("utf-8", errors="ignore").strip()
                if filtriraj(tekst):
                    recenice.append(tekst)
                if len(recenice) >= max_n:
                    break
    return recenice


def main():
    import functools
    global print
    print = functools.partial(print, flush=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--jezici",       type=str, nargs="+", required=True)
    parser.add_argument("--max_recenica", type=int, default=50000)
    parser.add_argument("--embedder",     type=str, default="multilingual-e5-large")
    args = parser.parse_args()

    embedder_path = EMBEDDER_PATH_MAP.get(args.embedder, args.embedder)
    print(f"Učitavam embedder: {args.embedder} ({embedder_path})")
    embedder = SentenceTransformer(embedder_path)

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    for kod in args.jezici:
        cur.execute("SELECT id FROM bb_jezik WHERE kod = %s", (kod,))
        row = cur.fetchone()
        if not row:
            print(f"Jezik '{kod}' nije u bb_jezik, preskačem.")
            continue
        jezik_id = row[0]

        # Provjeri koliko već imamo
        cur.execute("SELECT COUNT(*) FROM bb_rag_korpus WHERE jezik_id = %s", (jezik_id,))
        postojeci = cur.fetchone()[0]
        if postojeci >= args.max_recenica:
            print(f"\n── {kod}: već {postojeci} rečenica, preskačem.")
            continue

        preostalo = args.max_recenica - postojeci
        print(f"\n── Jezik: {kod} | cilj: {args.max_recenica} | postojeći: {postojeci} | download: {preostalo}")

        recenice = stream_recenice(kod, preostalo)
        print(f"  Skinuto i filtrirano: {len(recenice)} rečenica")

        upisano = 0
        for i in range(0, len(recenice), BATCH_SIZE):
            chunk = recenice[i:i + BATCH_SIZE]
            vektori = embedder.encode(chunk, show_progress_bar=False)

            for j, tekst in enumerate(chunk):
                vektor = vektori[j].tolist()
                cur.execute(
                    "INSERT INTO bb_rag_korpus (jezik_id, tekst, vektor) VALUES (%s, %s, %s)",
                    (jezik_id, tekst, vektor)
                )

            conn.commit()
            upisano += len(chunk)
            print(f"  Upisano: {upisano}/{len(recenice)}")

        print(f"  Jezik {kod} gotov — {upisano} rečenica u bb_rag_korpus.")

    cur.close()
    conn.close()
    print("\nGotovo.")


if __name__ == "__main__":
    main()
