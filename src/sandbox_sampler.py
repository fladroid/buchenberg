#!/usr/bin/env python3
"""
s173 SONDA (READ-ONLY): mjeri da li top_p/top_k defaultovi sijeku ono sto
temperatura otvara.  Ne upisuje nista, ne dira bb_03.

Rukavci (svaki = 4 odvojena poziva nad ISTIM batchom od N recenica):
  A1  temp 0.8                       -> danasnje ponasanje
  A2  temp 0.8                       -> sum ponavljanja
  B   temp 0.8, top_p 1.0, top_k 0   -> je li rep odsjecen?
  C   temp 1.0, top_p 1.0, top_k 0   -> Flaviova ideja, otvoren rep
  D   temp 1.3, top_p 1.0, top_k 0   -> koliko daleko prije raspada
  E   temp 1.0                       -> RAZDVAJA: je li zasluga temperature
                                        ili otvorenog repa?  C-E = doprinos repa,
                                        E-A = doprinos temperature

Mjere:
  raznolikost = prosjecan broj RAZLICITIH tekstova od 4 poziva, po recenici
  kvalitet    = sudija gemma4 nad po jednim kandidatom iz svakog rukavca,
                svih 6 u JEDNOM pozivu (sastav skupa mijenja ocjenu, s172)
"""
import os, sys, json, argparse, statistics as st
import requests, psycopg2
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import bb_03_prevod as bb03
import bb_08_sudija as sud

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY = os.getenv("OLLAMA_API_KEY", "")
WORKER = "mistral-large-3:675b"

RUKAVCI = [
    ("A1", {"temperature": 0.8}),
    ("A2", {"temperature": 0.8}),
    ("B",  {"temperature": 0.8, "top_p": 1.0, "top_k": 0}),
    ("C",  {"temperature": 1.0, "top_p": 1.0, "top_k": 0}),
    ("D",  {"temperature": 1.3, "top_p": 1.0, "top_k": 0}),
    ("E",  {"temperature": 1.0}),
]


def db():
    return psycopg2.connect(host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
                            dbname="bb", user=os.getenv("DB_USER"),
                            password=os.getenv("DB_PASSWORD"))


def chat(messages, options, max_retries=3, wait=30):
    """Kao bb03.ollama_chat, ali prima PUN options dict."""
    import time
    payload = {"model": WORKER, "messages": messages, "stream": False,
               "think": False, "options": options}
    headers = {"Authorization": f"Bearer {OLLAMA_KEY}", "Content-Type": "application/json"}
    for a in range(max_retries):
        try:
            r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload,
                              headers=headers, timeout=120)
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except Exception as e:
            if a == max_retries - 1:
                print(f"    [greska] {e}")
                return None
            time.sleep(wait)
    return None


def prevedi(tekstovi, jezik_naziv, tpl, options):
    """Batch prevod, isti format kao bb03.prevedi_batch."""
    numerirani = "\n".join(f"{i+1}. {t}" for i, t in enumerate(tekstovi))
    out = chat([{"role": "user",
                 "content": tpl.format(jezik_naziv=jezik_naziv, numerirani=numerirani)}],
               options)
    if out is None:
        return None
    linije = [l.strip() for l in out.split("\n") if l.strip()]
    ocisc = []
    for l in linije:
        if l[0].isdigit() and "." in l[:4]:
            ocisc.append(l.split(".", 1)[1].strip())
    return ocisc if len(ocisc) == len(tekstovi) else None


def ocijeni(lang, original, tekstovi):
    """Jedan poziv sudiji nad listom kandidata -> {index: avg}."""
    try:
        tr = "\n".join(f"{i+1}. {t}" for i, t in enumerate(tekstovi))
        prompt = sud.PROMPT_TEMPLATE.format(lang=lang, original=original, translations=tr)
        ocjene = sud.parse_ocjene(sud.call_sudija(prompt))
    except Exception as e:
        print(f"    [sudija greska] {e}")
        return None
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
    ap.add_argument("--n", type=int, default=15, help="recenica u batchu")
    ap.add_argument("--ponavljanja", type=int, default=4)
    ap.add_argument("--od", type=int, default=1)
    ap.add_argument("--izlaz", default="/tmp/sampler.tsv")
    args = ap.parse_args()

    conn = db(); cur = conn.cursor()
    bb03.ucitaj_jezike(cur)
    lang = bb03.JEZIK_NAZIVI[args.jezik]

    cur.execute("""SELECT p.prompt_prevod_batch FROM bb_faze_a3 a3
                   JOIN bb_promptovi p ON a3.prompt_id=p.id
                   WHERE a3.faza_id=1 AND a3.aktivan""")
    TPL = cur.fetchone()[0]

    cur.execute("""SELECT id, pozicija, tekst FROM bb_recenice
                   WHERE knjiga_id=%s AND pozicija >= %s
                     AND length(tekst) BETWEEN 60 AND 300
                   ORDER BY pozicija LIMIT %s""", (args.knjiga, args.od, args.n))
    rec = cur.fetchall()
    if len(rec) < args.n:
        print(f"UPOZORENJE: nasao samo {len(rec)} recenica"); 
    tekstovi = [r[2] for r in rec]
    print(f"Teren: k{args.knjiga}/{args.jezik}, {len(rec)} recenica, "
          f"pozicije {rec[0][1]}-{rec[-1][1]}, jezik u promptu: {lang}")
    print(f"Rukavaca: {len(RUKAVCI)} x {args.ponavljanja} poziva = "
          f"{len(RUKAVCI)*args.ponavljanja} prevoda + {len(rec)} sudija\n")

    # -- prevodi
    rez = {}   # rukavac -> lista od P lista prevoda
    for ime, opt in RUKAVCI:
        print(f"-- {ime}: {json.dumps(opt)}")
        prolazi = []
        for p in range(args.ponavljanja):
            out = prevedi(tekstovi, lang, TPL, opt)
            if out is None:
                print(f"    poziv {p+1}: NEUSPJEH (poravnanje ili greska)")
                continue
            prolazi.append(out)
            print(f"    poziv {p+1}: OK")
        rez[ime] = prolazi

    # -- raznolikost
    print("\n" + "="*64)
    print(f"{'rukavac':<10}{'prolaza':>9}{'razlicitih/N':>14}{'klon-stopa':>13}")
    print("-"*64)
    raznolikost = {}
    for ime, _ in RUKAVCI:
        pr = rez[ime]
        if len(pr) < 2:
            print(f"{ime:<10}{len(pr):>9}{'-':>14}{'-':>13}"); continue
        po_rec = [len(set(p[i] for p in pr)) for i in range(len(tekstovi))]
        klon = sum(1 for v in po_rec if v == 1) / len(po_rec)
        raznolikost[ime] = st.mean(po_rec)
        print(f"{ime:<10}{len(pr):>9}{st.mean(po_rec):>10.2f}/{len(pr)}"
              f"{klon*100:>12.1f}%")

    # -- kvalitet: po jedan kandidat iz svakog rukavca, svi u JEDNOM pozivu
    print("\n-- sudija (gemma4, svi rukavci u jednom pozivu po recenici)")
    imena = [i for i, _ in RUKAVCI if rez[i]]
    zbir = {i: [] for i in imena}
    for idx, (rid, poz, en) in enumerate(rec):
        kand = [rez[i][0][idx] for i in imena]
        oc = ocijeni(lang, en, kand)
        if oc is None:
            print(f"    poz {poz}: sudija preskocen"); continue
        for j, i in enumerate(imena):
            zbir[i].append(oc[j])
    print("\n" + "="*64)
    print(f"{'rukavac':<10}{'n':>5}{'sudija avg':>13}{'razlicitih':>13}")
    print("-"*64)
    for i in imena:
        v = zbir[i]
        if not v: continue
        print(f"{i:<10}{len(v):>5}{st.mean(v):>13.4f}"
              f"{raznolikost.get(i, float('nan')):>13.2f}")
    print("="*64)
    if "A1" in zbir and "A2" in zbir and zbir["A1"] and zbir["A2"]:
        sum_ocjena = abs(st.mean(zbir["A1"]) - st.mean(zbir["A2"]))
        print(f"SUM (|A1-A2|): ocjena {sum_ocjena:.4f} | "
              f"raznolikost {abs(raznolikost.get('A1',0)-raznolikost.get('A2',0)):.2f}")
        print("Svaka razlika manja od suma NIJE nalaz.")

    with open(args.izlaz, "w") as f:
        f.write("rukavac\tpoziv\tpozicija\tprevod\n")
        for ime, _ in RUKAVCI:
            for p, prolaz in enumerate(rez[ime]):
                for idx, t in enumerate(prolaz):
                    f.write(f"{ime}\t{p+1}\t{rec[idx][1]}\t{t}\n")
    print(f"\nSirovi tekstovi: {args.izlaz}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
