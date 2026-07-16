# Session 140 — 17. jul 2026.

## Fokus
KONCEPTUALNA sesija — nula izmjena koda/baze (korpus READ-ONLY). Nastavak s139
horizonta. Flavio postavio tri okvirne odluke, pa smo kroz dijalog razradili dva
aktivna koncepta: (1) prompt kao ravnopravan atribut faze; (2) random selekcija
atributa s marginalnim preferencama i mutacijom. Web: jedan mali dodatak
(McClintock u about + Key Concepts) — konkretan povod, ne "glačanje".

## Zdravlje na početku
50.624 rečenice · 1.595.460 prevoda · 302.168 pobjednika. BB_VERSION s138
(buchenberg 2fd219a, buchenweb 771bc44). 231 poznata rupa (2b) — sve faza 1,
retired modeli + novi par na djelomično prevedenim knjigama (Flaviovi f1 runovi),
prio 2, nepromijenjen obrazac. Sve zeleno.

## Zdravlje na kraju
Korpus nepromijenjen (nijedan prevod upisan — sve READ-ONLY osim web dodatka i
dokumentacije). Web: about.html + concepts.json (McClintock kartica). BB_VERSION
s138 → s140.

---

## 0. Tri okvirne odluke (Flavio, početak sesije)

1. **"Web stabilizacija/estetsko glačanje" (s138 Odluka 2) NIJE trajni horizont.**
   Flavio: "to nikad neće biti gotovo, ne treba ponavljati." Prestaje se navoditi
   kao "sljedeći koraci". Web izmjene = ad-hoc, kad ima konkretan povod.
2. **ti/vi + NER/sažetak kontekst-injection nit (s136-s138) TRAJNO ZATVORENA.**
   Flavio: "ne radimo." Ne oživljavati ni u "otvoreno za sljedeću sesiju".
3. **FOKUS na dva s139 koncepta** — Flavio: "to me najviše interesuje":
   (a) prompt kao neregistrovan parametar; (b) random selekcija s evoluirajućim
   preferencama. Sad aktivni radni prioriteti, ne pasivan horizont.

---

## 1. Prompt kao ravnopravan atribut faze

### 1.1 Put do odluke (EAV razmotren i odbačen)
Flavio je otvorio strukturnim pitanjem: sadašnja shema je
`faza_id, atribut1, atribut2, ..., atributn` (kolonska); dodavanje/mijenjanje
atributa traži `ALTER TABLE`. Alternativa `faza_id, atribut, vrijednost` (red po
atributu) čini dodavanje atributa običnim INSERT-om. Da li bi bilo manje problema?

Claudeov odgovor: to je klasičan **EAV (Entity-Attribute-Value)** trade-off.
Prednost EAV-a stvarna (nema migracije za nov atribut), ali cijena:
- **Gubi se tipska sigurnost** — temperatura je danas NUMERIC (s110 float lekcija,
  `ROUND(temperatura::numeric,4)`); u EAV sve postaje TEXT, cast u kodu ne u bazi.
- **UNIQUE se raspada** — `UNIQUE(naziv,temperatura,faza_id)` na bb_modeli je
  provjera jednog reda; u EAV "postoji li kombinacija" je upit preko više redova.
  `already_done()` se oslanja baš na to.
- Isti spor koji je Flavio već proživio na malom: `v_status_faza` (long, fleksibilan)
  vs `v_status_faza_matrica` (pivot, hardkod kolone, "ne skalira" — njegova s134 opaska).

**Flaviova odluka (principijelna):** EAV odbačen. Ključni argument — **shemu moraš i
ČITATI, ne samo mijenjati; ako za čitanje sheme treba priručnik, izgubili smo.**
`ALTER TABLE ADD COLUMN` je jeftin. Dodatni SELECT prompta jednom po runu je
zanemarljiv (pristup bazi je ionako obavezan jer bilježimo prevode). "A i da košta…"

### 1.2 Gdje prompt živi — bb_faze, ne bb_metode (Claudeov s139 stav ISPRAVLJEN)
Claude je u s139 zagovarao opciju B (prompt na `bb_metode`) po logici "faza je tanka,
sadržaj ide u metod". Flavio je tu logiku ispravio:

**"Tanka faza" NIKAD nije značila "zabranjeno dodavati atribute."** Značila je samo
praktičnu odluku da redni broj bude čitljiv umjesto mistična DB sekvenca. Faze su
mogle biti banana/jabuka/trešnja, ili čista sequence bez značenja — redni broj je
izabran da se "na prvi pogled zna šta se ispod skriva". Ergonomija, ne princip
identiteta. Značaj rednog broja čak OSLABIO od s134: nekad je kodirao redoslijed
("3 ne smije prije 2"), sada ni to — jedini preduslov je **postojanje pobjednika**
(s139), ne redoslijed.

**Princip:** "jedinstvena identifikacija faze su SVI atributi koji opisuju fazu."
Prompt opisuje fazu (parametar prevoda kao model/temp) → pripada opisu faze.
Metod ostaje KRUPNA kategorija (base/self-refine, root boolean, klasa operacije) i
NE dira se — prompt je finiji od metoda. Nova promjena prompta ne rađa nov metod
(prekrupno), nego je atribut faze.

**ODLUKA:** prompt se od sada posmatra kao **ravnopravan atribut skupa atributa faze**,
isto kao model ili temperatura. Ide na `bb_faze` kao TEXT kolona.

### 1.3 Mehanika i "sporo mijenjajuće dimenzije"
Flaviova ključna analogija: **naša istorija prevoda JEST istorija promjena root faze 1.**
Kad je pokrenuo fazu 1 s novim modelima — ništa dramatično se nije desilo jer je to
bio samo `UPDATE` aktivnih modela na bb_modeli; stari modeli i njihovi prevodi ostaju
u istoriji knjige, vezani za konkretne bb_modeli redove, ne za "trenutno stanje faze 1".
Root faza ostaje jedan red (isti id), mijenja se njen *trenutni sastav*.

Prompt se ponaša isto: `ADD COLUMN prompt TEXT` + `UPDATE` (upiši trenutni prompt).
Kad se jednom promijeni → `UPDATE` polja. Novi prevodi s novim promptom, stari ostaju
s onim s kojim su napravljeni.

Claudeova identifikacija obrasca: ovo je **slowly changing dimension (SCD), najbliže
Tipu 1** (overwrite — UPDATE prepiše tekuću vrijednost). Istorija ne živi u tabeli
faze nego u činjeničnoj tabeli (`bb_prevodi_recenica` preko `bb_prevodi_knjige`), gdje
svaki prevod nosi trag modela i temperature s kojima je nastao. Faza kaže "evo šta sam
SADA", prevodi kažu "evo pod čime smo tada radili".

**PRAZNINA (Flavio je sam imenovao, prihvaćena):** taj trag za prompt TRENUTNO NE
POSTOJI. Model i temperatura su u istoriji jer su na bb_modeli koji je FK-vezan za
svaki prevod. Prompt na bb_faze (Tip 1) znači da nakon UPDATE-a više ne znaš s kojim
je *tačno* promptom stari prevod napravljen. **Treba nešto ručno uraditi — dodati prompt
u istoriju** — "ali to smo i očekivali" (Flavio). Za refine (s139 cilj: stari-i-novi
prompt koegzistiraju za mjerenje) ovo je posebno relevantno — Tip 1 overwrite to ne
daje sam po sebi.

### 1.4 Root invarijanta provjerena na serveru (READ-ONLY)
`\d bb_faze` pokazao dvije relevantne prepreke za "nov prompt = nova faza":
- `bb_faze_root_jednom` UNIQUE btree (metod_id) WHERE metod_id = 1 — tačno JEDAN red
  s metod_id=1. Nova bazna faza je fizički nemoguća (s134 invarijanta, verifikovana).
- `bb_faze_redoslijed_key` UNIQUE (redoslijed) — dvije faze ne dijele redni broj.

**Posljedica, riješena Flaviovim SCD uvidom:**
- Za refine faze (metod_id=2): nov prompt = nova refine faza s novim redoslijedom →
  radi, partial index ne dira metod_id=2 (faze 2/3 već dokaz).
- Za baznu (root, metod_id=1): shema zaključava DRUGU baznu fazu. **I to je ispravno** —
  Flavio NE želi dvije bazne faze. Root je JEDAN red; mijenja se njegov trenutni sadržaj
  (Tip 1 SCD), a istorija promjena živi u prevodima. `bb_faze_root_jednom` OSTAJE
  netaknut. (Flavio: "fazu 1 sam u konceptu nazvao root da naglasim ulogu, ne redni broj.")

### 1.5 Rad koji slijedi (kad se gradi)
Čist posao, "običan update":
1. `ALTER TABLE bb_faze ADD COLUMN prompt TEXT`.
2. `UPDATE` — upisati sadašnji prompt: base prompt u fazu 1, refine prompt u faze 2+
   (različit, kao model/temp po fazi).
3. `bb_03` čita prompt iz baze na početku runa umjesto literala; **header loga dobija
   prompt**; sve što se danas radi s modelom/temperaturom (protokolisanje, kompletnost-
   provjera 1a, header) sada se radi I s promptom.
4. Ručno dodati prompt u istoriju postojećih prevoda (praznina iz 1.3).
5. Od danas: promjena prompta = nova kombinacija atributa; za refine → nova faza (nov id).

---

## 2. Random selekcija atributa s marginalnim preferencama

Razrada s139 §3 ideje kroz dijalog. Nekoliko Claudeovih početnih zamjerki Flavio je
raspustio precizacijom — zabilježeno jer mijenja karakter koncepta.

### 2.1 Faza 1 je temelj, nema filozofije
**Sav random/preferenca/mutacija aparat radi NAD SEEDOM; seed dolazi iz faze 1.**
Nema faze 1 → nema pobjednika → nema šta refine da žanje (s139 preduslov). Bazna faza
mora biti glupa i pouzdana (deterministična, aktivni modeli iz baze kako sad radi) baš
zato da bi refine iznad nje smio biti razigran. Random tek OD refine faza naviše.

### 2.2 Mehanika random faze: traži-ili-kreiraj
Random se biraju vrijednosti atributa (2 modela, temperatura, prompt, redovi/rečenice).
Provjeri postoji li faza s tim skupom atributa u registru faza:
- postoji → nastavi kao dosad (idempotentno);
- ne postoji → to više NIJE "update" nego **INSERT** nove faze.
Kombinatorika (broj modela × temp × prompt × …) velika ali konačna — baza to lako
podnese. (Flavio može vještački dodati faza_id da isproba višestruki poziv istih atributa.)

### 2.3 KLJUČNA precizacija — preferenca je MARGINALNA po atributu, ne po kombinaciji
Claude je pogrešno pretpostavio preferencu nad kombinacijom (MA+TB+PC pobjeđuje → daj
toj trojci širi interval) — to konvergira i zaključava favorita.

**Flavio: preferenca je po SVAKOM ATRIBUTU ZASEBNO (marginalno).** MB je najčešći
pobjednik *gledano po modelu* (preko svih temp/promptova); TA *po temperaturi*; PB
*po promptu*. Biraš svaki atribut iz njegove vlastite preferencijalne raspodjele i
kombinuješ ih **nezavisno**. Rezultat MB+TA+PB je vjerovatan ali se možda nikad nije
dogodio kao takav — sastavljaš ga iz marginalnih favorita.

**Zašto je otpornije (Claudeova analiza):** kombinatorna preferenca ima jedan vrh koji
raste dok ne proguta prostor. Marginalne preference održavaju raznolikost PO
KONSTRUKCIJI — tačka se svaki put iznova sastavlja iz odvojenih bacanja, nikad ne
kolabira u jednu. Svaki atribut zadržava nenulti interval (Flaviov anti-elitizam:
"niko nema 100% ni 0% šanse izbora"). Prostor ostaje pretraživan.

### 2.4 Mutacija — odvojen korak poslije izbora
Flavio: mutacija je JEDINO gdje se prirodno uklapa. Dva koraka: (1) izbor atributa po
preferenci, pa (2) mutacija izabranog zasebnim algoritmom ("koji moram dodati").
Čista GA struktura — selekcija pa mutacija, ne pomiješano. Mutacija na marginalnom
atributu je jeftina/sigurna (promijeni prompt na drugi, temp 0.8→0.1) — ostaje u
zatvorenom poznatom skupu, niska cijena greške (X-Ray kriterij dozvoljene mutacije,
pogl. VI).

### 2.5 Strop protiv preuzimanja (anti-konvergencija kao pravilo)
Flavio: neka self-refine kombinacija ne smije se pojaviti u knjizi/jeziku u više od
~50% rečenica. Diverzitet kao TVRDO OGRANIČENJE, ne kao statistička nada — favoritu se
*zabrani* da preuzme, umjesto oslanjanja na to da preferenca neće zaključati. Ne moraš
savršeno podesiti intervale ako ionako imaš strop.

### 2.6 Granularnost uspjeha — tri nivoa, ponderisano (kao ocjenjivanje)
Otvoreno pitanje: mjeri li se uspjeh atributa po Biblioteci, Jeziku ili Knjizi?

Prvo je Flavio naginjao **globalno (biblioteka)** — biblioteka mala, dijeljenje po
žanru fragmentira oskudne podatke. Claudeova zamjerka: Flaviova vlastita rečenica
"ne mogu iskustvom iz Hounda prevoditi Pepeljugu" argumentuje PROTIV globalnog —
globalno stapa Hound i Pepeljugu u jedan prosjek i tim prosjekom prevodi obje.
s137 već izmjerio da je efekat stvaran (stari par dobija na Moby Dick/R&J arhaičnoj
prozi, gubi na Hound/Big Four).

**Pitanje klase (žanra):** Flavio NE bi puštao knjigu kroz LLM da dobije klasu (nova
crna kutija, protiv projekta). Riješio elegantnije: **ne treba klasa ako imaš knjigu** —
knjiga je najsitnija jedinica, žanr je implicitno unutra (Moby Dick JEST svoja klasa).
Sišao nivo ispod klase i zaobišao problem njenog definisanja.

**Flaviov prijedlog (usvojen kao pravac):** kao kod ocjenjivanja — tri grupe informacija
Biblioteka / Jezik / Knjiga. Vidi kakav je model X u sve tri → tri ocjene → ponderisano
spoji. **Knjiga nosi najviše, Biblioteka najmanje** (ono što prevodiš je *ova* knjiga;
biblioteka je samo kontekst). To je `finalni_score` filozofija preslikana (0.4/0.6 =
dva ponderisana pogleda) i rješava globalno-vs-knjiga spor bez biranja strane.

**Claudeova jedina dopuna (Flavio prihvatio):** ponder treba da PRATI KOLIČINU DOKAZA.
Rani prevod knjige → Knjiga ocjena počiva na ~20 rečenica (šum) → Biblioteka nosi više
(jedini stabilan signal). Kako knjiga raste → težina se seli na Knjigu. Nivo se "zasluži"
podatkom. (Statistički: shrinkage / povlačenje ka širem prosjeku kad je uzorak mali —
ali ne treba mu ime, prosto "ne vjeruj knjizi dok knjiga nema šta da kaže".)

### 2.7 Prag ulaska — proporcionalan, ne apsolutan
Flavio: random faza kreće tek kad faza 1 dosegne predefinisani procentualni minimum
pokrivenosti knjige. Ispod praga → **čisti uniformni random** (nema statistike jer je
nema odakle — knjiga još ništa nije rekla). Iznad praga → uključi ponderisanu preferencu
(2.6). Prag je prekidač između "generiši slijepo" i "generiši vođeno" — pošteno jer
prije praga NEMA šuma da se mjeri.

**10% vs 400 (Claude izoštrio, Flavio potvrdio proporcionalno):** Flaviovo "400 rečenica
bi pokrilo većinu knjiga" bilo je grubo mjerilo, ne pravilo. 10% se skalira s knjigom
(Hound 385, Moby Dick 976, Alice 154); 400 apsolutno je 26% Alice ali 4% Moby Dicka —
nisu isti prag. **Ostajemo pri procentima** (~10%) — reprezentativnost seed uzorka je
proporcionalna veličini knjige.

### 2.8 Prizemljenje — ne simuliramo evoluciju (Flaviova ključna ograda)
Claude je kroz razgovor posezao za GA teorijom (prerana konvergencija,
fitness-proportionate, shrinkage) kao da se gradi evolucioni sistem koji mora poštovati
njena pravila. **Flavio vratio na tlo: "mi ne simuliramo evoluciju i znamo šta radimo,
ili bar šta želimo."** Jumping-genes je ANALOGIJA (način da se vidi ideja), ne
specifikacija koju treba ispuniti. Random selekcija je alat koji daje šarolik korpus i
mjerljive preference — ne mora vjerno reprodukovati McClintockin kukuruz. Ako se sistem
negdje "smiri", to je možda baš ono što se promatra i uči iz toga; nije kvar koji se
mora unaprijed spriječiti teorijom, nego pojava koja se pogleda kad se desi. **X-Ray je
promatranje, ne predviđanje.**

**Flaviova zaključna rečenica (cijela filozofija projekta):** "sve što se događa je naš
cilj, sve radimo zbog nas, i dobro i loše." Nema "greške sistema" odvojene od nas —
samo ono što smo napravili i što ćemo iz toga pročitati. Preferenca je X-Ray VLASTITOG
OCJENJIVANJA, ne istina o jeziku (s139 ograda: sudija je i igrač i mjerni instrument;
McClintock imala nezavisnu istinu = boja zrna, mi imamo sudiju).

---

## 3. Web — McClintock (jedini web dodatak, konkretan povod)

Flaviov zahtjev: "McClintockin kukuruz" mora ući u about i dobiti link ka Wikipediji.
Povod konkretan (jumping-genes je postao dio konceptualnog vokabulara projekta), nije
"glačanje" (Odluka 0.1).

- **about.html:** kratka rečenica u postojeći kontekst o evoluciji/GA/mutaciji koja
  imenuje Barbaru McClintock i transpozone ("jumping genes") kao istorijsku inspiraciju
  za čitanje šarolikosti kao podatka. i18n ×5 jezika (novi ključ).
- **data/concepts.json (about grupa):** nova Key Concepts kartica — Barbara McClintock,
  wiki slug `Barbara_McClintock` (postoji na EN Wikipediji, provjereno). Ikona 🌽.

---

## Odluke i status
- **Nijedna izmjena koda/baze.** Sve READ-ONLY (`\d bb_faze`) + web dodatak + dokumentacija.
- Prompt-kao-atribut-faze (§1) i random-selekcija-s-marginalnim-preferencama (§2) su
  RAZRAĐENI DIZAJN / horizont — konsenzus postignut, ali implementacija nije pokrenuta.
- Prompt na `bb_faze` (TEXT kolona), root invarijanta ostaje, istorija prompta = ručni
  posao (SCD Tip 1).
- Random: faza 1 temelj (deterministična), random iznad proporcionalnog praga (~10%),
  preferenca marginalna po atributu, tri nivoa (Bibl/Jezik/Knjiga, knjiga teža, ponder
  raste s podacima), mutacija odvojen korak, strop protiv preuzimanja.
- Faza 3 možda izbrisiva (najmanje prevoda/pobjednika) — ostavljeno za kasnije, ne dira
  se dok random-faza dizajn ne sazri (živi dokaz mehanike "nova faza za istu trojku").

## Lekcije
1. **Čitljivost sheme je projektni zahtjev, ne udobnost.** Flaviov argument protiv EAV-a:
   shemu moraš i čitati; ako za čitanje treba priručnik, izgubili smo. Fleksibilnost
   upisa (EAV) ne vrijedi ako plaća čitljivošću i tipskom sigurnošću.
2. **"Tanko" ≠ "zatvoreno za atribute."** Claudeova s139 greška: tretirao "tanku fazu"
   kao dogmu. Flavio: bila je ergonomska odluka (čitljiv redni broj), ne granica
   identiteta. Faza = svi njeni atributi; prompt je legitimno jedan od njih.
3. **Marginalna preferenca > kombinatorna preferenca za održavanje raznolikosti.**
   Kombinacija konvergira u jedan vrh; marginalni izbor po atributu sastavlja tačku
   iznova svaki put → raznolikost po konstrukciji. Flaviova precizacija raspustila
   Claudeovu glavnu zamjerku (prerana konvergencija).
4. **Knjiga-kao-svoja-klasa zaobilazi problem definisanja žanra.** Ne treba klasifikator
   (LLM = nova crna kutija) ako se mjeri direktno na najsitnijoj jedinici. Ponderisana
   tri nivoa (Bibl/Jezik/Knjiga) daje i stabilnost i specifičnost bez biranja strane.
5. **Analogija nije specifikacija.** "Ne simuliramo evoluciju" — jumping-genes je način
   da se vidi ideja, ne skup pravila koja se moraju poštovati. X-Ray je promatranje
   pojave kad se desi, ne teorijsko predviđanje kvara unaprijed.
6. **Idempotentnost skriva efekat parametra van ključa (s139, potvrđeno).** Prompt van
   (model,temp,faza) trojke = nevidljiv. Rješenje: prompt ulazi u identitet faze.

## Sljedeći koraci
- AKO se prompt-kao-atribut gradi: `ALTER TABLE bb_faze ADD COLUMN prompt TEXT` + UPDATE
  + bb_03 čita iz baze + header loga + ručni upis istorije prompta. Root ostaje jedan.
- AKO se random-selekcija gradi: redoslijed je faza 1 (temelj) → generativna mašina
  (uniformni random ispod praga) → preferenca (marginalna, tri nivoa) → mutacija → strop.
  Graditi mjerenje/promatranje prije mehanizma koji na osnovu njega dirigује.

---
*Flavio & Claude · Buchenberg · Sesija 140 · 17. jul 2026.*
