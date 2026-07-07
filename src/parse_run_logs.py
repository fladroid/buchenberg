import re, os, sys, json, statistics as stats

def parse_log(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    d = {"file": os.path.basename(path)}

    m = re.search(r"Knjiga\s*:\s*(\d+)", text); d["knjiga_id"] = m.group(1) if m else None
    m = re.search(r"Jezici\s*:\s*(.+)", text); d["jezici"] = m.group(1).strip() if m else None
    d["broj_jezika"] = len(d["jezici"].split()) if d["jezici"] else None

    m = re.search(r"Raspon\s*:\s*(.+)", text); d["raspon"] = m.group(1).strip() if m else None
    rm = re.search(r"(\d+)\s*[–-]\s*(\d+)", d["raspon"]) if d["raspon"] else None
    if rm:
        d["raspon_od"] = int(rm.group(1)); d["raspon_do"] = int(rm.group(2))
        d["broj_recenica"] = d["raspon_do"] - d["raspon_od"] + 1
    else:
        d["raspon_od"] = d["raspon_do"] = d["broj_recenica"] = None

    fm = re.search(r"Modeli \(faza (\d+)", text)
    d["faza"] = int(fm.group(1)) if fm else None
    d["faza_label"] = {1: "1 (baza)", 2: "2 (refine)"}.get(d["faza"], str(d["faza"]))

    m = re.search(r"Start\s*:\s*(.+)", text); d["start"] = m.group(1).strip() if m else None
    m = re.search(r"ZAVR[SŠ]ENO:\s*(.+)", text); d["end"] = m.group(1).strip() if m else None

    elapsed = re.findall(r"([\d:.]+)elapsed", text)
    d["elapsed_total_raw"] = elapsed[-1] if elapsed else None
    if d["elapsed_total_raw"]:
        parts = [float(p) for p in d["elapsed_total_raw"].split(":")]
        if len(parts) == 2: secs = parts[0]*60+parts[1]
        elif len(parts) == 3: secs = parts[0]*3600+parts[1]*60+parts[2]
        else: secs = None
        d["elapsed_total_sec"] = secs
    else:
        d["elapsed_total_sec"] = None

    if d["elapsed_total_sec"] and d["broj_recenica"]:
        d["recenica_po_minutu"] = round(d["broj_recenica"] / (d["elapsed_total_sec"]/60), 2)
    else:
        d["recenica_po_minutu"] = None

    steps = []
    for mm in re.finditer(r">>> Prevod: ([\w.:\-]+) @ temp=([\d.]+)(.*?)real\s+([0-9]+m[0-9.]+s)", text, re.DOTALL):
        model, temp, _, real = mm.groups()
        steps.append({"model": model, "temp": temp, "real": real})
    d["prevod_steps"] = steps
    m = re.search(r">>> Sudija: ([\w.:\-]+)(.*?)real\s+([0-9]+m[0-9.]+s)", text, re.DOTALL)
    d["sudija_real"] = m.group(3) if m else None
    m = re.search(r">>> Pobjednik(.*?)real\s+([0-9]+m[0-9.]+s)", text, re.DOTALL)
    d["pobjednik_real"] = m.group(2) if m else None

    lang_split = re.split(r"── Jezik: (\w+), prev_knjige_id=(\d+) ──", text)
    langs = []
    for i in range(1, len(lang_split), 3):
        lang, pk_id, block = lang_split[i], lang_split[i+1], lang_split[i+2]
        block = block.split("\nGotovo.")[0]
        finals = [float(x) for x in re.findall(r"final=([\d.]+)", block)]
        komps  = [float(x) for x in re.findall(r"komp=([\d.]+)", block)]
        sudije = [float(x) for x in re.findall(r"sudija=([\d.]+)", block)]
        upisano_m = re.search(r"Upisano:\s*(\d+)", block)
        model_counts = {}
        for mn in re.findall(r"^\s*s\d+:\s+([\w.:\-]+)\s+komp=", block, re.MULTILINE):
            model_counts[mn] = model_counts.get(mn, 0) + 1
        langs.append({
            "lang": lang, "prev_knjige_id": pk_id,
            "upisano": int(upisano_m.group(1)) if upisano_m else None,
            "avg_final": round(stats.mean(finals), 4) if finals else None,
            "avg_komp": round(stats.mean(komps), 4) if komps else None,
            "avg_sudija": round(stats.mean(sudije), 4) if sudije else None,
            "model_counts": model_counts,
        })
    d["langs"] = langs
    return d

if __name__ == "__main__":
    out = [parse_log(p) for p in sys.argv[1:]]
    print(json.dumps(out, ensure_ascii=False, indent=2))
