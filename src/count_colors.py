# src/count_colors.py
# Ulazni parametri: --test_id, --sent_from, --sent_to, --langs (opcionalno)

import argparse
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='Broji rečenice po boji za dati test')
    parser.add_argument('--test_id', required=True)
    parser.add_argument('--sent_from', type=int, required=True)
    parser.add_argument('--sent_to', type=int, required=True)
    parser.add_argument('--langs', nargs='+', default=None)
    args = parser.parse_args()

    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'), port=int(os.getenv('DB_PORT')),
        dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()

    lang_filter = ''
    params = [args.test_id, args.sent_from, args.sent_to]
    if args.langs:
        placeholders = ','.join(['%s'] * len(args.langs))
        lang_filter = f'AND target_lang IN ({placeholders})'
        params += args.langs

    cur.execute(f'''
        SELECT target_lang,
            SUM(CASE WHEN ms >= 0.90 THEN 1 ELSE 0 END) zelene,
            SUM(CASE WHEN ms >= 0.80 AND ms < 0.90 THEN 1 ELSE 0 END) zute,
            SUM(CASE WHEN ms < 0.80 THEN 1 ELSE 0 END) crvene,
            COUNT(*) ukupno
        FROM (
            SELECT target_lang, sentence_id, MAX(translation_score) ms
            FROM test_results
            WHERE test_id = %s
              AND sentence_id >= %s
              AND sentence_id <= %s
              {lang_filter}
            GROUP BY sentence_id, target_lang
        ) t
        GROUP BY target_lang
        ORDER BY target_lang
    ''', params)

    rows = cur.fetchall()
    if not rows:
        print("Nema rezultata.")
        conn.close()
        return

    print(f"\nTest: {args.test_id} | Rečenice: {args.sent_from}-{args.sent_to}")
    print(f"{'Lang':<6} {'🟢 Zelene':>10} {'🟡 Žute':>10} {'🔴 Crvene':>10} {'Ukupno':>8}")
    print("-" * 50)
    for row in rows:
        lang, z, y, r, u = row
        print(f"{lang:<6} {z:>10} {y:>10} {r:>10} {u:>8}")

    conn.close()

if __name__ == '__main__':
    main()
