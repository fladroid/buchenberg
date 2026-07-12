# Sesija 130 — NER orkestracija, CASCADE shema, i otkriće Massey taksonomije

**Datum:** 12. jul 2026.
**Fokus:** Objediniti tri NER metode pod jedan orkestrator; tjunirati DocRE rječnik na više žanrova.
**Ishod:** Orkestrator gotov i dokazan. Rječnik NIJE tjuniran — umjesto toga otkriveno da je **pogrešno postavljen**, i pronađena javna taksonomija koja to rješava.

---

## 1. Polazno stanje (health check)

Korpus nepromijenjen od s129: 50.624 rečenice, 1.518.170 prevoda, 296.578 pobjednika.
NER: Hound jedini s punim lancem (classic 201 / llm 181 / DocRE 74).

---

## 2. Odluke (Flavio)

**O1 — Orkestracija je shell, ne Python monolit.**
Obrazac već postoji (`run_pipeline.sh`). Skripte ostaju samostalno pokretljive (istraživački alat), orkestrator je proizvodni ulaz.
Granica: **petlja po knjigama pripada Pythonu** (model se učita jednom), **shell orkestrira samo redoslijed faza**. Tri poziva, ne 36.

**O2 — `--force`, ne `--samo-nove`.**
Default (bez flaga): radi samo ono čega nema. Uz `--force`: prepiši sve.
Uobičajena konvencija; siguran default za skupu operaciju.

**O3 — `--force` je svojstvo PROLAZA, ne faze.**
> "Force nije selektivan. Sve je force ili nije force."
Ko forsira temelj, forsira i sve iznad njega. Orkestrator prosljeđuje isti flag svim trima.

**O4 — Skripta ne smije rušiti rezultate ispod sebe, i ne smije znati za slojeve iznad sebe.**
> "Skripta ne sme ni u kom slucaju da rusi rezultate ispod sebe i radi sve sto joj je zadatak bez obzira na sledece korake za koje ni ne zna da postoje."

Posljedica: zavisnost slojeva **pripada shemi, ne kodu** → `ON DELETE CASCADE`.
Ovo je zamijenilo raniji prijedlog (svaka skripta ručno briše tuđe tabele) i ranije pravilo "ko briše taj i vraća" — CASCADE ga čini nepotrebnim.

**O5 — Bez potvrdnog prompta u skripti.**
> "Skripta radi sta joj se kaze i sta mora da se uradi."
`y/N` prompt bi se lomio u `nohup` pozivu. Odluka o trošku je Flaviova, donosi je kad kuca `--force`.

**O6 — Usvajamo Massey taksonomiju u cijelosti, bez naših dopuna.** (v. §7)

---

## 3. Popravke u kodu

### bb_09_ner.py — TRI zaostatka (svi iz s126/s129, nikad usklađeni)

| # | Zaostatak | Posljedica |
|---|---|---|
| 1 | `DELETE ... WHERE knjiga_id=%s` bez `method` | Brisao bi i **llm sloj**; puknuo bi na FK (RESTRICT) |
| 2 | `ON CONFLICT (knjiga_id, ime_norm, tip)` bez `method` | **Pucao** — s126 je UNIQUE proširen na 4 kolone |
| 3 | **`SUDIJA_MODEL = "gemma4:31b"` radio NER normalizaciju** | Kršenje s124 principa (sudija slijep i fiksan) |

Zaostatak #2 je otkriven u praksi: DELETE je prošao i commitovan, INSERT pukao → **Hound classic sloj je bio obrisan**. Idempotentnost skripte ga je vratila. Backup nije trebao.

Zaostatak #3 (Flaviovo pitanje: *"Sta radi gemma4 u neru?"*) — najozbiljniji, jer je bio tih i konceptualan, ne tehnički.
**Ispravka:** `NER_MODEL = "glm-5.2"`, `think:false`, temp 0.0 — isti model kao bb_10/bb_10c. Sve pojave "Gemma4" u tekstovima/logovima očišćene.

**Ostale izmjene:** `--knjiga N|all`, `--force` + EXISTS s ispisom preskakanja, spaCy učitan **jednom van petlje** (bio je unutar `faza1_spacy` → 12× učitavanje pri `all`).

### bb_10_ner_llm.py
`--knjiga N|all`, `--force` + EXISTS, održava svoje co-occ veze, DELETE samo svojih entiteta (ostalo CASCADE).
Preskače knjige **bez classic sloja** s porukom "pokreni bb_09 prvo".

### bb_10c_docre.py
`--force` + EXISTS. `--dry-run` **namjerno zaobilazi** EXISTS provjeru (alat za tjuning mora raditi i kad relacije postoje).
Preskače knjige bez llm sloja. (`--knjiga all` i e5-large-van-petlje već je imao.)

### run_ner.sh (novo)
```bash
run_ner.sh [--knjiga N|all] [--force]
  ├── bb_09_ner.py     (classic)
  ├── bb_10_ner_llm.py (llm)
  └── bb_10c_docre.py  (docre)
```
`set -euo pipefail` — staje na prvoj grešci. Flagovi se prosljeđuju svim trima.

---

## 4. Izmjena sheme — ON DELETE CASCADE

Backup: `/tmp/bb_backup_pre_cascade_20260712.dump` (1.5G).

**Pet FK-ova koji pokazuju na `bb_ner_entiteti(id)`** prevedeno s `NO ACTION` na `ON DELETE CASCADE`:
- `bb_ner_recenica.entitet_id`
- `bb_ner_veze.entitet1_id`, `.entitet2_id`
- `bb_ner_relacije.izvor_id`, `.cilj_id`

Ostala četiri (`knjiga_id` ×3, `tip_veze`) **ostaju NO ACTION namjerno** — to su lookup/domen veze, ne izvedeni slojevi.

**Dokazano u praksi:** `bb_10 --force` na Houndu obrisao llm entitete → **74 DocRE relacije pale same**. Nijedna skripta nije morala znati da postoje.

> **Princip:** Shema enkoduje zavisnost slojeva. Kod je ne poznaje.

---

## 5. Mjerenja (RUNOVI)

| Run | Trajanje | CPU | 524 | Napomena |
|---|---|---|---|---|
| bb_10c Hound (85 parova) | **28:28** | 4% | 5 | dominantno čekanje na Ollamu |
| run_ner.sh Alice (63 para) | **8:58** | 12% | 1 | bb_09 preskočen |
| bb_10c J&H dry (24 para) | **7:03** | 10% | 2 | paralelno s Flatlandom |
| bb_10 --knjiga all | **9:44** | 1% | — | 7 obrađeno, 5 preskočeno |
| run_ner.sh prazan prolaz | **20s** | — | — | sve preskočeno, nula LLM poziva |

**DocRE ≈ 28 min po srednjoj knjizi** → `--knjiga all` ≈ 4–6 sati.
**524 greška potvrđena kao ∝ veličina prompta** (drugi nezavisni slučaj, uz s129).

**Greška u procesu:** prvi `bb_10c` run pokrenut sinhrono s `| tail` → MCP timeout, izlaz izgubljen, proces ubijen nakon 20 min bez traga.
> **Pravilo (Flavio):** "Jedino ispravno je `nohup time` sa eventualno dodatnim trace podacima kad se testira." Važi i za NER skripte, ne samo pipeline runove.

---

## 6. Stanje NER slojeva na kraju

**llm sloj sad postoji na svih 9 originalnih knjiga** (bb_10 --knjiga all).
Kopije 22/23/24 nemaju classic → preskočene.

| Knjiga | classic | llm | DocRE |
|---|---|---|---|
| 1 Hound | 200 ent / 199 veza | 181 / 191 | **78** |
| 18 Alice | (postojeći) | 107 | **60** |
| 19 J&H | (postojeći) | 48 | dry-run (24 para) |
| 21 Flatland | (postojeći) | 259 | dry-run (107 parova) |
| 5, 8, 12, 17, 20 | (postojeći) | ✅ | — |

Hound brojke se blago razlikuju od s129 (201/198/74 → 200/199/78) — posljedica **nove normalizacije glm-5.2** umjesto sudije. Nije anomalija.

**Nedeterminizam faze 2 (mjereno):** spaCy pojave identične sva tri prolaza (1239), ali broj entiteta varira: gemma4 dao 201, pa 192; glm-5.2 dao 200. **±5% varijacije uz temp 0.0.** `--force` na bb_09 znači "preračunaj", ne "prepiši istim".

---

## 7. GLAVNO OTKRIĆE — rječnik nije loš, nego pogrešno postavljen

### 7.1 Ventil `ostalo` je mrtav po konstrukciji
Kalibracioni ispis (J&H dry-run): **najniži kosinus u cijeloj knjizi = 0.857.**
Prag `ostalo` = **0.85**. Ventil se **ne može aktivirati nikad**, ni na jednoj knjizi.
Potvrda s129 sumnje: svi kosinusi leže u pojasu **0.857–0.98**. e5-large ne diskriminiše kratke fraze.

### 7.2 Rječnik ne curi u ventil — curi u POGREŠNE GRUPE, tiho

Alice (60 relacija, `ostalo` = 0 pogodaka):

| grupa | stvarni opis | šta to jeste |
|---|---|---|
| `susjedstvo` (16!) | "converses with", "argues with" | razgovor/susret |
| `istraga` | "asks questions of and listens to the story of" | pripovijedanje |
| `prevara` | "pours hot tea on its nose" | zlostavljanje |
| `prevara` | "is the judge who interrogates, commands, threatens to execute" | suđenje/vlast |

J&H:

| kosinus | grupa | opis |
|---|---|---|
| 0.857 | **kretanje (M)** | **"murdered"** |
| 0.871 | **kretanje (M)** | **"condemns"** |
| 0.903 | kretanje | "is acquainted with" |
| 0.928 | srodstvo | "is the master of" |

**Ubistvo klasifikovano kao kretanje.** `susjedstvo` postao skriveni ventil.
Argmax uvijek nađe "najbližu" grupu, ma koliko daleka bila.

### 7.3 KORIJEN PROBLEMA: miješali smo STATUS i RADNJU

- `srodstvo`, `prijateljstvo`, `sluzba` = **status** (ko je kome šta)
- `kretanje`, `radnja`, `istraga`, `prevara` = **radnja** (šta je ko uradio)

Dvije nespojive ose u jednoj ravnoj listi. Zato "murdered" nema gdje osim u "kretanje" — **nemamo pojam za neprijateljstvo, samo za kretanje.**

### 7.4 Koreferencija promiče NER sloju
- Alice: `King → Majesty: "is the same person as"`
- J&H: `"is the same person as (coreference)"` — **dvaput**, a to je **cijeli zaplet knjige** (Jekyll = Hyde)

DocRED literatura: **17,6% relacija zahtijeva koreferencijsko rezonovanje** — to je imenovana faza koju nemamo. Pripada bb_10, ne bb_10c.

---

## 8. Pretraga javnih resursa (Flaviovo principijelno pitanje)

> "Ako postoje javno dostupni podaci ili algoritmi zasto ih ne koristimo?"

**DocRED** (96 tipova, 5.053 dokumenta) — **ODBAČEN**: građen iz Wikipedije/Wikidate; nauka 33,3%, umjetnost 11,5%, **lični život samo 4,2%**. Enciklopedijska, ne narativna taksonomija.
Ali dvije lekcije usvojene: (a) koreferencija je **prvi korak**, ne slučajnost; (b) `no_relation` je **97. tip**, standardna komponenta — ventil nije zakrpa.

**Massey, Xia, Bamman & Smith (2015) — "Annotating Character Relationships in Literary Texts"** — **USVOJENO**.
Repo: `dbamman/characterRelations` → skinuto u `data/external/characterRelations.txt`
2.170 anotacija, 109 tekstova (Homer → Joyce).

**Shema (ortogonalna, ne ravna lista):**

| dimenzija | vrijednosti |
|---|---|
| **coarse** (3) | social 887 · familial 823 · professional 423 |
| **affinity** (3) | positive 1120 · negative 597 · **neutral 421** |
| **fine** (29) | friend 342 · husband/wife 213 · lovers 199 · parent 190 · **enemy 148** · brother/sister 139 · child 117 · acquaintance 108 · servant 98 · unrequited love 69 · colleague 59 · employee 58 · rivals 56 · master 49 · … |

**Zašto rješava problem:**
- `murdered` → social / **enemy** / **negative** (a ne "kretanje")
- `converses with` → social / acquaintance / neutral
- `is the master of` → **professional** / master / neutral
- **Afinitet je dimenzija koju uopšte nemamo** — a Holmes–Watson i Holmes–Stapleton bi kod nas mogli završiti u istoj grupi.
- Tri coarse klase su **žanrovski neutralne** — rade i za Hound i za Alice i za Flatland.

**Radnja se čuva u slobodnom opisu; klasifikacija hvata odnos.**

### 8.1 UPOZORENJE — `detail` polja NISU upotrebljiva kao centroidi

Provjereno: **1.622 od 2.170 su `NR`** (75% prazno). Ostatak je šumovit — repo izričito kaže *"without any adjudication of disagreements or filtering"*:

| fine | affinity | detail |
|---|---|---|
| friend | positive | "Rocinante is Don's horse" |
| friend | positive | **"tries to kill him"** |
| friend | negative | "refuses to loan him money" |

**Uzimamo shemu, NE uzimamo njihove podatke kao centroide.**

### 8.2 Odluka O6 — usvajamo bez naših dopuna

Flatland će vjerovatno tražiti `hijerarhija/klasa`, čega kod Masseya nema. **Ne dodajemo.**
Razlog: fiksna tuđa shema + **živ ventil** je jedini raspored u kojem `ostalo` postaje **mjerni instrument**, a ne sramota. Ono što padne u `ostalo` je **nalaz o knjizi**, ne rupa u tabeli.
Rječnik može rasti kasnije — **iz podataka, s dokazom**, ne iz naše mašte. (To je "varijabilni rječnik", disciplinovan.)

---

## 9. OTVORENO — odavde nastavlja s131

**Neriješeno pitanje: od čega graditi centroide za 29 fine kategorija?**

| put | opis | rizik |
|---|---|---|
| **(a)** | Embeddovati **samo ime kategorije** (`"friend"`, `"enemy"`) | Kratke riječi → slabi embeddinzi |
| **(b)** | Naši seed opisi po kategoriji (kao sad, ali za Massey kategorije) | Vraća našu pristranost u igru |
| **(c)** | LLM bira **direktno iz zatvorene liste od 29** (lista u promptu) | Vraća prosudbu LLM-u — protiv s90 principa (grounding kroz embedding) |

**Ostali koraci za s131:**
1. Prepravka `bb_ner_relacije`: `coarse` + `fine` + `afinitet` umjesto `tip_veze`/`klasa`
2. Prepravka `bb_ner_tip_veze` (ili nova `bb_ner_massey`) — 29 fine + mapiranje na coarse
3. **Prag/margina:** apsolutni kosinus je dokazano slab instrument (pojas 0.857–0.98). Razmotriti **margin-based** aktivaciju ventila (razlika 1. i 2. najbližeg centroida) umjesto apsolutnog praga.
4. Koreferencija kao faza u `bb_10` (Jekyll=Hyde, King=Majesty)
5. `nlp.html` — DocRE tab treba prikazati afinitet (boja ivice?) i coarse klasu
6. Tek nakon toga: `run_ner.sh --knjiga all --force`

---

## 10. Novi principi (za README/ledger)

1. **`--force` je svojstvo prolaza, ne faze.** Sve je force ili nije force.
2. **Skripta ne ruši ništa ispod sebe i ne zna za slojeve iznad sebe.** Zavisnost enkoduje shema (CASCADE), ne kod.
3. **Sudija (gemma4) ostaje slijep i fiksan** — nikad u NER. Za NER: glm-5.2. (s124 princip, konačno sproveden u bb_09.)
4. **Dug LLM proces = `PYTHONUNBUFFERED=1 nohup time ... > logs/*.log 2>&1 &`.** Bez izuzetka, i za NER skripte.
5. **Prije izmjene stare skripte: pregledati CIJELI fajl na zaostatke** iz kasnijih sesija, ne samo onaj koji je zapao za oko. (bb_09 je imao tri.)
6. **Provjeriti kvalitet javnih podataka prije usvajanja** — Massey shema odlična, Massey `detail` polja 75% prazna i šumovita.

---

*Flavio & Claude · Buchenberg · Sesija 130 · 12. jul 2026.*
