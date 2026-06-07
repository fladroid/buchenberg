# Session 58 — Learn stranica: dorada, Match igra, navigacija, Library

**Datum:** 7. jun 2026.
**Sesija:** 58
**Autor:** Flavio & Claude

---

## Pregled sesije

Nastavak sesije 57. Dorada `learn.html`, implementacija druge igre (Sentence Match), fix navigacije, preименовање Books → Library, fix Word Cloud za neprevedene knjige.

---

## 1. Web arhitektura — vodič za nove stranice

### Struktura web fajlova

Svi web fajlovi su na Apache2 serveru na foxuno:
```
/var/www/buchenberg/
├── buchenberg.css       ← zajednički CSS (boje, tipografija, navigacija, dark mode)
├── index.html           ← Home
├── about.html           ← O projektu
├── stats.html           ← X-Ray Stats
├── books.html           ← Library (knjige)
├── nlp.html             ← NLP analiza
├── reader.html          ← Čitač
├── learn.html           ← Language Learning (novo u s57-58)
└── data/                ← JSON fajlovi (generira bb_web_export.py)
    ├── books.json
    ├── orig_{id}.json
    ├── tr_{id}_{lang}.json
    ├── ner_{id}.json
    └── version.json
```

> ⚠️ Web fajlovi NISU u gitu. Izmjene se rade direktno na `/var/www/buchenberg/`. TODO: refaktor da web fajlovi budu u gitu.

### Kako dodati novu stranicu

1. Kopirati header/footer pattern iz postojeće stranice (npr. `reader.html`)
2. Dodati `<link rel="stylesheet" href="buchenberg.css">` u `<head>`
3. Kopirati header blok (`#bb-header`) sa navigacijom i dark mode togglem
4. Dodati novi link u navigaciju **svih** postojećih stranica (ručno — TODO: nav.html)
5. Dodati vlastiti inline CSS u `<style>` tag u `<head>`

### Standardni header template

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Buchenberg — Nova stranica</title>
  <link rel="stylesheet" href="buchenberg.css">
  <style>
    /* vlastiti CSS ovdje */
  </style>
</head>
<body>

<div id="bb-header">
  <div id="bb-header-inner">
    <a href="index.html" id="bb-logo">Buchen<span>berg</span></a>
    <nav id="bb-nav">
      <a href="index.html" class="bb-nav-link">Home</a>
      <a href="about.html" class="bb-nav-link">About</a>
      <a href="stats.html" class="bb-nav-link">X-Ray Stats</a>
      <a href="books.html" class="bb-nav-link">Books</a>
      <a href="nlp.html" class="bb-nav-link">NLP</a>
      <a href="reader.html" class="bb-nav-link">Reader</a>
      <a href="learn.html" class="bb-nav-link">Learn</a>
      <a href="nova.html" class="bb-nav-link active">Nova stranica</a>
    </nav>
    <div id="bb-header-controls">
      <div id="bb-ui-lang-bar">
        <button class="bb-lang-btn active" data-lang="en">EN</button>
        <button class="bb-lang-btn" data-lang="de">DE</button>
        <button class="bb-lang-btn" data-lang="it">IT</button>
        <button class="bb-lang-btn" data-lang="hr">HR</button>
        <button class="bb-lang-btn" data-lang="sr">SR</button>
      </div>
      <button id="bb-theme-toggle" title="Toggle dark mode">☀️</button>
    </div>
  </div>
</div>
```

### Standardni JS za dark mode i cache busting

```javascript
// Dark mode
(function() {
  const saved = localStorage.getItem('bb-theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  document.getElementById('bb-theme-toggle').textContent = saved === 'dark' ? '☀️' : '🌙';
})();
document.getElementById('bb-theme-toggle').addEventListener('click', function() {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('bb-theme', next);
  this.textContent = next === 'dark' ? '☀️' : '🌙';
});

// Cache busting
async function fetchVersion() {
  try {
    const r = await fetch('data/version.json?t=' + Date.now());
    const j = await r.json();
    return j.v || Date.now();
  } catch(e) { return Date.now(); }
}
```

### Kritična napomena — show/hide panela

```javascript
// ISPRAVNO — override-uje CSS display:none
function show(id) { document.getElementById(id).style.display = 'block'; }
function hide(id) { document.getElementById(id).style.display = 'none'; }

// POGREŠNO — prazan string ne override-uje CSS rule
function show(id) { document.getElementById(id).style.display = ''; } // ← NE KORISTITI
```

### Dostupni JSON podaci

| Fajl | Sadržaj | Primjer korištenja |
|------|---------|-------------------|
| `data/books.json` | Sve knjige, jezici, broj rečenica | Lista knjiga, dropdowni |
| `data/orig_{id}.json` | Sve originalne EN rečenice knjige | Word cloud, čitač, learn igre |
| `data/tr_{id}_{lang}.json` | Pobjednički prevodi po jeziku | Igre, čitač, statistike |
| `data/ner_{id}.json` | NER entiteti i veze | NLP stranica, entity graph |
| `data/version.json` | Cache busting timestamp | Svaki fetch poziv |

---

## 2. learn.html — arhitektura

### Struktura stranice

```
learn.html
├── Header (buchenberg.css + dark mode + UI jezici)
├── Hero (naslov + subtitle)
└── learn-main div
    ├── Tabs (Fill in the Blank | Sentence Match)
    ├── fillin-panels div
    │   ├── #setup-panel      ← odabir knjige/jezika/smjera/težine
    │   ├── #game-panel       ← aktivna igra (display:none u CSS)
    │   └── #results-panel    ← rezultati (display:none u CSS)
    └── match-panels div (display:none)
        ├── #match-panel      ← odabir knjige/jezika
        ├── #match-game-panel ← aktivna match igra (display:none)
        └── #match-results-panel ← rezultati (display:none)
```

### Igra 1 — Fill in the Blank

**Tok:**
1. Setup: knjiga + jezik + smjer (učim strani/učim EN) + težina (1/2/3 blanka)
2. Fetch `tr_{id}_{lang}.json` → filter samo `translated: true`
3. Random 10 rečenica → za svaku N blanka (content words, dužina > 3 slova)
4. Prikaz: context rečenica (hint) + target rečenica s blankovima
5. Klik na blank → multiple choice popup (4 opcije: 1 tačna + 3 random iz korpusa)
6. Tačno na MC → +8 poena, input postaje zeleno
7. Netačno na MC → mora utipkati → tačno tipkanjem → +10 poena
8. Hint → otkriva blank → −3 poena
9. Check Answers → finalizuje neodgovorene blankove
10. Next Sentence → sljedeća od 10
11. Nakon 10 → Results panel

**Scoring:** MC tačno=8, tipkanje tačno=10, hint=−3, netačno=0

**Smjerovi učenja:**
- `learn-foreign`: target=prevod, context=EN original
- `learn-english`: target=EN original, context=prevod

### Igra 2 — Sentence Match

**Tok:**
1. Setup: knjiga + jezik
2. Fetch `tr_{id}_{lang}.json` → random 10 prevedenih rečenica
3. Prikaz: dvije kolone — EN (lijevo) i prevod (desno), obje random izmiješane
4. Klik na EN rečenicu → selected (plavi border)
5. Klik na prevod → provjera para
6. Tačan par → obje zelene, +10 poena
7. Netačan par → kratko crveno flash, −2 poena
8. 10/10 sparenih → automatski Results (sa vremenom)

**Scoring:** tačno=+10, netačno=−2

---

## 3. Izmjene u ovoj sesiji

### learn.html
- Dodana tab navigacija (Fill in the Blank | Sentence Match)
- Implementirana Sentence Match igra (dvije kolone, klik-klik sparivanje)
- Dodan UI jezik bar u navigaciju (bio missing)
- Fix: `show()` funkcija koristi `display='block'` umjesto `display=''`
- Fix: hero padding smanjen da setup panel bude vidljiv bez scrolla

### books.html
- Naslov "Translated Books" → "Library"
- Badge na svakoj kartici: broj prevedenih jezika
- Knjige bez prevoda prikazuju "No translations yet" badge
- Word Cloud sada radi za neprevedene knjige (prikazuje EN original)
- Fix: `openWordCloud` za knjige bez prevoda — `wcLang=null` više ne crasha

### Navigacija (sve stranice)
- `reader.html` nije imao "Learn" link (bio bug) — ispravljeno
- learn.html je imao samo dark mode toggle bez UI jezik bar — ispravljeno

---

## 4. Poznati bugovi i TODO

### TODO (navigacija)
- **nav.html** — zajednički include fajl za navigaciju; trenutno je svaka stranica hardkodirana. Svaki put kad se doda nova stavka mora se ručno mijenjati svih 8 stranica. Rješenje: jedan `nav.html` koji se učitava JS-om na svakoj stranici.

### TODO (learn.html)
- Testirati sve kombinacije igara (knjiga × jezik × smjer × težina)
- UI jezik prevodi za learn.html (trenutno samo EN strings)
- Persistirati score i statistike između sesija (localStorage)
- Dodati više igara

### TODO (pipeline)
- sr — gemma3+ministral s221–s300, sudija --force, pobjednici
- ON DELETE CASCADE na bb_prev_recenica
- hr/it/de → s350
- Ostali jezici → s101–s350
- mk/bg → s51–s100
- --skip-ollama flag u health_check.py
- Web fajlovi u git
- Favicon
- Relation Extraction
- bb_web_export.py refaktor → v_pobjednici

---

*Flavio & Claude · Buchenberg · Sesija 58 · 7. jun 2026.*
