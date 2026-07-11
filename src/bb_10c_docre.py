"""
bb_10c_docre.py
PRODUKCIJSKI DocRE — par-vodjena ekstrakcija usmjerenih relacija + drugi prolaz
(e5-large embedding opisa -> najbliza fiksna grupa) -> upis u bb_ner_relacije.

Prvi prolaz: kao proba (bb_10b) — kreni od parova entiteta (llm sloj), rangiranih
po bliskim susretima; za svaki par glm-5.2 daje JEDNU USMJERENU vezu + slobodni
opis + dokaz + pozicije + pouzdanost.

Drugi prolaz: e5-large embedduje slobodni opis, poredi kosinusom s CENTROIDIMA
grupa (prosjek embeddinga seed-opisa po grupi iz bb_ner_tip_veze). Argmax grupa;
ako max kosinus < PRAG -> 'ostalo' (slobodni opis se cuva netaknut).

Konzistentnost: e5-large se poziva GOLIM .encode() (bez query:/passage: prefiksa),
isto kao bb_06_enkodiranje.py — da vektori budu uporedivi s korpusom.

Upis: idempotentno (DELETE knjiga_id + INSERT). --knjiga N ili --knjiga all.
--dry-run: prvi prolaz + mapiranje, ISPIS kosinus-rastojanja (kalibracija praga),
           NULA upisa.

Model: glm-5.2 (isti obrazac kao bb_10 / bb_03).
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
PRAG_OSTALO = 0.55   # PRETPOSTAVKA — kalibrisati kroz --dry-run prije prve produkcije

# ---------------------------------------------------------------------------
# SEED opisi po grupi (iz s129 probe, 75 opisa) — ulaz za centroide (varijanta b)
# Dopunjivo kad dodju druge knjige.
# ---------------------------------------------------------------------------
SEED_OPISI = {
  "srodstvo": [
    "is the uncle of", "is the nephew of", "is the older brother of",
    "is the son of", "is the distant cousin and heir of", "is the heir to",
    "is the same person as",
  ],
  "prijateljstvo": [
    "is the friend of", "is the companion of", "is the mutual friend of",
    "is a friend and acquaintance of",
    "is a fellow educated neighbor and acquaintance of",
    "is the friend, companion, and colleague of",
    "is the personal friend and medical attendant of",
  ],
  "angazman": [
    "is the client of", "seeks assistance from", "is the client of / is consulting",
    "wrote to and made an appointment with",
    "is a professional colleague and acquaintance of",
  ],
  "sluzba": [
    "is the butler of", "is the butler and servant of", "is the old manservant of",
    "is the caretaker and servant of", "worked as a house-surgeon at",
    "is a colleague and assistant of",
  ],
  "istraga": [
    "is investigating", "is investigating the death of",
    "is investigating and suspicious of", "is investigating and interviewing",
    "investigated the case and death of",
  ],
  "zastita": [
    "accompanies and protects on the journey to Devonshire",
    "requests Watson's company and help at Baskerville Hall, expressing gratitude to him",
  ],
  "prevara": [
    "manipulates and exerts complete influence over, promising to marry her",
    "unwittingly provided his old clothes to (via Barrymore), which Selden wore when he was killed by the hound meant for Henry",
    "helps in the escape of and communicates with",
  ],
  "susjedstvo": [
    "is a neighbor who wants Henry to stay at Baskerville Hall",
    "introduces himself to and converses with",
    "knows and describes as a respectable butler",
  ],
  "kretanje": [
    "visited", "visits", "travels to / is visiting", "intended to travel to",
    "visited / traveled to", "travels to and visits", "returned to after making his fortune abroad",
    "fled to and resided in", "fled to and lived in", "fled to", "intended to go to",
    "visited and investigated a case in", "visited and observed the scene of the crime in",
    "travels to and resides in", "arrived in and is currently located in", "is traveling to / is visiting",
  ],
  "prebivaliste": [
    "lives in", "is based in / lives in", "lives in / is associated with",
    "is located in and being followed in",
  ],
  "posjed": [
    "travels to and owns an estate in", "is the heir to the estate in",
    "travels to / is the heir to the estate in",
  ],
  "radnja": [
    "is the town where Holmes stayed while watching",
    "buys cigarettes from a tobacconist located on",
    "was in the habit of walking down every night before going to bed",
    "received a warning message made from words clipped from",
    "visited and observed the scene of the crime in",
  ],
}


def get_conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER,
                            password=DB_PASSWORD, dbname="bb")


def ollama_call(prompt, temperature=0.0, max_retries=3, wait=30):
    headers = {"Content-Type": "application/json"}
    if OLLAMA_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_KEY}"
    payload = {"model": LLM_MODEL,
               "messages": [{"role": "user", "content": prompt}],
               "stream": False, "options": {"temperature": temperature}}
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
# DRUGI PROLAZ — centroidi grupa + mapiranje opisa (e5-large, goli encode)
# ---------------------------------------------------------------------------
def izgradi_centroide(embedder):
    """{grupa: centroid_vektor(np, normalizovan)} iz SEED_OPISI."""
    centroidi = {}
    for grupa, opisi in SEED_OPISI.items():
        v = embedder.encode(opisi, show_progress_bar=False)
        c = np.asarray(v).mean(axis=0)
        n = np.linalg.norm(c)
        centroidi[grupa] = c / n if n > 0 else c
    return centroidi


def mapiraj_grupu(opis, embedder, centroidi, prag):
    """(grupa, najbolji_kosinus). Ispod praga -> 'ostalo'."""
    v = np.asarray(embedder.encode([opis], show_progress_bar=False)[0])
    nv = np.linalg.norm(v)
    if nv > 0:
        v = v / nv
    best_g, best_k = None, -1.0
    for g, c in centroidi.items():
        k = float(np.dot(v, c))
        if k > best_k:
            best_g, best_k = g, k
    if best_k < prag:
        return "ostalo", best_k
    return best_g, best_k


# ---------------------------------------------------------------------------
# UPIS
# ---------------------------------------------------------------------------
def upisi_relacije(conn, knjiga_id, relacije):
    """idempotentno: DELETE knjiga_id + INSERT. relacije = lista dict-ova."""
    cur = conn.cursor()
    cur.execute("DELETE FROM bb_ner_relacije WHERE knjiga_id=%s", (knjiga_id,))
    for r in relacije:
        cur.execute("""
            INSERT INTO bb_ner_relacije
              (knjiga_id, izvor_id, cilj_id, tip_veze, opis, smjer, dokaz, dokaz_pozicije, pouzdanost)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (izvor_id, cilj_id, tip_veze) DO NOTHING
        """, (knjiga_id, r["izvor_id"], r["cilj_id"], r["tip_veze"], r["opis"],
              r["smjer"], r.get("dokaz"), r.get("dokaz_pozicije"), r.get("pouzdanost")))
    conn.commit()
    cur.close()


def obradi_knjigu(conn, embedder, centroidi, knjiga_id, prag, prozor, prag_ostalo, dry_run):
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
    kalibracija = []  # (opis, grupa, kosinus) za dry-run
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
        grupa, kos = mapiraj_grupu(opis, embedder, centroidi, prag_ostalo)
        kalibracija.append((opis, grupa, kos))
        relacije.append({
            "izvor_id": ent[izvor_ime]["id"], "cilj_id": ent[cilj_ime]["id"],
            "tip_veze": grupa, "opis": opis,
            "smjer": rel.get("smjer", "directed"),
            "dokaz": rel.get("dokaz"),
            "dokaz_pozicije": [rel["poz"]] if isinstance(rel.get("poz"), int) else None,
            "pouzdanost": rel.get("pouzdanost") if rel.get("pouzdanost") in ("high","medium","low") else None,
        })

    if dry_run:
        print(f"\n{'='*70}\nKALIBRACIJA (knjiga {knjiga_id}) — opis -> grupa (kosinus), NULA upisa")
        print('='*70)
        for opis, grupa, kos in sorted(kalibracija, key=lambda x: x[2]):
            flag = "  <-- OSTALO" if grupa == "ostalo" else ""
            print(f"  {kos:.3f}  [{grupa:14s}] {opis[:60]}{flag}")
        rasp = {}
        for _, g, _ in kalibracija:
            rasp[g] = rasp.get(g, 0) + 1
        print(f"\n  Raspodjela grupa: " + ", ".join(f"{g}:{c}" for g,c in sorted(rasp.items(), key=lambda x:-x[1])))
        print(f"  Ukupno relacija: {len(kalibracija)} | prag_ostalo={prag_ostalo}")
    else:
        upisi_relacije(conn, knjiga_id, relacije)
        logger.info(f"  Upisano {len(relacije)} relacija za knjigu {knjiga_id}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--knjiga", default="1", help="ID knjige ili 'all'")
    ap.add_argument("--prag", type=int, default=5)
    ap.add_argument("--prozor", type=int, default=5)
    ap.add_argument("--prag-ostalo", type=float, default=PRAG_OSTALO)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    logger.info(f"Ucitavam e5-large ({EMBEDDER_PATH})...")
    embedder = SentenceTransformer(EMBEDDER_PATH)
    centroidi = izgradi_centroide(embedder)
    logger.info(f"Centroidi: {len(centroidi)} grupa")

    conn = get_conn()
    if args.knjiga == "all":
        cur = conn.cursor()
        cur.execute("""SELECT DISTINCT knjiga_id FROM bb_ner_entiteti
                       WHERE method=%s ORDER BY knjiga_id""", (NER_METHOD,))
        knjige = [r[0] for r in cur.fetchall()]
        cur.close()
    else:
        knjige = [int(args.knjiga)]

    logger.info(f"Knjige za obradu: {knjige} | model {LLM_MODEL} | dry_run={args.dry_run}")
    for kid in knjige:
        obradi_knjigu(conn, embedder, centroidi, kid, args.prag, args.prozor,
                      args.prag_ostalo, args.dry_run)
    conn.close()


if __name__ == "__main__":
    main()
