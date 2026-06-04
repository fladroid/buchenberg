#!/usr/bin/env python3
"""
Buchenberg · health_check.py
Provjera svih infrastrukturnih komponenti projekta.
Pokretanje: venv/bin/python src/health_check.py
"""

import os
import sys
import subprocess
import requests
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

BUCH_HOME = Path(__file__).resolve().parent.parent
ENV_FILE  = BUCH_HOME / ".env"
BUCH_ENV  = BUCH_HOME / "buch_env.sh"

# ── Boje za terminal ────────────────────────────────────────────────
OK  = "\033[92m✅\033[0m"
WARN= "\033[93m⚠️ \033[0m"
ERR = "\033[91m❌\033[0m"
HDR = "\033[1;96m"
RST = "\033[0m"

def hdr(title):
    print(f"\n{HDR}{'═'*52}{RST}")
    print(f"{HDR}  {title}{RST}")
    print(f"{HDR}{'═'*52}{RST}")

def row(icon, label, value=""):
    print(f"  {icon}  {label:<36} {value}")

# ── 1. .env fajl ────────────────────────────────────────────────────
def check_env():
    hdr("1. .env fajl")
    required = [
        "OLLAMA_API_KEY", "OLLAMA_BASE_URL", "OLLAMA_MODEL",
        "DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD"
    ]
    if not ENV_FILE.exists():
        row(ERR, ".env fajl", f"NIJE PRONAĐEN: {ENV_FILE}")
        return False

    load_dotenv(ENV_FILE)
    row(OK, ".env fajl", str(ENV_FILE))

    all_ok = True
    for var in required:
        val = os.getenv(var)
        if val:
            display = val[:6] + "***" if "KEY" in var or "PASSWORD" in var else val
            row(OK, var, display)
        else:
            row(ERR, var, "NEDOSTAJE!")
            all_ok = False

    if BUCH_ENV.exists():
        row(OK, "buch_env.sh", str(BUCH_ENV))
    else:
        row(WARN, "buch_env.sh", "nije pronađen")

    return all_ok

# ── 2. PostgreSQL — bb baza ──────────────────────────────────────────
def check_postgres():
    hdr("2. PostgreSQL — bb baza")
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT", 5432)),
            dbname="bb", user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"), connect_timeout=5
        )
        cur = conn.cursor()

        cur.execute("SELECT version()")
        ver = cur.fetchone()[0].split(" on ")[0]
        row(OK, "Konekcija (bb)", ver)

        # Osnovne tabele
        for tbl in ("bb_knjige", "bb_recenice", "bb_prevodi_recenica", "bb_prev_recenica"):
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            n = cur.fetchone()[0]
            row(OK, f"  {tbl}", f"{n:,} redova")

        # Stanje prevoda po knjizi i jeziku
        cur.execute("""
            SELECT k.naziv, j.kod,
                   COUNT(DISTINCT pr.recenica_id) AS prev_rec,
                   COUNT(DISTINCT po.prevodi_recenica_id) AS pobjednici
            FROM bb_prevodi_knjige pk
            JOIN bb_knjige k  ON k.id = pk.knjiga_id
            JOIN bb_jezik  j  ON j.id = pk.jezik_id
            JOIN bb_prevodi_recenica pr ON pr.prevodi_knjige_id = pk.id
            LEFT JOIN bb_prev_knjige ppk ON ppk.knjiga_id = pk.knjiga_id AND ppk.jezik_id = pk.jezik_id LEFT JOIN bb_prev_recenica po ON po.prev_knjige_id = ppk.id
            GROUP BY k.naziv, j.kod
            ORDER BY k.naziv, j.kod
        """)
        rows_data = cur.fetchall()

        if rows_data:
            print(f"\n  {'─'*48}")
            print(f"  Stanje prevoda:")
            print(f"  {'Knjiga':<36} {'Lang':>4} {'Prev':>6} {'Pobj':>6}")
            print(f"  {'─'*56}")
            prev_knjiga = None
            for naziv, kod, prev_rec, pobjednici in rows_data:
                knjiga_display = naziv[:34] if naziv != prev_knjiga else ""
                prev_knjiga = naziv
                pobj_str = str(pobjednici) if pobjednici else "-"
                print(f"  {knjiga_display:<36} {kod:>4} {prev_rec:>6} {pobj_str:>6}")

        conn.close()
        return True
    except Exception as e:
        row(ERR, "Konekcija", str(e))
        return False

# ── 3. Ollama Cloud — modeli ─────────────────────────────────────────
def check_ollama():
    hdr("3. Ollama Cloud")
    api_key  = os.getenv("OLLAMA_API_KEY")
    base_url = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
    headers  = {"Authorization": f"Bearer {api_key}"}

    try:
        r = requests.get(f"{base_url}/api/tags", headers=headers, timeout=10)
        r.raise_for_status()
        available = {m["name"] for m in r.json().get("models", [])}
        row(OK, "API dostupan", f"{len(available)} modela")
    except Exception as e:
        row(ERR, "API nedostupan", str(e))
        return False

    used_models = {
        "gemma3:12b":      "prevod",
        "ministral-3:14b": "prevod",
        "gemma4:31b":      "sudija",
    }

    print(f"\n  {'─'*48}")
    print(f"  Modeli koji se koriste u projektu:")
    all_ok = True
    for model, uloga in used_models.items():
        if model in available:
            try:
                tr = requests.post(
                    f"{base_url}/api/chat",
                    headers={**headers, "Content-Type": "application/json"},
                    json={"model": model, "messages": [{"role": "user", "content": "Say OK"}], "stream": False},
                    timeout=30
                )
                reply = tr.json().get("message", {}).get("content", "")[:20].strip()
                row(OK, f"{model}", f"→ '{reply}'  [{uloga}]")
            except Exception as e:
                row(WARN, f"{model}", f"dostupan ali test poziv pao: {e}")
        else:
            row(ERR, f"{model}", f"NIJE u listi!  [{uloga}]")
            all_ok = False

    print(f"\n  {'─'*48}")
    print(f"  Svi dostupni modeli na Ollama Cloud:")
    for m in sorted(available):
        marker = OK if m in used_models else "  "
        print(f"  {marker}  {m}")

    return all_ok

# ── 4. NLLB (lokalni model) ──────────────────────────────────────────
def check_nllb():
    hdr("4. NLLB (lokalni model)")
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"

    nllb_dirs = list(cache_dir.glob("models--facebook--nllb*")) if cache_dir.exists() else []
    if nllb_dirs:
        row(OK, "NLLB keš", str(nllb_dirs[0].name))
    else:
        row(WARN, "NLLB keš", f"nije pronađen u {cache_dir}")

    try:
        result = subprocess.run(
            [str(BUCH_HOME / "venv" / "bin" / "python"), "-c",
             "from transformers import AutoTokenizer; print('transformers OK')"],
            capture_output=True, text=True, timeout=15
        )
        if "OK" in result.stdout:
            row(OK, "transformers import", "OK")
        else:
            row(ERR, "transformers import", result.stderr[:60])
    except Exception as e:
        row(ERR, "transformers import", str(e))

# ── 5. Python venv — paketi ──────────────────────────────────────────
def check_venv():
    hdr("5. Python venv — paketi")
    venv_python = BUCH_HOME / "venv" / "bin" / "python"

    if not venv_python.exists():
        row(ERR, "venv", f"nije pronađen: {venv_python}")
        return

    row(OK, "venv", str(venv_python))

    required_packages = [
        "psycopg2", "transformers", "sentencepiece", "sacremoses",
        "sentence_transformers", "loguru", "dotenv", "beautifulsoup4",
        "nltk", "spacy", "requests", "yaml"
    ]

    import_map = {
        "dotenv": "dotenv",
        "beautifulsoup4": "bs4",
        "yaml": "yaml",
    }

    for pkg in required_packages:
        import_name = import_map.get(pkg, pkg)
        result = subprocess.run(
            [str(venv_python), "-c", f"import {import_name}; print('ok')"],
            capture_output=True, text=True, timeout=10
        )
        if "ok" in result.stdout:
            row(OK, pkg)
        else:
            row(ERR, pkg, result.stderr.split("\n")[0][:50])

# ── 6. Git status ────────────────────────────────────────────────────
def check_git():
    hdr("6. Git status")
    try:
        result = subprocess.run(
            ["git", "-C", str(BUCH_HOME), "status", "--short"],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().splitlines()
        if not lines:
            row(OK, "Working tree", "čist — nema uncommitted promjena")
        else:
            row(WARN, "Uncommitted promjene", f"{len(lines)} fajlova")
            for l in lines:
                print(f"       {l}")

        result2 = subprocess.run(
            ["git", "-C", str(BUCH_HOME), "log", "--oneline", "-3"],
            capture_output=True, text=True, timeout=10
        )
        print(f"\n  Zadnja 3 commita:")
        for l in result2.stdout.strip().splitlines():
            print(f"    {l}")
    except Exception as e:
        row(ERR, "Git", str(e))

# ── Main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{HDR}{'█'*52}{RST}")
    print(f"{HDR}  BUCHENBERG · Health Check{RST}")
    print(f"{HDR}{'█'*52}{RST}")

    env_ok = check_env()
    if env_ok:
        check_postgres()
        check_ollama()
    check_nllb()
    check_venv()
    check_git()

    print(f"\n{HDR}{'═'*52}{RST}")
    print(f"{HDR}  Health check završen.{RST}")
    print(f"{HDR}{'═'*52}{RST}\n")
