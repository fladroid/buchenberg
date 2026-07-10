# Web Faza 3 — Fazni pobjednik i dublji stats sloj

**Status:** IZVRŠENO (sesija 123, 9. jul 2026.) — svih 8 koraka sprovedeno, vidi `session_123.md`. Ovaj dokument ostaje kao konceptualni nacrt/odluke (Nivo A/B). Analogan `WEB-FAZA1.md`
(koji je pripremio Fazu 2), ali za DB-upit / export sloj umjesto teksta/i18n.

**Razlika od Faze 1/2:** Faza 1/2 = tekst i i18n na postojećim podacima. Faza 3 = novi
podaci — izmjene u `bb_web_export.py` i/ili `bb_xray_export.py`, novi SQL upiti, novi
JSON izlazi. Veći rizik (dira export skripte koje pipeline koristi), veći dobitak
(otvara stvari koje trenutno NISU vidljive na webu ni u X-Ray modu).

---

## 1. Provjereno stanje u kodu (8. jul 2026, prije bilo koje izmjene)

### `bb_xray_export.py` — VEĆ ima fazu
`get_all_candidates()` selektuje `m.faza_id AS faza` po kandidatu. Reader X-Ray mod
(otvoren switch) već prikazuje "Phase" red po kandidatu (s115). **Ovo je već riješeno,
ne dira se.**

### `bb_web_export.py` — NEMA fazu na dva mjesta

**(A) `get_translations()`** (puni `tr_<knjiga>_<jezik>.json`, DEFAULT reader prikaz
bez X-Ray switcha) — SELECT ne uključuje `m.faza_id`. Reader trenutno NE MOŽE pokazati
iz koje faze dolazi prikazani (apsolutni) pobjednik van X-Ray moda, jer taj podatak
uopšte nije eksportovan u `tr_*.json`.

**(B) `get_stats()`** (puni `stats.json`, hrani `stats.html` winner tabelu) — win-rate
red grupisan `GROUP BY m.naziv, m.temperatura` — BEZ faze. Za novi par (glm-5.2,
mistral-large-3:675b) koji igra i fazu 1 i fazu 2 na istoj temperaturi (0.8), ovo
STAPA pobjede iz obje faze u jedan red. Rezultat: trenutni win-rate broj za
"glm-5.2 @0.8" ne govori da li su te pobjede iz baze, refine-a, ili mješavine.

### Baza — `bb_prev_recenica_faza` (fazni pobjednik, odvojena tabela)
Postoji od s112/s114, UNIQUE(prev_knjige_id, prevodi_recenica_id, faza_id) — čuva
pobjednika UNUTAR SVAKE FAZE POSEBNO (razlikuje se od `bb_prev_recenica`, koja čuva
SAMO apsolutnog pobjednika preko svih faza). `bb_web_export.py` ovu tabelu **nikad ne
dotiče** — potpuno neiskorišten izvor podataka za web.

**Pokrivenost (provjereno 8. jul):**

| Faza | Broj pobjednika |
|---|---|
| 1 (baza) | 287.978 |
| 2 (refine) | 18.210 (6.3% od faze 1) |

Svaka izmjena mora gracefully hendlati rečenice koje NEMAJU fazu 2 (94% korpusa) —
default/fallback prikaz ostaje kao danas.

---

## 2. Dva nivoa izmjene (rastuća složenost)

### Nivo A — jeftino: dodati `faza` gdje već postoji join na `bb_modeli`

`m.faza_id` je već dostupan u oba upita (`get_translations`, `get_stats`) kroz
postojeći JOIN na `bb_modeli` — samo nije u SELECT listi. Dodavanje je jedna linija po
upitu, bez nove tabele, bez novog JOIN-a.

**Omogućava:**
- Reader (van X-Ray): mala oznaka/ikonica na prikazanom prevodu — "iz faze 2" kad je
  primjenjivo, ništa kad nije (94% slučaja).
- Stats: `GROUP BY m.naziv, m.temperatura, m.faza_id` umjesto bez faze — winner tabela
  prestaje miješati baznu i refine pobjedu za isti model/temp.

**Ne omogućava:** poređenje "šta je faza 1 predlagala PRIJE refine-a" na rečenicama
gdje je faza 2 pobijedila — apsolutni pobjednik briše taj trag (samo JEDAN red po
rečenici u izvozu, onaj pobjednički).

### Nivo B — veći zahvat: uključiti `bb_prev_recenica_faza`

Novi upit koji za svaku rečenicu (gdje faza 2 postoji) povuče OBA pobjednika —
faza-1-pobjednika i faza-2-pobjednika — odvojeno, čak i kad je konačni apsolutni
pobjednik samo jedan od njih.

**Omogućava:**
- Reader "prije/poslije" prikaz: "Faza 1 je predlagala: ... (score 0.94) → Faza 2 je
  predložila: ... (score 0.97, POBJEDNIK)" — pravi uvid u self-refine, ne samo krajnji
  rezultat.
- Stats "Tabela 2" (by-configuration) kako je bilo zamišljeno još u s104: model × temp
  × faza kao posebna kolona, sa win-rate računatim u odnosu na PRAVI nazivnik za tu
  fazu (koliko je puta ta konfiguracija uopšte igrala u toj fazi), ne izmiješano.

**Cijena:** novi JOIN na `bb_prev_recenica_faza` po jeziku/knjizi (287k+18k redova),
novi JSON polja u `tr_*.json` (veći fajlovi) ili poseban `phases_<knjiga>_<jezik>.json`
export — treba odlučiti format.

---

## 3. Stranice na koje ovo utiče

### `stats.html`
Trenutno: JEDNA tabela (`winner-table-wrap`), grupisana po (model, temp), miješa faze
za novi par. Cilj (dogovoreno još s104, nikad implementirano — potvrđeno 8. jul,
`grep` na serveru: `config-table-wrap` i `renderConfigTable` ne postoje):
- **Tabela 1** (by-engine, Nivo A dovoljan): 3 reda — po ENGINE-u (LLM opšte namjene,
  LLM opšte namjene, namjenski MT), agregirano preko svih konfiguracija.
- **Tabela 2** (by-configuration, Nivo A dovoljan uz faza kolonu): red po
  model×temp×faza, win-rate na tačnom nazivniku za tu kombinaciju.

**Otvoreno pitanje iz 30. juna (nikad odgovoreno, prenosim ovdje da se ne izgubi):**
da li win-rate PO ENGINE-U (Tabela 1) treba miješati bazu i refine nazivnik u jedan
broj, ili engine-red treba prikazivati dva odvojena broja (baza win-rate / refine
win-rate)? Ovo je dizajn-odluka, ne tehničko pitanje — treba Flaviova odluka prije
pisanja upita za Tabelu 1.

### `reader.html`
Trenutno: X-Ray mod (otvoren switch) već pokazuje fazu po kandidatu (s115, gotovo).
DEFAULT prikaz (switch zatvoren) ne pokazuje ništa o fazi — prikazan prevod izgleda
identično bez obzira da li je iz faze 1 ili 2.

- **Nivo A dovoljan** za: mala oznaka na default prikazu ("refinovano" ili slično) kad
  je apsolutni pobjednik iz faze 2 — bez otvaranja X-Ray moda.
- **Nivo B potreban** za: "prije/poslije" prikaz uporedo (šta je faza 1 predlagala vs
  šta je faza 2 predložila) na onih 18.210 rečenica gdje oboje postoji.

### `about.html`
Bez izmjene — Self-refinement sekcija (s120) već objašnjava koncept tekstualno, ne
zavisi od ovih podataka.

---

## 4. Redoslijed ako se odluči za implementaciju

1. **Odluka Nivo A vs Nivo B** (ili A prvo, B kasnije kao poseban blok) — Flaviova
   odluka, nezavisno po stranici (stats i reader ne moraju ići zajedno).
2. **Odluka o Tabeli 1 win-rate mješavini** (otvoreno pitanje iz §3).
3. Izmjena `bb_web_export.py` (SELECT + GROUP BY dopune, Nivo A) i/ili nova funkcija za
   `bb_prev_recenica_faza` (Nivo B) — testirati na JEDNOJ knjizi/jeziku prije punog
   exporta.
4. Re-generisati `stats.json`/`tr_*.json` za pogođene knjige (ili sve — Flaviova
   odluka o obimu).
5. HTML/JS izmjene na `stats.html`/`reader.html` (nova tabela, nova oznaka/prikaz) —
   isti obrazac kao Faza 2 (str.replace + assert count==1, browser test, BB_VERSION
   step-marker po stranici).
6. Session dokument + README + memorija.

---

## 5. Šta OVAJ dokument namjerno NE pokriva

- Pokretanje bilo kakvog pipeline runa (Flaviov posao, ne planira se ovdje).
- SR `geo_c4_p1` typo, word cloud ćirilica-bug — sitni, nevezani zadaci sa s120.
- Diverzifikacija (druga familija modela) — poseban budući okvir, van dosega ovog
  dokumenta.

---

*Nacrt pisan 8. jul 2026. — IZVRŠENO u sesiji 123 (9. jul 2026.), vidi `session_123.md`.*
