#!/usr/bin/env python3
"""READ-ONLY parser kaskada4/5 logova. Ne dira bazu. Necommitovano (s169)."""
import re, sys, os
from datetime import datetime

TS = "%a %b %d %H:%M:%S UTC %Y"

def pts(s):
    try: return datetime.strptime(s.strip(), TS)
    except Exception: return None

def rsec(s):
    m = re.match(r"(?:(\d+)m)?([\d.]+)s", s.strip())
    return int(m.group(1) or 0)*60 + float(m.group(2)) if m else None

def parse(path):
    f = {"fajl": os.path.basename(path), "jezik": "", "opseg": "", "prag": "",
         "rundi": "", "start": None, "kraj": None, "proc": "", "load": "",
         "ram": "", "zavr": 0, "trace": 0, "tmo": 0, "recenica": ""}
    R = {}
    lab, rnd, expect = None, 0, None
    for ln in open(path, encoding="utf-8", errors="replace"):
        s = ln.rstrip("\n")
        if expect == "proc" and "bb_03 procesa" in s:
            f["proc"] = s.split(":")[-1].strip(); expect = "load"; continue
        if expect == "load" and "load average" in s:
            f["load"] = s.split(":")[-1].strip().split(",")[0]; expect = "ram"; continue
        if expect == "ram" and "RAM:" in s:
            f["ram"] = s.split(":")[-1].strip().split(" ")[0]; expect = None; continue
        if ">>> OKOLINA (start)" in s:
            f["start"] = pts(s.split("):", 1)[1]); expect = "proc"; continue
        if ">>> OKOLINA (kraj)" in s:
            f["kraj"] = pts(s.split("):", 1)[1]); expect = None; continue
        if ">>> PARAMETRI" in s:
            for k, pat in (("jezik", r"jezici='([^']+)'"), ("opseg", r"opseg=(\S+)"),
                           ("prag", r"prag=(\S+)"), ("rundi", r"rundi=(\S+)")):
                m = re.search(pat, s)
                if m: f[k] = m.group(1)
            continue
        if "Rečenica za obradu" in s and not f["recenica"]:
            m = re.search(r": (\d+)", s)
            if m: f["recenica"] = m.group(1)
            continue
        if ">>> KORAK 1: root" in s: lab, rnd = "root", 0; continue
        if ">>> KORAK 1: sudija" in s: lab = "sudija"; continue
        if ">>> KORAK 1: pobjednik" in s: lab = "pobjednik"; continue
        m = re.search(r"\| runda=(\d+) \| prag", s)
        if m: rnd = int(m.group(1)); continue
        if ">>> Prevod [self-refine]" in s: lab = "prevod"; continue
        if s.startswith(">>> Sudija:"): lab = "sudija"; continue
        if s.startswith(">>> Pobjednik (argmax"): lab = "pobjednik"; continue
        m = re.search(r"ispod praga ([\d.]+): (\d+) \(preskoceno (\d+)\)", s)
        if m:
            R.setdefault(rnd, {})["gate"] = int(m.group(2))
            R[rnd]["presk"] = int(m.group(3)); continue
        if s.startswith("real"):
            v = rsec(s.split("\t")[-1])
            if v is not None and lab: R.setdefault(rnd, {})[lab] = v
            continue
        if "ZAVRŠENO" in s: f["zavr"] += 1
        if "Traceback" in s: f["trace"] += 1
        if re.search(r"imeout|imedOut", s): f["tmo"] += 1
    return f, R

files, rows = [], []
for p in sys.argv[1:]:
    if not os.path.exists(p): print(f"NEMA: {p}", file=sys.stderr); continue
    f, R = parse(p)
    files.append(f)
    for r in sorted(R):
        d = R[r]
        rows.append({"fajl": f["fajl"], "jezik": f["jezik"], "opseg": f["opseg"], "runda": r,
                     "gate": d.get("gate", ""), "presk": d.get("presk", ""),
                     "root": d.get("root", ""), "prevod": d.get("prevod", ""),
                     "sudija": d.get("sudija", ""), "pobjednik": d.get("pobjednik", "")})

def dump(path, data, cols):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(cols) + "\n")
        for d in data:
            fh.write("\t".join(str(d.get(c, "") if d.get(c) is not None else "") for c in cols) + "\n")

dump("/tmp/kask_files.tsv", files,
     ["fajl","jezik","opseg","prag","rundi","recenica","start","kraj","proc","load","ram","zavr","trace","tmo"])
dump("/tmp/kask_rounds.tsv", rows,
     ["fajl","jezik","opseg","runda","gate","presk","root","prevod","sudija","pobjednik"])
print(f"logova: {len(files)}  redova rundi: {len(rows)}")
print(f"bez 4 ZAVRSENO: {[f['fajl'] for f in files if f['zavr'] != 4]}")
print(f"s Tracebackom: {[f['fajl'] for f in files if f['trace']]}")
print(f"s timeoutom:   {[(f['fajl'], f['tmo']) for f in files if f['tmo']]}")
