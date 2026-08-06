# READ-ONLY sonda: mjeri raznolikost izlaza po temperaturi
import os, sys, json, requests, itertools, psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np

load_dotenv("/home/balsam/buchenberg/.env")
URL = os.getenv("OLLAMA_BASE_URL") + "/api/chat"
KEY = os.getenv("OLLAMA_API_KEY")
MODEL, JEZIK, TEMPS, PONAV = "mistral-large-3:675b", "Croatian", [0.1, 0.5, 0.8, 1.0], 3

conn = psycopg2.connect(host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT",5432)),
                        dbname="bb", user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"))
cur = conn.cursor()
cur.execute("SELECT pozicija, tekst FROM bb_recenice WHERE knjiga_id=12 AND pozicija BETWEEN 1401 AND 1410 "
            "AND length(tekst) BETWEEN 80 AND 220 ORDER BY pozicija LIMIT 5")
recenice = cur.fetchall(); conn.close()

def prevedi(tekst, temp):
    import time
    p = f"Translate the following English sentence into {JEZIK}. Output ONLY the translation.\n\n{tekst}"
    for pok in range(3):
        try:
            r = requests.post(URL, headers={"Authorization": f"Bearer {KEY}"}, timeout=180,
                json={"model": MODEL, "messages":[{"role":"user","content":p}], "stream": False,
                      "think": False, "options": {"temperature": temp}})
            return (r.json().get("message",{}).get("content") or "").strip()
        except Exception as e:
            print(f"    greska ({e}), pokusaj {pok+1}/3", flush=True)
            time.sleep(30)
    return ""

emb = SentenceTransformer("intfloat/multilingual-e5-large")
def cos(a, b):
    v = emb.encode([a, b], normalize_embeddings=True); return float(np.dot(v[0], v[1]))

unutar, izmedju, identicni = {t: [] for t in TEMPS}, {}, 0
for poz, tekst in recenice:
    izlazi = {t: [prevedi(tekst, t) for _ in range(PONAV)] for t in TEMPS}
    for t in TEMPS:
        for a, b in itertools.combinations(izlazi[t], 2):
            unutar[t].append(cos(a, b))
            if a == b: identicni += 1
    for t1, t2 in itertools.combinations(TEMPS, 2):
        izmedju.setdefault((t1,t2), []).append(cos(izlazi[t1][0], izlazi[t2][0]))
    print(f"  s{poz} gotovo", flush=True)

print("\n=== UNUTAR iste temperature (3 ponavljanja) ===")
for t in TEMPS:
    print(f"  temp {t}: prosj. kosinus {np.mean(unutar[t]):.4f}  (nize = vise varijacije)")
print("\n=== IZMEDJU temperatura (prvi izlaz svake) ===")
for (t1,t2), v in izmedju.items():
    print(f"  {t1} vs {t2}: {np.mean(v):.4f}")
print(f"\nIdenticnih parova unutar iste temp: {identicni}/{len(recenice)*len(TEMPS)*3}")
