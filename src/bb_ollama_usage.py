"""
bb_ollama_usage.py
Ollama Cloud potrosnja (session + sedmicno) preko nezvanicnog /api/usage
endpointa — isti API kljuc kao za prevod (Bearer auth), ne login/lozinka.
Cuva stanje u schedulogs/ollama_stanje.json da bi se mogla racunati delta
izmedju poziva (koliko je potroseno OD PROSLOG upita).

NAPOMENA: endpoint nije zvanicno dokumentovan (vidi GitHub issues
ollama/ollama #15132, #15663, #16448 — sva tri traze bas ovo, sva tri jos
otvorena/nerijesena u avgustu 2026). Moze se promijeniti ili nestati bez
najave — provjeriti ako ovaj skript pocne vracati greske.

Upotreba:
    venv/bin/python src/bb_ollama_usage.py             # pun izvjestaj
    venv/bin/python src/bb_ollama_usage.py --kratko     # jedna linija (za scheduler/health_check)
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

BUCH_HOME = Path(__file__).resolve().parent.parent
load_dotenv(BUCH_HOME / ".env")

USAGE_URL = "https://ollama.com/api/usage"
STANJE_PATH = BUCH_HOME / "schedulogs" / "ollama_stanje.json"


def fetch_usage():
    """Vraca (dict, greska). Tacno jedno od dvoje je None. Nikad ne baca izuzetak."""
    api_key = os.getenv("OLLAMA_API_KEY")
    if not api_key:
        return None, "OLLAMA_API_KEY nije postavljen u .env"
    try:
        r = requests.get(
            USAGE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)


def load_stanje():
    if STANJE_PATH.exists():
        try:
            return json.loads(STANJE_PATH.read_text())
        except Exception:
            return None
    return None


def save_stanje(data):
    STANJE_PATH.parent.mkdir(parents=True, exist_ok=True)
    limits = data.get("limits", {})
    session = limits.get("session", {})
    weekly = limits.get("weekly", {})
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_usage": session.get("usage"),
        "weekly_usage": weekly.get("usage"),
        "weekly_models": {m["name"]: m["request_count"] for m in weekly.get("models", [])},
    }
    STANJE_PATH.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False))
    return snapshot


def pct(x):
    return f"{x*100:.1f}%" if x is not None else "n/a"


def delta_pct_str(prev_val, curr_val):
    """Formatira deltu izmedju dvije procentne vrijednosti (0..1) u procentnim
    poenima. Prazan string ako nema baze za poredjenje. Detektuje ocigledan
    reset (nagli pad) i to javlja umjesto besmislene negativne delte."""
    if prev_val is None or curr_val is None:
        return ""
    razlika_pp = (curr_val - prev_val) * 100
    if razlika_pp < -1:
        return " (izgleda resetovano od poslednje provjere)"
    return f" ({razlika_pp:+.1f}pp od poslednje provjere)"


def main():
    parser = argparse.ArgumentParser(
        description="Ollama Cloud potrosnja (session + sedmicno), sa deltom od poslednje provjere."
    )
    parser.add_argument("--kratko", action="store_true",
                         help="jedna linija, za scheduler/health_check")
    args = parser.parse_args()

    data, greska = fetch_usage()
    if greska:
        print(f"Ollama usage GRESKA — {greska}")
        sys.exit(1)

    limits = data.get("limits", {})
    session_usage = limits.get("session", {}).get("usage")
    weekly_usage = limits.get("weekly", {}).get("usage")
    weekly_models_now = {m["name"]: m["request_count"] for m in limits.get("weekly", {}).get("models", [])}

    prethodno = load_stanje()
    save_stanje(data)

    prev_session = prethodno.get("session_usage") if prethodno else None
    prev_weekly = prethodno.get("weekly_usage") if prethodno else None
    session_delta = delta_pct_str(prev_session, session_usage)
    weekly_delta = delta_pct_str(prev_weekly, weekly_usage)
    nema_baze = " (prva provjera, nema baze za poredjenje)" if not prethodno else ""

    if args.kratko:
        linija = (
            f"Ollama: sedmicno {pct(weekly_usage)}{weekly_delta}, "
            f"session {pct(session_usage)}{session_delta}.{nema_baze}"
        )
        print(linija)
        return

    print(f"Ollama Cloud potrosnja — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Session (resetuje se ~5h):    {pct(session_usage)}{session_delta}")
    print(f"  Sedmicno (resetuje se ned.):  {pct(weekly_usage)}{weekly_delta}")
    print()
    print("  Sedmicna potrosnja po modelu:")
    for naziv, broj in sorted(weekly_models_now.items(), key=lambda x: -x[1]):
        prije = prethodno.get("weekly_models", {}).get(naziv) if prethodno else None
        if prije is not None:
            d = broj - prije
            znak = f"  ({d:+d} od poslednje provjere)" if d != 0 else "  (bez promjene)"
        else:
            znak = ""
        print(f"    {naziv:<28} {broj:>7}{znak}")

    if prethodno:
        print(f"\n  Prethodna provjera: {prethodno.get('timestamp', 'n/a')}")
    else:
        print("\n  (prva provjera, nema baze za poredjenje)")


if __name__ == "__main__":
    main()
