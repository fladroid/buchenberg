#!/usr/bin/env python3
"""
sandbox_zamjena_uloga.py — READ-ONLY sonda (s172).

Pitanje (Flavio): sta ako zamijenimo uloge — gemma4:31b prevodi, a
mistral-large-3:675b sudi?

Dva odvojena pitanja u jednom dizajnu:
  (1) GEMMA KAO WORKER — kako se gemmin prevod rangira medju postojecim
      kandidatima (mistral / glm / nllb).
  (2) MISTRAL KAO SUDIJA — mijenja li se rangiranje kad sudi drugi model.

ZAMKA koju dizajn mora uhvatiti: gemma nikad ne prevodi, pa kao sudija nema
sta da favorizuje. Mistral JESTE aktivan prevodilac — kao sudija ocjenjuje
vlastite prevode. Self-preference se mjeri kao razlika-razlika:
      (S_mistral(M) - S_gemma(M)) - (S_mistral(GW) - S_gemma(GW))
gdje je M mistralov prevod a GW gemmin. Ako je pozitivno, mistral podize svoje.

Tri sudijska prolaza nad ISTIM kandidatima: gemma (S1), mistral (S2),
gemma opet (S1b = sum ovog seta). Bez treceg prolaza razlika S1-S2 nema
protiv cega da se mjeri.

Redoslijed kandidata randomizovan po recenici (sudija ostaje slijep).
NULA UPISA U BAZU. bb_08 se ne mijenja — SUDIJA_MODEL se privremeno zamijeni
u memoriji sonde.
"""

import os
import sys
import random
import argparse
import statistics as st

import psycopg2
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
load_dotenv(os.path.join(os.path.dirname(HERE), ".env"))

import bb_03_prevod as bb03
import bb_08_sudija as sud
from sentence_transformers import SentenceTransformer

GEMMA = "gemma4:31b"
MISTRAL = "mistral-large-3:675b"


def db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname="bb", user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
    )


def uzmi_teren(cur, knjiga, jezik, n):
    """Recenice koje imaju kandidata od SVE TRI porodice (mistral, glm, nllb)."""
    cur.execute("""
        WITH k AS (
          SELECT recenica_id, recenica_pozicija, recenica_tekst, model_naziv, prevod,
                 finalni_score,
                 ROW_NUMBER() OVER (PARTITION BY recenica_id, model_naziv
                                    ORDER BY finalni_score DESC NULLS LAST) AS rn
          FROM v_prevodi_full
          WHERE knjiga_id=%s AND jezik_kod=%s AND faza_id=1 AND prevod IS NOT NULL
        )
        SELECT recenica_id, recenica_pozicija, recenica_tekst,
               MAX(CASE WHEN model_naziv LIKE 'mistral%%' THEN prevod END) AS m,
               MAX(CASE WHEN model_naziv LIKE 'glm%%'     THEN prevod END) AS g,
               MAX(CASE WHEN model_naziv LIKE 'nllb%%'    THEN prevod END) AS nl
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


def ocijeni(model, lang, original, tekstovi):
    """Jedan poziv sudiji nad listom tekstova. Vrati {index: avg} ili None."""
    stari = sud.SUDIJA_MODEL
    sud.SUDIJA_MODEL = model
    try:
        tr = "\n".join(f"{i+1}. {t}" for i, t in enumerate(tekstovi))
        prompt = sud.PROMPT_TEMPLATE.format(lang=lang, original=original, translations=tr)
        ocjene = sud.parse_ocjene(sud.call_sudija(prompt))
    except Exception as e:
        print(f"    [sudija {model} greska] {e}")
        return None
    finally:
        sud.SUDIJA_MODEL = stari
    if not ocjene:
        return None
    out = {}
    for o in ocjene:
        try:
            out[int(o["id"]) - 1] = (float(o["grammar"]) + float(o["naturalness"])
                                     + float(o["fidelity"])) / 3
        except (KeyError, ValueError, TypeError):
            continue
    return out if len(out) == len(tekstovi) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--knjiga", type=int, default=23)
    ap.add_argument("--jezik", required=True)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--seed-rng", type=int, default=42)
    ap.add_argument("--izlaz", default="/tmp/zamjena_uloga.tsv")
    args = ap.parse_args()
    random.seed(args.seed_rng)

    conn = db(); cur = conn.cursor()
    bb03.ucitaj_jezike(cur)
    lang = bb03.JEZIK_NAZIVI[args.jezik]

    cur.execute("""
        SELECT p.prompt_prevod_batch, p.prompt_back_batch
        FROM bb_faze_a3 a3 JOIN bb_promptovi p ON a3.prompt_id=p.id
        WHERE a3.faza_id=1 AND a3.aktivan
    """)
    TPL_PREVOD, TPL_BACK = cur.fetchone()

    embedder = SentenceTransformer(
        bb03.EMBEDDER_PATH_MAP.get("multilingual-e5-large", "multilingual-e5-large"))

    teren = uzmi_teren(cur, args.knjiga, args.jezik, args.n)
    print(f"Recenica s kandidatom iz sve tri porodice: {len(teren)}")
    st_ = [{"rid": r[0], "poz": r[1], "en": r[2], "M": r[3], "G": r[4], "N": r[5]}
           for r in teren]

    # ── (1) GEMMA KAO WORKER
    print(f"\n── Gemma kao prevodilac ({GEMMA}@{args.temp}, base prompt)")
    B = 20
    for i in range(0, len(st_), B):
        ch = st_[i:i+B]
        tekstovi = [s["en"] for s in ch]
        pr = bb03.prevedi_batch(tekstovi, lang, GEMMA, args.temp, TPL_PREVOD)
        if pr is None:
            print("    [fallback single prevod]")
            pr = [bb03.prevedi_single(t, lang, GEMMA, args.temp, TPL_PREVOD) for t in tekstovi]
        bk = bb03.back_prevedi_batch(pr, lang, GEMMA, args.temp, TPL_BACK)
        if bk is None:
            print("    [fallback single back]")
            bk = [bb03.back_prevedi_single(p, lang, GEMMA, args.temp, TPL_BACK) for p in pr]
        for s, p, b in zip(ch, pr, bk):
            s["GW"], s["GW_back"] = p, b
        print(f"    batch {i//B+1} ok")

    ev = embedder.encode([s["en"] for s in st_])
    pv = embedder.encode([s["GW"] for s in st_])
    bv = embedder.encode([s["GW_back"] for s in st_])
    for j, s in enumerate(st_):
        ts, bts = bb03.cosine(ev[j], pv[j]), bb03.cosine(ev[j], bv[j])
        s["GW_komp"] = (ts + bts) / 2

    # ── (2) TRI SUDIJSKA PROLAZA nad istim kandidatima
    print(f"\n── Sudije: S1={GEMMA}  S2={MISTRAL}  S1b={GEMMA} (sum)")
    OZN = ["M", "G", "N", "GW"]
    for k, s in enumerate(st_):
        red = OZN[:]
        random.shuffle(red)
        s["red"] = red
        lista = [s[o] for o in red]
        for tag, model in (("S1", GEMMA), ("S2", MISTRAL), ("S1b", GEMMA)):
            oc = ocijeni(model, lang, s["en"], lista)
            if oc is None:
                s[f"{tag}_ok"] = 0
                continue
            s[f"{tag}_ok"] = 1
            for idx, avg in oc.items():
                s[f"{tag}_{red[idx]}"] = avg
        if (k + 1) % 10 == 0:
            print(f"    {k+1}/{len(st_)}")

    val = [s for s in st_ if s.get("S1_ok") and s.get("S2_ok") and s.get("S1b_ok")]
    print(f"\n{'='*70}\nREZULTAT  k{args.knjiga}/{args.jezik}  n={len(val)}/{len(st_)} s sva tri prolaza\n{'='*70}")

    print("\n(1) GEMMA KAO WORKER — prosjecna sudijina ocjena po autoru prevoda")
    print(f"{'autor':<10}{'S1 gemma':>11}{'S2 mistral':>12}{'S1b gemma':>11}{'komp':>9}")
    for o in OZN:
        komp = f"{st.mean(s['GW_komp'] for s in val):.4f}" if o == "GW" else "   (baza)"
        print(f"{o:<10}{st.mean(s[f'S1_{o}'] for s in val):>11.4f}"
              f"{st.mean(s[f'S2_{o}'] for s in val):>12.4f}"
              f"{st.mean(s[f'S1b_{o}'] for s in val):>11.4f}{komp:>9}")

    def argmax(s, tag):
        return max(OZN, key=lambda o: s[f"{tag}_{o}"])
    slag_s1_s2 = sum(1 for s in val if argmax(s, "S1") == argmax(s, "S2"))
    slag_s1_s1b = sum(1 for s in val if argmax(s, "S1") == argmax(s, "S1b"))
    print(f"\n(2) MISTRAL KAO SUDIJA — slaganje izbora pobjednika")
    print(f"    gemma naspram mistrala:  {slag_s1_s2}/{len(val)} ({100*slag_s1_s2/len(val):.1f}%)")
    print(f"    gemma naspram sebe:      {slag_s1_s1b}/{len(val)} ({100*slag_s1_s1b/len(val):.1f}%)  <- sum")
    mae12 = st.mean(abs(s[f"S1_{o}"] - s[f"S2_{o}"]) for s in val for o in OZN)
    mae11 = st.mean(abs(s[f"S1_{o}"] - s[f"S1b_{o}"]) for s in val for o in OZN)
    print(f"    MAE gemma-mistral: {mae12:.4f} | MAE gemma-gemma (sum): {mae11:.4f}")

    print(f"\n(3) SELF-PREFERENCE (razlika-razlika, + znaci 'sudija podize svoje')")
    dM = st.mean(s["S2_M"] - s["S1_M"] for s in val)
    dGW = st.mean(s["S2_GW"] - s["S1_GW"] for s in val)
    dG = st.mean(s["S2_G"] - s["S1_G"] for s in val)
    dN = st.mean(s["S2_N"] - s["S1_N"] for s in val)
    print(f"    mistral podize mistralov prevod za {dM:+.4f}, gemmin za {dGW:+.4f}")
    print(f"    (glm {dG:+.4f}, nllb {dN:+.4f})")
    print(f"    BIAS = (M) - (GW) = {dM - dGW:+.4f}")
    print(f"    referenca suma (S1b-S1, isti model): {st.mean(s['S1b_M'] - s['S1_M'] for s in val):+.4f}")

    pob_s1 = {o: sum(1 for s in val if argmax(s, "S1") == o) for o in OZN}
    pob_s2 = {o: sum(1 for s in val if argmax(s, "S2") == o) for o in OZN}
    print(f"\n(4) KO POBJEDJUJE\n    po gemmi:   " + "  ".join(f"{o}={pob_s1[o]}" for o in OZN))
    print(f"    po mistralu: " + "  ".join(f"{o}={pob_s2[o]}" for o in OZN))

    with open(args.izlaz, "w") as f:
        f.write("rid\tpoz\t" + "\t".join(f"{t}_{o}" for t in ("S1","S2","S1b") for o in OZN) + "\tGW_komp\n")
        for s in val:
            f.write(f"{s['rid']}\t{s['poz']}\t" +
                    "\t".join(f"{s[f'{t}_{o}']:.4f}" for t in ("S1","S2","S1b") for o in OZN) +
                    f"\t{s['GW_komp']:.4f}\n")
    print(f"\nTSV: {args.izlaz}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
