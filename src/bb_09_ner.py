"""
bb_09_ner.py
NER pipeline za Buchenberg knjige.

Faze:
  1. spaCy  — ekstrahuj PERSON/GPE/ORG entitete iz originalnih rečenica
  2. LLM — normalizacija kandidata (grupiranje varijanti)
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

NER_MODEL = "glm-5.2"   # NE sudija (gemma4 ostaje slijep i fiksan) — s124/s130
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
        "model": NER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
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
def faza1_spacy(conn, knjiga_id, tipovi, nlp):
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

# ── Faza 2: LLM normalizacija ─────────────────────────────
def faza2_normalizacija(entiteti, knjiga_naziv):
    """
    Za svaki tip šalje LLM listu svih oblika i traži grupiranje.
    Vraća: norm_map[tip][ime_orig] = ime_norm
    """
    norm_map = {}

    for tip, imena_dict in entiteti.items():
        svi_oblici = sorted(imena_dict.keys())
        logger.info(f"  Normalizacija {tip}: {len(svi_oblici)} oblika → LLM...")

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
            logger.warning(f"  LLM nije odgovorio za {tip} — koristim originalna imena")
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

    # Briši stari classic sloj (s130). Skripta briše SAMO svoje entitete —
    # sve izvedeno (pojave, veze, relacije) pada kroz ON DELETE CASCADE (s130).
    # bb_09 ne zna i ne smije znati za slojeve iznad sebe.
    cur.execute("DELETE FROM bb_ner_entiteti WHERE knjiga_id = %s AND method = 'classic'",
                (knjiga_id,))
    conn.commit()
    logger.info("  Stari classic NER podaci obrisani (entiteti + izvedeno kaskadno).")

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
                ON CONFLICT (knjiga_id, ime_norm, tip, method) DO UPDATE
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
    logger.info(f"  Upisano {upis_count} veza rečenica↔entiteta.")

    # Co-occurrence (ista rečenica) — materijalizovano u bb_ner_veze (s129/s130).
    # Skripta koja briše sloj odgovorna je i da ga vrati konzistentnim.
    cur.execute("""
        INSERT INTO bb_ner_veze (knjiga_id, entitet1_id, entitet2_id, tezina)
        SELECT %s, r1.entitet_id, r2.entitet_id, COUNT(*)
        FROM bb_ner_recenica r1
        JOIN bb_ner_recenica r2
          ON r1.recenica_id = r2.recenica_id
         AND r1.entitet_id < r2.entitet_id
        JOIN bb_ner_entiteti e1 ON e1.id = r1.entitet_id
        JOIN bb_ner_entiteti e2 ON e2.id = r2.entitet_id
        WHERE e1.knjiga_id = %s AND e1.method = 'classic'
          AND e2.knjiga_id = %s AND e2.method = 'classic'
        GROUP BY r1.entitet_id, r2.entitet_id
        ON CONFLICT DO NOTHING
    """, (knjiga_id, knjiga_id, knjiga_id))
    conn.commit()
    cur.execute("""
        SELECT COUNT(*) FROM bb_ner_veze v
        JOIN bb_ner_entiteti e ON e.id = v.entitet1_id
        WHERE e.knjiga_id = %s AND e.method = 'classic'
    """, (knjiga_id,))
    logger.info(f"  Co-occurrence veza (classic): {cur.fetchone()[0]}")
    cur.close()

# ── Main ──────────────────────────────────────────────────────
def ima_classic(conn, knjiga_id):
    """Ima li knjiga već classic NER sloj?"""
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM bb_ner_entiteti
        WHERE knjiga_id = %s AND method = 'classic'
    """, (knjiga_id,))
    n = cur.fetchone()[0]
    cur.close()
    return n


def main():
    parser = argparse.ArgumentParser(description="NER pipeline za Buchenberg (classic sloj)")
    parser.add_argument("--knjiga", default="1", help="ID knjige ili 'all'")
    parser.add_argument("--force", action="store_true",
                        help="Prepiši i knjige koje već imaju classic sloj")
    parser.add_argument("--tip", nargs="+", default=["PERSON", "GPE", "ORG"],
                        help="Tipovi entiteta (default: PERSON GPE ORG)")
    args = parser.parse_args()

    tipovi = set(args.tip)
    conn = get_conn()

    # Skup knjiga
    cur = conn.cursor()
    if str(args.knjiga).lower() == "all":
        cur.execute("SELECT id, naziv FROM bb_knjige ORDER BY id")
        knjige = cur.fetchall()
    else:
        cur.execute("SELECT id, naziv FROM bb_knjige WHERE id = %s", (int(args.knjiga),))
        knjige = cur.fetchall()
        if not knjige:
            logger.error(f"Knjiga id={args.knjiga} ne postoji!")
            sys.exit(1)
    cur.close()

    logger.info(f"bb_09_ner.py — knjiga={args.knjiga} ({len(knjige)} knjiga), "
                f"tipovi={tipovi}, force={args.force}")

    # spaCy — učitan JEDNOM, van petlje (s130)
    import spacy
    logger.info("Učitavam spaCy en_core_web_sm...")
    nlp = spacy.load("en_core_web_sm")

    obradjeno = preskoceno = 0
    for knjiga_id, knjiga_naziv in knjige:
        postoji = ima_classic(conn, knjiga_id)
        if postoji and not args.force:
            logger.info(f"[{knjiga_id}] {knjiga_naziv}: classic sloj postoji "
                        f"({postoji} entiteta) → PRESKAČEM (--force za prepis)")
            preskoceno += 1
            continue

        logger.info(f"[{knjiga_id}] {knjiga_naziv}: obrađujem"
                    + (f" (prepisujem {postoji} entiteta)" if postoji else ""))

        logger.info("  Faza 1: spaCy NER...")
        entiteti = faza1_spacy(conn, knjiga_id, tipovi, nlp)

        logger.info("  Faza 2: LLM normalizacija...")
        norm_map = faza2_normalizacija(entiteti, knjiga_naziv)

        logger.info("  Faza 3: Upis u bazu...")
        faza3_upis(conn, knjiga_id, entiteti, norm_map)
        obradjeno += 1

    logger.info(f"bb_09 gotov — obrađeno {obradjeno}, preskočeno {preskoceno}.")
    conn.close()
    logger.info("NER pipeline završen.")

if __name__ == "__main__":
    main()
