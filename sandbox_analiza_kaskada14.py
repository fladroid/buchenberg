"""
sandbox_analiza_kaskada14.py — READ-ONLY analiza kaskada14 logova (s177).
Fokus: efekat original/mesano po izvrsenju (faza x runda x redoslijed).
"""
import re, sys, glob
from datetime import datetime
from collections import defaultdict

FMT = "%a %b %d %H:%M:%S UTC %Y"

EXEC_RE = re.compile(
    r">>> (BLOK [AB](?: KRUG \d+)?) FAZA (\d+) runda=(\d+) \((\w+)\): "
    r"ispod praga (\d+) \(prebacila ([+-]\d+)\) \| zbir ([\d.]+)/(\d+) dodala ([+-][\d.]+) \| ([+-][\d.]+)% n"
)

def parse_log(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        content = f.read()
    content = re.sub(r'\x1b\[[0-9;]*m', '', content)

    d = {'file': path}
    m = re.search(r">>> PARAMETRI: knjiga=(\d+) jezici='(\w+)' opseg=(\d+)-(\d+) prag=([\d.]+)", content)
    d['jezik'] = m.group(2) if m else '???'
    d['od'] = int(m.group(3)) if m else None
    d['do'] = int(m.group(4)) if m else None
    d['n'] = (d['do'] - d['od'] + 1) if m else None

    ms = re.search(r">>> OKOLINA \(start\): (.+)", content)
    me = re.search(r">>> OKOLINA \(kraj\): (.+)", content)
    d['elapsed_min'] = None
    if ms and me:
        try:
            t0 = datetime.strptime(ms.group(1).strip(), FMT)
            t1 = datetime.strptime(me.group(1).strip(), FMT)
            d['elapsed_min'] = round((t1 - t0).total_seconds() / 60, 2)
        except Exception:
            pass

    m = re.search(r">>> ZBIR root: ([\d.]+)/(\d+) \| ispod praga: (\d+) \| iznad: (\d+)%", content)
    if m:
        d['root_zbir'] = float(m.group(1)); d['root_ispod'] = int(m.group(3)); d['root_iznad_pct'] = int(m.group(4))

    d['izvrsenja'] = []
    for em in EXEC_RE.finditer(content):
        d['izvrsenja'].append({
            'blok': em.group(1), 'faza': int(em.group(2)), 'runda': int(em.group(3)),
            'redoslijed': em.group(4), 'ispod_posle': int(em.group(5)), 'prebacila': int(em.group(6)),
            'zbir_posle': float(em.group(7)), 'dodala': float(em.group(9)), 'pct_dodala': float(em.group(10)),
        })

    m = re.search(r">>> SAZETAK: blok A=([\d/]+) \(([^)]+)\) \| blok B=([\d/]+) \(([^)]+)\)", content)
    d['blokB_status'] = m.group(4) if m else '???'
    m = re.search(r">>> SAZETAK: izvrseno faza ukupno=(\d+)", content)
    d['faza_ukupno'] = int(m.group(1)) if m else None
    m = re.search(r">>> SAZETAK: ispod praga na kraju=(\d+) \| iznad=(\d+)% \| zbir=([\d.]+)/(\d+)", content)
    if m:
        d['ispod_kraj'] = int(m.group(1)); d['iznad_kraj_pct'] = int(m.group(2)); d['zbir_kraj'] = float(m.group(3))

    d['tracebacks'] = content.count('Traceback')
    d['timeouts'] = len(re.findall(r'Read timed out|ReadTimeout', content))
    d['server_errors'] = len(re.findall(r'Server Error', content))
    return d


def main():
    files = sorted(glob.glob('logs/parapoc5_k12_*.log'))
    rows = [parse_log(f) for f in files]

    print(f"{'='*100}\nKASKADA14 (s177) — {len(rows)} fajlova\n{'='*100}")

    errs = [r for r in rows if r['tracebacks'] or r['timeouts'] or r['server_errors']]
    if errs:
        print(f"GRESKE u {len(errs)} fajlova:")
        for r in errs:
            print(f"   {r['file']}: traceback={r['tracebacks']} timeout={r['timeouts']} server_err={r['server_errors']}")
    else:
        print("Nula gresaka (Traceback/timeout/500) u svim fajlovima.")

    print(f"\n{'jezik':6s} {'opseg':13s} {'root_iznad%':11s} {'elapsed(min)':12s} {'blokB':16s} {'faza_uk':8s} {'ispod_kraj':10s} {'iznad_kraj%':11s}")
    for r in rows:
        print(f"{r['jezik']:6s} {str(r['od'])+'-'+str(r['do']):13s} {r['root_iznad_pct']:<11d} {r['elapsed_min']:<12.2f} "
              f"{r['blokB_status']:16s} {r['faza_ukupno']:<8d} {r['ispod_kraj']:<10d} {r['iznad_kraj_pct']:<11d}")

    # Po jeziku: prosjek root i finalnog iznad%
    by_lang = defaultdict(list)
    for r in rows:
        by_lang[r['jezik']].append(r)
    print(f"\n--- Prosjek po jeziku ---")
    for jz in sorted(by_lang):
        rs = by_lang[jz]
        print(f"  {jz}: root_iznad%={sum(r['root_iznad_pct'] for r in rs)/len(rs):.1f}  "
              f"finalno_iznad%={sum(r['iznad_kraj_pct'] for r in rs)/len(rs):.1f}  "
              f"elapsed={sum(r['elapsed_min'] for r in rs)/len(rs):.2f}min  "
              f"blokB_pokrenut={sum(1 for r in rs if 'nije-pokrenut' not in r['blokB_status'])}/{len(rs)}")

    # Po IZVRSENJU (blok, faza, runda, redoslijed) -- agregat "dodala" i "prebacila" preko svih fajlova/jezika
    print(f"\n--- Efekat po slotu izvrsenja (agregat svih {len(rows)} fajlova, oba jezika) ---")
    slot_stats = defaultdict(list)
    for r in rows:
        for e in r['izvrsenja']:
            key = (e['blok'], e['faza'], e['runda'], e['redoslijed'])
            slot_stats[key].append(e)

    print(f"{'blok':16s} {'faza':5s} {'runda':6s} {'redoslijed':11s} {'n':3s} {'prosj_prebacila':16s} {'prosj_dodala':13s} {'prosj_%dodala':13s}")
    for key in sorted(slot_stats.keys(), key=lambda k: (k[0], k[1], k[2])):
        es = slot_stats[key]
        avg_preb = sum(e['prebacila'] for e in es) / len(es)
        avg_dod = sum(e['dodala'] for e in es) / len(es)
        avg_pct = sum(e['pct_dodala'] for e in es) / len(es)
        print(f"{key[0]:16s} {key[1]:<5d} {key[2]:<6d} {key[3]:11s} {len(es):<3d} {avg_preb:<16.2f} {avg_dod:<13.4f} {avg_pct:<13.3f}")

    # original vs mesano, agregatno preko SVIH slotova (napomena: order-confound unutar k14, original UVIJEK prvi)
    orig_all = [e for r in rows for e in r['izvrsenja'] if e['redoslijed'] == 'original']
    mes_all  = [e for r in rows for e in r['izvrsenja'] if e['redoslijed'] == 'mesano']
    print(f"\n--- SIROVO original vs mesano (SVI slotovi zajedno, n={len(orig_all)} vs {len(mes_all)}) ---")
    print(f"  original: prosj_prebacila={sum(e['prebacila'] for e in orig_all)/len(orig_all):.3f}  prosj_dodala={sum(e['dodala'] for e in orig_all)/len(orig_all):.4f}")
    print(f"  mesano:   prosj_prebacila={sum(e['prebacila'] for e in mes_all)/len(mes_all):.3f}  prosj_dodala={sum(e['dodala'] for e in mes_all)/len(mes_all):.4f}")
    print("  NAPOMENA: u kaskada14 original UVIJEK izvrsava prije mesano u istom krugu -> ovo poredjenje")
    print("  je nuzno pobrkano sa redoslijedom izvrsavanja (drugi u nizu ima manji preostali bazen).")
    print("  kaskada15 (mesano prvo) postoji bas zato da se ovaj confound razdvoji.")


if __name__ == '__main__':
    main()
