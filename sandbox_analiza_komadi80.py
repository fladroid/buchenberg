"""
sandbox_analiza_komadi80.py — READ-ONLY analiza kaskada13 logova.
Poredi tri kruga: chunk50/4radnika (round1), chunk60/2radnika (round3),
chunk80/2radnika (round4, nova sesija). Ne dira bazu.
"""
import re, sys, glob
from datetime import datetime
from collections import defaultdict

FMT = "%a %b %d %H:%M:%S UTC %Y"

def parse_log(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        content = f.read()
    content = re.sub(r'\x1b\[[0-9;]*m', '', content)

    d = {'file': path}

    m = re.search(r">>> PARAMETRI: knjiga=(\d+) jezici='(\w+)' opseg=(\d+)-(\d+) prag=([\d.]+)", content)
    if m:
        d['jezik'] = m.group(2)
        d['od'] = int(m.group(3)); d['do'] = int(m.group(4))
        d['n'] = d['do'] - d['od'] + 1
    else:
        d['jezik'] = '???'; d['n'] = None

    ms = re.search(r">>> OKOLINA \(start\): (.+)", content)
    me = re.search(r">>> ZAVRSENO \(prag=[\d.]+, X=\d+\): (.+)", content)
    d['elapsed_min'] = None
    if ms and me:
        try:
            t0 = datetime.strptime(ms.group(1).strip(), FMT)
            t1 = datetime.strptime(me.group(1).strip(), FMT)
            d['elapsed_min'] = round((t1 - t0).total_seconds() / 60, 2)
        except Exception:
            pass

    m = re.search(r">>> SAZETAK: blok A=(\d+)/(\d+) \(([\w-]+)\) \| blok B=(\d+)/(\d+) \(([\w-]+)\)", content)
    if m:
        d['blokA_krugovi'] = int(m.group(1)); d['blokA_izlaz'] = m.group(3)
        d['blokB_krugovi'] = int(m.group(4)); d['blokB_status'] = m.group(6)
    else:
        d['blokA_krugovi'] = None; d['blokB_krugovi'] = None; d['blokB_status'] = '???'

    m = re.search(r">>> SAZETAK: izvrseno faza ukupno=(\d+)", content)
    d['faza_ukupno'] = int(m.group(1)) if m else None

    m = re.search(r">>> SAZETAK: ispod praga na kraju=(\d+) \| iznad=(\d+)% \| zbir=([\d.]+)/(\d+)", content)
    if m:
        d['ispod_kraj'] = int(m.group(1)); d['iznad_pct'] = int(m.group(2))
        d['zbir'] = float(m.group(3))
    else:
        d['iznad_pct'] = None

    mroot = re.search(r">>> KORAK 1: root.*?\n(.*?)>>> KORAK 1: sudija", content, re.DOTALL)
    d['root_min'] = None
    if mroot:
        rmatches = re.findall(r'real\s+(\d+)m([\d.]+)s', mroot.group(1))
        if rmatches:
            d['root_min'] = round(sum(int(mm) + float(ss)/60 for mm, ss in rmatches), 2)

    d['tracebacks'] = content.count('Traceback')
    d['timeouts'] = len(re.findall(r'Read timed out|ReadTimeout', content))
    d['server_errors'] = len(re.findall(r'Server Error', content))

    empty_A = len(re.findall(r'BLOK A KRUG \d+ FAZA \d+: ispod praga \d+ \(prebacila \+0\)', content))
    total_A_faze = len(re.findall(r'BLOK A KRUG \d+ FAZA \d+: ispod praga', content))
    d['blokA_empty'] = empty_A
    d['blokA_total_faze'] = total_A_faze

    return d


def aggregate(label, files):
    print(f"\n{'='*90}\n{label}  ({len(files)} fajlova)\n{'='*90}")
    rows = [parse_log(f) for f in files]

    errs = [r for r in rows if r['tracebacks'] or r['timeouts'] or r['server_errors']]
    if errs:
        print(f"  GREŠKE u {len(errs)} fajlova:")
        for r in errs:
            print(f"     {r['file']}: traceback={r['tracebacks']} timeout={r['timeouts']} server_err={r['server_errors']}")
    else:
        print("  Nula grešaka (Traceback/timeout/500) u svim fajlovima.")

    by_lang = defaultdict(list)
    for r in rows:
        by_lang[r['jezik']].append(r)

    print(f"\n  {'jezik':6s} {'n_fajl':7s} {'elapsed(min)':13s} {'root(min)':10s} {'faza_uk':8s} {'blokA_prazno%':14s} {'blokB_pokr':11s} {'iznad_prag%':12s}")
    for jz in sorted(by_lang):
        rs = by_lang[jz]
        el = [r['elapsed_min'] for r in rs if r['elapsed_min'] is not None]
        rt = [r['root_min'] for r in rs if r['root_min'] is not None]
        fz = [r['faza_ukupno'] for r in rs if r['faza_ukupno'] is not None]
        ip = [r['iznad_pct'] for r in rs if r['iznad_pct'] is not None]
        empty_tot = sum(r['blokA_empty'] for r in rs)
        total_tot = sum(r['blokA_total_faze'] for r in rs)
        blokB_pokr = sum(1 for r in rs if r['blokB_status'] not in ('nije-pokrenut', '???'))
        print(f"  {jz:6s} {len(rs):<7d} {sum(el)/len(el):<13.2f} {sum(rt)/len(rt):<10.2f} "
              f"{sum(fz)/len(fz):<8.2f} {100*empty_tot/total_tot if total_tot else 0:<14.1f} "
              f"{blokB_pokr}/{len(rs):<9} {sum(ip)/len(ip):<12.1f}")

    el_all = [r['elapsed_min'] for r in rows if r['elapsed_min'] is not None]
    rt_all = [r['root_min'] for r in rows if r['root_min'] is not None]
    fz_all = [r['faza_ukupno'] for r in rows if r['faza_ukupno'] is not None]
    ip_all = [r['iznad_pct'] for r in rows if r['iznad_pct'] is not None]
    empty_all = sum(r['blokA_empty'] for r in rows)
    total_all = sum(r['blokA_total_faze'] for r in rows)
    blokB_all = sum(1 for r in rows if r['blokB_status'] not in ('nije-pokrenut', '???'))
    print(f"\n  {'UKUPNO':6s} {len(rows):<7d} {sum(el_all)/len(el_all):<13.2f} {sum(rt_all)/len(rt_all):<10.2f} "
          f"{sum(fz_all)/len(fz_all):<8.2f} {100*empty_all/total_all if total_all else 0:<14.1f} "
          f"{blokB_all}/{len(rows):<9} {sum(ip_all)/len(ip_all):<12.1f}")
    return rows


if __name__ == '__main__':
    r1 = sorted(glob.glob('logs/parapoc_k12_*.log'))
    r1 = [f for f in r1 if re.search(r'_(es|fr|nl|bg|mk|sl)_', f)]
    r3 = sorted(glob.glob('logs/parapoc34_k12_*.log'))
    r4 = sorted(glob.glob('logs/parapoc4_k12_*.log'))

    aggregate("KRUG 1 — komad 50, 4 radnika, opseg 6001-6400 (6 jezika)", r1)
    aggregate("KRUG 3 — komad 60, 2 radnika, opseg 6801-7220 (6 jezika)", r3)
    aggregate("KRUG 4 — komad 80, 2 radnika, opseg 7221-7620 (6 jezika)", r4)
