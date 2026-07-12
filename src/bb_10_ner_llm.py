"""
bb_10_ner_llm.py
LLM-potpomognuta NER analiza za Buchenberg — DIO 1: type reconciliation.

Classic NER (bb_09) puni bb_ner_entiteti / bb_ner_recenica sa method='classic'.
Ovaj skript čita konfliktna imena (isto ime, više tipova = spaCy nekonzistentnost),
daje LLM-u DOKAZNE REČENICE po tipu (grounding, ne slijepo tumačenje — s90 princip),
i upisuje razriješenu verziju sa method='llm'.

Tri ishoda po konfliktnom imenu:
  - greska     : manjinski tip je spaCy greška -> jedan entitet, primarni tip
  - dvojnost   : ime legitimno nosi dva smisla (npr. Baskerville = porodica/osoba
                 I imanje) -> zadrži primarni + sekundarni, oba označena
  - ne_entitet : uopšte nije imenovani entitet (npr. "I." = zamjenica) -> odbaci

LLM smije predložiti tip koji se NE nalazi među postojećim labelama
(npr. Coombe Tracey: spaCy dao PERSON/ORG, pravi tip GPE).

Model: glm-5.2 (aktivni prevodilac, NE sudija — sudija ostaje slijep/fiksan, s124).

Upotreba:
  venv/bin/python src/bb_10_ner_llm.py --knjiga 1
  venv/bin/python src/bb_10_ner_llm.py --knjiga 1 --dry-run   # samo ispiši, ne piši u bazu
"""

import os
import sys
import json
import argparse
import requests
import psycopg2
from dotenv import load_dotenv
from loguru import logger

load_dotenv("/home/balsam/buchenberg/.env")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY = os.getenv("OLLAMA_API_KEY")

LLM_MODEL = "glm-5.2"
MAX_REC_PO_TIPU = 4   # koliko dokaznih rečenica po tipu šaljemo LLM-u

# -- DB --------------------------------------------------------
def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        dbname="bb"
    )

# -- Ollama (isti obrazac kao bb_03 ollama_chat) ---------------
def ollama_call(prompt, temperature=0.0, max_retries=3, wait=30):
    import time
    headers = {"Content-Type": "application/json"}
    if OLLAMA_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_KEY}"
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": temperature},
    }
    for attempt in range(max_retries):
        try:
            r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload,
                              headers=headers, timeout=180)
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except (requests.exceptions.HTTPError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                logger.warning(f"  Greska ({e}), cekam {wait}s (pokusaj {attempt+1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise

# -- Konfliktna imena + dokazne recenice -----------------------
def ucitaj_konflikte(cur, knjiga_id):
    """Vrati listu konfliktnih imena: [{ime, tipovi:[{tip,pojave,recenice:[...]}]}]."""
    cur.execute("""
        SELECT ime_norm, tip, pojave
        FROM bb_ner_entiteti
        WHERE knjiga_id = %s AND method = 'classic'
          AND ime_norm IN (
            SELECT ime_norm FROM bb_ner_entiteti
            WHERE knjiga_id = %s AND method = 'classic'
            GROUP BY ime_norm HAVING COUNT(*) > 1
          )
        ORDER BY ime_norm, pojave DESC
    """, (knjiga_id, knjiga_id))
    rows = cur.fetchall()

    konflikti = {}
    for ime, tip, pojave in rows:
        konflikti.setdefault(ime, []).append({"tip": tip, "pojave": pojave, "recenice": []})

    for ime, tipovi in konflikti.items():
        for t in tipovi:
            cur.execute("""
                SELECT rec.pozicija, rec.tekst
                FROM bb_ner_entiteti e
                JOIN bb_ner_recenica r ON r.entitet_id = e.id
                JOIN bb_recenice rec ON rec.id = r.recenica_id
                WHERE e.knjiga_id = %s AND e.method = 'classic'
                  AND e.ime_norm = %s AND e.tip = %s
                ORDER BY rec.pozicija
                LIMIT %s
            """, (knjiga_id, ime, t["tip"], MAX_REC_PO_TIPU))
            t["recenice"] = [{"pozicija": p, "tekst": tk} for p, tk in cur.fetchall()]

    return [{"ime": ime, "tipovi": tipovi} for ime, tipovi in konflikti.items()]

# -- Prompt ----------------------------------------------------
def sklopi_prompt(knjiga_naziv, konflikt):
    ime = konflikt["ime"]
    blokovi = []
    for t in konflikt["tipovi"]:
        recenice = "\n".join(
            f'      [pos {r["pozicija"]}] "{r["tekst"]}"' for r in t["recenice"]
        )
        blokovi.append(f'  Tagged as {t["tip"]} ({t["pojave"]}x):\n{recenice}')
    dokazi = "\n\n".join(blokovi)

    return f"""You are a literary NLP assistant analyzing named entities in the novel "{knjiga_naziv}".

The name "{ime}" was tagged with MULTIPLE entity types by an automatic NER tool. This usually means the tool was inconsistent, but sometimes a name legitimately carries two senses (e.g. a surname that is also a place, like "Baskerville" = the family/person AND Baskerville Hall).

Read the actual sentences below and decide what "{ime}" really refers to. Judge from the TEXT, not from the tags -- the tags may all be wrong.

Evidence sentences:
{dokazi}

Valid entity types: PERSON (people, families), GPE (places, geo-political), ORG (organizations).
You MAY assign a type that does NOT appear in the tags above if the text clearly shows it (e.g. a village mislabeled PERSON should become GPE).

Return ONLY valid JSON, no markdown, no explanation, in this exact shape:
{{
  "ishod": "greska" | "dvojnost" | "ne_entitet",
  "primarni_tip": "PERSON" | "GPE" | "ORG" | null,
  "sekundarni_tip": "PERSON" | "GPE" | "ORG" | null,
  "obrazlozenje": "one short sentence citing the evidence",
  "dokaz_pos": <sentence position number that best supports your decision, or null>
}}

Rules:
- "greska": the name has ONE real type; other tags are errors. Set primarni_tip, sekundarni_tip=null.
- "dvojnost": the name legitimately has TWO senses. Set primarni_tip (dominant) AND sekundarni_tip.
- "ne_entitet": this is not a real named entity at all (e.g. a pronoun, an initial). Set both tips=null.
"""

# -- Parse -----------------------------------------------------
def parse_odgovor(raw):
    clean = raw.strip()
    if clean.startswith("```"):
        clean = "\n".join(clean.split("\n")[1:])
    if clean.endswith("```"):
        clean = "\n".join(clean.split("\n")[:-1])
    return json.loads(clean)

# -- Faza upisa: LLM odluke -> method='llm' redovi -------------
def upisi_llm(cur, knjiga_id, odluke):
    """Pretvori LLM odluke u method='llm' redove. Idempotentno (DELETE llm pa INSERT)."""
    # Briši SAMO svoje llm entitete — pojave/veze/relacije padaju kaskadno (s130).
    # bb_10 ne zna za slojeve iznad sebe (DocRE); orkestrator ih obnavlja.
    cur.execute("DELETE FROM bb_ner_entiteti WHERE knjiga_id = %s AND method = 'llm'",
                (knjiga_id,))

    upis_ent = upis_veze = preskoceno = 0

    for od in odluke:
        ime = od["ime"]
        ishod = od["ishod"]

        if ishod == "ne_entitet":
            preskoceno += 1
            continue

        primarni = od.get("primarni_tip")
        sekundarni = od.get("sekundarni_tip")
        if not primarni:
            logger.warning(f"  '{ime}': ishod={ishod} bez primarni_tip -- preskacem")
            preskoceno += 1
            continue

        priznati = [primarni] + ([sekundarni] if sekundarni else [])

        cur.execute("""
            SELECT e.tip, e.ime_orig, e.pojave, e.id
            FROM bb_ner_entiteti e
            WHERE e.knjiga_id = %s AND e.method = 'classic' AND e.ime_norm = %s
        """, (knjiga_id, ime))
        classic_redovi = cur.fetchall()

        llm_ent_id = {}
        for tip in priznati:
            ime_orig = next((r[1] for r in classic_redovi if r[0] == tip),
                            classic_redovi[0][1] if classic_redovi else ime)
            if ishod == "greska":
                pojave = sum(r[2] for r in classic_redovi)
            else:
                pojave = sum(r[2] for r in classic_redovi if r[0] == tip) or 1
            cur.execute("""
                INSERT INTO bb_ner_entiteti (knjiga_id, tip, ime_orig, ime_norm, pojave, method)
                VALUES (%s, %s, %s, %s, %s, 'llm')
                RETURNING id
            """, (knjiga_id, tip, ime_orig, ime, pojave))
            llm_ent_id[tip] = cur.fetchone()[0]
            upis_ent += 1

        for c_tip, c_ime_orig, c_pojave, c_id in classic_redovi:
            if ishod == "greska":
                cilj_tip = primarni
            else:
                cilj_tip = c_tip if c_tip in llm_ent_id else primarni
            cilj_id = llm_ent_id[cilj_tip]
            cur.execute("""
                INSERT INTO bb_ner_recenica (recenica_id, entitet_id, ime_orig, method)
                SELECT r.recenica_id, %s, r.ime_orig, 'llm'
                FROM bb_ner_recenica r
                WHERE r.entitet_id = %s AND r.method = 'classic'
                ON CONFLICT DO NOTHING
            """, (cilj_id, c_id))
            upis_veze += cur.rowcount

    # -- Kopiraj NEKONFLIKTNE classic entitete kao ciste llm redove ---------
    # (llm postaje potpun samostalan sloj: razrijeseni konflikti + svi nekonfliktni)
    cur.execute("""
        SELECT e.id, e.tip, e.ime_orig, e.ime_norm, e.pojave
        FROM bb_ner_entiteti e
        WHERE e.knjiga_id = %s AND e.method = 'classic'
          AND e.ime_norm NOT IN (
            SELECT ime_norm FROM bb_ner_entiteti
            WHERE knjiga_id = %s AND method = 'classic'
            GROUP BY ime_norm HAVING COUNT(*) > 1
          )
    """, (knjiga_id, knjiga_id))
    nekonfliktni = cur.fetchall()

    kopirano_ent = kopirano_veze = 0
    for c_id, tip, ime_orig, ime_norm, pojave in nekonfliktni:
        cur.execute("""
            INSERT INTO bb_ner_entiteti (knjiga_id, tip, ime_orig, ime_norm, pojave, method)
            VALUES (%s, %s, %s, %s, %s, 'llm')
            RETURNING id
        """, (knjiga_id, tip, ime_orig, ime_norm, pojave))
        novi_id = cur.fetchone()[0]
        kopirano_ent += 1
        cur.execute("""
            INSERT INTO bb_ner_recenica (recenica_id, entitet_id, ime_orig, method)
            SELECT r.recenica_id, %s, r.ime_orig, 'llm'
            FROM bb_ner_recenica r
            WHERE r.entitet_id = %s AND r.method = 'classic'
            ON CONFLICT DO NOTHING
        """, (novi_id, c_id))
        kopirano_veze += cur.rowcount

    logger.info(f"  Kopirano nekonfliktnih: {kopirano_ent} entiteta, {kopirano_veze} veza.")

    logger.info(f"  Upisano: {upis_ent} llm entiteta, {upis_veze} veza, "
                f"{preskoceno} preskoceno (ne_entitet).")

    # Co-occurrence (ista rečenica) za llm sloj — ko briše, taj i vraća (s130).
    cur.execute("""
        INSERT INTO bb_ner_veze (knjiga_id, entitet1_id, entitet2_id, tezina)
        SELECT %s, r1.entitet_id, r2.entitet_id, COUNT(*)
        FROM bb_ner_recenica r1
        JOIN bb_ner_recenica r2
          ON r1.recenica_id = r2.recenica_id
         AND r1.entitet_id < r2.entitet_id
        JOIN bb_ner_entiteti e1 ON e1.id = r1.entitet_id
        JOIN bb_ner_entiteti e2 ON e2.id = r2.entitet_id
        WHERE e1.knjiga_id = %s AND e1.method = 'llm'
          AND e2.knjiga_id = %s AND e2.method = 'llm'
        GROUP BY r1.entitet_id, r2.entitet_id
        ON CONFLICT DO NOTHING
    """, (knjiga_id, knjiga_id, knjiga_id))
    cur.execute("""
        SELECT COUNT(*) FROM bb_ner_veze v
        JOIN bb_ner_entiteti e ON e.id = v.entitet1_id
        WHERE e.knjiga_id = %s AND e.method = 'llm'
    """, (knjiga_id,))
    logger.info(f"  Co-occurrence veza (llm): {cur.fetchone()[0]}")


# -- Main ------------------------------------------------------
def broj_sloja(cur, knjiga_id, method):
    """Koliko entiteta knjiga ima u datom sloju."""
    cur.execute("""
        SELECT COUNT(*) FROM bb_ner_entiteti
        WHERE knjiga_id = %s AND method = %s
    """, (knjiga_id, method))
    return cur.fetchone()[0]


def obradi_knjigu(conn, cur, knjiga_id, knjiga_naziv, dry_run):
    konflikti = ucitaj_konflikte(cur, knjiga_id)
    logger.info(f"  Konfliktnih imena: {len(konflikti)}")

    odluke = []
    for k in konflikti:
        prompt = sklopi_prompt(knjiga_naziv, k)
        raw = ollama_call(prompt)
        try:
            odluka = parse_odgovor(raw)
        except json.JSONDecodeError as e:
            logger.warning(f"  JSON parse greska za '{k['ime']}': {e}")
            logger.warning(f"  RAW: {raw[:200]}")
            continue
        odluka["ime"] = k["ime"]
        odluka["tagovi"] = {t["tip"]: t["pojave"] for t in k["tipovi"]}
        odluke.append(odluka)
        logger.info(
            f"  {k['ime']:16} {str(odluka['tagovi']):28} -> "
            f"{odluka['ishod']:10} {odluka.get('primarni_tip') or ''}"
            f"{'+' + odluka['sekundarni_tip'] if odluka.get('sekundarni_tip') else ''}"
        )

    if dry_run:
        logger.info("  DRY-RUN -- nista nije upisano. Rezime odluka:")
        print(json.dumps(odluke, ensure_ascii=False, indent=2))
    else:
        upisi_llm(cur, knjiga_id, odluke)
        conn.commit()


def main():
    parser = argparse.ArgumentParser(description="LLM NER (llm sloj) — type reconciliation")
    parser.add_argument("--knjiga", default="1", help="ID knjige ili 'all'")
    parser.add_argument("--force", action="store_true",
                        help="Prepiši i knjige koje već imaju llm sloj")
    parser.add_argument("--dry-run", action="store_true",
                        help="Samo ispisi LLM odluke, ne pisi u bazu")
    args = parser.parse_args()

    conn = get_conn()
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

    logger.info(f"bb_10_ner_llm — knjiga={args.knjiga} ({len(knjige)} knjiga), "
                f"force={args.force}, dry_run={args.dry_run}")

    obradjeno = preskoceno = 0
    for knjiga_id, knjiga_naziv in knjige:
        # llm sloj se izvodi IZ classic sloja — bez njega nema sirovine
        if broj_sloja(cur, knjiga_id, 'classic') == 0:
            logger.info(f"[{knjiga_id}] {knjiga_naziv}: nema classic sloj "
                        f"→ PRESKAČEM (pokreni bb_09 prvo)")
            preskoceno += 1
            continue

        postoji = broj_sloja(cur, knjiga_id, 'llm')
        if postoji and not args.force:
            logger.info(f"[{knjiga_id}] {knjiga_naziv}: llm sloj postoji "
                        f"({postoji} entiteta) → PRESKAČEM (--force za prepis)")
            preskoceno += 1
            continue

        logger.info(f"[{knjiga_id}] {knjiga_naziv}: obrađujem"
                    + (f" (prepisujem {postoji} entiteta)" if postoji else ""))
        obradi_knjigu(conn, cur, knjiga_id, knjiga_naziv, args.dry_run)
        obradjeno += 1

    logger.info(f"bb_10 gotov — obrađeno {obradjeno}, preskočeno {preskoceno}.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
