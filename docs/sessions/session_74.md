# Session 74 — Sentence Fingerprints

**Datum:** 13. jun 2026.
**Sesija:** 74
**Autor:** Flavio & Claude

---

## Što je urađeno

### 1. Checklist (standardni)
- Project files pročitani (buchenberg_napomena_new.md, X-Ray SR/EN)
- README pročitan (V3, s73)
- Sessions 71–73 pročitane
- Health check: sve zeleno — 38.333 rečenica, 124.128 prevoda, 8.602 pobjednika
- Git čist (2a5f77a buchenberg, b9ca62c buchenweb)

### 2. bb_06 status — zaključak
124.128 prevoda, od toga 2.530 bez `prevod_vektor`. Zaključak sesije:
- `prevod_vektor` koristi se samo na geometry.html (UMAP) i nije dio Reader X-Ray panela
- Reader X-Ray: back_translation, translation_score, back_score, sudija ocjene, model, temp — `prevod_vektor` nije potreban
- bb_06 retroaktivno punjenje: **nizak prioritet**, osim ako geometry.html ne dobije nove jezike/knjige
- Ovo se navodi ovdje kao trajni zaključak — ne tretirati kao otvoreni TODO

### 3. Istraživanje: Sentence Fingerprints u kontekstu MT

Pretraga pokazala: embedding vizualizacija (t-SNE, UMAP scatter) je dobro istražena oblast.
Deterministički generativni vizuelni otisak po rečenici za usporedbu prijevoda — **nije pronađeno** kao gotov pristup.

Potencijalni doprinos polju: **"vizuelni BLEU"** — brza humana procjena kvaliteta prijevoda bez lingvističke ekspertize za ciljni jezik.

BLEU (Bilingual Evaluation Understudy): mjeri n-gram preklapanje između mašinskog i referentnog (human) prijevoda. Problemi: treba referentni prijevod; mjeri leksičku sličnost, ne semantičku. Sentence Fingerprints bi bio semantički, vizuelni, bez referentnog prijevoda.

### 4. Sentence Fingerprints — implementacija (art.html, Exhibit 3)

**Algoritam otiska:**
- 1024-dimenzionalni embedding vektor → 64 sektora (svaki = 16 dimenzija)
- Duljina sektora = magnituda tih 16 dims (normalizirana na [minM, maxM])
- Boja sektora = hue izveden iz srednje vrijednosti tih 16 dims (`(mean*800+200)%360`)
- Isti vektor → uvijek isti otisak (deterministički)
- Slični vektori → vizuelno slični otisci

**UI:**
- Book selector + count selector (64/128/256 sentences, default 128)
- ◀ sentence X / total ▶ navigacija
- Grid: EN original + sve dostupne prevedene rečenice
- Ispod svakog otiska: lang label + cosine similarity vs EN (zelena boja po simi)
- Hover: `zoom-in` cursor
- Klik → modal overlay s 400×400 otiscom + lang + sim + tekst rečenice
- Klik izvan modala → zatvara

**Tehničke napomene:**
- Transformers.js lazy-load via dynamic import (isti CDN kao geometry.html)
- Model se kešira u `pipePromise` — prvi load ~30s, zatim brzo
- Vektori se kešuju u `vecCache` (key: `lang:sentenceIdx`) — navigacija postaje brza
- Count selector reloaduje book i resetuje na sentence 1
- Svaki jezik: učita se cijeli JSON, ali se reže na `fpCount` sentences

**Emergentna pojava — "peteljka" (maslačak):**
Neki sektori vektora imaju konzistentno visoku magnitudu bez obzira na rečenicu ili jezik. To su dimenzije koje su "uvijek aktivne" u multilingual-e5-large — univerzalna semantička osnova zajednička svim tekstovima. Vizuelno: dugi sektor koji podsjeća na stabljiku maslačka. Cvjetna kruna = semantički potpis rečenice. Peteljka = invarijanta prostora.
Zaključak: peteljku ostaviti — govori istinu o strukturi embedding prostora.

### 5. nav.js → s74 (13 Jun 2026)
Preskočen s73 bump (s73 sesija bila je isključivo git infrastruktura, bez web promjena).

### 6. buchenweb commit
`9427100` — art.html + nav.js, 201 insertions

---

## Stanje na kraju sesije

- art.html: Exhibit 3 (Sentence Fingerprints) implementiran i radi
- buchenweb: commit 9427100, git čist
- buchenberg: nepromijenjen

---

## Sljedeće (kumulativno)

- naturalness_score retroaktivno punjenje (nova skripta, analogna bb_06)
- bb_06 u standardni pipeline redosljed (dokumentacija)
- Prijevodi: hr/sr/it/de → s350; mk/bg → s51–s100
- Cache-Control za js/css (.htaccess)
- about.html i18n; learn.html nove igre

---

*Flavio & Claude · Buchenberg · sesija 74 · 13. jun 2026.*
