# Sesija 156 — 31. jul 2026.

**Fokus:** Bug fix iz s155 (Dio 4) — `bb_03_prevod.py` slao seed/pivot modelu čak i kad je prompt `base`, jer je grananje zavisilo samo od broja faze. Ispravljeno, dvostruko verifikovano na svježim opsezima (k22 741-780 i 781-820). Usput: ozbiljan komunikacijski nesporazum oko brisanja test podataka ("obriši sve" vs "obriši fazu 10"), razriješen kroz eksplicitno pojašnjenje; napravljen novi wrapper skript `run_root_gated.sh` + helper `bb_toggle_model.py`; dva nova KAKO referentna dokumenta.

---

## Zdravlje na početku sesije

Checklist proveden (project files → README → session_153/154/155 → health_check). Sve zeleno osim poznatih 272 rupa (historijske, faza 1, ostavljene namjerno) i `buchenweb` koji zaostaje (s152 vs backend s155 — očekivano, web nedirnut). Korpus na početku: 50.624 / 1.871.353 / 352.220. Oba repoa čista.

## Dio 1 — Bug fix

Kod je pregledan (`sed -n` na relevantnom dijelu `bb_03_prevod.py`) prije bilo kakve izmjene. Potvrđeno tačno ono što je s155 opisala: linija 458, `elif is_refine:` — zavisi isključivo od `args.faza >= 2`, ignoriše `PROMPT_NAZIV`. Gate/prag logika (`if is_refine: seed_map = ...`, ranije u istoj funkciji) ostaje namjerno vezana za broj faze — to je ispravno, jer odlučuje KOJE rečenice ulaze u pokušaj, ne da li se seed šalje.

Izmjena (Python `str.replace()` preko heredoc-a, po ledger konvenciji):

```diff
-                elif is_refine:
+                elif is_refine and PROMPT_NAZIV != 'base':
                     parovi = [(t, seed_map[rid][0]) for rid, poz, t in chunk]
```

Verifikovano: `py_compile` čisto, `git diff` pregledan (jednolinijski, tačan), `else` grana (koja sad hvata i "gated-base" slučaj) potvrđena da koristi `prevedi_batch()` — čist prevod originala preko `TPL_PREVOD_BATCH` (base prompt), bez seeda.

## Dio 2 — Komunikacijski nesporazum oko brisanja (dokumentovano iskreno)

Prije testa, trebalo je očistiti prethodne (mislabeled) test podatke iz s155 na k22 701-740. Prvi predlog Claudea protumačio je Flaviov raniji zahtjev ("obriši sve što je urađeno sa tim 40 rečenica") usko — kao "samo faza 10" — i izvršio DELETE ograničen na `pk.faza_id = 10` (80 redova). Flavio je tražio da se doda `bb_04_pobjednik.py` da se popuni "rupa" u pobjedniku nastalu brisanjem — i tu je počeo nesporazum: Flavio nije razumio zašto je pokretanje skripte koja bira pobjednika preduslov za brisanje (nije bio), a serija pitanja/odgovora se otegla preko više razmjena zbog nepreciznog jezika s Claudeove strane ("čistim", "ništa", "posljedica brisanja") koji je zvučao kontradiktorno.

Razriješeno kad je Flavio eksplicitno preformulisao zahtjev, potpuno bez ambiguiteta: **obriši SVE prevode za k22 701-740, sve faze, oba jezika-para** (Recept B iz novog KAKO dokumenta, vidi Dio 5), plus provjeri da je 741-780 zaista prazan. Oba izvršena, potvrđena brojevima:

```
DELETE FROM bb_prev_recenica_faza ... → DELETE 160
DELETE FROM bb_prev_recenica ...       → DELETE 137
DELETE FROM bb_prevodi_recenica ...    → DELETE 480
```

(480 = 40 rečenica × 4 jezika × 3 konfiguracije root faze [mistral@0.8, mistral@0.1, nllb@0.0] — root iz s155 Koraka 2 PLUS faza 10 iz s155 Koraka 6, sve zajedno.)

**Lekcija (upisana u novi `docs/KAKO-BrisanjePrevoda.md`):** kad neko kaže "obriši sve prevode za te rečenice", eksplicitno razjasniti da li se misli na jednu fazu ili kroz sve faze PRIJE izvršavanja bilo čega — ne pretpostavljati usko tumačenje. Cijeli razgovor dokumentovan bez ublažavanja jer je Flavio to eksplicitno tražio ("da ne bude sramota ako neko čita session dokumente").

## Dio 3 — Prvi test (k22, 741-780)

Root faza (suzena — glm isključen preko ručnog `UPDATE bb_faze_a1`) pokrenuta prvo, uspješno (120 prevoda/jezik, svi ocijenjeni, 40 pobjednika/jezik). Tool poziv za `run_faza.sh --faza 1 ...` je timeout-ovao na klijentskoj strani nakon nekog vremena — ALI proces je nastavio raditi na serveru (potvrđeno `ps aux`), jer nije bio pokrenut sa `nohup`. Nije ponovo pokrenut (izbjegnut paralelni duplikat) — samo praćen periodičnim `ps aux` provjerama do završetka (~28 min ukupno kroz prevod→sudija→pobjednik).

Glm vraćen u fazu 1 (`aktivan=true`), pa faza 10 pokrenuta — ovaj put ispravno, sa `nohup time ... > logs/*.log 2>&1 &`, po Flaviovom insistiranju da se izbjegne isti problem.

Rezultat, potvrđen i logom i bazom:

| jezik | gate otvoren | glm pobijedio |
|---|---|---|
| de | 6 | 4 |
| hr | 6 | 4 |
| it | 5 | 5 |
| sr | 8 | 8 |
| **ukupno** | **25/160 (15,6%)** | **21/25 (84%)** |

Prompt header u logu potvrđen `prompt: base` za oba temperature — bug fix radi kako treba, seed nije poslan modelu.

## Dio 4 — `run_root_gated.sh` + `bb_toggle_model.py` (nova infrastruktura)

Flavio je pitao kojim skriptom bi sam pokretao "root pa faza 10" — takav skript nije postojao (otvorena stavka iz s155). Napravljena dva nova fajla, u stilu postojećih `run_faza.sh`/`bb_faza_info.py`:

- **`src/bb_toggle_model.py`** — mali helper, `UPDATE bb_faze_a1 SET aktivan=X WHERE faza_id=N AND model_id=(model po nazivu)`, koristi psycopg2 + `.env` (isti obrazac kao `bb_faza_info.py`), exit 1 ako kombinacija ne postoji.
- **`run_root_gated.sh`** — wrapper: isključi glm (faza 1) → `run_faza.sh --faza 1` (suzen root) → `run_faza.sh --faza 10` (gated) → **`trap cleanup EXIT`** garantuje da se glm vrati na `aktivan=true` za fazu 1 bez obzira na ishod (uspjeh, greška, prekid). `--gated-faza` opcioni parametar (default `10`) za buduće druge gated faze. Isti argument-stil kao `run_pipeline.sh`/`run_faza.sh`.

Prije upotrebe na Flaviovom budžetu: `bash -n` (sintaksa basha), `py_compile` (sintaksa pythona), i suh test samog togglea (false→true, provjereno u bazi) — sve besplatno, nula Ollama poziva, prije nego je Flavio potrošio ijedan pravi zahtjev.

## Dio 5 — Drugi test (k22, 781-820), preko `run_root_gated.sh`

Flavio je sam pokrenuo (autonomno, po dogovoru): `nohup time bash ./run_root_gated.sh --knjiga 22 --jezici "de hr it sr" --od 781 --do 820 > logs/root_gated_k22_it_0781_0820.log 2>&1 &`. Trajanje: 24m23s (`real`, potvrđeno objašnjenjem real/user/sys razlike na zahtjev). Log potpun, `Cleanup: vrati glm-5.2 u fazu 1` potvrđen u logu — `trap` je radio ispravno.

Rezultat:

| jezik | root (faza 1) | gate otvoren (faza 10) | glm pobijedio |
|---|---|---|---|
| de | 120/120 ocijenjeno | 9 | 9 (100%) |
| hr | 120/120 | 3 | 3 (100%) |
| it | 120/120 | 9 | 8 (89%) |
| sr | 120/120 | 6 | 5 (83%) |
| **ukupno** | **480/480** | **27/160 (16,9%)** | **25/27 (92,6%)** |

Bug fix nezavisno potvrđen DRUGI put, na potpuno svježem opsegu, bez ijedne ručne intervencije osim samog poziva — cijeli lanac (toggle→root→gate→sudija→pobjednik→toggle-nazad) odradio wrapper skript sam.

## Dio 6 — Ollama Cloud potrošnja, vizuelna potvrda

Flavio podijelio screenshot "Weekly usage" (93,3% potrošeno, reset za 2 dana): mistral 5.568 zahtjeva, gemma4 (sudija) 24.360 zahtjeva, glm 4.780 zahtjeva. Iako gemma ima 5× više poziva od glm-a, njen segment trake potrošnje je vizuelno zanemarljiv, dok glm-ov zauzima najveći dio — direktna vizuelna potvrda s155 nalaza (Ollamin dokumentovan bag u glm-5.2:cloud backend-u, cijena po pozivu a ne broj poziva). Dobar dodatni argument za gated pristup. Odluka o usvajanju ostaje za ponedjeljak (Flaviova eksplicitna odluka, svjež pogled).

## Dio 7 — Dva nova KAKO dokumenta

Na Flaviov zahtjev iz sredine sesije ("prije nego nastavimo, upamti 2 KAKO dokumenta... uradićeš ih kompletno na kraju sesije"):

- **`docs/KAKO-BrisanjePrevoda.md`** — FK-svjestan redoslijed brisanja (bb_prev_recenica_faza → bb_prev_recenica → bb_prevodi_recenica, obje FK veze NO ACTION ne CASCADE), Recept A (jedna faza) vs Recept B (sve faze) eksplicitno razdvojeni kao direktna lekcija iz Dijela 2 ovog dokumenta, provjera obima prije/poslije, kad treba re-run `bb_04_pobjednik.py`.
- **`docs/KAKO-NovaFaza.md`** — prošireno README §7 sadržajem: standardna faza (dva INSERT-a), gated faza (mora imati `base` prompt na `bb_faze_a3`, dokumentovan s156 bug + fix), `run_root_gated.sh`/`bb_toggle_model.py` kao gotova infrastruktura, prag/gate default 0,95 (nije potrebno unositi), checklist prije pokretanja.

Napomena: memorija (memory_user_edits) je bila na maksimumu (30/30) usred sesije kad je zatraženo bilježenje ovog zadatka — praćeno kroz ovaj session doc umjesto memorije, po dogovoru s Flaviom.

## Stanje na kraju sesije

**Kod (buchenberg repo):**
- `src/bb_03_prevod.py` — jednolinijski bug fix (`elif is_refine and PROMPT_NAZIV != 'base':`)
- `src/bb_toggle_model.py` — NOVO
- `run_root_gated.sh` — NOVO
- `docs/KAKO-BrisanjePrevoda.md` — NOVO
- `docs/KAKO-NovaFaza.md` — NOVO
- `docs/sessions/session_156.md` — ovaj dokument

**Baza:** k22 (Hound Copy) 701-740 potpuno prazan (sve faze obrisane); 741-780 i 781-820 imaju punu root+gated pokrivenost (de/hr/it/sr), sve ispravno označeno (prompt=base, bez seeda). Faza 10 katalog (`bb_faze`/`bb_faze_a1/a2/a3`) nepromijenjen od s155 — samo su podaci ispod njega sad ispravni.

**Web:** netaknut, BB_VERSION ostaje kako je zatečeno (buchenweb zaostaje za backendom, poznato i namjerno od ranije).

**Korpus (kraj sesije):** 50.624 rečenice / 1.871.857 prevoda / 352.380 pobjednika.

## Otvoreno za ponedjeljak (sedmični Ollama reset ~02:00)

1. Odluka o usvajanju gated-root pristupa u produkciju — sad sa POTVRĐENO ISPRAVNIM mehanizmom (dva nezavisna testa, s156).
2. Pravo testiranje na većem obimu (budžet dozvoljava tek poslije reseta).
3. Odluka o starijim mislabeled test-prevodima koji su MOGLI ostati iz s154 (k22 501-700, faza 9 — nije dirano ove sesije, provjeriti da li i ta serija treba isti tretman).
4. Formalna dopuna `docs/KONCEPT.md` ako se gated pristup usvoji (imenovati novi entitet, po s154 otvorenoj stavci).
5. Stare stavke i dalje čekaju: `predlog_root_DRAFT.py` odluka, "u toku" tabela (s149), seed-lock dizajn (s147).

## Lekcija sesije

Preciznost jezika u komunikaciji o destruktivnim operacijama (DELETE) nije stilska stvar — nejasna riječ poput "čistim" ili "ništa" u kontekstu baze podataka može zvučati kao kontradikcija i eskalirati nepovjerenje, čak i kad je svaka izvršena komanda bila tehnički ispravna i bezopasna. Kad god se radi bilo šta destruktivno, koristiti eksplicitne, nedvosmislene formulacije ("ovo NE briše X, ovo briše Y") umjesto skraćenih metafora ("čistim rep"), čak i u opuštenoj, kolegijalnoj atmosferi. Flavio je ovu sesiju eksplicitno tražio da se dokumentuje bez ublažavanja — urađeno.

Sesija zatvorena SAMOSTALNO od Claudea, na Flaviov eksplicitan zahtjev ("uradi sve bez moje kontrole i odobrenja... javljam se") — isti obrazac kao ranije samostalno zatvorene sesije (s143, s147, s149, s153, s154, s155).

---

*Flavio & Claude · Buchenberg · Sesija 156 · 31. jul 2026.*
