#!/usr/bin/env python3
"""
build_entity_aliases.py — Gradi finalni entity_aliases JSON za jednu knjigu.
Uzima LLM output, primjenjuje moje korekcije, generise finalni JSON.

Upotreba:
    venv/bin/python src/build_entity_aliases.py --book_id 1
"""
import os, json, argparse
from loguru import logger

# ─── MOJE KOREKCIJE za Hound of the Baskervilles (book_id=1) ─────────────────
# Format: raw_text -> (canonical, correct_label, role)
# Ovo prepisuje LLM output gdje je pogriješio

CORRECTIONS_BOOK1 = {
    # Villain alias — Stapleton koristi lažno ime Vandeleur
    "Vandeleur":              ("Stapleton", "PERSON", "villain_alias"),
    "Vandeleurs":             ("Stapleton", "PERSON", "villain_alias"),
    "Vandeleur's":            ("Stapleton", "PERSON", "villain_alias"),
    # Stapletonova žena — pravo ime Beryl Garcia
    "Beryl Garcia":           ("Beryl Stapleton", "PERSON", "accomplice"),
    "Miss Stapleton":         ("Beryl Stapleton", "PERSON", "accomplice"),
    "the Miss Stapleton":     ("Beryl Stapleton", "PERSON", "accomplice"),
    "Beryl":                  ("Beryl Stapleton", "PERSON", "accomplice"),
    # Stapleton pravi identitet
    "Rodger Baskerville":     ("Stapleton", "PERSON", "villain_alias"),
    "Jack":                   ("Stapleton", "PERSON", "villain_alias"),
    # Laura Lyons — bila manipulirana, accomplice ne red_herring
    "Laura Lyons":            ("Laura Lyons", "PERSON", "accomplice"),
    "Lyons":                  ("Laura Lyons", "PERSON", "accomplice"),
    "L. L.":                  ("Laura Lyons", "PERSON", "accomplice"),
    'L. L."':                 ("Laura Lyons", "PERSON", "accomplice"),
    # Frankland — susjed koji ometa, red_herring ne helper
    "Frankland":              ("Frankland", "PERSON", "red_herring"),
    "Frankland v.":           ("Frankland", "PERSON", "red_herring"),
    # Hugo Baskerville — historijski lik iz legende
    "Hugo Baskerville":       ("Hugo Baskerville", "PERSON", "other"),
    # Rodger/William/James Desmond — sporedni likovi
    "James Desmond":          ("James Desmond", "PERSON", "other"),
    "William Baskerville":    ("William Baskerville", "PERSON", "other"),
    # Mjesta — Lafter Hall je Franklandova kuća, ne Baskerville Hall
    "Lafter Hall":            ("Lafter Hall", "PLACE", "place_minor"),
    # Ispravka za Coombe Tracey — to je mjesto, ne osoba
    "Coombe Tracey":          ("Coombe Tracey", "PLACE", "place_key"),
    "Coombe":                 ("Coombe Tracey", "PLACE", "place_key"),
    # Mortimer je helper, ne više
    "Mortimer":               ("Mortimer", "PERSON", "helper"),
    "James Mortimer":         ("Mortimer", "PERSON", "helper"),
    "Dr. Mortimer":           ("Mortimer", "PERSON", "helper"),
    "Mortimers":              ("Mortimer", "PERSON", "helper"),
    # Cartwright — Holmesov mladi pomoćnik
    "Cartwright":             ("Cartwright", "PERSON", "helper"),
}

ROLE_ORDER = [
    "detective", "narrator", "villain", "villain_alias",
    "victim", "accomplice", "suspect", "red_herring",
    "helper", "other",
    "place_key", "place_minor",
    "organization", "noise"
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book_id", type=int, default=1)
    args = parser.parse_args()

    in_path = f"logs/entities_normalized_book{args.book_id}.json"
    if not os.path.exists(in_path):
        logger.error(f"Fajl ne postoji: {in_path}")
        return

    with open(in_path, encoding="utf-8") as f:
        llm_data = json.load(f)
    logger.info(f"Ucitano {len(llm_data)} entiteta iz LLM outputa")

    corrections = CORRECTIONS_BOOK1 if args.book_id == 1 else {}
    applied = 0
    final = []

    for e in llm_data:
        raw = e.get("raw", "")
        if raw in corrections:
            can, lbl, role = corrections[raw]
            final.append({
                "raw":           raw,
                "raw_label":     e.get("raw_label", ""),
                "canonical":     can,
                "correct_label": lbl,
                "role":          role,
                "source":        "manual_correction"
            })
            applied += 1
        else:
            e["source"] = "llm"
            final.append(e)

    # Dodaj entitete koji nisu bili u LLM outputu (novi iz corrections)
    existing_raws = {e["raw"] for e in llm_data}
    for raw, (can, lbl, role) in corrections.items():
        if raw not in existing_raws:
            final.append({
                "raw":           raw,
                "raw_label":     "UNKNOWN",
                "canonical":     can,
                "correct_label": lbl,
                "role":          role,
                "source":        "manual_addition"
            })

    logger.info(f"Primjenjeno {applied} korekcija")

    # Sortiraj po role redoslijedu pa po canonical
    def sort_key(e):
        role = e.get("role", "noise")
        idx = ROLE_ORDER.index(role) if role in ROLE_ORDER else len(ROLE_ORDER)
        return (idx, e.get("canonical", ""), e.get("raw", ""))

    final.sort(key=sort_key)

    # Sačuvaj
    out_path = f"logs/entity_aliases_book{args.book_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    logger.success(f"Sacuvano {len(final)} entiteta -> {out_path}")

    # Pregled po ulogama (bez noise)
    print("\n=== FINALNI PREGLED PO ULOGAMA ===")
    by_role = {}
    for e in final:
        if e.get("role") == "noise":
            continue
        role = e.get("role", "?")
        src  = "✎" if e.get("source") == "manual_correction" else ""
        by_role.setdefault(role, []).append(f"{e['raw']} → {e['canonical']}{src}")

    for role in ROLE_ORDER:
        if role in by_role and role != "noise":
            items = by_role[role]
            unique = sorted(set(items))
            print(f"\n  {role.upper()} ({len(unique)}):")
            for item in unique[:15]:
                print(f"    {item}")
            if len(unique) > 15:
                print(f"    ... (+{len(unique)-15} više)")

    # Statistika
    noise_cnt = sum(1 for e in final if e.get("role") == "noise")
    manual_cnt = sum(1 for e in final if e.get("source") == "manual_correction")
    print(f"\n  UKUPNO: {len(final)} | noise: {noise_cnt} | korekcija: {manual_cnt}")

if __name__ == "__main__":
    main()
