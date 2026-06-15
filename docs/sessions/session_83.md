# Session 83 — 15. jun 2026.

**Fokus:** Otkrivanje kritičnog buga — bb_sr_cirilica.py konvertuje i back_translation

---

## Checklist

- Project files pročitani (buchenberg_napomena.md, buchenberg_napomena_new.md, X-Ray SR/EN)
- README pročitan (V3, s82)
- Sessions 80–82 pročitane
- Health check: sve zeleno
  - 38.333 rečenica
  - 154.578 prevoda
  - 11.102 pobjednika
  - buchenberg: `11454d5` (s82) ✅
  - buchenweb: `fa82d9c` (s82) ✅

---

## Šta je otkriveno

### Kritični bug: bb_sr_cirilica.py konvertuje back_translation

`bb_sr_cirilica.py` ažurira **obje** kolone u `bb_prevodi_recenica`:

```python
cur.execute("""
    UPDATE bb_prevodi_recenica
    SET prevod = %s, back_translation = %s
    WHERE id = %s
""", (novi_prevod, novi_back, row_id))
```

`back_translation` je engleski tekst (back-translation na engleski). Skripta ga tretira kao srpski latinički tekst i transliterira ga u ćirilicu.

Rezultat: "The Hound of the Baskervilles" → "Тхе Хоунд оф тхе Баскервиллес"

Ovo direktno ruši **X-Ray prikaz u Readeru** — najvažniji dio projekta — koji prikazuje originalni EN tekst, prevod i back_translation zajedno.

### Obim problema

```sql
SELECT COUNT(*) FROM bb_prevodi_recenica pr
JOIN bb_prevodi_knjige pk ON pk.id = pr.prevodi_knjige_id
JOIN bb_jezik j ON j.id = pk.jezik_id
WHERE j.kod = 'sr' AND pr.back_translation IS NOT NULL;
```

**Rezultat: ~17.870–19.000 redova** (broj raste jer Flavio pušta nove prevode).

### Što NIJE oštećeno

- `score` i `translation_score` — računati u `bb_03_prevod.py`, **prije** ćirilizacije → ispravni
- `prevod` kolona — ispravno ćirilična, kako treba
- Sudija ocjene — sudija je ocjenjivala `prevod` (ćirilica), ne `back_translation` → ispravne

### Što JE oštećeno

- `back_translation` za sve srpske redove — engleski tekst transliteriran u ćirilicu → nečitljivo u X-Ray readeru

---

## Rješenje — skripta bb_sr_fix_backtr.py (još nije napisana)

### Princip

Reverz tablice je deterministički. Engleski tekst ne sadrži srpske dijakritike (š, ž, č, ć, đ, lj, nj, dž) pa nema ambiguitetnih slučajeva. Svaki ćirilični karakter iz srpske transliteracije mapira se nazad na tačno jedan latinski karakter.

### Zahtjevi

- Prima `--knjiga ID` kao obavezan parametar (Flavio će raditi fix knjiga po knjiga)
- Ima `--dry-run` mode (prikazuje prvih 10 primjera bez upisa)
- Detektuje koji redovi su zahvaćeni (is_cirilica funkcija)
- Primjenjuje reverz tablicu samo na `back_translation`, ne na `prevod`
- Upisuje nazad u bazu
- Prikazuje broj ažuriranih redova

### Reverz tablica (ćirilica → latinica)

Obrnuti redosljed od LAT_CIR tablice u bb_sr_cirilica.py — digrame (љ→lj, њ→nj, џ→dž, ђ→dj) treba obraditi PRIJE single karaktera:

```python
CIR_LAT = [
    ("љ", "lj"), ("Љ", "Lj"),
    ("њ", "nj"), ("Њ", "Nj"),
    ("џ", "dž"), ("Џ", "Dž"),
    ("ђ", "dj"), ("Ђ", "Dj"),
    ("ш", "š"),  ("Ш", "Š"),
    ("ж", "ž"),  ("Ж", "Ž"),
    ("č", "č"),  ("Ч", "Č"),
    ("ћ", "ć"),  ("Ћ", "Ć"),
    ("а", "a"),  ("А", "A"),
    ("б", "b"),  ("Б", "B"),
    ("ц", "c"),  ("Ц", "C"),
    ("д", "d"),  ("Д", "D"),
    ("е", "e"),  ("Е", "E"),
    ("ф", "f"),  ("Ф", "F"),
    ("г", "g"),  ("Г", "G"),
    ("х", "h"),  ("Х", "H"),
    ("и", "i"),  ("И", "I"),
    ("ј", "j"),  ("Ј", "J"),
    ("к", "k"),  ("К", "K"),
    ("л", "l"),  ("Л", "L"),
    ("м", "m"),  ("М", "M"),
    ("н", "n"),  ("Н", "N"),
    ("о", "o"),  ("О", "O"),
    ("п", "p"),  ("П", "P"),
    ("р", "r"),  ("Р", "R"),
    ("с", "s"),  ("С", "S"),
    ("т", "t"),  ("Т", "T"),
    ("у", "u"),  ("У", "U"),
    ("в", "v"),  ("В", "V"),
    ("з", "z"),  ("З", "Z"),
]
```

### Pažnja: 'w' i 'y' nisu u srpskoj latinici

Originalna LAT_CIR tablica ne sadrži 'w' i 'y' — srpska latinica ih nema. Engleski tekst sadrži 'w' i 'y' koji su prošli kroz transliteraciju **nepromijenjen** (nisu u tablici). Dakle u ćiriličnom back_translation ostaje latinično 'w' i 'y'. Reverz to ne treba dirati.

Primjer iz baze potvrđuje:
`"Wатсон"` — W ostaje latinično, 'atson' je ćirilično.

Ovo znači reverz će ispravno rekonstruirati originalni engleski tekst.

### Fix bb_sr_cirilica.py (nakon što se fix backtr završi)

Nakon fixa back_translation, treba i popraviti `bb_sr_cirilica.py` da ubuduće **ne dira** `back_translation`:

```python
# Umjesto:
cur.execute("""
    UPDATE bb_prevodi_recenica
    SET prevod = %s, back_translation = %s
    WHERE id = %s
""", (novi_prevod, novi_back, row_id))

# Treba biti:
cur.execute("""
    UPDATE bb_prevodi_recenica
    SET prevod = %s
    WHERE id = %s
""", (novi_prevod, row_id))
```

I ukloniti `novi_back` iz logike — `back_translation` se ne smije dirati.

---

## Redosljed popravke (za sljedeću sesiju)

1. **Napisati `bb_sr_fix_backtr.py`** — reverz ćirilica→latinica za `back_translation`, po knjizi
2. **Dry-run na knjiga 1 (Hound)** — provjera prvih 10 primjera
3. **Pokrenuti fix po knjigama** — `--knjiga 1`, `--knjiga 5`, itd.
4. **Verificirati u bazi** — sample check po knjizi
5. **Popraviti `bb_sr_cirilica.py`** — ukloniti ažuriranje `back_translation`
6. **bb_web_export.py** — ponovo exportati JSON za sve SR knjige
7. **Commitati** — buchenberg + buchenweb

---

## Stanje na kraju sesije

- Corpus: 38.333 rečenica / ~154.578+ prevoda / 11.102 pobjednika
- back_translation za SR: **oštećeno** (~17.870–19.000 redova) — engleski tekst je ćirilica
- buchenberg git: `11454d5` (s82) — session doc s83 pending
- buchenweb git: `fa82d9c` (s82) ✅
- BB_VERSION: s82

---

## Sljedeće (prioritetno)

1. **Fix back_translation** — napisati i pokrenuti `bb_sr_fix_backtr.py` po knjigama
2. **Fix bb_sr_cirilica.py** — ukloniti ažuriranje back_translation
3. **Pipeline nastavak** — hr/sr/it/de → s350; mk/bg → s51–s100

---

*Flavio & Claude · Buchenberg · Session 83 · 15. jun 2026.*
