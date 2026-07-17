# Session 141 — Plan: konfiguracija kao faza

**Datum:** 17. jul 2026.
**Fokus:** Plan implementacije za dva zahvata iz s140 horizonta (prompt-kao-atribut
+ random selekcija). Konceptualna/planska sesija — nula izmjena koda i baze osim
snimanja plan-dokumenta. Korpus READ-ONLY.

---

## Snimak zdravlja (početak s141)

- Baza: 50.624 rečenice · 1.608.260 prevoda · 302.168 pobjednika. Zeleno.
- Kompletnost 2b: 231 poznata rupa (sve faza 1, retired/djelomični modeli), prio 2.
- Ollama: aktivni par (glm-5.2, mistral-large-3:675b) + sudija (gemma4:31b) OK.
- Git buchenberg: 18 .bak necommitovanih (backlog). buchenweb: čist, s140.

---

## Šta je urađeno

Napisan `docs/PLAN-KONFIGURACIJA.md` — plan izvršenja za spajanje dva s140
prioriteta u jedan koherentan zahvat. Kroz diskusiju se pokazalo da nisu nezavisni:
random selekcija bira prompt kao atribut → pretpostavlja da prompt već postoji kao
registrovan atribut → prompt-kao-atribut je TEMELJ (Dio A), random STOJI NA NJEMU
(Dio B).

### Ključni konceptualni pomak (Flaviov, kroz tri iteracije plana)

Zahvat je narastao od "dodaj prompt na bb_faze" u **redefiniciju šta je faza**:

- **Model je model, ne "model+temperatura".** Slijepljivanje a1+a2 u jedan
  bb_modeli red bila je ad-hoc odluka s početka projekta — radila dok su bile 4
  konfiguracije, boli kad naraste. Zahvat je ISPRAVLJA.
- **Faza = konfiguracija = kombinacija izbora po tri NEZAVISNE ose** (a1=model,
  a2=temperatura, a3=prompt). Svaka osa ima svoj katalog dozvoljenih vrijednosti.
  Faza bira iz svake ose NEZAVISNO. Nema sprega, nema "parova".
- **"Jedinstvena identifikacija faze su svi atributi koji je opisuju."**

### Ciljna shema (u planu)

- Tri kataloga: `bb_modeli` (čist, samo naziv+aktivan), `bb_temperature` (nova),
  `bb_promptovi` (nova — svaki prompt = svi tekstovi: prevod+back, batch+single).
- Tri odvojene simetrične veze: `bb_faze_a1`, `bb_faze_a2`, `bb_faze_a3`
  (faza_id + izbor + aktivan). Nijedna spojena.
- Migracija: raspakuj 25 bb_modeli redova u tri ose, prebaci 1.268
  bb_prevodi_knjige FK-ova na eksplicitne veze. `bb_prevodi_recenica` (1.6M)
  netaknut (visi ispod knjiga-nivoa). Pun redoslijed 0–8 u planu.

### Random selekcija (Dio B, dizajn iz s139/s140)

- Traži-ili-kreiraj po skupu atributa; nikad namjerni duplikat; rubni slučaj
  (isti skup na više faza, kao 2 vs 3) → uzmi najstariju (min id).
- Marginalna preferenca PO OSI (a1/a2/a3 nezavisno) — raznolikost po konstrukciji.
- Prag ~10% pokrivenosti (proporcionalno). Tri nivoa uspjeha ponderisano
  (Bibl/Jezik/Knjiga, ponder prati količinu dokaza). Mutacija odvojen korak.
  Strop ~50% protiv preuzimanja.

---

## Lekcije (Claudeove, ova sesija)

- **Semantika vrijednosti ≠ struktura sheme.** Tri puta sam pobrkao značenje
  imena ("temperatura", "faza", "broj faze") sa strukturom, i svaki put uveo lažnu
  nedoumicu (spregu model↔temp, "parove", redoslijed faza). Flaviov a1/a2/a3 okvir
  skida taj teret: atributi su neprozirne ose, faza je slog koji bira po svakoj.
  Da je faza od početka bila "record t888" umjesto "broj faze", ne bi bilo 3 dana
  diskusije o redoslijedu. TRAJNA LEKCIJA: kad struktura zapinje, provjeri da li
  značenje imena natovaruje pretpostavku koje u konceptu nema.
- **Plan sa "otvorenim pitanjima" nije plan ako su pitanja moja zbunjenost, ne
  rupa u konceptu.** Ubacio sam svoje nedoumice u dokument kao "otvorena pitanja
  projekta". Flavio: prvo odgovoriti na pitanja (raščistiti razumijevanje), PA
  plan. Plan je "kako izvršiti", ne "šta još ne razumijem".
- **Zatečeni podaci nisu koncept.** Gledao sam da faza 1 danas ima baš određene
  (model,temp) redove i iz toga zaključio da "faza bira parove" — ali to je
  artefakt STARE slijepljene sheme koju baš ispravljamo. Ne dozvoliti da zatečeno
  stanje baze uči strukturu nove sheme.

## Protokol (ova sesija)

- Sve read-only komande i upisi prikazani + OK prije izvršenja. Bez prekršaja.
- Backtick-escape bug u heredocu: `\`` ostao doslovno u fajlu (124 mjesta),
  ispravljeno Python `str.replace()` naknadno. Lekcija za heredoc s markdown
  code-spanovima: escape backtick-ova nepouzdan, čistiti naknadno ili izbjeći.

---

## Završno stanje

- `docs/PLAN-KONFIGURACIJA.md` na serveru (285 linija, v3, backtick-ovi čisti).
- Koncept zatvoren, nema otvorenih pitanja. Nijedna DDL/kod komanda nije pokrenuta.
- Baza i korpus netaknuti. BB_VERSION ostaje s138 (web netaknut).

## Sljedeći korak

- Kad Flavio odluči: kreće se od Koraka 0 (backup) Dijela A.
- Prije Koraka 5 (najveći — migracija traga na 1.268 prevoda) posebna pažnja:
  broj prevoda po (a1,a2,faza) prije/poslije MORA biti identičan.

---
*Flavio & Claude · Buchenberg · session 141 · 17. jul 2026.*
