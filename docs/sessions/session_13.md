# Session 13 — Buchenberg

**Datum:** 21. maj 2026.
**Autor:** Flavio & Claude

---

## Šta smo radili

Završili smo test_012 — trofazni pipeline za 6 jezika (bg, de, hr, it, nl, pt), 40 rečenica iz Hound of the Baskervilles.

### Redoslijed rada

1. Health check — infrastruktura OK, obrisan stari `run_test.py.bak`
2. Faza 3 (nllb + nllb_t05 za crvene) — svaki jezik posebno
3. GA za žute+crvene — svaki jezik posebno
4. ga_save_winners — upisano u test_results
5. Dodan novi skript `src/count_colors.py`

### Finalno stanje test_012

| Lang | 🟢 Zelene | 🟡 Žute | 🔴 Crvene |
|------|-----------|---------|-----------|
| BG   | 16        | 24      | 0 ✅      |
| DE   | 22        | 14      | 4         |
| HR   | 22        | 17      | 1         |
| IT   | 23        | 13      | 4         |
| NL   | 26        | 14      | 0 ✅      |
| PT   | 22        | 17      | 1         |

---

## Novo u ovoj sesiji

- `src/count_colors.py` — broji rečenice po boji, parametri: `--test_id`, `--sent_from`, `--sent_to`, `--langs`

---

## Problemi i zapažanja

**Paralelni GA za BG i HR** — pokrenuti istovremeno, ali Ollama Cloud (besplatni tier) dozvoljava samo jedan proces u jednom trenutku. Procesi su se međusobno koćili. Zaključak: GA pokretati serijalno, jedan jezik po jedan.

**Performanse GA** — 40 rečenica × 1 jezik ≈ 15-50 min ovisno o broju žutih+crvenih. Za produkcijsku skalu (700+ rečenica × više jezika) to su dani rada. Ovo je glavni otvoreni problem.

---

## Plan za sljedeću sesiju

### test_013 — performansniji GA

Isti algoritam, drugačiji "roditelji":
- **Izbaciti NLLB iz GA mutatora** — ostaviti ga samo u fazi 3
- **Koristiti oba LLM-a sa temperature=0.8** (gemma + ministral) kao jedine mutatore
- Ollama Cloud je brz — bez CPU bottlenecka

Hipoteza: isti ili bolji kvalitet, 2-3x brže.

### Ostalo
- Novi jezici: bs, sl, mk, af, es, ro
- Pipeline orchestrator — finalni prevod iz test_results
- multilingual-e5-large — testirati kao alternativu MiniLM

---

## Napomene za Claude

- `langs` je uvijek lista
- Paralelni GA samo ako plaćeni Ollama tier
- `count_colors.py` je kanonski način provjere stanja — ne inline upiti
- Protokol komandi nepregovoriv — prikaži, čekaj OK, izvrši
