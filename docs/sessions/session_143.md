# Session 143 — Dio B: mjerenje i konkretizacija dizajna

**Datum:** 18. jul 2026.
**Fokus:** Nastavak neposredno nakon s142 (isti dan). Provjera spremnosti za Dio B
(random selekcija), mjerenje uticaja postojećih refine faza na cijelom korpusu,
razrada tri nivoa granularnosti, rješavanje pitanja podobnosti po osi (NLLB,
sudija), popunjavanje `bb_promptovi` kataloga trećom i četvrtom refine varijantom.

## Zdravlje na početku
50.624 rečenice · 1.608.271 prevoda · 302.168 pobjednika. BB_VERSION s138.
Memorija zatečena na s141 ("čeka OK za Korak 0") — README/health check otkrili
da je s142 već izvršila Dio A kraj-do-kraja. Potvrđeno čitanjem README-a,
session_140/141/142.md i PLAN-KONFIGURACIJA.md u cijelosti (na Flaviov eksplicitan
zahtjev — "nemoj se oslanjati na sažetke").

## Zdravlje na kraju
Korpus nepromijenjen (50.624/1.608.271/302.168 — nijedan prevod dodat ni obrisan).
`bb_promptovi`: 2→4 reda (dodani `refine-lenient` id=3, `refine-strict` id=4).
`docs/ANALIZA.md` dopunjen kanonskim upitima. BB_VERSION ostaje s138 (web
netaknut). Nijedna DDL komanda — samo INSERT u postojeći katalog i dokumentacija.

---

## 1. Provjera spremnosti za Dio B

Pročitan `docs/PLAN-KONFIGURACIJA.md` u cijelosti. Dio A potvrđeno izvršen (s142).
Dio B (§4 plana) je dizajn, ne izvršni redoslijed kao §3.2 za Dio A — plan
eksplicitno kaže "manje kod, više dizajn" i "graditi mjerenje/promatranje PRIJE
mehanizma". Flavio potvrdio da je ovo dobro pročitano — ova sesija razrađuje
upravo taj mjerni korak.

## 2. Root faza isključena iz statistike; filter root umjesto faza_id

Flaviova odluka: nijedna statistika za Dio B ne smije koristiti root fazu 1 —
uvijek prisutna, deterministična, nadjačala bi refine signal.

Claude je prvo predložio da postojeće faze 2/3 zahtijevaju poseban tretman
("pažnju") zbog porijekla (male, istorijske). Flavio je ispravio: **sve faze
`root=false` rade na isti način bez obzira na porijeklo** (random ili ručno
kreirane) — jedini scenario koji bi tražio novo razmišljanje je faza koja krši
same strukturne invarijante, ne "faza koja nije nastala random-om". Zaključak:
filter mora biti `bb_faze.metod_id → bb_metode.root = false`, NE `faza_id > 1`
— otporno na buduće nove faze (4, 5, 6...) bez obzira na porijeklo.

## 3. Mjerenje — obim i efekat faza>root na cijelom korpusu

Dva upita (view sloj, bez ručnog JOIN-a — `v_prevodi_full`/`v_pobjednici_full`
već nose `faza_id`/`faza_naziv` direktno post-s142):

- **Obim** (svi kandidati, `v_prevodi_full`): faza 1=97.55% (1.568.905), faza
  2=2.44% (39.286), faza 3=0.00% (80).
- **Efekat** (apsolutni pobjednici, `v_pobjednici_full`): faza 1=98.27%
  (296.946), faza 2=1.73% (5.217), faza 3=0.00% (5).

Refine je 2.44% obima ali samo 1.73% pobjeda na CIJELOM korpusu — konzistentno
s malim kontrolisanim uzorcima iz s134-138 (refine agregatno gubi).

**Flaviova oštra ali konstruktivna primjedba:** ponavljanje traženja imena
tabela/kolona/algoritma sumiranja od nule svaku sesiju je neprofesionalno.
Zahtjev: formalizovati kanonske upite trajno. Riješeno upisom u
`docs/ANALIZA.md` (project knowledge dokument koji se čita PRIJE svake
refine/pipeline analize) — nova sekcija "Kanonski upiti — obim i efekat po
fazi" s oba upita, rezultatima i objašnjenjem. Ujedno ispravljena zastarjela
UNIQUE napomena u istom fajlu (referisala staru pred-s142 shemu).

## 4. Tri nivoa granularnosti — razjašnjenje

Flaviov prijedlog: 50% Knjiga / 25% Jezik / 25% Biblioteka. Otvoreno pitanje:
da li svaki nivo mora filtrirati i po fazi i po jeziku.

Razrješenje (Claude predložio, Flavio potvrdio): **root=false filter je
fiksan na sva tri nivoa; jezik/knjiga se puštaju POSTEPENO šire, ne dodaju
svugdje**:

- **Knjiga (50%):** knjiga=K i jezik=L, root=false — najspecifičniji.
- **Jezik (25%):** jezik=L preko SVIH knjiga, root=false — popušta knjigu.
- **Biblioteka (25%):** SVE knjige, SVI jezici, root=false — popušta obje
  dimenzije, jedini potpuno stabilan fallback kad su i knjiga i jezik oskudni.

Demonstrirano na dvije ose:
- **Temperatura** (Alice, hr): DEGENERISANO — 100% na sva tri nivoa, jer je
  refine ikad aktivirao SAMO temperaturu 0.8. Nema varijanse za pokazivanje
  razlike između nivoa.
- **Model (a1)** (Alice, hr): STVARNA razlika — na nivou Knjiga, refine
  pobjednici su ISKLJUČIVO stari penzionisani par (gemma3:12b 60% /
  ministral-3:14b 40%), novi par (glm-5.2/mistral-large-3:675b) se tu nikad
  nije pojavio. Na nivou Jezik/Biblioteka pojavljuju se sva četiri modela.
  Otkriva da istorijski podaci miješaju retired i aktivne modele — preferenca
  računata sirovo bi predložila modele koje random generator ne može ni
  izabrati (van aktivnog kataloga).

## 5. Podobnost po osi — preduslov prije anti-elitizma

Flaviovo pitanje: da li "maksimalni broj korišćenja" (strop ~50% iz s139/s140)
rješava problem degenerisane temperature. Razrješenje: NE direktno — strop je
poseban mehanizam. Pravi preduslov je **brojanje PODOBNIH vrijednosti po osi
prije primjene anti-elitizma**:

- Ako osa ima SAMO JEDNU aktivnu/podobnu vrijednost u datom kontekstu (kao
  temperatura u refine), 100% NIJE kršenje "niko 100% ni 0%" — nema
  alternative da se izabere, isto kao što je faza 1 deterministična jer mora
  biti, ne zato što je pohlepna.
- Anti-elitizam/strop imaju smisla SAMO kad osa ima ≥2 podobne vrijednosti.

**Redoslijed provjere po osi:** izbroj podobne vrijednosti → ako 1, uzmi
deterministički → ako ≥2, računaj marginalnu preferencu NAD PODOBNIM
vrijednostima (uz strop/anti-elitizam).

## 6. NLLB isključen iz a1 za refine faze — bez izmjene sheme

Flavio: "Ne mora da imamo tri odvojena kataloga (MT/LLM/sudija) — a ako
mislim da je bolje, uključi." Konkretan zahtjev: min strukturna izmjena,
max iskorišćenje postojećeg.

Claude provjerio `bb_model_registar` (tabela iz s123!) — već ima tačno tu
distinkciju:
```
nllb-600M              | namenski MT model | {prevodilac}
gemma4:31b              | opšti LLM         | {sudija}
glm-5.2, mistral-large  | opšti LLM         | {prevodilac}
```
Znači razdvajanje po ulozi već postoji, samo nije bilo povezano s a1
podobnošću za refine. Odluka: NLLB isključen iz a1 izbora za `root=false`
faze preko filtera `bb_model_registar.vrsta <> 'namenski MT model'` —
NIJEDNA nova tabela ni kolona. Dodatni tehnički razlog (ne samo dizajn):
NLLB nema pojam sampling temperature (CTranslate2/beam decode, uvijek 0.0)
— prava tehnička zavisnost a1→a2 za taj jedan model, izbjegnuta potpunim
isključenjem umjesto uslovnog zaključavanja a2.

Sudija (`gemma4:31b`) potvrđen POTPUNO VAN a1/a2/a3 rotacije — fiksna
pipeline konstanta po KONCEPT.md ("tačno 1 sudija"), ne konkuriše nikad.

Verifikovano upitom:
```sql
SELECT m.id, m.naziv, m.aktivan, r.vrsta
FROM bb_modeli m LEFT JOIN bb_model_registar r ON r.naziv = m.naziv
WHERE m.aktivan = true;
```
→ 3 aktivna, filter ostavlja tačno `glm-5.2` i `mistral-large-3:675b`.

## 7. Tri refine prompt varijante — bb_promptovi popunjen

Flavio opisao tri varijante: (1) prihvati prevod ako nema boljeg (originalna,
pre-s135), (2) bez te rečenice (trenutna, post-s135 fix), (3) mora uraditi
bolje ili barem drugačije (nova).

Pronađen tačan istorijski tekst za (1) u `src/bb_03_prevod.py.bak_s114`
(`grep -n -B3 -A15 "def prevedi_refine_single"`) — sadrži doslovno "Keep the
reference only if it is already optimal." BATCH varijanta za (1) NIKAD nije
istorijski postojala (batch-refine uveden tek u s137, POSLIJE s135 fix-a) —
konstruisana po analogiji sa trenutnim batch refine tekstom, jasno označena
kao Claudeova rekonstrukcija, ne citat.

Varijanta (3) potpuno nov tekst — Flavio odobrio formulaciju prije upisa.

Upisano u `bb_promptovi` (Python/psycopg2 preko `foxuno`, connectuje se na
`balsam` — isti obrazac kao `bb_03_prevod.py`):
- id=3 `refine-lenient` (pre-s135 stil)
- id=4 `refine-strict` (nova, "must be better or meaningfully different")

Back-translation prompt (batch/single) identičan za sve — kopiran doslovno
iz postojećeg `refine` reda, ne otkucan ponovo (izbjegnuta transkripciona
greška).

**Dva self-korigovana bug-a, oba uočena PRIJE izvršenja:**
1. Redoslijed polja u Python tuple-u za `refine-strict` (batch/single
   zamijenjeni mjestima) — uočeno u vlastitom pregledu prije slanja komande,
   ispravljeno, zatražen NOV OK (sadržaj se promijenio od prethodno
   odobrene verzije).
2. `load_dotenv()` bez argumenta baca `AssertionError` kad skripta ide kroz
   `python3 << 'EOF'` stdin heredoc (`find_dotenv()` koristi introspekciju
   poziva preko `frame.f_back`, koja ne postoji bez pravog fajla). Fix:
   eksplicitan path `load_dotenv('/home/balsam/buchenberg/.env')`.

Verifikacija poslije upisa (ne pretpostavka da je upisano tačno):
```sql
SELECT naziv, prompt_prevod_batch LIKE '%already optimal%' AS ima_optimal,
       prompt_prevod_batch LIKE '%meaningfully DIFFERENT%' AS ima_different
FROM bb_promptovi ORDER BY id;
```
→ `refine-lenient` ima_optimal=t/ima_different=f; `refine-strict`
ima_optimal=f/ima_different=t. Bez zamjene kolona, bez preklapanja.

**Napomena:** nijedna od tri refine varijante (2/3/4) još nije vezana za
fazu preko `bb_faze_a3` — katalog popunjen, mehanizam selekcije (Dio B
generator) nije građen.

---

## Odluke (Flavio)
- Statistika za Dio B nikad ne koristi root fazu 1.
- Filter za "sve refine faze" = `root=false` (metod_id→bb_metode), ne
  `faza_id > 1`.
- Tri nivoa granularnosti: Knjiga 50% (knjiga+jezik) / Jezik 25% (jezik) /
  Biblioteka 25% (ništa) — ponder FIKSAN za sada, revizija nakon analize
  par hiljada refine prevoda.
- NLLB isključen iz a1 za refine faze preko `bb_model_registar.vrsta`
  filtera — bez nove sheme. "Želim da mijenjamo strukturu baze najmanje
  moguće i iskoristimo ono što imamo maximalno moguće."
- Tri refine prompt varijante odobrene i upisane (`refine`, `refine-lenient`,
  `refine-strict`).
- Kanonski SQL upiti za obim/efekat po fazi trajno u `docs/ANALIZA.md`.

## Lekcije
1. **Memorija kasni — čitati dokumente uživo, ne oslanjati se na sažetke.**
   Ova sesija počela s memorijom zatečenom na s141, dok je s142 već izvršila
   Dio A. Otkriveno tek eksplicitnim Flaviovim zahtjevom da se pročitaju
   dokumenti, ne sažeci.
2. **Porijeklo faze (random vs ručno) ne mijenja kako se ona tretira.**
   Claudeova greška: izmislio da buduće ručno kreirane faze traže poseban
   tretman. Jedini pravi kriterij je da li faza poštuje strukturne
   invarijante (bira nezavisno po tri ose, sidri se na trenutnom pobjedniku)
   — ne kako je nastala.
3. **Anti-elitizam ima smisao samo kad postoji izbor.** Osa s tačno jednom
   podobnom vrijednošću nije "100% favorit" u smislu koji strop treba
   sprečavati — nema alternative. Provjeriti broj podobnih vrijednosti PRIJE
   primjene marginalne preference.
4. **Ne graditi novu strukturu za razliku koja već postoji negdje drugo.**
   `bb_model_registar` (s123) je već imao MT/LLM/sudija razliku — trebalo je
   samo povezati je kao filter, ne praviti tri nova kataloga.
5. **Ponavljanje istog upita svaku sesiju je proces-kvar, ne sitnica.**
   Trajno rješenje (upis u ANALIZA.md) je pravi odgovor, ne obećanje da će
   se sljedeći put paziti.
6. **Provjeri redoslijed argumenata prije slanja komande na OK, posebno kod
   raspakivanja tuple-a s više polja istog tipa (string, string, string...)** —
   lakо se zamijene bez greške tipa koja bi to uhvatila.

## Otvoreno / za sljedeću sesiju
- **Dio B — mehanizam selekcije** (generator koji stvarno bira a1/a2/a3 i
  radi traži-ili-kreiraj po skupu) nije još građen — dizajn iz s139/s140/s143
  spreman, treba izvršni redoslijed analogan §3.2 iz plana za Dio A.
  `docs/PLAN-KONFIGURACIJA.md` ažuriran s ovim odlukama (§4 dopuna).
- Formula ponderisanja tri nivoa je fiksna (50/25/25) — čeka empirijsku
  reviziju nakon par hiljada refine prevoda.
- Kako se tačno implementira "širi ali nenulti interval" (anti-elitizam) —
  nije formalizovano (s139 pominje rank selection kao mogući pravac).
- Prag ~10% pokrivenosti — operativna definicija (koji view/upit) nije
  vezana za konkretan SQL.
- Kako se strop ~50% provjerava — u trenutku izbora ili naknadno?
- Tri refine prompt varijante u katalogu, nijedna još vezana za fazu preko
  `bb_faze_a3`.
- Export skripte (iz s142) i dalje nisu pokrenute na živi
  `/var/www/buchenberg/data` — odvojena buduća odluka.
- Git: 22+ necommitovanih `.bak`/`x.x` fajlova — čeka čišćenje.
- Sesija zatvorena SAMOSTALNO (Flavio autorizovao unaprijed, odsutan od
  PC-a — nije prvi put).

---
*Flavio & Claude · Buchenberg · Sesija 143 · 18. jul 2026.*
