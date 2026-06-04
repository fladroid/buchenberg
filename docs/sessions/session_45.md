# Session 45 — Web portal: višestranična arhitektura

**Datum:** 4. jun 2026.
**Sesija:** 45
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Inicijalizacija sesije

README + posljednje 3 session docs (42, 43, 44) + stanje baze potvrđeno kroz README.
Memorija ažurirana — sve konzistentno.

---

### 2. Novi web portal — motivacija

Postojeći `index.html` bio je monolitna stranica (čitač). Flavio je izrazio želju da
web prisustvo bude bliže originalnoj ideji projekta: portal s jasnom hijerarhijom,
navigacijom i mjestom za sadržaj koji raste s projektom.

**Zahtjevi:**
- Glavna landing stranica s opisom projekta i objašnjenjem naziva "Buchenberg"
- Detaljna stranica o projektu i implementaciji
- X-Ray statistike iz sakupljenih podataka
- Lista prevedenih knjiga s karticama i linkovima
- Čitač kao zasebna stranica
- Wikipedia light stil (zadržan), dark mode toggle
- Navigacija konzistentna na svim stranicama
- UI jezik i dark mode persistiraju u `localStorage`

---

### 3. Shared stylesheet — `buchenberg.css`

Kreiran `/var/www/buchenberg/buchenberg.css` — zajednički CSS za sve stranice.

**Ključne komponente:**
- CSS varijable za light i dark mode (`[data-theme="dark"]`)
- `#bb-header` — sticky header s logom, navigacijom, UI lang bar, dark mode toggle
- `.bb-layout-sidebar` — grid layout za reader (220px + 1fr)
- `.bb-box` / `.bb-box-title` / `.bb-box-body` — surface box komponenta
- `.bb-toggle` / `.bb-toggle-wrap` — toggle switch (Show original, X-Ray)
- `.bb-infobox` — Wikipedia-stil infobox (float right)
- `.bb-badge` / `.bb-badge-coming-soon` — language badges, disabled state
- `.bb-btn` / `.bb-btn-primary` / `.bb-btn-disabled` — button varijante
- `.bb-hero` — landing page hero sekcija
- `.bb-cards` / `.bb-card` — grid kartice za books.html
- `.bb-section-title` / `.bb-section-subtitle` — naslovi sekcija
- `.bb-prose` — tipografija za about.html (serif, h2/h3, code, pre, table)
- `.bb-stats-grid` / `.bb-stat-card` — summary stat kartice
- `.bb-table` — stats tablice
- Responsive breakpoint na 700px (sidebar se skriva, gridi se stackaju)

---

### 4. Landing page — `index.html` (novi)

Zamjenjuje stari monolitni čitač.

**Sadržaj:**
- Hero sekcija: logo, tagline, opis projekta, objašnjenje naziva Buchenberg/Gutenberg
- Tri "pillar" kartice: Back-translation scoring / LLM judge / Sentence-level winner
- "Current status" — 4 stat kartice (broj knjiga, jezika, rečenica, modela) učitane live iz `data/books.json`
- Open source nota s linkovima na Gutenberg i Ollama
- CTA gumbi prema Books, About, X-Ray Stats

**I18N:** EN/DE/IT/HR/SR — hero tagline, sekcijski naslovi, labele stat kartica, CTA tekst.

---

### 5. Books stranica — `books.html`

Lista svih knjiga iz `data/books.json` kao kartice.

**Sadržaj kartice:**
- Naslov i autor (header)
- Broj rečenica i broj jezika (meta)
- Language badges (ISO 639-1, sortirani po abecedi nativnog naziva)
- Action gumbi:
  - **Read** → `reader.html?book={id}` (primary, aktivan)
  - **Gutenberg** → `gutenberg.org/ebooks/{gutenberg_id}` (aktivan)
  - **NER** → disabled, "coming soon" (placeholder za spaCy NER)
  - **Word cloud** → disabled, "coming soon" (placeholder)

**I18N:** EN/DE/IT/HR/SR — naslovi, labele, gumb tekst, "coming soon" poruka.

---

### 6. Reader — `reader.html`

Stari čitač iz `index.html` preseljen na `reader.html` s minimalnim izmjenama:
- Novi shared header i footer
- Dark mode podrška (CSS varijable iz `buchenberg.css`)
- Reader-specific CSS inlinovan u `<style>` blok
- **URL param `?book=ID`** — auto-select knjige pri otvaranju
  (`books.html` → "Read" otvara reader direktno na odabranoj knjizi)
- Sva funkcionalnost zadržana: Show original toggle, X-Ray toggle, infobox, score info, model badge

---

### 7. About stranica — `about.html`

Detaljna dokumentacija projekta.

**Sadržaj:**
- The name — objašnjenje Buchenberg/Gutenberg veze
- The problem — zašto back-translation scoring
- The pipeline — ASCII dijagram s formulama
- Models — tabela (gemma3, ministral, nllb, gemma4 kao sudija)
- Embeddings — e5-large vs MiniLM, razlog promjene
- Scoring — tabela metrika s težinama
- Infrastructure — foxuno + balsam, bez GPU-a
- Source material — Project Gutenberg
- Key learnings — 4 non-obvious nalaza iz razvoja

**Sidebar infoboxovi:** Project info / Target languages / Philosophy quote.

---

### 8. X-Ray Stats — `stats.html`

Agregatne statistike računate client-side iz JSON fajlova.

**Sadržaj:**
- 4 summary stat kartice (ukupno prevedenih rečenica, knjige, lang×book kombinacije, avg ts)
- **Winner distribution** — tabela s progress barom: koji model pobjeđuje i koliko %
- **Coverage** — tabela knjiga i jezika s brojem prevedenih rečenica
- **Score by language** — avg translation score i avg judge score po jeziku

**Napomena:** Stats se učitavaju client-side iz `tr_*.json` — isti JSON fajlovi koje koristi Reader. Nema zasebnog stats endpointa.

---

### 9. Logo — jednobojan

Na kraju sesije: `Buchen<span>berg</span>` (plavo-crni dvobojni logo) zamijenjen
jednostavnim `Buchenberg` — jednobojna boja teksta na svim 5 fajlova.

```bash
sed -i 's/Buchen<span>berg<\/span>/Buchenberg/g' \
  /var/www/buchenberg/index.html \
  /var/www/buchenberg/about.html \
  /var/www/buchenberg/books.html \
  /var/www/buchenberg/reader.html \
  /var/www/buchenberg/stats.html
```

---

## Struktura web fajlova na kraju sesije

```
/var/www/buchenberg/
├── buchenberg.css       ← novi shared stylesheet (dark mode, sve komponente)
├── index.html           ← novi landing page (zamjenjuje stari čitač)
├── about.html           ← novi: detaljan opis projekta
├── stats.html           ← novi: X-Ray statistike (live, client-side)
├── books.html           ← novi: lista knjiga s karticama
├── reader.html          ← preseljen čitač (stari index.html refaktorisan)
├── data/
│   ├── books.json
│   ├── orig_*.json
│   └── tr_*_*.json
└── BBOLD/               ← stari fajlovi (arhiva)
```

---

## Stanje baze — nepromijenjeno

| Knjiga | ID | Jezik | Rečenice | Status |
|--------|-----|-------|----------|--------|
| Hound | 1 | bs, hr | 350 | ✅ |
| Hound | 1 | af, de, es, fr, it, nl, sl, sr, pt, ro | 100 | ✅ |
| Big Four | 5 | pt | 100 | ✅ |
| Frankenstein | 8 | ro, it | 100 | ✅ |

---

## Otvoreno za sljedeće sesije

1. Proširenje Hound — svih 12 jezika na s101–s350
2. Proširenje PT (Big Four) i RO+IT (Frankenstein) na s101–s350
3. Refaktorisati `bb_web_export.py` da koristi `v_pobjednici` view
4. spaCy NER — kada bude spremno, aktivirati link na `books.html`
5. Word cloud — kada bude spremno, aktivirati link na `books.html`
6. `about.html` — prevesti na ostale jezike (trenutno samo EN sadržaj)
7. `stats.html` — razmisliti o dedicated `stats.json` koji generira `bb_web_export.py`
   umjesto client-side računanja iz tr_*.json

---

*Flavio & Claude · Buchenberg · Sesija 45 · 4. jun 2026.*
