# Buchenberg — Plan parsiranja HTML → sentences tabela

**Datum:** 15. maj 2026. (v2)

---

## Struktura Gutenberg HTML fajla

```
<div id="pg-header">   ← PRESKAČEMO (metapodaci, licenca)
    <h2> naslov knjige
    <p>  Title, Author, Release date...
</div>

<h1> Naslov knjige     ← HEADING → sentences (sentence_type='heading')
<h3> CONTENTS          ← PRESKAČEMO (TOC — nije sadržaj knjige)

<h3> Chapter 1 ...     ← HEADING → sentences (sentence_type='heading')
<p>  tekst...          ← TEKST → sentences (sentence_type='text')
<p>  tekst...
<h2> Naslov priče ...  ← HEADING → sentences (sentence_type='heading')
<p>  tekst...
...

<div id="pg-footer">   ← PRESKAČEMO (licenca, pravni tekst)
```

**Pravilo:** Svi H tagovi (H1–H6) van `pg-header` i `pg-footer` → `heading`.
Jedini izuzetak: TOC blok (H tag čiji je tekst "CONTENTS" ili "TABLE OF CONTENTS").

---

## Pseudokod

```
FUNKCIJA parse_book(html_path, book_id):

    html = učitaj_fajl(html_path)

    # Korak 1: Izreži pg-header i pg-footer
    sadrzaj = izvuci_izmedju(html, pocetak_posle="pg-header", kraj_pre="pg-footer")

    # Korak 2: Parsiraj DOM — prolaz kroz sve H i P elemente redom
    block_no = 0
    elementi = izvuci_elemente(sadrzaj)  # H1-H6 i P tagovi, redom

    ZA SVAKI element U elementi:

        AKO je element H tag (H1–H6):
            tekst = izvuci_tekst(element)
            tekst = normalizuj(tekst)

            AKO tekst.upper() IN ['CONTENTS', 'TABLE OF CONTENTS']: PRESKOČI

            block_no += 1
            upiši u sentences:
                book_id       = book_id
                block_no      = block_no
                sentence_no   = 1            # heading je uvijek 1 rečenica
                text          = tekst
                word_count    = len(tekst.split())
                sentence_type = 'heading'

        AKO je element P tag:
            tekst = izvuci_tekst(element)
            tekst = normalizuj(tekst)

            AKO je tekst prazan: PRESKOČI

            # Korak 3: Split paragrafa na rečenice (spaCy)
            rečenice = spacy_sent_split(tekst)

            block_no += 1
            ZA SVAKU rečenicu, sentence_no = 1, 2, 3...:
                upiši u sentences:
                    book_id       = book_id
                    block_no      = block_no
                    sentence_no   = sentence_no
                    text          = rečenica
                    word_count    = len(rečenica.split())
                    sentence_type = 'text'

    VRATI broj upisanih rečenica
```

---

## Napomene

### Šta preskačemo
- `id="pg-header"` — cijeli div (metapodaci Gutenberga)
- `id="pg-footer"` — cijeli div (licenca)
- H tag čiji je tekst "CONTENTS" / "TABLE OF CONTENTS" — TOC blok

### Generalnost
- Skript ne pretpostavlja broj poglavlja, dubinu H tagova, niti strukturu knjige
- Radi jednako za roman (Frankenstein), detektivski roman (Hound) i zbirku priča (Poirot)
- Poravnatost je garantovana: `block_no` se inkrementira za svaki element, `sentence_no` unutar bloka

### Normalizacija teksta
- Strip HTML tagova (`<i>`, `<b>`, `<span>` itd.)
- Kolaps višestrukih razmaka i newline-ova u jedan razmak
- Strip leading/trailing whitespace
- Encoding: UTF-8

### spaCy sentence splitter
- Model: `en_core_web_sm`
- Ulaz: cijeli paragraf
- Izlaz: lista rečenica

---

## Redoslijed izvršavanja

```
1. INSERT INTO books (gutenberg_id, title, author, html_path) VALUES (...)
2. parse_book(html_path, book_id)
3. UPDATE books SET status='parsed' WHERE id = book_id
```

---

*Buchenberg · parser_plan v2 · 15. maj 2026.*
