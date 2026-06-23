# Session 94 — 23. jun 2026.

**Fokus:** Kratka sesija — podsjećanje na graph-DB/Relation-Extraction odluku (s90) + UX sitnica: Library "NER" dugme preimenovano u "NLP". Pipeline/kod nedirnut.

## Onboarding
- Project files → README (s93 stanje, NLLB CT2 int8 default) → posljednje 3 sesije (s93/s92/s91) → health_check.py, sve po protokolu.
- ⚠️ Anthropic proxy stream timeout na health_check (potvrđeno na Anthropic statusu — preopterećenje infrastrukture, nije foxuno). Riješeno: nohup u log fajl → kratki read. Cold-start import doprinosi.
- Memorija na ulazu zastarjela za brojeve (s93 snapshot) — usklađeno sa serverom.

## Health snapshot (početak s94)
- Korpus: 38.333 rečenice, **521.274 prevoda** (+68.494 od s93), **94.894 pobjednika** (+12.400 od s93). Pipeline jako mleo između sesija (s92 najavio run 3 knjige × 10 jezika).
- Infra: PostgreSQL 17.9, .env / Ollama / NLLB keš / venv — sve zeleno.
- Git na ulazu: buchenberg=s93 stanje, buchenweb bd66455 (s90) zaostaje.

## Diskusija — zašto ne graph-DB za otkrivanje krivca (re-derivacija s90)
Flavio pitao za podsjećanje. Sažeto:
- **Problem = kombinatorni šum.** Tražiti relacije među svim parovima entiteta → većina besmislena ("SIM kartice na punom stadionu"). Graph-DB se davi u tom šumu jednako kao i sve ostalo.
- **Pomak 1 — graf kao istražni alat, ne proročište.** NER graf ne sudi ("X sumnjiv jer vezan za Y"), nego daje senku iz koje Flavio pravi hipotezu (policijska upit-logika). Za to je postojeći NER + co-occurrence graf (nlp.html) dovoljan — graph-DB nije potrebna.
- **Pomak 2 — rasplet kao ulaz.** Detektivski roman na kraju eksplicitno izgovori relacije (autorov pouzdan opis grafa). Invertuje teški problem: rasplet = upit, semantička pretraga unazad = grounding kroz provjerljivi kosinus. Daje i zlatni standard za evaluaciju. Žanrovski uslovljeno (Hound, Big Four imaju rasplet).
- **Status:** ostaje da odleži (Flaviova odluka iz s90, nepromijenjena).

## Urađeno — Library "NER" → "NLP"
- **Razlog:** dugme je vodilo na nlp.html ali pisalo "NER" → korisnik ne poveže s "NLP" menu stavkom; mogao pomisliti da NER stranica zasebno (ne) postoji. Plus: nlp.html odavno > NER (word cloud, entiteti, mreža, highlight). "NLP" je i konzistentniji i tačniji.
- **Izmjena:** `nav.js` i18n vrijednost `books_btn_ner` "NER" → "NLP" na svih 5 jezika (EN/DE/IT/HR/SR). Ključ neizmijenjen (samo vrijednost) → books.html nedirnut. Link je već vodio na `nlp.html?book=ID`.
- **Cache:** BB_VERSION s90.1 → **s94**, datum 23 Jun 2026.
- Verifikovano grep-om: svih 5 = "NLP", nijedan stari "NER".

## Lekcije
- Akronim-label ("NER") koji curi kao šum u grep-u (njem./hol. stopwords sadrže "ner") — ciljati jedinstven uzorak `books_btn_ner:"NER"`, ne goli "NER".
- Stream timeout može biti Anthropic-side infrastruktura, ne foxuno — provjeriti status, izolovati kroz nohup+log.

## Stanje na kraju
- BB_VERSION: **s94** (23 Jun 2026).
- Git: buchenweb commit (nav.js NER→NLP + version bump); buchenberg commit (session_94.md + README §9 snapshot/§10 label).
- Kod/pipeline: nedirnut.

## Sljedeće (po prioritetu — nepromijenjeno od s93)
1. Length bucketing za NLLB (opciono, nula drifta).
2. Proširenje prevoda (hr/sr/it/de→s350; mk/bg→s51–100) — brzo s CT2.
3. art.html v1, about.html i18n, learn.html nove igre, bb_web_export refaktor (v_pobjednici), favicon.
4. NLP Relation Extraction — rasplet kao ulaz (leži od s90).

---

*Flavio & Claude · Buchenberg · Session 94 · 23. jun 2026.*
