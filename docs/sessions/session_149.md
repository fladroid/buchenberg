# Sesija 149 — 23. jul 2026.

**Autori:** Flavio & Claude
**Fokus:** osvježavanje memorije + potvrda da su web_export/xray_export na starom
(ne-refaktorisanom) kodu + duži konceptualni razgovor o Flaviovoj ulozi u
odabiru šta se prevodi, koji je rezultovao probnom skriptom za predlog
sljedećeg ROOT koraka.

---

## Zdravlje na početku sesije

Checklist proveden (project files → README → session_146/147/148 → health_check).
Korpus: 50.624 rečenice / 1.680.725 prevoda / 314.168 pobjednika (raslo od s148
preko Flaviovih pozadinskih runova). 252 poznate rupe (nepromijenjeno), oba git
repoa čista i sinhronizovana (buchenberg `bff5ec7`, buchenweb `a701974`).

---

## 1. Potvrda stanja web_export/xray_export nakon s148 incidenta

Flavio je pitao da li su `bb_web_export.py`/`bb_xray_export.py` i dalje na
starom, funkcionalnom kodu nakon pokušaja refaktora u s148. Provjereno (ne
pretpostavljeno):
- `grep -n "v_pobjednici_full\|v_pobjednici_faza_full"` na oba fajla → 0
  poklapanja (nijedan ne koristi te viewove).
- `git status --short` na oba fajla → prazno (nema necommitovanih izmjena).
- `git log -3` na oba fajla → zadnji dodir s142 (`0d295d9`), ne s148.

Potvrđeno: oba fajla rade na starom, direktnom JOIN kodu iz s142. s148 pokušaj
refaktora nije ostavio nijedan trag u kodu — potpuno vraćen `git checkout`om,
tačno kako session_148.md navodi.

## 2. Kratka meta-rasprava o procesu

Flavio je iznio kritiku (ponovljenu iz s148 konteksta): kod koji dugo radi bez
greške ne treba mijenjati bez detaljno dokumentovane procedure za baš taj
zahvat — refaktoring je prioritet 2, funkcionalan kod prioritet 1. Provjereno
da li ovo pravilo već postoji prije nego što je predložen novi memorijski
zapis: **postoji, dva puta** — METHOD.md §5 ("Verifikuj, ne pretpostavljaj";
ledger grešaka koji se konsultuje, ne samo piše) i memorija s126 ("Kompatibilnost
PRIJE implementacije... Proaktivnost > isprika nakon greške"). Flaviova
ispravka: problem nije nedostatak pravila nego nekonsultovanje pravila pod
pritiskom — što je već zapisano kao poznat obrazac (s148 referencira "memorija
#24", isti obrazac kao s125/s135/s136). **Odluka: NIJE dodat nov memorijski
zapis** — dupliranje postojećeg pravila ne rješava problem konsultovanja.
Usput razjašnjeno: Flaviove oštrije reakcije nisu ljutnja/frustracija nego
iznenađenje, ponekad loše artikulisano.

## 3. Kratak prekid `balsam`/`foxuno` konektora

Usred sesije oba konektora (foxuno, balsam) su prestala da se pojavljuju u
`tool_search` (Google Drive i dalje radio normalno) — ni Flavio ni Claude nisu
ništa mijenjali. Flavio potvrdio screenshotom: oba konektora u statusu
"Connect" (ne povezano) u Settings → Connectors. Poslije Flaviovog ručnog
klika "Connect" na oba, alati su se odmah ponovo pojavili u pretrazi i radili
normalno. Infrastrukturna bilješka (auth/sesija istekla na strani konektora),
ne projektna greška — nema akcije potrebne u kodu/bazi.

## 4. Flaviova uloga u odabiru šta se prevodi — konceptualni razgovor

Flavio je opisao svoju ulogu (namjerno tako nazvanu, ne "funkciju" — uloga
zahtijeva odluku na osnovu rezultata, funkcija samo ulaz→izlaz):

**Hijerarhija jezičnih grupa** (fiksna, ali promjenjiva po Flaviovoj odluci):
- G1: de, hr, it, sr
- G2: bg, bs, mk, sl
- G3: es, fr, pt, ro
- G4: af, nl

Pravilo: traži nepotpunu knjigu unutar TRENUTNE grupe; ne prelazi na sljedeću
grupu dok trenutna ima ijednu nepotpunu knjigu. Isto važi (odvojeno, uz
mogućnost promjene "bilo kojeg jutra") za self-refine korak — trenutno pravilo
je da self-refine čeka dok ima nepotpunih root prevoda.

Ograničenje resursa: Ollama Cloud 5h sesijski + sedmični limit — nema
zvaničnog API-ja za očitavanje potrošnje (provjereno web pretragom, tri
otvorena GitHub feature request-a, mart/april/jun 2026, nijedan implementiran;
jedini način je ručni pregled `ollama.com/settings`). Odluka: za sada ručni
unos/procjena, scraping ostaje buduća nadogradnja.

### Šira ideja — razmotrena i namjerno sužena

Flavio je prvo zamišljao posebnu web stranicu koja prikazuje svaki ciklus
provjere/predloga/odluke/rezultata, i arhitekturu "agenata" (planer koji zna
šta nedostaje / worker koji traži posao i javlja završetak / refine-agent /
supervizor koji diriguje i umnožava). Claude je ovo mapirao na standardni
producer-consumer red poslova. Nakon razmatranja (uz spomen MQTT-a kao
prvobitne, potom odbačene ideje), Flavio je svjesno pojednostavio: **nova
stranica nije potrebna**, cilj sveden na jednu konkretnu funkciju.

### Dogovoren minimalni obim (za ROOT korak)

Iz `run_pipeline.sh --knjiga KK --jezici JJ --od OD --do DO` odrediti
vrijednosti KK/JJ/OD/DO. Ograničenja: 1 knjiga, 1 jezik po pozivu, OD-DO
opseg max 200. Paralelizam po jeziku i cijepanje opsega na više workera
razmatrani ranije u razgovoru (ista knjiga, različiti jezici grupe kao
prirodna osa paralelizma) ali NISU dio dogovorenog obima ove sesije — ostaju
zabilježeni kao pravac za kasnije.

### Implementacija — `predlog_root_DRAFT.py` (probna, necommitovana)

Prva verzija: frontier (prva pozicija koja nedostaje minus 1) računat
**odvojeno po svakoj AKTIVNOJ (model,temp) kombinaciji** za fazu 1, uzet MIN
preko svih — analogno logici `bb_aktivni_modeli.py` (koja je pročitana i
ponovo iskorištena za spisak aktivnih kombinacija: glm-5.2@0.8/0.1,
mistral-large-3:675b@0.8/0.1, nllb-600M@0.0). Prvi test: Hound/de →
OD=1301 DO=1500 (frontier=1300/3852).

**Flaviova korekcija (dva koraka, ključna):** knjiga+jezik je pokrivena do
pozicije N ako je **BILO KOJI** model u root fazi preveo tu poziciju —
nezavisno od toga da li je taj model trenutno aktivan. Prvo objašnjenje
(preskoči knjigu ako JE NEKA kombinacija ikad postigla puno pokriće) je bilo
blizu ali još netačno; drugo, konačno objašnjenje: pokrivenost se gleda **po
poziciji**, ne po modelu ni po kombinaciji — bilo koji model na toj poziciji
je dovoljan.

Provjereno prije izmjene koda (X-Ray disciplina, ne pretpostavljati):
```sql
-- Hound/de, bilo koji model, faza 1
SELECT COALESCE(MIN(gs) - 1, 3852) FROM generate_series(1,3852) gs LEFT JOIN (...) ...
→ 3852  -- potpuno pokriveno
```

Skripta pojednostavljena — uklonjena petlja po aktivnim kombinacijama iz
frontier računanja (aktivne kombinacije više NISU potrebne za "je li
kompletno", samo bi bile relevantne za to koje modele `run_pipeline.sh`
interno zove, što skripta i ne dira). Nova, ispravna logika: `generate_series`
+ `LEFT JOIN` na DISTINCT pozicije iz BILO KOJEG modela → frontier po
(knjiga,jezik,faza=1); OD=frontier+1, DO=min(frontier+200,total); petlja kroz
grupe redom, vraća prvu nepotpunu (knjiga,jezik) unutar prve nepotpune grupe.

**Validacija:**
- Hound/de (ranije lažno-nepotpun) → ispravno preskočen (3852/3852 kompletno).
- Prvi stvarni predlog: **Moby Dick/de, OD=1801, DO=2000** (frontier=1800/9764)
  — potvrđeno poklapanje sa "Stanje prevoda" tabelom iz health checka
  (Moby Dick de: 1800/1800, prev=pobj, nula rupa).
- Ponovljen poziv bez izvršenja između → identičan predlog (očekivano,
  skripta je stateless upit, ne mijenja bazu).

### Otvoren dizajnerski problem — "u toku" stanje

Demonstrirano uživo: pošto baza poznaje samo dva stanja po poziciji
("prevedeno"/"nije prevedeno"), ponovljen poziv predloga dok bi neki stvaran
posao bio u toku (pokrenut a nezavršen) vratio bi ISTI predlog — dva procesa
bi krenula na isti opseg. Claude je predložio tri opcije (nova tabela +
nezavisan proces koji je ažurira / oslanjanje na `ps aux` provjeru procesa na
serveru / čista disciplina bez baze dok je Flavio jedini izvršilac).

**Flaviova odluka:** treba I tabela I nezavisan proces koji je ažurira — uz
eksplicitno upozorenje da naivna simulacija DB transakcija samo tabelom i
indikatorima često ne radi ("mnogi su polomili zube" pokušavajući to).
Da li je taj nezavisni proces čovjek (Flavio) ili "inteligentan" agent —
OTVORENO, treba bolje promišljanje. Dizajn NIJE dalje razrađivan ove sesije —
eksplicitno odloženo za kasnije.

---

## Odluke (Flavio)

- Nova web stranica za prikaz ciklusa/predloga/odluka — NIJE potrebna.
- Definicija "kompletno": po poziciji, bilo koji model u root fazi, ne po
  (model,temp) kombinaciji i ne zahtijeva aktivne/nove modele specifično.
- Prvi obim: 1 knjiga, 1 jezik, OD-DO max 200 — paralelizam/cijepanje odloženi.
- Ollama usage API ne postoji zvanično — ručni unos za sada, scraping budući.
- "U toku" praćenje: treba I tabela I nezavisan proces (ne samo tabela) — dizajn
  ko/šta je taj proces ostaje otvoren.
- Nije dodat nov memorijski zapis za "refaktoring poslije dokumentacije" —
  pravilo već postoji (METHOD.md §5, memorija s126).

## Lekcije

1. **Provjeri da pravilo već ne postoji prije nego predložiš novo.** Flaviova
   intervencija ("to bi trebalo da već piše svuda") spriječila je nepotrebno
   dupliranje postojećeg principa u memoriji.
2. **Prva formulacija Flaviovog pravila o kompletnosti nije bila konačna** —
   trebalo je dva pokušaja objašnjenja da se stigne do prave granularnosti
   (po poziciji, ne po modelu/kombinaciji). Provjera u bazi PRIJE izmjene
   koda (X-Ray disciplina) uhvatila je razliku odmah, prije nego što je
   pogrešna verzija ušla u produkciju.
3. **Ambiciozna arhitektura ("agenti", MQTT) prirodno se suzila kroz razgovor**
   kad je Flavio sam sebe vratio na konkretan, odmah koristan obim — vrijedno
   ostaviti prostor za to umjesto guranja odmah ka najsloženijem rješenju.
4. **"Idempotentno" nije isto što i "sigurno za ponovljeno pozivanje dok je
   posao u toku"** — planer koji samo čita bazu je stateless i ispravan sam
   za sebe, ali otvara race condition čim se pretpostavi da ga nešto (čovjek
   ili agent) poziva dok prethodni predlog još nije izvršen do kraja.

## Otvoreno / za sljedeću sesiju

- **`predlog_root_DRAFT.py`** ostaje probni/necommitovan (analogno
  `analiza_s147_permutacije.py` iz s147) — treba odluku: preimenovati i
  commitovati kao pravi alat, ili ostaje eksploratorna skripta dok "u toku"
  dizajn ne postoji.
- **"U toku" tabela + nezavisan proces** — dizajn nije razrađen, samo
  imenovan kao potreba. Pitanje ko/šta ažurira tabelu (Flavio ručno vs.
  automatizovan proces) ostaje otvoreno.
- Paralelizam po jeziku unutar grupe (ista knjiga, više jezika odjednom,
  svaki svoj OD/DO) — pomenuto, nije implementirano.
- Ista logika (kompletnost po poziciji, bilo koji model) treba razmotriti i
  za self-refine korak (faze 2+) — nije diskutovano ove sesije, samo root.
- Git: `predlog_root_DRAFT.py` postoji na disku, netaknut od git-a (namjerno).

---

## Završno stanje

Korpus nepromijenjen u smislu izvršenih akcija ove sesije (nula pipeline
poziva od strane Claudea, u skladu sa s121 pravilom) — brojevi mogu biti veći
od Flaviovih pozadinskih runova. BB_VERSION ostaje s146 (web nedirnut).

Sesija zatvorena SAMOSTALNO od Claudea (Flavio eksplicitno autorizovao,
odsutan od PC-a, izuzetak).

---

*Flavio & Claude · Buchenberg · Sesija 149 · 23. jul 2026.*
