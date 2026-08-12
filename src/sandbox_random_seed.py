#!/usr/bin/env python3
"""
sandbox_random_seed.py — READ-ONLY sonda (s172).

Pitanje (Flavio): danas je seed UVIJEK apsolutni pobjednik. Sto ako se sidro
bira slucajno iz skupa postojecih prevoda te recenice — po mogucnosti tako da
se pobjednik ISKLJUCI kad alternativa postoji?

Motiv: u repu se pobjednik krugovima ne mijenja, pa faza 16 svaki krug radi
doslovno isti posao (isti model, temp, prompt, ISTO SIDRO). Random sidro uvodi
varijaciju tacno tamo gdje su sve ostale ose zamrznute.

Metod — tri rukavca nad ISTIM recenicama, isti model/temp/prompt:
  A1  seed = pobjednik            (danasnje ponasanje)
  B   seed = random NE-pobjednik  (prijedlog, stroga verzija)
  A2  seed = pobjednik, opet      (sum samog ponavljanja poziva)
A2 nije visak: bez njega se razlika A1-naspram-B mjeri protiv nicega.

Sudija: JEDAN poziv po recenici koji ocjenjuje sve kandidate zajedno
(pobjednik + A1 + B + A2), redoslijed randomizovan po recenici. Time varijacija
sudije ne ulazi u poredjenje rukavaca.

Klon = izlaz doslovno jednak nekom vec postojecem prevodu te recenice.
Ocekivano je da SVI prevodi mogu biti klonovi — sonda to mjeri, ne pretpostavlja.

NULA UPISA U BAZU. Prompt, pozivi modela i cosine se IMPORTUJU, ne kopiraju.
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


def db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname="bb", user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
    )


def uzmi_teren(cur, knjiga, jezik, n, prag, samo_faza):
    """Recenice ispod praga koje imaju bar dva razlicita prevoda."""
    uslov_faza = ""
    if samo_faza:
        uslov_faza = f"""
          AND p.recenica_id IN (
              SELECT recenica_id FROM v_prevodi_full
              WHERE knjiga_id=%(k)s AND jezik_kod=%(j)s AND faza_id={int(samo_faza)}
          )"""
    cur.execute(f"""
        SELECT p.recenica_id, p.recenica_tekst, p.prevod, p.finalni_score,
               p.recenica_pozicija, p.kompozitni
        FROM v_pobjednici_full p
        WHERE p.knjiga_id=%(k)s AND p.jezik_kod=%(j)s AND p.finalni_score < %(prag)s
          AND (SELECT COUNT(DISTINCT prevod) FROM v_prevodi_full v
               WHERE v.recenica_id=p.recenica_id AND v.jezik_kod=%(j)s) > 1
          {uslov_faza}
        ORDER BY p.recenica_pozicija
    """, {"k": knjiga, "j": jezik, "prag": prag})
    redovi = cur.fetchall()
    random.shuffle(redovi)
    return redovi[:n]


def kandidati(cur, rid, jezik):
    cur.execute("""
        SELECT DISTINCT prevod FROM v_prevodi_full
        WHERE recenica_id=%s AND jezik_kod=%s AND prevod IS NOT NULL
    """, (rid, jezik))
    return [r[0] for r in cur.fetchall()]


def refine_rukavac(parovi, jezik_naziv, model, temp, tpl_prevod, tpl_back):
    """parovi = [(en_tekst, seed_tekst)]. Vrati (prevodi, backs)."""
    prevodi = bb03.prevedi_refine_batch(parovi, jezik_naziv, model, temp, tpl_prevod)
    if prevodi is None:
        print("    [fallback na single refine]")
        prevodi = [bb03.prevedi_refine_single(t, jezik_naziv, model, temp, s, TPL_SINGLE)
                   for t, s in parovi]
    backs = bb03.back_prevedi_batch(prevodi, jezik_naziv, model, temp, tpl_back)
    if backs is None:
        print("    [fallback na single back]")
        backs = [bb03.back_prevedi_single(p, jezik_naziv, model, temp, TPL_BACK_SINGLE)
                 for p in prevodi]
    return prevodi, backs


def main():
    global TPL_SINGLE, TPL_BACK_SINGLE
    ap = argparse.ArgumentParser()
    ap.add_argument("--knjiga", type=int, required=True)
    ap.add_argument("--jezik", required=True)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--model", default="mistral-large-3:675b")
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--faza", type=int, default=16, help="odakle se cita prompt (a3)")
    ap.add_argument("--prag", type=float, default=0.95)
    ap.add_argument("--samo-faza", type=int, default=0,
                    help="uzmi samo recenice koje su prosle tu fazu (npr. 16 = iscrpljen teren)")
    ap.add_argument("--seed-rng", type=int, default=42)
    ap.add_argument("--izlaz", default="/tmp/random_seed_probe.tsv")
    args = ap.parse_args()

    random.seed(args.seed_rng)

    conn = db()
    cur = conn.cursor()
    bb03.ucitaj_jezike(cur)
    jezik_naziv = bb03.JEZIK_NAZIVI[args.jezik]

    cur.execute("""
        SELECT p.naziv, p.prompt_prevod_batch, p.prompt_prevod_single,
               p.prompt_back_batch, p.prompt_back_single
        FROM bb_faze_a3 a3 JOIN bb_promptovi p ON a3.prompt_id=p.id
        WHERE a3.faza_id=%s AND a3.aktivan
    """, (args.faza,))
    naziv_prompta, TPL_BATCH, TPL_SINGLE, TPL_BACK, TPL_BACK_SINGLE = cur.fetchone()

    print(f"Prompt: {naziv_prompta} (faza {args.faza}) | model {args.model}@{args.temp} | jezik {jezik_naziv}")
    embedder = SentenceTransformer(bb03.EMBEDDER_PATH_MAP.get("multilingual-e5-large",
                                                              "multilingual-e5-large"))

    teren = uzmi_teren(cur, args.knjiga, args.jezik, args.n, args.prag, args.samo_faza)
    print(f"Recenica u terenu: {len(teren)}")
    if not teren:
        sys.exit(1)

    stavke = []
    for rid, en, pobj_tekst, pobj_final, poz, pobj_komp in teren:
        svi = kandidati(cur, rid, args.jezik)
        alt = [t for t in svi if t != pobj_tekst]
        if not alt:
            continue
        stavke.append({
            "rid": rid, "poz": poz, "en": en,
            "pobj": pobj_tekst, "pobj_final": float(pobj_final),
            "pobj_komp": float(pobj_komp),
            "svi": svi, "alt_seed": random.choice(alt), "n_distinct": len(svi),
        })
    print(f"Sa alternativom: {len(stavke)}")

    B = 5
    for naziv, kljuc_seed in (("A1", "pobj"), ("B", "alt_seed"), ("A2", "pobj")):
        izlaz_p, izlaz_b = f"{naziv}_prevod", f"{naziv}_back"
        print(f"\n── Rukavac {naziv} (seed: {'pobjednik' if kljuc_seed=='pobj' else 'random ne-pobjednik'})")
        for i in range(0, len(stavke), B):
            chunk = stavke[i:i+B]
            parovi = [(s["en"], s[kljuc_seed]) for s in chunk]
            prevodi, backs = refine_rukavac(parovi, jezik_naziv, args.model, args.temp,
                                            TPL_BATCH, TPL_BACK)
            for s, p, b in zip(chunk, prevodi, backs):
                s[izlaz_p], s[izlaz_b] = p, b
            print(f"    batch {i//B+1}/{(len(stavke)+B-1)//B} ok")

    # ── skorovi
    for naziv in ("A1", "B", "A2"):
        en_v = embedder.encode([s["en"] for s in stavke])
        pv   = embedder.encode([s[f"{naziv}_prevod"] for s in stavke])
        bv   = embedder.encode([s[f"{naziv}_back"] for s in stavke])
        for j, s in enumerate(stavke):
            ts  = bb03.cosine(en_v[j], pv[j])
            bts = bb03.cosine(en_v[j], bv[j])
            s[f"{naziv}_ts"], s[f"{naziv}_bts"] = ts, bts
            s[f"{naziv}_komp"] = (ts + bts) / 2
            s[f"{naziv}_klon"] = 1 if s[f"{naziv}_prevod"] in s["svi"] else 0
            s[f"{naziv}_klon_seeda"] = 1 if s[f"{naziv}_prevod"] == (
                s["pobj"] if naziv != "B" else s["alt_seed"]) else 0

    # ── sudija: jedan poziv po recenici, svi kandidati zajedno, redoslijed random
    print("\n── Sudija (jedan poziv po recenici, svi kandidati zajedno)")
    for k, s in enumerate(stavke):
        oznake = ["W", "A1", "B", "A2"]
        tekstovi = {"W": s["pobj"], "A1": s["A1_prevod"], "B": s["B_prevod"], "A2": s["A2_prevod"]}
        random.shuffle(oznake)
        lista = [tekstovi[o] for o in oznake]
        tr = "\n".join(f"{i+1}. {t}" for i, t in enumerate(lista))
        prompt = sud.PROMPT_TEMPLATE.format(lang=jezik_naziv, original=s["en"], translations=tr)
        ocjene = sud.parse_ocjene(sud.call_sudija(prompt))
        s["sud_ok"] = 0
        if ocjene:
            for o in ocjene:
                try:
                    idx = int(o["id"]) - 1
                    avg = (float(o["grammar"]) + float(o["naturalness"]) + float(o["fidelity"])) / 3
                    s[f"sud_{oznake[idx]}"] = avg
                except (KeyError, ValueError, TypeError, IndexError):
                    continue
            s["sud_ok"] = 1 if all(f"sud_{o}" in s for o in ("W", "A1", "B", "A2")) else 0
        if (k + 1) % 10 == 0:
            print(f"    {k+1}/{len(stavke)}")

    # ── finalni score
    for s in stavke:
        if not s["sud_ok"]:
            continue
        for naziv in ("A1", "B", "A2"):
            s[f"{naziv}_final"] = 0.4 * s[f"{naziv}_komp"] + 0.6 * s[f"sud_{naziv}"]
        # Pobjednik se preracunava ISTOM formulom i ISTOM (novom) sudijinom ocjenom:
        # njegov kompozitni je iz baze (embedding, deterministicno), sudija iz ovog poziva.
        # Bez ovoga bi se novi kandidati poredili protiv ocjene iz druge sudijske ere (s167).
        s["W_final"] = 0.4 * s["pobj_komp"] + 0.6 * s["sud_W"]

    with open(args.izlaz, "w") as f:
        f.write("rid\tpoz\tn_distinct\tpobj_final\tW_final\tsud_W\t"
                "A1_final\tB_final\tA2_final\tA1_klon\tB_klon\tA2_klon\t"
                "A1_klon_seeda\tB_klon_seeda\tA2_klon_seeda\tsud_ok\n")
        for s in stavke:
            if not s["sud_ok"]:
                f.write(f"{s['rid']}\t{s['poz']}\t{s['n_distinct']}\t{s['pobj_final']:.4f}\tNA\tNA\t"
                        "NA\tNA\tNA\tNA\tNA\tNA\tNA\tNA\tNA\t0\n")
                continue
            f.write(f"{s['rid']}\t{s['poz']}\t{s['n_distinct']}\t{s['pobj_final']:.4f}\t"
                    f"{s['W_final']:.4f}\t{s['sud_W']:.4f}\t{s['A1_final']:.4f}\t{s['B_final']:.4f}\t{s['A2_final']:.4f}\t"
                    f"{s['A1_klon']}\t{s['B_klon']}\t{s['A2_klon']}\t"
                    f"{s['A1_klon_seeda']}\t{s['B_klon_seeda']}\t{s['A2_klon_seeda']}\t1\n")

    # ── agregat
    val = [s for s in stavke if s["sud_ok"]]
    print(f"\n{'='*66}\nREZULTAT  knjiga={args.knjiga} jezik={args.jezik} n={len(val)}/{len(stavke)} ocijenjeno")
    print(f"{'='*66}")
    print(f"{'rukavac':<8}{'klon%':>8}{'klon_seeda%':>13}{'avg_final':>11}{'tuce W':>9}{'avg delta':>11}")
    for naziv in ("A1", "B", "A2"):
        klon = 100 * sum(s[f"{naziv}_klon"] for s in val) / len(val)
        klons = 100 * sum(s[f"{naziv}_klon_seeda"] for s in val) / len(val)
        af = st.mean(s[f"{naziv}_final"] for s in val)
        tuce = sum(1 for s in val if s[f"{naziv}_final"] > s["W_final"])
        delta = st.mean(s[f"{naziv}_final"] - s["W_final"] for s in val)
        print(f"{naziv:<8}{klon:>7.1f}%{klons:>12.1f}%{af:>11.4f}{tuce:>6}/{len(val)}{delta:>+11.4f}")
    print(f"\nPobjednik, stari finalni_score:      avg {st.mean(s['pobj_final'] for s in val):.4f}")
    print(f"Pobjednik, ISTI poziv sudiji (W):    avg {st.mean(s['W_final'] for s in val):.4f}")
    print(f"  (razlika = pomak sudijine ocjene izmedju era/poziva, ne kvalitet)")
    nad = sum(1 for s in val if s["B_final"] > max(s["A1_final"], s["A2_final"]))
    print(f"B bolji od OBA pobjednik-rukavca:    {nad}/{len(val)}")
    print(f"\nTSV: {args.izlaz}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
