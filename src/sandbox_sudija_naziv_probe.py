#!/usr/bin/env python3
"""
sandbox_sudija_naziv_probe.py — READ-ONLY sonda.

Pitanje: mijenja li se sudijina ocjena kad mu se jezik imenuje na srpskom
(bb_jezik.naziv, sto pipeline radi danas) umjesto na engleskom (naziv_en)?

Metod: isti kandidati, tri prolaza — A1 (naziv A), B (naziv B), A2 (naziv A opet).
Treci prolaz NIJE visak: daje sum ovog konkretnog seta, pa se razlika izmedju
naziva mjeri protiv njega, a ne protiv s146 broja izmjerenog na drugom materijalu.

Nula upisa u bazu. Prompt i poziv se IMPORTUJU iz bb_08_sudija.py (ne kopiraju).
"""

import os
import sys
import argparse
import statistics as st

import psycopg2
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
load_dotenv(os.path.join(os.path.dirname(HERE), ".env"))

import bb_08_sudija as sud


def db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname="bb", user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
    )


def ocijeni(tekst, prevodi, naziv):
    """Vrati {redni_broj: avg} za jedan poziv sudiji. None ako parsiranje ne uspije."""
    translations_str = "\n".join(f"{i+1}. {p}" for i, p in enumerate(prevodi))
    prompt = sud.PROMPT_TEMPLATE.format(
        lang=naziv, original=tekst, translations=translations_str
    )
    ocjene = sud.parse_ocjene(sud.call_sudija(prompt))
    if not ocjene:
        return None
    out = {}
    for o in ocjene:
        try:
            out[int(o["id"])] = (float(o["grammar"]) + float(o["naturalness"])
                                 + float(o["fidelity"])) / 3
        except (KeyError, ValueError, TypeError):
            continue
    return out or None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--knjiga", type=int, default=22)
    p.add_argument("--jezik", required=True)
    p.add_argument("--od", type=int, default=1)
    p.add_argument("--do", type=int, default=30)
    p.add_argument("--naziv-a", required=True, help="npr. holandski (danasnje stanje)")
    p.add_argument("--naziv-b", required=True, help="npr. Dutch")
    args = p.parse_args()

    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT recenica_pozicija, recenica_tekst, prevod_id, prevod
        FROM v_prevodi_full
        WHERE knjiga_id = %s AND jezik_kod = %s AND faza_id = 1
          AND recenica_pozicija BETWEEN %s AND %s AND prevod IS NOT NULL
        ORDER BY recenica_pozicija, prevod_id
    """, (args.knjiga, args.jezik, args.od, args.do))
    grupe = {}
    for poz, tekst, pid, prevod in cur.fetchall():
        grupe.setdefault(poz, {"tekst": tekst, "prevodi": []})["prevodi"].append(prevod)
    cur.close()
    conn.close()

    print(f"Recenica: {len(grupe)} | jezik={args.jezik} | A='{args.naziv_a}' B='{args.naziv_b}'")
    if not grupe:
        sys.exit(1)

    d_ab, d_aa, preskoceno = [], [], 0
    # argmax: pobjednika bira poredak MEDJU kandidatima, ne apsolutni nivo ocjene
    arg_ab = arg_aa = arg_uporedivih = 0
    for n, (poz, g) in enumerate(sorted(grupe.items()), 1):
        a1 = ocijeni(g["tekst"], g["prevodi"], args.naziv_a)
        b  = ocijeni(g["tekst"], g["prevodi"], args.naziv_b)
        a2 = ocijeni(g["tekst"], g["prevodi"], args.naziv_a)
        if not (a1 and b and a2):
            preskoceno += 1
            print(f"  s{poz}: nepotpun odgovor, preskacem")
            continue
        kljucevi = sorted(set(a1) & set(b) & set(a2))
        for k in kljucevi:
            d_ab.append(b[k] - a1[k])       # sa znakom: + znaci da B ocjenjuje vise
            d_aa.append(a2[k] - a1[k])

        if len(kljucevi) > 1:               # argmax ima smisla tek od 2 kandidata
            arg_uporedivih += 1
            best_a1 = max(kljucevi, key=lambda k: a1[k])
            if max(kljucevi, key=lambda k: b[k])  != best_a1:
                arg_ab += 1
            if max(kljucevi, key=lambda k: a2[k]) != best_a1:
                arg_aa += 1
        print(f"  {n}/{len(grupe)} s{poz}", flush=True)

    if not d_ab:
        print("Nema uporedivih parova.")
        sys.exit(1)

    mae_ab = st.mean(abs(x) for x in d_ab)
    mae_aa = st.mean(abs(x) for x in d_aa)
    print(f"\nParova: {len(d_ab)} | preskoceno recenica: {preskoceno}")
    print(f"  |B - A1|  (naziv jezika)     MAE = {mae_ab:.4f}   bias = {st.mean(d_ab):+.4f}")
    print(f"  |A2 - A1| (isti naziv, sum)  MAE = {mae_aa:.4f}   bias = {st.mean(d_aa):+.4f}")
    print(f"  odnos signal/sum = {(mae_ab / mae_aa if mae_aa else float('inf')):.2f}")
    print(f"  razlika > 0.05:  B vs A1 = {sum(1 for x in d_ab if abs(x) > 0.05)}"
          f" | A2 vs A1 = {sum(1 for x in d_aa if abs(x) > 0.05)}")

    if arg_uporedivih:
        print(f"\n  ARGMAX (recenica s >1 kandidatom: {arg_uporedivih})")
        print(f"    pobjednik promijenjen  B vs A1 = {arg_ab}"
              f" ({100.0*arg_ab/arg_uporedivih:.1f}%)")
        print(f"    pobjednik promijenjen A2 vs A1 = {arg_aa}"
              f" ({100.0*arg_aa/arg_uporedivih:.1f}%)   <- sum")


if __name__ == "__main__":
    main()
