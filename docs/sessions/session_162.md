# Sesija 162 — 5. avgust 2026.

**Fokus:** Konceptualna sesija — misaoni eksperiment (Flavio eksplicitno: "nema veze sa stvarnošću"), nula izmjena koda/baze/weba. Provjera memorije protiv README-a i session dokumenata (jedan nalaz ispravljen). Zatim istraga, korak po korak, da li su "root faza", "self-refine" i "svjetovi" nužni dijelovi identiteta pipeline-a ili slučajno nataložena složenost oko jednostavnijeg jezgra. Metoda: istinitosna tabela.

---

## Otvaranje sesije

Standardni checklist proveden (project files, README u dva `sed` poziva, poslednja tri session dokumenta u cijelosti na Flaviov zahtjev, health check). Korpus na početku: 50.624 / 1.938.090 / 369.832 (rastao od s161 stanja — Flaviov k12 rad nastavljen van sesije). Health check: sve zeleno, 333 očekivane rupe (jezici van core-4), buchenweb i dalje zaostaje na s152 (namjerno, nedirano).

## Dio 1 — Provjera neslaganja (memorija vs README/session dokumenti)

Na Flaviov zahtjev, provjereno da li postoje nelogičnosti između README-a, poslednja tri session dokumenta i memorije. Nađena dva nalaza:

1. **Memorija interno kontradiktorna** — generisani "Current state"/"On the horizon" sažetak na vrhu memorije opisivao je Dio A/Dio B (s140/s141) kao "jedine aktivne niti", sa Dijelom B "stoji na Dijelu A, gradi se tek kad A radi" — zastarjelo ~20 sesija. Stvarno stanje (potvrđeno README §9/§14 i session dokumentima): Dio A izvršen u s142; Dio B napušten u s144 (random selekcija zamijenjena gated fazama), koje su od s159 standardni tok u produkciji. Uzrok: zapis #30 u `memory_user_edits` stao je na s143, nikad dopunjen s144-s161 razvojem — sažetak se gradio iz nepotpunog izvora.
2. Sitna numerička razlika (5.222 vs 5.217) — ispostavilo se da NE postoji u sirovom zapisu #30 (tamo je uvijek stajalo 5.217, tačno); greška je bila samo u generisanom sažetku.

**Ispravka:** zapis #30 dopunjen novim pasusom koji pokriva s144→s161 (Dio B napušten, gated faze, deklarisani svjetovi, s160 recovery mehanizam, s161 README audit). Zapis #29 (s140 odluka) namjerno nedirnut — tačan istorijski snimak trenutka odluke, isto pravilo kao za session dokumente ("hronološki zapis se ne prepisuje retroaktivno").

Dodatno potvrđeno kao već poznato, ne novo: nesklad session_159.md IT izvještaja sa stvarnim logom (otkriven u s160 Dio 7, i dalje neistražen) — nisam ga ja unio, otkriven je ranije.

## Dio 2 — Provjera mehanike: da li postoji skript za "prevedi ovu knjigu/jezik/opseg ovim modelom/temperaturom"

Flaviovo pitanje: da li postoji skript koji direktno prima knjigu, jezik, opseg, model, temperaturu.

**Odgovor (potvrđen kroz `--help` i kod):** DA — `bb_03_prevod.py` prima tačno `--knjiga --jezici --od --do --model --temp --embedder --faza` direktno na komandnoj liniji. Nema `--prompt` argumenta — prompt se bira automatski, čita se iz `bb_faze_a3` za zadatu fazu.

**Jedini uslov:** kombinacija `(faza, model, temp)` mora već postojati kao `aktivan=true` u `bb_faze_a1`/`bb_faze_a2` katalogu za tu fazu (tri `EXISTS` upita, kod linije 399-411). Ako nije registrovana, skripta ispiše `"nije aktivna kombinacija! Preskačem."` i preskoči — bez greške, bez pada.

**Razlika od "svjetova":** ovaj direktan poziv rješava "prevedi OVIM modelom/temp" bez ikakvog svijeta. Svjetovi (`bb_deklarisi_svet.py` i sl.) rješavaju uži, drugačiji problem — kad ISTA faza (obično root) treba privremeno promijeniti SASTAV takmičara dok više paralelnih procesa (po jeziku) istovremeno piše u isti dijeljeni red u bazi (race condition, s157 nalaz).

## Dio 3 — Rubni slučajevi: `--temp 1.5` i nepostojeći `--model`

Provjereno kroz `argparse` definicije (linije 342-355) i SQL logiku iz Dijela 2:

- `--temp`: `type=float, nargs="+"`, **bez ograničenja opsega**. `1.5` prolazi sintaksno; SQL provjera (`ROUND(t.vrijednost::numeric,4) = ROUND(1.5::numeric,4)`) ne nalazi red u `bb_temperature` (osim ako je neko ranije baš to registrovao) → ista poruka, preskoči, bez API poziva.
- `--model`: `type=str, required=True`, **bilo koji string prolazi**. Nepostojeće ime → `WHERE m.naziv = %s` ne vraća ništa → ista poruka.

**Nalaz:** oba slučaja — (a) potpuno nepostojeće ime/temperatura i (b) ispravno ime/temperatura koja postoji ali trenutno nije aktivna za tu fazu — daju **identičnu** poruku. Skripta ne razlikuje typo od neaktivnog stanja kataloga. Zabilježeno kao poznato ograničenje, ne kao hitna popravka.

## Dio 4 — Logika odluke "da li se prevodi" (already_done, seed_map, prag)

Flavio predložio tri hipoteze o pravilu odlučivanja. Provjereno kroz kod (linije 438-449):

- **Korak 0 (uvijek):** `todo = rečenice gdje NIJE already_done()` — `already_done()` (linije 278-283) provjerava `prevodi_knjige_id + recenica_id`, gdje `prevodi_knjige_id` već enkodira punu konfiguraciju (knjiga+jezik+faza+model+temp+prompt+embedder+runda). Dakle "nije prevedeno OVOM tačnom konfiguracijom", ne "nikad prevedeno bilo čim".
- **Faza 1 (root, `is_refine=False`):** tu se stane — čista idempotentnost, bez provjere pobjednika/praga.
- **Faza 2+ (refine, `is_refine=True`):** dvije dodatne filtracije redom — mora postojati pobjednik (`x[0] in seed_map`), pa mora biti ispod praga (`seed_map[x[0]][1] < args.prag`).

**Gdje se postavlja prag i runda:** `--prag` je CLI argument SAMO na `bb_03_prevod.py` (default 0.95); potvrđeno `grep`-om da `run_faza.sh` NE parsira niti prosljeđuje `--prag` — uvijek 0.95 kad se ide kroz standardne orkestratore. `--runda` JESTE parsirano i proslijeđeno kroz `run_faza.sh` (linije 20/52).

## Dio 5 — Flaviov misaoni eksperiment: 5 faza, bilo koji redoslijed

Flavio predložio (kao san, ne plan): `1) nllb@0.0 - sudija - pobjednik, 2) mistral@0.1 gated<0.95 ..., 3) mistral@0.8 ..., 4) glm@0.1 ..., 5) glm@0.8 ...`, u bilo kom redoslijedu.

**Analiza:**
- Gated faze (2-5) MOGU teći u bilo kom redoslijedu među sobom — svaka nezavisno čita TRENUTNOG apsolutnog pobjednika u trenutku poziva (potvrđeno pravilo iz s139, empirijski testirano u s147 permutacijskom eksperimentu: redoslijed mijenja SADRŽAJ sidra i postotak otvaranja gate-a, ne dozvoljenost).
- Jedini tvrd uslov: bazna/root faza mora prvo proizvesti bar jednog pobjednika prije nego ijedna gated faza ima šta da radi.
- Ako je "1) nllb@0.0" zamišljeno kao CIJELA bazna faza (bez mistral/glm) — krši `docs/KONCEPT.md` §2 ("najmanje 2 konkurentna LLM prevodioca u baznoj fazi" + "najmanje 1 namjenski MT"). Provjereno u šemi (`\d bb_faze_a1`): **nema CHECK constrainta** koji bi to tehnički spriječio — prepreka je čisto dokumentovan princip, ne baza.
- **Otkriven bitan nalaz:** produkcioni "svijet 2" (mistral+nllb, standard od s159, cijeli k12 se tako prevodi) VEĆ ima samo 1 LLM + 1 MT u root fazi — već krši §2 minimum, tiho, neprimijećeno do ove sesije.

## Dio 6 — Flaviova samorefleksija i predložena istinitosna tabela

Flavio je prepoznao da je "root faza", "self-refine" i "svjetovi" izmislio kao posljedicu iste greške — miješanja operativne preference ("dobro je imati konkurenciju modela") sa logičkom nužnošću ("mora postojati prevod da bi seed postojao"). Predložio je istinitosnu tabelu (tehnika iz njegovog ranijeg NLP iskustva) sa tri pitanja da se to razdvoji.

**Pitanja:**
- Q1 = postoji li pobjednik za rečenicu/jezik?
- Q2 = koristi li OVAJ pokušaj seed (prompt≠'base')?
- Q3 = da li je prag aktivan?

**Tabela:**

| Q1 | Q2 | Q3 | Ishod | Odgovara danas |
|---|---|---|---|---|
| F | – | – | PREVEDI (uvijek) | faza=1 — radi |
| T | F | F | PREVEDI (uvijek) | faza=1 — radi |
| T | F | T | PREVEDI ako pobjednik<prag | faza 10 (gated bez seeda) — radi |
| T | T | F | PREVEDI (uvijek) | NE postoji čisto — jedini put je --prag > 1.0 |
| T | T | T | PREVEDI ako pobjednik<prag | standardni refine — radi |

**Nalaz — pravi bug otkriven tabelom:** kod veže "mora postojati pobjednik" (Q1-zahtjev) na `is_refine` (faza≥2) kao cjelinu, ne na Q2 (koristi li se seed) posebno. Gated-bez-seeda faza (npr. faza 10, `PROMPT_NAZIV='base'`) TIHO preskače rečenice koje nemaju baš NIJEDAN prevod — red 1 tabele (Q1=F) je pogrešno spojen sa redom 3, umjesto tretiran nezavisno. Praktična posljedica: pokretanje gated faze na potpuno neprevedenom opsegu daje 0 rezultata bez objašnjenja. **Neispravljeno — samo identifikovano.**

**Zaključak (Flavio):** "root" nije bio posebna kategorija, nego samo IME dato redu Q1=F u tabeli — logička posljedica stanja podataka, ne dizajn koji treba registraciju/minimum/partial-unique.

## Dio 7 — Tri Flaviove "želje" (provjerene naspram koda)

1. **"Prevedi bez obzira na stanje"** = runda — tačno, potvrđeno.
2. **"Prevedi ako rečenica NIKAD nije prevedena ni sa čim"** — NE postoji danas kao ugrađen mod. `already_done()` gleda samo TAČNU konfiguraciju (Dio 4), ne "ikad bilo čim ikad prevedeno" — bio bi potreban drugačiji upit.
3. **"Prevedi ako nema nijednog prevoda iznad praga"** — poklapa se sa postojećim gate mehanizmom, uz nijansu da gate gleda POBJEDNIKA (argmax) kao predstavnika cijelog skupa, ne svaki red pojedinačno.

## Dio 8 — Seed i prag kao nezavisne ose; redni broj kao izvediva stvar

Flavio potvrdio eksplicitno: seed i prag NISU povezani (mogu biti oba aktivna, samo jedan, ili nijedan) — 2×2 kombinacija, sve četiri smislene kao samostalne.

**Redni broj pokušaja** (Flavio: "prirodno mi je da je prvi prevod redni broj 1"): NE treba čuvati kao kolonu — izvediv je iz `created_at` (`ROW_NUMBER() OVER (PARTITION BY recenica_id, jezik_id ORDER BY created_at)`), radi za SVAKI atom, čak i neplanirane. Predloženo (Claude) da se prati ODVOJENO po Q2 osi — širina bazena (broj Q2=F pokušaja, nezavisni glasovi) vs dubina lanca mutacije (broj Q2=T pokušaja, uzastopno poboljšanje) — umjesto jednog zbirnog broja, jer miješanje gubi baš tu razliku. Flavio se složio konceptualno, uz priznanje da mu je jedan zbirni broj intuitivniji.

**"Tip" prevoda** (root/seed/prag) svodi se na: prompt_id (već postoji, seed da/ne) + izvediva pozicija (root nije treći tip, samo pozicija=1). Prag NIJE osobina prevoda nego osobina ODLUKE prije prevoda — ne ostavlja trag u samom redu (dvije osobe mogu pokrenuti identičan poziv, jedna sa pragom jedna bez, isti rezultujući prevod ako je pobjednik već bio ispod praga u oba slučaja).

## Dio 9 — Prag istorija (razmotreno i odbačeno)

Flaviovo pitanje: da li bi bilježenje "koji je prag korišten pri svakom pozivu" pomoglo budućim prevodima. Kontekst: finansijski cilj (manje dodatnih prevoda) naspram poriva za genetskom raznolikošću (više različitih prevoda), plus signal slaganja nezavisnih modela kao potvrda kvaliteta.

**Zaključeno (Flaviova eksplicitna odluka, zadnja u ovoj niti):** NE graditi sada. "Globalni" prag (0.95) mu odgovara kao dovoljno dobar kompromis; ne želi eksperimentisati sa variranjem praga niti graditi istoriju poziva. Napomenuto da je informacija ionako rekonstruktivno izvediva iz logova (`docs/RUNOVI.md` + `parse_run_logs.py`, s117) ako ikad zatreba, bez nove kolone.

## Dio 10 — Zatvaranje niti

Flavio je eksplicitno zatražio da se ne nastavlja dalje u istoj sesiji (npr. pitanje "da li 'faza' uopšte treba da opstane kao pojam" ostaje otvoreno, neodgovoreno). Cijela nit izričito tretirana kao misaoni eksperiment — "nema veze sa stvarnošću" — ništa u bazi/kodu nije mijenjano tokom Dijelova 5-9.

---

## Stanje na kraju sesije

**Kod:** nedirnut (samo čitanje/grep radi provjere).

**Baza:** nedirnuta (sve read-only osim prirodnog rasta od Flaviovog paralelnog k12 rada).

**Web:** nedirnut, BB_VERSION se ne mijenja.

**Memorija:** zapis #30 dopunjen (Dio 1) sa s144-s161 nastavkom.

**README:** ažuriran ovim zatvarajućim commitom — §9 s162 snapshot, header/footer datum/sesija, §14 novi otvoreni koncept.

## Otvoreno za sljedeću sesiju

1. **Konceptualna revizija "faze"** (ako Flavio želi nastaviti) — da li "faza" treba da opstane kao pojam, i u kom obliku: (a) potpuno ukinuta u korist "poziva" kao jedinice (prag postaje atribut poziva), ili (b) zadržana ali samo kao neobavezujući "recept" (imenovana kombinacija argumenata) bez ikakvog minimuma/partial-unique tretmana za "prvi".
2. **Bug otkriven u Dijelu 6, neispravljen:** gated-bez-seeda faze (npr. faza 10) tiho preskaču rečenice koje nemaju nijedan prethodni prevod, iako im seed nije potreban — trebalo bi da rade kao root (Q1=F red tabele) za takve rečenice.
3. **`docs/KONCEPT.md` §2 nesklad sa praksom** (svijet 2 već ima samo 1 LLM u root) — dokument nije mijenjan ove sesije, otkriće samo zabilježeno; odluka o reviziji dokumenta nije donesena.
4. Sve iz s159-s161 i dalje otvoreno: "treći svijet" (glm temp split), Rupa A (pipe/tee), stepenasti retry backoff, session_159 IT nesklad, k12 nastavak.

## Lekcije sesije

- **Istinitosna tabela razdvaja logičku nužnost od operativne preference na način na koji proza (uključujući dokumentaciju kao KONCEPT.md) ne može** — Flaviova metoda iz preddobra NLP-a, direktno primijenjena i pokazala se vrijednom: otkrila je i konkretan bug u kodu (Dio 6) i konceptualno mjesto gdje se sistem greškom pretvorio u nešto rigidnije nego što je njegovo vlastito jezgro zahtijevalo.
- **Provjera "šta nas sprečava" treba uvijek razdvojiti tehnički nivo (DB constraint) od dokumentovanog principa** (KONCEPT.md) — ništa u šemi ne sprečava jednu-model root fazu; prepreka je bila isključivo na nivou teksta koji tretira preferencu i nužnost istim jezikom.
- **Kad se predlaže "šta je moguće/dozvoljeno"**, provjeriti kod/šemu direktno (argparse definicije, SQL EXISTS uslove, `\d` na tabeli) — ne nagađati iz README primjera koji su eksplicitno označeni kao istorijski.
- **Prije zaključivanja da je nešto novo, provjeriti da li već krši postojeći princip u produkciji** — otkriće da svijet 2 već krši KONCEPT.md §2 promijenilo je okvir cijele rasprave, od "da li smijemo" u "već radimo, samo nismo primijetili".

Sesija zatvorena SAMOSTALNO od Claudea (Flavio eksplicitno autorizovao: "Uradi ovu dokumentaciju samostalno bez moje kontrole i odobrenja").

---

*Flavio & Claude · Buchenberg · Sesija 162 · 5. avgust 2026.*
