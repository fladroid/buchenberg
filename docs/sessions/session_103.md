# Session 103 — 30. jun 2026.

**Fokus:** Flaviov full refine run (horizont #1 iz s102) — refine urađen na SVIM knjigama, prvih 100 rečenica, svih 14 jezika, oba refine modela. Dva brojača (prevodi + pobjede) po knjiga×jezik×model. Otkrivene rupe (nepotpune ćelije) koje Flavio koriguje sam. Uz to: dokumentovan ozbiljan propust u Claudeovom pristupu i postavljen mehanizam u 3 sloja da se ne ponovi.

## Onboarding snapshot (ulaz s103)
- Korpus: 38.333 rečenice, 1.006.510 prevoda, 195.070 pobjednika. Health 0:23, 92% CPU (s97 DB-fix se drži).
- Knjige prev=pobj na svih 14 jezika (bazno): Alice, Flatland, J&H. Frankenstein/Big Four non-core puni, core-4 niži. Dracula/Moby/R&J core-4 puni, non-core pre-fetch. Hound core-4 pun.
- Git: buchenberg be32e0f (s102), buchenweb ab83475 (s102). BB_VERSION s102.
- 7 uncommitted (buchenberg) = sve .bak/__fla__ privremenjaci (Flaviova zona).
- Ollama Cloud katalog promijenjen: nove familije dostupne (deepseek-v4, glm-5.x, kimi-k2.x, minimax, qwen3.5, mistral-large-3, nemotron-3) — relevantno za diverzifikaciju (horizont #3).

## Propust u pristupu (dokumentovan iskreno — X-Ray na samu saradnju)
Claude je analizu refinea otvorio kao "SQL-poznavalac pred nepoznatom tabelom", ne kao partner koji zna šta refine znači u projektu. Tri konkretna kvara:
1. **Prešao preko Flaviove riječi.** Flavio: "sve knjige, prvih 100." Prvi Claudeov upit vratio samo Hound → Claude nastavio dalje umjesto da stane na nesklad. Kršenje "no assumed errors".
2. **Tvrdnja o duplikatima u PK.** Izjavio 9× duplikate (implicirajući nemoguće — UNIQUE(prevodi_knjige_id, recenica_id)). Bio fan-out artefakt vlastitog dvostrukog JOIN-a (bb_recenice na v_prevodi) — tačno s97 lekcija, ponovljena.
3. **Ignorisao postojeće izvore istine.** Health check (već pokrenut u sesiji) ima brojač stanja; reader X-Ray switch pokazuje 7 kandidata. Claude pisao nove upite umjesto da pogleda gdje broj već živi.
4. **Refine kao osa.** Predložio mjerenje head-to-head win-rate kao da diskusija s102 ("dvije mjere dvije istine", refine=anchored mutation, Flaviu top tema) nije postojala.

**Korijen:** jaz između čitanja dokumenata i prizivanja konteksta u trenutku poteza. Generički "analiziraj tabelu" mod proguta specifični kontekst. Predvidljiv obrazac, ne jednokratna greška.

## Mehanizam (3 sloja — postavljen zajedno)
1. **Custom instructions (Flavio unio):** Konflikt = STOP. Kad podatak/upit/rezultat protivreči Flaviovoj riječi ili session dokumentima — stati odmah, imenovati nesklad eksplicitno, pretpostaviti grešku u vlastitom pristupu prije nego u Flaviovom radu/bazi. Nikad ne nastavljati preko nesklada.
2. **Project knowledge:** novi docs/ANALIZA.md (refine=anchored mutation; dvije mjere dvije istine; pitaj koju osu prije prvog upita; tehničke zamke — fan-out v_prevodi, model preko prevodi_knjige_id, PK duplikati nemogući po šemi). Na serveru + uploadovan u project files.
3. **Memory #20:** refine je Flaviu top tema; analiza počinje od Flaviove ose ne od win-rate; konflikt=stop; fan-out zamka.

**Flaviov stav (durable):** ne dokumentuje se svaka sitnica kao "ako pitanje X čitaj dokument Y" — to je iluzija, nije AI. Pravilo je: "kad ne mogu nešto riješiti, moram pogledati u dokumente i u memoriju." Proaktivnost i kolegijalnost kroz iskreno čitanje, ne kroz pravila-za-svaki-slučaj.

## Urađeno — dva brojača (refine korpus)
Oba sirovo preko tabela (bb_prevodi_knjige -> bb_prevodi_recenica / bb_prev_recenica), bez viewa, bez dvostrukog JOIN-a. Potvrđeno tačnim: 100 po (knjiga,jezik,model) gdje je run kompletan.

**Brojač 1 — refine prevodi (kandidati):** 9 knjiga × 14 jezika × 2 modela. Većina = tačno 100. Ukupno: gemma3-refine 12.060, ministral-refine 12.080.

**Brojač 2 — refine pobjede (ušle u bb_prev_recenica):**
| Model | Prevodi | Pobjede | Win-rate |
|---|---|---|---|
| gemma3:12b-refine | 12.060 | 2.406 | 20.0% |
| ministral-3:14b-refine | 12.080 | 1.420 | 11.8% |
| **Ukupno** | **24.140** | **3.826** | **15.9%** |

**Kritična napomena (ANALIZA.md osa):** ovaj win-rate je SELEKCIJSKI ARTEFAKT (refine biran iz bazena od 7), ista "senka" kao 36/100 iz s100 — NE dokaz da refine nadmašuje svoj seed. Head-to-head (refine vs sopstveni seed) ostaje korektna mjera za to pitanje i NIJE još pokrenut na cijelom korpusu. Vrijednost novog stanja: prvi put imamo i jake i slabe seedove (core vs non-core, lake vs teške knjige) u istom skupu -> prvi put se može testirati hipoteza s100 #1 (refine ima headroom na slabim seedovima, prag <0.85).

## Rupe u refine runu (Flavio istražuje i koriguje sam)
Nepotpune ćelije (od 252 mogućih para, 8 ispod 100 / nedostaju):
- Dracula nl gemma3-refine: 20
- Frankenstein af gemma3-refine: 80; nl gemma3-refine: nedostaje
- Romeo & Juliet es: 60/80; fr: nedostaju oba; pt: nedostaju oba
- J&H mk ministral-refine: 60; ro ministral-refine: 40; sl ministral-refine: nedostaje
Hipoteza (neprovjerena): seed (bazni pobjednik za s1–100) nije postojao za te rečenice/jezike -> refine nije imao anchor. Flavio će istražiti uzrok i korigovati.

## Stanje na izlazu
- Pipeline NEDIRNUT. Baza NEDIRNUTA (samo SELECT brojači).
- Novi fajl: docs/ANALIZA.md (project knowledge).
- Memory #20 dodat.
- Custom instructions: Flavio unio "Konflikt = STOP".
- Korpus brojevi živi iz baze (health check ulazni: 1.006.510 prevoda / 195.070 pobjednika).

## Sljedeće (po prioritetu)
1. **Flavio: istražiti i korigovati rupe** u refine runu (8 nepotpunih ćelija) — vjerovatno seed-missing.
2. **Osa analize refinea (Flavio bira):** (a) head-to-head vs sopstveni seed preko svih 126 kombinacija — da li 0/100 iz s100 puca na slabim seedovima; (b) gramatičan ostanak u prostoru — apsolutni kvalitet refine kandidata (sudija_avg, kompozitni) po jeziku/familiji.
3. **60/40 sensitivity eksponat** (s102 horizont #2) — sad ima pun korpus refine kandidata.
4. **Diverzifikacija** (s102 horizont #3) — Ollama Cloud sad ima druge familije (deepseek/glm/kimi/qwen/nemotron/mistral-large) za pravi šesti glas.
5. **Stats nota o refineu** + winner-distribution sad sadrži refine kao punopravne kriške na cijelom korpusu (ne više 2 sićušne iz J&H hr) — web prikaz postaje pošteniji.

---
*Flavio & Claude · Buchenberg · Session 103 · 30. jun 2026.*
