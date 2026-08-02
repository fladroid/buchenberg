#!/usr/bin/env python3
"""
bb_deklarisi_svet.py — deklariše POTPUNO stanje a1 (model) i a2 (temperatura) za zadanu fazu.
NIJE relativni toggle: SVAKI poziv postavlja CIJELO stanje eksplicitno (sve navedeno=aktivno,
sve nenavedeno=ugašeno), bez oslanjanja na to šta je bilo prije poziva.

Upotreba:
  venv/bin/python src/bb_deklarisi_svet.py --faza 1 \
      --modeli "mistral-large-3:675b,nllb-600M,glm-5.2" \
      --temperature "0.8,0.1,0.0"
"""
import os, sys, argparse, psycopg2
from dotenv import load_dotenv

load_dotenv()
DB = {
    "host":     os.getenv("DB_HOST", "balsam.dynu.net"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   "bb",
    "user":     os.getenv("DB_USER", "pgu"),
    "password": os.getenv("DB_PASSWORD"),
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--faza", type=int, required=True)
    p.add_argument("--modeli", type=str, required=True,
                    help="zarezom odvojena lista naziva iz bb_modeli koji treba da budu AKTIVNI; sve ostalo se gasi")
    p.add_argument("--temperature", type=str, required=True,
                    help="zarezom odvojena lista vrijednosti iz bb_temperature koje treba da budu AKTIVNE; sve ostalo se gasi")
    args = p.parse_args()

    modeli = [m.strip() for m in args.modeli.split(",") if m.strip()]
    temps = [round(float(t.strip()), 4) for t in args.temperature.split(",") if t.strip()]

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    cur.execute("""
        UPDATE bb_faze_a1 a1
        SET aktivan = (m.naziv = ANY(%s))
        FROM bb_modeli m
        WHERE a1.model_id = m.id AND a1.faza_id = %s
    """, (modeli, args.faza))
    n1 = cur.rowcount

    cur.execute("""
        UPDATE bb_faze_a2 a2
        SET aktivan = (ROUND(t.vrijednost::numeric,4) = ANY(%s))
        FROM bb_temperature t
        WHERE a2.temperatura_id = t.id AND a2.faza_id = %s
    """, (temps, args.faza))
    n2 = cur.rowcount

    conn.commit()

    cur.execute("""
        SELECT m.naziv, a1.aktivan FROM bb_faze_a1 a1 JOIN bb_modeli m ON m.id=a1.model_id
        WHERE a1.faza_id=%s ORDER BY a1.aktivan DESC, m.naziv
    """, (args.faza,))
    print(f"bb_faze_a1 (faza={args.faza}), {n1} redova azurirano:")
    for naziv, aktivan in cur.fetchall():
        print(f"  {'AKTIVAN ' if aktivan else 'ugašen  '} {naziv}")

    cur.execute("""
        SELECT t.vrijednost, a2.aktivan FROM bb_faze_a2 a2 JOIN bb_temperature t ON t.id=a2.temperatura_id
        WHERE a2.faza_id=%s ORDER BY a2.aktivan DESC, t.vrijednost
    """, (args.faza,))
    print(f"bb_faze_a2 (faza={args.faza}), {n2} redova azurirano:")
    for vrijednost, aktivan in cur.fetchall():
        print(f"  {'AKTIVAN ' if aktivan else 'ugašen  '} {vrijednost}")

    conn.close()

if __name__ == "__main__":
    main()
