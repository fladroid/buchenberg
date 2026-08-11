#!/usr/bin/env python3
"""
sandbox_batch_ponavljanje.py -- READ-ONLY sonda (s170)

PITANJE: ako u batch od 20 stavimo 5 recenica ponovljenih 4 puta,
dobijamo li 4 klona ili 4 razlicita prevoda?

Dvije sile vuku na suprotne strane:
  - kopiranje iz vlastitog konteksta (batch je JEDAN autoregresivni tok) -> klon
  - Ollama default repeat_penalty (~1.1) kaznjava ponavljanje          -> varijacija

CETIRI RUKAVCA, isti model/temperatura/prompt, iste ciljne recenice:
  A1 prepleteno  1 poziv,  20 stavki = 5 recenica x4, redoslijed 1..5,1..5,...
  A2 blokovi     1 poziv,  20 stavki = 5 recenica x4, redoslijed 1,1,1,1,2,2,...
  B  batch5      4 poziva, po 5 stavki (iste recenice)
  C  batch20     4 poziva, po 20 stavki (ciljnih 5 + 15 susjednih) = PRODUKCIJSKI

MJERI: broj razlicitih tekstova od 4 pokusaja po recenici, stopu klona po
parovima (6 parova po recenici), prosjecan kosinus medju varijantama.

NULA upisa u bazu. Iz baze samo cita recenice, prompt sablon i naziv jezika.
"""
import os, sys, argparse, itertools, importlib.util
import numpy as np
import psycopg2
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE, ".env"))

spec = importlib.util.spec_from_file_location(
    "bb_03_prevod", os.path.join(BASE, "src", "bb_03_prevod.py"))
bb03 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bb03)          # bezbjedno: bb_03 ima __main__ guard


def db():
    return psycopg2.connect(host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
                            dbname="bb", user=os.getenv("DB_USER"),
                            password=os.getenv("DB_PASSWORD"))


def statistika(v):
    parovi = list(itertools.combinations(range(len(v)), 2))
    isti = sum(1 for i, j in parovi if v[i] == v[j])
    return len(set(v)), isti, len(parovi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--knjiga", type=int, default=22)
    ap.add_argument("--od", type=int, default=1500)
    ap.add_argument("--broj", type=int, default=5)
    ap.add_argument("--ponavljanja", type=int, default=4)
    ap.add_argument("--jezici", nargs="+", default=["hr", "de"])
    ap.add_argument("--model", default="mistral-large-3:675b")
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--prompt", default="base")
    ap.add_argument("--bez-kosinusa", action="store_true")
    a = ap.parse_args()

    K, P = a.broj, a.ponavljanja
    cn = db(); cur = cn.cursor()
    cur.execute("SELECT prompt_prevod_batch FROM bb_promptovi WHERE naziv=%s", (a.prompt,))
    tpl = cur.fetchone()[0]
    cur.execute("SELECT kod, naziv_en FROM bb_jezik WHERE TRIM(kod) = ANY(%s)", (a.jezici,))
    imena = {k.strip(): v for k, v in cur.fetchall()}
    rec = bb03.get_recenice(cur, a.knjiga, a.od, a.od + 19)
    cn.close()
    if len(rec) < 20:
        sys.exit("Treba 20 recenica od pozicije %d, nadjeno %d." % (a.od, len(rec)))
    cilj = [r[2] for r in rec[:K]]
    puni = [r[2] for r in rec[:20]]

    print("knjiga=%d pozicije=%d-%d ciljnih=%d ponavljanja=%d"
          % (a.knjiga, a.od, a.od + 19, K, P))
    print("model=%s temp=%s prompt='%s' jezici=%s" % (a.model, a.temp, a.prompt, a.jezici))
    print("repeat_penalty: NIJE postavljen u bb_03 -> Ollama default\n")
    for i, t in enumerate(cilj):
        print("  [%d] %s" % (i + 1, t[:90]))
    print("", flush=True)

    embedder = None
    if not a.bez_kosinusa:
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer("intfloat/multilingual-e5-large")

    rezultat = {}
    for kod in a.jezici:
        jn = imena[kod]
        print("=== %s (%s) ===" % (kod, jn), flush=True)
        var = {r: {i: [] for i in range(K)} for r in ("A1", "A2", "B", "C")}

        out = bb03.prevedi_batch(cilj * P, jn, a.model, a.temp, tpl)
        if out:
            for idx, t in enumerate(out):
                var["A1"][idx % K].append(t)
        else:
            print("  A1: poravnanje palo")

        out = bb03.prevedi_batch([s for s in cilj for _ in range(P)], jn, a.model, a.temp, tpl)
        if out:
            for idx, t in enumerate(out):
                var["A2"][idx // P].append(t)
        else:
            print("  A2: poravnanje palo")

        for _ in range(P):
            out = bb03.prevedi_batch(cilj, jn, a.model, a.temp, tpl)
            if out:
                for idx, t in enumerate(out):
                    var["B"][idx].append(t)

        for _ in range(P):
            out = bb03.prevedi_batch(puni, jn, a.model, a.temp, tpl)
            if out:
                for idx in range(K):
                    var["C"][idx].append(out[idx])

        print("\n  %-10s%14s%13s%8s%10s" % ("rukavac", "razlicitih/N", "klon-parova", "stopa", "kosinus"))
        for r in ("A1", "A2", "B", "C"):
            razl, isti_uk, par_uk, kos = [], 0, 0, []
            for i in range(K):
                v = var[r][i]
                if len(v) < 2:
                    continue
                nr, isti, par = statistika(v)
                razl.append(nr); isti_uk += isti; par_uk += par
                if embedder and len(set(v)) > 1:
                    E = embedder.encode(list(set(v)))
                    kos += [bb03.cosine(E[x], E[y])
                            for x, y in itertools.combinations(range(len(E)), 2)]
            if not par_uk:
                print("  %-10s%14s" % (r, "--"))
                continue
            print("  %-10s%14.2f%7d/%-5d%7.1f%%%10s"
                  % (r, np.mean(razl), isti_uk, par_uk, 100.0 * isti_uk / par_uk,
                     ("%.4f" % np.mean(kos)) if kos else "--"))
        rezultat[kod] = var
        print("", flush=True)

    kod = a.jezici[0]
    print("-- Primjer (prva ciljna recenica, %s) --" % kod)
    for r in ("A1", "A2", "B", "C"):
        print("  %s:" % r)
        for t in rezultat[kod][r][0]:
            print("     %s" % t[:110])
    print("\nNula upisa u bazu.")


if __name__ == "__main__":
    main()
