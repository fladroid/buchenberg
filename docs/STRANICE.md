# STRANICE.md — Buchenberg web portal: stranica × menu tačka × naslov

Referentna tabela svih HTML stranica web portala, njihove menu tačke i vidljivog naslova u body-ju. Generisano iz stvarnog stanja fajlova (nav.js + HTML), ne iz pamćenja ili prošlih razgovora.

**Nastalo:** sesija 116, 6. jul 2026.

## Tabela

| HTML Stranica | Menu tačka | Naslov (vidljivi u body-ju) |
|---|---|---|
| index.html | Home | *(nema h1)* — hero brend "Buchenberg" + tagline "Open-source machine translation pipeline for classic literature" |
| about.html | About | About Buchenberg |
| stats.html | X-Ray Stats | X-Ray Statistics |
| books.html | Library | Library |
| nlp.html | NLP | Natural Language Processing |
| reader.html | Reader | *(nema fiksni)* — dinamički, ime trenutno otvorene knjige (`#book-title`) |
| learn.html | Learn | Language Learning |
| geometry.html | Geometry | Geometry of Meaning |
| art.html | Art | Art |

(Vrijednosti su EN — izvor `NAV_I18N.en` u `nav.js`. Menu tačka i naslov postoje na svih 5 jezika osim gdje je niže navedeno drugačije.)

## Otkriveni neskladi (s116)

1. **`art.html` naslov "Art" je hardkodovan u HTML-u, NIJE u `NAV_I18N`** — jedina stranica bez `_title` i18n ključa. Sve ostale (about/stats/geo/learn/nlp) imaju prevod na 5 jezika; Art ostaje "Art" bez obzira na odabrani UI jezik. Nije potvrđeno da li je namjerno.
2. **`books.html` `<title>` tag i dalje kaže "Books — Buchenberg"**, dok vidljivi `<h1>` kaže "Library" — `<title>` nije ažuriran nakon preimenovanja menu tačke u sesiji 72.
3. **`stats.html`**: menu tačka "X-Ray Stats" ≠ naslov "X-Ray Statistics" — različita formulacija za istu stranicu. Nije potvrđeno da li je namjerno (kraće u meniju) ili nesklad.
4. **`index.html` i `reader.html` nemaju fiksan naslov** u istom smislu kao ostale stranice — index koristi hero brend + tagline umjesto h1; reader je dinamičan po trenutno otvorenoj knjizi. Ne uklapaju se čisto u obrazac tri kolone.

## Svrha dokumenta

Nakon više od 100 sesija postalo je jasno da Claude — kao tekstualni AI bez pristupa vizuelnom prikazu stranice — ne može pouzdano znati koja je menu tačka povezana s kojom HTML stranicom, niti koji je naslov prikazan na kojoj stranici, osim ako to eksplicitno ne provjeri na serveru svaki put. Ovaj dokument je konsolidovana referenca umjesto oslanjanja na razbacane odluke iz pojedinačnih sesija — pisan svjesno protiv tog ograničenja.

---
*Flavio & Claude · Buchenberg · STRANICE.md · 6. jul 2026.*
