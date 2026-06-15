# Session 81 — 15. jun 2026.

**Fokus:** art.html i18n — rekonstrukcija s78+s79, buchenweb git uspostavljanje, health_check buchenweb provjera

---

## Checklist (standardni)

- Project files pročitani
- README pročitan (V3, s80)
- Sessions 78–80 pročitane
- Health check: sve zeleno — 38.333 rečenica, 150.328 prevoda, 10.202 pobjednika
- Git buchenberg: 0f503af (s80)
- Git buchenweb: a0d895f (s77) ⚠️ zaostaje

---

## Šta je urađeno

### 1. Health check — dodana buchenweb provjera

`src/health_check.py` proširen: sekcija 6 sada prikazuje status oba git repozitorijuma:
- buchenberg: uncommitted fajlovi + zadnja 3 commita
- buchenweb: uncommitted fajlovi + zadnja 3 commita + **upozorenje ako buchenweb zaostaje za buchenberg**

Commit buchenberg: `b636862`

### 2. Restore art.html iz buchenweb

art.html na disku bio s79 verzija (broken — referencirala art_* ključeve koji nisu bili u nav.js s77).
Vraćen na s77: `git restore art.html`

### 3. Backup nav.js i art.html

```
cp nav.js nav.js.bak
cp art.html art.html.bak
```

Princip: backup prije svake izmjene. Ako nešto krene naopako — `cp nav.js.bak nav.js` i portal odmah oporavljen.

### 4. Otkrivanje greške u insert metodi

Prethodne sesije koristile su string replace koji je uzrokovao dupli navodnik `""` na spoju:
- Staro (pogrešno): `vrijednost" },` → zamjena → `vrijednost"` + novi_blok + `" },`  
- Rezultat: `vrijednost"novi_blok" },` — dupli `"` ruši JS parser

Ispravna metoda: pronađi zadnji `\w+:"[^"]*"` u lang bloku, uzmi `end()` poziciju, insertuj direktno na tu poziciju.

### 5. art_* ključevi u nav.js — 5 jezika × 50 ključeva

**Metoda inserta (finalna, ispravna):**

```python
import re

def get_insert_pos(s, lang_start, lang_end):
    start = s.find(lang_start)
    end = s.find(lang_end, start)
    block = s[start:end]
    last_key = list(re.finditer(r'\w+:"[^"]*"', block))[-1]
    return start + last_key.end()

# Insert za EN, DE, IT, HR (završavaju s novim lang blokom):
insert_pos = get_insert_pos(s, 'en: { home:', '\n  de: {')
s = s[:insert_pos] + ART_EN + s[insert_pos:]

# Insert za SR (zadnji lang, završava s ];):
sr_start = s.find('\n  sr: {')
sr_end = s.find('\n];\n', sr_start)
sr_block = s[sr_start:sr_end]
idx = sr_block.rfind('about_sidebar_authorship_text:')
val_start = sr_block.find('"', idx + len('about_sidebar_authorship_text:'))
val_end = sr_block.find('"', val_start + 1)
insert_pos = sr_start + val_end + 1
s = s[:insert_pos] + ART_SR + s[insert_pos:]
```

**Ključno pravilo: svi art_* stringovi pisani su s Unicode escape sekvencama u Python kodu:**
- Curly apostrof: `\u2019` (umjesto plain `'`)
- Em dash: `\u2014`
- Specijalni znakovi: `\u00b7`, `\u00e0`, `\u00e8`, itd.
- HTML entiteti se ne koriste unutar JS stringova — koriste se direktni Unicode escape

**Popis art_* ključeva (50):**
```
art_subtitle, art_h_synesthesia, art_synesthesia_intro
art_th_figure, art_th_gift, art_th_question
art_row_abbott, art_row_borges, art_row_wittgenstein, art_row_kandinsky
art_gift_geometry, art_gift_selection, art_gift_use, art_gift_synesthesia
art_q_abbott, art_q_borges, art_q_wittgenstein, art_q_kandinsky
art_card_kandinsky_h, art_card_kandinsky_p1/p2/p3
art_card_scriabin_h, art_card_scriabin_p1/p2/p3
art_card_buchenberg_h, art_card_buchenberg_p1/p2/p3/p4
art_xray_quote, art_xray_sig
art_h_tapestry, art_tapestry_p1/p2
art_tap_all, art_tap_score, art_tap_model, art_tap_abs, art_tap_rel
art_h_sound, art_sound_p1/p2
art_snd_slow, art_snd_med, art_snd_fast
art_h_fingerprints, art_fp_p1, art_fp_p2
```

**Testiranje po koracima:**
- Nakon svakog lang bloka: bump BB_VERSION (s81.1, s81.2...) → provjera browsera
- Ako header/footer nestanu → `cp nav.js.bak nav.js` i analiza greške
- EN: s81.3 ✅ | DE: s81.4 ✅ | IT: s81.5 ✅ | HR: s81.6 ✅ | SR: s81.7 ✅

### 6. art.html refaktor — id atributi i applyPageI18n()

Svaki sadržajni element dobio `id` atribut koji odgovara i18n ključu (s crticama umjesto podvlaka):

```html
<!-- Primjeri -->
<h2 id="art-h-synesthesia"></h2>
<span id="art-subtitle"></span>
<th id="art-th-figure"></th>
<td id="art-row-abbott"></td>
<h3 id="art-card-kandinsky-h"></h3>
<span id="art-card-kandinsky-p1"></span>
<option value="slow" id="art-snd-slow"></option>
```

`applyPageI18n()` funkcija koristi mapping id → ključ:

```javascript
function applyPageI18n() {
  var t = (typeof BB_NAV !== 'undefined' && BB_NAV.t) ? BB_NAV.t : function(k){return k;};
  var ids = {
    'art-subtitle': 'art_subtitle',
    'art-h-synesthesia': 'art_h_synesthesia',
    // ... svi ostali
  };
  Object.keys(ids).forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.innerHTML = t(ids[id]);
  });
}
document.addEventListener('DOMContentLoaded', applyPageI18n);
BB_NAV.onLangChange = applyPageI18n;
```

### 7. Commit buchenweb

```
git add nav.js art.html
git commit -m "s81: art.html i18n complete — art_* keys (50 per lang x 5 langs), art.html refaktor, BB_VERSION s81.7"
git push
```
Commit: `e94ae11`

---

## Workflow: prevod stranice korak po korak

Ovo je finalni, testirani workflow za i18n bilo koje stranice portala.

### Korak 0 — Priprema

```bash
# Backup OBAVEZNO prije bilo kakve izmjene
cp /var/www/buchenberg/nav.js /var/www/buchenberg/nav.js.bak
cp /var/www/buchenberg/stranica.html /var/www/buchenberg/stranica.html.bak
```

### Korak 1 — Inventar

Pročitati HTML fajl i identificirati sve sadržajne tekstove za prevod.
Definisati popis `prefix_*` ključeva (npr. `geo_*`, `art_*`, `learn_*`).
Formule, tehničke labele i nazivi modela se **ne prevode**.

### Korak 2 — Insert EN ključeva u nav.js

```python
import re

PATH = "/var/www/buchenberg/nav.js"
with open(PATH) as f:
    s = f.read()

# Nađi insert poziciju za EN blok
en_start = s.find('en: { home:')
de_start = s.find('\n  de: {')
en_block = s[en_start:de_start]
last_key = list(re.finditer(r'\w+:"[^"]*"', en_block))[-1]
insert_pos = en_start + last_key.end()

PREFIX_EN = ''',
    kljuc1:"Vrijednost 1",
    kljuc2:"Vrijednost 2"'''
# PRAVILO: svi apostrofi → \u2019 (curly), em dash → \u2014, ne HTML entiteti!

s = s[:insert_pos] + PREFIX_EN + s[insert_pos:]

# Bump verzija za test
s = s.replace("const BB_VERSION = 'sXX';", "const BB_VERSION = 'sXX.1';")

with open(PATH, "w") as f:
    f.write(s)
```

**Test u browseru:** header/footer vidljivi? Ako da → nastaviti na DE.
**Ako ne:** `cp nav.js.bak nav.js` → analizirati grešku.

### Korak 3–6 — Insert DE, IT, HR, SR ključeva

Isti pattern, drugačiji markeri:

| Lang | lang_start | lang_end |
|------|-----------|---------|
| EN | `'en: { home:'` | `'\n  de: {'` |
| DE | `'\n  de: {'` | `'\n  it: {'` |
| IT | `'\n  it: {'` | `'\n  hr: {'` |
| HR | `'\n  hr: {'` | `'\n  sr: {'` |
| SR | poseban tretman (vidi niže) | |

**SR poseban tretman** (zadnji lang, završava s `};` umjesto novim lang blokom):
```python
sr_start = s.find('\n  sr: {')
sr_end = s.find('\n];\n', sr_start)
sr_block = s[sr_start:sr_end]
idx = sr_block.rfind('about_sidebar_authorship_text:')
val_start = sr_block.find('"', idx + len('about_sidebar_authorship_text:'))
val_end = sr_block.find('"', val_start + 1)
insert_pos = sr_start + val_end + 1
s = s[:insert_pos] + PREFIX_SR + s[insert_pos:]
```

Nakon svakog jezika: bump verzija (sXX.2, sXX.3...) → browser test → nastaviti samo ako OK.

### Korak 7 — HTML refaktor

Za svaki sadržajni element:
- Ukloniti tekst iz HTML-a
- Dodati `id` atribut koji odgovara ključu (podvlake → crtice):
  `art_subtitle` → `id="art-subtitle"`

```html
<!-- Prije -->
<h2>The Tapestry</h2>
<p>A book as woven fabric...</p>

<!-- Poslije -->
<h2 id="art-h-tapestry"></h2>
<p><span id="art-tapestry-p1"></span></p>
```

Napisati `applyPageI18n()` funkciju i `BB_NAV.onLangChange` hook.

**Browser test:** promjena jezika → sadržaj se mijenja za svih 5 jezika.

### Korak 8 — Bump finalne verzije i datum

```python
s = s.replace("const BB_VERSION = 'sXX.N';", "const BB_VERSION = 'sXX';")
s = s.replace("const BB_VERSION_DATE = 'DD Mon YYYY';", "const BB_VERSION_DATE = '15 Jun 2026';")
```

### Korak 9 — Commit buchenweb

```bash
cd /var/www/buchenberg
git add nav.js stranica.html
git commit -m "sXX: stranica.html i18n complete — prefix_* keys (N per lang x 5 langs), stranica.html refaktor, BB_VERSION sXX"
git push
```

**Verifikacija:**
```bash
git status -sb && git log origin/master -1 --oneline
```

### Korak 10 — Session doc + README + buchenberg commit

```bash
cd /home/balsam/buchenberg
# Napisati session_NN.md
git add docs/sessions/session_NN.md README.md
git commit -m "sXX: session doc + README update"
git push
```

---

## Pravila koja se ne smiju zaboraviti

1. **Backup UVIJEK** prije izmjene nav.js ili HTML fajla
2. **Apostrof u JS stringovima**: plain `'` (U+0027) unutar `"double-quoted"` stringa ruši JS parser. Koristiti `\u2019` (curly) ili HTML entity `&#39;`
3. **HTML entiteti ne idu u JS stringove**: `&mdash;` → `\u2014`, `&middot;` → `\u00b7`, `&agrave;` → `\u00e0`, `&egrave;` → `\u00e8`
4. **Insert metoda**: koristiti pozicijsko insertovanje na `last_key.end()`, NIKAD string replace s `" },` kao anchorem
5. **Test nakon svakog jezika**: browser potvrda prije nastavka
6. **BB_VERSION bump za svaki test**: `sXX.1`, `sXX.2`... — jedini način da se razlikuje cache od greške
7. **SR poseban tretman**: SR blok završava s `};`, ne s novim lang blokom
8. **Dva gita**: buchenberg (`/home/balsam/buchenberg/`) i buchenweb (`/var/www/buchenberg/`) — oba se commitaju zasebno
9. **Health check** od sada prikazuje status oba repozitorijuma i upozorenje ako buchenweb zaostaje

---

## Stanje na kraju sesije

- buchenweb: `e94ae11` (s81) — čist ✅
- buchenberg: `b636862` (s81 health_check) — čist (osim flanel.sh D, nohup.out M)
- nav.js: EN/DE/IT/HR/SR art_* ključevi ✅
- art.html: i18n refaktor ✅, svih 5 jezika ✅
- BB_VERSION: s81.7 · 15 Jun 2026

## i18n status po stranicama

| Stranica | Status |
|---------|--------|
| `stats.html` | ✅ Potpun (s77) |
| `books.html` | ✅ Potpun (s77) |
| `index.html` | ✅ Potpun (s77) |
| `nlp.html` | ✅ Potpun (s77) |
| `about.html` | ✅ Potpun (s78→s81) |
| `art.html` | ✅ Potpun (s79→s81) |
| `reader.html` | ⏭ Namjerno preskočen |
| `geometry.html` | 🔲 TODO |
| `learn.html` | 🔲 TODO (nizak prioritet) |

## Sljedeće

- `geometry.html` i18n — koristiti ovaj workflow
- `learn.html` i18n — nizak prioritet
- Pipeline: hr/sr/it/de → s350; mk/bg → s51–s100

---

*Flavio & Claude · Buchenberg · Session 81 · 15. jun 2026.*
