# Sesija 157 — 1. avgust 2026.

**Fokus:** Konceptualna sesija, nula pipeline poziva, nula DB/kod izmjena tokom same diskusije. Flavio je iznio dvije nove ideje za dalje sužavanje gated-root troška. Kroz razgovor o paralelizmu otkriven je strukturni problem: `run_root_gated.sh` mehanizam (toggle `bb_faze_a1.aktivan` za fazu 1) je nekompatibilan sa Flaviovim standardnim radnim obrascem (paralelno po jeziku) — race condition na globalnom stanju. Diskusija razriješena kroz analogiju "zajednički recept na zajedničkom zidu" i formulisan predlog rješenja: promjena "svijeta" (root konfiguracije) postaje ručan, protokolom-vođen čin, potpuno odvojen od automatizovanih skripti, po istom obrascu koji refine faze već prate.

---

## Dio 1 — Dvije nove ideje (dokumentovane, NEIMPLEMENTIRANE)

Kontekst: cilj je dalje smanjiti pozive skupom modelu (glm-5.2) unutar već postojećeg gated-root obrasca (s154-156), bez gubljenja kvaliteta.

**Ideja 1 — podjela gated glm faze po temperaturi.** Umjesto da faza 10 zove glm@0.1 i glm@0.8 zajedno za svaku rečenicu ispod praga (kao sada), razdvojiti u dvije sekvencijalne gated faze: prvo glm@0.1 → sudija → pobjednik; zatim SAMO za rečenice i dalje ispod praga, glm@0.8 → sudija → pobjednik. Ako 0.1 sam riješi većinu, drugi poziv se za te rečenice nikad ne desi. Ista logika kao sami gate, primijenjena unutar glm-a.

Nijansa (Claude, tokom razgovora): README §3 "Temperatura pattern po jezičnoj grupi" sugeriše da 0.1 nije uvijek jača temperatura (germanski jezici favorizuju 0.8) — redoslijed 0.1-pa-0.8 možda nije optimalan za sve jezike; vrijedi izmjeriti prije čvrste odluke o redoslijedu. Pattern je označen kao trend, ne pravilo.

**Ideja 2 — radikalnija varijanta, gatovanje i mistrala.** Root = SAMO nllb@0.0 + mistral@0.1 → sudija → pobjednik. Gated faza za rečenice ispod praga: mistral@0.8 → sudija → pobjednik. Zatim iste dvije glm gated faze iz Ideje 1. Flavio je sam istakao ogradu: mistral nije disproporcionalno skup (dashboard s156: mistral segment zanemarljiv naspram glm-a) — ušteda ovdje je vremenska/brojčana (izbjegavanje nepotrebnog ponovnog prevođenja), ne novčana.

Nijanse (Claude): (a) ovo mijenja semantiku same root faze (mistral@0.8 postaje uslovan umjesto uvijek-aktivan) — vrijedi eksplicitno imenovati u KONCEPT.md ako se usvoji; (b) sekvencijalni lanac od 4 gated faze umjesto paralelnog 3-way roota može POVEĆATI ukupno vrijeme po rečenici i pored manje poziva, jer svaka faza čeka prethodnu; (c) prag 0,95 je kalibrisan na presjeku 3-way roota (s144) — ako root postane 2-way, vrijedi provjeriti da li prag i dalje ima smisla ili treba prekalibraciju.

Obje ideje slijede istu filozofiju: "ne prevoditi dvaput nešto što je već dobro" — konzistentno sa postojećim gate principom (s144 headroom-gate nalaz).

## Dio 2 — Otkriven strukturni problem: race condition na gated-root switchu

Flaviovo pitanje (motivisano opažanjem da paralelan rad po jeziku, ne po grupi jezika, radi brže — isti empirijski nalaz kao s132 2,47×): da li trenutni gated-root mehanizam (`run_root_gated.sh`, s156) dozvoljava paralelno pokretanje po jeziku, kao standardni tok rada?

**Odgovor: NE.** Provjerom koda (`bb_toggle_model.py`, `run_root_gated.sh`, `bb_aktivni_modeli.py`, `run_faza.sh`) potvrđeno: `bb_faze_a1.aktivan` za (faza_id=1, model_id=glm) je JEDAN globalan red u bazi — ne postoji ništa što bi ga izolovalo po procesu, jeziku, ili knjizi. `run_root_gated.sh` ga toggle-uje OFF na početku i ON na kraju (`trap` na EXIT) unutar SVAKOG pojedinačnog poziva.

Konkretan scenario kvara (dva paralelna poziva, npr. de i hr): Proces A završi svoj gated-root ciklus i vrati glm na aktivan=true (cleanup); ako Proces B u tom trenutku tek započinje svoju root fazu, `bb_aktivni_modeli.py` čita GLOBALNO stanje kakvo trenutno jeste — dobija glm=true — njegov "suzen root" tiho postaje pun 3-way root, identičan klasičnom metodu, bez ijedne greške ili upozorenja. Obrnuto: dok je A usred suženog prozora, BILO KOJI drugi paralelan poziv koji očekuje standardan 3-way root (npr. običan `run_pipeline.sh` za sasvim drugu knjigu) bi u tom prozoru tiho dobio glm isključen. Dodatni manji rizik: `kill -9` zaobilazi `trap`, ostavljajući glm trajno isključenim dok se ručno ne vrati.

Gated faza (10) sama nije ugrožena — njen red u `bb_faze_a1` (faza_id=10) se nikad ne dira, glm je tu uvijek aktivan nezavisno od stanja faze 1. Problem je isključivo oko privremenog sužavanja ROOT faze.

**Flaviova dijagnoza (formulisana kroz razgovor, potvrđena):** ovo nije bag u implementaciji toggle mehanizma — to je strukturna nekompatibilnost. Root invarijanta (KONCEPT.md, s112: `base` metod postoji tačno jednom, partial UNIQUE u shemi) je izgrađena na pretpostavci da faza ima STABILAN identitet u svakom trenutku — isti skup modela, čitljiv na isti način od bilo kog pozivaoca. Gated-root switch krši baš tu pretpostavku: privremeno prepisuje sadržaj identiteta faze 1 usred izvršavanja, umjesto da ga ostavi netaknutim.

**Ključna razlika naspram refine faza (2,3,4,5,6,9,10...):** one NIKAD ne trpe ovaj problem, jer je njihova konfiguracija upisana JEDNOM, kao INSERT, prije bilo kakvog izvršavanja — trajna deklaracija, nikad prepisivanje usred trke. Alice i Bob mogu paralelno pokretati fazu 4 i fazu 5 bez sudara. Root faza (kroz gated-toggle) je jedina koja je taj princip prekršila.

**Analogija koja je razjasnila problem (Flaviova formulacija, potvrđena kroz razgovor):** nije problem u tome koliko modela root ima u datom trenutku (3 vs 2 vs 5) — problem je u tome što je "koliko modela root trenutno ima" upisano kao JEDNA zajednička činjenica na zajedničkom mjestu ("recept na zajedničkom zidu"), koju različiti paralelni procesi pokušavaju istovremeno da pročitaju i prepišu, misleći da je privatna.

Usput pomenuta Deutschova multiverse analogija (digresija, namjerno kratka): Everettovi paralelni svjetovi rade jer se grane ne prepisuju međusobno — svaka nosi svoju izolovanu stvarnost. Naš bag nije bio "previše svjetova" nego odsustvo izolacije: dva procesa u JEDNOM svijetu koji oba misle da je privatan. "Pravo" kvantno rješenje bi izolovalo grane (svaki poziv nosi svoj privatni parametar umjesto globalnog reda); Flaviovo predloženo rješenje je klasično — nema paralelnih svjetova, samo jedan svijet mijenjan svjesno kroz vrijeme.

## Dio 3 — Predloženo rješenje (dogovoreno, NEIMPLEMENTIRANO — prio 1 za sljedeću sesiju)

Promjena "svijeta" (root konfiguracije) postaje ručan, protokolom-vođen čin, potpuno odvojen od automatizovanih skripti za prevođenje:

1. **Ulazak u svijet** — eksplicitna, prikazana, OK-ovana komanda (`UPDATE bb_faze_a1 ...`) koja kaže "od sada, root = ovi modeli". Prije toga: provjeriti da ništa trenutno ne trči nad starim svijetom (ps aux / logs).
2. **Rad unutar svijeta** — dok to stanje važi, proizvoljno mnogo paralelnih pokretanja po jeziku (`run_faza.sh --faza 1 ...`) — svi čitaju isti, stabilan recept. Gated faze rade nezavisno, kao i do sad.
3. **Izlazak iz svijeta** — eksplicitna, prikazana, OK-ovana komanda koja vraća staro stanje. NE automatski na kraju skripta.

**Direktna posljedica:** `run_root_gated.sh` u sadašnjem obliku (auto-toggle unutar `trap` na EXIT, zamišljen za ponovljeno/paralelno pozivanje) se povlači iz upotrebe za paralelan rad — treba ili preraditi da NE dira toggle uopšte (pretpostavlja da je svijet već ručno postavljen prije poziva), ili zadržati samo za striktno sekvencijalne/testne pozive gdje je poznato da ništa drugo ne trči.

Nije implementirano ovu sesiju — dogovoren pravac, izvršenje je Flaviov prio 1 za sljedeću sesiju (2. avgust 2026).

## Stanje na kraju

Nula izmjena koda/baze tokom same diskusije. Korpus na kraju sesije (health check na početku, nepromijenjen tokom sesije): 50.624 rečenice / 1.873.377 prevoda / 352.816 pobjednika. BB_VERSION nepromijenjen (web nedirnut). Ideje 1/2 i nalaz o race condition-u dokumentovani ovdje da se ne izgube prije nego se sutra (prio 1) uradi popravka; nakon toga, po Flaviovim riječima, "samo je mašta granica koje svjetove gradimo" — ideje 1/2 nastavljaju se tek nakon te izmjene.

Sesija zatvorena SAMOSTALNO od Claudea, na Flaviov eksplicitan zahtjev ("dokumentuj sve detaljno kao i uvijek ali ovog puta samostalno bez moje kontrole i odobrenja") — isti obrazac kao ranije samostalno zatvorene sesije (s143, s147, s149, s153, s154, s155, s156).

---

*Flavio & Claude · Buchenberg · Sesija 157 · 1. avgust 2026.*
