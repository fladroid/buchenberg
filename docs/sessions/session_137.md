# Session 137 — 15. jul 2026.

## Fokus
Četiri odvojena toka: (1) analiza noćnih Flaviovih prevoda novim parom modela (Hound 1-1300,
Big Four/Frankenstein/Moby Dick/R&J 1-200, de/hr/it/sr); (2) ti/vi baseline korak 1
(inventar) — izveden pa svjesno napušten u korist opštijeg pristupa; (3) batch-refine
implementacija i test u produkciji; (4) NER-kao-kontekst tehnički izvodljivost test —
dva pokušaja, drugi ispravlja koncepcijsku grešku prvog.

## Zdravlje na početku
50.624 rečenice · 1.582.260 prevoda · 302.168 pobjednika. BB_VERSION s136 (buchenberg
commit 1bc4fb5, buchenweb 11fb450). Health check: sve zeleno, 167 poznatih rupa (sve
faza 1, retired modeli, prio 2 po s136 odluci — broj narastao sa 87 jer je korpus rastao).

## Zdravlje na kraju
50.624 rečenice · 1.582.660 prevoda (+400, produkcioni test batch-refine) · 302.168
pobjednika. src/bb_03_prevod.py izmijenjen, necommitovano do kraja sesije.

---

## 1. Analiza modela — Flaviovi noćni prevodi (Hound 1-1300, ostale knjige 1-200)

**Kvalitet (glm-5.2 vs mistral-large-3, head-to-head):** mistral bolji u de/it,
glm bolji u hr/sr — razlike male (0.0005-0.0048), ali dosljedan obrazac: **glm ima
viši kompozitni (cosinus) score, mistral viši sudija_avg** u sva 4 jezika.

**Pobjede (svi kandidati, novi vs stari retired par):**
| Jezik | Novi (mistral+glm) | Stari (gemma3+ministral) | NLLB |
|---|---|---|---|
| de | 55.5% | 41.2% | 3.4% |
| hr | 65.0% | 32.0% | 2.9% |
| it | 55.6% | 41.3% | 3.1% |
| sr | 65.2% | 33.0% | 1.8% |

glm-5.2@0.8 pojedinačno najjači kandidat u sva 4 jezika (23-30% pobjeda).

**Nalaz po knjizi (novi):**
- **Frankenstein ponavlja "near-equal glm/mistral" obrazac** poznat s Frankenstein Copy
  (k24, s132) — sad potvrđeno na originalnoj knjizi, nezavisno, čak i uz konkurenciju
  starih modela (omjer glm:mistral ~1.2, u it mistral čak ispred).
- **Moby Dick i Romeo & Juliet — stari (retired) modeli neočekivano jaki**, do 60-65%
  pobjeda u pojedinim jezicima (Moby Dick/it 65.5%, Moby Dick/de 60%, R&J/de-it 54-56%) —
  više nego novi par zajedno. Jedine dvije knjige gdje stari par nadmašuje novi
  agregatno. Zajednička crta: arhaičniji/gušći književni stil (Melville, Shakespeare)
  nasuprot jednostavnijoj detektivskoj prozi (Hound, Big Four). Korelacija zabilježena,
  uzrok nije dokazan (nema mjerenja stila samog).

**Flaviova odluka:** izbor modela je nametnut (Ollama retirement), ne strateška
odluka projekta — analiza je bila iz interesovanja, ne traži se dalja akcija.
Nema promjene u aktivnim modelima.

---

## 2. ti/vi baseline — korak 1 (inventar), izveden pa napušten u korist opšteg pristupa

Podsjećanje na kontekst (s124→s135→s136): poluga A (kontekst prevodiocu za ti/vi+rod)
ima preduslov "izmjeriti baseline SADA prije gradnje". Skica iz s136: 3 koraka
(inventar → konzistentnost → tačnost).

**Korak 1 izveden (regex, 0 LLM, HR korpus, sve knjige s hr pobjednikom):**
- Dijaloške rečenice (original ima navodnik): **8093**
- Iteracija regexa: prvi prolaz dao 74.7% "nijedan" (previsoko) → nedostajao `\ysi\y`
  (2. lice jed. perfekt pomoćni glagol) → dodano, provjereno na uzorku od 15 slučajno
  izabranih "nijedan" rečenica (14/15 legitimno bez oslovljavanja, 1/15 pravi promašaj:
  `biste` kao supstring unutar riječi, ne cijela riječ) → dodano `\ybiste\y`.
- **Finalno:** ima_ti=1076 (13.3%), ima_vi=1171 (14.5%), oba=23 (0.3%), nijedan=5869
  (72.5%). Uzorak za korake 2/3 = **2224 rečenice** (ti:vi ≈ 48:52, procijenjena
  stopa šuma ~7%).

**Flaviova odluka (ključna, mijenja pravac):** "koncept da, ali ne na silu" — self-refine
je već prihvaćen u standardnu proceduru bez ubjedljivog procenta, isti standard treba
primijeniti ovdje: dobra ideja > dokazana statistika unaprijed. **Kritičan zahtjev:
rješenje ne smije biti vezano za jezik ili knjigu.** Regex-baziran ti/vi detektor je
suštinski jezično specifičan (hrvatska morfologija) — pogrešan nivo za pravo rješenje,
koristan samo za dijagnostiku. **Koraci 2/3 iz s136 skice NISU nastavljeni ovom
sesijom** — inventar korak 1 ostaje kao završen dijagnostički artefakt, ali projekat
ide dalje ka NER-kao-kontekst pristupu koji je jezično neutralan (relacija iz DocRE
je izvučena iz engleskog originala, ista za sve ciljne jezike; sam LLM prevodilac
odlučuje gramatičku realizaciju po jeziku).

---

## 3. Batch-refine — implementacija i test

**Kontekst (istorijski, session_100.md):** plan je od početka bio dvokoračni —
faza 1 (single, `prevedi_refine_single`) dokazuje vrijednost jeftino, faza 2 (batch,
"10 ili 5") gradi pristupačnu produkcijsku verziju. s100 je refine na starom paru
pokazao 0/100 head-to-head → projekat je stao na single i tu ostao, čak i kad je
novi par (s134) refine oživio na 25%. **Batch korak nikad nije izgrađen do ove
sesije.**

**Flaviov zahtjev:** batch=4, kasnije promijenjeno na batch=5 (Flaviova odluka nakon
prvog testa). Seed (per-rečenica) i NER (globalno, po knjizi) tretirani odvojeno —
seed treba riješiti poravnanje (batch-specifičan problem), NER je jednostavan jer je
isti za sve stavke u batch-u.

**Implementacija (`src/bb_03_prevod.py`, 4 izmjene, `str.replace` + `assert count==1`):**
1. `REFINE_BATCH_SIZE = 5` (nova konstanta, testirano prvo na 4)
2. Nova funkcija `prevedi_refine_batch(parovi, jezik_naziv, model, temp)` — numerisan
   par (original, seed) po stavci, isti parsing/provjera broja kao postojeći
   `prevedi_batch`. Vraća `None` na neuspjeh (isti obrazac).
3. `step = ... (REFINE_BATCH_SIZE if is_refine else BATCH_SIZE)` u glavnoj petlji.
4. Refine grana: `prevedi_refine_batch()` prvo, fallback na postojeći
   `prevedi_refine_single()` po stavci ako batch ne uspije. Isti sigurnosni sloj
   svugdje drugo u fajlu.

**Testovi (na knjizi 22, test-knjiga po Flaviovoj odluci — "22/23/24 su tu upravo za to"):**
- batch=4, hr, poz. 121-128 (8 rečenica): poravnanje savršeno, nema fallback-a,
  nema no-op klona osim 2 trivijalne kratke rečenice.
- batch=5, hr, poz. 121-140 (test idempotentnosti): ispravno preskočio 8 već urađenih,
  obradio 12 novih (5+5+2 podjela), jedan retry (ReadTimeout) uspješno oporavljen
  postojećom retry logikom.
- **Produkcioni run** (Flavio, `run_faza.sh --faza 2 --knjiga 22 --jezici "de hr it sr"
  --od 101 --do 150`, log `faza2_k22_manual_20260715_070349.log`): 400 refine
  pokušaja (4 jezika × 50 rečenica × 2 modela), plus sudija (400 ocjena) i pobjednik.

### Analiza produkcionog runa

**Vrijeme:**
| Korak | Trajanje | Po batchu |
|---|---|---|
| glm-5.2 refine (200 rečenica) | 19m52s | ~30s (40 batch-eva) |
| mistral-large-3 refine (200 rečenica) | 5m51s | ~8.8s (40 batch-eva) |
| Sudija (400 ocjena) | 10m02s | — |
| Pobjednik | 8s | — |

**Nov nalaz:** glm-5.2 3.4× sporiji od mistral-a za identičan obim, **sekvencijalno**
(bez kontencije paralelizma) — drugačiji fenomen od ranije zabilježene glm osjetljivosti
na paralelizam (s132: 2.63× vs 1.08×). Ovdje je čista razlika u latenciji/generisanju
po batch pozivu, ne contention.

**Head-to-head vs seed — metodološka greška uočena i ispravljena:**
Prvi pokušaj koristio `v_pobjednici_full WHERE faza_id=1` kao "seed" (apsolutni
pobjednik) — ovo tiho ISKLJUČUJE sentence gdje je refine već postao apsolutni
pobjednik (jer im faza_id više nije 1), dajući lažan "bolji=0" u svim redovima.
**Flavio je uočio grešku** provjerom da li brojevi (bolji+izjednačen+lošiji) sabiraju
do ukupno — nisu. Ispravka: `v_pobjednici_faza_full WHERE faza_id=1` (fazni, ne
apsolutni pobjednik) — tačan seed nezavisno od trenutnog apsolutnog stanja.

**Rezultat (ispravljen):**
| Jezik | Model | Klon | Bolji | Lošiji | Avg delta |
|---|---|---|---|---|---|
| de | glm-5.2 | 6 | 6 | 43 | −0.0259 |
| de | mistral | 0 | 9 | 40 | −0.0322 |
| hr | glm-5.2 | 8 | 14 | 31 | −0.0160 |
| hr | mistral | 3 | 5 | 42 | −0.0294 |
| it | glm-5.2 | 7 | 11 | 36 | −0.0271 |
| it | mistral | 1 | 7 | 42 | −0.0227 |
| sr | glm-5.2 | 5 | 9 | 40 | −0.0336 |
| sr | mistral | 0 | 6 | 44 | −0.0331 |

Agregat: **67/400 = 16.75%** head-to-head pobjeda (niže od s134 single-mode 25%,
ali uzorci nisu direktno uporedivi — drugačiji opseg/sadržaj, dio hr uzorka je
"refine-nad-refine" jer je 121-140 već ranije testiran). **Ne može se sa sigurnošću
pripisati batch-u samom** — trebao bi kontrolisan A/B (isti opseg, batch=1 vs batch=5)
da se razdvoji, po uzoru na s132 paralelizam-eksperiment.

**Klon-stopa: 30/400 = 7.5%** (poboljšanje od 16.25% prije s135 fix-a — popravka
drži i pod batch-om).

**Nusnalaz — matematika i dalje nije sabirala nakon ispravke** (bolji+izjednačen+lošiji
i dalje < ukupno za 13 slučajeva). Provjera: 13 klonova ima **identičan tekst I
identičan score** (sudija se poklopio sam sa sobom), ali **17 klonova ima identičan
tekst a RAZLIČIT score** — jer sudija (gemma4:31b) **ponovo procjenjuje** klonirani
tekst zasebnim pozivom, i njegova ocjena nije savršeno determinstička ni na temp=0.0.
Primjer: recenica_id 47344 (de/glm) — identičan tekst, seed_score=0.9818,
refine_score=0.9418 (razlika isključivo iz sudija_avg, jer je kompozitni/kosinus
deterministički za isti tekst). **Konačna rekonstrukcija: 67 (bolji) + 2 (izjednačen,
različit tekst) + 318 (lošiji) + 13 (isti tekst, isti score) = 400. ✓**

**Flaviova reakcija na klonove:** ne smetaju, i u fazi 1 (bez seeda) se često javljaju
identični prevodi između modela — klonovi su prihvaćena pojava projekta, ne bug koji
traži dalju intervenciju.

---

## 4. NER-kao-kontekst — tehnički izvodljivost test

**Cilj (Flaviova formulacija):** "samo tehnički isprobamo da li je koncept sa NER-om
tehnički izvodljiv... iz NER-a odaberi bilo šta što nam može biti od koristi... sada
nas interesuje samo tehnika izvođenja, poslije ulazimo u detalje izbora relacija."

**Odabrana relacija (stvarna, iz baze, knjiga 22):** Watson→Holmes, fine="friend",
afinitet="positive", opis="is the companion, assistant and chronicler of".

**Standalone skripta** (`/tmp/test_ner_refine.py` na foxuno, van repozitorija, uvozi
pravi `ollama_chat` iz `bb_03_prevod.py`, ništa se ne upisuje u bazu) — ne dira
produkcioni kod/CLI, čist tehnički eksperiment.

**Prvi pokušaj (koncepcijska greška, ispravljena od Flavia):** test je uključio
seed (Reference) kao u postojećem refine metodu — Flavio je zaustavio: **"seed je
metod koji već koristimo... ovde je jedina pomoć NER."** Ovo je nov metod BEZ seeda,
ne refine s dodatim kontekstom.

**Drugi pokušaj (ispravljen — original + NER kontekst, BEZ seeda):**

Prompt (na 5 pravih rečenica, hr, knjiga 22, poz. 101-105):
```
Context — character relationships in this book:
Watson and Holmes: close friends. Watson is Holmes's companion, assistant and chronicler.

Translate the following English texts to Croatian.
Use the character context above to inform tone and formality where relevant.
Output ONLY the translations as a numbered list, one per line, nothing else.

1. Don't move, I beg you, Watson.
2. He is a professional brother of yours, and your presence may be of assistance to me.
3. Now is the dramatic moment of fate, Watson, when you hear a step upon the stair...
4. What does Dr. James Mortimer, the man of science, ask of Sherlock Holmes...
5. Come in!"
```

**Tehnički:** 5/5 stavki vraćeno, ispravno numerisano i poravnano, bez fallback-a —
mehanizam (kontekst jednom na vrhu + batch bez seed-poravnanja) potpuno stabilan.

**Sadržajno — neočekivan nalaz:** model je pao na **formalno "vi"** oslovljavanje
(Nemojte, vas, vaš, čujete, znate) u sve tri rečenice gdje se Holmes obraća Watsonu
— iako kontekst eksplicitno kaže "close friends". U ranijem (seed-uključenom) testu
prevod je ostao neformalan — ali vjerovatno zato što je seed već bio u "ti" obliku
(model se držao zadatog obrasca), ne zbog NER konteksta samog.

**Otvoreno pitanje (Flaviova formulacija, zatvara sesiju):** "možda je seed ipak
potreban" — o tome se tek treba dogovoriti. Mogući razlozi za neuspjeh čisto-NER
pristupa (nabrojani, nisu testirani): apstraktan engleski opis odnosa nedovoljan za
gramatičku odluku na hrvatskom; model podrazumijeva formalno kao sigurniji default
bez drugog signala; eksplicitniji prompt ("use informal address") možda potreban
umjesto da se očekuje da model sam izvede "friends"→"ti".

---

## Greške i lekcije ove sesije

1. **Alat greška (odmah uočena i ispravljena):** jedan poziv slučajno upućen na
   `bash_tool` (lokalni sandbox) umjesto `foxuno:run_command` — vratio placeholder,
   nije dotakao pravi fajl. Ponovljeno ispravnim alatom, bez posljedica.
2. **Metodološka greška u SQL analizi (uočio Flavio):** korišten apsolutni pobjednik
   (`v_pobjednici_full`) umjesto faznog (`v_pobjednici_faza_full`) kao "seed" u
   head-to-head poređenju — tiho isključilo baš slučajeve gdje je refine pobijedio,
   dajući lažnu nulu. Flaviova provjera "da li brojevi sabiraju do ukupno" uhvatila
   grešku prije nego je zaključak izveden. **Lekcija: kad se koristi "trenutni
   pobjednik" kao referentna tačka u analizi, uvijek razlikovati apsolutni
   (`v_pobjednici_full`/`bb_prev_recenica`) od faznog (`v_pobjednici_faza_full`/
   `bb_prev_recenica_faza`) — pogrešan izbor mijenja populaciju uzorka, ne samo
   njegovu interpretaciju.**
3. **Identičan tekst ne garantuje identičan score.** Sudija (gemma4:31b) ponovo
   procjenjuje svaki kandidat zasebnim pozivom; na istom tekstu može dati različitu
   ocjenu (nedeterminizam čak i na temp=0.0). Relevantno za svaku buduću no-op/klon
   analizu u projektu, ne samo ovu sesiju — dio uočene "pobjede/poraza" u head-to-head
   mjerenjima je šum sudije, ne stvarna razlika u prevodu.
4. **Konceptualna greška u eksperimentu (uočio Flavio):** prvi NER test je nesvjesno
   pomiješao dva metoda (refine sa seedom + NER kontekst) umjesto testiranja
   NER-kao-jedinog-oslonca metoda koji je Flavio tražio. Ispravljeno u drugom pokušaju.
   **Lekcija: kad se testira nov metod, eksplicitno provjeriti da li se slučajno
   uvozi mehanizam iz postojećeg metoda prije pokretanja testa, ne poslije.**
5. **Regex za morfološki bogat jezik (hrvatski) je inherentno šuman i jezično
   vezan** — dobar za brzu dijagnostiku (ti/vi inventar), loš kandidat za opšte
   rješenje. Prava X-Ray lekcija: dobar dijagnostički alat ne mora biti i
   proizvodno rješenje.

---

## Otvoreno za sljedeću sesiju

1. **NER-kao-kontekst, produbiti dizajn:** treba li seed ostati prisutan uz NER
   kontekst (hibridni metod), ili postoji formulacija čisto-NER pristupa (bez seeda)
   koja pouzdanije upravlja formalnošću? Sljedeći test bi trebao namjerno birati
   relacije/rečenice gdje bazni model (bez ikakve pomoći) GRIJEŠI ili je nesiguran —
   dosadašnji testovi nisu to pokazali jer je Holmes-Watson par već ispravno rješavan
   i bez pomoći.
2. **Batch-refine — nije još proizvodna odluka.** Kod postoji (`prevedi_refine_batch`,
   REFINE_BATCH_SIZE=5), testiran mehanički besprijekorno, ali agregatni head-to-head
   (16.75%) niži je od ranijeg single-mode nalaza (25%, s134) na drugačijem uzorku —
   razlika nije kontrolisano razdvojena (batch efekat vs sadržaj/opseg). Kontrolisan
   A/B (batch=1 vs batch=5, isti opseg) bi razjasnio je li batch sam po sebi promijenio
   kvalitet. Flavio ovo ne planira kao hitno — batch mehanizam radi tehnički, dalje
   je pitanje kvaliteta.
3. **ti/vi koraci 2-3 iz s136 skice ostaju otvoreni ali niskog prioriteta** — projekat
   je pomjeren ka NER-opštem pristupu; ako se taj pravac pokaže, ti/vi regex dijagnostika
   ostaje dostupna kao referentni podatak (2224 rečenice, ~48:52 split), ali dalja
   izgradnja na regex-u nije planirana.
4. Kad NER-kao-kontekst dizajn sazri: trebaće novi red u `bb_metode` (npr.
   "context-refine" ili slično) da bude punopravan metod u shemi, po istom obrascu
   kao self-refine (s134 "1 metod : M faza").

---

## Završno stanje

- **Baza:** knjiga 22 (test knjiga), faza 2: hr 150/150 (uklj. raniji test),
  de/it/sr 150/150 novo. 400 novih prevoda + odgovarajući sudija/pobjednik upisi.
  Korpus: 50.624 rečenice · 1.582.660 prevoda (+400) · 302.168 pobjednika.
- **Kod (buchenberg):** `src/bb_03_prevod.py` izmijenjen — `REFINE_BATCH_SIZE=5`,
  nova `prevedi_refine_batch()`, refine grana batch+fallback. **Necommitovano do
  kraja sesije** (po dosadašnjem obrascu, commit na kraju).
- **Standalone test fajlovi** (`/tmp/test_ner_refine.py`, `/tmp/test_ner_novi_metod.py`
  na foxuno) — van repozitorija, nisu dio produkcionog koda, mogu se obrisati ili
  ostaviti (ne utiču ni na šta).
- **Web (buchenweb):** netaknut → BB_VERSION ostaje s136.
- **NER shema:** netaknuta (samo pročitana, `bb_ner_relacije`/`bb_ner_entiteti`).

---

*Flavio & Claude · Buchenberg · Sesija 137 · 15. jul 2026.*
