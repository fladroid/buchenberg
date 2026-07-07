# WEB-FAZA1 — Priprema tekstualnih izmjena web prezentacije

Radni dokument za FAZU 1 (samo tekst + prevodi + vidljivi elementi: menu, title).
Tehnička implementacija = FAZA 2 (zaseban prolaz, "u jednom dahu").
HTML fajl x.html ostaje x.html — mijenja se samo prikazani naslov, ne ime fajla.

**Metod:** stranica po stranica. Cross-cutting nalazi (važe za sve) → sekcija GLOBALNA PRAVILA.

---

## GLOBALNA PRAVILA (otkrivena tokom rada, važe za SVE stranice)

### G1 — HTML hardkod fallback mora pratiti i18n rječnik (otkriveno na index.html)
Trajni princip iz s115 (nijedan model se ne imenuje u web prezentaciji) primijenjen je
na i18n RJEČNIK u nav.js, ali NE i na HTML hardkod fallback u samim stranicama.
HTML hardkod je no-JS fallback — ali JS ga pregazi tek kad se učita. Do tada (i za
korisnike bez JS-a, i za pretraživače/preview) vide se STARA imena modela.
→ PRAVILO: kad i18n ključ očistimo od imena, isti tekst mora se očistiti i u HTML
  hardkodu iste stranice. Inače hardkod i rječnik protivriječe jedan drugom.
→ Zahvaćeno na index.html: how-desc, how-desc2, pillar-judge, pillar-refine
  (hardkod još kaže "Gemma 3 12B / Ministral 3 14B / NLLB-600M / Gemma 4 31B").

### G2 — Odnos "title tag" ↔ "menu tačka" ↔ "vidljivi naslov" (iz STRANICE.md)
Tri različita mjesta, mogu se razići. Kod svake stranice provjeriti sva tri.
Poznati neskladi (STRANICE.md s116): art (nema _title ključ), books (<title>="Books"
≠ h1="Library"), stats (menu "X-Ray Stats" ≠ naslov "X-Ray Statistics").
→ Odluke o svakom donosimo per-stranica niže, ali obrazac je globalan.

---

## STRANICA: index.html (menu: Home)

### Status i18n rječnika: ČIST ✅
Nijedan `index` ključ (tagline, hero_desc, sec_how, how_desc, how_desc2, pillar_bt,
pillar_judge, pillar_refine, pillar_winner, opensource) ne imenuje model — potvrđeno
grep-om (s115 posao stoji). Uloge opisane, ne komponente.

### Preostali problem: HTML hardkod fallback još imenuje modele (vidi G1)
Za FAZU 2 (tehnički): sinhronizovati hardkod tekst u index.html s već-čistim i18n
vrijednostima za: how-desc (l.42-44), how-desc2, pillar-judge (l.78 "Gemma 4 31B"),
pillar-refine. Tekst za kopirati POSTOJI u nav.js EN bloku — samo prepisati hardkod
da mu odgovara. Nema novih prevoda (rječnik već preveden na 5 jezika).

### Title / naslov: OK, bez izmjene
`<title>Buchenberg — MT lab</title>` — brend, ne imenuje model. Hero brend+tagline
umjesto h1 (namjerno, landing). Ništa za mijenjati u fazi 1.

### Tekstualne izmjene (sadržaj): NEMA
Home je već prošao kroz s108+s115. Sadržajno kompletan i konzistentan s KONCEPT-om.

### Zaključak za index.html
Faza 1 (tekst/prevodi): ništa novo za pisati.
Faza 2 (tehnički): jedna stavka — G1 hardkod sync (bez novih prevoda).

---

## STRANICA: about.html (menu: About)

### Odluka o imenima modela: SVJESNI IZUZETAK (Flavio, s118)
Za razliku od Home (s115, imena uklonjena), about ZADRŽAVA imena — ali uokvirena.
Razlog (Flaviov): about je edukativna stranica; imena prvih modela pomažu da se
koncept lakše i jednostavnije shvati na konkretnom primjeru. Ne krši se nijedno
pravilo — pravila i kvalitet definisani su MINIMUMIMA (KONCEPT §2), a minimum ne
zabranjuje konkretnu ilustraciju iznad njega. Uvodni okvir (novi ključ
about_p_models_note) eksplicitno kaže: ovo su imena PRVIH modela, zamjenjivih;
trajno je minimum/konfiguracija/uloga. Time about postaje jedini dozvoljeni
izuzetak od s115 principa — svjestan i obrazložen, ne nesklad.

### i18n rječnik: imenuje modele (očekivano, po odluci ostaje)
about_p_llm1 (Gemma/Ministral), about_p_llm2/3 (NLLB), tabela modela (HTML hardkod:
gemma3:12b/ministral-3:14b/nllb-600M/gemma4:31b), pipeline dijagram (judge=Gemma4:31b).
Po okviru iznad — OSTAJU kao ilustracija prvih modela. NE diramo ih u fazi 1.
> ⚠️ Napomena za budućnost: tabela prikazuje POVUČENI par (ne aktuelni mistral-large-3
> + glm-5.2). Po okviru "prvi modeli" to je tehnički OK (jesu prvi), ali vrijedi
> razmisliti treba li tabela nositi napomenu "(prvi modeli)" da ne zavara. Flaviov poziv.

### NOVA SEKCIJA: Self-refinement (tekst POTVRĐEN — EN + DE/IT/HR/SR)
about.html trenutno NE spominje refine/faze uopšte (opisuje samo baznu fazu).
Dodaje se nova sekcija POSLIJE "The pipeline" (poslije about_pipeline_outro).
Naslov "Self-refinement — a further round of the same pipeline" rješava "sve je
pipeline" (refine JESTE pipeline, nastavak unaprijed, ne prikačen poslije).

Pet novih i18n ključeva. Pun tekst svih 5 jezika (POTVRĐENO, izvor istine za Fazu 2):
- about_p_models_note  — okvir o imenima (ide u sekciju Models, prije tabele)
- about_h_refine       — naslov nove sekcije
- about_p_refine1..4   — refine proza (vidi TEKST niže)

Pozicija: about_p_models_note → uvod "Models" (prije tabele modela);
about_h_refine + about_p_refine1..4 + dijagram → POSLIJE "The pipeline"
(poslije about_pipeline_outro).

#### TEKST — EN
**about_p_models_note:** The models named below are the ones we <strong>started with</strong>. Model names are not part of the architecture — they are parameters: replaceable, and subject to withdrawal by a provider without notice. We have already swapped them more than once, for technical and cost reasons. What is permanent is not the name but the shape of the competition — the <strong>minimum number</strong> of competitors, their <strong>configuration</strong>, and their <strong>role</strong>. We keep the names of our first models here because the concept is easier to grasp through a concrete example.

**about_h_refine:** Self-refinement — a further round of the same pipeline

**about_p_refine1:** The translation above is the <strong>base phase (Phase 1)</strong> — candidates built from the original alone. It runs once per sentence. From there the process moves <strong>forward</strong> into refinement: after Phase 1 you can add Phase 2, then Phase 3, and so on — a phase is never re-run, only followed by the next one.<br><br>What makes a refine phase different is its <strong>seed</strong>: each new candidate is built from the original <strong>plus the current absolute winner</strong> — the single best translation the system has produced so far, across every phase played. The model is handed the best answer to date and asked to better it, staying within grammatical space while exploring. This is <strong>anchored mutation</strong> — the LLM as a grammatically safe mutation operator. This seed is also why refinement <strong>cannot precede</strong> the base phase: with no winner yet, there is nothing to anchor to.

**about_p_refine2:** This is <strong>self-refinement in the literal sense</strong>: the system reaches for nothing outside itself. It feeds its own accumulated concept and its own best results back into itself, and improves on them. Every refine phase stands on the shoulders of every phase before it.

**about_p_refine3:** Refinement is not a new component — it is the <strong>same competition</strong> turned on the system's own output. Same judge, same score, same winner rule. A phase winner is not automatically the final answer: the <strong>absolute winner is the best candidate across all phases played</strong>, drawn from the combined pool.

**about_p_refine4:** Our choice, above the minimum: the identity of the project requires only <strong>one model</strong> in a refine phase. We use <strong>two, at the highest temperature only</strong> — high temperature pushes toward freer, more adventurous phrasing, exactly what mutation needs; a low-temperature refine would cling to the anchor and defeat the purpose. The <strong>dedicated MT model takes no part in refinement</strong>: it is deterministic, so re-running it would only repeat the same sentence. Its base-phase candidate stays a full competitor in the combined pool through every phase.

#### TEKST — DE
**about_p_models_note:** Die unten genannten Modelle sind jene, mit denen wir <strong>begonnen</strong> haben. Modellnamen sind nicht Teil der Architektur — sie sind Parameter: austauschbar und jederzeit von einem Anbieter ohne Vorwarnung zurückziehbar. Wir haben sie aus technischen und Kostengründen bereits mehr als einmal ausgetauscht. Beständig ist nicht der Name, sondern die Form des Wettbewerbs — die <strong>Mindestzahl</strong> der Teilnehmer, ihre <strong>Konfiguration</strong> und ihre <strong>Rolle</strong>. Wir behalten hier die Namen unserer ersten Modelle, weil sich das Konzept an einem konkreten Beispiel leichter erfassen lässt.

**about_h_refine:** Selbst-Verfeinerung — eine weitere Runde derselben Pipeline

**about_p_refine1:** Die obige Übersetzung ist die <strong>Basisphase (Phase 1)</strong> — Kandidaten allein aus dem Original. Sie läuft einmal pro Satz. Von dort bewegt sich der Prozess <strong>vorwärts</strong> in die Verfeinerung: nach Phase 1 kann Phase 2 folgen, dann Phase 3, und so weiter — eine Phase wird nie wiederholt, nur von der nächsten gefolgt.<br><br>Was eine Verfeinerungsphase ausmacht, ist ihr <strong>Seed</strong>: jeder neue Kandidat entsteht aus dem Original <strong>plus dem aktuellen absoluten Gewinner</strong> — der besten Übersetzung, die das System bisher hervorgebracht hat, über alle gespielten Phasen hinweg. Das Modell erhält die bisher beste Antwort und soll sie übertreffen, im grammatikalischen Raum bleibend und dabei erkundend. Dies ist <strong>verankerte Mutation</strong> — das LLM als grammatikalisch sicherer Mutationsoperator. Dieser Seed ist auch der Grund, warum Verfeinerung der Basisphase <strong>nicht vorausgehen kann</strong>: ohne Gewinner gibt es nichts zu verankern.

**about_p_refine2:** Dies ist <strong>Selbst-Verfeinerung im wörtlichen Sinne</strong>: das System greift nach nichts außerhalb seiner selbst. Es speist sein eigenes gesammeltes Konzept und seine eigenen besten Ergebnisse in sich zurück und verbessert sie. Jede Verfeinerungsphase steht auf den Schultern jeder Phase davor.

**about_p_refine3:** Verfeinerung ist keine neue Komponente — es ist derselbe <strong>Wettbewerb</strong>, gerichtet auf die eigene Ausgabe des Systems. Derselbe Richter, dieselbe Bewertung, dieselbe Gewinnerregel. Ein Phasengewinner ist nicht automatisch die endgültige Antwort: der <strong>absolute Gewinner ist der beste Kandidat über alle gespielten Phasen</strong>, gezogen aus dem gemeinsamen Pool.

**about_p_refine4:** Unsere Wahl, über dem Minimum: die Identität des Projekts verlangt nur <strong>ein Modell</strong> in einer Verfeinerungsphase. Wir verwenden <strong>zwei, nur bei höchster Temperatur</strong> — hohe Temperatur drängt zu freieren, gewagteren Formulierungen, genau was Mutation braucht; eine Verfeinerung bei niedriger Temperatur würde am Anker kleben und den Zweck verfehlen. Das <strong>dedizierte MT-Modell nimmt an der Verfeinerung nicht teil</strong>: es ist deterministisch, ein erneuter Lauf würde nur denselben Satz wiederholen. Sein Basisphasen-Kandidat bleibt durch jede Phase ein vollwertiger Teilnehmer im gemeinsamen Pool.

#### TEKST — IT
**about_p_models_note:** I modelli indicati di seguito sono quelli con cui <strong>abbiamo iniziato</strong>. I nomi dei modelli non fanno parte dell'architettura — sono parametri: sostituibili e soggetti al ritiro da parte di un provider senza preavviso. Li abbiamo già sostituiti più di una volta, per ragioni tecniche e di costo. Ciò che è permanente non è il nome ma la forma della competizione — il <strong>numero minimo</strong> di concorrenti, la loro <strong>configurazione</strong> e il loro <strong>ruolo</strong>. Manteniamo qui i nomi dei nostri primi modelli perché il concetto è più facile da cogliere attraverso un esempio concreto.

**about_h_refine:** Auto-raffinamento — un altro giro della stessa pipeline

**about_p_refine1:** La traduzione sopra è la <strong>fase base (Fase 1)</strong> — candidati costruiti dal solo originale. Viene eseguita una volta per frase. Da lì il processo si muove <strong>in avanti</strong> nel raffinamento: dopo la Fase 1 si può aggiungere la Fase 2, poi la Fase 3, e così via — una fase non viene mai ripetuta, solo seguita dalla successiva.<br><br>Ciò che distingue una fase di raffinamento è il suo <strong>seed</strong>: ogni nuovo candidato è costruito dall'originale <strong>più il vincitore assoluto attuale</strong> — la migliore traduzione che il sistema ha prodotto finora, attraverso ogni fase giocata. Al modello viene consegnata la migliore risposta finora e gli si chiede di superarla, restando nello spazio grammaticale mentre esplora. Questa è <strong>mutazione ancorata</strong> — l'LLM come operatore di mutazione grammaticalmente sicuro. Questo seed è anche il motivo per cui il raffinamento <strong>non può precedere</strong> la fase base: senza un vincitore, non c'è nulla a cui ancorarsi.

**about_p_refine2:** Questo è <strong>auto-raffinamento in senso letterale</strong>: il sistema non attinge a nulla al di fuori di sé. Riporta in se stesso il proprio concetto accumulato e i propri migliori risultati, e li migliora. Ogni fase di raffinamento poggia sulle spalle di ogni fase precedente.

**about_p_refine3:** Il raffinamento non è un nuovo componente — è la stessa <strong>competizione</strong> rivolta all'output del sistema stesso. Stesso giudice, stesso punteggio, stessa regola del vincitore. Un vincitore di fase non è automaticamente la risposta finale: il <strong>vincitore assoluto è il miglior candidato attraverso tutte le fasi giocate</strong>, estratto dal pool combinato.

**about_p_refine4:** La nostra scelta, sopra il minimo: l'identità del progetto richiede solo <strong>un modello</strong> in una fase di raffinamento. Ne usiamo <strong>due, solo alla temperatura più alta</strong> — l'alta temperatura spinge verso formulazioni più libere e audaci, esattamente ciò di cui ha bisogno la mutazione; un raffinamento a bassa temperatura si aggrapperebbe all'ancora e vanificherebbe lo scopo. Il <strong>modello MT dedicato non partecipa al raffinamento</strong>: è deterministico, quindi rieseguirlo ripeterebbe solo la stessa frase. Il suo candidato della fase base resta un concorrente a pieno titolo nel pool combinato attraverso ogni fase.

#### TEKST — HR
**about_p_models_note:** Modeli navedeni ispod su oni s kojima smo <strong>počeli</strong>. Imena modela nisu dio arhitekture — ona su parametri: zamjenjiva i podložna povlačenju od strane providera bez najave. Već smo ih mijenjali više puta, iz tehničkih i financijskih razloga. Ono što je trajno nije ime nego oblik natjecanja — <strong>minimalni broj</strong> takmičara, njihova <strong>konfiguracija</strong> i njihova <strong>uloga</strong>. Ovdje zadržavamo imena naših prvih modela jer se koncept lakše shvaća kroz konkretan primjer.

**about_h_refine:** Samo-poboljšanje — daljnji krug iste pipeline

**about_p_refine1:** Prijevod iznad je <strong>bazna faza (Faza 1)</strong> — kandidati građeni samo iz originala. Izvodi se jednom po rečenici. Odatle se proces kreće <strong>naprijed</strong> u poboljšanje: nakon Faze 1 može se dodati Faza 2, pa Faza 3, i tako dalje — faza se nikad ne ponavlja, samo je slijedi sljedeća.<br><br>Ono što razlikuje fazu poboljšanja je njezin <strong>seed</strong>: svaki novi kandidat gradi se iz originala <strong>plus trenutni apsolutni pobjednik</strong> — najbolji prijevod koji je sustav dosad proizveo, kroz svaku odigranu fazu. Modelu se predaje dosad najbolji odgovor i traži se da ga nadmaši, ostajući u gramatičkom prostoru dok istražuje. To je <strong>usidrena mutacija</strong> — LLM kao gramatički siguran operator mutacije. Taj seed je i razlog zašto poboljšanje <strong>ne može prethoditi</strong> baznoj fazi: bez pobjednika nema se za što usidriti.

**about_p_refine2:** To je <strong>samo-poboljšanje u doslovnom smislu</strong>: sustav ne poseže ni za čim izvan sebe. Vraća vlastiti akumulirani koncept i vlastite najbolje rezultate natrag u sebe i poboljšava ih. Svaka faza poboljšanja stoji na ramenima svake faze prije nje.

**about_p_refine3:** Poboljšanje nije nova komponenta — to je isto <strong>natjecanje</strong> okrenuto prema vlastitom izlazu sustava. Isti sudac, isti score, isto pravilo pobjednika. Pobjednik faze nije automatski konačni odgovor: <strong>apsolutni pobjednik je najbolji kandidat kroz sve odigrane faze</strong>, izvučen iz zajedničkog bazena.

**about_p_refine4:** Naš izbor, iznad minimuma: identitet projekta zahtijeva samo <strong>jedan model</strong> u fazi poboljšanja. Mi koristimo <strong>dva, samo na najvišoj temperaturi</strong> — visoka temperatura gura prema slobodnijim, smjelijim formulacijama, upravo ono što mutacija treba; poboljšanje na niskoj temperaturi priljubilo bi se uz sidro i promašilo svrhu. <strong>Namjenski MT model ne sudjeluje u poboljšanju</strong>: deterministički je, pa bi ponovno pokretanje samo ponovilo istu rečenicu. Njegov kandidat iz bazne faze ostaje punopravni takmičar u zajedničkom bazenu kroz svaku fazu.

#### TEKST — SR (ćirilica; latinični tehnički termini ostaju latinicom)
**about_p_models_note:** Модели наведени испод су они с којима смо <strong>почели</strong>. Имена модела нису део архитектуре — она су параметри: заменљива и подложна повлачењу од стране провајдера без најаве. Већ смо их мењали више пута, из техничких и финансијских разлога. Оно што је трајно није име него облик такмичења — <strong>минимални број</strong> такмичара, њихова <strong>конфигурација</strong> и њихова <strong>улога</strong>. Овде задржавамо имена наших првих модела јер се концепт лакше схвата кроз конкретан пример.

**about_h_refine:** Само-побољшање — даљи круг исте pipeline

**about_p_refine1:** Превод изнад је <strong>базна фаза (Фаза 1)</strong> — кандидати грађени само из оригинала. Изводи се једном по реченици. Одатле се процес креће <strong>напред</strong> у побољшање: након Фазе 1 може се додати Фаза 2, па Фаза 3, и тако даље — фаза се никад не понавља, само је следи следећа.<br><br>Оно што разликује фазу побољшања је њен <strong>seed</strong>: сваки нови кандидат гради се из оригинала <strong>плус тренутни апсолутни победник</strong> — најбољи превод који је систем досад произвео, кроз сваку одиграну фазу. Моделу се предаје досад најбољи одговор и тражи се да га надмаши, остајући у граматичком простору док истражује. То је <strong>усидрена мутација</strong> — LLM као граматички сигуран оператор мутације. Тај seed је и разлог зашто побољшање <strong>не може претходити</strong> базној фази: без победника нема се за шта усидрити.

**about_p_refine2:** То је <strong>само-побољшање у дословном смислу</strong>: систем не посеже ни за чим изван себе. Враћа сопствени акумулирани концепт и сопствене најбоље резултате натраг у себе и побољшава их. Свака фаза побољшања стоји на раменима сваке фазе пре ње.

**about_p_refine3:** Побољшање није нова компонента — то је исто <strong>такмичење</strong> окренуто према сопственом излазу система. Исти судија, исти score, исто правило победника. Победник фазе није аутоматски коначни одговор: <strong>апсолутни победник је најбољи кандидат кроз све одигране фазе</strong>, извучен из заједничког базена.

**about_p_refine4:** Наш избор, изнад минимума: идентитет пројекта захтева само <strong>један модел</strong> у фази побољшања. Ми користимо <strong>два, само на највишој температури</strong> — висока температура гура ка слободнијим, смелијим формулацијама, управо оно што мутација треба; побољшање на ниској температури приљубило би се уз сидро и промашило сврху. <strong>Наменски MT модел не учествује у побољшању</strong>: детерминистички је, па би поновно покретање само поновило исту реченицу. Његов кандидат из базне фазе остаје пуноправни такмичар у заједничком базену кроз сваку фазу.

Ključne suštinske tačke (ispravke iz dijaloga s118):
- Faza se NE ponavlja ("repeatable" je bilo pogrešno) — ide se UNAPRIJED (faza 2->3->4),
  faza 2 se ne pokreće ponovo. Prevod 1-10 pa 1-20 = uradi samo 11-20.
- Seed (=apsolutni pobjednik) je SUŠTINSKA kvalitativna razlika refinea, i razlog
  zašto refine ne može prije baznog prevoda (nema pobjednika = nema sidra).
- "self-" istaknuto namjerno (Flaviov naglasak): samo-poboljšanje iz sopstvenog
  koncepta i dosadašnjih rezultata.

Dijagram (`<pre><code>`, stil postojećeg pipeline bloka): dvije kolone PHASE 1 /
PHASE 2 iste strukture (iste mašine, drugi seed), spajaju se u jedan zajednički
bazen -> isti sudija/score/pravilo -> apsolutni pobjednik preko svih faza (hrani
seed sljedeće faze).

#### DIJAGRAM (<pre><code>, stil postojećeg pipeline bloka)
```
PHASE 1  ·  base translation          PHASE 2  ·  refinement
──────────────────────────           ──────────────────────────
EN original                          EN original + absolute winner
     │                                        │   (seed)
     ▼                                        ▼
competing candidates                 re-translation / mutation
(≥ 2 LLMs + 1 MT model)              (LLMs only, highest temp)
     │                                        │
     └────────────────┬───────────────────────┘
                      ▼
        one combined pool — all candidates, all phases
                      │
                      ▼
        same judge · same score · same winner rule
                      │
                      ▼
        absolute winner = best across ALL phases
              (feeds the next phase's seed)
```

### Title / menu / naslov (G2): ČISTO
"About Buchenberg" ne imenuje model, nema nesklada u STRANICE.md za about.
Ništa za mijenjati.

### FAZA 2 zadaci za about.html (tehnika, u jednom dahu)
1. Upis 5 novih ključeva × 5 jezika = 25 unosa u nav.js (tačan tekst: sekcija TEKST iznad).
2. Pozicija: about_p_models_note u Models sekciju (prije tabele); refine sekcija
   (h + 4 pasusa + dijagram) poslije "The pipeline".
3. HTML: novi elementi s id-jevima + apply-linije u about.html inline scriptu.
4. G1 (globalno): postojeći hardkod imena — po okviru OSTAJU (izuzetak), ali
   provjeriti da hardkod fallback za NOVE ključeve odgovara rječniku.

### Zaključak za about.html
Faza 1 (tekst/prevodi): ✅ KOMPLETNO — okvir imena + refine sekcija, EN + 4 jezika
potvrđeno. Sljedeća stranica: stats.html.

---

## STRANICA: stats.html (menu: X-Ray Stats → Stats)

Napomena: ovo je OPIS šta Faza 2 (implementacija) treba uraditi. Sada se ništa
ne dira. Pri implementaciji koristiti KAKO-JeziciUI.md (i18n) i KAKO-KeyConcepts.md
(kartice) iz docs/.

### Title / menu / naslov (G2): TRI IZMJENE (Flavio, s118)
Rješava nesklad iz STRANICE.md (menu "X-Ray Stats" ≠ naslov "X-Ray Statistics").
Uklanja se "X-Ray" iz sve tri tačke → dosljedno Stats/Statistics.
- **Menu tačka:** "X-Ray Stats" → "Stats"  (NAV_I18N, 5 jezika)
- **`<title>`:** "X-Ray Stats — Buchenberg" → "Stats — Buchenberg"  (HTML head)
- **Naslov (h1, `stats_title`):** "X-Ray Statistics" → "Statistics"  (i18n, 5 jezika)

### stats_reading_note: preformulisati (tretman kao Home s115, NE about izuzetak)
Razlog za Home-put (bez imena), a ne about-izuzetak: about je čisto edukativan
(imena prvih modela pomažu razumjeti koncept), ali stats prikazuje ŽIVE podatke
gdje imena više nisu tačna. Winner tablica živo prikazuje novi par (glm-5.2,
mistral-large-3) uz zamrznute stare modele — imenovati gemma3/ministral u prozi
dok tablica pokazuje glm-5.2 je nesklad, ne pedagogija.

Trenutni tekst (svih 5 jezika) sadrži DVA problema:
1. **Imena modela:** "gemma3 and ministral", "NLLB" — skinuti, opisati po ulozi
   (general-purpose LLMs + dedicated MT model, isto kao Home/reader s115).
2. **Hardkodovani brojevi u prozi:** "38,333 English sentences", "9 books",
   "3 engines", "5 configurations" — ZASTARJELI i protivriječe živom funnelu tik
   iznad (funnel povlači total_sentences iz stats.json; health check s118 pokazuje
   50.624 rečenice, 12 knjiga — ne 38.333/9). Skinuti fiksne brojeve iz proze;
   broj rečenica nosi ŽIVI funnel, proza objašnjava samo ODNOS (zašto selected >
   source: jedan "prevod" = par rečenica–jezik, ne nova rečenica). Isti X-Ray
   princip kao imena: fiksni brojevi u prozi zastarijevaju, živi podatak ne.
> Flaviova nota: tekstovi su manje-više ok; brojevi se uvijek osvježavaju iz JSON-a
> koji generiše web_export; uvijek će se nešto mijenjati/dodavati/oduzimati.

### Hardkodirano u navesti — POPIS za Fazu 2 (ne dira se sad)
- **Funnel hardkod (HTML):** "9 books · Project Gutenberg", "5 configs × up to 14
  languages" — statični brojevi strukture; uskladiti sa živim stanjem ili
  generalizovati (isti razlog kao reading note).
- **JS `modelShortName()`** (l.~funkcija): prepoznaje samo gemma3/ministral/nllb/
  gemma4 → novi par (glm-5.2, mistral-large-3:675b) pada na `return model` (puni
  naziv, ružan prikaz). Treba proširiti ili preraditi da bude nezavisan od imena.
- **JS `modelClass()`**: iste 3 stare klase (model-gem3/min3/nllb) → nova imena
  bez boje. Vezano za CSS ispod.
- **CSS klase** (`.model-gem3/.model-min3/.model-nllb` u <style>): vezane za stara
  imena. Preraditi zajedno s modelClass.
- **subtitle (`stats_subtitle`)** spominje "Data is loaded live from translation
  JSON files" — provjeriti tačnost (od s99 čita agregirani stats.json, ne 126 tr_*).

### Key Concepts: OBRISATI 2 kartice (Flavio, s118)
Ukloniti iz data/concepts.json (pri implementaciji koristiti KAKO-KeyConcepts.md,
obavezno json.load validacija poslije):
- **"X-ray style art"** (wiki: X-ray_style_art)
- **"Rock Art and the X-Ray Style"** (wiki: Rock_Art_and_the_X-Ray_Style)
Napomena: ove kartice su dodane s96 na index/about/stats. Provjeriti pri
implementaciji s kojih stranica se tačno brišu (Flaviova odluka: navedene 2 kartice).

### Veći zadatak — ODVOJENO, NE u Fazi 1
"Stats dvije tabele" (by engine / by configuration s win_rate, s107/s108) je
strukturni/tehnički redizajn — zaseban budući prolaz, ne pripada Fazi 1.

### Zaključak za stats.html
Faza 1 (tekst/odluke): ✅ KOMPLETNO — odluke donesene i opisane gore. Nema novih
prevoda za pisati sada (reading note preformulacija = Faza 2, jer zavisi od
tehničke odluke o funnel/JS uskladi). Sljedeća stranica: books.html.

---

## STRANICA: books.html (menu: Library)

Napomena: OPIS za Fazu 2. Sada se ništa ne dira. Stranica zadovoljava —
svi podaci žive iz JSON-a (web_export). Nema imena modela nigdje (subtitle kaže
"produced by the Buchenberg pipeline" — uloga, ne komponente). Čisto.

### Title / menu / naslov (G2): DVIJE izmjene
Rješava nesklad iz STRANICE.md (<title>="Books" ≠ h1="Library", nedovršen rename s72)
PLUS otkriveni nesklad UNUTAR i18n rječnika (naslov znači različito po jeziku).
Koncept stranice (Flavio, s118): "Library" — SVE knjige su knjige (prevedene,
neprevedene, djelimično, fazno, djelimično fazno). Ne samo prevedene.

1. **`<title>`:** "Books — Buchenberg" → "Library — Buchenberg"  (HTML head, hardkod)
2. **`books_title` na DE/IT/HR/SR:** trenutno "Translated Books" (Übersetzte Bücher /
   Libri tradotti / Prevedene knjige / Преведене књиге) → uskladiti na "Library":
   - DE: "Bibliothek"
   - IT: "Biblioteca"
   - HR: "Knjižnica"
   - SR: "Библиотека"
   EN već "Library", menu već "Library". Cilj: naslov = "Library" na svih 5 jezika,
   dosljedno s menijem i konceptom.
   > HTML hardkod fallback <h1>Library</h1> već OK (EN); JS pregazi po jeziku.

### Sve ostalo: BEZ IZMJENE
subtitle, kartice, badges, word cloud modal, dugmad (Read/Gutenberg/NLP/Word cloud) —
sve zadovoljava. Svi brojevi/jezici/statusi žive iz books.json (web_export).

### Zaključak za books.html
Faza 1 (tekst/odluke): ✅ KOMPLETNO. Samo title/naslov usklada (Faza 2), bez nove
proze. Sljedeća stranica: nlp.html.

---

## STRANICA: nlp.html (menu: NLP)

Napomena: OPIS za Fazu 2 (ovdje: nema šta za implementirati).

### Nalaz: NAJČISTIJA stranica — BEZ IZMJENE
- **Imena modela:** NEMA nigdje (HTML/i18n/JS). Radi s originalnim EN tekstovima +
  NER podacima; backend (spaCy + normalizacija) se ne prikazuje korisniku. Ništa za skidati.
- **Title/menu/naslov (G2):** menu "NLP" = `<title>` "NLP — Buchenberg" (slažu se);
  h1 (`nlp_title`) = "Natural Language Processing" (opisni, prevedeno na 5 jezika).
  NIJE nesklad kao stats — menu i title su isti, naslov je namjerno opisniji
  (kratko u meniju, puno u naslovu). Flaviova odluka (s118): ostaviti sve isto.
- **i18n:** kompletan i dosljedan na svih 5 jezika (dugmad, tabele, tooltipovi, tipovi).
- **Sadržaj:** sve žive iz JSON-a (orig_*, ner_*, books.json). Bez hardkod brojeva strukture.

### Zaključak za nlp.html
Faza 1: ✅ NIŠTA ZA MIJENJATI. Sljedeća stranica: learn.html.

---

## STRANICA: learn.html (menu: Learn)

Napomena: OPIS za Fazu 2 (ovdje: nema šta za implementirati u Fazi 1).

### Nalaz: ČISTA stranica — BEZ IZMJENE (kao nlp)
- **Imena modela:** NEMA nigdje. Igre rade s prevedenim rečenicama iz tr_*.json —
  nikad ne spominju koji ih je model proizveo. Čisto.
- **Title/menu/naslov (G2):** menu "Learn" = `<title>` "Buchenberg — Learn" (slažu se);
  h1 (`learn_title`) = "Language Learning" (opisni, prevedeno 5 jezika). Isti obrazac
  kao nlp — menu i title isti, naslov namjerno opisniji. NIJE nesklad. Ostaviti isto.
- **i18n:** opsežan, kompletan na svih 5 jezika (labele, dugmad, pravila 4 igre).
- **Sadržaj:** sve žive iz books.json + tr_*.json. Bez hardkod brojeva strukture.

### Zabilježeno za Fazu 2 (opciono, NIJE dio čišćenja imena) — i18n propust
Neki UI stringovi hardkodovani na EN u JS-u umjesto kroz i18n → ostaju engleski
na drugim jezicima: showToast poruke ("Please select a language.", "Loading...",
"Not enough translated sentences." itd.), direction badge ("You will see English
as context and fill in ..."), match kolone ("English"/"Translation"), placeholder
("Click words below to build the sentence..."), "Sentence X of Y", "Score:",
"Attempts:", "matched", "pairs". Širi i18n zadatak — nezavisan od imena modela i
sadržaja. Flaviova odluka (s118): ne dirati sada; eventualno poseban i18n prolaz.

### Zaključak za learn.html
Faza 1: ✅ NIŠTA ZA MIJENJATI. Sljedeća stranica: geometry.html.

---

## STRANICA: geometry.html (menu: Geometry)

Napomena: OPIS za Fazu 2. Sada se ništa ne dira.

### Imena modela: DVIJE vrste, različit tretman (Flavio, s118)
1. **Sudija "Gemma4:31b"** u `geo_c4_p1` ("...a blind LLM judge (Gemma4:31b)") →
   IZBACITI samo "(Gemma4:31b)", ostaje "a blind LLM judge". Razlog: ZAMJENJIVOST
   (princip s115 — imena su parametri), NE zastarjelost. gemma4:31b je aktivan
   sudija (provjereno health check s118) — nije povučen kao prevodilački par.
   Na svih 5 jezika (geo_c4_p1 postoji u en/de/it/hr/sr).
2. **Embedder "multilingual-e5-large"** (`geo_banner`, `geo_subtitle`,
   `geo_measure_sub`) → ZADRŽATI. Razlog: (a) stvarni model koji stranica
   POKREĆE u browseru (Transformers.js, ~100 MB) — banner mora reći korisniku
   šta preuzima; (b) embedder je INVARIJANTA projekta (KONCEPT §2 "tačno 1
   embedder", README "UVIJEK e5-large"), ne prolazni parametar. Uklanjanje bi bilo
   netačno i besmisleno.

### NE dirati (Flaviova odluka s118)
- Broj "Five models" u geo_c4_p1 — NE dirati (nije traženo; ne nagađati).
- geo_c4 formula blok (HTML hardkod: composite/final/judge_avg) — tačan, ostaje.

### Title / menu / naslov (G2): ČISTO
menu "Geometry" / `<title>` "Geometry of Meaning — Buchenberg" / h1 "Geometry of
Meaning". Nema nesklada u STRANICE.md. Bez izmjene.

### Ostalo: čisto
Borges/Wittgenstein proza, cosine kartice (01-03), scatter, measure similarity —
bez imena prevodilačkih modela, konceptualno. Sadržaj iz geometry.json (živ).

### FAZA 2 zadatak za geometry.html
Jedna izmjena: geo_c4_p1 na 5 jezika — ukloniti "(Gemma4:31b)". Ništa drugo.

### Zaključak za geometry.html
Faza 1 (tekst/odluke): ✅ KOMPLETNO. Sljedeća stranica: art.html (posljednja).

---

## STRANICA: art.html (menu: Art)

Napomena: OPIS za Fazu 2. Sada se ništa ne dira.

### Naslov "Art" — STANDARDIZOVATI (Flavio, s118)
STRANICE.md nesklad: `<h1 class="bb-section-title">Art</h1>` hardkodovan u HTML-u,
BEZ id, BEZ i18n ključa — jedina stranica bez `_title` ključa. Naslov ostaje "Art"
na svim jezicima. ODLUKA: uraditi standardno kao sve ostale stranice.
- Dodati novi ključ `art_title` u nav.js, svih 5 jezika:
  - EN: "Art" · DE: "Kunst" · IT: "Arte" · HR: "Umjetnost" · SR: "Уметност"
- Dati `<h1>` id (npr. `art-title`) + apply-liniju u art.html inline script
  (ids mapa: 'art-title':'art_title'). HTML hardkod fallback ostaje "Art" (EN, no-JS).
- Time art se uklapa u isti obrazac kao about/stats/geo/learn/nlp (prevedeni naslov).

### Imena modela — dvije vrste, isti tretman kao geometry
1. **Embedder "multilingual-e5-large"** (`art_card_buchenberg_p1`, svih 5 jezika) →
   ZADRŽATI. Invarijanta (KONCEPT §2), i Fingerprints eksponat ga STVARNO pokreće u
   browseru (Transformers.js). Isti razlog kao geometry.
2. **JS `MODEL_COLORS`** (Tapestry legenda, "Model" mod): hardkoduje povučene modele
   (gemma3:12b@0.8, ministral-3:14b@0.8, nllb-600M@0.0 + temp varijante). Novi par
   (glm-5.2, mistral-large-3) nema boju -> pada na '#888'. FAZA 2 TEHNIKA (isti problem
   kao stats modelShortName/modelClass). Ne dira se sad.

### Title / menu (G2)
`<title>` "Art — Buchenberg" / menu "Art". Menu ima prevod (NAV_I18N), `<title>`
ostaje EN brend (kao ostale stranice). Naslov h1 se standardizuje (gore).

### Ostalo: čisto
Kandinsky/Scriabin/Borges/Wittgenstein proza — konceptualno, bez imena prevodilačkih
modela. Tri eksponata (Tapestry/Sound/Fingerprints) — sadržaj iz tr_*.json (živ).

### FAZA 2 zadaci za art.html
1. Novi ključ `art_title` × 5 jezika + `<h1>` id + apply-linija (standardizacija naslova).
2. `MODEL_COLORS` hardkod povučenih modela — isti tretman kao stats (nezavisno od imena
   u prezentaciji; vizuelna legenda). Preraditi da bude nezavisno od imena ili proširiti.

### Zaključak za art.html
Faza 1 (tekst/odluke): ✅ KOMPLETNO. **Sve stranice obrađene (9/9).**

═══════════════════════════════════════════════════════════════
## FAZA 1 ZAVRŠENA — sažetak (s118)

Svih 9 stranica obrađeno. Nalaz po stranici:
- **index.html:** rječnik čist (s115); Faza 2: G1 hardkod sync.
- **about.html:** okvir o imenima (svjesni izuzetak) + NOVA Self-refinement sekcija
  (tekst EN+4 jezika + dijagram, gotovo). Najveći tekstualni posao.
- **stats.html:** title/menu/naslov (X-Ray Stats->Stats, Statistics); reading note
  Home-put (bez imena+brojeva); Key Concepts -2 kartice; hardkod popis za F2.
- **books.html:** title->Library; books_title uskladjen na "Library" 5 jezika.
- **nlp.html:** BEZ IZMJENE (najčistija).
- **learn.html:** BEZ IZMJENE; zabilježen i18n propust (hardkod EN u JS) za budući prolaz.
- **geometry.html:** izbaciti (Gemma4:31b) iz geo_c4_p1; e5-large ostaje.
- **art.html:** standardizovati naslov (art_title × 5 jezika); e5-large ostaje;
  MODEL_COLORS = F2 tehnika.

Globalna pravila (G1 hardkod sync, G2 title<->menu<->naslov) primijenjena po stranici.
Trajni princip s115 (bez imena prolaznih modela) primijenjen; about = svjesni izuzetak;
e5-large (embedder) = invarijanta, uvijek ostaje.

**SLJEDEĆE: Faza 2 (tehnička implementacija, "u jednom dahu").** Redoslijed po stranici
iz zadataka gore. Koristiti KAKO-JeziciUI.md (i18n) i KAKO-KeyConcepts.md (kartice).

---

## STRANICA: reader.html (menu: Reader)

Napomena: OPIS za Fazu 2. Sada se ništa ne dira. Puni implementacioni plan: vidi
DIO ispod (samodovoljan — bez zavisnosti od artefakata).

### Kontekst: reader je bio POTPUNI i18n izuzetak (s77/s78)
reader.html ima VLASTITI `const I18N = {...}` objekat (5 jezika) ugrađen u stranicu,
odvojen od centralnog NAV_I18N u nav.js. Posljedica: svaka i18n izmjena mora se raditi
dvaput ili reader "ispadne" (mijenjaš NAV_I18N — reader ne gleda tamo). To se danas
i desilo (reader preskočen u prvom prolazu). Flaviova odluka s118: standardizovati
ono što je dosljedno; izuzetke izričito navesti.

### NAVEDENI IZUZETAK — ostaje (NE diramo)
**X-Ray legenda = SAMO ENGLESKI, hardkodovana.** Dogovoreno na početku X-Ray
implementacije (isti obrazac kao Key Concepts kartice — namjerno EN, ne prevoditi).
Cijela legenda + X-Ray Full mod tekstovi ostaju EN hardkod. Ovo NIJE propust —
svjesna odluka. Poslije migracije reader dosljedno ima dva režima:
  (a) nav + kontrole → nav.js i18n (5 jezika) = STANDARD
  (b) X-Ray legenda/Full → EN hardkod = NAVEDENI IZUZETAK (kao Key Concepts)

### A1 — sitna izmjena (hardkod, jedan red)
Judge Average red u legendi: "...assigned by the LLM judge (gemma4:31b)." →
"...assigned by the LLM judge." Razlog: zamjenjivost (s115), kao geometry geo_c4_p1.
NIJE zastarjelost (gemma4:31b aktivan sudija). Legenda ostaje EN hardkod → prosta
izmjena jednog reda, NE kroz rječnik. e5-large (Translation Score red) OSTAJE (invarijanta).

### B1 — migracija nav+kontrole u NAV_I18N (reader_ prefiks, vrijednosti iz lokalnog I18N)
14 ključeva × 5 jezika (preseljenje, ne nov prevod):
reader_books, reader_translations, reader_select, reader_show_original, reader_sentences,
reader_author, reader_language, reader_sentences_lbl, reader_pipeline, reader_source,
reader_infobox_title, reader_gutenberg, reader_original, reader_untranslated.
ISPRAVKA usput (ODLUKA s118 = DA): SR reader_author/reader_language su latinica
("Autor"/"Jezik") u lokalnom I18N dok je ostatak SR ćirilica → ispraviti na
"Аутор"/"Језик" (dosljednost SR bloka, pravilo koje već slijedimo).

### B2+B3 — brisanje + prepravka u reader.html
- Obrisati cijeli lokalni `const I18N = {...}`.
- Obrisati ručno punjenje nav labela (navLinks[0..5].textContent = t('nav_*')) —
  nav.js SAM puni nav (buildHeaderHTML l.1491-1493 + l.1540 na promjenu jezika).
- `const t = key => (I18N[state.uiLang]||I18N.en)[key]||key;` →
  `const t = key => BB_NAV.t('reader_'+key) || BB_NAV.t(key) || key;`
  (legenda EN hardkod NIJE t() poziv → nepogođena).
- Ukloniti vlastiti .bb-lang-btn handler → `BB_NAV.onLangChange = applyI18n`
  (inače dupli listeneri s nav.js).
- apply na DOMContentLoaded + BB_NAV.onLangChange.

### FAZA 2 zadaci za reader.html
1. A1 (jedan red hardkoda).
2. B1 (14 reader_ ključeva × 5 jezika u NAV_I18N; SR author/language ćirilica).
3. B2+B3 (obrisati lokalni I18N + ručni nav; prepraviti apply na BB_NAV.t).
4. Metoda: KAKO-JeziciUI §7 (Python heredoc, assert count==1, strukturni trap
   `" },`, ćirilica literalno). node NE postoji.
5. Browser test: 5 jezika — nav/kontrole/infobox rade; legenda OSTAJE EN (potvrda izuzetka).
6. Ažurirati KAKO-JeziciUI.md §2/§10 + STRANICE.md (reader nav+kontrole = standard,
   legenda = navedeni EN izuzetak).

### Zaključak za reader.html
Faza 1 (odluke): ✅ KOMPLETNO. **Svih 9 stranica sada stvarno obrađeno (9/9).**

═══════════════════════════════════════════════════════════════
## ISPRAVKA "9/9" (s118)
Prethodni "FAZA 1 ZAVRŠENA" sažetak iznad je BIO PREURANJEN — reader.html preskočen
u prvom prolazu (uhvaćeno provjerom broja STRANICA sekcija: 8 zaglavlja = 8 fajlova,
reader fali). Sada dopunjen. Stvarno stanje: svih 9 stranica obrađeno.

### Redoslijed Faze 2 (ODLUKA s118): "u jednom dahu", sve zajedno
Kao s114 refaktor. Backup → stranice po redu (index G1 hardkod sync → about nova
sekcija+okvir → stats title/reading-note/KeyConcepts → books title → geometry Gemma4
→ art naslov standard → reader migracija) → JEDAN browser test svih stranica × 5 jezika
→ JEDAN commit set (buchenweb) + BB_VERSION bump + push verifikacija.
nlp i learn: bez izmjene (osim learn i18n propust — zaseban budući prolaz, ne sad).
