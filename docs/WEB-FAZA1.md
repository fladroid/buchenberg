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
