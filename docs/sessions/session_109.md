# Session 109 — Sandbox sonda za ponašanje Ollama modela (izazvano retiranjem gemma3:12b + ministral-3:14b)

**Datum:** 3. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Ollama najavila povlačenje gemma3:12b i ministral-3:14b za 15. jul 2026. Umjesto ad-hoc zamjene — izgraditi alat koji ponašanje BILO KOG modela mjeri sistematski, da promjena modela postane "uobičajen posao". Koncept prvo, implementacija fleksibilna i otporna.

## Health snapshot (početak)
- bb_recenice: 38.333 · bb_prevodi_recenica: 1.186.730 · bb_prev_recenica: 229.990
- Git ulaz: buchenberg 9b6ea25 (s108), buchenweb e1278f7 (s108.4). BB_VERSION s108.4.
- Korpus narastao od s108 (~1,122M→1,187M) — Flaviovi noćni procesi, očekivan rast.
- Big Four/Frankenstein/Dracula/Moby/R&J odmakli daleko preko README snapshot tabele.

## Povod: retirement notice
Ollama Cloud najavila (screenshot Flavio):
- gemma3:12b — retire 15. jul 2026
- ministral-3:14b — retire 15. jul 2026
Tačno 2 od 3 cloud prevodilačka modela (4 od 5 konfiguracija model×temp). Sudija gemma4:31b i lokalni NLLB NISU pogođeni. Postojeći ~1,19M prevoda ostaje validan — samo NOVI runovi trebaju zamjenu.

## Koncept (Flaviov reframe — najvažniji dio sesije)
Cilj NIJE izabrati dva modela — cilj je da mijenjanje modela bude RUTINA. Modeli su prolazni; sposobnost zamjene je trajna. X-Ray na vlastiti alat: koliko nas košta bilo koja promjena modela? Prevodilac = zamjenjiva komponenta; sudija/embedder/formula/šema fiksni.

## X-Ray na bb_03 (gdje su imena modela zakucana)
grep pokazao: prevodilac je VEĆ skoro potpuno zamjenjiv.
- ollama_chat/prevedi_batch/back_prevedi_batch primaju model+temp kao PARAMETRE — nema `if "gemma" in model` grananja.
- Jedina tvrda grana: NLLB vs cloud (is_nllb = args.model=="nllb-600M") — ispravna granica (drugi supstrat), ne krutost.
- Refine vezan stringom (.replace("-refine","")) — radi za bilo koju familiju uz -refine konvenciju.
- ollama_chat čita samo message.content → za thinking modele automatski pokupi čist prevod (thinking je odvojen field), IGNORIŠE reasoning. Pipeline radi s thinking modelima BEZ izmjene.

## Izgrađeno: src/sandbox_model_probe.py (180 red)
Read-only sonda ponašanja (NE kvaliteta). Ne dira bazu/bb_modeli/pipeline/produkciju — samo Ollama /api/chat. Test set: 5 hardkodovanih EN rečenica. Preslikava STVARNI prompt iz bb_03 (single/batch/back). Prima --models (lista), --jezik, --no-think.
Mjeri 5 pitanja: (1) čistoća izlaza, (2) thinking + eval_count + sec [trošak], (3) temp 0.1vs0.8 reakcija, (4) batch N/N preživljavanje, (5) round-trip EN→L→EN.
Baseline modeli (gemma3/ministral) = ETALON; kandidati se čitaju naspram njih.
Bug uhvaćen i popravljen: sonda čitala OLLAMA_KEY bez load_dotenv() → 401 na SVE (i etalone koje znamo da rade). Fix: dodat `from dotenv import load_dotenv; load_dotenv()` kao u bb_03 — samodovoljna, ne zavisi od ručnog `. .env`.

## Nalazi sonde (hr)

| model | think | evalC | sec | čistoća | batch | napomena |
|-------|-------|------:|----:|---------|-------|----------|
| gemma3:12b (etalon) | ne | 14-15 | ~1.5 | čist | 5/5 | odlazi 15.jul |
| ministral-3:14b (etalon) | ne | 12 | ~1 | čist | 5/5 | odlazi 15.jul |
| gpt-oss:20b | DA | 251 | 2.5 | čist | 5/5 | thinking ZAGLAVLJEN |
| nemotron-3-nano:30b | DA | 907 | 6.0 | čist | 5/5 | thinking gasiv |
| ministral-3:8b | ne | 9 | 0.9 | čist | 5/5 | unutar-familije |
| gemma3:27b | ne | 11 | 1.1 | čist | 5/5 | unutar-familije |
| gemma4:31b (sudija) | ne | 10 | 0.8 | čist | 5/5 | digresija |

## Ključna otkrića
1. **Thinking, NE veličina, je glavni množilac troška.** gemma4:31b i gemma3:27b su veliki a jeftini (10-11 tok) jer nisu thinking. nemotron:30b isti red veličine ali 907 tok SA thinkingom. "Veći=sporiji" važi, ali pravi rez je thinking on/off.
2. **think:false se poštuje PO MODELU, ne univerzalno:**
   - gpt-oss:20b IGNORIŠE (i dalje 312 tok) — trošak zaglavljen.
   - nemotron:30b POŠTUJE (907→10 tok, 6s→0.7s) — ali prevod postaje GORI ("It was a secret place"). Thinking kupuje kvalitet; gašenje ga skida s cijenom kvaliteta. Trade-off koji samo sudija mjeri.
3. **Svi kandidati tehnički čisti** (content/thinking razdvojeni, batch 5/5) → pipeline kompatibilan bez izmjene. Koncept "prevodilac = zamjenjiv" POTVRĐEN.
4. **Pretpostavka o 8b inferiornosti dovedena u pitanje:** ministral-3:8b dao NAJBOLJI round-trip od svih na test-rečenici ("The moor was a place of mystery" netaknut). Jedna rečenica ≠ dokaz, ali dovoljno da 8b ne odbacimo unaprijed — pusti kroz sudiju.
5. **Dva puta, izmjeren trade-off:** unutar-familije (gemma3:27b/ministral:8b) = jeftin drop-in, ponašanje kao etaloni, ALI nije dekorelacija. Strani rod (gpt-oss/nemotron) = prava dekorelacija ALI thinking-trošak. Dekorelacija košta; sigurnost je jeftina.

## Odluka (Flavio)
Za produkcijski test uzimamo **unutar-familije par: gemma3:27b + ministral-3:8b** ("novi mistral i gemma3"). Jeftin drop-in, sonda potvrdila ponašanje. Kvalitet tog para → sudija, sljedeća sesija.

## Stanje na izlazu
- Kod: src/sandbox_model_probe.py (nova, read-only sonda) → commit.
- Baza: NETAKNUTA (sonda ne piše). Korpus živ (Flaviovi procesi).
- Web: NETAKNUT → BB_VERSION ostaje s108.4.
- README: novi §15 Ollama API how-to + sonda u §7 + retirement napomena u §3 + s109 snapshot red u §9.

## Sljedeće
1. **Produkcijski mini-test kvaliteta** (fokus sljedeće sesije): gemma3:27b + ministral-3:8b kroz PRAVI bb_03+bb_08 na malom opsegu (npr. 25 rec × hr/de/it/sr), iz već-kompletne knjige (baseline postoji). Registracija u bb_modeli + faza_id. Head-to-head score vs stari pobjednici kroz v_prevodi_full — NE win-rate (selekcijski artefakt).
2. Ako kvalitet zadovolji → puna zamjena u produkcijskom workflowu prije 15. jula.
3. Otvoreno iz s107/s108 (nastavlja se): brojači faze 2 nad view slojem, web fazni pobjednik prikaz, stats dvije tabele.

---

*Flavio & Claude · Buchenberg · session 109 · 3. jul 2026.*
