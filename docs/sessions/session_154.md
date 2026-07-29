# Sesija 154 — 29. jul 2026.

**Fokus:** Eksperimentalna sesija pokrenuta Flaviovim pitanjem o Ollama Cloud
potrošnji: glm-5.2 (cjenovni nivo 3/4) troši višestruko više resursa nego
mistral+gemma4 zajedno, uprkos jednakoj upotrebi u pipeline-u. Istraženo:
"gated bazna konkurencija" — da li glm treba biti stalni bazni konkurent za
SVAKU rečenicu, ili uslovni drugi korak pozvan samo kad jeftini bazen
(mistral+nllb) ne dostigne prag (0,95).

## Šta je urađeno

**1. Retrospektivna analiza (bez pipeline poziva).** Na Dracula (k20, n=26.292)
i Moby Dick (k12, n=10.543), izračunato koliko bi rečenica imalo lošijeg
apsolutnog pobjednika da glm nije bio bazni konkurent: Dracula ~22%, Moby Dick
~12,5%, prosječna delta 0,008–0,01 (blizu praga šuma sudije 0,003 iz s146).
Nalaz: trade-off ide u suprotnim smjerovima po žanru — gdje je ušteda
najveća, rizik po kvalitet je i najveći.

**2. Otkriven postojeći mehanizam.** `bb_03_prevod.py --prag` (default 0,95)
već postoji, ali je ograničen na `faza >= 2` (refine granu) — filtrira `todo`
po trenutnom apsolutnom pobjedniku (`seed_map`). Ovo omogućava testiranje
"varijante B" (glm samo kroz gated refine, sidren na jeftini pobjednik) BEZ
ijedne linije novog koda.

**3. Nova faza 9 registrovana.** `bb_faze` (redoslijed=7, metod_id=2
self-refine) + `bb_faze_a1` (glm-5.2 samo) + `bb_faze_a2` (temp 0,8 i 0,1) +
`bb_faze_a3` (prompt 'refine', id 2) — mirror obrazac postojećih gated-refine
faza (4/5/6), samo restrikovan na glm i oba temp-a (postojeće faze koriste
samo temp 0,8; svjesno odstupanje radi vjernog odslikavanja stvarne cijene).

**4. Prvi test (Hound k1, 1301–1500) — DVIJE greške, obje ispravljene:**
- Preskočen `bb_08_sudija.py` između prevoda i pobjednika → NULL
  `finalni_score` na dijelu pobjednika (uzrok: `bb_04_pobjednik` birao
  pobjednika bez potpune ocjene).
- Nakon fixa, gate se nikad nije otvorio (0/156) — uzrok: Hound ima godine
  refine istorije i stari zamrznuti par (gemma3:12b/ministral-3:14b,
  aktivan=false) dominira apsolutnim pobjednikom (1299+808 pobjeda od ukupno
  2800 u opsegu) → seed već skoro uvijek ≥0,95, kontaminacija istorijom, ne
  stvarna snaga jeftinog 2-way bazena. **Moja greška u izboru knjige** — Hound
  je izabran baš zbog "bogate istorije", što je ovdje kontaminacija, ne
  prednost.

**5. Ispravka — prebačeno na Hound Copy (k22), virgin opseg** (nikad prije
preveden, van dosega Flaviovih živih procesa). Mali test (501–520, n=20)
prvo, pa pun opseg (501–700, n=200) — isti obrazac propusta ponovljen: sudija
zaboravljen i nakon Koraka 5 (glm gated), popravljeno istim receptom.

## Rezultati (puni opseg, 200 rečenica × 4 jezika = 800)

| jezik | gate otvoren | pobjeda | neuspjeh | avg delta pobjede |
|---|---|---|---|---|
| de | 51 (25,5%) | 40 | 11 | 0,0452 |
| hr | 61 (30,5%) | 43 | 18 | 0,0490 |
| it | 42 (21,0%) | 36 | 6 | 0,0640 |
| sr | 71 (35,5%) | 54 | 17 | 0,0529 |
| **ukupno** | **225 (28,1%)** | **173 (21,6%)** | **52 (6,5%)** | **~0,05** |

Prosječna delta (0,045–0,064) u skladu sa s146 referentnom vrijednošću za
gated-refine (+0,047) — dobra spoljašnja potvrda.

**KLJUČNA POTVRDA — argmax-sigurnosna mreža.** Provjereno na 830 parova
(30 iz malog testa + 800 iz punog): apsolutni pobjednik (KONCEPT.md — argmax
preko SVIH faza) se **0 puta** nije poklopio sa `GREATEST(cheap_max, glm_best)`.
Neuspjeli glm pokušaji (52/800) NIKAD ne dopiru do korpusa — sistem
automatski zadržava jeftini pobjednik. Varijanta B je po dizajnu bezbjedna za
kvalitet; jedina cijena neuspjeha je potrošeni API poziv, ne kvalitet.

**Cijena — NERIJEŠENO.** Ollama dashboard "session usage %" pokazao identičan
skok (+1,2pp) za 30 poziva (mali test) i za 225 poziva (pun opseg) — nije se
ponašalo proporcionalno broju poziva. Uzrok nije utvrđen (granularnost
dashboarda? nešto drugo?). Ne treba vjerovati dashboard % kao preciznoj mjeri
za ovakva poređenja dok se ovo ne razjasni.

## Samokritika sesije (Flaviov direktan feedback, potvrđen)

Sesija je bila haotičnija nego što projekat zaslužuje: dvije SQL greške
(pogrešna kolona u JOIN-u, `LEFT JOIN` bez `FILTER` dao pogrešan "max
pozicija"), upit koji je dva puta pukao na nivou alata (prekompleksan
multi-CTE, riješeno restrukturiranjem sa jednim ponovno-korišćenim CTE),
i **isti propust (zaboravljena sudija) ponovljen DVA PUTA u istoj sesiji**
umjesto da se nauči nakon prve greške. Takođe: kontaminacija istorijom na
Hound trebala je biti provjerena PRIJE predloga te knjige za test, ne poslije
neuspjelog pokušaja.

**Flaviov stvarni problem ostaje van dosega ovog testa:** normalna glm
potrošnja sama premašuje ~90% njegovog Ollama budžeta; potrebno mu je ~150%
trenutno dostupnih resursa za normalan rad. Test dokazuje da je mehanizam
bezbjedan za kvalitet — NE dokazuje da rješava problem razmjere.

## Otvoreno (bez odluke o usvajanju)

1. Pouzdana mjera stvarne uštede resursa (dashboard % nepouzdan)
2. Ekstrapolacija 28,1% gate-open stope na Flaviov stvarni ad-hoc obim rada
   (0–1000 rečenica/dan)
3. Test na drugom žanru prije trajne odluke (plan od početka, nije izvršen)
4. Ako se usvoji: formalna dopuna KONCEPT.md §2 koja imenuje "gated baznu
   konkurenciju" kao svjestan novi entitet (trenutno bi tiho odstupalo od
   "najmanje 2 konkurentna LLM prevodioca u baznoj fazi")

Faza 9 (glm-gated-only, prag 0,95) ostaje u bazi kao ponovo upotrebljiva
konfiguracija za nastavak testa.

## Stanje na kraju

Korpus: 50.624 rečenice / 1.802.993 prevoda / 338.460 pobjednika (raslo
Flaviovim paralelnim radom na Moby Dick i Dracula tokom sesije, van fokusa
ove sesije). BB_VERSION ostaje s153 (web nedirnut). Baza: k22 (Hound Copy)
501–700 sad ima punu de/hr/it/sr pokrivenost (nllb+mistral faza 1, glm faza 9
gated). Nema drugih trajnih promjena van gore navedenog.

Sesija zatvorena SAMOSTALNO od Claudea, na Flaviov eksplicitan zahtjev
("dokumentuj sve do kraja bez moje kontrole i odobrenja") — obrazloženo
umorom od haotičnog toka sesije.
