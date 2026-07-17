# Plan implementacije — Konfiguracija kao faza

**Datum:** 17. jul 2026. (sesija 141)
**Autori:** Flavio & Claude
**Status:** PLAN IZVRŠENJA. Koncept ispro-diskutovan i zatvoren. Nema otvorenih
pitanja. Nijedna komanda još nije pokrenuta.

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

DIO B (na temelju A):
  - Mjerenje/promatranje preferenci PRIJE mehanizma
  - Traži-ili-kreiraj fazu po marginalno izabranim osama (svaka nezavisno)
  - Prag ~10%: uniformni random ispod, ponderisan iznad
  - Mutacija odvojen korak; strop protiv preuzimanja
```

---

## 6. Status

- Ovaj dokument = plan izvršenja. Nijedna komanda nije pokrenuta.
- Koncept zatvoren, nema otvorenih pitanja.
- Kreće se od Koraka 0 (backup) kad Flavio odluči.

---
*Flavio & Claude · Buchenberg · Plan konfiguracije v3 · 17. jul 2026.*
