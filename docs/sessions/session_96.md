# Session 96 — 25. jun 2026.

**Fokus:** Web identitet i X-Ray lineage — "MT Lab" podnaslov (Xpong RL Lab paralela), heksagon ikona uz home logo, dvije X-Ray Wikipedia kartice u Key Concepts. Pipeline/kod nedirnut (Flavio vodi prevode).

## Onboarding
- Project files → README (s95 stanje) → posljednje 3 sesije (s95/s94/s93) → health_check.py, sve po protokolu.
- Health check kroz nohup→log; cold-start spor (~5 min). **Flaviova dijagnoza: usko grlo je DB query nad bb_prevodi_recenica (~624k redova), ne CPU.** Stavljeno na horizont.

## Health snapshot (početak s96)
- Korpus: 38.333 rečenice, **623.710 prevoda** (+53.599 od s95), **116.674 pobjednika** (+1.160). Pipeline melje između sesija (Flaviova taktika, paralelni procesi).
- Kompletno na svih 14 jezika (prev=pobj): Alice (1535), Flatland (1341), Jekyll & Hyde (1157). Big Four ≥400 pobj svuda.
- Asimetrija namjerna (NIJE anomalija): Hound de/hr/it/sr=3852 pobj, ostali 3852 prev/800 pobj. Dracula/Frankenstein/Moby/Romeo core 4 puni, ostali ~200.
- Infra: PG 17.9, Ollama 35 modela, NLLB keš + transformers OK, venv kompletan.
- Git na ulazu: buchenberg 33d826f (s95), buchenweb 7c619ce (s95), oba čista.

## Urađeno (sve buchenweb)

**1. "MT Lab" identitet (Xpong RL Lab paralela).**
- Pogledao Xpong izvor (`/var/www/xpong/`): `<title>xpong — RL lab</title>`, hero red `lab:'Reinforcement Learning Lab'` (nepreveden, EN na svim jezicima), `.xp-hero-lab` stil (12px, bold, uppercase, letter-spacing, accent).
- Buchenberg analogno: novi red `<div class="bb-hero-lab">Machine Translation Lab</div>` između loga i taglinea; `.bb-hero-lab` CSS (13px umjesto Xpongovih 12 zbog Flaviovog vida); `<title>Buchenberg</title>` → `<title>Buchenberg — MT lab</title>`.

**2. Heksagon ikona uz home logo.**
- `favicon.svg` (Flatland heksagon, 64×64, crno `#111111` na sivom `#d8dadd`) ubačen kao `<img class="bb-hero-icon">` lijevo od "Buchenberg" u home heru.
- `.bb-hero-logo` → flex (align/justify center, gap 16px) da ikona+tekst ostanu centrirani kao cjelina; `.bb-hero-icon { width/height 64px }`. Samo index.html.

**3. Key Concepts — dvije X-Ray kartice.**
- Cilj: linkovi ka Wikipediji na home/about/stats. Sistem: `data/concepts.json` per-stranica, render (nav.js ~1520) gradi link auto iz `wiki` sluga (`en.wikipedia.org/wiki/<slug>`), fetch s `?t=Date.now()` (keš-bust ugrađen).
- Dodane 2 kartice na index/about/stats (idempotentno, provjera po name):
  - 🩻 **X-ray style art** → `X-ray_style_art` (aboridžinska/prehistorijska umjetnost, poglavlje I X-Ray pamfleta)
  - 🎸 **Rock Art and the X-Ray Style** → `Rock_Art_and_the_X-Ray_Style` (Strummer 1999, epigraf pamfleta)
- Oba URL-a verifikovana HTTP 200 (curl -L, bez redirecta). "Key Concepts" naslov se NE prevodi (ostaje EN svuda).

## Lekcije
- **Spec-razumijevanje:** sesija počela s lošom komunikacijom oko zadatka 3 (gdje idu linkovi). Pretpostavio Philosophy sidebar blok + "samo EN tekst"; Flavio mislio Key Concepts kartice. Više iteracija + jedan revert (Philosophy blok dodan pa vraćen na staro). Lekcija: za "dodaj link X negdje" — prvo mapirati sve kandidate-lokacije i pitati KOJU, ne implementirati prvu pretpostavku.
- Xpong je živ referentni obrazac za zajednički "Lab/X-Ray project" identitet — gledati izvor prije analogne izmjene.
- favicon.svg živi u web rootu, ali venv NIJE (`/home/balsam/buchenberg/venv` — eksplicitna putanja za Python edite web fajlova).

## Stanje na kraju
- BB_VERSION: **s96** (25 Jun 2026).
- Git: buchenweb (index.html, buchenberg.css, nav.js version bump, data/concepts.json); buchenberg (session_96.md + README).
- Kod/pipeline: nedirnut. Philosophy blok: nepromijenjen (revert čist).
- Backupi: buchenberg.css.bak_s96_mtlab, index.html.bak_s96_mtlab, nav.js.bak_s96_xraylinks, data/concepts.json.bak_s96.

## Sljedeće (po prioritetu)
1. **DB optimizacija health_check / agregacija** (NOVO — Flaviova dijagnoza s96): query nad bb_prevodi_recenica usko grlo kako korpus raste (~624k). Indeksi / optim. COUNT / materijalizovani view za stanje.
2. Length bucketing za NLLB (opciono, nula drifta).
3. Proširenje prevoda (Flaviova taktička odluka — vodi sam).
4. art.html v1, about.html i18n, learn.html nove igre, bb_web_export refaktor (v_pobjednici).
5. NLP Relation Extraction — rasplet kao ulaz (leži od s90).

---

*Flavio & Claude · Buchenberg · Session 96 · 25. jun 2026.*
