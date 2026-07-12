"""
bb_10c_docre.py
PRODUKCIJSKI DocRE — par-vodjena ekstrakcija usmjerenih relacija + drugi prolaz
(glm-5.2 klasifikacija iz zatvorene Massey liste) -> upis u bb_ner_relacije.

Prvi prolaz: kreni od parova entiteta (llm sloj), rangiranih po bliskim
susretima; za svaki par glm-5.2 daje JEDNU USMJERENU vezu + slobodni opis +
dokaz + pozicije + pouzdanost. (Nedirano od s129.)

Drugi prolaz (s131, Massey/Bamman taksonomija):
  - 29 fine kategorija cita se IZ BAZE (bb_ner_massey) — ne hardkod.
  - Klasifikacija se poziva SAMO za osoba-osoba parove (oba tipa PERSON) —
    deterministicki filter; Massey je striktno character-character taksonomija.
    Osoba-mjesto i ostali parovi: fine/afinitet/audit = NULL bez LLM poziva.
  - glm-5.2 (think:false, temp 0.0) bira fine iz zatvorene liste + afinitet
    (positive/negative/neutral). "ostalo" dozvoljen odgovor -> fine=NULL (ventil).
  - audit_kosinus: e5-large kosinus(opis, ime izabrane kategorije) — mjerni
    instrument, ne sudija (odluka s131 nakon cluster-probe dijagnostike).

--reklasifikuj: preskace prvi prolaz; cita postojece relacije knjige i
  UPDATE-uje samo fine/afinitet/audit_kosinus. Za migraciju postojecih podataka.

Upis: idempotentno (DELETE knjiga_id + INSERT). --knjiga N ili --knjiga all.
--dry-run: prvi prolaz + klasifikacija, ISPIS, NULA upisa.

Model: glm-5.2 (isti obrazac kao bb_10 / bb_09).
"""

import os, sys, json, time, argparse, requests, psycopg2
import numpy as np
from dotenv import load_dotenv
from loguru import logger
from sentence_transformers import SentenceTransformer

load_dotenv("/home/balsam/buchenberg/.env")

DB_HOST = os.getenv("DB_HOST"); DB_PORT = os.getenv("DB_PORT", 5432)
DB_USER = os.getenv("DB_USER"); DB_PASSWORD = os.getenv("DB_PASSWORD")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY = os.getenv("OLLAMA_API_KEY")

LLM_MODEL = "glm-5.2"
NER_METHOD = "llm"
EMBEDDER_PATH = "intfloat/multilingual-e5-large"


def get_conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER,
                            password=DB_PASSWORD, dbname="bb")


def ollama_call(prompt, temperature=0.0, max_retries=3, wait=30):
    headers = {"Content-Type": "application/json"}
    if OLLAMA_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_KEY}"
    payload = {"model": LLM_MODEL,
               "messages": [{"role": "user", "content": prompt}],
               "stream": False, "think": False,
               "options": {"temperature": temperature}}
    for attempt in range(max_retries):
        try:
            r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload,
                              headers=headers, timeout=180)
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except (requests.exceptions.HTTPError, requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                logger.warning(f"  Greska ({e}), cekam {wait}s ({attempt+1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise


# ---------------------------------------------------------------------------
# PRVI PROLAZ — par-vodjena ekstrakcija (iz probe bb_10b, nedirano)
# ---------------------------------------------------------------------------
def ucitaj_pozicije_entiteta(cur, knjiga_id, method):
    """{ime_norm: {'tip':.., 'id':.., 'poz':[sortirane pozicije]}}"""
    cur.execute("""
        SELECT e.ime_norm, e.tip, e.id, r.pozicija
        FROM bb_ner_recenica nr
        JOIN bb_recenice r     ON r.id=nr.recenica_id
        JOIN bb_ner_entiteti e ON e.id=nr.entitet_id
        WHERE e.knjiga_id=%s AND e.method=%s
        ORDER BY e.ime_norm, r.pozicija
    """, (knjiga_id, method))
    ent = {}
    for ime, tip, eid, poz in cur.fetchall():
        if ime not in ent:
            ent[ime] = {"tip": tip, "id": eid, "poz": []}
        ent[ime]["poz"].append(poz)
    return ent


def nadji_parove(ent, prozor, prag):
    imena = sorted(ent.keys())
    parovi = []
    for i in range(len(imena)):
        for j in range(i+1, len(imena)):
            a, b = imena[i], imena[j]
            pa, pb = ent[a]["poz"], ent[b]["poz"]
            susreti = []
            for x in pa:
                for y in pb:
                    if abs(x - y) <= prozor:
                        susreti.append((min(x, y), max(x, y)))
            if len(susreti) >= prag:
                parovi.append((a, b, susreti, len(susreti)))
    parovi.sort(key=lambda t: -t[3])
    return parovi


def ucitaj_recenice(cur, knjiga_id):
    cur.execute("SELECT pozicija, tekst FROM bb_recenice WHERE knjiga_id=%s", (knjiga_id,))
    return {p: t for p, t in cur.fetchall()}


def skupi_regione(susreti, recenice, prozor, max_regiona=4):
    intervali = sorted(set((max(1, lo - prozor), hi + prozor) for lo, hi in susreti))
    spojeni = []
    for od, do in intervali:
        if spojeni and od <= spojeni[-1][1] + 1:
            spojeni[-1] = (spojeni[-1][0], max(spojeni[-1][1], do))
        else:
            spojeni.append((od, do))
    spojeni = spojeni[:max_regiona]
    out = []
    for od, do in spojeni:
        linije = [f"[{p}] {recenice[p]}" for p in range(od, do+1) if p in recenice]
        if linije:
            out.append((od, do, "\n".join(linije)))
    return out


def sklopi_prompt(a, tip_a, b, tip_b, regioni):
    blokovi = "\n\n---\n\n".join(txt for _, _, txt in regioni)
    return f"""You are analyzing passages from a novel to determine the relationship between two named entities.

ENTITY A: {a} ({tip_a})
ENTITY B: {b} ({tip_b})

PASSAGES where they appear near each other (sentence position in brackets):

{blokovi}

TASK: Based ONLY on these passages, describe the DIRECTED relationship between
A and B. Direction matters: A -> B is different from B -> A. Choose the direction
the text supports (or note if it is mutual/symmetric).

Return ONLY a JSON object, no preamble, no markdown:
{{
  "izvor": "the source entity name (A or B, exactly as given)",
  "cilj": "the target entity name",
  "opis": "short free-text description in your own words (e.g. 'is the friend and colleague of', 'is investigating', 'owns')",
  "smjer": "directed" or "mutual",
  "dokaz": "a short quote from the passages supporting this",
  "poz": the sentence position number of the evidence,
  "pouzdanost": "high" / "medium" / "low"
}}

If the passages do NOT actually establish a relationship, return {{"opis": "none"}}."""


def parse_json_obj(raw):
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("```", 2)[1] if "```" in s else s
        if s.startswith("json"):
            s = s[4:]
        s = s.strip("` \n")
    i, j = s.find("{"), s.rfind("}")
    if i >= 0 and j > i:
        s = s[i:j+1]
    return json.loads(s)


# ---------------------------------------------------------------------------
# DRUGI PROLAZ (s131) — glm-5.2 klasifikacija iz zatvorene Massey liste
# ---------------------------------------------------------------------------
KLASIFIKACIONI_PROMPT = """You are classifying a relationship between two characters in a novel.

RELATIONSHIP (as extracted from the text): "{opis}"
SUPPORTING QUOTE: "{dokaz}"

Choose the SINGLE best matching category from this closed list:
{lista}

If NONE of the categories fits the relationship, answer with "ostalo".

Also determine the affinity of the relationship from the perspective of the text:
"positive", "negative", or "neutral".

Return ONLY a JSON object, no preamble, no markdown:
{{"fine": "...", "afinitet": "..."}}"""


def ucitaj_massey(cur):
    """29 fine kategorija iz baze — bb_ner_massey je izvor istine."""
    cur.execute("SELECT fine FROM bb_ner_massey ORDER BY fine")
    return [r[0] for r in cur.fetchall()]


def je_osoba_osoba(tip_a, tip_b):
    """Deterministicki filter: Massey klasifikacija samo za PERSON-PERSON parove."""
    return tip_a == "PERSON" and tip_b == "PERSON"


def klasifikuj_relaciju(opis, dokaz, fine_lista):
    """(fine|None, afinitet|None). 'ostalo' ili nepoznat odgovor -> fine=None."""
    prompt = KLASIFIKACIONI_PROMPT.format(
        opis=opis, dokaz=dokaz or "(no quote)",
        lista="\n".join(f"- {f}" for f in fine_lista))
    rel = parse_json_obj(ollama_call(prompt))
    fine = rel.get("fine"); afinitet = rel.get("afinitet")
    if fine == "ostalo" or fine not in fine_lista:
        fine = None
    if afinitet not in ("positive", "negative", "neutral"):
        afinitet = None
    return fine, afinitet


def audit_kos(embedder, opis, fine):
    """e5-large kosinus(opis, ime kategorije) — audit metrika, NULL uz NULL fine."""
    if fine is None:
        return None
    v = embedder.encode([opis, fine], show_progress_bar=False)
    va = np.asarray(v[0]); vb = np.asarray(v[1])
    na = np.linalg.norm(va); nb = np.linalg.norm(vb)
    if na > 0: va = va / na
    if nb > 0: vb = vb / nb
    return float(np.dot(va, vb))


# ---------------------------------------------------------------------------
# UPIS
# ---------------------------------------------------------------------------
def upisi_relacije(conn, knjiga_id, relacije):
    """idempotentno: DELETE knjiga_id + INSERT."""
    cur = conn.cursor()
    cur.execute("DELETE FROM bb_ner_relacije WHERE knjiga_id=%s", (knjiga_id,))
    for r in relacije:
        cur.execute("""
            INSERT INTO bb_ner_relacije
              (knjiga_id, izvor_id, cilj_id, opis, smjer, dokaz, dokaz_pozicije,
               pouzdanost, fine, afinitet, audit_kosinus)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (izvor_id, cilj_id) DO NOTHING
        """, (knjiga_id, r["izvor_id"], r["cilj_id"], r["opis"], r["smjer"],
              r.get("dokaz"), r.get("dokaz_pozicije"), r.get("pouzdanost"),
              r.get("fine"), r.get("afinitet"), r.get("audit_kosinus")))
    conn.commit()
    cur.close()


def obradi_knjigu(conn, embedder, fine_lista, knjiga_id, prag, prozor, dry_run):
    cur = conn.cursor()
    ent = ucitaj_pozicije_entiteta(cur, knjiga_id, NER_METHOD)
    recenice = ucitaj_recenice(cur, knjiga_id)
    cur.close()
    if not ent:
        logger.info(f"Knjiga {knjiga_id}: nema llm entiteta, preskacem.")
        return

    parovi = nadji_parove(ent, prozor, prag)
    logger.info(f"Knjiga {knjiga_id}: {len(ent)} entiteta, {len(parovi)} parova "
                f"(prag>={prag}, prozor+-{prozor})")

    relacije = []
    for n, (a, b, susreti, broj) in enumerate(parovi, 1):
        regioni = skupi_regione(susreti, recenice, prozor)
        prompt = sklopi_prompt(a, ent[a]["tip"], b, ent[b]["tip"], regioni)
        try:
            rel = parse_json_obj(ollama_call(prompt))
        except Exception as e:
            logger.warning(f"  PAR {n} {a}<->{b}: greska ({e}); preskacem")
            continue
        opis = rel.get("opis", "?")
        if opis == "none":
            continue
        izvor_ime = rel.get("izvor"); cilj_ime = rel.get("cilj")
        def _norm(v):
            if not v: return v
            v = v.split(" (")[0].strip()
            if v == "A": return a
            if v == "B": return b
            return v
        izvor_ime = _norm(izvor_ime); cilj_ime = _norm(cilj_ime)
        if izvor_ime not in ent or cilj_ime not in ent:
            logger.warning(f"  PAR {n}: izvor/cilj van para ({izvor_ime}->{cilj_ime}); preskacem")
            continue

        # DRUGI PROLAZ: Massey klasifikacija samo osoba-osoba (deterministicki filter)
        fine = afinitet = kos = None
        if je_osoba_osoba(ent[izvor_ime]["tip"], ent[cilj_ime]["tip"]):
            try:
                fine, afinitet = klasifikuj_relaciju(opis, rel.get("dokaz"), fine_lista)
                kos = audit_kos(embedder, opis, fine)
            except Exception as e:
                logger.warning(f"  PAR {n}: klasifikacija pukla ({e}); fine=NULL")

        relacije.append({
            "izvor_id": ent[izvor_ime]["id"], "cilj_id": ent[cilj_ime]["id"],
            "opis": opis, "smjer": rel.get("smjer", "directed"),
            "dokaz": rel.get("dokaz"),
            "dokaz_pozicije": [rel["poz"]] if isinstance(rel.get("poz"), int) else None,
            "pouzdanost": rel.get("pouzdanost") if rel.get("pouzdanost") in ("high","medium","low") else None,
            "fine": fine, "afinitet": afinitet, "audit_kosinus": kos,
        })

    if dry_run:
        print(f"\n{'='*70}\nDRY-RUN (knjiga {knjiga_id}) — klasifikacija, NULA upisa\n{'='*70}")
        for r in sorted(relacije, key=lambda x: (x["fine"] is None, x["fine"] or "", -(x["audit_kosinus"] or 0))):
            f = r["fine"] or "—(ventil/mjesto)"
            k = f"{r['audit_kosinus']:.3f}" if r["audit_kosinus"] is not None else "  —  "
            print(f"  {k}  [{f:<36s}|{(r['afinitet'] or '—'):<8s}] {r['opis'][:55]}")
        rasp = {}
        for r in relacije:
            key = r["fine"] or "NULL"
            rasp[key] = rasp.get(key, 0) + 1
        print(f"\n  Raspodjela fine: " + ", ".join(f"{g}:{c}" for g,c in sorted(rasp.items(), key=lambda x:-x[1])))
        print(f"  Ukupno relacija: {len(relacije)}")
    else:
        upisi_relacije(conn, knjiga_id, relacije)
        logger.info(f"  Upisano {len(relacije)} relacija za knjigu {knjiga_id}")


# ---------------------------------------------------------------------------
# REKLASIFIKACIJA — samo drugi prolaz nad postojecim relacijama (UPDATE)
# ---------------------------------------------------------------------------
def reklasifikuj_knjigu(conn, embedder, fine_lista, knjiga_id, dry_run):
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, r.opis, r.dokaz, ei.tip, ec.tip
        FROM bb_ner_relacije r
        JOIN bb_ner_entiteti ei ON ei.id = r.izvor_id
        JOIN bb_ner_entiteti ec ON ec.id = r.cilj_id
        WHERE r.knjiga_id=%s
        ORDER BY r.id
    """, (knjiga_id,))
    rows = cur.fetchall()
    if not rows:
        logger.info(f"[{knjiga_id}] nema relacija za reklasifikaciju, preskacem.")
        cur.close()
        return

    logger.info(f"[{knjiga_id}] reklasifikacija {len(rows)} relacija...")
    n_upd = n_pp = 0
    izvjestaj = []
    for rid, opis, dokaz, tip_a, tip_b in rows:
        fine = afinitet = kos = None
        if je_osoba_osoba(tip_a, tip_b):
            n_pp += 1
            try:
                fine, afinitet = klasifikuj_relaciju(opis, dokaz, fine_lista)
                kos = audit_kos(embedder, opis, fine)
            except Exception as e:
                logger.warning(f"  rel {rid}: klasifikacija pukla ({e}); fine=NULL")
        izvjestaj.append((rid, opis, fine, afinitet, kos))
        if not dry_run:
            cur.execute("""UPDATE bb_ner_relacije
                           SET fine=%s, afinitet=%s, audit_kosinus=%s WHERE id=%s""",
                        (fine, afinitet, kos, rid))
            n_upd += 1

    if dry_run:
        print(f"\n{'='*70}\nREKLASIFIKACIJA DRY-RUN (knjiga {knjiga_id}) — NULA upisa\n{'='*70}")
        for rid, opis, fine, afinitet, kos in sorted(izvjestaj, key=lambda x: (x[2] is None, x[2] or "", -(x[4] or 0))):
            f = fine or "—(ventil/mjesto)"
            k = f"{kos:.3f}" if kos is not None else "  —  "
            print(f"  {k}  [{f:<36s}|{(afinitet or '—'):<8s}] {opis[:55]}")
        rasp = {}
        for _, _, fine, _, _ in izvjestaj:
            rasp[fine or "NULL"] = rasp.get(fine or "NULL", 0) + 1
        print(f"\n  Raspodjela fine: " + ", ".join(f"{g}:{c}" for g,c in sorted(rasp.items(), key=lambda x:-x[1])))
        print(f"  Ukupno: {len(rows)} | osoba-osoba (klasifikovano): {n_pp}")
    else:
        conn.commit()
        logger.info(f"  [{knjiga_id}] azurirano {n_upd} relacija ({n_pp} klasifikovano LLM-om)")
    cur.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--knjiga", default="1", help="ID knjige ili 'all'")
    ap.add_argument("--prag", type=int, default=5)
    ap.add_argument("--prozor", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="Prepisi i knjige koje vec imaju relacije")
    ap.add_argument("--reklasifikuj", action="store_true",
                    help="Samo drugi prolaz nad postojecim relacijama (UPDATE)")
    args = ap.parse_args()

    logger.info(f"Ucitavam e5-large ({EMBEDDER_PATH})...")
    embedder = SentenceTransformer(EMBEDDER_PATH)

    conn = get_conn()
    cur = conn.cursor()
    fine_lista = ucitaj_massey(cur)
    logger.info(f"Massey kategorije iz baze: {len(fine_lista)}")

    if args.knjiga == "all":
        cur.execute("""SELECT DISTINCT knjiga_id FROM bb_ner_entiteti
                       WHERE method=%s ORDER BY knjiga_id""", (NER_METHOD,))
        knjige = [r[0] for r in cur.fetchall()]
    else:
        knjige = [int(args.knjiga)]

    logger.info(f"Knjige za obradu: {knjige} | model {LLM_MODEL} | "
                f"force={args.force} | dry_run={args.dry_run} | reklasifikuj={args.reklasifikuj}")

    obradjeno = preskoceno = 0
    for kid in knjige:
        if args.reklasifikuj:
            reklasifikuj_knjigu(conn, embedder, fine_lista, kid, args.dry_run)
            obradjeno += 1
            continue

        cur.execute("""SELECT COUNT(*) FROM bb_ner_entiteti
                       WHERE knjiga_id=%s AND method=%s""", (kid, NER_METHOD))
        if cur.fetchone()[0] == 0:
            logger.info(f"[{kid}] nema {NER_METHOD} sloj -> PRESKACEM (pokreni bb_10 prvo)")
            preskoceno += 1
            continue

        cur.execute("SELECT COUNT(*) FROM bb_ner_relacije WHERE knjiga_id=%s", (kid,))
        postoji = cur.fetchone()[0]
        if postoji and not args.force and not args.dry_run:
            logger.info(f"[{kid}] relacije postoje ({postoji}) -> PRESKACEM (--force za prepis)")
            preskoceno += 1
            continue

        obradi_knjigu(conn, embedder, fine_lista, kid, args.prag, args.prozor, args.dry_run)
        obradjeno += 1

    logger.info(f"bb_10c gotov — obradjeno {obradjeno}, preskoceno {preskoceno}.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
