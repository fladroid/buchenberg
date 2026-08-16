# Session 176 — 16. avgust 2026.

**Fokus:** Analiza logova produkcije (tri kruga, komadi 50/60, 4→2 radnika), DB-driven analiza težine segmenata knjige 12 (kritičan nalaz: pozicije <489 nisu proza), istraživanje vizuelnog identiteta za About stranicu (Ken Burns / NotebookLM stilovi), sonda o efektu redoslijeda unutar batcha (nastavak s170).

Sesija duža od uobičajene, ali svi otvoreni pravci zatvoreni ili jasno predati sljedećoj sesiji.

---

## 1. Scheduler — razjašnjenje (kratko)

Flavio je sa Cowork-Claudeom riješio tehničko ograničenje "minut izvršavanja ne može biti 0" za Claude Scheduled taskove. Claude (ovaj chat) je pogrešno protumačio Flaviovu informaciju kao implicitnu kritiku i krenuo da traži gdje je "pogriješio" umjesto da je samo primi na znanje — obrazac ("kalkulator", doslovno čitanje umjesto praćenja namjere) već imenovan u ranijim sesijama, ponovljen na početku ove. Ispravljeno nakon eksplicitnog upozorenja; nema tehničkog rezultata iz ove teme.

## 2. Analiza logova — tri kruga, tri konfiguracije

**Krug 1 — `parapoc_*` (88 fajlova, komadi 50, 4 radnika, 6001-6400, svih 11 perifernih jezika).**
Mjereno: iznad-praga %, broj faza, vrijeme, blok B (glm) okidanje. Jasan gradijent težine, jezici se grupišu u parove (es≈pt, fr≈bs, nl≈af≈bg, ro≈ja≈mk, sl sam na dnu). **Preporuka za produkciju: es, fr, nl, bg, mk, sl** — po jedan iz svakog pojasa, pokriva raspon 0/8→7/8 blok B okidanja.

Usput: Ollama-trošak i broj poziva **ne koreliraju** (Flaviova korekcija) — gemma4 (104k poziva) nosi <1% sedmičnog troška, glm (3k poziva) nosi 25%. Isti obrazac kao qwen (s172). Odluka: mjeriti poslije, ne predviđati prije, za Ollama pitanja.

**Krug 2 — `parapoc3_*`/`parapoc32_*`/`parapoc33_*` (komadi 60, prelaz 4→2 radnika, 6501-6760).**
Flavio je "ponovo zeznuo komade od 60" — pogrešan broj radnika za budžet, pa zaboravljen interval (parapoc32 dupli opseg), pa suženje liste jezika. `already_done()` je zaštitio bazu — parapoc32 duplikat je završio normalno ali brzo (5-7 faza umjesto 13, jer je većina već postojala). Prvi pravi test 2 naspram 4 radnika na istom opsegu (af/mk/es): **~1.7-1.9× brže po poslu sa 2 radnika** — RAM kontencija (s164/s165 hipoteza) potvrđena mjerenjem, ne samo teorijom.

**Krug 3 — `parapoc34_*` (24 fajla, komadi 60, 2 radnika, 6-jezična lista, 6801-7100).**
Potvrđuje raniju listu (es/fr/nl/bg/mk/sl), isti redoslijed težine. Vrijeme i blok-B stopa niži nego kod kruga 1 čak i uz veći komad — ali dio toga je pozicija teksta, ne samo broj radnika (vidi §3).

## 3. DB-driven analiza težine — knjiga 12 (Moby Dick)

Flaviova ideja: prosječna sudijina ocjena pobjednika po poziciji = težina segmenta (paradoks: povremeni pad = problem, dosljedan pad = osobina jezika, ne kvar). Sve iz baze (`v_pobjednici_full`, `bb_recenice`, `bb_prevodi_recenica`), nula iz logova. Puni izvještaj isporučen kao `analiza_tezine_k12.md` (Flaviov download, nije u gitu).

**Kritičan nalaz prije svega ostalog:** pozicije 1-488 u knjizi 12 **nisu proza** — naslovna strana + sadržaj (135 poglavlja × 2 reda) + Etymology/Extracts (Melvilleova zbirka citata). Prava priča ("Call me Ishmael.") počinje na **poziciji 489**. Flaviov primjer segmenta "100-200" je pogodio baš tu zonu (16 karaktera/2.7 riječi prosjek — očigledan artefakt strukture, ne proze). **Svaka buduća analiza pozicije u k12 mora isključiti poz. <489.**

Nalazi na 9.275 rečenica prave proze (poz. >489):
- Dužina rečenice ↔ ocjena: r=-0.211 (slabo-umjereno, stvarno, ne dominantno)
- Kriva težine kroz knjigu: raspon 0.937-0.952, najteže oko poz. 4200-4663
- Paradoks potvrđen po jeziku: **ro (rumunski) je pravi izuzetak** — najniža korelacija sa konsenzusom (0.529) + najveća varijansa odstupanja + 95 "upadanja" >0.15 ispod konsenzusa, dvostruko više od sljedećeg. **es/fr/bs/bg/mk najdosljedniji** (korelacija 0.66-0.71, malo upadanja).
- ja (japanski) poseban slučaj: niska korelacija sa konsenzusom ALI i niska varijansa — dosljedno drugačiji obrazac, ne nasumičan.
- Vrijeme root faze (created_at delte) **ne korelira sa dužinom rečenice** (sve korelacije ~0) — trošak je dominantno fiksni overhead po pozivu. sr/de/hr/it (najstarija, potpuno pokrivena grupa) **2.5-3× sporiji po rečenici** od ostalih — vjerovatno artefakt perioda/uslova rada, ne težine (ne korelira sa njihovom pozicijom u §consistency tabeli).

**Direktna provjera ograde iz §2:** poz. 6001-6400 naspram 6801-7100, svih jezika — B je stvarno lakši/kraći (score +0.002, dužina -7%), ali **premalo da objasni** veličinu efekta iz §2 (pad blok-B stope sa 4-7/8 na 1-3/4). Broj radnika ostaje vjerovatno dominantan uzrok, pozicija je stvaran ali sekundaran doprinos — potvrđeno mjerenjem, ne samo ogradom.

**Session lekcija:** Claude je prvi put analizirao samo Flaviove "iz stomaka" brojeve (100-200 vs 500-600) i **zaboravio pravu motivaciju** (6001-6400 vs 6801-7100 iz §2 ograde) dok Flavio nije eksplicitno vratio pažnju na to. Imenovano direktno, ispravljeno u istom potezu.

## 4. Vizuelni identitet za About — istraživanje (horizont, ništa implementirano)

Flavio je predložio grafičku (Ken Burns stil) prezentaciju Buchenberga kao projekta (ne romana — prvi pokušaj pomiješao dvije ideje, razjašnjeno). Kroz sesiju testirano 6 AI-generisanih video primjera (NotebookLM):
- Prvi krug (2 videa, "Buchenberg Translation" / "How AI Judges..."): kraći/portretni format s vektorskom paletom preferiran nad dužim "whiteboard doodle" formatom.
- Drugi krug ("Geometry of Meaning", tamni mod): najbolji koncept — vektorski uglovi, "Anchored Mutation" dijagram (poklapa se sa ANALIZA.md terminologijom), pošten "STRUCTURAL CONTEXT NOT MEASURED" pečat. Regenerisan u svijetlom modu — ispalo 4 nedosljedna stila u istom videu.
- Napisan precizan prompt (zaključana paleta krem/ugalj/koralna, zabrana miješanja tehnika, imenovani kadrovi za zadržati) za ponovnu generaciju.
- Treći krug (2 nova videa): kratki format pogodio paletu tačno, ali **vratio se u tamno ~25s unutra** — potvrđuje da model ne drži instrukciju do kraja duže generacije. Dugi format opet skliznuo u whiteboard-doodle žanr, samo prebojen — sugeriše da **dužina videa bira porodicu stila nezavisno od prompta**.

**Odluka:** odustati od dugog formata za ovu namjenu; kratki format (75-80s) je jedini koji je ikad pogodio blizu cilja. Referentni kadar za buduću implementaciju: frame 240 iz "Geometry of Meaning" (svijetli mod) — podebljana flet tipografija, krem+koralna, rastavljena geometrija.

Dva probna Claude-artefakta napravljena uzgred (Moby Dick tema, pa ispravno Buchenberg-pipeline tema) — demonstracija koncepta, ne finalni dizajn.

## 5. Sonda — efekat redoslijeda unutar batcha (nastavak s170)

Flavio je pitao da li je "pozicija unutar batcha" (ne samo pozicija u knjizi) uzeta u obzir kao faktor težine. Nije bila — i pri provjeri koda otkriveno (ponovo, Claude je zaboravio) da `BATCH_SIZE=20` (base) i `REFINE_BATCH_SIZE=5` šalju više rečenica u JEDNOM pozivu, numerisano — model ih vidi zajedno u istom kontekstu.

Flavio se sjetio da je ovo već mjereno u s170 (`sandbox_batch_ponavljanje.py`) — Claude nije, dok nije eksplicitno zamoljen da pretraži prošle sesije. Nalaz s170, rekonstruisan: 5 rečenica ponovljenih 4× u JEDNOM pozivu → **100% klonova**, oba rasporeda (isprepleteno/blokovi), oba jezika (hr/de) — kopiranje iz konteksta pobjeđuje `repeat_penalty` ubjedljivo. Odvojenim pozivima: 23-47% klonova. Zaključak tada: batch je JEDNA odluka, ne 20 nezavisnih; sastav batcha mijenja sam prevod (ne samo klonove).

**Nova sonda ove sesije** (`src/sandbox_redosled_paketa.py`, READ-ONLY): Flaviov dizajn — 4 runde na istih 20 rečenica (k22, poz. 2000-2019, hr+de): original (O1) → promiješano (S2) → original ponovo (O3, bazni šum za O) → isto promiješano ponovo (S4, bazni šum za S). Pokrenuto sa `nohup` (real Ollama pozivi, ~4 min ukupno).

**Rezultat — dvije različite priče:**
- Sličnost teksta (kosinus): baseline (unutar-O, unutar-S šum) naspram unakrsnog (O×S) — **t=4.73, p=0.00003, visoko značajno**. Sastav batcha mjerljivo mijenja formulaciju, potvrđuje i produbljuje s170.
- Sudijina ocjena: S-grupa blago viša od O-grupe u OBA jezika nezavisno (hr -0.023, de -0.011), ali **p=0.19, nije statistički značajno** na n=20 po jeziku.

**Zaključak:** mešanje pouzdano mijenja RIJEČI, ne pouzdano mijenja KVALITET (na ovom uzorku). Za kaskada ideju: mešanje kao izvor raznolikosti — potkrijepljeno. Kao izvor boljeg kvaliteta — nije potkrijepljeno, treba mnogo veći uzorak (stotine rečenica) da se razdvoji od šuma (sd~0.07-0.08 naspram izmjerene razlike ~0.02).

Puni izvještaj: `sonda_redosled_paketa.md` (Flaviov download, nije u gitu). Log: `logs/sandbox_redosled_paketa.log`.

## Greške ove sesije (za ledger)

1. **`create_file` alat piše u Claude-ov lokalni sandbox, NE na foxuno server.** Prvi pokušaj pisanja `sandbox_redosled_paketa.py` je "uspio" lokalno, ali fajl nije postojao na serveru — otkriveno odmah pri provjeri sintakse, ispravljeno heredoc-om prije ijednog pokretanja. Nijedna šteta, ali pravilo (već postojeće u napomeni) je prekršeno uprkos tome što je poznato.
2. **Kalkulator obrazac, dva puta u istoj sesiji:** (a) Scheduler tema, (b) analiza samo doslovnih brojeva koje je Flavio "iz stomaka" naveo, uz zaborav prave motivacije (pozicioni konfaund iz §2). Oba puta ispravljeno tek nakon eksplicitnog upozorenja, ne samostalno.
3. **Zaboravljena postojeća sonda (s170)** — Claude je predložio "novu" analizu (kloniranje/redoslijed unutar batcha) kao da pitanje nikad nije postavljeno, dok Flavio nije podsjetio da je već mjereno.

## Stanje na kraju sesije (health check)

Korpus: **50.624** rečenice, **2.134.313** prevoda, **415.832** pobjednika (raste iz Flaviove produkcije tokom sesije, krugovi 1-3 iz §2). Ollama sedmično: **91.6%** — Flavio svjesno ostavlja preostalih ~8% za manje/kraće testove (uklj. sondu iz §5).

## Sljedeća sesija — otvoreno

1. **Implementacija nove kaskada skripte "sa mešanjem"** — na osnovu §5 nalaza (mešanje = raznolikost, ne dokazano poboljšanje kvaliteta). Dizajn nije počet.
2. **Ponoviti sondu iz §5 na mnogo većem uzorku** (stotine rečenica) sljedeći sedmični Ollama ciklus — trenutni nalaz o kvalitetu (p=0.19) je neuvjerljiv zbog n=20, ne zbog odsustva efekta.
3. **Komadi od 80** — najavljeno da slijede, još nije rađeno/analizirano.
4. **About vizuelni identitet** — kad Flavio dobije skuplju regeneraciju "Geometry of Meaning" u svijetlom modu (sutra), uporediti sa jeftinijom; birati konačan referentni stil prije bilo kakve prave implementacije.
5. BPT implementacija i treći-svijet (glm temp split) i dalje čekaju, nepromijenjeno iz s174/s159.

---

*Flavio & Claude · Buchenberg · sesija 176 · 16. avgust 2026.*
