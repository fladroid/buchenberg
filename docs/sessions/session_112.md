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
