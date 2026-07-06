# KAKO-KeyConcepts.md — Kako mijenjati, dodavati i brisati Key Concepts / Wikipedia kartice

Konsolidovana referenca iz sesija 90, 96, 108 + stvaran kod (`nav.js`, `data/concepts.json`) provjeren na serveru. Ovo je POSEBAN sistem od multijezičkog UI teksta — vidi `KAKO-JeziciUI.md` za taj, odvojeni mehanizam.

**Nastalo:** sesija 116, 6. jul 2026.

---

## 1. Arhitektura — potpuno odvojena od NAV_I18N

Key Concepts kartice **NISU** dio i18n sistema opisanog u `KAKO-JeziciUI.md`. Ključne razlike:

- **Podaci:** `/var/www/buchenberg/data/concepts.json` — poseban fajl, ne `nav.js` rječnik.
- **Jednojezične su** — `name`/`description` postoje SAMO na engleskom. Ne mijenjaju se kad korisnik promijeni UI jezik.
- **Naslov sekcije "Key Concepts" je hardkodovan string u JS-u** (`title.textContent = CONCEPT_TITLES[page] || 'Key Concepts'`), ne ide kroz `t()` — nikad se ne prevodi, na bilo kojoj stranici, bilo kom jeziku. Ovo je Flaviova eksplicitna odluka, ne propust.
- **Renderovanje je centralizovano u `nav.js`** (IIFE blok, ~linija 1549), ne po-stranici kako je slučaj s ostalim i18n tekstom.

---

## 2. Tačan mehanizam (iz `nav.js`, verifikovano na serveru)

```js
const CONCEPT_PAGES = ['index','about','geometry','art','nlp','stats','learn','reader','books'];
const CONCEPT_TITLES = { books: 'The Books on Wikipedia' };
const page = window.location.pathname.split('/').pop().replace('.html','') || 'index';
if (!CONCEPT_PAGES.includes(page)) return;
const footer = document.getElementById('bb-footer');
if (!footer) return;
fetch('data/concepts.json?t=' + Date.now())
  .then(r => r.json())
  .then(data => {
    const concepts = data[page];
    if (!concepts || !concepts.length) return;
    // ... gradi <section id="bb-key-concepts"> sa karticama, insertuje prije #bb-footer
  })
  .catch(function() {});
```

**Šta ovo znači praktično:**
- **`CONCEPT_PAGES`** — lista stranica gdje se Key Concepts uopšte pokušava prikazati. **Nova stranica MORA biti dodata ovdje** ili se kartice nikad neće ni pokušati učitati na njoj, bez obzira šta piše u `concepts.json`.
- **Page key** = naziv HTML fajla bez ekstenzije (`about.html` → `about`) — mora se poklapati sa ključem u `concepts.json`.
- **`<div id="bb-footer">` mora postojati na stranici** — to je insertion point (kartice se ubacuju TAČNO ispred njega). Bez tog elementa: tiho ništa, bez greške.
- **`data[page]` ne postoji ili prazan niz** → tiho ništa, bez greške.
- **Fetch cache-bust je AUTOMATSKI** (`?t=Date.now()`) — nema potrebe za ručnim bump-om verzije kad se samo `concepts.json` mijenja.
- **`CONCEPT_TITLES`** — override mapa za naslov sekcije po stranici; trenutno samo `books: 'The Books on Wikipedia'`. Default za sve ostale: "Key Concepts".
- **`books.html` NIJE poseban kod** — ide kroz ISTI mehanizam kao sve ostale stranice, samo su njegove "kartice" zapravo knjige (naslov → Wikipedia članak o knjizi) umjesto opštih pojmova, uz override naslova sekcije.

### ⚠️ Najvažnija posljedica: tiho, sajt-široko brisanje kartica
`.catch(function() {})` guta SVAKU grešku (broken JSON, network fail) **bez ijedne poruke, bez pada stranice**. Ako `concepts.json` postane sintaksno nevažeći JSON — **Key Concepts kartice nestaju na SVIM stranicama, na svim jezicima, bez ikakvog vizuelnog znaka da je nešto pošlo po zlu.** Jedini način da se to otkrije je eksplicitna JSON validacija (§7) ili slučajna browser provjera. **Zato: validacija JSON-a nakon SVAKE izmjene nije opciona.**

---

## 3. Struktura `concepts.json`

```json
{
  "index": [
    { "icon": "🌐", "name": "Machine translation", "description": "...", "wiki": "Machine_translation" },
    ...
  ],
  "about": [ ... ],
  "stats": [ ... ],
  ...
}
```

- Grupisano **po stranici** (ključ = page key, isti kao u `CONCEPT_PAGES`).
- Svaka kartica: `{icon, name, description, wiki}`.
  - **`name`** — kratko, BEZ zagrada (npr. "Attention", ne "Attention (machine learning)").
  - **`wiki`** — PUN Wikipedia slug, UKLJUČUJUĆI disambiguation zagrade gdje su dio stvarnog naslova članka (npr. `Attention_(machine_learning)`, `Mutation_(evolutionary_algorithm)`).
  - **`description`** — prost tekst (ubacuje se kao `innerHTML` pa tehnički podržava HTML, ali konvencija je čist tekst).
  - Link se **auto-gradi**: `https://en.wikipedia.org/wiki/{wiki}`, `target="_blank" rel="noopener"`.

---

## 4. Pravilo sadržaja (Flaviova odluka, nepregovorivo)

**Samo pojmovi koji STVARNO imaju članak na engleskoj Wikipediji.** Ako pojam nema Wikipedia članak (potvrđen primjer: *self-refinement* kao LLM tehnika — postoji na arXiv/NeurIPS/blogovima, ali NE na Wikipediji) — **kartica se ne dodaje**. Pojam se može spomenuti unutar `description` SRODNE kartice koja ima važeći Wikipedia link (primjer: self-refinement spomenut u opisu kartice "Mutation", jer je koncept anchored mutation vezan za self-refine).

**Broj kartica po stranici — nema minimuma ni maksimuma.** Odluka iz s90: ne forsirati simetriju. `reader.html` ima svega 6 kartica (nema više relevantnog materijala); `about.html` ima 15 (zbog opsežne intelektualne loze/lineage sekcije). Kriterij je stvarna relevantnost, ne broj.

---

## 5. Kako DODATI karticu

1. **Odluči stranicu** (page key) — mora postojati u `CONCEPT_PAGES` u `nav.js`. Ako je stranica nova, prvo je dodaj u taj niz.
2. **Provjeri da pojam STVARNO ima Wikipedia članak** — web pretraga prvo (ne pretpostavljati).
3. **Potvrdi tačan slug prije upisa** — `curl -sS -o /dev/null -w "HTTP %{http_code} | final: %{url_effective}\n" -L https://en.wikipedia.org/wiki/SLUG`. Provjeri HTTP 200 i da nema neočekivanog redirecta (stari naziv članka može biti preusmjeren na novi slug — koristiti trenutni kanonski naslov). Pažljivo sa disambiguation zagradama i specijalnim znacima (provjereni primjeri iz s90: `Moby-Dick` sa crticom, `Strange_Case_of_Dr_Jekyll_and_Mr_Hyde` bez "The", `The_Big_Four_(novel)`, `Alice%27s_Adventures_in_Wonderland` URL-enkodiran apostrof).
4. **Odaberi icon** koji se ne poklapa sa postojećim iconima na ISTOJ stranici (izbjegavati vizuelne duplikate).
5. **Dodaj JSON objekat na KRAJ niza** za tu stranicu — konvencija projekta: nove kartice idu na kraj, ne na proizvoljnu poziciju.
6. **Validiraj JSON** (§7) — obavezno, ne opciono.
7. **Browser test** — jedina prava potvrda da se kartica prikazuje ispravno.

---

## 6. Kako IZMIJENITI ili OBRISATI karticu

**Izmjena:** pronađi karticu po `name` ili `wiki` (`grep -n '"wiki": "TAČAN_SLUG"' concepts.json`), izmijeni `description`/`icon`/`wiki` istim `str.replace` + `assert count==1` obrascem kao kod `nav.js`. Validiraj JSON poslije.

**Brisanje:** ukloni cijeli `{...}` objekat kartice iz niza za tu stranicu. **Pažnja na zareze** — brisanje prvog ili poslednjeg elementa niza čest je izvor slomljenog JSON-a (višak ili nedostajući zarez). Validiraj JSON ODMAH poslije brisanja, prije nego što nastaviš na sljedeću izmjenu.

---

## 7. Validacija JSON-a (obavezna, nakon SVAKE izmjene)

```bash
/home/balsam/buchenberg/venv/bin/python3 -c "import json; json.load(open('/var/www/buchenberg/data/concepts.json')); print('JSON OK')"
```

Ovo NIJE isto što i JS sintaksa provjera iz `KAKO-JeziciUI.md` — JSON je stroži format (nema komentara, nema trailing zareza, sve ključeve moraju biti u navodnicima). Nema `node` na serveru za alternativnu provjeru — `json.load` je kanonski i dovoljan alat.

---

## 8. Tehnička metoda izmjene (isti obrazac kao `nav.js`)

```bash
cd /var/www/buchenberg && venv_py=/home/balsam/buchenberg/venv/bin/python3 && $venv_py - << 'PYEOF'
import json
f = "data/concepts.json"
s = open(f, encoding="utf-8").read()

old = '<TAČAN POSTOJEĆI JSON FRAGMENT — anchor>'
new = '<NOVI JSON FRAGMENT>'

assert s.count(old) == 1, f"anchor count = {s.count(old)}"
s = s.replace(old, new)

json.load(open(f, encoding="utf-8"))  # provjeri STARI fajl je važeći prije pisanja (sanity)
open(f, "w", encoding="utf-8").write(s)
json.load(open(f, encoding="utf-8"))  # provjeri NOVI fajl je važeći poslije pisanja — OBAVEZNO
print("OK — JSON valid prije i poslije")
PYEOF
```

`assert s.count(old) == 1` prije pisanja (isto pravilo kao `nav.js` — anchor mora biti jedinstven), `json.load` odmah poslije pisanja (specifično za ovaj fajl — JSON ne prašta sintaksne greške kao JS).

---

## 9. Git

`concepts.json` JE pod git kontrolom — izuzetak od ostatka `data/` direktorijuma (koji je generisan i van gita). `.gitignore` koristi `data/*` + `!data/concepts.json` (restruktuirano u s90 baš iz ovog razloga). Ako se `.gitignore` ikad ponovo dira, provjeriti da ovaj izuzetak ostane.

---

## 10. Poznati slučajevi / lekcije

| Slučaj | Sesija | Detalj |
|---|---|---|
| self-refinement nema Wikipedia članak | 108 | Isključen iz kartica; spomenut u opisu srodne kartice "Mutation" umjesto toga |
| Ambiguozni slugovi (Moby-Dick, Jekyll&Hyde, Big Four, Alice) | 90 | Svi provjereni web pretragom PRIJE upisa — ne pretpostavljati slug iz naziva |
| `.gitignore` isključivao `concepts.json` zajedno sa ostatkom `data/` | 90 | Restruktuirano u `data/*` + `!data/concepts.json` |
| node nedostupan na serveru | više sesija | JSON validacija ide kroz Python `json.load`, ne kroz JS alat |

---

*Flavio & Claude · Buchenberg · KAKO-KeyConcepts.md · 6. jul 2026.*
