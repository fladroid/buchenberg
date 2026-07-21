import os, sys
from collections import defaultdict
sys.path.insert(0, '/home/balsam/buchenberg/src')
from dotenv import load_dotenv
load_dotenv('/home/balsam/buchenberg/.env')
import psycopg2

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
    dbname="bb", user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD")
)
cur = conn.cursor()
cur.execute("""
    SELECT recenica_pozicija, jezik_kod, faza_id, finalni_score
    FROM v_prevodi_full
    WHERE knjiga_id = 20 AND recenica_pozicija BETWEEN 2801 AND 3400
      AND jezik_kod IN ('hr','de','it','sr')
      AND faza_id IN (1,4,5,6)
""")
rows = cur.fetchall()
conn.close()

data = defaultdict(lambda: defaultdict(list))
for pos, jezik, faza, score in rows:
    data[(pos, jezik)][faza].append(float(score))

BLOCK_ORDER = {
    (2801,2900): [4,5,6],
    (2901,3000): [4,6,5],
    (3001,3100): [5,4,6],
    (3101,3200): [5,6,4],
    (3201,3300): [6,4,5],
    (3301,3400): [6,5,4],
}
def block_of(pos):
    for (lo,hi), order in BLOCK_ORDER.items():
        if lo <= pos <= hi:
            return (lo,hi), order
    return None, None

# step_stats[step_idx] -> list of (gate_open, refine_won, delta)
step_stats = defaultdict(list)
faza_stats = defaultdict(list)
faza_at_step = defaultdict(list)  # (faza, step_idx) -> list
block_final = defaultdict(list)   # block -> list of final_delta
lang_final = defaultdict(list)
n_missing_seed = 0
n_total = 0

for (pos, jezik), fdict in data.items():
    blk, order = block_of(pos)
    if blk is None or 1 not in fdict:
        n_missing_seed += 1
        continue
    n_total += 1
    seed0 = max(fdict[1])
    seed = seed0
    for step_idx, faza in enumerate(order, start=1):
        cands = fdict.get(faza, [])
        gate_open = len(cands) > 0
        if gate_open:
            best_cand = max(cands)
            new_seed = max(seed, best_cand)
            refine_won = best_cand > seed
            delta = new_seed - seed
        else:
            new_seed = seed
            refine_won = False
            delta = 0.0
        step_stats[step_idx].append((gate_open, refine_won, delta))
        faza_stats[faza].append((gate_open, refine_won, delta))
        faza_at_step[(faza, step_idx)].append((gate_open, refine_won, delta))
        seed = new_seed
    final_delta = seed - seed0
    block_final[blk].append(final_delta)
    lang_final[jezik].append(final_delta)

def summarize(label, items):
    n = len(items)
    if n == 0:
        print(f"  {label}: n=0")
        return
    n_open = sum(1 for g,w,d in items if g)
    n_win = sum(1 for g,w,d in items if w)
    avg_delta_all = sum(d for g,w,d in items) / n
    avg_delta_open = (sum(d for g,w,d in items if g) / n_open) if n_open else 0.0
    print(f"  {label}: n={n}  gate_open={n_open} ({100*n_open/n:.1f}%)  "
          f"win={n_win} ({100*n_win/n_open:.1f}% od otvorenih)  "
          f"avg_delta(svi)={avg_delta_all:+.4f}  avg_delta(otvoreni)={avg_delta_open:+.4f}")

print(f"\n=== Ukupno rečenica-jezik parova: {n_total} (bez seed-a: {n_missing_seed}) ===\n")

print("--- Po POZICIJI U LANCU (1./2./3. korak, nezavisno od koje faze) ---")
for step_idx in sorted(step_stats):
    summarize(f"korak {step_idx}", step_stats[step_idx])

print("\n--- Po KONKRETNOJ FAZI (nezavisno od pozicije u lancu) ---")
NAZIVI = {4:"refine-gated", 5:"refine-lenient-gated", 6:"refine-strict-gated"}
for faza in sorted(faza_stats):
    summarize(f"faza {faza} ({NAZIVI[faza]})", faza_stats[faza])

print("\n--- Faza x pozicija (kontrola za oboje, 2 bloka po ćeliji) ---")
for faza in sorted(NAZIVI):
    for step_idx in (1,2,3):
        items = faza_at_step.get((faza, step_idx), [])
        summarize(f"faza {faza} @ korak {step_idx}", items)

print("\n--- Po BLOKU (redoslijedu) — prosječan finalni pomak seed0->kraj lanca ---")
for blk, order in BLOCK_ORDER.items():
    vals = block_final.get(blk, [])
    n = len(vals)
    avg = sum(vals)/n if n else 0.0
    print(f"  {blk[0]}-{blk[1]} redoslijed {order}: n={n}  avg_final_delta={avg:+.4f}")

print("\n--- Po JEZIKU — prosječan finalni pomak ---")
for jezik, vals in lang_final.items():
    n = len(vals)
    avg = sum(vals)/n if n else 0.0
    print(f"  {jezik}: n={n}  avg_final_delta={avg:+.4f}")

print("\nGotovo.")
