# Session 32 — Book X-Ray: UMAP vizualizacija + audio sonifikacija

**Datum:** 2026-05-30
**Učesnici:** Flavio & Claude
**Nastavlja:** Session 31 (eksperimenti evaluacije, e5 vektori)

---

## Kontekst — gdje smo stali

Session 31 je završila s e5-large vektorima (4520 redova) i nizom eksperimenata
evaluacije (pivot, hint, kontekst, DeepL). Flavio je izrazio subjektivni osjećaj
da prevodi nisu dovoljno dobri i predložio istraživanje nečeg sasvim drugog —
duboku analizu engleskog teksta, ne samo statistički.

---

## Korak 1 — Protokol i retrospektiva

Na početku sesije obavili smo retrospektivu radnog protokola. Utvrđeni propusti:

- Claude je izvršio komande (cat README, cat sessions, health_check) bez prethodnog
  prikaza i čekanja OK — direktno kršenje protokola
- Claude je potvrdio da zna protokol, ali ga nije primjenjivao (default mode
  "budi koristan brže" pobijedio je eksplicitnu instrukciju)

**Zaključak:** Protokol "prikaži komandu → čekaj OK → izvrši" mora biti bez izuzetka.
Izuzetke za "readonly" komande ne postoje — navika mora biti konzistentna.

Flavio je predložio set pitanja za provjeru konteksta na početku sesije:
1. U kom projektu radimo i gdje živi kod?
2. Koji server za razvoj, koji za bazu?
3. Kako se oslovljavamo i kako komuniciramo?
4. Protokol prije svake komande?
5. Zadnja stvar koju smo uradili?
6. Koji embedder za produkciju i thresholdovi?
7. Šta je tabela translations i zašto postoji?

---

## Korak 2 — Istraživanje: duboka analiza teksta

Flavio predložio pivot od prevoda ka analizi samog engleskog teksta — tri nivoa:

**Strukturalni:** narativni luk, perspektiva, temporalna struktura
**Semantički:** tematske mreže, karakterizacija kroz jezik, motivi i simboli
**Diskursni:** kohezija, dijaloški vs narativni dijelovi, register i stil

Prošireno na eksperimentalne ideje:
- Cellular automaton i ant colony na semantičkim podacima
- Knjiga kao 1024×1024 slika (UMAP + boja)
- Knjiga kao zvuk (sonifikacija)
- Cross-media embedding (CLIP, Music2Vec)

---

## Korak 3 — UMAP vizualizacija (Book X-Ray v1)

### Infrastruktura

- Instaliran `umap-learn` u venv
- Generirani e5-large vektori za rečenice 41–100 (60 novih, 15 sec)
- Ukupno: 100 EN e5 vektora u `sentence_embeddings`

### Pipeline

```bash
# Dodavanje e5 vektora za s41-s100
venv/bin/python src/run_embeddings.py --embedder e5 --sent_from 41 --sent_to 100

# UMAP redukcija 1024D → 2D (na serveru, Python)
# Export kao JSON → hardcoded u React artifakt
```

### UMAP parametri

```python
umap.UMAP(n_components=2, random_state=42, n_neighbors=10, min_dist=0.1)
```

### Artifakt v1 — vizualizacija

React + Recharts scatter plot. Mapping:
- **X, Y** — UMAP 2D koordinate
- **Boja točke** — sentiment (🟢 positive, ⚫ neutral, 🔴 negative)
- **Veličina točke** — word_count (proporcionalna)
- **Klik** — detalji rečenice (tekst, sentiment, score, wc, UMAP koordinate)
- **Filter** — dugmad za positive/neutral/negative/all

### Prirodni klasteri koji su emergirali

- **Gornji desni kut** — kratki dijalozi ("Good!", "Excellent!", "Why so?")
- **Donji lijevi kut** — rečenice o "the stick" i psu (fizički opisi)
- **Desno središte** — medicinski podaci o Mortimeru (formalni register)
- **Sredina** — narativne rečenice srednje dužine

Klasteri su nastali bez ikakve supervizije — samo iz semantičkih vektora.

---

## Korak 4 — Audio sonifikacija (Book X-Ray v2)

### Mapiranje tekst → zvuk

| Dimenzija | Zvučni parametar |
|-----------|-----------------|
| sentiment label | valni oblik (positive=triangle, neutral=sine, negative=sawtooth) |
| sentiment label | muzička skala (positive=dur C5-E6, neutral=pentatonska C4-D5, negative=mol C3-Eb4) |
| UMAP X pozicija | visina note unutar skale |
| word_count | trajanje tona (0.15–1.2 sec) |
| sentiment score | glasnoća (vol = -20 + score×10 dB) |

### Implementacija

React + Tone.js (WebAudio API). Dva moda:
- **Autoplay** — knjiga svira od rečenice 1 do 100 kao kompozicija, progress bar
- **Klik na točku** — svira samo tu rečenicu + panel s detaljima (nota, waveform, trajanje)

Canvas API za scatter plot (umjesto Recharts) — potrebna preciznost klika i
animacija aktivne točke (glow efekt pri sviranju).

### Detalji panela

Za svaku odabranu rečenicu prikazuje:
- Tekst rečenice
- Sentiment label + score
- Broj riječi
- UMAP koordinate
- Koja nota se svira
- Valni oblik (waveform)
- Trajanje tona

---

## Izmjene koda i infrastrukture

| Komponenta | Izmjena |
|------------|---------|
| `sentence_embeddings` | +60 e5 vektora (s41–s100), ukupno 100 |
| `venv` | Instaliran `umap-learn` |
| `src/visualize_book.py` | NE postoji — vizualizacija je direktno u artifaktu |

**Napomena:** Vizualizacijski kod živi u Claude artifaktima, ne u repo-u. Za produkcijsku
web aplikaciju, export logika (UMAP redukcija + JSON export) treba postati skripta
u `src/`.

---

## Ključni zaključci

1. **UMAP na e5 vektorima otkriva semantičku strukturu bez supervizije** — klasteri
   odgovaraju narativnim i registarskim razlikama koje su smislene.

2. **Sonifikacija radi** — različite rečenice zvuče različito, sentiment je čujan.
   Negativne rečenice imaju hrapav sawtooth zvuk, pozitivne čist triangle.

3. **Isti vektori, više reprezentacija** — iz jednog seta e5 vektora možemo praviti
   vizualizacije, zvuk, i potencijalno druge forme (CA, grafovi, CLIP usporedbe).

4. **Pivot od prevoda ka analizi** — Flavio je predložio i sesija je potvrdila da
   duboka analiza teksta može biti vrijedna sama po sebi, neovisno od pipeline-a.

5. **X-Ray filosofija u praksi** — vizualizacija i sonifikacija su doslovni X-Ray
   knjige: gledamo unutra, ne samo na površinu (prijevod).

---

## Na horizontu

1. **`src/export_umap.py`** — skripta za UMAP export (ne artifakt) za produkcijsku upotrebu
2. **Skaliranje na cijelu knjigu** — 3852 rečenica Hound-a, puniti e5 vektore postupno
3. **Cellular automaton** — rečenice kao ćelije, semantička sličnost kao pravilo
4. **Višeknjižna vizualizacija** — Hound + Frankenstein + Poirot na istom platnu
5. **HTTPS prezentacija** — web stranica koja servira Book X-Ray za svaku knjigu
6. **Cross-media embedding** — CLIP prostor: gdje tekst živi u odnosu na slike?
7. **Commit `run_deepl.py`** — uncommitted iz sesije 31, treba čistiti

---

## Handoff blok

- **`sentence_embeddings`:** 100 EN e5 vektora (s1–s100), `translation_embeddings`: 4480
- **`umap-learn`:** instaliran u venv
- **Artifakti:** Book X-Ray v1 (vizualizacija) i v2 (vizualizacija + audio) — u Claude UI
- **Git:** treba commit (`run_deepl.py` + ovaj dokument)
- **Model:** Sonnet 4.6 medium

---

*Flavio & Claude · Session 32 · 2026-05-30*
