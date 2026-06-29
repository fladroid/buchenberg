# Session 102 — 29. jun 2026.

**Fokus:** Self-refine kao X-Ray eksponat (Tema 2 iz s101 — ali drugačije razriješena). Refine prikaz u readeru učinjen vidljivim i objašnjenim; legenda dopunjena. Konceptualni preokret: refine NIJE neuspjeh, nego *anchored mutation* — LLM kao operator mutacije koji ostaje u gramatičkom prostoru. Pipeline nedirnut (Flavio gasi pozadinske procese pred full refine run).

## Onboarding snapshot (ulaz s102)
- Korpus: 38.333 rečenice, 962.570 prevoda, 189.870 pobjednika. Health 0:23, 92% CPU (s97 DB-fix se drži).
- Knjige prev=pobj na svih 14 jezika: Alice (1535), Flatland (1341), Jekyll & Hyde (1157).
- Git: buchenberg 6fa119d (s101), buchenweb 62a992c (s101). BB_VERSION s101.
- 7 uncommitted (buchenberg) = sve \`.bak\`/\`__fla__\` privremenjaci (Flaviova zona).

## Konceptualna diskusija — preokvirivanje s100 nalaza (Flavio)
- Flavio privučen "self-*" paradigmom (self-learning agenti, LLM koji pišu LLM, self-research). Suština: početno stanje → loop poboljšanja → bolje među/krajnje stanje.
- **Ključni Flaviov uvid:** kod evolucije nad jezikom NE možeš samo izmiješati riječi (crossover/mutacija razbija sintaksu) — moraju ostati gramatički ispravne. Self-refine to RJEŠAVA: **LLM = pametni operator mutacije koji garantuje da varijanta ostaje u gramatičkom prostoru.** Most koji je nedostajao za "evolucija nad jezikom".
- **Dvije mjere, dvije istine (razriješen prividni konflikt s s100):** s100 mjerio "refine pobjeđuje svoj seed head-to-head" → 0/100 (ostaje tačno). Flaviova svrha je DRUGA: "pomak ostaje u gramatičkom svijetu" → uspjeh (gemma3-refine sudija 0.851, gramatičan, smislen). Nalaz nije bio neuspjeh koncepta nego primjena mutacije gdje po pamfletu nema headroom-a (jak seed = pejsmejker; "vrijednost mutacije zavisi od cijene greške").
- **Refine ≠ raznolikost.** Refine = mutacija (lokalni pomak iz tačke). Raznolikost = diverzifikacija (nove tačke, šesti nezavisni model iz DRUGE familije). Dva odvojena GA operatora. Flavio se slaže s diverzifikacijom ali kao ZASEBNA tema.

## Odluka (Flavio — durable)
- **Self-refine ostaje kako jest.** Pobjednik se bira između svih 7 prevoda (\`bb_04\` argmax netaknut). Ništa se ne prepisuje, ne vraća base-seedovima, ne filtrira iz agregata. Refine je legitiman takmičar i ostaje pobjednik gdje god je pobijedio.
- **7 modela u winner-distribution = istina, prikazuje se kao istina.** (Opcije "filter u kodu" i "vrati pobjede base-seedovima" odbačene — druga je bila anti-X-Ray: tiho prepisivanje rezultata koje reader demantuje.)
- Razlog zašto je to čisto: reader pokazuje svih 7 kandidata + scoreove; ako bi baza rekla drugog pobjednika nego što formula pokazuje, sjenka i original se ne bi poklapali.

## Urađeno — A2 eksponat
- **Izviđanje (read-only):** \`bb_xray_export.py:get_all_candidates\` NEMA \`LIMIT 5\` ni filter modela → već generički vraća sve kandidate po rečenici (5 ili 7). Backend eksponata postojao od s100; refine kartice bile vidljive otkad su podaci ušli — ali NEME (bez objašnjenja).
- **reader.html render** podnosi N kartica (\`candidates.forEach\`, bez fiksnog 5). \`modelShort\` lanac \`.replace()\` slučajno ispravno daje \`gemma3-refine\`/\`ministral-refine\` (\`-refine\` nije ni u jednom replace patternu, preživi). Sreća, ne dizajn, ali radi.
- **reader.html legenda (2 izmjene, str.replace + assert count==1, em-dash bajt-verifikovan):**
  1. "Model" red dopunjen: spomen \`-refine\` varijanti (self-refine kandidati, isti model re-prevodi s pobjednikom kao referencom).
  2. Novi "Self-Refine" red: *anchored mutation*, rijetko pobjeđuje jak seed (anchor near-ceiling), ali pokazuje da vođena varijacija nad jezikom ostaje u gramatičkom prostoru — missing piece za evoluciju nad prevodom. Iskren X-Ray eksponat.
  - Engleski (cijela X-Ray legenda je goli HTML, NIJE i18n — reader inače ima \`t('...')\` na 35 mjesta; legenda je izuzetak/propust). Puna i18n legende = zaseban horizont.
- **\`bb_xray_export.py\` docstring fix:** "SVIH 5 kandidata" → "SVE kandidate (5 baznih + eventualni self-refine)". Kod ne laže, komentar je lagao — X-Ray ne trpi senku laži ni u komentaru.
- **Verifikacija uživo:** \`xray_19_hr.json\` raspodjela {5: 1057, 7: 100} — tačno (s1–100 ima refine). pos1 winner = \`gemma3:12b-refine\` (jedna od 36 win-rate pobjeda; head-to-head vs svoj seed i dalje 0/100 — pobijedio bazen, ne svoj seed). Flavio potvrdio u svim browserima: 7 kartica, imena čista, X-Ray radi, legenda vidljiva.
- BB_VERSION s101 → **s102.1** (intermedijarna za test; čista s102 pri commitu).

## Lekcije
- **Backend je već radio generički** — posao A2 nije bio prikaz nego OBJAŠNJENJE. Kartice su bile tu od s100, neme; legenda im je dala glas.
- **"Dvije mjere, dvije istine"** — isti eksperiment može biti neuspjeh na jednoj osi (head-to-head 0/100) i uspjeh na drugoj (gramatična mutacija nad jezikom). Pitaj ŠTA mjeriš prije nego proglasiš (ne)uspjeh.
- **Anti-X-Ray test za svaku "čistu" odluku:** ako bi potez sakrio/prepisao nešto što reader pošteno pokazuje — ne radi se. Sjenka mora pratiti original.
- **Provjeri bajtove prije str.replace s posebnim znakovima** (s101 ledger primijenjen: em-dash \`\u2014\` u "Meta NLLB — local", ne hyphen/en-dash; \`assert count==1\` + Python heredoc koji čita stvarni sadržaj umjesto kucanja iz glave).

## Stanje na izlazu
- Web izmjene: \`reader.html\` (legenda +2), \`nav.js\` (BB_VERSION). Backup: \`reader.html.bak_s102_refine\`.
- Backend: \`bb_xray_export.py\` (docstring).
- Pipeline NEDIRNUT. Korpus brojevi živi iz baze (health check ulazni).
- **NIJE još commitano** — čeka kraj sesije (BB_VERSION → s102 čisto, pa git oba repoa).

## Sljedeće (po prioritetu)
1. **Flaviov full refine run:** self-refine po 100 rečenica × sve knjige × svi jezici (Flavio vodi). Kad regeneriše X-Ray JSON, refine kartice + legenda zažive na cijelom korpusu automatski (sve napisano generički). Tada winner-distribution dobija refine kao punopravne kriške (ne više 2 sićušne iz jedne knjige) — prikaz postaje POŠTENIJI, nota i dalje korisna.
2. **60/40 sensitivity eksponat (horizont):** težine \`0.4 kompozitni / 0.6 sudija\` NIKAD ozbiljno testirane. Klizač težine u readeru za J&H hr (imamo svih 7 kandidata + komponente): "pri 60/40 pobjeđuje X, pri 50/50 Y, pri 40/60 Z". X-Ray u najčistijem obliku — pokazati koliko ishod ovisi o nepretestiranoj pretpostavci.
3. **Diverzifikacija — zaseban okvir (Flaviovo "o tom potom"):** "zašto ne odmah 9 modela (4 LLM × 2 temp + nllb)?". Odgovor iz pamfleta: vrijednost iz DEKORELACIJE familija, ne broja konfiguracija. 4. LLM iste loze + druga temp = korelisana greška (\`rho·sigma²\`). Pravi šesti glas = DRUGA familija (van gemma/ministral/nllb). Treba pripremiti i objasniti zasebno.
4. **Self-refine na SLABIM seedovima** (s100 horizont): apsolutni prag seed < 0.85 — jedini netestiran režim, jedini gdje mutacija ima headroom.
5. Ranije: length bucketing (NLLB), art.html v1, NLP relation extraction (leži od s90), \`bb_web_export\` v_pobjednici refaktor, OCJENJIVANI_MODELI → kolona \`grupa\` (s100, kad se gase procesi za ALTER).

---
*Flavio & Claude · Buchenberg · Session 102 · 29. jun 2026.*

## Dodatak — pokretanje self-refine (run_refine.sh)

**Ispravan poziv** (jedan jezik ili lista, jedna knjiga):
```bash
cd /home/balsam/buchenberg && PYTHONUNBUFFERED=1 nohup bash ./run_refine.sh \
  --knjiga 21 --jezici "pt ro" --od 1 --do 100 \
  > logs/refine_k21_ptro.log 2>&1 & echo "PID: $!"
```
- BEZ vanjskog `time` — skript ima `time` interno na svakom koraku (gemma3-refine → ministral-refine → sudija → pobjednik).
- Skript usporedo piše vlastiti timestamped log preko `tee` (`logs/refine_kNN_YYYYMMDD_HHMMSS.log`); vanjski `> ... 2>&1` je samo nohup kopija.
- `run_refine.sh` parsira `--knjiga --jezici --od --do`; `$JEZICI` ide nequoted u `--jezici $JEZICI` (lista "de hr it sr" se pravilno razdvaja). 2 modela (gemma3-refine, ministral-refine) @0.8, single, bez NLLB. `set -e`.

**Lekcija — dvostruki start (haos 09:04/09:07):** pokrenut DVAPUT (vjerovatno dupli enter/paste u terminalu), ne greška skripta. Dva refine procesa paralelno na isti cilj (k19 de/hr/it/sr) → oba zovu istu gemma3-refine na Ollama Cloud (jedna sesija!) + pišu isti (knjiga,jezik,model,opseg). Posljedica BLAGA jer `bb_03 --refine` ima ON CONFLICT zaštitu (provjereno: `n == distinct_rec` svuda, nula duplikata) i inkrementalni režim (`Preostalo: 0` → preskače već urađeno). Čišćenje: `pkill -f "bb_03_prevod.py.*refine"` + `pkill -f "run_refine.sh"` (NE dira base prevode — komande im ne sadrže "refine"). **Pravilo: jedan start, sačekaj "PID:", ne ponavljaj. Ne dva refine procesa istovremeno (Cloud = jedna sesija).**

**Verifikovano uživo:** jednojezični (af k19) i dvojezični (pt ro k21) pozivi rade besprijekorno — `Refine: N rečenica sa seedom` potvrđuje da refine nalazi pobjednika kao hint; inkrementalni preskok radi (af-gemma3-refine već postojao → `Preostalo: 0`, 13s; af-ministral-refine novo → 100 sa seedom). Flatland pt ima pobjednike za s1–100 (seed postoji).
