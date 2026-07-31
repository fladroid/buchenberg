# Sesija 155 — 31. jul 2026.

**Fokus:** Analiza Ollama Cloud potrošnje (glm-5.2 disproporcionalna cijena) na osnovu Flaviovih stvarnih podataka + koncepcijski dizajn i prva implementacija "gated root" arhitekture (sužen root bez glm-a + gated glm drugi krug) — mehanizam RADI kraj-do-kraja, ALI otkriven i NEISPRAVLJEN bug: gated glm prolaz ne radi ono što je trebalo (šalje seed/referencu modelu iako je registrovan bez pivota). Sesija zatvorena samostalno na Flaviov eksplicitan zahtjev (odsutan od PC-a).

---

## Dio 1 — Analiza Ollama Cloud troškova

Flavio je prezentovao 48h posla: prevod knjige 12 (Moby Dick) na de/hr/it/sr,
po-jeziku paralelizam (4 procesa istovremeno, isti obrazac kao ranije runove),
3600 rečenica × 4 jezika = 14.400 rečenica-jezik parova. Sedmična Ollama Cloud
potrošnja skočila sa 32,5% na 92,9% (delta 60,4%) — čist, izolovan uzorak (samo
taj rad, cijeli sedmični prozor, potvrđeno od Flavija).

**Pozadina koju je Flavio objasnio:** Ollama Cloud ima dva limita (5-satni i
sedmični, faktor uticaja ~0,18 između njih, izmjeren empirijski od strane
Flavija kroz ručno praćenje — Ollama nema API za potrošnju). Modeli imaju
deklarisanu "klasu" 1-4 (gemma=1, mistral=2, glm=3 po Flaviovom dashboardu),
ali stvarna potrošnja ne prati tu klasu — glm subjektivno troši ~10× više od
gemma+mistral zajedno, iako je klasa samo 1 stepenik viša od mistrala.

**Istraženo (web search) i potvrđeno iz tri nezavisna izvora:**
1. Ollama Cloud naplaćuje po **GPU-vremenu (trajanju zahtjeva)**, ne po broju
   tokena ili fiksnoj klasi (ollama.com/pricing, zvanično).
2. Arhitektura NE objašnjava razliku — glm-5.2 (~744B total / ~40B aktivnih,
   MoE) i mistral-large-3:675b (~675B total / ~41B aktivnih, MoE) su praktično
   identični po računu-po-tokenu.
3. **Ollamin vlastiti library page** (ollama.com/library/.../tags) etiketira
   glm-5.2:cloud kao **"High Usage"**, dok su i mistral-large-3:675b-cloud i
   gemma4:31b-cloud oba **"Medium Usage"** — nezavisna, javna potvrda da glm
   ide u viši razred potrošnje.
4. **Dokumentovan bag specifično za glm-5.2:cloud na Ollaminom backend-u**
   (GitHub issues ollama/ollama #16779 i #17091, potonji aktivan prije 3
   sedmice): pozivi traju 10-75+ sekundi naspram <2s za uporediv cloud model
   (kimi-k2.6) na ISTOJ Ollama instanci; isti model kroz drugi gateway radi
   normalno — sugeriše da je problem u Ollaminom posredovanju/proxy-ju ka
   Z.ai-jevoj infrastrukturi, ne u samom modelu.
5. Ovo se poklapa sa projektovim vlastitim ranijim mjerenjima: s137 (glm 3,4×
   sporiji od mistrala sekvencijalno) i s132 (glm 2,63× sporiji pod
   paralelizmom naspram mistralovog 1,08×).

**Zaključak (sinteza, ne dokaz sa sigurnošću):** ako je naplata GPU-vremenom, a
glm-5.2 ima nezavisno dokumentovan, ponovljiv problem latencije specifično na
Ollaminom backend-u, to objašnjava zašto slični brojevi zahtjeva (Flaviov
dashboard: mistral 5470 vs glm 4714 ovu sedmicu) proizvode nesrazmjernu
potrošnju. Flaviov paralelni 4-jezični obrazac rada dodatno pogoršava efekat,
jer glm pod kontencijom usporava mnogo više od mistrala.

**Flaviova odluka:** ograničiti glm na uslovni drugi korak (gated), pozvan
samo kad jeftini bazen (mistral+nllb) ne dostigne prag — princip: ne
pokušavati predvidjeti/optimizovati nepredvidljivu, tuđe-kontrolisanu cijenu,
nego minimizovati izloženost njoj. Isti princip važi za bilo koji budući
model čija stvarna cijena ne odgovara deklarisanoj.

---

## Dio 2 — Dizajn "gated root" arhitekture

Kroz nekoliko rundi razjašnjavanja (Flavio postavljao ideju, Claude tražio
konkretizaciju, Flavio precizirao), stigli do jasnog dizajna:

**Trenutni root (faza 1):** glm (2 temp) + mistral (2 temp) + nllb (1 temp) →
sudija → pobjednik. Sve rade istovremeno, glm uvijek uključen.

**Novi/dodatni root koji Flavio želi (za buduće, po volji — stari ostaje
dostupan):**
1. Prevod: mistral (2 temp) + nllb (1 temp) → sudija → pobjednik
2. Ako pobjednik < 0,95 → prevod: glm (2 temp) → sudija → pobjednik (argmax
   preko proširenog bazena)

**Ključne konceptualne odluke usput (Flaviove, potvrđene):**
- Nije bitno da li je ovo "nova" ili "stara" faza po broju — bitno je da NEMA
  pivota (referentnog/seed prevoda) u koraku 1-3, za razliku od svih
  dosadašnjih refine faza (2/3/4/5/6/9) koje su UVIJEK anchored mutation nad
  postojećim pobjednikom.
- Root (metod_id=1, "base") je PO DEFINICIJI bez pivota — root-invarijanta u
  shemi ("base ide tačno jednom") se ne krši jer korak 1-3 ostaje unutar
  POSTOJEĆE faze 1 (samo privremeno suženog a1 skupa), ne nova faza tipa root.
- Korak 4-7 (gated glm) NIJE isto što i faza 9 (postojeća, iz s154) — faza 9
  koristi `refine` prompt (SA pivotom/referencom), Flavio je htio glm da
  prevodi ORIGINAL nezavisno, ne da ispravlja mistralov prevod.
- Rezultat trebao biti: nova self-refine faza (isti recept kao faza 9 — dva
  koraka registracije) ali zakačena na **`base`** prompt (bb_promptovi id=1)
  umjesto na `refine` prompt — bez ijedne linije novog koda, "samo drugi
  izbor iz postojećeg kataloga".
- **Claude je pogrešno tvrdio** (prije implementacije) da pivot zavisi
  isključivo od toga da li prompt template sadrži `{seed}` placeholder — ovo
  se pokazalo netačno za batch-mode kod (vidi Dio 4, bug).

**Krajnje stanje (Flavio, buduće, van ovog testa):** treba mali novi wrapper
skript (npr. `run_root_gated.sh`, ~10-ak linija bash-a) koji interno radi
toggle glm off → root → toggle glm on → gated faza, kao JEDAN poziv za
Flavija (isti UX kao postojeći `run_pipeline.sh`), bez ručnog SQL-a. NIJE
napravljen ovu sesiju — samo dogovoren koncept; ručni SQL toggle korišten za
test.

---

## Dio 3 — Implementacija i test (uspješan mehanički, do bug-a u Dijelu 4)

Test opseg: k22 (Hound Copy), core-4 (de/hr/it/sr), pozicije **701-740** (40
rečenica, virgin — iznad s154-testa koji je zauzeo 501-700).

**Koraci izvršeni (svaki uz Flaviov OK):**

1. `UPDATE bb_faze_a1 SET aktivan=false WHERE faza_id=1 AND model_id=20;`
   (glm ugašen za fazu 1)
2. `run_faza.sh --faza 1 --knjiga 22 --jezici "de hr it sr" --od 701 --do 740`
   — **uspješno, 17m32s, bez grešaka.** 2-way root (mistral+nllb), 160
   rečenica-jezik parova, sudija ispravno ocijenio sve (nema NULL — izbjegnuta
   s154 greška).
3. `UPDATE bb_faze_a1 SET aktivan=true WHERE faza_id=1 AND model_id=20;`
   (glm vraćen za fazu 1 — standardno 3-way stanje za buduće ručne runove)
4. Registrovana **nova faza 10** ("root-gated-glm-base", redoslijed=8,
   metod_id=2 self-refine):
   - `bb_faze_a1`: model_id=20 (glm-5.2), aktivan=true
   - `bb_faze_a2`: temperatura_id 1 (0,8) i 4 (0,1), oba aktivna
   - `bb_faze_a3`: prompt_id=1 (**base**), aktivan=true
5. **Greška uočena i ispravljena:** `run_faza.sh --prag 0.95` puklo
   ("Nepoznat argument: --prag") — `run_faza.sh` ne podržava taj flag. Nije
   ni potrebno: `bb_03_prevod.py --prag` ima default 0,95 i automatski se
   aktivira za svaku fazu ≥2 (`is_refine = args.faza >= 2`, linija 358).
   Ispravljena komanda bez `--prag`.
6. `run_faza.sh --faza 10 --knjiga 22 --jezici "de hr it sr" --od 701 --do 740`
   — **uspješno, 5m08s, bez grešaka.** Gate ispravno filtrirao 40/160 (25,0%)
   rečenica ispod praga 0,95 — brojevi po jeziku (de=14, hr=7, it=9, sr=10)
   se poklapaju 1:1 sa ručnim SQL provjerama urađenim između koraka 2 i 4.
   Slaže se sa ranijim gate-open stopama (s146: 29,2%, s154: 28,1%).
7. Argmax pobjednik ispravno birao preko CIJELOG bazena (mistral + nllb +
   gated glm zajedno) — potvrđeni pobjednici glm-a na nekoliko pozicija
   (npr. s717 u sve 4 jezika).

**Zaključak Dijela 3 (prije otkrića bug-a):** mehanizam izgledao potpuno
ispravan — nula novog koda, samo katalog + postojeći alati, tačno kako je
planirano.

---

## Dio 4 — KRITIČAN BUG, otkriven, NEISPRAVLJEN (Flaviov ulov)

Nakon prikaza log izlaza, Flavio je primijetio liniju:

```
── Jezik: it (Italian), prevodi_knjige_id=16197 ──
  Preostalo: 40 rečenica
  Refine: 40 sa seedom -> 40; ispod praga 0.95: 9 (preskoceno 31)
```

i postavio pitanje: "Da li je ovo samo komentar? Nema seeda/pivot prevoda?"

**Odgovor, provjeren u kodu — NE, nije samo komentar. Seed SE ŠALJE modelu,
uprkos `base` promptu.**

Uzrok: `bb_03_prevod.py` grananje (linija ~421) glasi:
```python
if is_nllb: ...
elif is_refine: ...        # is_refine = args.faza >= 2 — SAMO broj faze!
else: prevedi_batch(...)   # čist prevod bez reference — SAMO za fazu 1
```

`is_refine` zavisi ISKLJUČIVO od broja faze (`≥2`), ne od toga koji je prompt
zakačen preko `bb_faze_a3`. Funkcija `prevedi_refine_batch()` (koja se poziva
u `elif is_refine` grani) **hardkoduje referencu direktno u tekst poruke**,
nezavisno od sadržaja prompt template-a iz baze:

```python
def prevedi_refine_batch(parovi, jezik_naziv, model, temp, tpl):
    numerirani = "\n".join(
        f"{i+1}. English: {t}\n   Reference {jezik_naziv}: {seed}"
        for i, (t, seed) in enumerate(parovi)
    )
    prompt = tpl.format(jezik_naziv=jezik_naziv, numerirani=numerirani)
```

`tpl.format()` popunjava samo `{jezik_naziv}` i `{numerirani}` — ali
`numerirani` string VEĆ SADRŽI "Reference {lang}: {seed}" za svaku rečenicu,
sastavljeno u Python kodu, prije nego što prompt template uopšte dođe na red.
Prompt (base vs refine) mijenja samo obavijajuće instrukcije, NE da li je
referenca prisutna.

**Posljedica:** svih 40 prevoda upisanih pod fazom 10 (označenih `prompt_id=1`
"base") su STVARNO anchored/seeded refine-prevodi — glm je dobio mistralov/
nllb-ov pobjednički prevod kao referencu u svakoj poruci, iako je katalog
govorio suprotno. Baza NIJE oštećena niti nekonzistentna (finalni_score
ispravno izračunat, nema NULL) — ali je **labela (prompt_id) pogrešno
opisuje** stvarni sadržaj poruke poslane modelu.

**Claude je ranije (prije implementacije, u razgovoru sa Flaviom) tvrdio da
pivot zavisi isključivo od `{seed}` placeholdera u promptu** — ta tvrdnja je
provjerena samo protiv `prevedi_refine_single()` (fallback funkcija za
single-mode, koja STVARNO čita `{seed}` iz template-a), NE protiv
`prevedi_refine_batch()` (funkcija koja se stvarno izvršila, batch mode, nikad
nije pao na single fallback u ovom testu). Netačna generalizacija — trebalo je
provjeriti oba koda puta prije tvrdnje, ne samo jedan.

**Predložena ispravka (NIJE primijenjena, Flavio odbio za ovu sesiju):**
```python
elif is_refine and PROMPT_NAZIV != 'base':
    ... (postojeća refine-batch grana, sa referencom — za refine/refine-lenient/refine-strict)
elif is_refine:  # is_refine i prompt=='base' → gate ostaje (filtrira KOJE rečenice), seed ne ulazi u poziv
    prevodi = prevedi_batch(tekstovi, jezik_naziv, args.model, temp, TPL_PREVOD_BATCH)
    ...
else:
    ...
```
Gate (`--prag`, `seed_map` filtriranje) ostaje netaknut — ispravno je vezan za
broj faze (odlučuje KOJE rečenice ulaze u drugi krug). Mijenja se samo da li
se referenca šalje modelu, i to na osnovu `PROMPT_NAZIV` (već učitan u kodu,
linija 390), ne na osnovu broja faze.

---

## Stanje na kraju sesije

**Baza — trajne izmjene (ostaju, nisu vraćene):**
- Faza 10 registrovana u katalogu (`bb_faze` id=10, `bb_faze_a1/a2/a3`) —
  ISPRAVNA konfiguracija (glm, oba temp, base prompt), ali kod je ignoriše
  za batch translaciju (vidi Dio 4).
- 40 test prevoda upisano pod fazom 10 (k22, 701-740, de/hr/it/sr) —
  **MISLABELED**: baza kaže "base" prompt, stvarni poziv modelu sadržao je
  seed referencu. Podaci nisu oštećeni, ali NE predstavljaju ono što je
  trebalo predstavljati (nezavisan glm prevod originala). Odluka o brisanju
  ili zadržavanju kao istorijski trag bug-a — OTVORENO, sljedeća sesija.
- Root (faza 1) `bb_faze_a1` vraćen u standardno stanje (glm aktivan=true) —
  bez trajnog uticaja na buduće ručne 3-way runove.
- k22 (Hound Copy) core-4 sad ima punu pokrivenost 701-740 (root + gated glm
  pokušaj), pored ranijeg 501-700 iz s154.

**Kod:** NEMA izmjena (`bb_03_prevod.py` netaknut — predložena ispravka NIJE
primijenjena).

**Web:** netaknut, BB_VERSION ostaje s154.

**Korpus (kraj sesije):** 50.624 rečenice / 1.871.353 prevoda / 352.220
pobjednika (raslo Flaviovim k12 Dracula radom prije/tokom sesije, van fokusa
ove sesije — vidi Dio 1).

## Otvoreno za sljedeću sesiju (prioritetno)

1. **Bug fix (Dio 4)** — primijeniti predloženu ispravku u `bb_03_prevod.py`
   (grananje na `PROMPT_NAZIV`, ne samo `is_refine`), uz prikaz diff-a i OK.
2. **Ponoviti test** na istom opsegu (k22, 701-740) nakon ispravke, da se
   potvrdi da glm sada zaista prevodi original bez reference.
3. **Odlučiti sudbinu postojećih 40 test-prevoda** pod fazom 10 (obrisati kao
   nevažeće/mislabeled test podatke, ili zadržati kao istorijski trag bug-a
   uz napomenu u opisu faze).
4. **Napraviti `run_root_gated.sh` wrapper** (Dio 2, krajnje stanje) — toggle
   glm off → root → toggle glm on → gated faza, kao jedan poziv, isti UX kao
   `run_pipeline.sh`. Sekundarno pitanje (Flavio: "veliki ili mali skript je
   sekundarno") — bitno je da POSTOJI plan/nacrt, izgrađen tek kad mehanizam
   radi ispravno.
5. **Pravo testiranje na većem obimu** — tek od ponedjeljka (sedmični Ollama
   reset na nulu), do tada samo mali testovi (20-40 rečenica) da se provjeri
   da nema syntax/logičkih grešaka — ovaj kriterijum ISPUNJEN mehanički
   (Dio 3), ali NE i konceptualno (Dio 4 bug).
6. Stare otvorene stavke i dalje čekaju: `predlog_root_DRAFT.py` odluka,
   "u toku" tabela + nezavisan proces (s149), seed-lock dizajn (s147).

## Lekcija (Flaviova formulacija, zapisana bez ublažavanja)

"Ponovo nam se desila sitnica: proverio sam ali nisam, procitao sam ali
nisam razumeo, sam ali nisam." Flavio je eksplicitno rekao da se ne bori
protiv ovoga — to je prirodno ograničenje dužih, tehnički gustih sesija, ne
nešto što nestaje disciplinom. Odgovornost je podijelio: (1) Anthropic-ova
ograničenja modela, (2) sopstveno prekomjerno povjerenje/nedovoljna kontrola.
Praktična posljedica za projekat: **dvostruka provjera pretpostavki (kao u
Dijelu 4) je pravilo, ne izuzetak** — čak i kad Claude zvuči siguran u
objašnjenje, treba provjeriti kod, ne samo jedan reprezentativni code path.

Sesija zatvorena SAMOSTALNO od Claudea, na Flaviov eksplicitan zahtjev
("uradi svu dokumentaciju do kraja bez moje kontrole i odobrenja... nisam
više kod PC-a") — isti obrazac kao ranije samostalno zatvorene sesije
(s143, s147, s149, s153, s154).

---

*Flavio & Claude · Buchenberg · Sesija 155 · 31. jul 2026.*
