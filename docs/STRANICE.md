# STRANICE.md — Buchenberg web portal: stranica × menu tačka × naslov

Referentna tabela svih HTML stranica web portala, njihove menu tačke i vidljivog naslova u body-ju. Generisano iz stvarnog stanja fajlova (nav.js + HTML), ne iz pamćenja ili prošlih razgovora.

**Nastalo:** sesija 116, 6. jul 2026.

## Tabela

| HTML Stranica | Menu tačka | Naslov (vidljivi u body-ju) |
|---|---|---|
| index.html | Home | *(nema h1)* — hero brend "Buchenberg" + tagline "Open-source machine translation pipeline for classic literature" |
| about.html | About | About Buchenberg |
| stats.html | Stats (od s120, bilo "X-Ray Stats") | Statistics (od s120, bilo "X-Ray Statistics") |
| books.html | Library | Library |
| nlp.html | Entities (od s127, bilo "NLP") | Named Entities & Relations (od s127, bilo "Natural Language Processing"; word cloud uklonjen, dodan classic/with-llm toggle) |
| reader.html | Reader | *(nema fiksni)* — dinamički, ime trenutno otvorene knjige (`#book-title`) |
| learn.html | Learn | Language Learning |
| geometry.html | Geometry | Geometry of Meaning |
| art.html | Art (od s120: `art_title` i18n ključ × 5 jezika, prije hardkod bez ključa) | Art |

(Vrijednosti su EN — izvor `NAV_I18N.en` u `nav.js`. Menu tačka i naslov postoje na svih 5 jezika osim gdje je niže navedeno drugačije.)

## Neskladi otkriveni s116 — SVI RIJEŠENI u s120 (WEB-FAZA1.md → Faza 2 implementacija)

1. ~~`art.html` naslov "Art" hardkodovan, bez `_title` ključa~~ — RIJEŠENO s120: `art_title` dodan × 5 jezika (Art/Kunst/Arte/Umjetnost/Уметност), h1 dobio `id="art-title"`.
2. ~~`books.html` `<title>` "Books" ≠ h1 "Library"~~ — RIJEŠENO s120: `<title>` → "Library — Buchenberg"; `books_title` usklađen na "Library" ekvivalent svih 5 jezika (bio "Translated Books" na DE/IT/HR/SR).
3. ~~`stats.html` menu "X-Ray Stats" ≠ naslov "X-Ray Statistics"~~ — RIJEŠENO s120 (Flaviova odluka): "X-Ray" uklonjen iz sve tri tačke (menu/`<title>`/h1) → dosljedno "Stats"/"Statistics" na svih 5 jezika.
4. **`index.html` i `reader.html` nemaju fiksan naslov** u istom smislu kao ostale stranice — index koristi hero brend + tagline umjesto h1; reader je dinamičan po trenutno otvorenoj knjizi. Namjerno, ne nesklad (Flavio s118) — ne uklapaju se u obrazac tri kolone, i ne treba da se uklapaju.

## Svrha dokumenta

Nakon više od 100 sesija postalo je jasno da Claude — kao tekstualni AI bez pristupa vizuelnom prikazu stranice — ne može pouzdano znati koja je menu tačka povezana s kojom HTML stranicom, niti koji je naslov prikazan na kojoj stranici, osim ako to eksplicitno ne provjeri na serveru svaki put. Ovaj dokument je konsolidovana referenca umjesto oslanjanja na razbacane odluke iz pojedinačnih sesija — pisan svjesno protiv tog ograničenja.

---
*Flavio & Claude · Buchenberg · STRANICE.md · 6. jul 2026.*
