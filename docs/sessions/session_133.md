# Sesija 133 — NER ZAVRŠEN: tri metoda potvrđena, exporti i stranica Entiteti kompletirani

**Datum:** 13. jul 2026.
**Fokus:** Flaviova odluka — zatvoriti NER liniju. Provjeriti šta od tri metoda radi
tehnički; prihvatiti rezultat nezavisno od subjektivne procjene; kompletirati export
skripte; završiti stranicu Entiteti.
**Ishod:** Sva tri metoda rade. DocRE proširen na knjige <2000 rečenica. Web usklađen
s Massey shemom (stajao razdvojen od s131). Oba exporta pokrenuta. BB_VERSION s129.4 → s133.

---

## 1. Okvir sesije (Flavio)

> "Ono što ne radi ne radimo."

Kriterij prihvatanja je **tehnički**: skripta se izvršava, upisuje potpun sloj, sloj je
izvoziv u web. Kvalitet klasifikacije NIJE kriterij — on je **nalaz**.

**Odluka o obimu:** sve što se proba/testira radi se **samo na knjigama <2000 rečenica**.
Velike knjige (Big Four, Frankenstein, Moby Dick, R&J, Dracula) idu sekvencijalno kad
bude resursa — to je pokretanje, ne razvoj.

## 2. Stanje slojeva na početku

| sloj | pokrivenost |
|---|---|
| classic (bb_09) | svih 9 originalnih knjiga ✅ |
| llm (bb_10) | svih 9 originalnih knjiga ✅ |
| DocRE (bb_10c) | samo Hound (78) + Alice (60) |

DocRE je bio jedini neprovjeren metod.

## 3. DocRE — proširen na knjige <2000

| knjiga | parova | trajanje | relacija |
|---|---|---|---|
| J&H (19) | 24 | **1:15** | 23 |
| Flatland (21) | 107 | **4:05** | 101 |

Trajanja **daleko ispod s130 procjene** (~28 min/knjiga): tamo je mjeren prvi prolaz s
velikim promptovima; s131 sitni promptovi po relaciji su drugi prolaz učinili jeftinim.

**Greška u procesu (moja):** oba procesa pokrenuta jednom komandom s `&` + `&&` lancem
→ drugi `nohup` nikad nije startovao, tiho, bez loga.
**Pravilo: jedan `nohup` po komandi; nikad `&& echo` iza `&`.**

## 4. Rezultat klasifikacije (nalaz, ne ocjena)

| knjiga | rel | fine | ventil/mjesta | negative |
|---|---|---|---|---|
| Hound | 78 | 29 | 49 | 4 |
| Alice | 60 | 10 | 50 | 6 |
| J&H | 23 | 10 | 13 | 4 |
| **Flatland** | **101** | **1** | **100** | 1 |

**Flatland = najčistiji dokaz da ventil radi kao mjerni instrument.** Ekstrakcija uspijeva
(101 usmjerena relacija s opisom i dokazom), ali Massey gotovo ništa ne klasifikuje —
knjiga nema likove u karakternom smislu (geometrijske figure, alegorija; Massey je
character-character taksonomija). **Nalaz o žanru, ne kvar skripte** (O6/s130: ono što
padne u ventil je nalaz o knjizi, ne rupa u tabeli).

## 5. Verifikacija argumenata (Flaviovo pitanje, provjereno u kodu)

| skripta | --knjiga | --force | napomena |
|---|---|---|---|
| bb_09_ner.py | N\|all ✅ | ✅ | |
| bb_10_ner_llm.py | N\|all ✅ | ✅ | + --dry-run |
| bb_10c_docre.py | N\|all ✅ | ✅ | + --dry-run, --reklasifikuj |
| **run_ner.sh** | N\|all ✅ | ✅ | prosljeđuje oba svim trima |
| bb_web_export.py | — | — | **ne treba**: regeneriše sve, idempotentno (40s) |
| bb_xray_export.py | ✅ | — | uvijek prepisuje; --jezici filter |

Proizvodni ulaz za NER:
```
bash run_ner.sh --knjiga all           # radi samo ono cega nema
bash run_ner.sh --knjiga 19 --force    # preracunaj sve slojeve te knjige
```

## 6. Web — usklađen (stajao razdvojen od s131)

s131 je prepravio `get_ner_relacije` ali ga NIJE pokrenuo, jer nlp.html još čita staru
shemu. Zatvoreno zajedno, "u jednom dahu":

**nlp.html (6 zamjena, `str.replace` + assert):**
- `KLASA_COLOR` (P/M/O) → `COARSE_COLOR` (social/familial/professional/other)
- klik-panel: `tip_veze` → `fine · coarse [± afinitet]`
- legenda: 4 coarse klase + nota "dashed = negative affinity"
- arrow markeri + boja ivice po coarse; `coarseKey()` fallback `other` (NULL fine = ventil/mjesta)
- **afinitet = stil linije** (Flaviov OK): `negative` → isprekidana; `pouzdanost` zadržava debljinu

**nav.js i18n ×5:** DocRE kartica prepisana — drugi prolaz više nije "embedding → grupa",
nego klasifikacija u objavljenu taksonomiju književnih odnosa (29 kategorija, 3 klase) +
afinitet, s **eksplicitno imenovanim ventilom** ("ta praznina je nalaz o knjizi, a ne rupa
u tablici"). Nijedan model se ne imenuje (s115).

**Exporti pokrenuti (oba):**
- `bb_web_export.py` — 40s; `ner_<id>.json` nosi `fine/coarse/afinitet/audit` na 4 knjige.
- `bb_xray_export.py` — 1:09; **168 fajlova** (bilo 126) — pokriveni novi opsezi iz
  Flaviovih runova (stajalo otvoreno od s132).

**Browser test (Flavio):** nlp.html novo i staro radi; ostale menu tačke provjerene;
reader X-Ray na novim opsezima radi.

## 7. Završno stanje

- **Baza:** DocRE na 4 knjige (1, 18, 19, 21); ostalo netaknuto.
- **Kod:** netaknut (bb_10c bio spreman iz s131).
- **Web:** nlp.html + nav.js (backupi `.bak_s133_massey` ×2) → **BB_VERSION s133**.
- **Podaci:** web + xray export kompletni i konzistentni s bazom.
- **NER linija: ZATVORENA.** Tri metoda rade tehnički; web ih prikazuje ravnopravno.

## 8. Otvoreno (pokretanje/resurs — ne razvoj)

1. DocRE na knjigama >2000 rečenica — sekvencijalno, pokreće Flavio (`run_ner.sh --knjiga N`).
2. Koreferencija + type audit u bb_10 — **zasebna odluka, van NER zatvaranja**.
3. Iz s132: RUNOVI.md zapis, korekcija 3.77× → 2.47× u README, `pg_stat_user_tables`.

---
*Flavio & Claude · Buchenberg · Sesija 133 · 13. jul 2026.*
