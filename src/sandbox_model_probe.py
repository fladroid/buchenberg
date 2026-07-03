#!/usr/bin/env python3
"""
sandbox_model_probe.py — read-only sonda ponašanja prevodilačkih modela.

Svrha: kad Ollama povuče model (ili kad želimo isprobati novi), pustiti kandidata
kroz istu prompt-mašineriju koju koristi bb_03_prevod.py i izmjeriti PONAŠANJE
(ne kvalitet — kvalitet ide kroz pravi bb_03+bb_08 na malom opsegu poslije).

IZOLACIJA: ne dira bazu, bb_modeli, pipeline ni produkciju. Samo Ollama /api/chat.
Test rečenice su hardkodovane (nema ni čitanja baze).

Baseline modeli (gemma3, ministral) služe kao ETALON — novi kandidati se čitaju
naspram njih, ne u vakuumu.

Upotreba:
  venv/bin/python src/sandbox_model_probe.py
  venv/bin/python src/sandbox_model_probe.py --models "gemma3:12b gpt-oss:20b" --jezik hr
  venv/bin/python src/sandbox_model_probe.py --no-think     # testira gasi li se thinking
"""
import os, sys, time, json, argparse
import requests
from dotenv import load_dotenv
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY = os.getenv("OLLAMA_API_KEY", "")

# Test set: 5 EN rečenica, raznolike (kratka / duga / dijalog / vlastito ime / kratka fraza)
TEST_EN = [
    "The moor was a place of mystery.",
    "It was one of those cases in which the art of the reasoner should be used rather for the sifting of details than for the acquiring of fresh evidence.",
    '"Come, Watson, come!" he cried. "The game is afoot."',
    "Sir Charles Baskerville had left the house for his usual evening walk.",
    "Nothing stirred in the vast expanse.",
]

LANG_NAZIV = {"hr": "Croatian", "de": "German", "it": "Italian", "sr": "Serbian",
              "bs": "Bosnian", "sl": "Slovenian", "mk": "Macedonian", "bg": "Bulgarian",
              "nl": "Dutch", "af": "Afrikaans", "fr": "French", "es": "Spanish",
              "pt": "Portuguese", "ro": "Romanian"}


def ollama_raw(model, temperature, messages, think=None, wait=15, max_retries=2):
    """Kao ollama_chat u bb_03, ali vraća CIJELI json (za thinking/eval_count/duration)."""
    headers = {"Content-Type": "application/json"}
    if OLLAMA_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_KEY}"
    payload = {"model": model, "messages": messages, "stream": False,
               "options": {"temperature": temperature}}
    if think is not None:
        payload["think"] = think
    for attempt in range(max_retries):
        try:
            r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, headers=headers, timeout=180)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(wait)
            else:
                return {"_error": str(e)}


def prompt_single(tekst, jezik_naziv):
    return (f"Translate the following English text to {jezik_naziv}.\n"
            f"Output only the translation, nothing else.\n\n{tekst}")

def prompt_batch(tekstovi, jezik_naziv):
    numerirani = "\n".join(f"{i+1}. {t}" for i, t in enumerate(tekstovi))
    return (f"Translate the following English texts to {jezik_naziv}.\n"
            f"Output ONLY the translations as a numbered list, one per line, nothing else.\n\n{numerirani}")

def prompt_back(tekst, jezik_naziv):
    return (f"Translate the following {jezik_naziv} text to English.\n"
            f"Output only the translation, nothing else.\n\n{tekst}")


def parse_batch(odgovor, n):
    linije = [l.strip() for l in odgovor.splitlines() if l.strip()]
    prevodi = []
    for l in linije:
        if l and l[0].isdigit() and ". " in l:
            prevodi.append(l.split(". ", 1)[1].strip())
        else:
            prevodi.append(l)
    return prevodi


def probe(model, jezik, think_flag):
    jn = LANG_NAZIV.get(jezik, jezik)
    R = {"model": model}

    # ── 1+2. Čistoća + trošak (single, temp 0.1) ───────────────────────────
    t0 = time.time()
    j = ollama_raw(model, 0.1, [{"role": "user", "content": prompt_single(TEST_EN[0], jn)}], think=think_flag)
    dt = time.time() - t0
    if "_error" in j:
        R["status"] = f"ERROR: {j['_error'][:60]}"
        return R
    msg = j.get("message", {})
    content = (msg.get("content") or "").strip()
    thinking = (msg.get("thinking") or "")
    R["status"]     = "ok"
    R["prevod"]     = content[:60]
    R["has_think"]  = "DA" if thinking else "ne"
    R["think_len"]  = len(thinking)
    R["eval_cnt"]   = j.get("eval_count", 0)
    R["sec"]        = round(dt, 1)
    # preambula/markdown detekcija (prljav izlaz)
    prljav = []
    if content.startswith(("Here", "The translation", "Sure", "```", "**")):
        prljav.append("preambula")
    if "\n" in content:
        prljav.append("visered")
    R["cistoca"] = "čist" if not prljav else "+".join(prljav)

    # ── 3. Temperatura (0.1 vs 0.8, ista rečenica) ─────────────────────────
    ja = ollama_raw(model, 0.1, [{"role": "user", "content": prompt_single(TEST_EN[3], jn)}], think=think_flag)
    jb = ollama_raw(model, 0.8, [{"role": "user", "content": prompt_single(TEST_EN[3], jn)}], think=think_flag)
    ca = (ja.get("message", {}).get("content") or "").strip()
    cb = (jb.get("message", {}).get("content") or "").strip()
    R["temp_react"] = "razlika" if ca != cb else "identično"

    # ── 4. Batch preživljavanje (5 odjednom) ───────────────────────────────
    jbatch = ollama_raw(model, 0.1, [{"role": "user", "content": prompt_batch(TEST_EN, jn)}], think=think_flag)
    cbatch = (jbatch.get("message", {}).get("content") or "").strip()
    parsed = parse_batch(cbatch, len(TEST_EN))
    R["batch"] = f"{len(parsed)}/{len(TEST_EN)}" + ("" if len(parsed) == len(TEST_EN) else " ✗")

    # ── 5. Round-trip (EN→L→EN, prva rečenica) ─────────────────────────────
    jback = ollama_raw(model, 0.1, [{"role": "user", "content": prompt_back(content, jn)}], think=think_flag)
    R["roundtrip_en"] = ((jback.get("message", {}).get("content") or "").strip())[:60]

    return R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="gemma3:12b ministral-3:14b gpt-oss:20b nemotron-3-nano:30b")
    ap.add_argument("--jezik", default="hr")
    ap.add_argument("--no-think", action="store_true", help="Šalje think:false (testira poštuje li model)")
    args = ap.parse_args()
    think_flag = False if args.no_think else None

    models = args.models.split()
    print(f"\n{'='*78}")
    print(f"  SANDBOX MODEL PROBE — jezik={args.jezik}  think_flag={think_flag}")
    print(f"  baseline (etalon) prvi; kandidati ispod")
    print(f"{'='*78}\n")

    rezultati = []
    for m in models:
        print(f"  → {m} ...", flush=True)
        rezultati.append(probe(m, args.jezik, think_flag))

    # tabela
    print(f"\n{'─'*78}")
    hdr = f"{'model':<22}{'stat':<6}{'think':<7}{'evalC':<7}{'sec':<6}{'čistoća':<12}{'temp':<10}{'batch':<8}"
    print(hdr)
    print(f"{'─'*78}")
    for R in rezultati:
        if R.get("status", "").startswith("ERROR"):
            print(f"{R['model']:<22}{R['status']}")
            continue
        print(f"{R['model']:<22}{R.get('status','?'):<6}{R.get('has_think','?'):<7}"
              f"{R.get('eval_cnt',0):<7}{R.get('sec',0):<6}{R.get('cistoca','?'):<12}"
              f"{R.get('temp_react','?'):<10}{R.get('batch','?'):<8}")
    print(f"{'─'*78}\n")

    # detalji (prevod + round-trip po modelu)
    for R in rezultati:
        if R.get("status") == "ok":
            print(f"  {R['model']}")
            print(f"     prevod:     {R.get('prevod','')}")
            print(f"     back→EN:    {R.get('roundtrip_en','')}")
            print(f"     think_len:  {R.get('think_len',0)} znakova")
            print()

if __name__ == "__main__":
    main()
