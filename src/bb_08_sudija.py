"""
bb_08_sudija.py
Gemma4:31b kao blind sudija — ocjenjuje prevode po gramatici,
prirodnosti i vjernosti originalu. Upisuje ocjene u bb_prevodi_recenica.

Modeli koji se ocjenjuju: gemma3:12b, ministral-3:14b, nllb-600M
Sudija: gemma4:31b (temperature=0.0)

Primjer:
    venv/bin/python src/bb_08_sudija.py \
        --knjiga 1 --od 1 --do 10 --jezici hr it
"""

import os
import re
import json
import argparse
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB = {
    "host":     os.getenv("DB_HOST", "balsam.dynu.net"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   "bb",
    "user":     os.getenv("DB_USER", "pgu"),
    "password": os.getenv("DB_PASSWORD"),
}

OLLAMA_URL   = os.getenv("OLLAMA_URL", "https://api.ollama.com")
OLLAMA_KEY   = os.getenv("OLLAMA_API_KEY", "")
SUDIJA_MODEL = "gemma4:31b"
SUDIJA_TEMP  = 0.0

OCJENJIVANI_MODELI = ["gemma3:12b", "ministral-3:14b", "nllb-600M"]

PROMPT_TEMPLATE = """You are evaluating {lang} translations of an English sentence.
Rate each translation on a scale 0.0–1.0 for three criteria:
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
  {{"id": 3, "grammar": 0.0, "naturalness": 0.0, "fidelity": 0.0}}
]"""


def call_sudija(prompt):
    headers = {"Authorization": f"Bearer {OLLAMA_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": SUDIJA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": SUDIJA_TEMP}
    }
    resp = requests.post(f"{OLLAMA_URL}/api/chat", headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def parse_ocjene(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\[.*?\]', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def main():
    import functools
    global print
    print = functools.partial(print, flush=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--knjiga", type=int, required=True)
    parser.add_argument("--od",     type=int, required=True)
    parser.add_argument("--do",     type=int, required=True)
    parser.add_argument("--jezici", type=str, nargs="+", required=True)
    args = parser.parse_args()

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    for kod in args.jezici:
        cur.execute("SELECT id, naziv FROM bb_jezik WHERE kod = %s", (kod,))
        row = cur.fetchone()
        if not row:
            print(f"Nepoznat jezik: {kod}, preskačem.")
            continue
        jezik_id, jezik_naziv = row

        print(f"\n══ Jezik: {kod} ({jezik_naziv}) ══")

        cur.execute("""
            SELECT r.id, r.pozicija, r.tekst,
                   m.naziv AS model,
                   pr.id   AS prevod_id,
                   pr.prevod
            FROM bb_recenice r
            JOIN bb_prevodi_knjige pk ON pk.knjiga_id = r.knjiga_id
            JOIN bb_prevodi_recenica pr ON pr.prevodi_knjige_id = pk.id
                                      AND pr.recenica_id = r.id
            JOIN bb_modeli m ON pk.model_id = m.id
            JOIN bb_jezik j  ON pk.jezik_id = j.id
            JOIN bb_embeddings e ON pk.embeddings_id = e.id
            WHERE r.knjiga_id = %s
              AND r.pozicija BETWEEN %s AND %s
              AND j.kod = %s
              AND m.naziv = ANY(%s)
              AND e.naziv = 'multilingual-e5-large'
              AND pr.sudija_avg IS NULL
            ORDER BY r.pozicija, m.naziv
        """, (args.knjiga, args.od, args.do, kod, OCJENJIVANI_MODELI))

        rows = cur.fetchall()

        # Grupiraj po rečenici
        recenice = {}
        for rid, pozicija, tekst, model, prevod_id, prevod in rows:
            if pozicija not in recenice:
                recenice[pozicija] = {"id": rid, "tekst": tekst, "prevodi": []}
            recenice[pozicija]["prevodi"].append({
                "model": model, "prevod_id": prevod_id, "prevod": prevod
            })

        if not recenice:
            print(f"  Nema rečenica za ocjenjivanje (sve već ocijenjene).")
            continue

        for pozicija, data in sorted(recenice.items()):
            prevodi = data["prevodi"]
            if len(prevodi) < 2:
                print(f"  s{pozicija}: premalo prevoda, preskačem.")
                continue

            translations_str = "\n".join(
                f"{i+1}. {p['prevod']}" for i, p in enumerate(prevodi)
            )

            prompt = PROMPT_TEMPLATE.format(
                lang=jezik_naziv,
                original=data["tekst"],
                translations=translations_str
            )

            print(f"  s{pozicija}: pozivam sudiju...")
            raw = call_sudija(prompt)
            ocjene = parse_ocjene(raw)

            if not ocjene:
                print(f"  s{pozicija}: nije moguće parsirati odgovor: {raw[:100]}")
                continue

            print(f"  s{pozicija} rezultati:")
            for ocjena in ocjene:
                idx = ocjena["id"] - 1
                if idx >= len(prevodi):
                    continue
                p = prevodi[idx]
                ukupno = (ocjena["grammar"] + ocjena["naturalness"] + ocjena["fidelity"]) / 3
                print(f"    [{idx+1}] {p['model']:20s} grammar={ocjena['grammar']:.2f} "
                      f"naturalness={ocjena['naturalness']:.2f} fidelity={ocjena['fidelity']:.2f} "
                      f"avg={ukupno:.3f} | {p['prevod'][:50]}...")

                cur.execute("""
                    UPDATE bb_prevodi_recenica
                    SET sudija_grammar     = %s,
                        sudija_naturalness = %s,
                        sudija_fidelity    = %s,
                        sudija_avg         = %s
                    WHERE id = %s
                """, (ocjena["grammar"], ocjena["naturalness"], ocjena["fidelity"],
                      ukupno, p["prevod_id"]))

            conn.commit()

        print()

    cur.close()
    conn.close()
    print("Gotovo.")


if __name__ == "__main__":
    main()
