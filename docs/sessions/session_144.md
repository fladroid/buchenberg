# Session 144 — Dio B preokret: gated fiksne faze umjesto random selekcije

**Datum:** 19. jul 2026.
**Fokus:** Nastavak s143 (ista nit, druga sesija). Trebalo je formalizovati
mehanizam selekcije za random Dio B (rank selection formula) — umjesto toga,
Flaviova provokacija o sopstvenom istorijskom iskustvu ("6 minuta po
rečenici") pokrenula je preispitivanje cijele premise. Sesija je završila s
potpuno drugačijim, jednostavnijim Dijelom B: tri fiksne gated faze umjesto
random generatora.

## Zdravlje na početku
50.624 rečenice · 1.608.271 prevoda · 302.168 pobjednika. BB_VERSION s138.
Memorija osvježena čitanjem README-a, session_141/142/143.md i
`docs/PLAN-KONFIGURACIJA.md` uživo (na Flaviov eksplicitan zahtjev, ista
lekcija kao s143 — ne oslanjati se na sažetke).

## Zdravlje na kraju
50.624 rečenice · **1.608.277** prevoda (+6, test-prevodi k22/hr pozicija
109 kroz šest bootstrap poziva) · 302.168 pobjednika (nepromijenjeno —
zamjena postojećeg reda na poziciji 109, ne dodavanje). BB_VERSION ostaje
s138 (web netaknut). Tri nova DB reda u `bb_faze` (id 4/5/6) + prateće
`bb_faze_a1/a2/a3` veze. Dvije izmjene koda (`bb_03_prevod.py`,
`bb_04_pobjednik.py`), README i `PLAN-KONFIGURACIJA.md` ažurirani.

---

## 1. Formalizacija rank selection (napuštena, ali dokumentovana)

Prije preokreta, dogovorena je konkretna formula za "širi ali nenulti
interval" iz s139/s140 dizajna: linear rank selection,
`P(r) = [(2-s) + 2(s-1)·r/(n-1)] / n`, `s∈(1,2)` pritisak selekcije,
default `s=1.5`. Provjereno da za n=2 daje ~75%/25%, blizu Flaviovog
originalnog s139 primjera (70%/30%). Formula ostaje zapisana ovdje kao
istorijski trag — nije implementirana jer je cijeli mehanizam koji ju je
trebao koristiti napušten u nastavku sesije.

## 2. Provokacija — Flaviovo pitanje o "6 minuta" i matematici kataloga

Flavio je iznio sopstveno istorijsko iskustvo: rani Buchenberg je imao
~6 minuta po rečenici s mnogo jednostavnijim algoritmom, što ga je godinama
odvratilo od ideje. Postavio je provokativno pitanje: sa fiksnim MT (NLLB),
2 LLM-a za prevod, 1 LLM-sudijom, i varijablama temperatura×prompt — ako
imamo npr. 3 prompta × 5 temperatura = 15 kombinacija, ne treba li samo
pustiti svih 15 da se takmiče po fazi, umjesto graditi random mehanizam?
"Šta sam dobio sa self-refine? Da li me je opet '6 minuta' odvelo negdje
gdje nije trebalo?"

**Claudeova analiza:** genetski algoritam (mutacija, marginalna preferenca,
anti-elitizam) opravdan je kad je prostor pretrage OGROMAN — kad se ne može
iscrpiti direktno. Sa fiksnim, poznatim katalogom (na kraju: 2 modela × 3
prompta × 1 istorijski korišćena temperatura = 6 smislenih kombinacija),
to nije taj slučaj — to je katalog koji se može prstom prebrojati. Mutacija
posebno nema smisla: Flavio već ručno pravi nove promptove
(refine-lenient/strict), to nikad nije bio automatski korak.

**Reformulacija pravog problema:** ne "koju od N kombinacija probati" nego
"da li uopšte vrijedi probati OVU rečenicu" — headroom pitanje, ne izbor
konfiguracije. Originalni prag ~10% iz plana (§4.4) mjerio je POKRIVENOST
(koliko urađeno), ne KVALITET seeda (ima li prostora za poboljšanje) —
pogrešna osa praga.

## 3. Mjerenje — seed_score vs. win-rate, cijeli korpus

Bucket-analiza (`width_bucket`, `v_prevodi_full`/`v_pobjednici_full`,
filter `bb_metode.root=false` po s143 kanonskom pravilu): za svaku
rečenicu gdje je refine POKUŠAN, mjeri se najbolji root/faza-1 kandidat
(`seed_score`) i da li je apsolutni pobjednik na kraju iz refine faze.

Rezultat: čist, monoton gradijent kroz 20+ bucketa. Ispod seed_score ~0.85
refine pobjeđuje 77-91% puta; oko ~0.92 win-rate prelazi ispod 50%; iznad
~0.97 refine gubi 90%+ puta. Nije šum — gladak pad potvrđuje da headroom
gate radi.

Provjera gornjeg ekstrema (seed=1.0000 tačno, n=471): 90% su rečenice
kraće od 20 znakova (naslovi, brojevi) — objašnjava blagi porast win-rate
na samom vrhu kao artefakt trivijalnog sadržaja, ne preokret gradijenta.

## 4. Konfaund — mješavina generacija modela (Flaviova sumnja, opravdana)

Flavio je posumnjao da mješavina starih (penzionisanih) i novih modela u
istorijskim podacima izobličuje gradijent. Provjera (`seed_gen × refine_gen`
raspodjela): old/old=27.204 (69%), new/old=6.620 (17%), new/new=2.748 (7%),
nllb/old=2.576 (7%), nllb/new=138 (0.4%) — ukupno 39.286, poklapa se sa
s143 nalazom obima refine faza.

Ponovljena bucket-analiza SAMO na čistom novi-seed×novi-refine presjeku
(n=1.382 nakon isključivanja izjednačenih redova) — gradijent se održao,
ali 50%-prag se pomjerio sa ~0.92 (mješani agregat) na **~0.95** (čist
presjek). Zaključak: konfaund je mijenjao BROJ, ne OBLIK nalaza — Flaviova
sumnja bila opravdana i promijenila je odluku o pragu.

Dodatna finija provjera niskog ekstrema (0.30-0.80): otkrivena
nemonotonost na samom dnu (seed 0.37-0.40, n=77, win-rate 22-44% —
suprotno očekivanju). Hipoteza: strukturni problem (prazan/pokvaren
prevod) a ne headroom — mali n, zabilježeno kao opservacija, ne mijenja
odluku o gornjem pragu.

**Usvojen prag: 0.95** (Flaviova odluka, na osnovu čistog novi-vs-novi
presjeka).

## 5. Buduće opterećenje uz prag 0.95

Kad je najbolji root prevod od NOVOG modela (jedini aktivni ubuduće):
15.41% rečenica (5.898/38.286) ispod praga. Za poređenje: stari modeli
33.98%, NLLB 31.22%, sveukupno (mješano) 31.38%. Praktična posljedica:
refine bi se ubuduće pokretao na ~1 od 6-7 rečenica, ne na svakoj — red
veličine smanjenje troška koje je Flavio tražio od početka razgovora.

## 6. Flaviov prijedlog — tri fiksne faze umjesto random-a

Flavio: sa tri gotova prompta (refine/refine-lenient/refine-strict), tri
odvojene gated faze (redoslijed proizvoljan, jer gate gleda TRENUTNOG
pobjednika pa se posao sam sužava faza-po-faza) su dovoljne — "kad ovo
gledam, nismo morali ništa da mijenjamo."

Tri razjašnjenja prije izvršenja:
1. **NLLB isključen** iz refine (potvrđeno, konzistentno sa s143 odlukom —
   Flavio je samo opisivao opšti pipeline, ne predlagao NLLB u refine-u).
2. **Faze 2/3 ostaju netaknute** (istorijski par vezan za `refine` prompt);
   nove faze dobijaju svježe ID-ove (4/5/6), ne prepravljaju postojeće —
   Flavio potvrdio, brojevi u njegovom originalnom prijedlogu bili su samo
   primjer.
3. **Gate provjerava TRENUTNOG pobjednika**, ne originalni seed — potvrđeno
   kao namjeravano ponašanje (samo-sužavajući lijevak).

## 7. Implementacija — kod

**`bb_03_prevod.py`** (4 izmjene, verifikovane diff-om i `py_compile`):
- `get_seed_map()` prepisan — jedan upit na `v_pobjednici_full` vraća
  `(prevod, finalni_score)` umjesto ranijeg ručnog tro-tabelarnog JOIN-a
  koji je vraćao samo tekst.
- Nov CLI `--prag` (default `0.95`) — konfigurabilan, ne hardkodovan
  (isti obrazac kao `--temp`).
- Filter `seed_score < args.prag` primijenjen NA `todo` PRIJE poziva
  modela (štedi Ollama pozive, ne samo upis) — uz print liniju koja
  pokazuje koliko je preskočeno.
- Dva mjesta gdje se `seed_map[rid]` koristilo kao tekst ažurirana na
  `seed_map[rid][0]` (tuple raspakivanje).

## 8. Implementacija — baza

Tri nove faze, isti obrazac kao README "Kako pokrenuti NOVU FAZU":

| id | naziv | redoslijed | metod | a1 | a2 | a3 |
|----|-------|-----------|-------|----|----|----|
| 4 | refine-gated | 4 | self-refine | mistral-large-3:675b, glm-5.2 | 0.8 | refine |
| 5 | refine-lenient-gated | 5 | self-refine | mistral-large-3:675b, glm-5.2 | 0.8 | refine-lenient |
| 6 | refine-strict-gated | 6 | self-refine | mistral-large-3:675b, glm-5.2 | 0.8 | refine-strict |

Sve verifikovano SELECT-om nakon INSERT-a (id-ovi tačno 4/5/6, veze tačne).

## 9. Testiranje kroz cijeli lanac

**Test 1 — direktan `bb_03_prevod.py --faza 4`** na k22/hr, pozicije
105-115: 11 rečenica, gate propustio tačno 1 (pozicija 109, seed 0.9088),
preskočio 10. Ispravan rezultat na prvi pokušaj.

**Otkriven nusprodukt:** postojeća "provjera opsega" (s136) i
`health_check.py` 2b (`v_status_faza_model`) pretpostavljaju da SVAKA
rečenica u opsegu treba prevod — netačno za gated faze gdje je većina
namjerno preskočena. **Flaviova odluka: ostaviti kao poznatu razliku**
(kao postojećih 236 rupa), ne popravljati logiku brojanja danas.

**Bootstrap problem otkriven:** `bb_aktivni_modeli.py` (s142 dizajn) čita
SAMO istorijski korišćene (model,temp) parove iz `bb_prevodi_knjige`. Za
potpuno nove faze bez ijednog prevoda, vraća prazno → `run_faza.sh` petlja
se izvrši nula puta, tiho, bez greške, ispisuje "ZAVRŠENO" kao da je
uspjelo. Dokumentovano trajno u README-u (novi warning). Popravljeno
bootstrap pozivima: 5 direktnih `bb_03_prevod.py` poziva (glm za fazu 4;
oba modela za faze 5 i 6), isti mali opseg — `bb_aktivni_modeli.py` sad
tačno vraća oba modela za sve tri faze.

**Test 2 — pun `run_faza.sh --faza 4`** na istom opsegu (idempotentno —
pozicija 109 već prevedena): `bb_03` petlja ispravno prepoznala oba
modela, gate ispravno pokazao 0 novih kandidata (već urađeno); sudija
ocijenio 6 kandidata za s109 (3 glm + 3 mistral varijante preko faza);
`bb_04_pobjednik.py` upisao apsolutnog pobjednika (11 rečenica) ali
**PUKAO** na sljedećem koraku (fazni pobjednik →
`bb_prev_recenica_faza`) s `psycopg2.errors.UndefinedColumn: column
m.faza_id does not exist`.

**Pravi bug, ne nusprodukt gated faza:** `bb_04_pobjednik.py` je od s142
migracije čitao `m.faza_id`/`m.temperatura` sa `bb_modeli` — obje kolone
uklonjene u s142 Koraku 6 (bb_modeli postao čist a1 katalog). Nikad
testirano jer nijedan refine nije pokretan između s142 i ovog testa —
klasičan primjer s142-ove vlastite lekcije #5 ("plan koji kaže
'orkestratori se usklađuju' ne pokriva sve dodirne tačke").

**Popravka:** `pk.faza_id` (direktno na `bb_prevodi_knjige`, s142 kolona)
umjesto `m.faza_id`; `bb_temperature` join + `t.vrijednost DESC` umjesto
`m.temperatura DESC` za tie-break. Verifikovano diff-om, `py_compile`, i
živim ponovnim pokretanjem — `Upisano faza: 25`, bez greške.

**Verifikacija fazne tabele:** `bb_prev_recenica_faza` sadrži tačno po 1
red za svaku od tri nove faze (hr, pozicija 109) — potvrđuje da fazni
pobjednik ispravno prepoznaje nove faze.

**Finalni `health_check.py`:** sve zeleno osim očekivanog (git
uncommitted, buchenweb zaostaje s143 vs s140). 236 poznatih rupa
nepromijenjeno — nove gated faze ne dodaju šum jer gate dosljedno svodi
oba modela na isti mali broj završenih rečenica.

## 10. Dokumentacija

- **README.md:** nov trajan warning u sekciji "Kako pokrenuti NOVU FAZU" —
  potpuno nova faza + `run_faza.sh` bez bootstrapa = tihi no-op.
- **`docs/PLAN-KONFIGURACIJA.md`:** nova sekcija §4.7 dokumentuje cijeli
  preokret (provokacija → mjerenje → prag → arhitektura → bug fix).
  §4.1-§4.6 (originalni random dizajn) ostaju netaknuti kao istorijski
  trag rasuđivanja, s upozorenjem na vrhu da je preokrenuto. Header,
  status (§6) i footer ažurirani na v4.

---

## Odluke (Flavio)
- Prag za gated refine: **0.95**, na osnovu čistog novi-model-vs-novi-model
  presjeka (ne mješanog agregata).
- Dio B: tri fiksne gated faze (po jedna po postojećem promptu) umjesto
  random selekcije. Redoslijed faza proizvoljan.
- NLLB isključen iz refine-a (potvrđeno, ne nova odluka).
- Nove faze dobijaju svježe ID-ove (4/5/6), faze 2/3 ostaju netaknute.
- Nuspojava "opseg"/rupa brojanja za gated faze: ostaviti kao poznatu
  razliku, ne popravljati sada.
- Imena novih faza (`refine-gated`, `refine-lenient-gated`,
  `refine-strict-gated`) — Flavio odobrio kao odlična.

## Lekcije
1. **Provokacija utemeljena na sopstvenom iskustvu otkrila je pogrešnu
   premisu cijelog Dijela B.** GA mašinerija (mutacija, anti-elitizam,
   marginalna preferenca) rješava problem OGROMNOG prostora pretrage —
   sa fiksnim katalogom od 6 kombinacija, taj problem ne postoji. Prava
   dijagnoza došla je iz Flaviovog neposrednog inženjerskog iskustva
   ("6 minuta"), ne iz apstraktne analize.
2. **Sumnja na konfaund je bila opravdana i promijenila je broj (prag
   0.92→0.95), ne samo potvrdila postojeći zaključak.** "Ne vjerovati
   linearnom trendu bez provjere" (Flaviova berzanska analogija) je
   tačno ANALIZA.md pravilo primijenjeno uživo.
3. **Nusprodukt testiranja (bug u `bb_04_pobjednik.py`) pokazuje vrijednost
   stvarnog end-to-end testa nad pukom verifikacijom sheme.** s142 je
   testirao bazu pobjednika, ali fazni pobjednik nije bio stvarno
   vježban refine pozivom sve do ove sesije — praznina ostala nevidljiva
   mjesecima jer je uslov za njeno otkrivanje (refine run poslije s142)
   izostao.
4. **Bootstrap problem (`bb_aktivni_modeli.py` prazno za nove faze) je
   opasniji od greške koja puca — tih no-op koji izgleda kao uspjeh.**
   Vrijedi trajno dokumentovati ovakve tihe otkaze, ne samo popraviti ih
   jednom.
5. **X-Ray princip primijenjen na sopstveni plan-dokument:** stari dizajn
   (§4.1-§4.6) nije obrisan nego zadržan kao vidljiv trag rasuđivanja uz
   jasan pokazivač na novo stanje — proces ostaje transparentan, ne
   samo rezultat.

## Otvoreno / za sljedeću sesiju
- Gated faze (4/5/6) testirane samo na k22 (test knjiga), mali opseg
  (11 rečenica). Šire pokretanje (druge knjige, puni opseg) je Flaviova
  odluka kad ima resurse — Claude ne planira niti pokreće pipeline
  runove (s121 pravilo, i dalje važi).
- `health_check.py` "opseg"/rupa logika za gated faze ostaje netačna
  (namjerno, po Flaviovoj odluci) — revizija samo ako počne smetati.
- Export skripte (`bb_web_export.py`/`bb_xray_export.py`) nisu provjerene
  za nove faze — nisu ni bile u fokusu ove sesije (web ostaje odvojena
  odluka, kao i ranije).
- Git: i dalje raste `.bak` backlog (sad +4 nova `.bak_s144` fajla) —
  čišćenje odloženo kao i ranijih sesija.
- Formula rank selection (§1 ove sesije) zapisana ali neupotrijebljena —
  moguće da nikad neće ni trebati, s obzirom na napuštanje random dizajna.

---
*Flavio & Claude · Buchenberg · Sesija 144 · 19. jul 2026.*
