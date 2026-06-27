# Session 99 — 27. jun 2026.

**Fokus:** Web prezentacija (3 Flaviove molbe) — (1) "Verify, not fiction" blok iz Xponga na about, (2) pet About izmjena, (3) stats.html performanse: DB-side agregacija (165 MB / 126 fetch → 14.6 KB / 1 fetch). Pipeline nedirnut (Flavio vodi 3 paralelna prevodilačka procesa).

## Onboarding
- Project files → README (s98 stanje) → posljednje 3 sesije (s96/s97/s98) → health_check.py, sve po protokolu.
- Health check kroz nohup→log: **0:24 elapsed, 86% CPU** — s97 DB-fix se drži, nema regresije.
- Čišćenje: obrisana 4 `.bak` fajla (README s96/s97/s98, health_check s97) na Flaviov zahtjev. `__*__` probni fajlovi, `fla_*.sh` privremeni prevodilački i `nohup.out` — Flaviovi, ignorisati (on čisti).

## Health snapshot (početak s99)
- Korpus: 38.333 rečenice, **803.090 prevoda** (+101.360 od s97), **155.470→157.070 pobjednika** (pipeline melje tokom sesije).
- Kompletno na svih 14 jezika (prev=pobj): Alice (1535), Flatland (1341), Jekyll & Hyde (1157).
- Core-4 puni (de/hr/it/sr): Hound 3852, Dracula 2200, Romeo 1600, Moby 1500/1200.
- Frankenstein/Big Four obrazac: non-core jezici (bg/bs/mk/sl) imaju VIŠE pobjednika nego core-4 — namjerno taktičko sekvenciranje, NIJE anomalija.
- Infra: PG 17.9, Ollama 35 modela, NLLB keš + transformers OK, venv kompletan.
- Git na ulazu: buchenberg **10af9e6** (s98), buchenweb **f2b94b4** (s96), oba čista. BB_VERSION s96.

## Urađeno

### Molba 1 — "Verify, not fiction" blok (about, svih 5 jezika)
- Izvor: Xpong `about.html` (`<aside>` sa `xp-infobox` blokovima) + `app.js` (i18n EN/DE/IT/HR/SR). Prenesen 1:1, jedna adaptacija: zadnja rečenica vezana za RL-agenta ("light up what the agent does inside") → MT ("what happens inside the translation") na svih 5 jezika.
- **Mehanizam (drugačiji od Xponga):** Buchenberg about koristi `id` + `ti(id, key)` → `t(k)` → `BB_NAV.t('about_'+k)`. i18n stringovi žive u **nav.js** (centralni), ne inline. `ti()` koristi `innerHTML` → `<br><br>` se renderuje (nije trebao zaseban `data-i18n-html`).
- **nav.js:** dodano `about_sidebar_verify` + `about_sidebar_verify_text` u svaki od 5 jezičnih blokova, odmah iza `about_sidebar_project_info` (anchor jedinstven po jeziku jer je vrijednost različita).
- **about.html:** novi `bb-infobox` blok (`id=about-sidebar-verify` + `-text`) odmah iza Project info bloka; dva `ti()` poziva.
- Verifikacija: paran broj `"` po svih 10 izmijenjenih linija (string-balans, node nedostupan na foxunu).

### Molba 2 — pet About izmjena
1. **Claude koncept-kartica** → `data/concepts.json` about niz (na kraj — dogovor: sve nove kartice idu na kraj). `✨ Claude` → `Claude_(language_model)` (slug verifikovan web searchom). 18 kartica ukupno. (concepts.json fetcha s `?t=Date.now()` — auto cache-bust.)
2+3. **Philosophy tekst:** "autorova/the author's X-Ray stava" → prvo lice ("mog/my/meiner/mio/мог") u svih 5 jezika. Potpis ionako "— Flavio".
4. **Infrastruktura pasus:** "dva kućna/home/domestici servera" → "dva cloud servera"; + dodatak (svih 5 jez.): foxuno besplatno pod uslovima oci.oracle.com, balsam mjesečna najamnina cloud provideru strato.de.
5. **SR ćirilica:** podnaslov modela `двије врсте машина` → `две врсте машина` (ekavica fix; Flavio spomenuo kao "мssина" tipo, stvarni issue bio ijekavski "двије").

### Molba 3 — stats.html performanse (DB-side agregacija)
- **Dijagnoza (mjereno, ne nagađano):** stats.html `loadStats()` je serijski fetchao **126 `tr_*.json` fajlova = 165 MB** (`du -ch`), pa 4× petljao kroz sve u browseru. Dizajn iz prve verzije (par jezika, par stotina rečenica) → sad 803k redova. Oba uska grla: transfer + JS-računanje.
- **Uvid:** stats stranici ne treba nijedan od 165 MB — samo agregati (~par KB). Browser vuče 165 MB da izračuna par KB. Isti X-Ray obrazac kao s97: pomakni posao gdje je jeftin (baza GROUP BY nad 803k = ms).
- **SQL mjeren prije implementacije** (`\timing`): summary 0.5s, winner-dist 0.26s, score-by-lang 0.35s — sve <0.5s nad 157k pobjednika. `v_pobjednici` nema knjigu kao kolonu → agregati pisani direktnim JOIN lancem + `bb_knjige` (README §5 dozvoljava pri gradnji novog exporta).
- **`bb_web_export.py`:** dodana `get_stats(cur)` (4 GROUP BY nad zajedničkim `base_from`: summary, winner-dist, coverage, score-by-lang) + `stats.json` generisanje u `main()` prije `cur.close()`. `ast.parse` OK.
- **stats.json:** **14.6 KB** (vs 165 MB = ~11.000× manje), 1 fetch (vs 126). Agregacija ~7s pri exportu (pipeline melje paralelno, dijeli resurse) — dešava se jednom na serveru, korisnik ne osjeti.
- **stats.html:** `loadStats()` prepravljen — 1 `stats.json` fetch, mapiranje na iste `window._winnerRows/_coverageRows/_scoreRows` formate (render funkcije netaknute). Stara `allTranslations` logika potpuno uklonjena (grep verify: tr_ fetch=0, allTranslations=0). + loading state ("Loading…" u 3 wrap-a prije fetcha, `t('stats_loading')` s fallbackom) + ojačan error catch (sva 3 wrap-a, ne samo winner).
- **version.json** bumpan (svjež `?v=` fetch).
- **Verifikacija:** Flavio pokrenuo pun `bb_web_export.py` → **0:22.62 elapsed, 33% CPU**, čist end-to-end (svih 126 + stats.json). stats.html učitava "blic brzo".

## Lekcije
- **node nije na foxunu** — `node --check` pao na "command not found", ne na sintaksi (lažna uzbuna). JS-sintaksu provjeravati Pythonom (paran broj `"` po liniji). Diskutovano: nvm (izolovano u ~/.nvm, bez sudo, bez Apache dodira) kad zatreba — za sad ne treba (vanilla statički model).
- **Apache + statički sajt ne treba node u produkciji** — node bi bio dev/build alat (lint, --check), ne runtime. Node-runtime server (Express/Next) = nepotreban skok (živi proces koji pada, kao pgAdmin FD-exhaustion).
- **Mjeri prije nego biraš rješenje** (kao s97): `du -ch tr_*.json` = 165 MB dao dijagnozu jednim potezom. Bez mjerenja birali bismo naslijepo (možda samo loading state, a stvarni problem je transfer).
- **Epistemika putanje:** stats.html nije u repo dir nego web root — prazan rezultat grepa u `/home/balsam/buchenberg/` nije "ne postoji", nego "gledam pogrešno mjesto" (web fajlovi žive u `/var/www/buchenberg/`).
- **i18n mehanizam Buchenberg ≠ Xpong:** Buchenberg = `ti(id,key)` + centralni nav.js; Xpong = `data-i18n`/`data-i18n-html` + app.js. Prenos blokova zahtijeva prilagodbu mehanizmu, ne copy-paste markupa.
- **Flavio ODBIJA interaktivne formulare** (ask_user_input) — pitanja običnim tekstom, kao kolege. Upisano u memoriju (#16).

## Stanje na kraju
- **BB_VERSION: s99** (27 Jun 2026) — bumpan (web mijenjan).
- Git buchenweb: about.html, nav.js, stats.html, data/concepts.json, data/version.json. Backupi: nav.js.bak_s99_verify, about.html.bak_s99_verify, stats.html.bak_s99, data/concepts.json.bak_s99.
- Git buchenberg: src/bb_web_export.py (get_stats + stats.json), session_99.md, README. Backup: src/bb_web_export.py.bak_s99.
- Pipeline nedirnut. stats.json (14.6 KB) generisan i u produkciji.

## Sljedeće (po prioritetu)
1. Isti fan-out/agregacija pattern provjeriti u preostalim mjestima (nlp.html backend?) — stats riješen.
2. Opciono: `stats_loading` i18n ključ u nav.js (sad fallback "Loading…").
3. Length bucketing za NLLB (opciono, nula drifta).
4. Proširenje prevoda (Flaviova taktička odluka — vodi sam).
5. art.html v1, about.html i18n (ostatak), learn.html nove igre, bb_web_export refaktor (v_pobjednici za tr_).
6. NLP Relation Extraction — rasplet kao ulaz (leži od s90).
7. Infra: pgAdmin Opcija 2 (FD limit 65536) kad se simptom vrati.

---

*Flavio & Claude · Buchenberg · Session 99 · 27. jun 2026.*
