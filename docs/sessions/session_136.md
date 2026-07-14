# Session 136 — 14. jul 2026.

## Fokus
Kontrola kompletnosti prevoda (nivo 1a + 1b), analiza log fajlova k22/k23/k24
faza-2 runova, popravka rupe k24, stats.html coverage kolona "Ukupno".

## Zdravlje na početku
50.624 rečenica · 1.548.480 prevoda · 302.168 pobjednika — sve zeleno.
BB_VERSION s135. buchenberg 13a809d, buchenweb f4b13b1.

## Urađeno

### 1. Analiza logova jučerašnjih runova (k22/k23/k24, f2, 1–100)
- k22, k23: čisti (retry-ji se sami oporavili, "pokušaj 1/3" nefatalni)
- k24: glm-5.2 pukao na it batch 81–100 (ReadTimeout Ollama, 2 retry-a,
  nehvatana iznimka srušila proces prije sr) → rupa: it 80/100, sr 20/100.
  mistral restartovan čisto (novi prevodi_knjige_id 13675–13678, svi 100/100).

### 2. v_status_faza_model (NOVI VIEW)
Long-format, granularnost (knjiga, jezik, faza, model, temperatura), COUNT
DISTINCT recenica_id, derivat v_prevodi_full. Detekcija rupa: MAX(prevedeno)
po (knjiga, jezik, faza) grupi = očekivano; svaki model ispod = rupa.
- Definicija rupe (Flavio): brojčano neslaganje, nivo 1; pozicijski view
  ("koje tačno rečenice") = nivo 2, gradi se TEK kad zatreba dijagnoza.
- Ograničenje (eksplicitno): view vidi "počeo pa nije završio", NE vidi
  "trebalo je postojati a nikad nije počelo" (model bez ijednog reda u grupi).
- Za algoritam rupa=1 i rupa=999M su isti nalaz — nema praga, nema filtera.

### 3. Nivo 1a — provjera opsega u bb_03_prevod.py
Na kraju svakog jezika: COUNT nad zadatim --od/--do intervalom (interval
tog runa, NE MIN/MAX iz podataka!) vs očekivano (do-od+1) → ✅/❌ u log.
Testirano u produkciji (vidi 5).

### 4. Nivo 1b — check_kompletnost() u health_check.py
Nova sekcija 2b, koristi v_status_faza_model + MAX logiku. Kolone uključuju
knjiga_id i faza_id (Flaviov zahtjev — bez ID-a teško identifikovati).
Nalaz: 87 rupa, SVE faza 1 (base), SVE retired modeli (gemma3/ministral).
ODLUKA (Flavio): rupe ostaju na miru dok imamo pobjednike. Prio 2.

### 5. Popravka k24 rupe — run 1–110, de hr it sr, faza 2
run_faza.sh, PID 163692, log faza2_k24_20260714_092858.log. Rezultat:
8/8 "Provjera opsega [1-110]: 110/110 OK" (2 modela × 4 jezika), nula
grešaka. DB potvrda kroz view: svih 8 redova = 110. Nova provjera 1a
validirana u produkciji istim runom.

### 6. stats.html — kolona "Ukupno" u Coverage bloku
Uzrok Flaviovog pitanja ("Hound/ro 3852 na statsu, a rupa 200?"):
coverage broji POBJEDNIKE po rečenici (bar jedan kandidat dovoljan),
ne kompletnost po modelu — dvije različite istine, obje tačne.
- bb_web_export.py: coverage upit + kn.id, spoj s get_books() totalima,
  novi "total" ključ u stats.json
- nav.js: stats_col_total_sent ×5 jezika (Total/Gesamt/Totale/Ukupno/Укупно)
- stats.html: kolona Ukupno u coverage tabeli, sortabilna
- Verifikovano: Hound/ro 3852/3852, Hound Copy/ro 500/3852. Browser OK.

### 7. Usputna epizoda — test na krivoj kombinaciji
Claude predložio "besplatan" test 1a na Hound/hr glm-5.2@0.1 f1 uz pogrešnu
pretpostavku da already_done() sve preskače — kombinacija nije postojala,
10 stvarnih Ollama poziva. Podaci legitimni ali neplanirani → obrisani
(prevodi_knjige_id 13706, DELETE 10+1, FK provjeren prije brisanja).
LEKCIJA: prije test-runa provjeriti da kombinacija (knjiga,jezik,model,
temp,faza) POSTOJI u bazi — "kompletno" za stare modele ne znači ništa
za nove.

## Protokol — prekršaji (3. put zabilježeno)
Claude 2× u istoj seriji izvršio komandu bez prikaza i OK (bb_web_export
izmjena; stats.html izmjena — odmah nakon priznanja prvog prekršaja).
Flavio tolerantan ("nastavi, posle se vrati na protokol"), ali obrazac
je AKTIVAN rizik — s125, s135, s136.

## Konceptualno — kontekst-injection (bez implementacije)
Flavio pitao mišljenje a priori o NER→prompt za prevođenje. Rezime s124
odluka potvrđen: sudija slijep/fiksan (kontekst SAMO prevodiocu), NER+
relacije = infrastruktura, PREDUSLOV = baseline mjerenje, ti/vi dinamično.
Claudeovo mišljenje: opšti score se NEĆE pomjeriti (headroom mali,
pejsmejker), ali klasa grešaka nevidljiva sentence-level metrici
(ti/vi, skriveni rod, konzistentnost kroz knjigu) je stvarna meta —
poboljšanja mjerljiva samo ciljanom evaluacijom, ne BLEU/kosinus/sudija.

### Skica baseline analize ti/vi (za budući session)
1. INVENTAR (SQL+regex, 0 LLM): dijaloške rečenice s 2. licem →
   veličina uzorka = gornja granica koristi. Oba pisma za SR.
2. KONZISTENTNOST (SQL+Python, 0 LLM): po govornik→adresat paru
   (J&H/Flatland, DocRE parovi) izbroj ti vs vi oblike; mješavina bez
   narativnog razloga = greška. Ne treba ground truth. Slaba tačka:
   atribucija govornika (dijalozi bez "reče X").
3. TAČNOST (uzorak 50–100 + presuda): DocRE relacija → očekivano ti/vi;
   presuda ručno ili odvojen LLM anotator (mali uzorak, Flavio pregleda).
Korak 1 = jedna sesija, sam odgovara "vrijedi li ovo uopšte".

## Završno stanje
- BB_VERSION s136 (sufiks skinut pred commit)
- v_status_faza_model u bazi (CREATE VIEW, bez backupa — view, ne DDL nad podacima)
- 87 poznatih rupa faza 1 — prihvaćeno, prio 2
- k24 f2 kompletan 1–110 svi jezici/modeli

## Sljedeći koraci
- ti/vi baseline (skica gore) — kandidat za zaseban session
- stats model-nivo prikaz na portalu (predloženo, neodlučeno)
- Nivo 2 pozicijski view — tek kad zatreba dijagnoza
