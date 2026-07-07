# Session 117 — RUNOVI statistika alat + web faza 1 start (index.html)

**Datum:** 7. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Dva odvojena posla — (1) trajni alat za statistiku pipeline/refine runova iz log fajlova, primijenjen na prvi k23 bazni run; (2) start web modifikacije po novom "prvo priprema, pa implementacija u jednom dahu" pristupu — faza 1 (tekst/prevodi), stranica po stranica, počevši od index.html.

---

## Health snapshot (početak)
- bb_recenice: 50.624 · bb_prevodi_recenica: 1.403.170 · bb_prev_recenica: 273.578
- Git ulaz: buchenberg 6b82fee (s116), buchenweb cd1e82e (s115). BB_VERSION s115.
- k23 (Big Four Copy) bazna faza gotova: 500/500 na de/hr/it/sr (Flaviov samostalan run noć 6. jul).

## Urađeno

### 1. Memorija — KONFLIKT pravilo ublaženo
Na Flaviov zahtjev: "KONFLIKT = STOP" → "konflikt MOŽE biti stop ako je suštinski i ne kosi se s ostalim pravilima". Primjenjuje se prosudbom, ne kao rigidan okidač. (memory #18)

### 2. RUNOVI statistika — trajni alat
- **NOVO `src/parse_run_logs.py`**: parsira pipeline/refine logove → JSON. Polja: knjiga, jezici, broj_jezika, raspon, broj_recenica, faza (iz "Modeli (faza N)" headera), start/end, elapsed, recenica_po_minutu, prevod_steps (model+temp+real), sudija_real, pobjednik_real; po jeziku: upisano/avg_final/avg_komp/avg_sudija/model_counts.
- **NOVO `docs/RUNOVI.md`**: rastući dokument, dvije tabele po runu (identifikacija&vrijeme / kvalitet&pobjede) + zapažanja. Format osmišljen s Flaviom kroz iteraciju (dodati: broj jezika, rečenica/min, start/end za detekciju paralelnih sesija, faza).
- **Prvi run dokumentovan:** k23 Big Four Copy, de/hr/it/sr, 1–500, faza 1. Ukupno: avg_final 0.9691, pobjede glm-5.2 63.0% / mistral-large-3 30.7% / nllb 6.3%. Zapažanja: batch 1–20 niži (metapodaci), rečenica/min 0.64–1.33 (Ollama Cloud opterećenje, ne veličina batcha).
- Commit buchenberg `3b78ff6`.

### 3. Web faza 1 — pristup i start
- **Pristup usvojen (Flaviov):** kao s114 refaktor — prvo SVE pripremiti, pa implementirati u jednom dahu. Dvije faze: (1) tekst + UI prevodi + vidljivi elementi (menu, title) — samo tekstualne odluke, ne tehničke; (2) tehnička implementacija. x.html ostaje x.html (mijenja se naslov, ne ime fajla). Stranica po stranica. Cross-cutting nalazi → globalna pravila (ne ponavljati/ne razilaziti se).
- **Obavezno čitano prije starta:** ANALIZA.md, KONCEPT.md (project files), STRANICE.md (server).
- **NOVO `docs/WEB-FAZA1.md`**: radni dokument faze 1.
- **index.html obrađen** (Flavio tražio da Claude radi samostalno — jučerašnji s115 rad ostao u lošoj uspomeni). Nalaz: i18n rječnik ČIST (s115 posao stoji, nijedan index ključ ne imenuje model). Ali otkriveno globalno pravilo:
  - **G1:** HTML hardkod fallback još imenuje modele (how-desc/how-desc2/pillar-judge/pillar-refine u index.html još kažu Gemma/Ministral/NLLB) — hardkod mora pratiti očišćeni rječnik. Za fazu 2, bez novih prevoda.
  - **G2:** title↔menu↔naslov odnos — provjeriti sva tri po stranici (iz STRANICE.md neskladi).
- index.html faza 1: ništa novo za tekst; faza 2: jedna stavka (G1 hardkod sync).

## Sljedeće
1. **Web faza 1 nastavak — about.html** (menu About). Napetost za riješiti: about je EDUKATIVNA stranica, imena modela nose pedagošku vrijednost (LLM vs specijalizovani NLLB) — odlučiti da li princip "bez imena" važi jednako strogo ili about dobija izuzetak.
2. Ostale stranice faze 1 redom (stats, books, nlp, learn, geometry, art, reader).
3. Faza 2 (tehnička implementacija) tek nakon što faza 1 kompletna za sve stranice.
4. k23 refine faza (faza 2) kad Flavio pusti; k22/k24 puni runovi — otvoreno.
5. Otvoreno s107/s108: brojači faze 2, stats dvije tabele.

## Stanje na izlazu
- buchenberg: commit 3b78ff6 (RUNOVI+parse_run_logs) + ova sesija (session_117 + README + WEB-FAZA1.md, slijedi commit)
- buchenweb: NETAKNUT, BB_VERSION s115
- Baza: netaknuta

---
*Flavio & Claude · Buchenberg · session 117 · 7. jul 2026.*
