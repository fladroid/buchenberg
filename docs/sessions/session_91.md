# Session 91

**Datum:** 20. jun 2026.
**Fokus:** Meta-sesija — kreiranje prenosivog priručnika za saradnju (METHOD) i custom instructions. Buchenberg pipeline/portal nije diran.

## Onboarding
- Project files → README → poslednje 3 sesije (s90/s89/s88) → `health_check.py`, sve po protokolu (prikaži, OK).
- Memorija na ulazu bila zastarela (s88); stvarno stanje s90. Usklađeno iz session doca — potvrda principa "server je izvor istine, ne pamćenje".

## Health snapshot (početak s91)
- Korpus: 38.333 rečenice, 335.068 prevoda, 54.722 pobednika (+44.580 prevoda / +10.400 pobednika od s90 — pipeline mleo između sesija).
- Hound (de/it/sr/hr) i Flatland (de/it/sr/hr) kompletni. PostgreSQL 17.9, Ollama Cloud (35 modela), NLLB, venv — sve zeleno.
- Git na ulazu: buchenberg `7b7e58a` (s90), buchenweb `bd66455` (s90), oba čista.

## Urađeno
- **METHOD** — prenosivi priručnik za saradnju čovek–AI, destilovan iz Buchenberga.
  - Struktura: Deo I Principi (filozofija saradnje, komunikacijski protokol, ritam sesije, dokumentacija, verifikacija); Deo II Mašinerija (tehničko okruženje, tri sloja AI pamćenja, Day-0 pokretanje); Deo III X-Ray sloj (integralni, vezuje sve ranije sekcije); Dodatak (Buchenberg kao razrađen primer A.1–A.9 + snimak).
  - Obrazac po sekciji: Princip → Zašto radi → Primer iz Buchenberga → `⟦ fill-in ⟧` slot.
  - Ključno razlikovanje: prenosiv je *princip* ispod Buchenberg-specifične *mehanike*.
- **Dvojezično:** `METHOD.md` (EN) + `METHOD_SR.md` (SR, ekavica). Oba popeta u project knowledge — deo Day-0 seta za ovaj i sve nove projekte.
- **Custom instructions** napisane (project instructions tekst za copy-paste): protokol komandi, stil, podela alata, onboarding/closing, verifikacija. Cilj: protokol komandi kao invarijanta u najjačem sloju (namerna redundancija iz §7), nezavisno od toga je li fajl pročitan.
- Mehanika tri sloja memorije verifikovana protiv zvanične dokumentacije (Claude.ai: custom instructions / project knowledge / memory; dva nivoa instructions; veliki knowledge se čita selektivno preko retrievala).

## Lekcije
- Razlika mehanika→princip je nosiva os prenosivog dokumenta: ne prepisivati Buchenberg pravila, nego destilovati princip ispod njih.
- METHOD sam pripada knowledge sloju koji propisuje — dokument se samoizvršava (od sledeće sesije čita se na onboardingu).

## Stanje na kraju
- BB_VERSION: **s90.1** (bez promene — web/portal nije diran ove sesije).
- Pobednici: **prio 2** (rade OK).
- Git: bez izmena u repoima osim ovog session doca. METHOD trenutno živi u knowledge/UI, ne u gitu (odluka Flavia).

## Sledeće
- (opc.) METHOD kopija i u git repo radi verzionisanja — knowledge je za čitanje, git za trag/istoriju.
- Web: favicon, `bb_web_export.py` refaktor na `v_pobjednici`, Cache-Control headeri (`.htaccess`/`mod_headers`).
- NLP Relation Extraction (leži od s90; najjača varijanta — rasplet detektivskog romana kao ulaz).
- Proširenje prevoda po planu (hr/sr/it/de → s350; mk/bg → s51–s100).
