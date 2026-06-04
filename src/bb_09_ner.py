"""
bb_09_ner.py
NER pipeline za Buchenberg knjige.

Faze:
  1. spaCy  — ekstrahuj PERSON/GPE/ORG entitete iz originalnih rečenica
  2. Gemma4 — normalizacija kandidata (grupiranje varijanti)
  3. Upis   — bb_ner_entiteti + bb_ner_recenica

Primjer:
  venv/bin/python src/bb_09_ner.py --knjiga 1
  venv/bin/python src/bb_09_ner.py --knjiga 1 --tiket PERSON
"""

import os
import sys
import json
import argparse
import requests
import psycopg2
from collections import defaultdict
from dotenv import load_dotenv
from loguru import logger

load_dotenv("/home/balsam/buchenberg/.env")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY = os.getenv("OLLAMA_API_KEY")

SUDIJA_MODEL = "gemma4:31b"
TIPOVI = {"PERSON", "GPE", "ORG"}

# ── DB ────────────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        dbname="bb"
    )

# ── Ollama ────────────────────────────────────────────────────
def ollama_call(prompt):
    url = f"{OLLAMA_URL}/api/chat"
    payload = {
        "model": SUDIJA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.0}
    }
    for attempt in range(3):
        try:
            r = requests.post(
                url, json=payload,
                headers={"Authorization": f"Bearer {OLLAMA_KEY}"},
                timeout=120
            )
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"Ollama attempt {attempt+1}/3: {e}")
    return None

# ── Faza 1: spaCy NER ─────────────────────────────────────────
def faza1_spacy(conn, knjiga_id, tipovi):
    import spacy
    nlp = spacy.load("en_core_web_sm")

    cur = conn.cursor()
    cur.execute(
        "SELECT id, tekst FROM bb_recenice WHERE knjiga_id = %s ORDER BY pozicija",
        (knjiga_id,)
    )
    recenice = cur.fetchall()
    cur.close()

    logger.info(f"  spaCy NER na {len(recenice)} rečenica...")

    # entiteti[tip][ime_orig] = [(recenica_id, ...), ...]
    entiteti = defaultdict(lambda: defaultdict(list))

    for rec_id, tekst in recenice:
        doc = nlp(tekst)
        for ent in doc.ents:
            if ent.label_ in tipovi:
                ime = ent.text.strip()
                if len(ime) < 2:
                    continue
                entiteti[ent.label_][ime].append(rec_id)

    # Sažetak
    for tip, imena in entiteti.items():
        logger.info(f"    {tip}: {len(imena)} jedinstvenih oblika")

    return entiteti

# ── Faza 2: Gemma4 normalizacija ─────────────────────────────
def faza2_normalizacija(entiteti, knjiga_naziv):
    """
    Za svaki tip šalje Gemma4 listu svih oblika i traži grupiranje.
    Vraća: norm_map[tip][ime_orig] = ime_norm
    """
    norm_map = {}

    for tip, imena_dict in entiteti.items():
        svi_oblici = sorted(imena_dict.keys())
        logger.info(f"  Normalizacija {tip}: {len(svi_oblici)} oblika → Gemma4...")

        prompt = f"""You are a literary NLP assistant. I have a list of named entities of type {tip} extracted from the novel "{knjiga_naziv}".

Many of these are variants of the same entity (e.g. "Holmes", "Mr. Holmes", "Sherlock Holmes", "Sherlock" all refer to the same person).

Your task: group these variants and assign a canonical normalized name to each group.

Rules:
- Use the most complete/formal form as the canonical name
- Only group entities you are confident refer to the same real entity in this novel
- When uncertain, keep them separate
- Return ONLY valid JSON, no explanation, no markdown

Input list:
{json.dumps(svi_oblici, ensure_ascii=False)}

Return format (JSON object mapping each input string to its canonical form):
{{"original_name": "Canonical Name", ...}}"""

        response = ollama_call(prompt)
        if not response:
            logger.warning(f"  Gemma4 nije odgovorio za {tip} — koristim originalna imena")
            norm_map[tip] = {ime: ime for ime in svi_oblici}
            continue

        # Parse JSON iz odgovora
        try:
            # Ukloni moguće markdown backticks
            clean = response.strip()
            if clean.startswith("```"):
                clean = "\n".join(clean.split("\n")[1:])
            if clean.endswith("```"):
                clean = "\n".join(clean.split("\n")[:-1])
            mapping = json.loads(clean)
            # Provjera — svaki originalni oblik mora biti u mappingu
            result = {}
            for ime in svi_oblici:
                result[ime] = mapping.get(ime, ime)
            norm_map[tip] = result
            logger.info(f"    → {len(set(result.values()))} normalizovanih entiteta")
        except json.JSONDecodeError as e:
            logger.warning(f"  JSON parse error za {tip}: {e} — koristim originalna imena")
            norm_map[tip] = {ime: ime for ime in svi_oblici}

    return norm_map

# ── Faza 3: Upis u bazu ───────────────────────────────────────
def faza3_upis(conn, knjiga_id, entiteti, norm_map):
    cur = conn.cursor()

    # Briši stare podatke za ovu knjigu
    cur.execute("""
        DELETE FROM bb_ner_recenica
        WHERE entitet_id IN (
            SELECT id FROM bb_ner_entiteti WHERE knjiga_id = %s
        )
    """, (knjiga_id,))
    cur.execute("DELETE FROM bb_ner_entiteti WHERE knjiga_id = %s", (knjiga_id,))
    conn.commit()
    logger.info("  Stari NER podaci obrisani.")

    # Upiši entitete
    entitet_ids = {}  # (tip, ime_norm) → id

    for tip, imena_dict in entiteti.items():
        tip_norm = norm_map.get(tip, {})

        # Grupiraj po normalizovanom imenu
        grupe = defaultdict(lambda: {"pojave": 0, "ime_orig": None})
        for ime_orig, rec_ids in imena_dict.items():
            ime_norm = tip_norm.get(ime_orig, ime_orig)
            grupe[ime_norm]["pojave"] += len(rec_ids)
            if grupe[ime_norm]["ime_orig"] is None:
                grupe[ime_norm]["ime_orig"] = ime_orig

        for ime_norm, info in grupe.items():
            cur.execute("""
                INSERT INTO bb_ner_entiteti (knjiga_id, tip, ime_orig, ime_norm, pojave)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (knjiga_id, ime_norm, tip) DO UPDATE
                    SET pojave = EXCLUDED.pojave
                RETURNING id
            """, (knjiga_id, tip, info["ime_orig"], ime_norm, info["pojave"]))
            ent_id = cur.fetchone()[0]
            entitet_ids[(tip, ime_norm)] = ent_id

    conn.commit()
    logger.info(f"  Upisano {len(entitet_ids)} normalizovanih entiteta.")

    # Upiši bb_ner_recenica
    upis_count = 0
    for tip, imena_dict in entiteti.items():
        tip_norm = norm_map.get(tip, {})
        for ime_orig, rec_ids in imena_dict.items():
            ime_norm = tip_norm.get(ime_orig, ime_orig)
            ent_id = entitet_ids.get((tip, ime_norm))
            if not ent_id:
                continue
            for rec_id in rec_ids:
                try:
                    cur.execute("""
                        INSERT INTO bb_ner_recenica (recenica_id, entitet_id, ime_orig)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (rec_id, ent_id, ime_orig))
                    upis_count += 1
                except Exception as e:
                    logger.warning(f"  Upis greška: {e}")

    conn.commit()
    cur.close()
    logger.info(f"  Upisano {upis_count} veza rečenica↔entiteta.")

# ── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="NER pipeline za Buchenberg")
    parser.add_argument("--knjiga", type=int, required=True)
    parser.add_argument("--tip", nargs="+", default=["PERSON", "GPE", "ORG"],
                        help="Tipovi entiteta (default: PERSON GPE ORG)")
    args = parser.parse_args()

    tipovi = set(args.tip)
    logger.info(f"bb_09_ner.py — knjiga_id={args.knjiga}, tipovi={tipovi}")

    conn = get_conn()

    # Naziv knjige
    cur = conn.cursor()
    cur.execute("SELECT naziv FROM bb_knjige WHERE id = %s", (args.knjiga,))
    row = cur.fetchone()
    cur.close()
    if not row:
        logger.error(f"Knjiga id={args.knjiga} ne postoji!")
        sys.exit(1)
    knjiga_naziv = row[0]
    logger.info(f"  Knjiga: {knjiga_naziv}")

    # Faza 1
    logger.info("Faza 1: spaCy NER...")
    entiteti = faza1_spacy(conn, args.knjiga, tipovi)

    # Faza 2
    logger.info("Faza 2: Gemma4 normalizacija...")
    norm_map = faza2_normalizacija(entiteti, knjiga_naziv)

    # Faza 3
    logger.info("Faza 3: Upis u bazu...")
    faza3_upis(conn, args.knjiga, entiteti, norm_map)

    conn.close()
    logger.info("NER pipeline završen.")

if __name__ == "__main__":
    main()
