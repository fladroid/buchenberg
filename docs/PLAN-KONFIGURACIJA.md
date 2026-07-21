# Plan implementacije — Konfiguracija kao faza

**Datum:** 17. jul 2026. (sesija 141), dopunjeno 18. jul 2026. (s142 izvršenje,
s143 razrada Dijela B), preokrenuto 19. jul 2026. (s144 — random zamijenjen
fiksnim gated fazama), dopunjeno 19. jul 2026. (s145 — bootstrap fix +
"runda" dizajn testiran), dopunjeno 21. jul 2026. (s147 — "runda" IZVRŠENA)
**Autori:** Flavio & Claude
**Status:** DIO A IZVRŠEN (s142) i NEDIRNUT ovim preokretom. DIO B: random
selekcija NAPUŠTENA (s144) — zamijenjena s tri fiksne gated faze (prag
seed_score<0.95). IZVRŠENO i testirano. s145: bootstrap problem iz §4.7
ISPRAVLJEN u kodu (nije bio tih no-op kako je opisano — vidi §4.8). "Runda"
kao alternativa klon-triku RAZMATRANA i TESTIRANA (§4.9), IMPLEMENTIRANA
(s147, 21. jul 2026) — DDL + view + bb_03_prevod.py + run_faza.sh, testirano
kraj-do-kraja na k22. Seed-lock (potreban za mjerenje uticaja redoslijeda
refine koraka po rundi) OSTAJE NEIMPLEMENTIRAN — posebna, kasnija odluka.
Vidi §4.7-§4.9 i §6 Status za detalje.

---

## 0. Okvir — atributi kao nezavisne ose

Faza se opisuje skupom atributa. Da nas imena ne navode na lažne pretpostavke,
mislimo o njima kao **a1, a2, a3** — nezavisne ose, svaka sa svojim katalogom
dozvoljenih vrijednosti:

| Osa | Danas zovemo | Katalog dozvoljenih vrijednosti (primjer) |
|-----|--------------|-------------------------------------------|
| a1  | model        | {gemma3:12b, glm-5.2, mistral-large-3:675b, nllb-600M, ...} |
| a2  | temperatura  | {0, 0.1, 0.5, 0.8, 1} |
| a3  | prompt       | {base, refine, ...} |

**Faza bira atribute — svaki nezavisno.** Bilo koji atribut faze bira se nezavisno
od toga koji su atributi već izabrani i da li su izabrani. Jedino moranje: svaka osa
mora biti izabrana. Nema sprega, nema "parova", nema "baš ovih kombinacija".

**Vrijednosti su neprozirne oznake iz kataloga.** Nijedna a2 ne "pripada" nekoj a1;
nijedna nije "zabranjena". Open-source LLM ne zna niti mari koju temperaturu
koristimo — a2 je parametar poziva, ne svojstvo a1.

**Faza = red koji za svaku osu bira jednu ILI VIŠE vrijednosti iz kataloga.**
Faza nije "broj" ni "redoslijed" — ona je identifikator sloga koji nosi skup izbora.
Ime i redoslijed su čitljivost za čovjeka, ne struktura.

- a1 je N po fazi. a2 je N po fazi. a3 je N po fazi. **Sve tri simetrične.**
- To što stara baza ima baš određene redove je istorijski podatak o tome šta je
  POKRENUTO, ne o tome šta faza JEST.

**Metod** (base / self-refine) je iznad osa — krupna kategorija, root boolean.
Ne dira se.

---

## 1. Ishodište — kako je danas (pročitano s servera s141)

### 1.1 Shema

```
bb_prevodi_recenica  → bb_prevodi_knjige → bb_modeli → bb_faze → bb_metode
   (1.608.260)             (1.268)          (25)        (3)        (2)
```

- **`bb_modeli`** (25): `id, naziv, temperatura, faza_id, aktivan`.
  Jedan red SLIJEPLJUJE a1+a2+fazu. UNIQUE(naziv, temperatura, faza_id).
  **Ovo slijepljivanje je ono što zahvat ISPRAVLJA** — a1 i a2 su nezavisne ose
  koje su slučajno završile u istom redu.
- **`bb_faze`** (3): `id, naziv, redoslijed, opis, metod_id`.
  UNIQUE(redoslijed); partial UNIQUE root WHERE metod_id=1.
  Faza NE zna svoje atribute direktno — veza je OBRNUTA (bb_modeli.faza_id → faza).
- **`bb_metode`** (2): base (root=t) / self-refine (root=f).
- **`bb_prevodi_knjige`** (1.268): `knjiga_id, jezik_id, model_id, embeddings_id`.
  `model_id` je JEDINA veza prevoda ka konfiguraciji — preko jednog slijepljenog
  reda prevod implicitno zna a1, a2, fazu, metod.

### 1.2 Zatečene vrijednosti po osi

- **a1 (~11 imena):** claude-sonnet-4-6, gemma3:12b, gemma3:27b, gemma4:31b,
  glm-5.2, ministral-3:8b, ministral-3:14b, mistral-large-3:675b, nllb-600M.
  (gemma4:31b je SUDIJA — ima red ali nema prevoda; ostaje u katalogu a1, nijedna
  prevodilačka faza ga ne bira. bb_model_registar već nosi uloge — iskoristiti.)
- **a2:** 0, 0.1, 0.5, 0.8, 1.
- **Faze:** 1 (base, root), 2 (refine), 3 (refine-2 — "trik" oko UNIQUE, isti skup
  kao faza 2).

### 1.3 Obim

`bb_prevodi_knjige` = **1.268 redova** (knjiga × jezik × a1 × embedder), NE 1.6M.
Migracija FK-a dodiruje 1.268. `bb_prevodi_recenica` (1.6M) visi ISPOD knjiga-
nivoa i **ostaje netaknut**.

### 1.4 Promptovi u kodu (bb_03_prevod.py) — danas a3 nema traga u shemi

Tri para (batch + single-fallback):
- `prevedi_batch` / `prevedi_single` — prevodilački base
- `prevedi_refine_batch` / `prevedi_refine_single` — prevodilački refine
- `back_prevedi_batch` / `back_prevedi_single` — back-translation (mjerni korak)

**Svi promptovi koje faza koristi su njeni atributi** — i prevodilački I back.
a3 vrijednost = jedan slog sa svim svojim tekstovima. a3 danas živi samo kao
string-literal u kodu; `already_done()` + idempotentnost SAKRIVAJU efekat promjene
a3 (s139/s140 nalaz).

---

## 2. Cilj — kako treba da bude

### 2.1 Ciljna shema

**Tri kataloške tabele — tri nezavisne ose:**

- `bb_modeli` (a1) → ČIST katalog imena. `id, naziv, aktivan`. Gubi temperatura,
  faza_id. UNIQUE(naziv).
- `bb_temperature` (a2) → NOVA. `id, vrijednost NUMERIC`. UNIQUE(vrijednost).
- `bb_promptovi` (a3) → NOVA. Jedan red = jedan prompt sa svim tekstovima:
  `id, naziv, prompt_prevod_batch, prompt_prevod_single, prompt_back_batch,
   prompt_back_single`.

**Faza bira iz svake ose nezavisno — tri odvojene, simetrične veze:**

- `bb_faze`: `id, naziv, redoslijed, opis, metod_id` (identitet + metod).
- `bb_faze_a1` → koji modeli: `faza_id, model_id, aktivan`.
- `bb_faze_a2` → koje temperature: `faza_id, temperatura_id, aktivan`.
- `bb_faze_a3` → koji promptovi: `faza_id, prompt_id, aktivan`.

Sve tri veze su istog oblika (faza_id + izbor + aktivan). Nijedna nije spojena s
drugom. Faza bira a1, a2, a3 nezavisno.

**Prevodi nose eksplicitan trag:** prevod pokazuje na fazu + na konkretno izabranu
a1, a2, a3 vrijednost kojom je nastao (§3.2 Korak 5).

### 2.2 Šta se NE dira

- `bb_metode` (metod je iznad osa).
- `bb_prevodi_recenica` (1.6M, ispod knjiga-nivoa).
- root invarijanta (jedan base red).
- embedder osa (`bb_embeddings`) — već zasebna, dobar presedan.

---

## 3. DIO A — razdvajanje osa i migracija (TEMELJ)

### 3.1 Ponašanje po tipu faze

- **Base (root):** jedan red. Promjena = UPDATE veze (ukinut a1 → zamijeni u
  bb_faze_a1). SCD Tip 1. Root invarijanta ostaje. Istorija u prevodima, ne u fazi.
- **Refine (2, 3, buduće random):** "traži-ili-kreiraj po skupu atributa". Čim
  faza postoji, procedura je IDENTIČNA bez obzira na porijeklo.

### 3.2 Puni redoslijed migracije

> Svaki korak = zaseban prikaz + OK pri izvršenju. DDL se piše pri izvršenju.
> Backup prije SVAKE DDL faze (pg_dump -Fc).

**Korak 0 — Backup.** `pg_dump -Fc` cijele bb baze na host. Bez ovoga se ne kreće.

**Korak 1 — Kreiraj kataloške tabele (prazne):** `bb_temperature`, `bb_promptovi`.

**Korak 2 — Napuni kataloge iz zatečenog:**
- `bb_temperature` ← DISTINCT temperatura iz bb_modeli.
- `bb_promptovi` ← tekstovi prepisani IZ KODA (bb_03_prevod.py). Minimalno dva
  reda: base (prevedi_batch/single + back), refine (prevedi_refine_* + back).

**Korak 3 — Kreiraj tabele-veze (prazne):** `bb_faze_a1`, `bb_faze_a2`, `bb_faze_a3`.

**Korak 4 — Napuni veze iz OBRNUTE veze starog bb_modeli:**
- za svaku fazu, čitaj `bb_modeli WHERE faza_id=X`:
  - DISTINCT naziv modela → `bb_faze_a1`
  - DISTINCT temperatura → `bb_faze_a2`
  - a3 iz koda (base faza→base prompt, refine faze→refine prompt) → `bb_faze_a3`

**Korak 5 — Prebaci trag konfiguracije na `bb_prevodi_knjige`:**
NAJVEĆI korak (1.268 redova, svaki mora zadržati tačan identitet).
Za svaki prevod: pročitaj stari `model_id` → raspakuj na (a1, a2, faza) →
upiši u nove eksplicitne kolone. Podatak POSTOJI u starom bb_modeli redu →
RASPAKIVANJE, ne izmišljanje. Determinističko.
- a1, a2: raspakuju se iz podataka.
- a3: pripiše se iz faze (base→base, refine→refine). Bez vremenske preciznosti
  oko s135 (Flaviova odluka — ne treba).
Oblik novih kolona (tehnički izbor pri izvršenju): prevod nosi `faza_id` +
`model_id` + `temperatura_id` (+ a3 izvedeno iz faze ili eksplicitno `prompt_id`).
Provjeriti da UNIQUE ograničenje prevoda i dalje razdvaja legitimne kombinacije.

**Korak 6 — Novi bb_modeli katalog.**
Tek kad prevodi više ne zavise od slijepljenog model_id: raščisti bb_modeli na
`id, naziv, aktivan`. DISTINCT naziv. Ukloni temperatura, faza_id. UNIQUE(naziv).

**Korak 7 — Kod čita iz baze:**
- bb_03_prevod.py: a1 iz bb_faze_a1, a2 iz bb_faze_a2, a3 iz bb_faze_a3
  (`.format()` template umjesto literala). Header loga dobija a3 (sve što se radi
  s a1/a2 radi se i s a3).
- orkestratori (run_faza.sh, bb_aktivni_modeli.py, bb_faza_info.py) — usklađuju se.

**Korak 8 — Verifikacija:**
- Broj prevoda po (a1, a2, faza) prije i poslije MORA biti identičan.
- health_check 2b (v_status_faza_model) radi na novoj shemi.
- View sloj: `v_prevodi_full` (majka) + svi izvedeni koji čitaju bb_modeli.
  temperatura/.faza_id se PRERAĐUJU (majka prije izvedenih).
- stats/web export (bb_web_export.py, bb_xray_export.py) usklađeni (inače stats
  stapaju ili gube ose).
- Test run na knjizi 22: jedan base + jedan refine, provjeri da identitet stiže
  tačno kroz cijeli lanac.

### 3.3 Rizici (mapa dodira, ne pitanja)

- **View sloj širok zavisnik** — sve što čita bb_modeli.temperatura/.faza_id.
- **stats/web export** čitaju model×temp×faza iz bb_modeli.
- **`bb_prev_recenica_faza`** već ima direktan faza_id — presedan, provjeriti
  da se ne sudari s novim traceom.
- **sudija gemma4:31b** ostaje u katalogu a1, označen preko bb_model_registar uloga.

---

## 4. DIO B — random selekcija atributa (STOJI NA A)

> ⚠️ **PREOKRENUTO s144 — vidi §4.7.** Ovaj dizajn (§4.1-§4.6) je NAPUŠTEN i
> zamijenjen fiksnim gated fazama. Ostaje ispod kao istorijski trag
> rasuđivanja (X-Ray princip — proces vidljiv, ne obrisan), ne kao aktivan
> plan. Za trenutno stanje čitaj §4.7.

> Dizajn iz s139/s140. Gradi se TEK kad A radi. Manje kod, više dizajn.

### 4.1 Mehanika

- **Faza 1 = temelj, bez random-a.** Deterministična, seed za sve iznad.
  Random tek OD refine faza.
- **Random po osi:** baci kocku po a1, a2, a3 (marginalno, §4.2) + izbor rečenica.
  Svaka osa nezavisno. Sastavi kombinaciju.
- **Traži-ili-kreiraj:** kombinacija postoji kao faza → koristi je; ne postoji →
  INSERT nove faze. **Nikad namjerni duplikat.**
- **Rubni slučaj (isti skup na više faza, kao faza 2 vs 3):** uzmi NAJSTARIJU
  (min id). Random ne reprodukuje ručni "trik" faze 3.

### 4.2 Preferenca — MARGINALNA po osi (ključno)

- Preferenca po SVAKOJ OSI ZASEBNO: favorit-a1 (preko svih a2/a3), favorit-a2,
  favorit-a3 — biraju se NEZAVISNO i kombinuju. Kombinatorna preferenca konvergira
  u jedan vrh; marginalna sastavlja tačku iznova → raznolikost PO KONSTRUKCIJI.
- **Anti-elitizam:** bolja vrijednost = ŠIRI ali NENULTI interval. Niko 100% ni 0%.
- **Mutacija = odvojen korak POSLIJE izbora** (čista GA: selekcija pa mutacija).
  Jeftina/sigurna — ostaje u zatvorenom katalogu (niska cijena greške).
- **Strop protiv preuzimanja:** jedna kombinacija ne prelazi ~50% rečenica knjige/
  jezika. Diverzitet kao TVRDO PRAVILO.

### 4.3 Granularnost uspjeha — tri nivoa ponderisano

- Uspjeh ose mjeri se po Biblioteci / Jeziku / Knjizi, ponderisano (kao 0.4/0.6
  finalni_score = dva ponderisana pogleda).
- **Knjiga najviše, Biblioteka najmanje** (prevodiš OVU knjigu).
- **Ponder prati količinu dokaza:** rana knjiga (malo rečenica, šum) → biblioteka
  vodi; zrela knjiga → težina se seli na knjigu. Nivo se "zasluži" podatkom.
- Klasa/žanr se NE računa preko LLM (nova crna kutija). Knjiga = svoja klasa.

### 4.4 Prag ulaska — proporcionalan

- Random kreće tek kad faza 1 dosegne **~10% pokrivenosti knjige** (proporcionalno,
  NE apsolutnih 400 — 400 je 26% Alice ali 4% Moby Dicka).
- Ispod praga → čisti uniformni random.
- Iznad praga → ponderisana preferenca (§4.3).

### 4.5 Ograda (trajna)

- Preferenca dolazi od POBJEDA PO NAŠEM SUDIJI → X-Ray VLASTITOG OCJENJIVANJA, ne
  istina o jeziku. Sudija je i igrač i mjerni instrument. Ne kvari ideju, određuje
  kako se čita rezultat.
- Jumping-genes (McClintock) je ANALOGIJA, ne specifikacija. Promatramo pojavu kad
  se desi, ne predviđamo kvar unaprijed.
- **Graditi mjerenje/promatranje PRIJE mehanizma koji dirigira.**

---

### 4.6 Konkretizacija dizajna — odluke iz s143 (18. jul 2026)

Nakon što je Dio A izvršen (s142), sljedeća sesija (s143) razradila je nekoliko
otvorenih pitanja iz §4 na konkretne odluke — sve bez izmjene sheme.

**Filter za "sve faze koje ulaze u random tretman":**
```sql
-- ISPRAVNO (otporno na buduće faze bilo kog porijekla):
... JOIN bb_faze f ON f.id = X.faza_id JOIN bb_metode m ON m.id = f.metod_id
WHERE m.root = false

-- POGREŠNO (lomi se čim postoji faza čiji id nije uzastopan/veći):
... WHERE X.faza_id > 1
```
Nema posebnog tretmana po porijeklu faze (random vs ručno kreirana) — sve
`root=false` faze rade identično.

**Izmjereno na cijelom korpusu (kanonski upiti u `docs/ANALIZA.md`):** faze
`root=false` = 2.44% obima svih prevoda, 1.73% apsolutnih pobjednika —
konzistentno gubi agregatno, slaže se s malim uzorcima s134-138.

**Tri nivoa granularnosti (§4.3) — precizna definicija filtera:**

| Nivo | Ponder | Filter |
|---|---|---|
| Knjiga | 50% | `knjiga_id=K AND jezik_id=L AND root=false` |
| Jezik | 25% | `jezik_id=L AND root=false` (sve knjige) |
| Biblioteka | 25% | `root=false` (sve knjige, svi jezici) |

Dimenzije (knjiga, jezik) se puštaju POSTEPENO šire prema širem nivou — ne
dodaju se svugdje. Ponder OSTAJE FIKSAN (50/25/25) do empirijske revizije
nakon analize par hiljada refine prevoda — adaptivni/shrinkage prijedlog iz
§4.3 nije odbačen, samo odgođen.

**Preduslov prije anti-elitizma (§4.2) — podobnost po osi:**
Anti-elitizam/strop ima smisla SAMO kad osa ima ≥2 podobne vrijednosti u
datom kontekstu. Ako 1, deterministički izbor (nije kršenje "niko 100% ni
0%" — nema alternative). Provjeriti broj podobnih vrijednosti PRIJE računanja
marginalne preference. (Empirijski dokaz: temperatura u postojećim refine
fazama je degenerisana — samo 0.8 ikad aktivirana, 100% na sva tri nivoa.)

**a1 podobnost za refine faze — NLLB isključen, bez nove sheme:**
```sql
SELECT m.id, m.naziv FROM bb_modeli m
JOIN bb_model_registar r ON r.naziv = m.naziv
WHERE m.aktivan = true AND r.vrsta <> 'namenski MT model'
```
Koristi POSTOJEĆI `bb_model_registar` (s123) umjesto nove tabele/kolone —
Flaviov princip: "mijenjamo strukturu baze najmanje moguće, iskoristimo
maksimalno ono što imamo." Razlog za isključenje NLLB: (a) uvijek već
pokriven u root fazi; (b) tehnička zavisnost a1→a2 — NLLB nema pojam
sampling temperature (uvijek 0.0, CTranslate2 beam decode), pa slobodan
izbor a2 preko svih 5 vrijednosti ne bi bio smislen za taj a1.

**Sudija van sistema:** `gemma4:31b` potpuno van a1/a2/a3 rotacije — fiksna
pipeline konstanta (KONCEPT.md: tačno 1 sudija), nikad ne konkuriše u
izboru, nema "grupu temperatura za sudiju" (njegova temp=0.0 živi
hardkodovano u `bb_08_sudija.py`, van ovog sistema).

**Prompt katalog (a3) popunjen — tri refine varijante:** `refine` (id 2,
postojeći), `refine-lenient` (id 3, pre-s135 tekst), `refine-strict` (id 4,
nova). Nijedna od tri još nije vezana za fazu preko `bb_faze_a3` — katalog
spreman, mehanizam selekcije NIJE građen.

**Još otvoreno (za sljedeću sesiju kad se gradi mehanizam):**
- Izvršni redoslijed za Dio B (analogan §3.2 Korak 0-8 iz Dijela A) —
  konkretan generator koji stvarno bira a1/a2/a3 i radi traži-ili-kreiraj.
- Formalizacija "širi ali nenulti interval" (s139 pominje rank selection).
- Operativna definicija praga ~10% (koji upit/view).
- Kad se strop ~50% provjerava — u trenutku izbora ili naknadno.

Detalji cijele rasprave: `docs/sessions/session_143.md`.

---

## 4.7 PREOKRET (s144): random napušten, fiksne gated faze usvojene

Flavio je, testirajući ideju kroz sopstveno iskustvo ("6 minuta po rečenici" —
istorijska mjera nedopustivo dugog procesa), postavio provokativno pitanje:
zašto graditi GA-stil random selekciju (§4.1-§4.6) kad katalog ima samo
2 aktivna LLM-a × 3 gotova prompta × 1 istorijski korišćena temperatura (0.8)
= 6 smislenih kombinacija? Genetski algoritam (mutacija, marginalna
preferenca, anti-elitizam) opravdan je kad je prostor pretrage OGROMAN — kad
ga ne možeš iscrpiti. Sa 6 fiksnih, ručno-kuriranih kombinacija, to nije taj
slučaj: to je katalog koji se može prstom prebrojati, ne prostor koji treba
evoluirati.

**Pravi problem nikad nije bio "koju od N kombinacija probati" nego "da li
uopšte vrijedi probati OVU rečenicu."** Mjerenje (bucket-analiza
`seed_score` vs. win-rate refine-a, cijeli korpus, potvrđeno i na čistom
novi-model-vs-novi-model presjeku da konfaund miješanja generacija modela ne
mijenja oblik nalaza) pokazalo je čist, monoton gradijent: ispod seed_score
~0.85 refine pobjeđuje ~8/10 puta, iznad ~0.97 gubi ~9/10 puta. Prag
**0.95** usvojen kao gate.

**Nova arhitektura Dijela B — potpuno unutar postojeće a1/a2/a3 sheme
(Dio A), BEZ NOVE STRUKTURE:**

- Tri nove faze (`refine-gated`=4, `refine-lenient-gated`=5,
  `refine-strict-gated`=6), svaka: a1={mistral-large-3:675b, glm-5.2},
  a2={0.8}, a3=jedan od tri postojeća prompta (`refine`/`refine-lenient`/
  `refine-strict`). Kreirane po IDENTIČNOM obrascu kao faza 2/3 (README
  "Kako pokrenuti NOVU FAZU") — nijedan novi tip reda, nijedna nova tabela.
- Redoslijed faza je proizvoljan (Flavio: "svejedno") — jer gate mehanika
  sama sužava posao: svaka faza gleda TRENUTNOG apsolutnog pobjednika
  (ne originalni seed), pa ako ranija gated faza popravi rečenicu iznad
  praga, sljedeća je automatski preskače. Samo-sužavajući lijevak bez ijedne
  random komponente.
- **Implementacija gate-a: jedan novi CLI parametar** `--prag` (default 0.95)
  u `bb_03_prevod.py`. `get_seed_map()` sad vraća `(prevod, finalni_score)`
  iz `v_pobjednici_full` (bilo: ručni tro-tabelarni JOIN); filter
  `seed_score < prag` primijenjen PRIJE poziva modela (štedi pozive, ne samo
  upis).

**Šta je napušteno (§4.1-§4.6 ostaju kao istorijski trag rasuđivanja, ne
kao aktivan plan):** traži-ili-kreiraj generator, marginalna preferenca po
osi, anti-elitizam/strop ~50%, mutacija kao odvojen korak, tri nivoa
granularnosti (Biblioteka/Jezik/Knjiga) ponderisano, prag ~10% pokrivenosti.
Sve je zamijenjeno jednim pragom kvaliteta seeda i fiksnim skupom faza.
**Dio A (a1/a2/a3 nezavisne ose) OSTAJE NEDIRNUT kao temelj** — ovaj
preokret mijenja samo KAKO se faze biraju/pokreću, ne strukturu koja ih
opisuje.

**Mjerenja (kanonski upiti, cijeli korpus + novi-vs-novi presjek):**
- Cijeli korpus (svi seed-ovi, mješani modeli): 50% win-rate prag ≈ 0.92.
- Čist presjek (seed I refine oba iz {glm-5.2, mistral-large-3:675b}):
  50% win-rate prag ≈ 0.95 — usvojeno kao operativni prag (konzervativnije,
  usklađeno s modelima koji su jedini aktivni ubuduće).
- Buduće opterećenje ako se korpus prevodi isključivo novim modelima: samo
  **15.41%** rečenica (5.898/38.286, gdje je najbolji root kandidat od
  novog modela) padne ispod praga 0.95 — refine se pokreće na ~1 od 6-7
  rečenica, ne na svakoj.

**Nuspojava pronađena i ispravljena tokom testiranja:** `bb_04_pobjednik.py`
(fazni pobjednik → `bb_prev_recenica_faza`) je od s142 imao neotkriven
zaostatak — čitao `m.faza_id`/`m.temperatura` sa `bb_modeli` (uklonjeno u
s142 Koraku 6), nikad testiran jer nijedan refine nije pokretan između s142
i ovog testa. Popravljeno: `pk.faza_id` (direktno na `bb_prevodi_knjige`) +
`bb_temperature` join za tie-break. Vidi `docs/sessions/session_144.md`.

**Operativna napomena (README) — ISPRAVLJENA s145, vidi §4.8:** opis iznad
("tiho ne radi ništa") nije bio tačan; ispravan opis i kod fix u §4.8.

## 4.8 Bootstrap problem — ispravka opisa i kod fix (s145, 19. jul 2026.)

Live test (s145) je pokazao da opis iz prethodnog pasusa NIJE tačan:
`run_faza.sh` se NE zaustavlja tiho. `bb_aktivni_modeli.py` je oduvijek
(već u s142 verziji, provjereno diff-om) imao `if not rows: exit(1)`
zaštitu — pod `set -e` na vrhu `run_faza.sh`, to zaustavlja cijelu
skriptu odmah, s greškom na stderr ("Nema aktivnih modela za fazu N!"),
bez "ZAVRŠENO". Prethodna sesija je vjerovatno pretpostavila poznatu bash
`set -e` + command-substitution zamku umjesto da je uživo testira — ovdje
se ispostavilo da zamka ne važi (potvrđeno: `bash -c 'set -e; x=$(exit 1);
echo NEDOSTIŽNO'` zaista stane prije echo-a).

**Pravi uzrok (i dalje stoji, samo ne kao "tihi" bug nego kao "glasan"
preduslov):** `bb_aktivni_modeli.py` ne čita "koji model/temp JE AKTIVAN
za fazu N" iz kataloga (`bb_faze_a1`/`bb_faze_a2`) — čita "koji model/temp
je VEĆ KORIŠTEN za fazu N" iz `bb_prevodi_knjige` (istorija). Za potpuno
svježu fazu (0 redova) to je uvijek prazno → glasna greška, ne tih no-op.

**Zašto je istorijski pristup uopšte izabran (otkriveno pri provjeri prije
kod-izmjene):** za fazu 1 (root), katalog (`bb_faze_a1` × `bb_faze_a2`)
NIJE jednoznačan — sve tri temperature (0.0/0.1/0.8) su "aktivne" za sva
tri modela (glm-5.2, mistral-large-3:675b, nllb-600M), ali stvarno
korištenih kombinacija je samo 5 od mogućih 9 (nllb je deterministički,
nikad zvan na 0.1/0.8). a1/a2 osе po dizajnu (§0) nemaju spregu u shemi —
tako da čist katalog-cross-product NIJE ispravan odgovor za fazu 1. Za sve
self-refine faze (2,3,4,5,6...) katalog UVIJEK ima tačno 1 aktivnu
temperaturu → cross-product je tamo potpuno jednoznačan i tačan.

**Popravka:** `bb_aktivni_modeli.py` prvo pokuša istoriju (nepromijenjeno
ponašanje — faza 1 uvijek ima punu istoriju, nikad ne stiže do nove
grane). Ako je istorija prazna, PADA na katalog
(`bb_faze_a1` × `bb_faze_a2`, oba aktivan) kao fallback. Za sve buduće
proste self-refine faze (uvijek 1 temperatura) to je uvijek tačno —
bootstrap direktnim `bb_03_prevod.py` pozivima više NIJE potreban.

**Testirano (s145):**
- `py_compile` prošao.
- Faza 4 (ima istoriju od s144 bootstrapa): rezultat nepromijenjen
  (`glm-5.2|0.8`, `mistral-large-3:675b|0.8`).
- Fallback grana: testirana kroz SIGURNU DB transakciju (privremena test-
  faza + a1/a2 katalog redovi, upit identičan fallback grani u kodu,
  `ROLLBACK` na kraju — nula trajnih upisa). Vratila tačno očekivane
  parove iz kataloga.
- Faza 999 (ne postoji nigdje): i dalje pada s greškom kao i prije.

**Status:** kod izmijenjen u `src/bb_aktivni_modeli.py`, testiran,
NEKOMITOVAN na kraju s145 (čeka Flaviov redovan git ritual). README
operativna napomena treba ažuriranje da odražava popravku (vidi README
"Kako pokrenuti NOVU FAZU").

## 4.9 "Runda" — alternativa klon-triku za ponovno izvršavanje faze (razmatrano i testirano s145, IMPLEMENTIRANO s147)

**Problem koji rješava:** ponovno pokretanje iste gated refine faze (npr.
kad se prag 0.95 ponovo primijeni na već-poboljšan tekst) zahtijeva danas
klon-trik — nova faza (7/8/9 = klon 4/5/6) samo da zaobiđe
`UNIQUE(..., faza_id, ...)` na `bb_prevodi_knjige`. Isti obrazac kao faza
2→3 (s139: "faze 2 i 3 su tehnički identične"). Ovo utiskuje BROJ POKUŠAJA
u IDENTITET faze (`faza_id`), što je u napetosti s KONCEPT.md principom
"identitet = minimumi + proces, NE komponente" — broj pokušaja je proces,
ne identitet.

**Predložena alternativa (Flaviova ideja, s145):** dodati atribut `runda`
(cijeli broj, default 1) na `bb_prevodi_knjige`, uključen u UNIQUE
ograničenje umjesto novog `faza_id` po pokušaju. `faza_id` ostaje
"koja konfiguracija" (metod + a1/a2/a3); `runda` postaje "koji pokušaj te
iste konfiguracije". Druga posljedica (logička, ne namjeravana ali
tačna): fazni pobjednik (`bb_prev_recenica_faza`, grupisan po
(rečenica, faza)) bi automatski gledao najbolji rezultat PREKO SVIH
RUNDI te faze — bliže konceptu "najbolji pokušaj ove konfiguracije" nego
klon-trik koji pravi potpuno odvojene bazene pobjednika po faza_id.

**Cijena:** `bb_prevodi_knjige` ADD COLUMN + zamjena UNIQUE ograničenja
(jeftino — tabela ima 1.268 redova, ne 1.6M); `--runda` CLI parametar u
`bb_03_prevod.py` (isti obrazac kao `--temp`/`--prag`), uključen u
`already_done()` provjeru; `--runda` passthrough u `run_faza.sh`; view
sloj (`v_prevodi_full` i nasljednici) treba novu kolonu izloženu — sigurna
ADDITIVE izmjena (dodavanje na kraj SELECT liste), ne kida downstream za
razliku od preimenovanja iz s142.

**Testirano (s145) — prava DDL migracija u transakciji, ROLLBACK na
kraju, nula trajnih izmjena:**
```sql
ALTER TABLE bb_prevodi_knjige ADD COLUMN runda INTEGER NOT NULL DEFAULT 1;
ALTER TABLE bb_prevodi_knjige DROP CONSTRAINT bb_prevodi_knjige_full_key;
ALTER TABLE bb_prevodi_knjige ADD CONSTRAINT bb_prevodi_knjige_full_key
  UNIQUE (knjiga_id, jezik_id, faza_id, model_id, temperatura_id, prompt_id, embeddings_id, runda);
```
- Duplikat na runda=1 (isti tuple kao postojeći red faze 4): PAO kao i
  prije (nema promjene ponašanja za default rundu).
- Isti tuple na runda=2: PROŠAO čisto (novi red, `RETURNING id=14793,
  runda=2`).
- `v_prevodi_full` view nastavio raditi ispravno poslije ADD COLUMN
  (COUNT provjeren, 132 kandidata za fazu 4, netaknuto).
- `ROLLBACK` potvrđen — 0 zaostalih test-redova u bazi.

**Preporuka (Claude):** runda je konceptualno čistija (izbjegava
ponavljanje faza-2/3 "broj pokušaja kao identitet" problema), ali klon
i dalje potpuno radi i već je dokazan na 4/5/6. Nije hitna odluka — cijena
čekanja je samo gomilanje `bb_faze` redova (kozmetičko, ne funkcionalno).
Vrijedi implementirati ako ponovno pokretanje gated refine faza postane
rutina; ako ostaje rijetka stvar, klon je sasvim pragmatično OK.

**Status:** IMPLEMENTIRANO (s147, 21. jul 2026) — vidi §6 za pun opis
izvršenja i testa. Seed-lock (izolacija seed-a po rundi, potreban da bi
runda mogla mjeriti uticaj redoslijeda refine koraka na ocjenu prevoda —
vidi raspravu s147) ostaje posebna, neimplementirana odluka.

## 5. Sažetak redoslijeda

```
DIO A (temelj):
  0. Backup (pg_dump -Fc)
  1. Kreiraj bb_temperature, bb_promptovi (prazne)
  2. Napuni kataloge (a2 iz DISTINCT, a3 iz koda)
  3. Kreiraj bb_faze_a1, bb_faze_a2, bb_faze_a3 (prazne)
  4. Napuni veze (obrnuta veza iz starog bb_modeli, DISTINCT po osi)
  5. bb_prevodi_knjige: prebaci trag (raspakuj model_id → faza+a1+a2)
  6. bb_modeli → čist katalog imena
  7. Kod (bb_03 + orkestratori + export) čita iz baze
  8. Verifikacija (broj po osi identičan; view sloj; test run k22)

DIO B (na temelju A) — PREOKRENUTO s144, vidi §4.7:
  0. Mjerenje: bucket-analiza seed_score vs. win-rate (cijeli korpus +
     novi-vs-novi presjek) -> prag = 0.95
  1. Tri nove faze (bb_faze + a1/a2/a3, isti obrazac kao faza 2/3):
     refine-gated(4) / refine-lenient-gated(5) / refine-strict-gated(6)
  2. bb_03_prevod.py: nov --prag CLI (default 0.95), get_seed_map vraca
     (prevod, finalni_score), filter PRIJE poziva modela
  3. Bootstrap: direktan bb_03 poziv po (faza,model) prije prvog run_faza.sh
  4. Verifikacija: run_faza.sh end-to-end (bb_03->sudija->bb_04) na k22
     (usput otkriven i ispravljen bb_04_pobjednik.py zaostatak iz s142)
```

---

## 6. Status

- **Dio A: IZVRŠEN kraj-do-kraja (s142, 18. jul 2026).** Svih 9 koraka (0-8)
  izvršeno i verifikovano. Detalji: `docs/sessions/session_142.md`.
- **Dio B: random selekcija (§4.1-§4.6) NAPUŠTENA (s144, 19. jul 2026).**
  Zamijenjena s tri fiksne gated faze (4/5/6), prag seed_score<0.95.
  IZVRŠENO i testirano kraj-do-kraja (bb_03->sudija->bb_04 na k22, sve tri
  faze). Vidi §4.7. Detalji: `docs/sessions/session_144.md`.
- Sljedeći korak kad Flavio odluči: pokrenuti gated faze na širem korpusu
  (van test-knjige k22); health_check "opseg"/rupa logika za gated faze
  ostavljena namjerno kao poznata razlika (Flaviova odluka s144), ne
  popravljena.
- **"Runda" (§4.9): IMPLEMENTIRANA kraj-do-kraja (s147, 21. jul 2026).**
  `bb_prevodi_knjige.runda` (INTEGER, default 1) u UNIQUE ograničenju;
  `v_prevodi_full` dopunjen kolonom `runda` (additive, kraj SELECT liste);
  `bb_03_prevod.py --runda` (default 1, `already_done()` automatski
  runda-svjestan preko `prevodi_knjige_id`); `run_faza.sh --runda`
  passthrough. Testirano na k22/hr/faza4/pozicija109: runda=1 bez
  regresije (already_done ispravno preskočio), runda=2 napravio nezavisan
  nov red, refine izvršen, sudija ocijenila, bb_04 argmax ispravno odabrao
  bolji rezultat preko obje runde. Backup prije DDL-a:
  `/tmp/bb_backup_pre_runda_20260721.dump`. Health check poslije: sve
  zeleno, nijedan izvedeni pogled ni export skripta nije pogođena (nema
  `SELECT *` ni zavisnosti na `v_prevodi_full` u bb_web_export.py/
  bb_xray_export.py). **Seed-lock (§4.9 dio o izolaciji seed-a po rundi,
  potreban za mjerenje uticaja redoslijeda refine koraka) NIJE
  implementiran** — namjerno odvojen kao posebna, kasnija odluka.

---
*Flavio & Claude · Buchenberg · Plan konfiguracije v4 · 17. jul 2026., preokrenuto 19. jul 2026. (s144), dopunjeno 19. jul 2026. (s145), dopunjeno 21. jul 2026. (s147)*
