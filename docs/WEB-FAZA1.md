# WEB-FAZA1 — Priprema tekstualnih izmjena web prezentacije

Radni dokument za FAZU 1 (samo tekst + prevodi + vidljivi elementi: menu, title).
Tehnička implementacija = FAZA 2 (zaseban prolaz, "u jednom dahu").
HTML fajl x.html ostaje x.html — mijenja se samo prikazani naslov, ne ime fajla.

**Metod:** stranica po stranica. Cross-cutting nalazi (važe za sve) → sekcija GLOBALNA PRAVILA.

---

## GLOBALNA PRAVILA (otkrivena tokom rada, važe za SVE stranice)

### G1 — HTML hardkod fallback mora pratiti i18n rječnik (otkriveno na index.html)
Trajni princip iz s115 (nijedan model se ne imenuje u web prezentaciji) primijenjen je
na i18n RJEČNIK u nav.js, ali NE i na HTML hardkod fallback u samim stranicama.
HTML hardkod je no-JS fallback — ali JS ga pregazi tek kad se učita. Do tada (i za
korisnike bez JS-a, i za pretraživače/preview) vide se STARA imena modela.
→ PRAVILO: kad i18n ključ očistimo od imena, isti tekst mora se očistiti i u HTML
  hardkodu iste stranice. Inače hardkod i rječnik protivriječe jedan drugom.
→ Zahvaćeno na index.html: how-desc, how-desc2, pillar-judge, pillar-refine
  (hardkod još kaže "Gemma 3 12B / Ministral 3 14B / NLLB-600M / Gemma 4 31B").

### G2 — Odnos "title tag" ↔ "menu tačka" ↔ "vidljivi naslov" (iz STRANICE.md)
Tri različita mjesta, mogu se razići. Kod svake stranice provjeriti sva tri.
Poznati neskladi (STRANICE.md s116): art (nema _title ključ), books (<title>="Books"
≠ h1="Library"), stats (menu "X-Ray Stats" ≠ naslov "X-Ray Statistics").
→ Odluke o svakom donosimo per-stranica niže, ali obrazac je globalan.

---

## STRANICA: index.html (menu: Home)

### Status i18n rječnika: ČIST ✅
Nijedan `index` ključ (tagline, hero_desc, sec_how, how_desc, how_desc2, pillar_bt,
pillar_judge, pillar_refine, pillar_winner, opensource) ne imenuje model — potvrđeno
grep-om (s115 posao stoji). Uloge opisane, ne komponente.

### Preostali problem: HTML hardkod fallback još imenuje modele (vidi G1)
Za FAZU 2 (tehnički): sinhronizovati hardkod tekst u index.html s već-čistim i18n
vrijednostima za: how-desc (l.42-44), how-desc2, pillar-judge (l.78 "Gemma 4 31B"),
pillar-refine. Tekst za kopirati POSTOJI u nav.js EN bloku — samo prepisati hardkod
da mu odgovara. Nema novih prevoda (rječnik već preveden na 5 jezika).

### Title / naslov: OK, bez izmjene
`<title>Buchenberg — MT lab</title>` — brend, ne imenuje model. Hero brend+tagline
umjesto h1 (namjerno, landing). Ništa za mijenjati u fazi 1.

### Tekstualne izmjene (sadržaj): NEMA
Home je već prošao kroz s108+s115. Sadržajno kompletan i konzistentan s KONCEPT-om.

### Zaključak za index.html
Faza 1 (tekst/prevodi): ništa novo za pisati.
Faza 2 (tehnički): jedna stavka — G1 hardkod sync (bez novih prevoda).
