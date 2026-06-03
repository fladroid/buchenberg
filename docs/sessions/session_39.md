# Session 39 — Novi jezici, analiza temperatura, BS prevod

**Datum:** 3. jun 2026.
**Sesija:** 39
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Analiza temperatura i modela (s1–s80, 4 postojeća jezika)

Upitom u bazu analizirani pobjednici po modelu i temperaturi za hr, it, fr, de.

**Ključni zaključci:**
- Temperatura 0.5 praktično mrtva — samo DE ima par pobjeda, ostali 0. Može se izbaciti.
- `gemma3@0.8` dominira za germanske/sl jezike
- `ministral@0.1` dominira za romanske i sr
- HR je izuzetak — skoro izjednačeno

**Odluka:** zadržati obje temperature (0.1 i 0.8) za oba modela jer sudija bira između 4 kandidata i kvalitet je bolji nego sa 2.

### 2. Proširenje na 5 novih jezika: sr, sl, es, nl, af

Pokrenuti prevodi (gemma3@0.8, ministral@0.1, nllb@0) za s1–s80:
- Cloud (gemma3 + ministral serijski) + NLLB paralelno
- Sudija za svih 5 jezika
- Pobjednici za svih 5 jezika

**Distribucija pobjednika s1–s80:**

| Jezik | gemma3 0.8 | ministral 0.1 | nllb |
|-------|-----------|--------------|------|
| sr | 36 | 37 | 7 |
| sl | 50 | 22 | 8 |
| es | 32 | 39 | 9 |
| nl | 43 | 25 | 12 |
| af | 36 | 30 | 14 |

**Napomena:** Slovenački lingvistički nije germanski ali se ponaša slično germanskim jezicima po distribuciji temperatura.

Nakon pada aplikacije tokom sesije, sudija je nastavio raditi u pozadini (nohup). Pobjednici za sr su ponovo pokrenuti jer je 9 rečenica bilo bez sudija ocjene (fallback na kompozitni).

### 3. Mjerenje vremena — BS, 350 rečenica

Pokrenut test na bosanskom (bs), s1–s350, sa svim modelima:
- gemma3@0.8, gemma3@0.1, ministral@0.8, ministral@0.1 (cloud, serijski)
- nllb@0 (lokalno, paralelno)

**Trajanje po modelu (iz `created_at` u bazi):**

| Model | Trajanje |
|-------|---------|
| gemma3@0.8 | 22.5 min |
| gemma3@0.1 | 21.3 min |
| ministral@0.8 | 12.5 min |
| ministral@0.1 | 12.6 min |
| nllb@0 (paralelno) | 40.0 min |
| **Cloud ukupno** | **69.5 min** |

**Sudija (sa `nohup time`):** 13:59 min za 350 rečenica.

**Procjena za cijelu knjigu (3500 rečenica, 1 jezik):**
- Cloud: ~11.5h
- NLLB: ~6.7h (paralelno)
- Sudija: ~2.3h
- **Ukupno: ~14h**

### 4. Analiza pobjednika — BS

| Model | Temperatura | Pobjede | % |
|-------|-------------|---------|---|
| gemma3 | 0.1 | 105 | 30.0% |
| gemma3 | 0.8 | 90 | 25.7% |
| ministral | 0.1 | 68 | 19.4% |
| ministral | 0.8 | 61 | 17.4% |
| nllb | 0 | 26 | 7.4% |

**gemma3 dominira** (55.7%). Iznenađenje: za BS gemma3@0.1 pobjeđuje više od gemma3@0.8 — suprotno od germanskih jezika. BS se ponaša slično HR (gemma3 dominira), za razliku od SR (ministral izjednačen).

### 5. HR prevod s81–s350 pokrenut

Na kraju sesije pokrenuti prevodi za HR, s81–s350 (isti setup kao BS):
- Cloud: gemma3@0.8, gemma3@0.1, ministral@0.8, ministral@0.1 — PID 96680
- NLLB: PID 96691
- Sudija i pobjednici — sljedeća sesija

---

## ⚠️ Protokolarna greška — obavezno pročitati

**Greška:** Cloud i NLLB skripte za BS prevod pokrenute su sa `nohup` ali **bez `time`**.

**Posljedica:** Trajanje nije zabilježeno u logu. Morali smo koristiti `created_at` timestamps iz baze kao zamjenu.

**Ispravak:** Svaki duži run **mora** koristiti `nohup time` — trajanje mora biti vidljivo direktno u logu.

**Pravilo od sada:** `PYTHONUNBUFFERED=1 nohup time venv/bin/python ...` — bez izuzetka.

---

## Otvoreno za sljedeću sesiju

1. **HR s81–s350** — čeka završetak prevoda (pokrenuto), sudija + pobjednici
2. **Proširenje BS** — s351–s3852 (cijela knjiga)
3. **Proširenje HR** — s351–s3852
4. **Novi jezici** — bs, sl kompletni do s350; razmotriti sl, es, nl, af za s81–s350
5. **Export** — `bb_05_export.py` za bs i hr (s1–s350)
6. **Session dokument** — README update

---

## Git

- Commit: `session 39: novi jezici sr/sl/es/nl/af, BS prevod s1-350, HR s81-350 pokrenut, analiza temperatura`

