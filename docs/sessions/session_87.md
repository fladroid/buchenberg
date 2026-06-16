# Session 87 — 16. jun 2026.

**Datum:** 16. jun 2026.  
**Sesija:** 87  
**Commits:** `ababb11` (buchenweb s86), `6e279dd` (buchenweb s87), `3f123f1` (buchenberg)  
**Autor:** Flavio & Claude

---

## Urađeno

### 1. Cache cleanup — foxuno

Očišćeno ~39G iz `/home/balsam/.cache/`:

- Obrisani HuggingFace modeli koji nisu u produkciji: `nllb-200-3.3B` (17G), `nllb-200-distilled-1.3B` (11G), SONAR, LaBSE, Helsinki-NLP (5 modela), MiniLM varijante, classla, twitter-roberta
- Pip cache purge (5G)
- Ostalo: `nllb-200-distilled-600M` (4.7G) + `multilingual-e5-large` (2.2G) — produkcija

### 2. about.html — ispravka Gutenberg broja naslova

`about_p_name` u `nav.js` — sve 5 jezika (EN/DE/IT/HR/SR):

- "millions of public-domain books" → "tens of thousands of public-domain books"
- Razlog: Project Gutenberg ima ~75.000 naslova, ne milijune

### 3. X-Ray Full Mode — reader.html

Najveći zahvat sesije. Potpuno novi mod za Reader stranicu.

**Nova skripta: `bb_xray_export.py`**
- Generira `data/xray_<knjiga_id>_<lang>.json`
- Svih 5 kandidata po rečenici (gemma3@0.8, gemma3@0.1, ministral@0.8, ministral@0.1, nllb-600M)
- Kompletni scoreovi: translation, back_score, sudija_grammar, sudija_naturalness, sudija_fidelity, judge_avg, finalni_score
- Pobjednik označen (`is_winner: true`)
- Pokrenuto za knjiga 1 / HR: 3852 rečenica, 19300 kandidata → `xray_1_hr.json`

**Implementacija u reader.html:**
- Switch "X-Ray" u toolbar (umjesto dugmeta — Flaviov prijedlog)
- Paginacija: 25 rečenica po stranici (hardcoded, bez konfiguracije)
- Layout: model label lijevo (160px), prijevod + BT + scores desno
- Prijevod: 17px serif font (veći od normalnog)
- Back translation: ispod prijevoda, sivo, italic
- Scores: horizontalni red ispod BT (translation, backtrans, grammar, naturalness, fidelity, judge avg, **final** u accent boji)
- Pobjednik: plavi border-left, blago accent pozadina, bold tekst
- Legenda (X-Ray Score Guide) vidljiva dok je X-Ray aktivan
- Pozicija se čuva pri prelasku Normal ↔ X-Ray Full
- Backup: `reader.html.bak3`

**Filozofski kontekst:**
Diskusija o "defanzivnom vs ofanzivnom" pristupu. Počeli s "prvih 100 rečenica", završili s paginacijom cijele knjige. X-Ray Full nije debugging alat — to je drugi mod čitanja. Ko hoće da čita, isključi X-Ray. Ko hoće da istražuje, uključi. Flatland analogija: Square ne živi u 3D, ali može vidjeti 3D kad Sfera posjeti.

---

## Tehnički detalji

**HTML struktura reader.html (finalna):**
```
reader-main
  ├── reader-loading
  ├── reader-toolbar      ← uvijek vidljiv kad je knjiga učitana
  ├── xray-legend         ← vidljiv samo kad je X-Ray aktivan
  ├── xray-full-container ← vidljiv samo kad je X-Ray aktivan
  └── #content            ← sakriven kad je X-Ray aktivan
        ├── book-header
        └── reader
```

Ključna lekcija: toolbar mora biti **van** `#content` — u suprotnom nestaje kad se content sakrije.

**bb_xray_export.py — pokretanje:**
```bash
# Sve knjige, svi jezici s pobjednicima
venv/bin/python src/bb_xray_export.py

# Specifična knjiga i jezici
venv/bin/python src/bb_xray_export.py --knjiga 1 --jezici hr sr de
```

---

## Greške u sesiji

- `scoresHtml` deklariran nakon `card.innerHTML` koji ga koristio → JS `const` nije hoisted → blank X-Ray sadržaj. Fix: premjestiti deklaraciju prije upotrebe.
- Višestruki puta pokušaj sakrivanja toolbar-a sakrivanjem parent diva — rješenje: toolbar izvući van `#content` u HTML strukturi.
- Cache busting protokol (verzija u footeru pred svaki test) uveden od s87.1 — primjenjivati u svim budućim sesijama.

---

## TODO (X-Ray Full — sljedeće sesije)

- Pokrenuti `bb_xray_export.py` za sve knjige i jezike koji imaju pobjednike
- Razmotriti: link "Jump to X-Ray" iz normalnog readera direktno na određenu stranicu
- Legenda: ažurirati `t=` → `temp` da se poklopi s labelom u kartici

---

## Stanje baze (kraj sesije)

- 38.333 rečenica
- ~165.692 prevoda
- ~13.843 pobjednika

---

*Flavio & Claude · Buchenberg · sesija 87 · 16. jun 2026.*
