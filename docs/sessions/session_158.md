# Sesija 158 — 2. avgust 2026.

**Fokus:** Prio 1 iz s157 — race condition u `run_root_gated.sh` (globalni DB toggle `bb_faze_a1.aktivan` bez izolacije po procesu). Prvi pokušaj rješenja (ručni relativni toggle) bio je POGREŠAN pristup po Flaviovoj korekciji — konačno rješenje je koncept "deklarisanih svjetova": svaki poziv postavlja CIJELO stanje a1/a2 eksplicitno, ne relativno. Usput: prekid i oporavak `balsam` MCP konektora, tri teoretska pitanja o pragu/kombinacijama, i test niz koji je otkrio Claudeov vlastiti propust (preskočen gated korak) u obrascu koji se ponavlja kroz više sesija.

---

## Otvaranje sesije — memorijski zaostatak potvrđen

Sažetak na početku konteksta tvrdio je da je s141 (plan-only, prompt-kao-atribut) najnovije stanje. `README.md`, `session_155/156/157.md` i `health_check.py` pokazali su stvarno stanje: **s157**, sa prio-1 zadatkom već formulisanim (ručni protokol za gated-root switch, NEIMPLEMENTIRANO). Ovo je tačno onaj scenario koji je s143 upisala kao trajnu lekciju — sažetak kasni, čitati dokumente uživo. Korpus na početku: 50.624 / 1.873.377 / 352.816.

---

## Dio 1 — Prvi pokušaj rješenja (POGREŠAN pristup): ručni relativni toggle

Plan iz s157 protumačen doslovno: "promjena root konfiguracije postaje ručan, protokolom-vođen čin" → implementirano kao ulazak/rad/izlazak preko `bb_toggle_model.py --faza 1 --model glm-5.2 --aktivan false/true`, pozvanog ručno prije/poslije rada.

**Izvršeno:**
- `run_root_gated.sh` prerađen — uklonjen `cleanup()`/`trap` i Korak 1 (auto-toggle unutar skripte); skripta sad samo pokreće root+gated fazu, pretpostavljajući da je stanje već postavljeno.
- `docs/KAKO-NovaFaza.md` — nova sekcija "Protokol za gated root — ručni ulazak/izlazak", tri koraka (ulazak/rad/izlazak), checklist stavka 6.
- `README.md` §14 — naslov, blockquote (⚠️ BLOKIRA → ✅ RIJEŠENO), infrastruktura pasus ažurirani.

**Test (k22 Hound Copy, 930-939, core-4):** `bb_toggle_model.py --aktivan false` → `run_root_gated.sh` → provjera log-a (glm odsutan iz root modela, `prompt: base` potvrđen u gated fazi, gate otvoren 4/40=10%, glm pobijedio 2/4) → `bb_toggle_model.py --aktivan true`. Mehanički besprijekorno — skripta zaista više nije dirala `bb_faze_a1` sama.

Ovaj pristup je kasnije (Dio 4) proglašen nedovoljnim — vidi niže.

---

## Dio 2 — Prekid i oporavak `balsam` MCP konektora

Prije SQL provjere pokrivenog opsega, `balsam:run_command` alat je nestao iz `tool_search` rezultata (pretraga za "balsam", "docker", "psql" — ništa). Flavio je potvrdio SSH pristupom da MCP server proces na balsam hostu i dalje radi (`/home/balsam/mcp_balsam/.venv/bin/python .../server.py`, PID živ). Problem je bio na Claude-strani konektora: UI je prikazivao "Couldn't register with balsam's sign-in service" (OAuth handshake greška, referenca `ofid_dbf7314977edb8ce`).

Claude je predložio disconnect/reconnect kroz Settings i, kao rezervnu opciju, Anthropic support. Flavio je oštro odbio obje ideje kao neizvodljive/beskorisne u tom trenutku (nedjelja, "sada sede oni koji moraju, ne oni koji znaju") i **sam restartovao balsam server**. Poslije reboot-a, konektor je proradio bez daljnje intervencije.

Provjera obje konekcije (`balsam:server_status` — svi kontejneri `pgad/pgdb/ntfy/ollama` Up 4 minuta; `foxuno:run_command echo+date`) potvrdila normalno stanje. Nastavljeno bez gubitka konteksta.

**Napomena za budućnost:** ako se `balsam` konektor ponovo prikaže kao "connection issue" a MCP proces na serveru radi, prvi pokušaj treba biti restart samog balsam servera (ne disconnect/reconnect kroz UI, ne Anthropic support) — ovo je jednom riješilo problem, nije potvrđeno kao opšte pravilo.

---

## Dio 3 — Tri teoretska pitanja (Flavio), odgovorena bez zalaska u implementaciju

1. **Da li je prag 0.95 promjenljiv ili hardkodiran?** Djelimično oboje — `bb_03_prevod.py --prag` ima default 0.95, tehnički promjenljiv na najnižem nivou, ali `run_faza.sh` ne prima/prosljeđuje taj flag, pa je za standardni tok efektivno fiksan.
2. **Da li se može isključiti kombinacija model+temperatura (ne cijeli model)?** Teoretski ne bez nove strukture — a1/a2 su namjerno nezavisne ose (s142), nema reda koji predstavlja baš par. Zahtijevalo bi treću strukturu, što bi vratilo dio "slijepljivanja" koje je s142 namjerno razdvojio.
3. **Postoji li minimum kandidata po rečenici za sudiju/pobjednika?** Ne — sudija ocjenjuje koliko god kandidata postoji (makar 1), pobjednik je argmax preko dostupnog. Nema ugrađene provjere minimuma; oslanja se na to da root faza obično daje 3+ (posljedica AKTIVNIH modela, ne nametnuto pravilo).

**Dodatno pitanje:** može li se temperatura isključiti simetrično kao model? Da — `bb_faze_a2` strukturirana identično kao `bb_faze_a1`. Gotov helper (`bb_toggle_model.py`) postoji samo za a1; ekvivalent za a2 ne postoji, ali bi bio strukturno identičan.

---

## Dio 4 — Flaviova korekcija: "svjetovi" moraju biti POTPUNE deklaracije, ne relativni toggle (KLJUČNA LEKCIJA SESIJE)

Flavio je artikulisao svoj mentalni model kroz dijalog: uvijek postoji tačno JEDAN svijet koji mu treba u datom trenutku; on ga aktivira eksplicitno, imenovanom skriptom (`bb_aktiviraj_svet_1.sh` ili slično); mehanizam iza skripte (SQL, fajl, šta god) mu je irelevantan; kad aktivira svijet X, siguran je da ima SVE što mu treba i NIŠTA što bi smetalo. Ne zna niti želi znati da drugi svjetovi postoje. Multiverse (izolacija po procesu) je budućnost, ne sadašnjost.

**Prvi pokušaj implementacije ovog zahtjeva (POGREŠAN, Flavio: "Nije dobro!"):** dvije imenovane skripte (`bb_svet_standard.sh` / `bb_svet_bez_glm.sh`) koje su i dalje samo **relativno** toglovale glm (uključi/isključi TO JEDNO), oslanjajući se na pretpostavku da je sve ostalo (mistral, nllb, temperature) već u ispravnom stanju od ranije — plus međusobno referenciranje u komentarima ("vrati na standard kad završiš"), što krši "ne znam da drugi svjetovi postoje".

Flavio je precizirao grešku pitanjem: *šta ako sutra treba svijet gdje je mistral isključen, ili temperatura 0.1 isključena?* — skripte pisane za VIĐENI slučaj (glm on/off) ne generalizuju na bilo koji budući svijet.

**Ispravno rješenje:** svaki svijet je POTPUNA, eksplicitna deklaracija cijelog stanja za obje ose (a1 i a2) — ne relativni toggle jedne stvari. Implementirano:

- **`src/bb_deklarisi_svet.py`** — generički alat; prima `--faza`, `--modeli` (zarezom odvojena lista naziva koji treba da budu aktivni) i `--temperature` (isto za a2). Postavlja `aktivan = (naziv = ANY(lista))` preko SVIH redova u `bb_faze_a1`/`bb_faze_a2` za tu fazu — svako navedeno postaje aktivno, sve ostalo ugašeno, bez obzira na prethodno stanje. Ispisuje kompletno rezultujuće stanje za verifikaciju.
- **`bb_svet_1.sh`** — puna 3-way root: `mistral-large-3:675b,nllb-600M,glm-5.2`, temp `0.8,0.1,0.0`.
- **`bb_svet_2.sh`** — sužen root za gated obrazac: `mistral-large-3:675b,nllb-600M` (bez glm), temp `0.8,0.1,0.0`.

Svaka skripta neutralno imenovana (`_1`/`_2`, ne "standard"/"bez_glm"), nezavisna, ne referencira drugu. Novi svijet ubuduće = nova tanka skripta s drugačijom listom, nula izmjena logike u `bb_deklarisi_svet.py`.

**Usputno otkriće:** tokom provjere sadržaja `bb_faze_a1` za fazu 1, primijećen je neočekivan red u `bb_modeli` katalogu — `claude-sonnet-4-6` (aktivan=false, bez uticaja). Flavio je objasnio: ostatak testa modela od prije ~160 sesija, kad je testiran i Claude kao model kandidat za prevod. Legitiman istorijski artefakt, ne greška ni sumnjiv unos. Flavio je predložio da bude bar pomenut u README ("Nema veze, idemo dalje" — nije prioritet ove sesije, ostaje otvoreno).

Funkcionalna verifikacija (SQL potvrda, bez Ollama poziva): `bb_svet_1.sh` → svih 9 modela ispravno klasifikovano (3 aktivna uklj. glm, 6 ugašenih uklj. `claude-sonnet-4-6`), sve temperature ispravno (0.8/0.1/0.0 aktivne, 0.5/1.0 ugašene). `bb_svet_2.sh` → isto, samo glm ugašen. Prebačaj naprijed-nazad potvrđen dvaput.

---

## Dio 5 — Dokumentacija ažurirana na finalni dizajn

`docs/KAKO-NovaFaza.md`: sekcija "Protokol za gated root — ručni ulazak/izlazak" (iz Dijela 1) u potpunosti zamijenjena sekcijom "Protokol za gated root — deklarisani svjetovi (s158)" — objašnjava zašto je prvi pokušaj (relativni toggle) bio pogrešan, opisuje `bb_deklarisi_svet.py` mehanizam i imenovane svjetove. Checklist stavka 6 i header referenca ažurirani da odražavaju "deklarisani svjetovi" umjesto "ručni ulazak/izlazak". Svaka izmjena provjerena `grep` pretragom cijelog fajla za zaostale reference na stari pristup — nijedna pronađena.

`README.md` §14 "Gated root" — infrastruktura pasus ažuriran: `bb_deklarisi_svet.py` + `bb_svet_1.sh`/`bb_svet_2.sh` kao primarni mehanizam; `bb_toggle_model.py` (s156) ostaje kao ad-hoc/debug alat za pojedinačni model, van standardnog toka, eksplicitno tako označen.

---

## Dio 6 — Test niz (930-939 → 940-949 → 950-959) i Claudeov propust

Flavio je odobrio testiranje s realnim Ollama pozivima (budžet: >5% preostalo do sedmičnog reseta, potrošeno <1% ovim nizom).

**Test A (930-939, k22 core-4)** — pokriven u Dijelu 1, prije nego je "svijet" koncept postojao: ručni `bb_toggle_model.py` + `run_root_gated.sh`. Uspješan.

**Test B (940-949, k22 core-4, "novi svijet" = svijet 2) — Claudeov propust:** Za ovaj test Claude je odlučio da NE koristi `run_root_gated.sh` (kompletan lanac) nego da direktno pozove `run_faza.sh --faza 1` — rezonujući da mu za provjeru "da li svijet 2 isključuje glm iz roota" treba samo taj jedan korak. Root faza izvršena čisto (10/10 po jeziku, samo mistral+nllb, kako i treba za svijet 2), ali **gated faza 10 nikad nije pozvana** — test je stao na pola šeme.

Flavio je primijetio da nešto nije u redu, ali namjerno nije rekao šta ("Sta mogu? Uvek je tako... Opet sve iz pocetka... Da li je moguce da drzimo ovu promenu svaki dan i pokusavamo da je implementiramo i uvek nesto zaboravimo") — signalizirajući obrazac koji se ponavlja kroz sesije (s155 bug u seed-slanju, s157 race condition, sad Claudeov vlastiti propust u sopstvenom testu) vezan uz isti dvokoračni "sužen root + gated glm bez seed-a" mehanizam. Claude je, uz eksplicitnu uputu da pogleda posljednjih 5-6 sesija ako treba, pronašao i imenovao tačan propust bez daljnjeg navođenja.

Flavio je zatim postavio provjeru razumijevanja: *da li smo do juče ovaj "svijet" puštali jednim skriptom, a sad sa dva?* Claude je objasnio: alat (`run_root_gated.sh`) se nije promijenio niti danas radi u dva poziva — i dalje je jedan poziv koji radi oba koraka. Ono što se promijenilo bila je Claudeova ODLUKA za taj konkretan test, da zaobiđe wrapper i pozove niži nivo direktno, pa zaboravi drugi dio.

Flavio je zatim eksplicitno tražio da se zadatak izvrši **kao da nema nikakvog predznanja** o tome da je root dio već urađen — "pravi se da nemaš pojma u kom si svetu": (1) switch na svijet 2, (2) pokreni `run_root_gated.sh` za 940-949. Izvršeno bukvalno: `bash bb_svet_2.sh` (potvrdio nepromijenjeno stanje) → `run_root_gated.sh --od 940 --do 949` — root korak je bio idempotentan (0 novih Ollama poziva, `already_done()` prepoznao postojeće), gated faza 10 je ovaj put stvarno izvršena: glm@0.8/0.1, `prompt: base` potvrđen, gate otvoren 10/40 (25%: de 1/10, hr 4/10, it 1/10, sr 4/10), pobjednik ispravno birao preko cijelog bazena (glm pobijedio na nekoliko pozicija, npr. hr s940/s941/s943).

**Test C (950-959, k22 core-4, "stari svijet" = svijet 1):** `bash bb_svet_1.sh` → `run_faza.sh --faza 1` direktno (svijet 1 nema gated korak — glm je ravnopravan takmičar u root fazi odmah, 5 kandidata po rečenici: glm@0.8/0.1, mistral@0.8/0.1, nllb). Sve 4 jezika, 10/10 pozicija, pobjednik miješan preko sva tri modela (glm dominira hr/sr, mistral/nllb dijele de/it). Uspješno, bez komplikacija.

**Zaključak testnog niza:** oba imenovana svijeta (1 i 2) funkcionalno potvrđena end-to-end — svijet 2 dvaput (Test A i Test B, jednom uz ispravku propuštenog koraka), svijet 1 jednom (Test C). Mehanizam `bb_deklarisi_svet.py` + `run_root_gated.sh` (bez auto-toggle) radi kako je dizajnirano.

---

## Stanje na kraju sesije

**Kod (buchenberg repo), 6 izmijenjenih/novih fajlova:**
- `run_root_gated.sh` — auto-toggle uklonjen (Korak 1 + `trap`/`cleanup`); sad samo pokreće root+gated fazu.
- `src/bb_deklarisi_svet.py` — NOVO. Generički alat za potpunu deklaraciju a1/a2 stanja.
- `bb_svet_1.sh` — NOVO. Standardni svijet (3-way root, glm uključen).
- `bb_svet_2.sh` — NOVO. Sužen svijet za gated obrazac (bez glm).
- `docs/KAKO-NovaFaza.md` — sekcija "gated root" u potpunosti prepisana (dva puta tokom sesije — prvi pokušaj pa konačna verzija), checklist dopunjen.
- `README.md` — §14 "Gated root" ažuriran (naslov, blockquote, infrastruktura pasus); §9 dobija ovaj snapshot.

`src/bb_toggle_model.py` (s156) netaknut — ostaje kao ad-hoc/debug alat za pojedinačni model, sad eksplicitno van standardnog toka rada.

**Baza:** k22 (Hound Copy) core-4 (de/hr/it/sr) sad ima punu root pokrivenost do pozicije 959 (nastavak od ranijeg 929), sa gated fazom 10 primijenjenom na 930-949 (dva testna opsega). Trenutno DB stanje: **svijet 1 aktivan** (glm uključen za fazu 1 — standardno/podrazumijevano stanje, odgovarajuće stanje za mirovanje).

**Korpus (kraj sesije):** 50.624 rečenice / 1.873.845 prevoda / 352.936 pobjednika (+468 prevoda / +120 pobjednika kroz testni niz ove sesije — tri opsega × 4 jezika × 10 rečenica, plus gated dodaci).

**Web:** netaknut, BB_VERSION ostaje s157 (buchenweb i dalje zaostaje na s152, poznato i namjerno od ranije).

## Otvoreno za sljedeću sesiju

1. **Ideje 1/2 iz s157** (podjela glm gated faze po temperaturi; gatovanje i mistrala) sad mogu nastaviti — race condition koji ih je blokirao je riješen.
2. **Legacy red `claude-sonnet-4-6`** u `bb_modeli` katalogu — Flavio je predložio pominjanje u README kao istorijska bilješka (~s-nešto rana sesija, testiranje raznih modela); nije urađeno ove sesije, ostaje otvoreno ako se smatra vrijednim.
3. **`balsam` MCP konektor** — ako se ponovo pojavi "connection issue" a server proces radi, prvi pokušaj = restart balsam servera (vidi Dio 2).
4. Stare stavke i dalje čekaju: `predlog_root_DRAFT.py` odluka, "u toku" tabela (s149), seed-lock dizajn (s147), formalna dopuna `docs/KONCEPT.md` ako se gated-root pristup usvoji u produkciju (otvoreno od s154).

## Lekcije sesije

**Deklarisano stanje ≠ relativni toggle (Flavio, kroz dvije korekcije).** "Ulazak/izlazak" protokol iz Dijela 1 je i dalje bio krhak — oslanjao se na to da je sve OSIM eksplicitno pomenute stvari već ispravno postavljeno. Prava invarijanta koju je Flavio tražio: svaki poziv koji mijenja stanje sistema treba biti POTPUNA izjava namjere, ne razlika u odnosu na nepoznato prethodno stanje. Ovo je opštiji princip od konkretnog glm/root slučaja — primjenjuje se svugdje gdje se stanje dijeli između paralelnih aktera.

**Wrapper skripta vs ručni pozivi nižeg nivoa.** Test B je pokazao praktičnu posljedicu razdvajanja koraka koje bi trebalo raditi zajedno: kad postoji gotov wrapper (`run_root_gated.sh`) koji ispravno vezuje dva koraka, zaobilaženje wrappera radi "brže/manje pozivanja" nosi rizik da se drugi korak zaboravi. Isti obrazac (nešto vezano za dvokoračni sužen-root+gated-glm mehanizam ispadne, na različit način svaki put) primijećen kroz s155 (bug u seed-u), s157 (race condition), i sada s158 (Claudeov propušten poziv) — vrijedno imati na umu kao poznatu tačku loma ovog specifičnog obrasca.

Sesija zatvorena SAMOSTALNO od Claudea, na Flaviov eksplicitan zahtjev ("dokumentuj sve detaljno... ovog puta izuzetno bez moje kontrole i odobrenja") — isti obrazac kao ranije samostalno zatvorene sesije (s143, s147, s149, s153, s154, s155, s156, s157).

---

*Flavio & Claude · Buchenberg · Sesija 158 · 2. avgust 2026.*
