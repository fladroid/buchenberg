#!/usr/bin/env python3
"""
ask_llm_entities.py — LLM normalizacija NER entiteta za jednu knjigu.

Upotreba:
    venv/bin/python src/ask_llm_entities.py --book_id 1
"""
import os, json, argparse, psycopg2, requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY = os.getenv("OLLAMA_API_KEY", "")
DB_HOST    = os.getenv("DB_HOST")
DB_PORT    = int(os.getenv("DB_PORT", 5432))
DB_NAME    = os.getenv("DB_NAME")
DB_USER    = os.getenv("DB_USER")
DB_PASS    = os.getenv("DB_PASSWORD")

MODEL = "gemma4:31b"

PROMPT_TEMPLATE = """You are a literary analyst with expert knowledge of classic English literature.

The following is a raw list of Named Entity Recognition (NER) results extracted by spaCy from the novel:
BOOK: "{title}" by {author}

spaCy makes mistakes — it sometimes labels people as places, places as organizations, etc.
Your task: for each raw entity, provide:
1. canonical_name: the correct, normalized name (e.g. "Holmes" for "Sherlock Holmes", "Mr. Holmes")
2. correct_label: the correct type — one of: PERSON, PLACE, ORGANIZATION, OTHER
3. role: narrative role — one of: detective, narrator, victim, villain, villain_alias, helper, suspect, accomplice, red_herring, place_key, place_minor, organization, noise
   - "noise" = NER error, not a real named entity (e.g. "yew hedge", "stealthy air", "meek")
   - "villain_alias" = false name used by the villain
   - "place_key" = important location in the story
   - "place_minor" = minor/incidental location

Raw entities (label, text, frequency):
{entity_list}

Return ONLY a valid JSON array, no markdown, no explanation:
[
  {{"raw": "Holmes", "raw_label": "PERSON", "canonical": "Holmes", "correct_label": "PERSON", "role": "detective"}},
  ...
]
"""

def get_entities(book_id):
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                            user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute("""
        SELECT ne.label, ne.text, COUNT(*) as cnt,
               b.title, b.author
        FROM named_entities ne
        JOIN sentences s ON ne.sentence_id = s.id
        JOIN books b ON s.book_id = b.id
        WHERE s.book_id = %s
        AND ne.label IN ('PERSON','GPE','LOC','FAC','ORG','NORP')
        GROUP BY ne.label, ne.text, b.title, b.author
        ORDER BY ne.label, cnt DESC
    """, (book_id,))
    rows = cur.fetchall()
    conn.close()
    title  = rows[0][3] if rows else "Unknown"
    author = rows[0][4] if rows else "Unknown"
    return rows, title, author

def ask_llm(entity_list_str, title, author):
    prompt = PROMPT_TEMPLATE.format(
        title=title, author=author, entity_list=entity_list_str
    )
    logger.info(f"Saljem {len(entity_list_str.splitlines())} entiteta modelu {MODEL}...")
    r = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_KEY}",
                 "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0.1},
            "stream": False
        },
        timeout=300
    )
    r.raise_for_status()
    content = r.json()["message"]["content"].strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])
    return json.loads(content)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book_id", type=int, default=1)
    args = parser.parse_args()

    rows, title, author = get_entities(args.book_id)
    logger.info(f"Knjiga: {title} by {author} — {len(rows)} jedinstvenih entiteta")

    # Formatiraj listu za prompt
    lines = [f"  {label}, \"{text}\", freq={cnt}" for label, text, cnt, _, _ in rows]
    entity_list_str = "\n".join(lines)

    # Sačuvaj sirovu listu
    os.makedirs("logs", exist_ok=True)
    with open(f"logs/entities_raw_book{args.book_id}.txt", "w") as f:
        f.write(entity_list_str)
    logger.info(f"Sirova lista sacuvana u logs/entities_raw_book{args.book_id}.txt")

    # Pitaj LLM
    try:
        result = ask_llm(entity_list_str, title, author)
        out_path = f"logs/entities_normalized_book{args.book_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.success(f"Normalizovano {len(result)} entiteta -> {out_path}")

        # Kratki pregled
        by_role = {}
        for e in result:
            role = e.get("role","?")
            by_role.setdefault(role, []).append(e.get("canonical","?"))

        print("\n=== PREGLED PO ULOGAMA ===")
        for role, names in sorted(by_role.items()):
            unique = sorted(set(names))
            print(f"  {role:20s}: {', '.join(unique[:10])}{' ...' if len(unique)>10 else ''}")

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        logger.debug(f"Raw: {r.text[:500]}")
    except Exception as e:
        logger.error(f"Greska: {e}")

if __name__ == "__main__":
    main()
