#!/usr/bin/env python3
"""READ-ONLY: cijena runde po jeziku (minute i pozivi po osvojenom pobjedniku).
Spaja /tmp/kask_*.tsv s bazom. Ne upisuje nista. Necommitovano (s169)."""
import csv, os, re, psycopg2
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv("/home/balsam/buchenberg/.env")

F = list(csv.DictReader(open("/tmp/kask_files.tsv"), delimiter="\t"))
R = list(csv.DictReader(open("/tmp/kask_rounds.tsv"), delimiter="\t"))
kompletan = {f["fajl"] for f in F if f["zavr"] == "4"}

opseg = {}
for f in F:
    if f["fajl"] in kompletan and f["opseg"]:
        od, do = f["opseg"].split("-")
        opseg[f["fajl"]] = (f["jezik"], int(od), int(do))

def num(x):
    try: return float(x)
    except Exception: return 0.0

sek = defaultdict(float); poz = defaultdict(int)
for r in R:
    if r["fajl"] not in opseg: continue
    jz = opseg[r["fajl"]][0]; rd = int(r["runda"])
    sek[(jz, rd)] += num(r["root"]) + num(r["prevod"]) + num(r["sudija"]) + num(r["pobjednik"])
    if r["gate"]: poz[(jz, rd)] += int(r["gate"])

cn = psycopg2.connect(host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
                      dbname="bb", user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"))
cur = cn.cursor()
pob = defaultdict(int); rec = defaultdict(int)
for fajl, (jz, od, do) in opseg.items():
    cur.execute("""SELECT CASE WHEN p.faza_id=1 THEN 0 ELSE k.runda END AS r, COUNT(*)
                   FROM v_pobjednici_full p JOIN bb_prevodi_knjige k ON k.id=p.prevodi_knjige_id
                   WHERE p.knjiga_id=12 AND p.jezik_kod=%s
                     AND p.recenica_pozicija BETWEEN %s AND %s GROUP BY 1""", (jz, od, do))
    for r, n in cur.fetchall():
        pob[(jz, r)] += n
    rec[jz] += do - od + 1
cur.close(); cn.close()

print(f"{'jz':<4}{'rec':>6}{'runda':>7}{'poziva':>8}{'pobjed':>8}{'minuta':>8}{'min/pob':>9}{'poz/pob':>9}")
print("-" * 60)
for jz in sorted(rec):
    for rd in sorted({r for (j, r) in list(sek) + list(pob) if j == jz}):
        p = pob[(jz, rd)]; c = poz[(jz, rd)]; m = sek[(jz, rd)] / 60
        mp = f"{m/p:.2f}" if p else "-"
        cp = f"{c/p:.2f}" if p and c else "-"
        print(f"{jz:<4}{rec[jz]:>6}{rd:>7}{c if c else '-':>8}{p:>8}{m:>8.1f}{mp:>9}{cp:>9}")
    print()
