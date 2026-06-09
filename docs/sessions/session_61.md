# Session 61 — 9. jun 2026.

## Učesnici
Flavio & Claude

## Što smo uradili

### 1. Checklist i memorija
- Osvježena memorija na početku sesije
- Dogovoreno: checklist se upisuje u memoriju i primjenjuje automatski na početku svake Buchenberg sesije
- Protokol komandi (prikaži → čekaj OK → izvrši) potvrđen kao nepregovoriv

### 2. Health check — stanje po dolasku
- Flatland it/de: 500 prevoda, 0 pobjednika (NLLB pre-fetch bez cloud modela)
- Nove knjige od Flavia (juce): Alice, Moby Dick, Romeo and Juliet, Big Four hr/sr/de — sve po 50 rečenica, pipeline kompletan
- Jekyll, Dracula, Flatland hr/sr — po 50 rečenica, pipeline kompletan

### 3. Flatland it/de pobjednici
- Pokrenuto: `run_pipeline.sh --knjiga 21 --jezici "it de" --od 1 --do 50`
- Trajanje: 33 minute
- Rezultat: 50/50 pobjednika za oba jezika ✅

### 4. Web export
- `bb_web_export.py` pokrenut — sve nove knjige i jezici ažurirani na portalu

### 5. nav.js — centralni nav refactor
- Kreiran `/var/www/buchenberg/nav.js`
- Header se ubacuje sinhrono via `document.write`
- i18n za sve jezike (en/de/it/hr/sr) uključujući Learn i Geometry (ranije nedostajalo)
- Auto-active klasa na osnovu trenutne stranice
- Theme i language switcher upravljani centralno
- Sve postojeće stranice refaktorisane (index, about, stats, books, nlp, reader, learn)

### 6. geometry.html
- Kreirana nova stranica `/var/www/buchenberg/geometry.html`
- Placeholder "Coming soon"
- Navigacija radi ispravno na svim stranicama

## Stanje prevoda nakon sesije

| Knjiga | Jezici | Pobj |
|--------|--------|------|
| Hound | hr | 3852 ✅ |
| Hound | bs | 350 |
| Hound | sr | 300 |
| Hound | de/it | 200 |
| Hound | af/es/fr/nl/pt/ro/sl | 100 |
| Hound | bg/mk | 50 |
| Big Four | it/pt | 100 |
| Big Four | hr/sr/de | 50 |
| Frankenstein | it/ro | 100 |
| Jekyll | hr/sr/it/de | 50 |
| Dracula | hr/sr/it/de | 50 |
| Flatland | hr/sr/it/de | 50 |
| Alice | hr/sr/it/de | 50 |
| Moby Dick | hr/sr/it/de | 50 |
| Romeo and Juliet | hr/sr/it/de | 50 |

## Ključne napomene
- Flavio koristi NLLB pre-fetch namjerno — prevodi veći broj rečenica bez trošenja Ollama resursa
- run_pipeline.sh koristi se autonomno kada su Ollama resursi slobodni
- nav.js mora biti prva skripta u <head> svih stranica

## Sljedeće
- geometry.html sadržaj: embeddings vizualizacija, cosine similarity na Buchenberg rečenicama
- data/geometry.json generisanje via bb_web_export.py
- Proširenje prijevoda: hr/sr/it/de → s100+, mk/bg → s51–100

## Git
