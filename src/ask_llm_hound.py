#!/usr/bin/env python3
"""
ask_llm_hound.py — Pitamo 3 modela sta znaju o Hound of the Baskervilles.
Upotreba:
    venv/bin/python src/ask_llm_hound.py
"""
import os, json, requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
OLLAMA_KEY = os.getenv("OLLAMA_API_KEY", "")

MODELS = {
    "gemma3:12b":      "Gemma3 12b",
    "ministral-3:14b": "Ministral3 14b",
    "gemma4:31b":      "Gemma4 31b",
}

PROMPT = '''You are a literary analyst. Answer questions about "The Hound of the Baskervilles" by Arthur Conan Doyle.

Return ONLY valid JSON with exactly these keys (no markdown, no backticks, no explanation):
{
  "villain": "main villain name",
  "villain_alias": ["any false names or aliases used by the villain"],
  "detective": "detective name",
  "narrator": "narrator name",
  "victims": ["victims or intended victims"],
  "helpers": ["characters who help the detective"],
  "suspects": ["suspicious but innocent characters"],
  "accomplices": ["characters manipulated by the villain"],
  "red_herrings": ["characters that distract from real villain"],
  "setting": "main locations",
  "plot_summary": "one sentence",
  "name_variants": {"canonical_name": ["variant1","variant2"]}
}'''


def ask(model_id, model_name):
    logger.info(f"Pitam {model_name}...")
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            headers={"Authorization": f"Bearer {OLLAMA_KEY}",
                     "Content-Type": "application/json"},
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": PROMPT}],
                "options": {"temperature": 0.1},
                "stream": False
            },
            timeout=120
        )
        r.raise_for_status()
        content = r.json()["message"]["content"].strip()
        if content.startswith("```"):
            content = "\n".join(content.split("\n")[1:-1])
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "json_parse_failed", "raw": content[:300]}
    except Exception as e:
        return {"error": str(e)}


def main():
    results = {}
    for mid, mname in MODELS.items():
        results[mname] = ask(mid, mname)

    print("\n" + "="*65)
    print("STA MODELI ZNAJU O HOUND OF THE BASKERVILLES")
    print("="*65)
    for mname, data in results.items():
        print(f"\n{'─'*65}\nMODEL: {mname}\n{'─'*65}")
        if "error" in data:
            print(f"  GRESKA: {data['error']}")
            if "raw" in data:
                print(f"  Raw: {data['raw']}")
        else:
            for k, v in data.items():
                if isinstance(v, list):
                    print(f"  {k}: {', '.join(str(x) for x in v)}")
                elif isinstance(v, dict):
                    print(f"  {k}:")
                    for kk, vv in v.items():
                        vv_str = ', '.join(vv) if isinstance(vv, list) else str(vv)
                        print(f"    {kk}: {vv_str}")
                else:
                    print(f"  {k}: {v}")

    os.makedirs("logs", exist_ok=True)
    with open("logs/hound_llm_knowledge.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.success("Sacuvano u logs/hound_llm_knowledge.json")

if __name__ == "__main__":
    main()
