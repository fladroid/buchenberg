# Sesija 153 — 25. jul 2026.

**Autori:** Flavio & Claude
**Fokus:** analiza 16 novih log fajlova (k20 Dracula, opseg 6601–8200, de/hr/it/sr) — otkriven neplaniran prelazak paralelno→sekvencijalno usred niza; upis u RUNOVI.md; sesija zatvorena samostalno (Flavio unaprijed autorizovao, odsutan od PC-a)

---

## Zdravlje na početku sesije

Checklist proveden (project files → README → session_150/151/152 → health_check). Health check otkrio da je README footer stao na "sesija 151" iako je header govorio "sesija 152" i korpus/git jasno pokazivali s152 kao stvarno stanje — mala unutrašnja nekonzistentnost u samom README-u, ne pravi memorijski zaostatak. Korpus na početku: 50.624 / 1.728.725 / 323.768 (raslo od s152 Flaviovim pozadinskim runovima). 252 poznate rupe (nepromijenjeno). Oba repoa čista, BB_VERSION s152.

## Analiza log fajlova

Flavio dostavio 16 log fajlova (`pipeline_k20_{de,hr,it,sr}_{6601_7000,7001_7400,7401_7800,7801_8200}.log`) — direktan nastavak prethodnog PO-JEZIKU runa dokumentovanog u prošloj RUNOVI.md sekciji (koji je stao na poziciju 6600). `docs/RUNOVI.md` pročitan prvo radi podsjećanja na metodologiju/format, zatim `parse_run_logs.py` pokrenut nad svih 16 fajlova.

**Glavni nalaz:** obrazac izvršavanja se promijenio usred niza. Prva serija (6601–7000) nastavlja paralelni PO-JEZIKU obrazac (sva 4 jezika startuju istovremeno) — agregat 11.85 rec/min, u skladu s ranije izmjerenim rasponom. Od druge serije naviše (7001–7400, 7401–7800, 7801–8200), jezici se izvršavaju strogo sekvencijalno — svaki naredni jezik starta tačno u trenutku kad prethodni završi, kroz sve tri preostale serije, bez pauze. Ovo nije viđeno ni u jednom prethodnom RUNOVI.md unosu.

**Cijena promjene:** za isti obim posla (1600 rečenica = 4×400), sekvencijalni režim daje ~3.78–4.30 rec/min agregatno naspram ~11.85 paralelno — faktor ~2.8–3.1× sporije u wall-clock vremenu da se korpus pomjeri za isti broj rečenica. Pojedinačna brzina po jeziku dok radi solo (3.43–5.00 rec/min) je sama po sebi solidna, ali pošto samo jedan jezik radi u datom trenutku, agregatni napredak pati.

Flavio potvrdio: promjena režima bila je **namjerna** (ne greška ni nepredviđena posljedica).

**Sporedni nalazi:**
- Sudija (gemma4:31b) trajanje 18–32 min po seriji, bez jasnog dan/noć trenda u ovom uzorku — znatno slabiji efekat nego 6.1× faktor iz prethodnog runa (taj je vjerovatno bio specifičan za ta dva konkretna termina).
- Kvalitet stabilan kroz oba režima (avg_final 0.9593–0.9684) — potvrđuje već uspostavljen obrazac (brzina varira, kvalitet ne).
- Dracula (k20) de/hr/it/sr napredovao sa pozicije 6600 na 8200 (knjiga ima 9.073 rečenice ukupno — još ~873 preostaje).

Rezultat upisan u `docs/RUNOVI.md` kao novi run-blok (4 serije, tabele + zapažanja, isti format kao dosadašnji unosi).

## Zatvaranje sesije — samostalno

Flavio je eksplicitno autorizovao samostalno zatvaranje ("uradi ceo ritual samostalno... ovo je izuzetak jer ne mogu da kontrolišem predlog rada i odobravanje izvršenja") prije nego što se udaljio od računara. Ritual proveden bez međukoraka show→OK→execute za preostale komande (RUNOVI.md upis, ovaj dokument, README update, commit, push) — isti obrazac kao ranije samostalno zatvorene sesije (s143, s147, s149).

## Završno stanje

Korpus nepromijenjen sesijskim djelovanjem (nula pipeline poziva, analitička sesija). BB_VERSION ostaje **s152** (web nedirnut). `buchenberg` repo: `docs/RUNOVI.md` (+1 run-blok) + ovaj dokument — commit i push slijede. `buchenweb` repo: netaknut.

## Sljedeći koraci

- Otvorene stavke iz s149/s150 i dalje čekaju: `predlog_root_DRAFT.py` odluka, "u toku" tabela + nezavisan proces, seed-lock dizajn (s147).
- Flavio nastavlja slati nove RUNOVI logove po potrebi.

---

*Flavio & Claude · Buchenberg · Sesija 153 · 25. jul 2026.*
