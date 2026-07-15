# Session 138 — 15. jul 2026.

## Fokus
Dva web poboljšanja (X-Ray faza po kandidatu, nlp.html metod-kartice), pa konceptualno
istraživanje veze NER↔prevod i sažetak↔prevod kao kontekst-injection za kvalitet prevoda.
Istraživačka nit zatvorena negativnim nalazom. Dvije odluke na kraju sesije.

## Zdravlje na početku
50.624 rečenice · 1.582.660 prevoda · 302.168 pobjednika. BB_VERSION s136
(buchenberg 9f75393, buchenweb 11fb450). 167 poznatih rupa (sve faza 1, retired
modeli, prio 2 po s136 odluci). Sve zeleno.

## Zdravlje na kraju
Korpus nepromijenjen (nijedan prevod nije upisan u bazu — svi testovi standalone,
van produkcije). Web izmijenjen: BB_VERSION s136 → s138.2.

---

## 1. Web — X-Ray faza po kandidatu (reader.html)

**Flaviov zahtjev:** U readeru, "refined" badge pokazuje fazu pobjednika kroz
before/after panel, ali X-Ray Full mod ne pokazuje iz koje je faze svaki pojedinačni
kandidat (pobjednik ili ne).

**Nalaz:** `bb_xray_export.py` VEĆ izvozi `"faza": faza` (iz `m.faza_id`) po kandidatu
— podatak je u svim `xray_*.json` fajlovima od s114. Problem je bio isključivo
frontend: `renderXrayPage()` gradi `.xf-card` (model, temp, ★ winner) ali nikad
nije čitao `c.faza`. Bez backend izmjene, bez re-exporta.

**Izmjena (reader.html, renderXrayPage()):** dodat jedan red u label kolonu kartice —
`(c.faza != null ? '...' + t('phase_n').replace('{n}', c.faza) + '...' : '')`.
Koristi postojeći i18n ključ `reader_phase_n` ("Phase {n}", preveden ×5 jezika od s135)
i postojeći `t()` helper. Isti obrazac kao `togglePhases()` panel.

**Verifikacija (Flavio, browser):** `reader.html?book=22` (hr, faze 1/2/3) — Phase N
se pojavljuje na svakoj kartici. Radi kako je zamišljeno.

**Commit:** buchenweb `5feb09e` — BB_VERSION s138.1. Push potvrđen.

---

## 2. Web — nlp.html metod-kartice postaju klikabilni birač

**Flaviov problem (sa screenshotom):** tri metod-tastera (Classic / With LLM / DocRE)
su vrlo mali i neuočljivi; Flavio stalno klikće na veliku karticu-opis ispod nadajući
se da će prebaciti pogled, ali kartica nije klikabilna — ništa se ne dešava.

**Dijagnoza:** mali tasteri `.nlp-method-btn` (font 0.8rem) su bili JEDINI stvarni
kontroler; velike kartice `.nlp-mcard` ispod su imale samo `.active` klasu (vizuelnu,
suptilnu) ali NIJEDAN klik handler. Izgledale klikabilno, nisu bile.

**Flaviove dvije opcije:** (1) veći tasteri poravnati s karticama + klik na opis vodi
gdje i taster; (2) taster integrisan u opis. **Odabrana opcija 2** (Claudeov argument:
kod već ima `.nlp-mcard.active` logiku koja prati aktivnu metodu — kartica kao jedini
kontroler znači manje pokretnih dijelova, nema rizika desinhronizacije dva paralelna
kontrolera).

**Izmjena (nlp.html, tri str.replace):**
1. `.nlp-mcard` — veći padding (14/16px), `cursor:pointer`, hover (border accent),
   jači active (`box-shadow 0 0 0 2px accent` + `.nlp-mcard-h` obojen accentom),
   naslov 0.85rem→1rem bold.
2. `#nlp-method-bar { display: none !important; }` — stari mali tasteri skriveni
   trajno, ali OSTAJU u DOM-u i rade ispod haube (postojeća logika ih i dalje ažurira).
3. Klik/keydown na `.nlp-mcard` PROKSIRA klik skrivenom `.nlp-method-btn` istog metoda
   (`getElementById('nlp-method-'+method).click()`) — sva postojeća logika (provjera
   dostupnosti sloja, DocRE vidljivost) se ponovo koristi, nula duplikacije. Dodat
   `tabindex`/`role=button`/Enter/Space za pristupačnost.

**Verifikacija (Flavio, browser):** kartice sad izgledaju kao pravi tasteri, klik bilo
gdje na karticu mijenja pogled, aktivna kartica jasno istaknuta. DocRE kartica i dalje
nestaje kod knjiga bez relacija.

**Commit:** buchenweb `4270b02` — BB_VERSION s138.2. Push potvrđen.

---

## 3. Konceptualno istraživanje — NER↔prevod i sažetak↔prevod (ZATVORENO)

Nastavak otvorenog pitanja iz s137 ("možda je seed ipak potreban uz NER"). Kroz razgovor
se pretvorilo u širu istragu: može li se prevod poboljšati globalnim kontekstom (NER
relacije ili sažetak knjige) u promptu prevodioca. **INVARIJANTA cijelo vrijeme:** sudija
(gemma4:31b) slijep i fiksan, kontekst SAMO prevodiocu, nikad sudiji (s124 princip);
kosinus nedirnut. Sve što se mijenja je na strani prevoda.

### 3.1 Flaviov cilj (razjašnjen)
Na pitanje šta je meta NER-hinta, Flavio: **opšta kvaliteta prevoda po NAŠEM scoreu**
("znam da viša ocjena nije automatski bolji prevod, ali dok nemamo ništa drugo, toga se
držimo"). To pojednostavljuje eksperiment — nema posebnog ti/vi evaluatora, sudija+kosinus
presuđuju kao za sve ostalo.

### 3.2 Šta je "NER" kao hint
Tri sloja koja imamo, filtrirana po korisnosti za prevod:
- **Entiteti** (imena/tipovi) — plauzibilno korisni (spriječiti pogrešnu deklinaciju imena).
- **Co-occurrence** — odbačeno (statistika blizine, bez značenja za prevod).
- **DocRE relacije** — nose značenje odnosa (friend/enemy/servant + afinitet); jedini
  sloj sa semantikom odnosa.
Flaviov instinkt "globalno za cijelu knjigu, ne po rečenici" — konzistentan sa smislom
cijele DocRE linije (odnos živi IZNAD rečenice; to je bio cijeli razlog gradnje DocRE).
Takođe jezično/knjižno neutralno: relacija izvučena iz EN originala, ista za sve ciljne
jezike; isti kod za svaku knjigu.

### 3.3 Test C (NER, 3 verzije) — /tmp/test_ner_c.py
Knjiga 22, hr, glm-5.2@0.8, 5 dijaloških rečenica (poz 101,105,110,111,112).
Tri prompta: **A** gol / **B** +svih 85 relacija / **C** +32 relacije sa `fine`.
(k22 ima 85 relacija: 32 sa fine = socijalna mapa, 53 bez = radnje+geografija.)

Ključni rezultat, rečenica 101 "Don't move, I beg you, Watson." (Holmes→Watson):
```
A gol : Ne mičite se, preklinjem VAS, Watsone.    → "vi"
B +85 : Ne pomičite se, preklinjem VAS, Watsone.  → "vi"
C +32 : Nemoj se micati, preklinjem TE, Watsone.  → "ti"
```
**Dva nalaza:** (1) C (samo fine) jedina promijenila registar ka "ti" — NER kontekst
MOŽE promijeniti gramatiku, za razliku od s137. (2) B (svih 85) pala na "vi" kao gol A —
**geografski/radni šum RAZBLAŽUJE signal; manje čistijeg konteksta > više šumnog.**
Ostale razlike kozmetičke.

### 3.4 Flaviov preokret — NER je pogrešan alat
Flavio (iz vlastitog iskustva): gledao Holmes/Watson filmove sinhronizovane na njemački —
oslovljavaju se sa "Sie" (vi). Šekspirovi ljubavnici na "vi". Djeca roditeljima "vi" u
tom dobu. **Zaključak: "ispravan" ti/vi izbor je funkcija EPOHE, KULTURE, ciljnog jezika
i konvencije prevođenja — NE prosta posljedica relacije friend/lovers/parent.** To ruši
premisu s koje smo krenuli (mislili smo "prijatelji → ti" je ispravno; naša "pobjeda" C
iz 3.3 bila je zasnovana na modernom očekivanju, možda POGREŠNA za viktorijanski registar).

**Dublji nalaz:** DocRE daje STRUKTURU odnosa, a zadatak traži REGISTAR I EPOHU — dvije
različite ose. NER ne sadrži informaciju koju zadatak traži. Nije loš alat, nego pogrešan
alat. **Flaviova odluka: definitivno odustajem od NER-prevod veze u ovoj fazi.**

### 3.5 Sažetak kao alternativa — Flaviova ideja
Flavio: jednostavnije bi bilo da LLM prepriča knjigu u ~20 rečenica i to damo kao globalni
ulaz. Ideja konceptualno tačnija — sažetak prirodno hvata epohu/registar/atmosferu koju
relacija ne nosi. Odluka: probati prije gradnje (isti princip kao NER).

**Extra model za sažetak:** pošto se sažetak pravi JEDNOM po knjizi (van vruće petlje),
možemo potrošiti jači/skuplji model. Provjera /api/show (README §15): deepseek-v4-pro
(1.6T, ctx 524k, thinking), kimi-k2.6 (1.04T), qwen3.5:397b, minimax-m3 (nema param).
Odabran **deepseek-v4-pro** (najveći, najveći kontekst, jasne karakteristike). Probni
poziv: tačno pogodio "kasna viktorijanska epoha, gornja klasa/plemstvo" — registar koji
NER nije mogao dati.

### 3.6 Test sažetak (2 verzije, pa 3) — /tmp/test_sazetak.py, /tmp/test_sazetak3.py
Isti model prevoda (glm-5.2@0.8), iste rečenice. deepseek-v4-pro pravi "prevodilački
brief" (fokus: epoha, klasa, registar, konvencije oslovljavanja) iz prvih 200 rečenica k22.

**deepseek brief je izvanredan artefakt** — razlikuje dva registra (moderni glas 1880-ih
vs arhaični rukopis 1742), daje EKSPLICITNA pravila oslovljavanja (Holmes↔Watson topao/
neformalan, svi↔Mortimer formalno "sir"/"Dr."), hvata M.R.C.S. "Mr." distinkciju. Tačno
informacija koja fali NER-u.

**Prvi prolaz (test_sazetak.py), rečenica 101:**
```
A gol      : Ne mičite se, preklinjem VAS, Watsone.    → "vi"
D +sažetak : Nemojte se pomicati, molim VAS, Watsone.  → "vi"  (sažetak gurnuo ka formalnom!)
```
Napetost: sam sažetak KAŽE "Holmes-Watson neformalno", a prevod ispao "vi" — opšti ton
epohe preplavio specifičnu nijansu para.

**Flaviovo pitanje: zašto ne Gutenbergov (besplatni, gotov) sažetak?** Validno. Ali
Gutenbergov je SADRŽAJNI (zaplet, likovi, misterija) — nema NIŠTA o registru/oslovljavanju.
Deepseek je PREVODILAČKI (namjerno o tonu). Dva različita alata.

**Drugi prolaz (test_sazetak3.py) — A gol / D deepseek / G gutenberg, isti prolaz:**
```
[101] "Don't move, I beg you, Watson."
  A gol       : Ne mičite se, preklinjem VAS, Watsone.    → "vi"
  D deepseek  : Nemoj se pomicati, molim TE, Watson.      → "ti"   ← OBRNUTO od prvog prolaza!
  G gutenberg : Nemojte se micati, preklinjem VAS, Watsone. → "vi"
```

### 3.7 GLAVNI NALAZ — signal je ispod šuma
**Rečenica 101 se PREOKRENULA između dva prolaza istog prompta.** Prvi prolaz: deepseek
"vi", gol "ti". Drugi prolaz: deepseek "ti", gol "vi". Iste rečenice, isti model, isti
promptovi — jedina razlika stohastičnost (temp 0.8).

**Varijacija između dva poziva istog prompta VEĆA je od razlike između promptova.**
Bilo koji zaključak "sažetak daje X" iz jednog poziva NIJE bio stvaran — bila je to
slučajnost pogrešno pročitana kao efekat (uključujući našu "pobjedu" C u 3.3).

Konzistentno JESTE: G (gutenberg) ≈ A (gol) oba prolaza — sadržajni sažetak praktično
ne mijenja ništa. I: sažetak ponekad ODMAŽE (111 "Tako sam veoma sretan" lošije od
"Jako mi je drago").

**Zaključak (dvostruk):** (1) Nema jednoznačno tačnog cilja — "vi" možda ispravan za
epohu uprkos prijateljstvu (Flaviov uvid). (2) Signal slabiji od šuma — čak i sa savršenim
kontekstom, temperatura pomjera izbor više nego kontekst. Kontekst-injection za registar,
na ovom nivou (prompt + stohastičan model), nije pouzdano rješiv. Isti tip granice kao
NER, sad izmjeren i za sažetak (skupi deepseek I besplatni Gutenberg).

Pošten NEGATIVAN nalaz, ne poraz. deepseek brief ostaje vrijedan artefakt — možda za
nešto drugo kasnije, ne za ovo.

---

## Odluke (kraj sesije)

**Odluka 1:** Odustajemo od poboljšanja prevoda kontekst-injectionom — i NER i sažetak.
Nalaz negativan i dvostruk: cilj (ti/vi ispravnost) nejasan jer zavisi od epohe/konvencije,
a signal ispod šuma temperature. Jezgro pipeline-a (3 modela + kosinus + sudija) radi i ne
treba mu ovaj dodatak.

**Odluka 2:** Sljedećih nekoliko sesija — stabilizacija Buchenberg web prezentacije i
estetsko/stilsko glačanje. Flavio: "dovoljno sam vidio, osjetio i probao."

---

## Lekcije

1. **Signal mora nadmašiti šum da bi bio signal.** Preokret rečenice 101 između dva
   prolaza je definitivan dokaz: prije zaključka o efektu prompt-varijable na
   stohastičnom modelu (temp>0), pokrenuti VIŠE prolaza. Jedan poziv na temp 0.8 ne
   razlikuje efekat od slučajnosti. Ovo važi za SVAKI budući prompt-eksperiment u projektu.
2. **Pogrešan alat ≠ loš alat.** NER (DocRE) je tehnički besprijekoran za ono za šta je
   građen (struktura odnosa), ali zadatak (registar/epoha) traži drugu osu informacije.
   Znati ZAŠTO alat ne radi je precizniji nalaz od "ne radi".
3. **Provjeriti vlastite skrivene premise.** Krenuli smo od "prijatelji → ti = ispravno".
   Flaviov uvid (njemačke sinhronizacije, Šekspir, viktorijanski manir) srušio je premisu.
   Naša "pobjeda" u prvom testu bila je mjerenje vlastitog modernog očekivanja, ne
   ispravnosti. X-Ray okrenut ka sopstvenoj pretpostavci.
4. **Manje čistijeg konteksta > više šumnog.** B (85 relacija) pala kao gol; C (32 fine)
   promijenila registar. Geografski/radni šum aktivno razblažuje signal u promptu.
5. **Iskoristiti postojeći podatak prije generisanja novog** (Flaviovo Gutenberg pitanje) —
   dobra navika, iako je ovdje pokazala da gotov sadržajni sažetak ne služi svrsi. Provjera
   je bila jeftina i vrijedna.
6. **Frontend često već ima podatak koji backend šalje** (X-Ray faza — u JSON-u od s114,
   samo se nije prikazivao). Prije backend izmjene, provjeriti prikazuje li frontend ono
   što već stiže.

---

## Završno stanje
- **Web (buchenweb):** reader.html + nlp.html + nav.js izmijenjeni, commitovani
  (`5feb09e`, `4270b02`). BB_VERSION s138.2 (sufiks se skida pred finalni commit ove sesije).
- **Baza:** netaknuta — svi NER/sažetak testovi standalone, van produkcije, nula upisa.
- **Kod (buchenberg):** netaknut u produkciji. Standalone test skripte na foxuno
  (`/tmp/test_ner_c.py`, `/tmp/test_sazetak.py`, `/tmp/test_sazetak3.py`) — van repozitorija,
  mogu se obrisati ili ostaviti (ne utiču ni na šta).
- **README:** ažuriran (§9 s138 snapshot, §14 self-refine sekcija — NER/sažetak nit zatvorena).

## Sljedeći koraci
- Web stabilizacija i estetsko/stilsko glačanje (Odluka 2) — sljedećih nekoliko sesija.
- Kontekst-injection za kvalitet prevoda: ZATVORENO (Odluka 1). Ako se ikad vrati, polazna
  tačka je nalaz 3.7 (signal ispod šuma) — trebao bi drugačiji režim (niža temp?
  deterministički pristup?), ne isti prompt-na-temp-0.8.

---
*Flavio & Claude · Buchenberg · Sesija 138 · 15. jul 2026.*
