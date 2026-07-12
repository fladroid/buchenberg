#!/usr/bin/env python3
"""
sandbox_cluster_probe.py — dijagnostička sonda (s131)

Pitanje: vidi li e5-large embedding prostor STRUKTURU u slobodnim DocRE
opisima, ili je sve "blizu svega" (pojas 0.857-0.98 iz s130)?

READ-ONLY: čita bb_ner_relacije, nula upisa, nula LLM poziva.

Izlaz:
  - silhouette score po k (numerička mjera stvarnosti klastera)
  - po klasteru: svi opisi + trenutna tip_veze grupa (poređenje golim okom)
"""
import os
import sys
import argparse
import numpy as np
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

load_dotenv()

def db_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname="bb", user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, nargs="+", default=[8, 15, 25],
                    help="vrijednosti k za k-means (default: 8 15 25)")
    args = ap.parse_args()

    # 1. Opisi iz baze (read-only)
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, r.knjiga_id, r.opis, r.tip_veze,
               ei.ime_norm AS izvor, ec.ime_norm AS cilj
        FROM bb_ner_relacije r
        JOIN bb_ner_entiteti ei ON ei.id = r.izvor_id
        JOIN bb_ner_entiteti ec ON ec.id = r.cilj_id
        ORDER BY r.knjiga_id, r.id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    opisi = [r[2] for r in rows]
    print(f"Ucitano {len(rows)} relacija ({len(set(opisi))} distinct opisa)")

    # 2. Embedding — goli .encode(), konzistentno s bb_10c/bb_06
    print("Ucitavam multilingual-e5-large ...")
    model = SentenceTransformer("intfloat/multilingual-e5-large")
    emb = model.encode(opisi, show_progress_bar=False, normalize_embeddings=True)
    print(f"Embeddings: {emb.shape}")

    # 3. K-means + silhouette po k
    print("\n=== SILHOUETTE PO K (blizu 0 = proizvoljno, blize 1 = stvarna struktura) ===")
    results = {}
    for k in args.k:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(emb)
        sil = silhouette_score(emb, labels, metric="cosine")
        results[k] = (labels, sil)
        print(f"  k={k:3d}  silhouette={sil:.4f}")

    # 4. Detaljni ispis za svaki k: klaster -> opisi + trenutna grupa
    for k in args.k:
        labels, sil = results[k]
        print(f"\n{'='*70}")
        print(f"=== KLASTERI ZA k={k} (silhouette {sil:.4f}) ===")
        print(f"{'='*70}")
        for c in range(k):
            idx = [i for i, l in enumerate(labels) if l == c]
            print(f"\n--- klaster {c} ({len(idx)} clanova) ---")
            for i in idx:
                r = rows[i]
                print(f"  [k{r[1]:2d}|{r[3]:<13s}] {r[4]} -> {r[5]}: {r[2]}")

if __name__ == "__main__":
    main()
