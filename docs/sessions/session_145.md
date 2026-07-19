# Session 145 — Hound analiza, bootstrap ispravka, "runda" dizajn

**Datum:** 19. jul 2026.
**Fokus:** Analiza Flaviovog samostalnog runa (Hound k1, 200 rečenica ×
de/hr/it/sr, faze 4/5/6), zatim dvije nezavisne teme otvorene u razgovoru:
(1) ispravka pogrešnog opisa i STVARNI kod-fix "bootstrap tihi no-op"
problema iz s144, (2) razrada i test Flaviove ideje "runda" kao alternative
klon-triku za ponovno pokretanje iste faze.

## Zdravlje na početku
50.624 rečenice · 1.608.553 prevoda · 302.168 pobjednika. BB_VERSION s138.
Health check pokazao 236 poznatih rupa (nepromijenjeno), 26 uncommitted
`.bak_*` fajlova (poznat backlog), buchenweb zaostaje (s144 vs s140,
namjerno). Memorija osvježena čitanjem README-a i otkriveno postojanje
session_144.md — nepoznat memoriji (memorija je zastala na s143), pročitan
uživo (ista lekcija kao s143/s144: čitati dokumente, ne oslanjati se na
sažetke).

## Zdravlje na kraju
50.624 rečenice · 1.608.553 prevoda (nepromijenjeno — nula pipeline poziva
ove sesije) · 302.168 pobjednika. BB_VERSION ostaje s138 (web netaknut).
Kod izmijenjen: `src/bb_aktivni_modeli.py` (fallback fix). Dokumenti
izmijenjeni: `README.md`, `docs/PLAN-KONFIGURACIJA.md`, novi
`docs/sessions/session_145.md`.

---

## 1. Analiza — Hound (k1), 200 rečenica, de/hr/it/sr, faze 4/5/6

Flavio je prije sesije samostalno pustio gated refine faze 4/5/6 na Hound-u,
prvih 200 rečenica, četiri jezika. Zatraženo: kratka analiza mješavine
stari/novi model × stari/novi refine.

**Gate se otvorio na 62/800 rečenica-jezik parova (7.75%)** — de 17, hr 16,
it 9, sr 20.

**Kad je gate otvoren, novi gated refine pobjeđuje 79% (49/62)** — de 65%,
hr 94%, it 100%, sr 70%. Snažna potvrda dizajna: naspram ranijeg ne-gated
head-to-head rezultata (25%, s134) i starog agregatnog win-rate-a (30%),
headroom gate zaista cilja rečenice gdje ima prostora za poboljšanje.

**Zanimljivi rubni slučajevi (traženo "svašta"):**
- 2 rečenice (hr/109, sr/17) gdje penzionisani stari model (gemma3:12b,
  faza `refine`) i dalje drži tron — konkretan primjer hr/109: stari refine
  0.9326 vs najbolji novi pokušaj (refine-lenient-gated, mistral-large-3)
  0.9296, razlika 0.003.
- 11 rečenica gdje je gate otvoren ali NIJEDAN pokušaj (stari ni novi
  refine) nije uspio nadmašiti base — svi skorovi 0.91–0.95, tik ispod
  praga, vidljiv trag opadajućeg headroom gradijenta iz s144.
- Unutar tri gated faze: `refine-gated` (originalni prompt, pokreće se prvi
  u lijevku) uzima 76% pobjeda (37/49), `refine-lenient-gated` 7,
  `refine-strict-gated` 5 — očekivano, faza 4 "pokupi" većinu popravljivih
  rečenica prije nego 5/6 dobiju priliku (broj kandidata opada kroz lijevak:
  npr. sr 20→10→9).
- U bazi (root), glm-5.2 dominira na sva 4 jezika (74-87 pobjeda), ali stari
  par i dalje drži solidan dio (gemma3 35-46, ministral 10-28 po jeziku).

**Nakon 4/5/6, gate bi se ponovo otvorio na 22/800 (2.75%)** — tvrd rep.
Od tih 22: 9 su rečenice gdje je novi gated refine već pobijedio i
poboljšao tekst ali ostao ispod 0.95 (drugi pokušaj bi bio refine-na-refine,
pošto gate gleda trenutnog pobjednika); 11 su base koje nijedan refine nije
uspio popraviti; 2 su stari-refine ostaci. Svi skorovi 0.916–0.950.

---

## 2. "Trik" podsjetnik — klon faza 7/8/9

Flavio je podsjetio da bi ponovno pokretanje gated refine-a na preostalih
22 rečenica zahtijevalo isti trik kao faza 2→3: klonirati 4/5/6 u 7/8/9
(nov `faza_id`, isti a1/a2/a3 izbor), jer `UNIQUE(..., faza_id, ...)` na
`bb_prevodi_knjige` blokira ponovni pokušaj iste trojke unutar iste faze.
Potvrđeno: mehanizam identičan, uz napomenu da prag (0.95) nije dio UNIQUE
kombinacije, pa se ne može mijenjati po pokušaju bez šire izmjene.

Ovo je pokrenulo dvije odvojene teme: čišćenje bootstrap problema (§3) i
razrada alternative klon-triku (§4).

---

## 3. Bootstrap "tihi no-op" — ispravka opisa i STVARNI kod-fix

Flavio je iskreno rekao da ne razumije šta se dešava i zašto — zatraženo
objašnjenje prije bilo kakve popravke.

**Prvi pokušaj objašnjenja bio je pogrešno fokusiran** — Claude je pomiješao
"da li rečenica ima seed za refine" (ispravna provjera, po rečenici, u
`bb_03_prevod.py`, koristi trenutnog pobjednika bilo koje faze) sa "koje
(model,temp) parove uopšte treba pozvati u ovoj fazi" (`bb_aktivni_modeli.py`,
gleda ISTORIJU umjesto KATALOGA). Flavio je ispravno insistirao: "provjera
postojanja neke faze ne zavisi od temperature... ukoliko taj broj postoji
šta ima još da provjeravam?" — primorao razdvajanje ta dva pitanja.

**Live test prije kod-izmjene** (X-Ray princip — verifikuj, ne pretpostavljaj):
`bash -c 'set -e; x=$(exit 1); echo NEDOSTIŽNO'` — echo se NIKAD ne izvrši,
vanjski exit kod 1. Zatim direktan test `bb_aktivni_modeli.py --faza 999`
(garantovano prazna istorija) potvrdio isto ponašanje uživo kroz stvarni
`run_faza.sh`-ekvivalentni wrapper.

**Otkrivena netačnost u session_144.md:** opis "petlja se izvrši nula puta,
tiho, bez greške, ispisuje ZAVRŠENO" NIJE tačan opis stvarnog ponašanja.
`bb_aktivni_modeli.py` je već u s142 verziji (potvrđeno diff-om `.bak_s142`
vs trenutni fajl — sam upit se promijenio, `if not rows: exit(1)` zaštita
NIJE) imao zaštitu koja GLASNO zaustavlja skriptu pod `set -e`. Prethodna
sesija je vjerovatno primijenila poznatu bash zamku (command substitution +
`set -e`) kao pretpostavku umjesto da je testira — ovdje se ispostavilo da
zamka ne važi za plain variable assignment u ovom slučaju.

**Pravi uzrok (i dalje realan, samo drugačije okarakterisan):**
`bb_aktivni_modeli.py` čita "koji model/temp je VEĆ KORIŠTEN za fazu N" iz
`bb_prevodi_knjige` (istorija), ne "koji je AKTIVAN po katalogu" iz
`bb_faze_a1`/`bb_faze_a2`. Za potpuno svježu fazu, istorija je prazna →
glasna greška prije ijedne komande u petlji.

**Zašto je istorijski pristup uopšte izabran** (provjereno prije izmjene,
`SELECT` na `bb_faze_a1`×`bb_faze_a2` kros-proizvod): za fazu 1 (root),
katalog NIJE jednoznačan — sve tri temperature (0.0/0.1/0.8) aktivne za sva
tri modela (glm-5.2, mistral-large-3:675b, nllb-600M) po shemi bez sprege
a1↔a2, ali stvarno korišteno je samo 5 od 9 mogućih kombinacija (nllb je
deterministički, nikad zvan na 0.1/0.8). Za sve self-refine faze
(2,3,4,5,6...) katalog ima UVIJEK tačno 1 aktivnu temperaturu → kros-
proizvod je tamo potpuno jednoznačan.

**Dogovorena popravka (Flavio OK):** `bb_aktivni_modeli.py` prvo pokuša
istoriju kao i do sada (faza 1 uvijek ima punu istoriju, nikad ne stiže do
nove grane); ako je prazna, pada na katalog kao fallback.

**Implementacija** (heredoc + Python `str.replace()`, `assert count==1`,
standardni obrazac): dodana grana `if not rows:` PRIJE `conn.close()`, koja
izvršava drugi upit (`bb_faze_a1` JOIN `bb_faze_a2` WHERE `faza_id=%s AND
aktivan`) i ponovo puni `rows`. Poruka na **stderr** (ne stdout), da ne
pokvari `MODELI=$(...)` parsing u `run_faza.sh`.

**Testirano:**
- `py_compile` prošao.
- `--faza 4` (ima istoriju): rezultat nepromijenjen — `glm-5.2|0.8`,
  `mistral-large-3:675b|0.8`.
- Fallback grana testirana kroz sigurnu DB transakciju (`docker exec -i` —
  primijećeno usput da `docker exec` BEZ `-i` ne prima heredoc stdin,
  vraća prazan izlaz bez greške; ispravljeno za sve naredne SQL blokove):
  privremena test-faza (`test-s145-faza`, redoslijed 9999) + a1/a2 katalog
  redovi za glm-5.2/mistral-large-3:675b@0.8, upit identičan fallback grani
  u kodu, `ROLLBACK` na kraju. Vratio tačno očekivane parove. `SELECT COUNT`
  poslije potvrdio 0 zaostalih test-redova.
- `--faza 999` (ne postoji nigdje ni u istoriji ni u katalogu): i dalje
  pada s greškom kao i prije.

**Status:** kod izmijenjen, testiran, **NEKOMITOVAN** na kraju sesije (ide
u standardni git ritual). README operativna napomena ažurirana da odražava
ispravku (§9 i "Kako pokrenuti NOVU FAZU"). Detalji: `docs/PLAN-
KONFIGURACIJA.md` §4.8.

**Praktična posljedica:** buduće self-refine faze s tačno 1 aktivnom
temperaturom (npr. eventualne 7/8/9) više ne trebaju ručni bootstrap prije
prvog `run_faza.sh` poziva.

---

## 4. "Runda" — alternativa klon-triku (razrađeno, testirano, NIJE implementirano)

Flavio je predložio: dodati fazi atribut `runda` (broj pokušaja iste
konfiguracije), default 1, umjesto kloniranja cijele faze za svaki novi
pokušaj. Pitao je direktno: ima li ovo smisla, ili je klon i dalje bolji/
sigurniji, s obzirom da klon već radi bez rizika.

**Claudeova analiza:** runda je konceptualno čistija. Faza 2/faza 3 su već
zapisane kao poznata mana (s139: "tehnički identične", uvedene samo da
zaobiđu UNIQUE) — klon-trik za 7/8/9 bi tu manu ponovio, utiskujući BROJ
POKUŠAJA u IDENTITET faze (`faza_id`), što je u napetosti s KONCEPT.md
principom "identitet = minimumi + proces, NE komponente". Dodatna logička
posljedica (ne namjeravana, ali tačna): fazni pobjednik
(`bb_prev_recenica_faza`, grupisan po (rečenica, faza)) bi automatski
gledao najbolji rezultat PREKO SVIH RUNDI iste faze, umjesto da klon-trik
pravi potpuno odvojene bazene pobjednika po `faza_id`.

Cijena: `bb_prevodi_knjige` ADD COLUMN + zamjena UNIQUE (jeftino, 1.268
redova), `--runda` CLI u `bb_03_prevod.py` (isti obrazac kao `--temp`/
`--prag`) uključen u `already_done()`, `--runda` passthrough u
`run_faza.sh`, view sloj treba novu kolonu (additive, bezbjedno).

**Test — prava DDL migracija u transakciji, `ROLLBACK` na kraju:**
```sql
ALTER TABLE bb_prevodi_knjige ADD COLUMN runda INTEGER NOT NULL DEFAULT 1;
ALTER TABLE bb_prevodi_knjige DROP CONSTRAINT bb_prevodi_knjige_full_key;
ALTER TABLE bb_prevodi_knjige ADD CONSTRAINT bb_prevodi_knjige_full_key
  UNIQUE (knjiga_id, jezik_id, faza_id, model_id, temperatura_id, prompt_id, embeddings_id, runda);
```
Rezultati: (1) duplikat na runda=1 (isti tuple kao postojeći red faze 4)
PAO kao i prije — nema promjene ponašanja za default rundu (potvrđeno
indirektno: nema `INSERT 0 1` potvrde između `SAVEPOINT` i `ROLLBACK TO
SAVEPOINT`, tačna greška na stderr nije vidljiva alatu ali odsustvo uspjeha
je nedvosmisleno). (2) Isti tuple na runda=2 PROŠAO čisto — novi red,
`RETURNING id=14793, faza_id=4, model_id=18, runda=2`. (3) `v_prevodi_full`
nastavio raditi ispravno poslije ADD COLUMN (`COUNT`=132 za fazu 4,
netaknuto). (4) `ROLLBACK` potvrđen — `SELECT COUNT(*) FROM bb_faze WHERE
naziv='test-s145-faza'` = 0, isto za `bb_metode`.

**Preporuka (Claude):** runda je konceptualno čistija, klon je pragmatično
i dalje sasvim OK i već dokazan. Nije hitno — cijena čekanja je samo
gomilanje `bb_faze` redova (kozmetičko). Vrijedi implementirati ako
ponovno pokretanje gated refine faza postane rutina.

**Status:** Flavio — "implementacija za sada u drugom planu". Dizajn i
test zapisani u `docs/PLAN-KONFIGURACIJA.md` §4.9 kao spremna, provjerena
opcija za kad odluka padne.

---

## Odluke (Flavio)
- Popraviti `bb_aktivni_modeli.py` da padne na katalog kad je istorija
  prazna — implementirano i testirano ove sesije.
- "Runda" dizajn: zapisati kao razrađenu, testiranu opciju u
  `PLAN-KONFIGURACIJA.md`, implementacija odložena.
- Sesija zatvorena SAMOSTALNO (Flavio eksplicitno autorizovao unaprijed,
  odsutan od PC-a — isti obrazac kao s143/s144).

## Lekcije
1. **Pogrešan opis u prethodnoj sesiji (s144) nije bio zlonamjeran ni
   nemaran — bio je nepotvrđena pretpostavka (poznata bash zamka) koja se
   ispostavila netačnom kad je uživo testirana.** X-Ray princip
   "verifikuj, ne pretpostavljaj" primijenjen retroaktivno na prethodnu
   sesiju, ne samo na trenutni rad — čak i prethodni Claude-ov zapis može
   biti pogrešan i vrijedi ga provjeriti kad nešto "ne štima" korisniku.
2. **Flaviovo insistiranje da razdvojim dva različita pitanja ("da li faza
   postoji" vs "šta ta faza treba da radi") otkrilo je da je Claude
   provjeravao pogrešnu stvar na pogrešnom mjestu** — root-provjera
   (po rečenici, u bb_03) bila je uvijek ispravna; problem je bio što je
   "koga zovem" provjera nepotrebno zavisila od istorije umjesto kataloga.
3. **`docker exec` bez `-i` flaga tiho ne prima heredoc stdin** — vraća
   prazan izlaz bez ijedne greške (izgleda kao uspješan no-op, slično
   klasi bug-ova koje projekat inače lovi). Novo pravilo: uvijek `docker
   exec -i pgdb psql ...` kad se heredoc koristi za multi-statement SQL.
4. **Sigurna transakcija (BEGIN...SAVEPOINT...ROLLBACK) je pouzdan način da
   se testira prava DDL migracija na produkcionoj tabeli bez ijednog
   trajnog rizika** — korišteno dvaput ove sesije (bootstrap fallback test,
   runda DDL test), oba puta uspješno i bez ostataka.
5. **Alat za izvršavanje komandi ne prikazuje stderr** — Python skripte
   koje pišu greške na stderr (kao `bb_aktivni_modeli.py`) daju "tih"
   izgled u ovom okruženju čak i kad greška postoji; exit kod (`echo $?`)
   je pouzdaniji signal od odsustva vidljive poruke.

## Otvoreno / za sljedeću sesiju
- `bb_aktivni_modeli.py` izmjena nekomitovana — čeka Flaviov redovan git
  ritual (ili sljedeću sesiju).
- "Runda" implementacija — čeka Flaviovu odluku, dizajn spreman u
  PLAN-KONFIGURACIJA.md §4.9.
- 22 preostale "tvrdi rep" rečenice (Hound k1, 200×4 jezika) — čekaju
  Flaviovu odluku o daljem refine pokušaju (runda ili klon 7/8/9).
- Šire pokretanje gated faza (van k1/200 i k22 test opsega) — i dalje
  Flaviova odluka, Claude ne planira niti pokreće pipeline runove (s121).
- Git: `.bak_*` backlog i dalje raste (nepromijenjeno ove sesije).

---
*Flavio & Claude · Buchenberg · Sesija 145 · 19. jul 2026.*
