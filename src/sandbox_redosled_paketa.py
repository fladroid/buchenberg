#!/usr/bin/env python3
"""
sandbox_redosled_paketa.py -- READ-ONLY sonda

PITANJE (Flavio): mesanje redoslijeda unutar batcha (20 recenica) -- da li
menja prevod/ocjenu VISE nego sto to cini sama nezavisna varijacija (sum)?

DIZAJN: 4 runde na ISTIH 20 recenica, isti model/temp/prompt:
  Runda 1 (O1): originalan redoslijed
  Runda 2 (S2): promijesan redoslijed (fiksan shuffle)
  Runda 3 (O3): originalan redoslijed ponovo   -> bazni sum za O
  Runda 4 (S4): ISTI shuffle kao S2 ponovo     -> bazni sum za S

MJERI po recenici (nakon un-shuffle-ovanja S2/S4 nazad na originalni indeks):
  - kosinus O1<->O3 (bazni sum, original)
  - kosinus S2<->S4 (bazni sum, mesano)
  - kosinus unakrsno (O1,O3) x (S2,S4), 4 para -> efekat mesanja
  - sudija ocjenjuje sve 4 verzije zajedno (grammar/naturalness/fidelity),
    poredi prosjek O-grupe naspram S-grupe

NULA upisa u produkcionu bazu. Samo cita recenice/prompt/jezik iz baze.
"""
import os, sys, json, random, itertools, importlib.util, re
import numpy as np
import psycopg2
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE, ".env"))

spec = importlib.util.spec_from_file_location(
    "bb_03_prevod", os.path.join(BASE, "src", "bb_03_prevod.py"))
bb03 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bb03)

import requests
OLLAMA_URL   = os.getenv("OLLAMA_URL", "https://api.ollama.com")
OLLAMA_KEY   = os.getenv("OLLAMA_API_KEY", "")
SUDIJA_MODEL = "gemma4:31b"
SUDIJA_TEMP  = 0.0

SUDIJA_TPL = """You are evaluating {lang} translations of an English sentence.
Rate each translation on a scale 0.0-1.0 for three criteria:
- grammar: grammatical correctness in {lang}
- naturalness: idiomatic fluency in {lang}
- fidelity: faithfulness to the original meaning

Original English:
{original}

Translations:
{translations}

Return JSON only, no explanation, no markdown:
[
  {{"id": 1, "grammar": 0.0, "naturalness": 0.0, "fidelity": 0.0}},
  {{"id": 2, "grammar": 0.0, "naturalness": 0.0, "fidelity": 0.0}},
  {{"id": 3, "grammar": 0.0, "naturalness": 0.0, "fidelity": 0.0}},
  {{"id": 4, "grammar": 0.0, "naturalness": 0.0, "fidelity": 0.0}}
]"""


def call_sudija(prompt, max_retries=3, wait=30):
    import time
    headers = {"Authorization": f"Bearer {OLLAMA_KEY}", "Content-Type": "application/json"}
    payload = {"model": SUDIJA_MODEL, "messages": [{"role": "user", "content": prompt}],
               "stream": False, "options": {"temperature": SUDIJA_TEMP}}
    for attempt in range(max_retries):
        try:
            r = requests.post(f"{OLLAMA_URL}/api/chat", headers=headers, json=payload, timeout=120)
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except (requests.exceptions.HTTPError, requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                print(f"    [sudija greska] {e}, cekam {wait}s...", flush=True)
                time.sleep(wait)
            else:
                raise


def parse_ocjene(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r'\[.*?\]', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def db():
    return psycopg2.connect(host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
                             dbname="bb", user=os.getenv("DB_USER"),
                             password=os.getenv("DB_PASSWORD"))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--knjiga", type=int, default=22)
    ap.add_argument("--od", type=int, default=2000)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--jezici", nargs="+", default=["hr", "de"])
    ap.add_argument("--model", default="mistral-large-3:675b")
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--prompt", default="base")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    cn = db(); cur = cn.cursor()
    cur.execute("SELECT prompt_prevod_batch FROM bb_promptovi WHERE naziv=%s", (a.prompt,))
    tpl = cur.fetchone()[0]
    cur.execute("SELECT kod, naziv_en FROM bb_jezik WHERE TRIM(kod) = ANY(%s)", (a.jezici,))
    imena = {k.strip(): v for k, v in cur.fetchall()}
    rec = bb03.get_recenice(cur, a.knjiga, a.od, a.od + a.n - 1)
    cn.close()
    if len(rec) < a.n:
        sys.exit(f"Treba {a.n} recenica od pozicije {a.od}, nadjeno {len(rec)}.")
    izvor = [r[2] for r in rec[:a.n]]
    N = a.n

    random.seed(a.seed)
    shuffle_idx = list(range(N))
    random.shuffle(shuffle_idx)
    unshuffle = [0] * N
    for pos, orig in enumerate(shuffle_idx):
        unshuffle[orig] = pos

    print(f"knjiga={a.knjiga} pozicije={a.od}-{a.od+N-1} n={N}")
    print(f"model={a.model} temp={a.temp} prompt='{a.prompt}' jezici={a.jezici}")
    print(f"shuffle (pozicija_u_paketu -> originalni_indeks): {shuffle_idx}\n", flush=True)

    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer("intfloat/multilingual-e5-large")

    svi_rezultati = {}

    for kod in a.jezici:
        jn = imena[kod]
        print(f"=== {kod} ({jn}) ===", flush=True)

        original_tekst = izvor
        shuffled_tekst = [izvor[i] for i in shuffle_idx]

        print("  Runda 1 (O1, original)...", flush=True)
        O1 = bb03.prevedi_batch(original_tekst, jn, a.model, a.temp, tpl)
        print("  Runda 2 (S2, promijesano)...", flush=True)
        S2_raw = bb03.prevedi_batch(shuffled_tekst, jn, a.model, a.temp, tpl)
        print("  Runda 3 (O3, original ponovo)...", flush=True)
        O3 = bb03.prevedi_batch(original_tekst, jn, a.model, a.temp, tpl)
        print("  Runda 4 (S4, isto promijesano ponovo)...", flush=True)
        S4_raw = bb03.prevedi_batch(shuffled_tekst, jn, a.model, a.temp, tpl)

        if not all([O1, S2_raw, O3, S4_raw]):
            print(f"  PRESKACEM {kod}: poravnanje palo u jednoj od rundi.")
            continue

        S2 = [S2_raw[unshuffle[i]] for i in range(N)]
        S4 = [S4_raw[unshuffle[i]] for i in range(N)]

        po_recenici = []
        for i in range(N):
            texts = {"O1": O1[i], "S2": S2[i], "O3": O3[i], "S4": S4[i]}
            E = embedder.encode([texts["O1"], texts["S2"], texts["O3"], texts["S4"]])
            cos = lambda x, y: float(np.dot(E[x], E[y]) / (np.linalg.norm(E[x]) * np.linalg.norm(E[y])))
            kos_O = cos(0, 2)
            kos_S = cos(1, 3)
            kos_cross = np.mean([cos(0,1), cos(0,3), cos(2,1), cos(2,3)])

            sudija_prompt = SUDIJA_TPL.format(
                lang=jn, original=izvor[i],
                translations="\n".join(f"{n+1}. {texts[k]}" for n, k in enumerate(["O1","S2","O3","S4"])))
            raw = call_sudija(sudija_prompt)
            ocjene = parse_ocjene(raw)
            skorovi = {}
            if ocjene and len(ocjene) == 4:
                for n, k in enumerate(["O1", "S2", "O3", "S4"]):
                    o = ocjene[n]
                    skorovi[k] = (o["grammar"] + o["naturalness"] + o["fidelity"]) / 3
            else:
                print(f"    [{i}] sudija parse fail, raw={raw[:120]!r}")

            po_recenici.append({
                "pozicija": a.od + i, "shuffle_pos": unshuffle[i],
                "kos_O": kos_O, "kos_S": kos_S, "kos_cross": kos_cross,
                "skor": skorovi, "tekst": texts,
            })
            print(f"    [{i:2d}] kos_O={kos_O:.4f} kos_S={kos_S:.4f} kos_cross={kos_cross:.4f}"
                  + (f"  skor O1={skorovi.get('O1',0):.3f} S2={skorovi.get('S2',0):.3f} "
                     f"O3={skorovi.get('O3',0):.3f} S4={skorovi.get('S4',0):.3f}" if skorovi else ""),
                  flush=True)

        svi_rezultati[kod] = po_recenici

        kosO = [r["kos_O"] for r in po_recenici]
        kosS = [r["kos_S"] for r in po_recenici]
        kosX = [r["kos_cross"] for r in po_recenici]
        skorO = [np.mean([r["skor"]["O1"], r["skor"]["O3"]]) for r in po_recenici if r["skor"]]
        skorS = [np.mean([r["skor"]["S2"], r["skor"]["S4"]]) for r in po_recenici if r["skor"]]

        print(f"\n  --- {kod} sazetak ---")
        print(f"  kosinus O1<->O3 (bazni sum, original):   avg={np.mean(kosO):.4f}  sd={np.std(kosO):.4f}")
        print(f"  kosinus S2<->S4 (bazni sum, mesano):     avg={np.mean(kosS):.4f}  sd={np.std(kosS):.4f}")
        print(f"  kosinus unakrsno (O x S, efekat mesanja): avg={np.mean(kosX):.4f}  sd={np.std(kosX):.4f}")
        if skorO and skorS:
            print(f"  sudija prosjek O-grupa (O1,O3): avg={np.mean(skorO):.4f}  sd={np.std(skorO):.4f}")
            print(f"  sudija prosjek S-grupa (S2,S4): avg={np.mean(skorS):.4f}  sd={np.std(skorS):.4f}")
            print(f"  razlika (O - S): {np.mean(skorO) - np.mean(skorS):+.4f}")
        print("", flush=True)

    print("=== SVE GOTOVO ===")
    print("Nula upisa u bazu.")


if __name__ == "__main__":
    main()
