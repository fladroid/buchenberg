"""
bb_03_prevod.py
Prevodi rečenice, radi back-translation i računa cosine score.

Podržani engini:
  - Ollama Cloud (gemma3:12b, ministral-3:14b, gemma4:31b, ...)
  - NLLB-200 lokalno (nllb-600M) — deterministički beam search

Primjer (Ollama):
    venv/bin/python src/bb_03_prevod.py \
        --knjiga 1 --od 1 --do 40 \
        --model "gemma3:12b" --temp 0.8 \
        --embedder "paraphrase-multilingual-MiniLM-L12-v2" \
        --jezici hr it de

Primjer (NLLB):
    venv/bin/python src/bb_03_prevod.py \
        --knjiga 1 --od 1 --do 40 \
        --model "nllb-600M" \
        --embedder "paraphrase-multilingual-MiniLM-L12-v2" \
        --jezici hr fr it
"""

import os
import sys
import argparse
import requests
import psycopg2
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

DB = {
    "host":     os.getenv("DB_HOST", "balsam.dynu.net"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   "bb",
    "user":     os.getenv("DB_USER", "pgu"),
    "password": os.getenv("DB_PASSWORD"),
}

OLLAMA_URL  = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY  = os.getenv("OLLAMA_API_KEY", "")
BATCH_SIZE  = 20
REFINE_BATCH_SIZE = 5

# NLLB engine: "fp32" = HF transformers (default), "ct2" = CTranslate2 int8 (brze na CPU)
NLLB_ENGINE       = os.getenv("NLLB_ENGINE", "ct2").lower()
NLLB_CT2_DIR      = os.getenv("NLLB_CT2_DIR",
                              os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                           "models", "nllb-600M-ct2-int8"))
NLLB_CT2_BATCH    = int(os.getenv("NLLB_CT2_BATCH", "200"))
NLLB_CT2_MAXBATCH = int(os.getenv("NLLB_CT2_MAXBATCH", "14"))
NLLB_CT2_INTER    = int(os.getenv("NLLB_CT2_INTER", "4"))
NLLB_CT2_INTRA    = int(os.getenv("NLLB_CT2_INTRA", "1"))

# Mapping: naziv u bb_embeddings → HuggingFace model path
EMBEDDER_PATH_MAP = {
    "multilingual-e5-large": "intfloat/multilingual-e5-large",
    "paraphrase-multilingual-MiniLM-L12-v2": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
}

NLLB_MODEL_NAME = "facebook/nllb-200-distilled-600M"

NLLB_LANG_MAP = {
    "hr": "hrv_Latn",
    "sr": "srp_Cyrl",
    "bs": "bos_Latn",
    "sl": "slv_Latn",
    "mk": "mkd_Cyrl",
    "bg": "bul_Cyrl",
    "de": "deu_Latn",
    "nl": "nld_Latn",
    "af": "afr_Latn",
    "fr": "fra_Latn",
    "it": "ita_Latn",
    "es": "spa_Latn",
    "pt": "por_Latn",
    "ro": "ron_Latn",
}

JEZIK_NAZIVI = {
    "hr": "Croatian",
    "sr": "Serbian",
    "bs": "Bosnian",
    "sl": "Slovenian",
    "mk": "Macedonian",
    "bg": "Bulgarian",
    "de": "German",
    "nl": "Dutch",
    "af": "Afrikaans",
    "fr": "French",
    "it": "Italian",
    "es": "Spanish",
    "pt": "Portuguese",
    "ro": "Romanian",
}


# ── NLLB ────────────────────────────────────────────────────────────────────

def load_nllb():
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL_NAME)
    if NLLB_ENGINE == "ct2":
        import ctranslate2
        print(f"Učitavam NLLB (CTranslate2 int8): {NLLB_CT2_DIR}")
        model = ctranslate2.Translator(NLLB_CT2_DIR, device="cpu",
                                       intra_threads=NLLB_CT2_INTRA,
                                       inter_threads=NLLB_CT2_INTER,
                                       compute_type="int8")
    else:
        from transformers import AutoModelForSeq2SeqLM
        print(f"Učitavam NLLB (FP32 HF): {NLLB_MODEL_NAME}")
        model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL_NAME)
    return tokenizer, model


def _nllb_batch_ct2(texts, tokenizer, translator, src_lang, tgt_lang):
    tokenizer.src_lang = src_lang
    src = [tokenizer.convert_ids_to_tokens(tokenizer.encode(t)) for t in texts]
    res = translator.translate_batch(
        src,
        target_prefix=[[tgt_lang]] * len(texts),
        beam_size=1,
        repetition_penalty=1.3,
        max_decoding_length=512,
        max_batch_size=NLLB_CT2_MAXBATCH,
    )
    out = []
    for r in res:
        h = r.hypotheses[0]
        if h and h[0] == tgt_lang:
            h = h[1:]
        out.append(tokenizer.decode(tokenizer.convert_tokens_to_ids(h), skip_special_tokens=True))
    return out


def nllb_batch(texts, tokenizer, model, src_lang, tgt_lang):
    if NLLB_ENGINE == "ct2":
        return _nllb_batch_ct2(texts, tokenizer, model, src_lang, tgt_lang)
    tokenizer.src_lang = src_lang
    inputs = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    )
    generated = model.generate(
        **inputs,
        forced_bos_token_id=tokenizer.convert_tokens_to_ids(tgt_lang),
        max_length=512,
        repetition_penalty=1.3,
        do_sample=False,
    )
    return tokenizer.batch_decode(generated, skip_special_tokens=True)


def nllb_single(text, tokenizer, model, src_lang, tgt_lang):
    return nllb_batch([text], tokenizer, model, src_lang, tgt_lang)[0]


# ── Ollama ──────────────────────────────────────────────────────────────────

def ollama_chat(model, temperature, messages, max_retries=3, wait=30):
    import time
    headers = {"Content-Type": "application/json"}
    if OLLAMA_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_KEY}"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    for attempt in range(max_retries):
        try:
            r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, headers=headers, timeout=120)
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except (requests.exceptions.HTTPError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                print(f"  Greška ({e}), čekam {wait}s pa ponavljam (pokušaj {attempt+1}/{max_retries})...", flush=True)
                time.sleep(wait)
            else:
                raise


def prevedi_batch(tekstovi, jezik_naziv, model, temp, tpl):
    numerirani = "\n".join(f"{i+1}. {t}" for i, t in enumerate(tekstovi))
    prompt = tpl.format(jezik_naziv=jezik_naziv, numerirani=numerirani)
    try:
        odgovor = ollama_chat(model, temp, [{"role": "user", "content": prompt}])
        linije = [l.strip() for l in odgovor.splitlines() if l.strip()]
        prevodi = []
        for l in linije:
            if l and l[0].isdigit() and ". " in l:
                prevodi.append(l.split(". ", 1)[1].strip())
            else:
                prevodi.append(l)
        if len(prevodi) == len(tekstovi):
            return prevodi
        return None
    except Exception as e:
        print(f"  [batch error] {e}")
        return None


def prevedi_single(tekst, jezik_naziv, model, temp, tpl):
    prompt = tpl.format(jezik_naziv=jezik_naziv, tekst=tekst)
    return ollama_chat(model, temp, [{"role": "user", "content": prompt}])


def back_prevedi_batch(prevodi, jezik_naziv, model, temp, tpl):
    numerirani = "\n".join(f"{i+1}. {t}" for i, t in enumerate(prevodi))
    prompt = tpl.format(jezik_naziv=jezik_naziv, numerirani=numerirani)
    try:
        odgovor = ollama_chat(model, temp, [{"role": "user", "content": prompt}])
        linije = [l.strip() for l in odgovor.splitlines() if l.strip()]
        rezultati = []
        for l in linije:
            if l and l[0].isdigit() and ". " in l:
                rezultati.append(l.split(". ", 1)[1].strip())
            else:
                rezultati.append(l)
        if len(rezultati) == len(prevodi):
            return rezultati
        return None
    except Exception as e:
        print(f"  [batch error] {e}")
        return None


def back_prevedi_single(prevod, jezik_naziv, model, temp, tpl):
    prompt = tpl.format(jezik_naziv=jezik_naziv, prevod=prevod)
    return ollama_chat(model, temp, [{"role": "user", "content": prompt}])


# ── Embeddings & score ──────────────────────────────────────────────────────

def cosine(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# ── DB helpers ──────────────────────────────────────────────────────────────

def get_or_create_prevodi_knjige(cur, knjiga_id, jezik_id, faza_id, model_id, temperatura_id, prompt_id, embeddings_id, runda):
    cur.execute("""
        INSERT INTO bb_prevodi_knjige (knjiga_id, jezik_id, faza_id, model_id, temperatura_id, prompt_id, embeddings_id, runda)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (knjiga_id, jezik_id, faza_id, model_id, temperatura_id, prompt_id, embeddings_id, runda) DO NOTHING
        RETURNING id
    """, (knjiga_id, jezik_id, faza_id, model_id, temperatura_id, prompt_id, embeddings_id, runda))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("""
        SELECT id FROM bb_prevodi_knjige
        WHERE knjiga_id=%s AND jezik_id=%s AND faza_id=%s AND model_id=%s AND temperatura_id=%s AND prompt_id=%s AND embeddings_id=%s AND runda=%s
    """, (knjiga_id, jezik_id, faza_id, model_id, temperatura_id, prompt_id, embeddings_id, runda))
    return cur.fetchone()[0]


def get_recenice(cur, knjiga_id, od, do):
    cur.execute("""
        SELECT id, pozicija, tekst FROM bb_recenice
        WHERE knjiga_id = %s AND pozicija BETWEEN %s AND %s
        ORDER BY pozicija
    """, (knjiga_id, od, do))
    return cur.fetchall()


def already_done(cur, prevodi_knjige_id, recenica_id):
    cur.execute("""
        SELECT 1 FROM bb_prevodi_recenica
        WHERE prevodi_knjige_id = %s AND recenica_id = %s
    """, (prevodi_knjige_id, recenica_id))
    return cur.fetchone() is not None


def upisi_prevod(cur, prevodi_knjige_id, recenica_id, prevod, back_translation, score, translation_score):
    cur.execute("""
        INSERT INTO bb_prevodi_recenica
            (prevodi_knjige_id, recenica_id, prevod, back_translation, score, translation_score)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (prevodi_knjige_id, recenica_id) DO NOTHING
    """, (prevodi_knjige_id, recenica_id, prevod, back_translation, score, translation_score))


def prevedi_refine_batch(parovi, jezik_naziv, model, temp, tpl):
    numerirani = "\n".join(
        f"{i+1}. English: {t}\n   Reference {jezik_naziv}: {seed}"
        for i, (t, seed) in enumerate(parovi)
    )
    prompt = tpl.format(jezik_naziv=jezik_naziv, numerirani=numerirani)
    try:
        odgovor = ollama_chat(model, temp, [{"role": "user", "content": prompt}])
        linije = [l.strip() for l in odgovor.splitlines() if l.strip()]
        prevodi = []
        for l in linije:
            if l and l[0].isdigit() and ". " in l:
                prevodi.append(l.split(". ", 1)[1].strip())
            else:
                prevodi.append(l)
        if len(prevodi) == len(parovi):
            return prevodi
        return None
    except Exception as e:
        print(f"  [refine batch error] {e}")
        return None


def prevedi_refine_single(tekst, jezik_naziv, model, temp, seed, tpl):
    prompt = tpl.format(jezik_naziv=jezik_naziv, tekst=tekst, seed=seed)
    return ollama_chat(model, temp, [{"role": "user", "content": prompt}])


def get_seed_map(cur, kod, rids):
    if not rids:
        return {}
    cur.execute("""
        SELECT recenica_id, prevod, finalni_score
        FROM v_pobjednici_full
        WHERE recenica_id = ANY(%s) AND jezik_kod = %s
    """, (rids, kod))
    return {r[0]: (r[1], r[2]) for r in cur.fetchall()}


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    import functools
    global print
    print = functools.partial(print, flush=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--knjiga",   type=int,   required=True)
    parser.add_argument("--od",       type=int,   required=True)
    parser.add_argument("--do",       type=int,   required=True)
    parser.add_argument("--model",    type=str,   required=True)
    parser.add_argument("--temp",     type=float, nargs="+", default=[0.0])
    parser.add_argument("--embedder", type=str,   required=True)
    parser.add_argument("--jezici",   type=str,   nargs="+", required=True)
    parser.add_argument("--faza", type=int, default=1,
                        help="Faza pipeline-a (1=base, 2+=refine: pobjednik kao hint)")
    parser.add_argument("--prag", type=float, default=0.95,
                        help="Prag finalni_score seeda ispod kojeg se refine pokusava (samo faza 2+)")
    parser.add_argument("--runda", type=int, default=1,
                        help="Runda ponavljanja iste konfiguracije (faza/model/temp/prompt) - default 1")
    parser.add_argument("--uradi-ako-nema", action="store_true", default=False,
                        help="Label u logu: namjeran nastavak/dovrsavanje raspona (already_done()+prag logika se ne mijenja)")
    args = parser.parse_args()

    is_nllb = (args.model == "nllb-600M")
    is_refine = args.faza >= 2
    ollama_naziv = args.model

    embedder_path = EMBEDDER_PATH_MAP.get(args.embedder, args.embedder)
    print(f"Učitavam embedder: {args.embedder} ({embedder_path})")
    embedder = SentenceTransformer(embedder_path)

    nllb_tok, nllb_mod = (None, None)
    if is_nllb:
        nllb_tok, nllb_mod = load_nllb()

    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    cur.execute("SELECT id FROM bb_embeddings WHERE naziv=%s", (args.embedder,))
    row = cur.fetchone()
    if not row:
        print(f"Embedder '{args.embedder}' nije u bb_embeddings!")
        sys.exit(1)
    embeddings_id = row[0]

    # a3: aktivni prompt za ovu fazu (base ili refine) — čita se JEDNOM za cijeli run
    cur.execute("""
        SELECT p.naziv, p.prompt_prevod_batch, p.prompt_prevod_single, p.prompt_back_batch, p.prompt_back_single
        FROM bb_faze_a3 a3
        JOIN bb_promptovi p ON a3.prompt_id = p.id
        WHERE a3.faza_id = %s AND a3.aktivan
    """, (args.faza,))
    prow = cur.fetchone()
    if not prow:
        print(f"Nema aktivnog prompta (a3) za fazu {args.faza}!")
        sys.exit(1)
    PROMPT_NAZIV, TPL_PREVOD_BATCH, TPL_PREVOD_SINGLE, TPL_BACK_BATCH, TPL_BACK_SINGLE = prow

    recenice = get_recenice(cur, args.knjiga, args.od, args.do)
    print(f"Rečenica za obradu: {len(recenice)} (pozicije {args.od}–{args.do})")
    if args.uradi_ako_nema:
        print("REZIM: --uradi-ako-nema (namjeran nastavak/dovrsavanje raspona; logika already_done()+prag nepromijenjena)")

    for temp in args.temp:
        cur.execute("""
            SELECT m.id, t.id, p.id
            FROM bb_modeli m, bb_temperature t, bb_promptovi p
            WHERE m.naziv = %s
              AND ROUND(t.vrijednost::numeric,4) = ROUND(%s::numeric,4)
              AND EXISTS (SELECT 1 FROM bb_faze_a1 a1 WHERE a1.faza_id=%s AND a1.model_id=m.id AND a1.aktivan)
              AND EXISTS (SELECT 1 FROM bb_faze_a2 a2 WHERE a2.faza_id=%s AND a2.temperatura_id=t.id AND a2.aktivan)
              AND EXISTS (SELECT 1 FROM bb_faze_a3 a3 WHERE a3.faza_id=%s AND a3.prompt_id=p.id AND a3.aktivan)
        """, (args.model, temp, args.faza, args.faza, args.faza))
        row = cur.fetchone()
        if not row:
            print(f"Model '{args.model}' temp={temp} faza={args.faza} nije aktivna kombinacija! Preskačem.")
            continue
        model_id, temperatura_id, prompt_id = row

        engine = "NLLB" if is_nllb else "Ollama"
        print(f"\n═══ Model: {args.model} | temp: {temp} | engine: {engine} | prompt: {PROMPT_NAZIV} | runda: {args.runda} ═══")

        for kod in args.jezici:
            jezik_naziv = JEZIK_NAZIVI.get(kod)
            if not jezik_naziv:
                print(f"Nepoznat jezik: {kod}, preskačem.")
                continue

            if is_nllb and kod not in NLLB_LANG_MAP:
                print(f"NLLB ne podržava jezik: {kod}, preskačem.")
                continue

            cur.execute("SELECT id FROM bb_jezik WHERE kod=%s", (kod,))
            jezik_id = cur.fetchone()[0]

            prevodi_knjige_id = get_or_create_prevodi_knjige(
                cur, args.knjiga, jezik_id, args.faza, model_id, temperatura_id, prompt_id, embeddings_id, args.runda
            )
            conn.commit()

            print(f"\n── Jezik: {kod} ({jezik_naziv}), prevodi_knjige_id={prevodi_knjige_id} ──")

            todo = [(rid, poz, tekst) for rid, poz, tekst in recenice
                    if not already_done(cur, prevodi_knjige_id, rid)]
            print(f"  Preostalo: {len(todo)} rečenica")

            seed_map = {}
            uses_seed = is_refine and PROMPT_NAZIV != 'base'
            if is_refine:
                seed_map = get_seed_map(cur, kod, [rid for rid, _, _ in todo])
                pre_seed = len(todo)
                todo = [x for x in todo if x[0] in seed_map]
                pre_prag = len(todo)
                bez_ocjene = [x for x in todo if seed_map[x[0]][1] is None]
                if bez_ocjene:
                    poz = ", ".join(str(p) for _, p, _ in bez_ocjene[:20])
                    if len(bez_ocjene) > 20:
                        poz += f" ... (+{len(bez_ocjene) - 20})"
                    print(f"  PREKID: {len(bez_ocjene)} pobjednika bez sudijine ocjene (jezik {kod})")
                    print(f"    Pozicije: {poz}")
                    print(f"    Stanje: nijedan prevod nije napravljen, baza netaknuta.")
                    print(f"    Rjesenje: pokreni sudiju za ovaj opseg, pa ponovi ovaj isti poziv:")
                    print(f"      venv/bin/python src/bb_08_sudija.py --knjiga {args.knjiga} "
                          f"--od {args.od} --do {args.do} --jezici {kod}")
                    sys.exit(3)
                todo = [x for x in todo if seed_map[x[0]][1] < args.prag]
                seed_oznaka = "sa seedom" if uses_seed else "bez seeda"
                print(f"  Refine: {pre_seed} {seed_oznaka} -> {pre_prag}; ispod praga {args.prag}: {len(todo)} (preskoceno {pre_prag - len(todo)})")

            step = NLLB_CT2_BATCH if (is_nllb and NLLB_ENGINE == "ct2") else (REFINE_BATCH_SIZE if uses_seed else BATCH_SIZE)
            for i in range(0, len(todo), step):
                chunk = todo[i:i + step]
                tekstovi = [t for _, _, t in chunk]

                print(f"  Batch {i//step + 1}: pozicije {chunk[0][1]}–{chunk[-1][1]}")

                if is_nllb:
                    nllb_tgt = NLLB_LANG_MAP[kod]
                    prevodi = nllb_batch(tekstovi, nllb_tok, nllb_mod, "eng_Latn", nllb_tgt)
                    backs   = nllb_batch(prevodi,  nllb_tok, nllb_mod, nllb_tgt, "eng_Latn")
                elif is_refine and PROMPT_NAZIV != 'base':
                    parovi = [(t, seed_map[rid][0]) for rid, poz, t in chunk]
                    prevodi = prevedi_refine_batch(parovi, jezik_naziv, ollama_naziv, temp, TPL_PREVOD_BATCH)
                    if prevodi is None:
                        print("    Fallback na single refine...")
                        prevodi = [prevedi_refine_single(t, jezik_naziv, ollama_naziv, temp, seed_map[rid][0], TPL_PREVOD_SINGLE)
                                   for rid, poz, t in chunk]

                    backs = back_prevedi_batch(prevodi, jezik_naziv, ollama_naziv, temp, TPL_BACK_BATCH)
                    if backs is None:
                        print("    Fallback na single back-translation...")
                        backs = [back_prevedi_single(p, jezik_naziv, ollama_naziv, temp, TPL_BACK_SINGLE)
                                 for p in prevodi]
                else:
                    prevodi = prevedi_batch(tekstovi, jezik_naziv, args.model, temp, TPL_PREVOD_BATCH)
                    if prevodi is None:
                        print("    Fallback na single prevod...")
                        prevodi = [prevedi_single(t, jezik_naziv, args.model, temp, TPL_PREVOD_SINGLE)
                                   for t in tekstovi]

                    backs = back_prevedi_batch(prevodi, jezik_naziv, args.model, temp, TPL_BACK_BATCH)
                    if backs is None:
                        print("    Fallback na single back-translation...")
                        backs = [back_prevedi_single(p, jezik_naziv, args.model, temp, TPL_BACK_SINGLE)
                                 for p in prevodi]

                en_vektori     = embedder.encode(tekstovi)
                back_vektori   = embedder.encode(backs)
                prevod_vektori = embedder.encode(prevodi)

                for j, (rid, poz, tekst) in enumerate(chunk):
                    score             = cosine(en_vektori[j], back_vektori[j])
                    translation_score = cosine(en_vektori[j], prevod_vektori[j])
                    upisi_prevod(cur, prevodi_knjige_id, rid,
                                 prevodi[j], backs[j], score, translation_score)
                    print(f"    s{poz}: score={score:.4f} ts={translation_score:.4f}")

                conn.commit()

            print(f"  Jezik {kod} gotov.")

            cur.execute("""
                SELECT COUNT(DISTINCT pr.recenica_id)
                FROM bb_prevodi_recenica pr
                JOIN bb_recenice r ON pr.recenica_id = r.id
                WHERE pr.prevodi_knjige_id = %s AND r.pozicija BETWEEN %s AND %s
            """, (prevodi_knjige_id, args.od, args.do))
            stvarno = cur.fetchone()[0]
            ocekivano = args.do - args.od + 1
            if stvarno == ocekivano:
                print(f"  ✅ Provjera opsega [{args.od}-{args.do}]: {stvarno}/{ocekivano} OK")
            else:
                print(f"  ❌ Provjera opsega [{args.od}-{args.do}]: {stvarno}/{ocekivano} — nedostaje {ocekivano - stvarno}")

    cur.close()
    conn.close()
    print("\nGotovo.")


if __name__ == "__main__":
    main()
