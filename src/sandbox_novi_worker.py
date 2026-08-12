#!/usr/bin/env python3
"""
sandbox_novi_worker.py — READ-ONLY sonda (s172).

Pitanje: vrijedi li qwen3.5:397b kao TRECI worker uz mistral i glm?
Sonda ponasanja (sandbox_model_probe) kaze da model radi; ovo mjeri KVALITET,
kroz istu mjeru koju pipeline koristi za odluku.

Dizajn — po recenici pet kandidata, isti skup, jedan poziv sudiji:
  M   najbolji mistral iz baze     (postojeci)
  G   najbolji glm iz baze         (postojeci)
  N   nllb iz baze                 (postojeci)
  Q1  novi kandidat @ temp 0.1
  Q8  novi kandidat @ temp 0.8
Isti broj kandidata kao produkcijski "svijet 1", pa je rang direktno citljiv.

Sudija (gemma4, nepromijenjen, slijep) ocjenjuje svih pet U JEDNOM POZIVU,
redoslijed randomizovan po recenici. Drugi prolaz istim sudijom daje sum seta.

finalni_score = 0.4*kompozitni + 0.6*sudija, kanonska formula. Za M/G/N
kompozitni dolazi iz baze (embedding, deterministican), sudijina ocjena je NOVA
iz ovog poziva — inace bi se novi kandidat poredio protiv ocjene iz druge
sudijske ere (s167).

NULA UPISA U BAZU. Model se NE registruje u bb_modeli.
"""

import os, sys, random, argparse
import statistics as st
import psycopg2
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
load_dotenv(os.path.join(os.path.dirname(HERE), ".env"))

import bb_03_prevod as bb03
import bb_08_sudija as sud
from sentence_transformers import SentenceTransformer

OZN = ["M", "G", "N", "Q1", "Q8"]


def db():
    return psycopg2.connect(host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
                            dbname="bb", user=os.getenv("DB_USER"),
                            password=os.getenv("DB_PASSWORD"))


def uzmi_teren(cur, knjiga, jezik, n):
    cur.execute("""
        WITH k AS (
          SELECT recenica_id, recenica_pozicija, recenica_tekst, model_naziv, prevod,
                 (score+translation_score)/2 AS komp, finalni_score,
                 ROW_NUMBER() OVER (PARTITION BY recenica_id, model_naziv
                                    ORDER BY finalni_score DESC NULLS LAST) AS rn
          FROM v_prevodi_full
          WHERE knjiga_id=%s AND jezik_kod=%s AND faza_id=1 AND prevod IS NOT NULL
        )
        SELECT recenica_id, recenica_pozicija, recenica_tekst,
          MAX(CASE WHEN model_naziv LIKE 'mistral%%' THEN prevod END),
          MAX(CASE WHEN model_naziv LIKE 'mistral%%' THEN komp END),
          MAX(CASE WHEN model_naziv LIKE 'glm%%'     THEN prevod END),
          MAX(CASE WHEN model_naziv LIKE 'glm%%'     THEN komp END),
          MAX(CASE WHEN model_naziv LIKE 'nllb%%'    THEN prevod END),
          MAX(CASE WHEN model_naziv LIKE 'nllb%%'    THEN komp END)
        FROM k WHERE rn=1
        GROUP BY recenica_id, recenica_pozicija, recenica_tekst
        HAVING MAX(CASE WHEN model_naziv LIKE 'mistral%%' THEN prevod END) IS NOT NULL
           AND MAX(CASE WHEN model_naziv LIKE 'glm%%'     THEN prevod END) IS NOT NULL
           AND MAX(CASE WHEN model_naziv LIKE 'nllb%%'    THEN prevod END) IS NOT NULL
        ORDER BY recenica_pozicija
    """, (knjiga, jezik))
    r = cur.fetchall()
    random.shuffle(r)
    return r[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--knjiga", type=int, default=23)
    ap.add_argument("--jezik", required=True)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--worker", default="qwen3.5:397b")
    ap.add_argument("--seed-rng", type=int, default=42)
    ap.add_argument("--izlaz", default="/tmp/novi_worker.tsv")
    args = ap.parse_args()
    random.seed(args.seed_rng)

    conn = db(); cur = conn.cursor()
    bb03.ucitaj_jezike(cur)
    lang = bb03.JEZIK_NAZIVI[args.jezik]
    cur.execute("""SELECT p.prompt_prevod_batch, p.prompt_back_batch
                   FROM bb_faze_a3 a3 JOIN bb_promptovi p ON a3.prompt_id=p.id
                   WHERE a3.faza_id=1 AND a3.aktivan""")
    TPL_P, TPL_B = cur.fetchone()
    emb = SentenceTransformer(bb03.EMBEDDER_PATH_MAP.get("multilingual-e5-large",
                                                         "multilingual-e5-large"))

    teren = uzmi_teren(cur, args.knjiga, args.jezik, args.n)
    S = [{"rid": r[0], "poz": r[1], "en": r[2], "M": r[3], "M_komp": float(r[4]),
          "G": r[5], "G_komp": float(r[6]), "N": r[7], "N_komp": float(r[8])}
         for r in teren]
    print(f"k{args.knjiga}/{args.jezik}: {len(S)} recenica s kandidatom iz sve tri porodice")

    # ── novi worker, dvije temperature
    for tag, temp in (("Q1", 0.1), ("Q8", 0.8)):
        print(f"\n── {args.worker} @ {temp}  (oznaka {tag})")
        B = 20
        for i in range(0, len(S), B):
            ch = S[i:i+B]
            tx = [s["en"] for s in ch]
            pr = bb03.prevedi_batch(tx, lang, args.worker, temp, TPL_P)
            if pr is None:
                print("    [fallback single]")
                pr = [bb03.prevedi_single(t, lang, args.worker, temp, TPL_P) for t in tx]
            bk = bb03.back_prevedi_batch(pr, lang, args.worker, temp, TPL_B)
            if bk is None:
                print("    [fallback single back]")
                bk = [bb03.back_prevedi_single(p, lang, args.worker, temp, TPL_B) for p in pr]
            for s, p, b in zip(ch, pr, bk):
                s[tag], s[f"{tag}_back"] = p, b
            print(f"    batch {i//B+1} ok")
        ev = emb.encode([s["en"] for s in S])
        pv = emb.encode([s[tag] for s in S])
        bv = emb.encode([s[f"{tag}_back"] for s in S])
        for j, s in enumerate(S):
            ts, bts = bb03.cosine(ev[j], pv[j]), bb03.cosine(ev[j], bv[j])
            s[f"{tag}_komp"] = (ts + bts) / 2
            s[f"{tag}_klon"] = 1 if s[tag] in (s["M"], s["G"], s["N"]) else 0

    # ── sudija: dva prolaza (drugi = sum)
    print("\n── Sudija gemma4 (svih pet kandidata u jednom pozivu)")
    for k, s in enumerate(S):
        red = OZN[:]; random.shuffle(red); s["red"] = red
        lista = [s[o] for o in red]
        tr = "\n".join(f"{i+1}. {t}" for i, t in enumerate(lista))
        prompt = sud.PROMPT_TEMPLATE.format(lang=lang, original=s["en"], translations=tr)
        for tag in ("S1", "S2"):
            oc = sud.parse_ocjene(sud.call_sudija(prompt))
            s[f"{tag}_ok"] = 0
            if oc:
                for o in oc:
                    try:
                        idx = int(o["id"]) - 1
                        s[f"{tag}_{red[idx]}"] = (float(o["grammar"]) + float(o["naturalness"])
                                                  + float(o["fidelity"])) / 3
                    except (KeyError, ValueError, TypeError, IndexError):
                        continue
                s[f"{tag}_ok"] = 1 if all(f"{tag}_{o}" in s for o in OZN) else 0
        if (k+1) % 10 == 0:
            print(f"    {k+1}/{len(S)}")

    V = [s for s in S if s.get("S1_ok") and s.get("S2_ok")]
    for s in V:
        for o in OZN:
            s[f"F_{o}"] = 0.4 * s[f"{o}_komp"] + 0.6 * s[f"S1_{o}"]

    print(f"\n{'='*72}\nREZULTAT k{args.knjiga}/{args.jezik}  worker={args.worker}  n={len(V)}/{len(S)}\n{'='*72}")
    print(f"{'kandidat':<10}{'sudija':>9}{'kompozit':>10}{'finalni':>10}{'pobjede':>9}{'klon':>7}")
    for o in OZN:
        klon = f"{100*sum(s.get(f'{o}_klon',0) for s in V)/len(V):.0f}%" if o.startswith("Q") else "—"
        pob = sum(1 for s in V if max(OZN, key=lambda x: s[f"F_{x}"]) == o)
        print(f"{o:<10}{st.mean(s[f'S1_{o}'] for s in V):>9.4f}{st.mean(s[f'{o}_komp'] for s in V):>10.4f}"
              f"{st.mean(s[f'F_{o}'] for s in V):>10.4f}{pob:>6}/{len(V)}{klon:>7}")
    mae = st.mean(abs(s[f"S1_{o}"] - s[f"S2_{o}"]) for s in V for o in OZN)
    print(f"\nsum sudije (MAE S1 vs S2, isti prompt): {mae:.4f}")
    bezQ = sum(1 for s in V if max(("M","G","N"), key=lambda x: s[f"F_{x}"]) and
               max(OZN, key=lambda x: s[f"F_{x}"]) in ("Q1","Q8"))
    print(f"qwen bi promijenio pobjednika u: {bezQ}/{len(V)} recenica")
    dob = [max(s["F_Q1"], s["F_Q8"]) - max(s["F_M"], s["F_G"], s["F_N"]) for s in V]
    print(f"prosjecan dobitak kad qwen pobijedi: "
          f"{st.mean([d for d in dob if d>0]) if any(d>0 for d in dob) else 0:.4f}")
    print(f"prosjek najboljeg BEZ qwena: {st.mean(max(s['F_M'],s['F_G'],s['F_N']) for s in V):.4f}"
          f" | SA qwenom: {st.mean(max(s['F_M'],s['F_G'],s['F_N'],s['F_Q1'],s['F_Q8']) for s in V):.4f}")

    with open(args.izlaz, "w") as f:
        f.write("rid\tpoz\t" + "\t".join(f"F_{o}" for o in OZN) + "\t" +
                "\t".join(f"sud_{o}" for o in OZN) + "\tQ1_klon\tQ8_klon\n")
        for s in V:
            f.write(f"{s['rid']}\t{s['poz']}\t" +
                    "\t".join(f"{s[f'F_{o}']:.4f}" for o in OZN) + "\t" +
                    "\t".join(f"{s[f'S1_{o}']:.4f}" for o in OZN) +
                    f"\t{s['Q1_klon']}\t{s['Q8_klon']}\n")
    print(f"\nTSV: {args.izlaz}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
