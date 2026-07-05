# Session 112 — KONCEPT.md: identitet pipeline-a, eliminacija sufiksa, kompletna implementaciona mapa

**Datum:** 5. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Konceptualni opis "kako projekt radi" kao izvor istine za refaktor — apstrakcija od konkretnih imena modela, faze kao svojstvo, eliminacija `-refine` sufiksa. Identifikacija (ne implementacija) svega što treba promijeniti.

---

## Health snapshot (početak)
- bb_recenice: 38.333 · bb_prevodi_recenica: 1.328.860 · bb_prev_recenica: 257.736 (rast od s111 očekivan — noćni procesi)
- Git ulaz: buchenberg 871b7fa (s111), buchenweb e1278f7 (s108.4). BB_VERSION s108.4.
- Health check čist, sve zeleno.

## Kontekst
Flaviova inicijativa: web opisi previše direktno vežu imena modela; prevod više nije jedan nego višefazni (bazni + opcionalni refine); refine treba identifikovati strukturirano (koji model, koja faza), ne kroz ime. Redoslijed: opis → audit skripti/sheme → implementacija → tek onda web.

## 1. `docs/KONCEPT.md` — novi kanonski dokument (glavni proizvod sesije)
Šest sekcija: princip takmičenja (imena modela = parametri, ne arhitektura) · minimumi kao identitet (≥2 LLM bazna faza, ≥1 MT, tačno 1 sudija, tačno 1 embedder, 0.4:0.6, argmax) · model = model + konfiguracija (svjesna ER odluka) · faze kao iterabilnost procesa · identifikacija porijekla kao trojka (model, konfiguracija, faza) · posljedice po implementaciju.

**Ključne Flaviove odluke ugrađene u koncept:**
- Identitet = minimumi + proces, NE komponente (retirement lekcija: svaka komponenta zamjenjiva)
- Refine = iteracija istog procesa, ne nova komponenta (ista mašina, seed je parametar ulaza)
- **Apsolutni pobjednik = najbolji preko SVIH faza** (ne pobjednik posljednje faze — Claudeova prva formulacija bila pogrešna, korigovana)
- Minimum u refine fazi = **1 model** (konkurencija već postoji u bazenu; korekcija ranijih formulacija)
- NLLB samo u baznoj fazi (deterministički, bez sidra), ali njegov kandidat punopravan u ukupnom bazenu
- Numeracija ostaje 1-bazna: faza 1 = base, refine od 2
- Sufiks `-refine` = istorijski artefakt brzine koji je postao kočnica ("sufikse smo koristili da budemo brzi, a sada smo zbog njih spori u razvoju")

## 2. Nalazi audita (šema + skripte + web)
- **`bb_modeli`:** UNIQUE (naziv, temperatura) postoji → mora postati (naziv, temperatura, faza_id). Legacy redovi id 2,4,6–9 imaju `faza_id=NULL` (era prije koncepta faza) → UPDATE na 1 + SET NOT NULL (i zbog UNIQUE semantike — NULL se ne poredi).
- **Ključno pojednostavljenje:** redovi 12/13 se samo **preimenuju** (FK na `id` se ne mijenja) — ~1,33M prevoda netaknuto. Trojka postaje prirodni ključ tabele.
- **`bb_03`:** refine mod već ide preko `--refine` flaga, NE preko sufiksa; sufiks služi samo lookup-u i `.replace()` na l.358. Izmjena mala: `--faza N` arg, lookup +faza_id, replace nestaje. Zapažen tihi default temp (run_refine.sh ne šalje `--temp`).
- **Exporti:** bez logike na sufiksu, ali **ne iznose fazu u JSON** — poslije preimenovanja kandidati faza 1/2 nerazlučivi → `bb_xray_export.py` dobija `faza` polje.
- **Web:** nema JS logike na sufiksu (prikaz je vizuelan, iz imena u JSON-u); reader legenda (l.358) i nav.js proza ("two refine models", 5 jezika) hardkoduju sufiks i broj — web korak.

## 3. Kompletna implementaciona mapa (redoslijed)
- **Korak 0:** backup baze
- **Korak 1 (shema, jedan blok):** faza_id NULL→1 (id 2,4,6–9) · SET NOT NULL · ADD `aktivan` boolean DEFAULT true + false za legacy i stare modele · UNIQUE → (naziv, temperatura, faza_id) · rename 12/13 (skidanje sufiksa)
- **Korak 2 (skripte):** `bb_03` (`--faza`, lookup, briše replace, eksplicitni temp) · `run_pipeline.sh` + `run_refine.sh` (petlje čitaju aktivne modele po fazi iz baze) · `bb_08_sudija.py` (OCJENJIVANI_MODELI → upit nad aktivan; `bb_08_sudija1.py` se briše) · `health_check.py` · `bb_xray_export.py` (+faza u JSON) · `bb_01_init_lookup.py` (nizak prioritet)
- **Korak 3:** test malog opsega kroz cijeli lanac (base + refine + sudija + pobjednik)
- **Korak 4 (web, poslije testa):** reader legenda + faza prikaz; nav.js proza po KONCEPT-u bez brojeva, svih 5 jezika
- **Trajno pravilo (u KONCEPT-u):** buduće ADD COLUMN ovog tipa uvijek s DEFAULT prve faze

## Odluke (Flavio)
1. **Zamjenski par: gemma3:27b + ministral-3:8b** — prihvaćen bez daljeg testa (s110 neodlučivost = razlike male; koncept čini buduću korekciju trivijalnom kroz `aktivan` toggle)
2. **Bez minimalne zamjene — sve u jednom dahu:** refaktor + zamjena zajedno, gotovo prije 15. jula
3. Mapa u session dokument, KONCEPT ostaje principijelan

## Stanje na izlazu
- Kod: `docs/KONCEPT.md` (novi, v1 + korekcija §6 nakon nalaza o shemi) → commit
- Baza: NETAKNUTA (samo čitanje: bb_modeli sadržaj + `\d`)
- Web: NETAKNUT → BB_VERSION ostaje s108.4
- README: §9 s112 snapshot red, §14 referenca na KONCEPT.md i odluku

## Sljedeće
1. **Implementaciona sesija ("jedan dah"):** koraci 0–3 mape — backup, shema, skripte, test. Rok: prije 15. jula.
2. Korak 4 (web) poslije uspješnog testa.
3. Otvoreno iz s107/s108 nastavlja se (brojači faze 2 nad view slojem, stats dvije tabele — napomena: refaktor im mijenja podlogu na bolje, faza čista u shemi).

---

*Flavio & Claude · Buchenberg · session 112 · 5. jul 2026.*

---

## DODATAK (5. jul 2026, kasnije istog dana) — drugi retirement talas

Nova Ollama Cloud informacija (email Flaviu): kompletna lista modela koji se povlače 15. jula 2026. **Odluka o paru gemma3:27b + ministral-3:8b iz ove sesije postaje nevažeća** — oba su na listi.

Puna lista povučenih (s Ollama preporukama):
- deepseek-v3.1:671b → deepseek-v4-flash
- deepseek-v3.2 → deepseek-v4-flash
- devstral-2:123b → mistral-large-3:675b
- devstral-small-2:24b
- ministral-3:14b
- ministral-3:3b
- ministral-3:8b
- gemini-3-flash-preview → minimax-m3
- gemma3:12b → gemma4:31b
- gemma3:27b → gemma4:31b
- gemma3:4b → gemma4:31b
- glm-4.7 → glm-5.2
- glm-5 → glm-5.2
- minimax-m2.1 → minimax-m3
- qwen3-coder-next → qwen3.5:397b
- qwen3-coder:480b → qwen3.5:397b

Posljedice:
- Cijele gemma3 i ministral-3 porodice nestaju — prisilna dekorelacija: novi prevodioci dolaze iz stranih familija (s102 "diverzifikacija o tom potom" postaje obavezna)
- Sudija gemma4:31b NIJE na listi (Ollama ga čak preporučuje kao gemma3 zamjenu — za nas neupotrebljivo kao prevodilac dok je sudija, dok postoji izbor)
- Redovi 14–17 u bb_modeli (registracija s110) mrtvi prije ulaska u produkciju
- KONCEPT.md i implementaciona mapa NETAKNUTI — mijenja se samo podatak (imena), ne arhitektura; drugi talas u nedjelju dana potvrđuje ispravnost principa "identitet = minimumi + proces"

Nove Flaviove odluke:
- Ranija preferencija veličine (~12B) više ne važi — bitna je upotrebljivost u produkciji, ne veličina
- Pretplata aktivna — besplatni resursi nisu više ograničavajući faktor (ali ni pretplata nije bezgranična)
- Sudija/takmičar u istom modelu (različite konfiguracije/uloge) nije tabu — ali dok postoji izbor, koristimo izbor
- Smjer: pronaći **dva ne-misleća (non-thinking) modela** kroz sandbox sondu (s109 alat, građen tačno za ovo)

---

## DODATAK 2 (5. jul 2026) — sonda novih kandidata i odluka o paru

Sandbox sonda (s109 alat) pušteno model po model, jezik hr, `--no-think` na mislećim kandidatima. Ispravka poziva: `--models` prima JEDAN string s razmakom kao separatorom unutar navodnika (npr. `--models "m1 m2"`), ne više argumenata.

**Capability filter (/api/show, 14 preostalih kandidata):** samo mistral-large-3:675b je nativno ne-misleći; svi ostali nose `thinking` capability → drugi test-kriterij: poštuje li model `think:false`.

**Prvi krug (6 modela):**

| model | think:false | tok | sec | temp | zastavica |
|---|---|---|---|---|---|
| mistral-large-3:675b | nativno ne-misleći | 10 | 1.4 | razlika | mystery→secrets drift |
| deepseek-v4-flash | poštuje | 12 | 0.9 | identično | — (najbolji round-trip) |
| glm-5.2 | poštuje | 13 | 0.9 | razlika | drift kao mistral |
| minimax-m3 | IGNORIŠE (384 tok, think_len 1234) | 384 | 4.4 | — | OTPADA (obrazac kao gpt-oss s109) |
| qwen3.5:397b | poštuje | 16 | 0.7 | identično | "vrelo" — semantička greška (moor) |
| kimi-k2.6 | poštuje | 15 | 1.1 | razlika | rod ("je bilo" umjesto "je bila") |

**Drugi krug (temp-identično modeli, Flaviovo pravilo — jedna rečenica nije dokaz):**
- deepseek-v4-flash: temp identično PONOVO + prevod identičan prvom krugu od riječi do riječi → efektivni determinizam s ugašenim thinkingom; njegova druga temperatura bila bi plaćeni duplikat (2×2 temp shema ne radi)
- qwen3.5:397b: temp identično ponovo, ALI prevod različit između krugova ("vrelo" greška se nije ponovila) — varijansa između runova postoji, unutar runa temperature ne razdvajaju

**Aliasi (Flaviova provjera):** qwen3.5:cloud / qwen3.5:397b-cloud = qwen3.5:397b; gemma4:cloud / gemma4:31b-cloud = gemma4:31b — ista veličina/familija, već testirani → izbačeni po pravilu "testirano → izbaci". Nijansa: /api/show za gemma4 lista `thinking` capability iako ga s109 sonda mjeri kao ne-mislećeg — capability kaže šta model MOŽE, sonda šta RADI po defaultu; ponašanje sudije nepromijenjeno.

**gemma4 manje veličine (Flaviova provjera library stranice):** gemma4:12b/26b/e2b/e4b = "not found" na api.ollama.com — cloud tag važi samo za 31b; manje veličine su download-za-lokalno (12B LLM na CPU nepraktičan za produkciju, za razliku od NLLB 600M). Otpadaju.

**ODLUKA (Flavio, "nema sumnje"): novi par = mistral-large-3:675b + glm-5.2.**
Obrazloženje: oba temp-živa (2×2 shema se čuva bez izmjene strukture), oba čista bez kvalitativnih zastavica, oba u rangu starih etalona po trošku (10–13 tok, ~1s), različite familije (Mistral/Zhipu — prava dekorelacija), mistral nosi kontinuitet Mistral loze. Rezerve: deepseek-v4-flash (#1 — najbolji round-trip, ali temp-mrtav; KONCEPT dozvoljava ulazak s jednom konfiguracijom), kimi-k2.6 (#2 — rod-greška).

Kvalitet para formalno presuđuje sudija u koraku 3 implementacione mape (test malog opsega). Implementaciona sesija koristi ovaj par u koraku 1 (registracija u bb_modeli + aktivan) — sve ostalo iz mape nepromijenjeno.
