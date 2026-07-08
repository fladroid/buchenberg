# KAKO-JeziciUI.md — Kako mijenjati, dodavati i brisati tekstove u multijezičkom UI-u

Konsolidovana referenca iz README §"Web how-to" + sesija 61, 77–82, 108, 114, 115. Cilj: da bilo ko (uključujući Claude bez pristupa browseru) može samostalno izvesti izmjenu i18n teksta bez ponavljanja poznatih bagova.

**Nastalo:** sesija 116, 6. jul 2026.

---

## 1. Arhitektura — izvor istine

Tekst prikazan na stranici **NIJE** ono što piše u HTML hardkodu. Izvor istine je **i18n rječnik `NAV_I18N`** u `/var/www/buchenberg/nav.js`.

- **5 jezičkih blokova:** `en`, `de`, `it`, `hr`, `sr` (`NAV_I18N = { en:{...}, de:{...}, it:{...}, hr:{...}, sr:{...} }`).
- **Ključevi su prefiksovani po stranici:** `index_*`, `about_*`, `stats_*`, `books_*`, `nlp_*`, `geo_*`, `learn_*`, `art_*`.
- **Apply-kod je U SAMOJ STRANICI** (`<page>.html`, inline `<script>`), **NE** u `nav.js`. Tipičan obrazac:
  ```js
  const x = t('kljuc');
  if (x && x !== 'kljuc') document.getElementById('id').innerHTML = x;
  // ili .textContent za čist tekst bez HTML-a unutra
  ```
- **JS prepisuje hardkod na SVAKOM jeziku, uključujući EN.** Hardkodovan tekst u HTML-u je samo **no-JS fallback** — nikad ono što korisnik stvarno vidi kad JS radi (a radi skoro uvijek).
- Poziv apply-funkcije mora ići nakon što je DOM učitan i nakon definicije funkcije — `DOMContentLoaded`, ne inline poziv usred dokumenta prije definicije (bag: about.html s78 — stranica prazna dok se ručno ne promijeni jezik).

### Kritična posljedica ove arhitekture (uzrok najčešćeg bага)
Ako neko (uključujući Claude) **izmijeni tekst direktno u HTML hardkodu** misleći da je to ono što se prikazuje — izmjena će raditi SAMO na jeziku gdje rječnik slučajno nema taj ključ (fallback ostaje), a bit će **nevidljivo pregažena** na svakom jeziku gdje ključ postoji (uključujući EN). Ovo se dogodilo u s108: izmjena hardkoda izgledala je tačna na HR/SR ekranu (jer je stari prevod slučajno bio ispravan za taj kontekst), ali EN je pokazivao stari, netačan tekst. **Pravilo:** svaka trajna izmjena teksta ide u `nav.js` rječnik. Hardkod se dira samo kao no-JS fallback, nikad kao "pravi" sadržaj.

---

## 2. `reader.html` — standard od s120, uz jedan navedeni izuzetak

`reader.html` je od s120 MIGRIRAN u `NAV_I18N` sistem — nav + kontrole (14 `reader_` ključeva × 5 jezika) prate isti obrazac kao ostale stranice. Prije s120 imao je vlastiti, zaseban `const I18N = {...}` mehanizam (odluka iz s77/s78, potvrđena u s82 tabeli statusa) — ta arhitektura je obrisana u s120 (session_120.md).

**Preostali navedeni izuzetak:** X-Ray legenda i X-Ray Full mod tekstovi ostaju EN hardkod, namjerno neprevedeni na bilo kom jeziku (isti obrazac kao Key Concepts kartice, §Web how-to u README). Ovo NIJE propust nego svjesna odluka iz same X-Ray implementacije.

---

## 3. Kako DODATI novi tekst / novi ključ

**Checklist (redosljed fiksan):**
1. Dodaj ključ u **svih 5** jezičkih blokova u `nav.js` (`index_novi:"...",` u `en`, `de`, `it`, `hr`, `sr` — svaki na svom jeziku, ne kopija EN-a).
2. Dodaj apply-liniju u `<page>.html` inline scriptu: `t('novi')` → `getElementById('novi-id')`.
3. Element u HTML-u mora imati taj `id`.

**Preskočiš (1)** → tekst ostaje hardkod-EN na svim jezicima.
**Preskočiš (2)** → rječnik postoji ali se nikad ne primjenjuje — vidljivo je samo hardkod.
**Preskočiš (3)** → apply-linija ne nalazi element, ništa se ne dešava.

**Sva tri propusta su TIHA — nema greške u konzoli, ni pada stranice.** Jedini način da se otkriju je provjera u browseru na svakom jeziku, ili grep provjera da ključ postoji i da se stvarno poziva (vidi §7 Verifikacija).

---

## 4. Kako IZMIJENITI postojeći tekst

Isto pravilo kao dodavanje, ali cilj izmjene je **vrijednost ključa u `nav.js`**, ne HTML. Koraci:
1. Pronađi tačan ključ i njegovu trenutnu vrijednost u `nav.js` za jezik koji mijenjaš (`grep -n "kljuc:" nav.js`).
2. **Pročitaj doslovan sadržaj prije zamjene** — multiline blokovi (npr. `how_desc`) razlikuju se po jeziku (prelomi, navodnici, HTML tagovi unutra). Ne pisati `str.replace` naslijepo za jezik čiji sadržaj nisi vidio (lekcija s115).
3. Ponovi za svih 5 jezika ako izmjena treba biti dosljedna na svima (npr. uklanjanje imena modela iz opisa — s115 primjer).
4. HTML fallback (hardkod) po želji ažurirati radi konzistentnosti — ali on nije ono što korisnik vidi dok JS radi.

---

## 5. Kako OBRISATI ključ ("mrtvi ključevi")

Ključ postaje "mrtav" kad postoji u `nav.js` rječniku ali ga stranica više ne poziva (otkriveno u s115: `index_funnel_*`, `index_lbl_*`, `index_sec_status`, `index_cta_*` — ostaci stare verzije Home stranice).

**Prije brisanja bilo kojeg ključa:**
1. `grep -n "t('kljuc')\|getElementById('kljuc-id')" <page>.html` — potvrdi da se STVARNO ne poziva nigdje na toj stranici.
2. Provjeri i druge stranice ako je ključ generički imenovan (rijetko, ali moguće preklapanje).
3. Ako potvrđeno mrtav — obriši iz svih 5 jezičkih blokova (isti anchor/assert obrazac kao dodavanje, obrnuto).
4. Ne brisati "za svaki slučaj" bez grep potvrde — bolje ostaviti mrtav ključ nego slučajno obrisati aktivan.

**Napomena:** mrtvi ključevi sami po sebi ne štete (ne renderuju se, ne usporavaju stranicu) — čišćenje je higijena, ne hitnost.

---

## 6. Kako dodati i18n na SASVIM NOVU stranicu (od nule)

Na osnovu redoslijeda kojim su about.html, art.html, geometry.html prošle kroz i18n (s77–s82):

1. Za SVAKI vidljiv tekstualni element odluči prefiks ključa (`<page>_*`) — naslov, podnaslov, sekcije, pasusi, tabele, dugmad, legende.
2. Insertuj ključeve u svih 5 `NAV_I18N` blokova odjednom (ili jezik po jezik — sporije ali sigurnije za prve pokušaje).
3. HTML: svaki element koji nosi prevodivi tekst dobija `id`; sadržaj ostaje kao hardkodovan EN fallback.
4. Inline `<script>` na stranici: apply-funkcija (obrazac `applyPageI18n()`) koja za svaki ključ radi `getElementById(id).textContent/innerHTML = t(kljuc)`; poziva se na `DOMContentLoaded` i ponovo na promjenu jezika (`BB_NAV.onLangChange`).
5. **Testiraj JEDAN jezik potpuno prije nego pređeš na svih pet** — batch izmjene bez međuprovjere u browseru direktan su uzrok kumuliranih bagova (lekcija s78: tri odvojena baga otkrivena tek na kraju jer se nije testiralo usput).

---

## 7. Tehnička metoda izmjene (na serveru)

**Alat:** Python heredoc, NE `sed` (sed ne radi pouzdano za višelinijske zamjene — poznato pravilo cijelog projekta).

```bash
cd /var/www/buchenberg && venv_py=/home/balsam/buchenberg/venv/bin/python3 && $venv_py - << 'PYEOF'
f = "nav.js"
s = open(f, encoding="utf-8").read()

old = '<TAČAN POSTOJEĆI TEKST — anchor>'
new = '<NOVI TEKST>'

assert s.count(old) == 1, f"anchor count = {s.count(old)}"
s = s.replace(old, new)
open(f, "w", encoding="utf-8").write(s)
print("OK")
PYEOF
```

**Pravila za anchor:**
- **Uvijek prvo pročitati stvarni sadržaj** (`sed -n 'LINE,LINEp' nav.js`) prije nego što konstruišeš anchor — razlike u crtici (`—` UTF-8 vs `\u2014` escape), razmacima ili navodnicima lome poklapanje.
- **Ćirilica (SR):** koristiti literalni ćirilični string kao anchor direktno u heredocu (quoted delimiter `<<'PYEOF'` čuva UTF-8), ne rekonstruisati preko Unicode escape sekvenci.
- **`assert s.count(old) == 1`** prije svakog pisanja — ako anchor nije jedinstven ili ne postoji, assert puca i NIŠTA se ne piše. Ovo je zaštita, ne formalnost — pusti da padne umjesto da nagađaš.

**Strukturna zamka unutar `NAV_I18N` bloka (bag s79, ozbiljan — slomio je cijeli sajt):**
Zadnji ključ u jezičnom bloku izgleda `posljednji_kljuc:"vrijednost" },` — taj `" },` **istovremeno** zatvara i vrijednost ključa I sam jezični objekat (`}`) I odvaja ga zarezom od sljedećeg jezika. Ako anchor traži "prvi `\" },`" od neke tačke unutra, može pogoditi kraj CIJELOG jezičnog bloka umjesto kraja jednog ključa — insertovani ključevi tad završe IZVAN ispravnog `lang` objekta, što lomi JS sintaksu na cijelom sajtu (`Missing initializer in const declaration`).
**Ispravan obrazac:** pronađi zadnji postojeći ključ, promijeni njegov završetak iz `"` u `",` (dodaj zarez), pa dodaj nove ključeve, gdje SAMO poslednji novi ključ završava sa `" },` (zatvara blok).

**Navodnici u HTML unutar JS stringova:**
String koji sadrži HTML sa atributima (npr. `<a href="...">`) mora koristiti backtick template literal ili single-quote za HTML atribute — NIKAD double-quote unutar double-quote JS stringa (bag s78: `Unexpected identifier` jer je `href="https"` slomio parsing).

---

## 8. Verifikacija

**Nema `node` instaliranog na serveru** — `node --check nav.js` ili `node -c` NEĆE raditi (pokušano i otkriveno kao slijepa ulica u s115). Ne izmišljati alate koji ne postoje.

**Kanonska verifikacija (dvoslojna):**

1. **Strukturna (grep/Python, prije bilo kakvog browser testa):**
   - Broj backtick-ova mora biti paran.
   - Broj vitičastih zagrada `{`/`}` treba biti balansiran — **OPREZ:** template placeholderi unutar JS string literala kao `{n}` ili `{lang}` (npr. `"{n} of {total} sentences"`) NISU strukturne zagrade i lažno će pokvariti prebrojavanje ako se ne isključe (lažna uzbuna s79, SR blok).
   - `grep -c "kljuc:" nav.js` — potvrdi tačan broj pojavljivanja (5 za sve jezike, ili 1 ako namjerno samo jedan).
2. **Funkcionalna (JEDINA prava potvrda):** **browser test** — otvoriti stranicu, ručno prebaciti kroz svih 5 UI jezika, vizuelno potvrditi da se tekst mijenja i da ništa nije prazno/slomljeno. Claude ovo ne može uraditi sam (nema pristup vizuelnom prikazu) — **Flavio potvrđuje u browseru**, Claude priprema i predlaže šta tačno provjeriti.

---

## 9. Poznati bagovi — ledger (ne ponavljati)

| Bag | Sesija | Uzrok | Fix |
|---|---|---|---|
| Nova stranica dodana, nav slomljen na drugim stranicama | 61 | Nav bio hardkodovan po stranici, bez centralnog fajla | Centralni `nav.js` sa `document.write` |
| `nlp_*` ključevi izvan EN bloka | 77 | Insert izvan zatvarajuće `}` jezičnog objekta | Ispravan anchor na zadnji ključ unutar bloka |
| `Unexpected identifier 'https'` | 78 | Double-quote HTML atribut unutar double-quote JS stringa | Backtick ili single-quote za HTML atribute |
| about.html prazna dok se ručno ne promijeni jezik | 78 | `applyPageI18n()` pozvan inline prije definicije funkcije | Poziv na `DOMContentLoaded` |
| Svih 250 `art_*` ključeva izvan `NAV_I18N`, sajt slomljen | 79 | Anchor pogodio kraj CIJELOG EN bloka umjesto kraja jednog ključa | Ispravljen anchor: `" },\n...art_subtitle:` → `",\n...art_subtitle:` |
| Lažna uzbuna: SR blok "neuravnotežen" | 79 | `{n}`/`{lang}` template placeholderi brojani kao strukturne zagrade | Isključiti template placeholdere iz brojanja |
| SR `geo_*` ključevi u `NAV_LINKS` umjesto `NAV_I18N.sr` | 82 | Anchor (`about_sidebar_authorship_text`) postojao u pogrešnom kontekstu za SR | Python skripta izvukla blok i insertovala na ispravno mjesto |
| Legenda scatter plota nema SR boju | 82 | Ne-i18n stara greška, otkrivena usput | Dodana SR stavka + i18n legend labele |
| Izmjena hardkoda u index.html "nije radila" na EN | 108→s114 otkriveno | Izmjena u HTML hardkodu pregažena `nav.js` rječnikom pri učitavanju | Sve izmjene idu u `nav.js`, ne u hardkod |
| Mrtvi ključevi (`index_funnel_*` i dr.) | 115 | Ostaci stare verzije stranice, stranica ih više ne poziva | Otkriveno grep-om; cleanup kao zaseban zadatak, nije hitno |

---

## 10. Trenutni status po stranicama (provjeri prije oslanjanja — može biti zastarjelo)

Prema s82 tabeli statusa (posljednja poznata potpuna evidencija — provjeriti grep-om ako je prošlo dosta sesija):

| Stranica | Status (na dan s82) |
|---|---|
| stats.html | ✅ Potpun |
| books.html | ✅ Potpun |
| index.html | ✅ Potpun (sadržaj poslije mijenjan više puta, npr. s108, s115) |
| nlp.html | ✅ Potpun |
| about.html | ✅ Potpun |
| art.html | ✅ Potpun (od s120: `art_title` ključ dodan × 5 jezika, h1 više nije hardkod) |
| geometry.html | ✅ Potpun |
| reader.html | ✅ Potpun od s120 (migriran u NAV_I18N, `reader_` prefiks); X-Ray legenda = navedeni EN izuzetak |
| learn.html | Nizak prioritet, status na dan s82 nepoznat/TODO — provjeriti prije oslanjanja |

---

*Flavio & Claude · Buchenberg · KAKO-JeziciUI.md · 6. jul 2026.*
