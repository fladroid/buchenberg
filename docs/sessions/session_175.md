# Session 175 — 14. avgust 2026.

## Fokus

Tri nezavisna toka koja su se prirodno spojila u jedan dan: (1) analiza kaskada13 logova radi procjene dobre veličine komada za prevod (`min_komad` iz BPT koncepta), (2) dva nova upitna alata nad pobjednicima (`run_rupe.sh`, `run_prazno.sh`), i (3) potpuno nov, prethodno neistražen pravac — Claude.ai Scheduled tasks kao "claude-cron" za automatski satni monitoring projekta, plus otkriće nezvaničnog Ollama Cloud usage API-ja.

## Snimak zdravlja (kraj sesije, iz `run_health_delta.sh`)

| Mjera | Vrijednost |
|---|---|
| Rečenice | 50,624 |
| Prevodi | 2,094,065 |
| Pobjednici | 408,812 |
| Rupe (2b. Kompletnost prevoda) | 357 (bez promjene od početka sesije) |
| Provjere okoline/DB/Ollama/NLLB/venv/git | 41 OK / 0 problema |
| Ollama sedmično | 57.0% |
| Ollama session | 9.9% |

Rast prevoda/pobjednika (405,812 → 408,812 kroz sesiju, ~350 sedmični Ollama zahtjevi vidljivi kroz `run_ousage.sh`) dolazi iz Flaviovog pozadinskog rada (multi-jezik eksperiment, opisan niže), ne iz ove sesije direktno.

## Šta je urađeno

### 1. Analiza veličine komada (kaskada13, k12/ja)

Flavio je dao dvije grupe logova iz vlastite prakse — 8×50 (opseg 3301–3700) i 5×80 (opseg 3701–4100) — s pitanjem koja je veličina komada bolja i koliki je dobar stepen paralelnosti. Analiza je prošla kroz nekoliko rundi ispravki prije nego što je stigla do korisnog nalaza:

- **Prva greška**: izvještaj se fiksirao na "čudne greške na >400 rečenica" kao da je to nešto što treba dokazati u datim logovima, iako tih logova uopšte nije bilo u zadatom skupu — Flavio je to spomenuo kao opšti kontekst iz ranijeg iskustva, ne kao zahtjev za taj konkretan dokaz. Ispravljeno nakon eksplicitne povratne informacije.
- **Druga greška, ozbiljnija**: kad je Flavio kasnije eksplicitno tražio da se ignoriše ta linija istraživanja i fokusira samo na sirove podatke iz logova, odgovor je ipak ponovo skrenuo na "čudne greške" na kraju izvještaja — ista greška ponovljena unutar iste sesije, nakon što je već ispravljena. Flavio je to nazvao "kalkulator" ponašanjem — doslovno čitanje umjesto praćenja konteksta razgovora. Ovo se dogodilo **tri puta u sesiji** (analiza logova, "veći od 400"/"više od 8" kao opšte iskustvo a ne konkretan zahtjev, i treći put oko sitne primjedbe o navodnicima u komandnoj liniji) — obrazac vrijedan pažnje u budućim sesijama, ne izolovan incident.

Nakon ispravke, čist nalaz iz podataka:
- **Trajanje po komadu ne zavisi prvenstveno od veličine nego od trenutka pokretanja.** Komadi pušteni u punoj paralelnosti (4 istovremeno) trajali su 3–6× duže od onih puštenih kad se već oslobodilo mjesto — direktna potvrda s164 nalaza o lokalnoj RAM kontenciji, sad viđena na Flaviovim vlastitim komandama.
- Root vrijeme po rečenici slično za 50 i 80 (9s naspram 11s po rečenici) — nema znaka da veći komad sam po sebi nesrazmjerno usporava.
- Dva izolovana Ollama timeout-a (oba u 80-komadu, oba na glm pozivu, oba samo-oporavljena na "pokušaj 2/3", nula gubitka podataka).
- **Ključni nalaz iz analize po fazama (Flaviova hipoteza, potvrđena)**: manji komad ima veći udio "praznih" (+0) rundi u bloku A — 36.2% (50-komad) naspram 28.9% (80-komad). Mehanizam: manji bazen rečenica ispod praga statistički lakše "izgleda" iscrpljen dok mistral radi, iako stvarno nije. Ovo je ista mehanika koju je BPT koncept (s174) već imenovao kao cijenu sitnjenja, sad direktno izmjerena. Blok B (glm) nije pokazao isti obrazac — identična stopa praznih poziva (31.25%) u obje grupe, moguće jer glm radi dosljednije nezavisno od veličine bazena u ovom rasponu (nepotvrđeno, samo zapažanje).

**Dvanaest dodatnih ja logova** (opseg 3701–4520, komadi od 60) koje je Flavio kasnije dao ispalo je **duplikat rada** — cijeli opseg je već imao pobjednike od ranije (1–5300 kontinuirano), plus unutrašnje preklapanje (4061–4120 i 4101–4160 dijele 4101–4120) i dvije rupe u samom nizu (3821–3880, 3941–4000). Svi su tehnički uspješno završeni (nema grešaka), ali nisu korisni kao materijal za analizu veličine komada. Ignorisano po Flaviovoj instrukciji.

**Otvoreno za sledeću sesiju**: Flavio je pokrenuo tri paralelna eksperimenta — isti opseg (6001–6400 / 6401–6800 / 6801–7200), svih 11 perifernih jezika (bez de/hr/it/sr), redom komad 50/60/80. Ovo eliminiše konfaund pozicije u knjizi koji je ometao 8×50-vs-5×80 poređenje. Kad ovi rezultati stignu, treba provjeriti da li se "manji komad → veći udio praznih faza u bloku A" obrazac ponavlja dosljedno kroz svih 11 jezika.

### 2. Dva nova alata nad pobjednicima

- **`src/bb_rupe_pobjednika.py` + `run_rupe.sh`** — kompaktni intervali (od–do) gdje pobjednik postoji/ne postoji, po (knjiga, jezik) paru. `./run_rupe.sh [--knjiga ID] [--jezik KOD]`.
- **`src/bb_prazno_svuda.py` + `run_prazno.sh`** — isto, ali agregirano preko skupa jezika: "prazno" = nijedan jezik iz skupa nema pobjednika na toj poziciji, "dotaknuto" = bar jedan ima. `./run_prazno.sh [--knjiga ID] [--jezik KOD1 KOD2 ...]` (lista, razmakom, bez navodnika — dodato naknadno na Flaviov zahtjev).

Oba testirana na više knjiga/jezika, brojevi potvrđeni protiv postojećeg health checka. Otkriven usput zanimljiv nalaz: knjiga 22 (Hound Copy) pokazuje četiri razbacana ostrva dotaknutosti koja se poklapaju s poznatim test-opsezima iz s154–s158.

### 3. Scheduled tasks — "claude-cron" (novo za Flavija)

Flavio je primijetio dvije nepoznate stavke u Claude aplikaciji, "Scheduled" i "Dispatch". Istraženo preko `product-self-knowledge` skilla i zvaničnih support.claude.com članaka (ne iz memorije, jer se radi o Claude.ai proizvodu koji se mijenja nezavisno od ovog razgovora):

- **Scheduled** = ponavljajući zadaci u oblaku, rade i kad je računar ugašen/aplikacija zatvorena.
- **Dispatch** = suprotno — sa telefona zadaješ zadatak koji se izvršava na desktop računaru (mora biti budan), za pristup lokalnim fajlovima/aplikacijama. Za Buchenberg nije relevantan jer foxuno nije lokalni fajl na Flaviovom desktopu.

Flavio je uporedio Scheduled sa "claude-cron" — tačna analogija uz jednu bitnu razliku: prompt se sam prepravlja poslije prvog izvršavanja, izlaz je poruka/rezime umjesto sirovog loga, i svaki zakazan zadatak ima pristup istim alatima kao ručna sesija (konektori, fajlovi).

**Praktično kreiran i testiran, uživo, tokom sesije:**
1. Zadatak "Buchenberg health check", hourly, Auto-approve, folder=buchenberg, preko Cowork sidebar-a — Flavio ga je sam kreirao uz vođenje korak-po-korak (uključujući `step_card_display_v0` widget i čitanje pravih screenshotova ekrana da se izbjegne nagađanje o UI).
2. **Push notifikacija potvrđena uživo na Androidu** — stigla bez ikakve akcije s Flaviove strane, rješava pitanje na koje zvanična dokumentacija nije davala siguran odgovor (support.claude.com za Scheduled ne pominje notifikacije eksplicitno; samo Dispatch članak to potvrđuje zvanično). Sad je to empirijski potvrđeno za ovaj nalog.
3. Zaključeno da je "Hourly" vezan za trenutak kreiranja zadatka, ne za pun sat (vidljivo direktno iz "Next run" polja u UI, bez potrebe za nagađanjem).

### 4. `run_health_delta.sh` — satni monitoring skript

Ključna dizajn odluka (Flaviova, potvrđena kao ispravna): **Cowork prompt ostaje fiksan skelet** ("pokreni skriptu, pošalji mi izlaz") — sva logika/format/koraci žive u samoj skripti na serveru, izmjenjivi bez ikad ponovo dirati sam Cowork zadatak.

- Čuva stanje broja rupa u `schedulogs/rupa_stanje.txt`, računa deltu (server je izvor istine za poređenje, ne AI pamćenje iz prošle Cowork sesije, koje ionako ne postoji jer je svako pokretanje svježa sesija).
- Poslije Flaviove ideje o razdvajanju "kratko za push, detaljno na serveru" — prošireno da piše u `schedulogs/health_check.log` (trajna hronološka istorija: rupe, korpus brojevi, broj OK/problem provjera van rupa) dok kratka poruka ostaje jedna linija.

### 5. Otkriće: nezvaničan Ollama Cloud usage API

Flavio je pitao za automatsko praćenje Ollama potrošnje, s pravim pitanjem "kako se ulogovati bez lozinke". Odgovor: **ne treba lozinka** — postoji nedokumentovan `GET https://ollama.com/api/usage` endpoint koji prihvata isti `OLLAMA_API_KEY` (Bearer auth) koji projekat već koristi za prevod. Potvrđeno sa tri otvorena, nerazriješena GitHub feature-requesta (ollama/ollama #15132, #15663, #16448) da zvaničan API ne postoji — ovo je nezvaničan put, može se promijeniti/nestati bez najave.

Testirano uživo (`curl` sa postojećim ključem) — vratio je pun, koristan JSON: session%, sedmično%, i potrošnju po modelu. Otkriveno usput: tri modela van aktivnog rostera sa po tačno 5 zahtjeva svaki (`minimax-m2.7`, `deepseek-v4-flash:0731`, `nemotron-3-super`) — porijeklo nepoznato, prijavljeno bez pretpostavki, moguća tema za sledeću sesiju.

**Izgrađeno, sve testirano po svakoj grani:**
- **`src/bb_ollama_usage.py`** — jezgro. `fetch_usage()` (dohvat), `load_stanje()`/`save_stanje()` (JSON u `schedulogs/ollama_stanje.json`, čuva i puni snapshot po modelu, ne samo agregat), `delta_pct_str()` (dijeljena logika delte, koristi se i u kratkom i u punom izvještaju — ovo je bilo mjesto prve verzije koja je imala asimetriju, ispravljeno usred sesije).
- **`run_ousage.sh`** — wrapper (`./run_ousage.sh` pun izvještaj, `--kratko` jedna linija).
- **`health_check.py`** — nova sekcija "3b. Ollama Cloud — potrošnja", uvezena iz iste `bb_ollama_usage.py` (bez duplirane logike), snapshot bez delte (dosljedno ostatku health checka).
- **`run_health_delta.sh`** — proširen da poziva `run_ousage.sh --kratko` i dodaje drugu liniju u satnu poruku i detaljni log.

**Greška uočena i ispravljena u istoj sesiji**: prva verzija `bb_ollama_usage.py` je imala deltu za sedmičnu potrošnju samo u `--kratko` grani, ne i u punom izvještaju (iako je puni izvještaj imao deltu po modelu ispod) — Flavio je to primijetio praktičnim korišćenjem alata, ne teorijski. Ispravljeno zajedničkom `delta_pct_str()` funkcijom, primijenjenom dosljedno na session i sedmično u oba moda; testirane sve tri grane (normalna delta, prva provjera bez baze, vještački izazvan "reset" scenario).

## Lekcije

- **"Kalkulator" obrazac** (Flaviov termin) — doslovno čitanje teksta poruke umjesto praćenja konteksta i namjere razgovora, ponovljeno tri puta u ovoj sesiji na različite načine. Nije riješeno definitivno, samo prepoznato i imenovano naglas kad se desilo. Vrijedi pratiti u narednim sesijama da li se obrazac nastavlja.
- **"Više od X" kod Flavija znači blago-do-mnogo više, rijetko manje, nikad mnogo manje** — eksplicitno ponovljeno pravilo, važno za čitanje njegovih budućih formulacija o brojevima.
- **Dizajn "fiksni skelet prompta + fleksibilna skripta"** za Scheduled zadatke — Flaviova ideja, potvrđena kao ispravna kroz praksu (dodano dosta logike u `run_health_delta.sh` kroz sesiju bez ijednom dirati sam Cowork zadatak). Prenosivo na buduće scheduled zadatke.
- **Nezvanični API-ji vrijede probu kad koriste postojeći, već legitiman kredencijal** (API ključ, ne lozinka) — razlika između "zabranjeno" (lozinka/login) i "vrijedi pokušati" (već ovlašćen ključ, GET zahtjev, ništa destruktivno) je bila jasna i korisna razlika u praksi.
- Duplikat-prevod (12 ja logova, 3701–4520) je koristan podsjetnik da provjera baze **prije** čitanja logova (`run_rupe.sh`) štedi vrijeme — otkriveno je da je opseg već pokriven prije nego što se ušlo u detaljno čitanje 12 fajlova.

## Završno stanje

**Novi fajlovi (buchenberg repo):**
- `src/bb_rupe_pobjednika.py`, `run_rupe.sh`
- `src/bb_prazno_svuda.py`, `run_prazno.sh`
- `src/bb_ollama_usage.py`, `run_ousage.sh`
- `run_health_delta.sh`

**Izmijenjeni fajlovi:**
- `src/health_check.py` (nova sekcija 3b, import iz `bb_ollama_usage`)
- `.gitignore` (dodato `schedulogs/`)

**Van gita (namjerno, runtime stanje):**
- `schedulogs/` — `rupa_stanje.txt`, `ollama_stanje.json`, `health_check.log` (trajna hronološka istorija, raste sa svakim satnim pokretanjem)

**Novo van repozitorijuma, u Claude Cowork nalogu:**
- Scheduled task "Buchenberg health check" — hourly, folder=buchenberg, Auto-approve, prompt: pokreni `run_health_delta.sh` na foxunu, pošalji izlaz. Aktivan, potvrđeno radi sa push notifikacijom.

**Korpus:** 50,624 rečenica / 2,094,065 prevoda / 408,812 pobjednika / 357 rupa (v_status_faza_model, nepromijenjeno kroz sesiju).

## Sledeći koraci

1. **Multi-jezik eksperiment (u toku, Flaviov rad)** — isti opseg (6001–7200), 11 jezika, tri veličine komada (50/60/80). Kad završi, analizirati "manji komad → veći udio praznih faza" obrazac kroz svih 11 jezika odjednom — jači test od 8×50-vs-5×80.
2. Razmisliti o pragu upozorenja u `run_ousage.sh`/`run_health_delta.sh` za sedmičnu Ollama potrošnju (npr. javi ako pređe 90%, prije nego što 429 iznenadi usred prevoda) — spomenuto, nije izgrađeno.
3. Porijeklo tri modela sa po 5 zahtjeva u sedmičnoj Ollama potrošnji (`minimax-m2.7`, `deepseek-v4-flash:0731`, `nemotron-3-super`) — neriješeno, samo zapaženo.
4. Nasljeđeno iz s173/s174, i dalje otvoreno: REP analiza, `top_p`/`top_k` kao osa u šemi, sonda skaliranja Ollame (1/2/4/8/16 za threading), BPT v0 implementacija (dispečer skripta), odluka o qwenu, evaluacija sudije.
5. `buchenweb` repo i dalje zaostaje 7 sesija (BB_VERSION i dalje s168) — nije dirano ove sesije, web portal nije bio u fokusu.

---
*Flavio & Claude · Buchenberg · 14. avgust 2026. · Session 175*
