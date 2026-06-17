# Session 88 — 17. jun 2026.

**Fokus:** Web portal SR ekavica fix + infrastruktura napomena + analiza Hound/DE

---

## Checklist

- Project files pročitani (buchenberg_napomena.md, buchenberg_napomena_new.md, X-Ray SR/EN)
- README pročitan (V3, s87)
- Sessions 84, 85, 87 pročitane
- Health check: sve zeleno
  - 38.333 rečenica
  - 189.182 prevoda
  - 19.683 pobjednika
  - buchenberg: `51ae6f0` (s87) ✅
  - buchenweb: `6e279dd` (s87) ✅

---

## Šta je urađeno

### 1. Analiza Hound/DE pobjednika

Flavio je primijetio ~40 nepotpuno prevedenih rečenica u Hound/DE.

**Nalaz:**
- Prvih 100 rečenica: svih 5 kandidata za sve 4 jezika (de, hr, it, sr) ✅
- Hound/DE pobjednici: 1100 (s1–s1100)
- Od s1101 do s3852: samo NLLB prevodi, bez LLM kandidata — pipeline nije pokrenut za taj opseg
- Stanje je konzistentno — pobjednici se biraju samo kad je pipeline kompletno pokrenut

**Lekcija:** `bb_04_pobjednik.py` se pokreće za opseg koji je preveden. Pokretanje za neprevedene rečenice gubi vrijeme bez rezultata.

### 2. about_p_infrastructure — Ubuntu napomena

Dodato "both running Ubuntu" u Infrastructure paragraf za svih 5 jezika:
- EN: "...both running Ubuntu."
- DE: "...beide unter Ubuntu."
- IT: "...entrambi con Ubuntu."
- HR: "...oba s Ubuntu sustavom."
- SR: "...оба са Ubuntu системом."

Commit: `6c7e1a7`

### 3. SR ekavica fix — Home stranica

Ispravljeni ijekavizmi:
- намјерни → намерни
- прошириен → проширен (i bug)
- њемачком → немачком
- дјелује → делује
- слијепи → слепи
- вјерност → верност
- Побједник → Победник
- мјери → мери
- оцјењује → оцењује
- побјеђује → побеђује

Commit: `c641654`

### 4. SR ekavica fix — About stranica

Ispravljeni ijekavizmi:
- намјерни → намерни
- њемачки → немачки
- писаној ријечи → писаној речи
- процијенити → проценити
- захтијевају → захтевају
- slијепим → слепим
- Побједник → Победник
- опће намјене → опште намене
- ријеч по ријеч → реч по реч
- вриједности → вредности
- увијек → увек
- досљедан → доследан
- досљедну вјерност → доследну верност
- мјерила → мерила
- захтијева → захтева
- извјештајем → извештајем
- сјецишту → пресеку
- Двије → Две
- оцјењиван → оцењиван
- широком пресјеку → широком пресеку

Commit: `d409cd4`

### 5. Embeddingi → Embeddings (HR+SR)

Odluka: tehnički termin ostaje na engleskom — konzistentno s ostalim terminima (back-translation, scoring, LLM...).

Commit: `99d02ca`

### 6. SR ekavica fix — Stats stranica

- побједничком → победничком
- захтијевају → захтевају
- просјека → просека

Commit: `3a69021`

### 7. SR ekavica fix — Art stranica

Opsežan zahvat — sve SR ijekavizme zamijenjene ekavskim oblicima:
- осјет → чуло (svugdje — "осет" nije dobar prevod za "sense")
- "Исти подаци, други осјет" → "Исти подаци, друго чуло"
- умјетности → уметности
- недјеља → недеља
- осјетила → чула
- стољеће → столеће
- промијенио → променио
- свјетло → светло
- свјетлосна → светлосна
- дјело → дело
- складатеља → композитора
- унутарњег → унутрашњег
- обје → обе
- темељне → основне
- видјети → видети
- промијенили → променили
- редослијед → редослед
- лијева → лева
- побједника/побједнички → победника/победнички
- пријевод → превод
- умјесто → уместо
- пјева → пева
- лљествицу → лествицу
- исјечак → исечак
- дуљина → дужина
- вриједност → вредност
- вјеран → веран
- сјена → сена
- двије → две
- додијељена → додељена
- уметници уместо умјетници
- његова → Његова (veliko slovo)
- "Тапесерија" → "Taписерија"
- "чуто уместо гледаног" → "слушано уместо гледаног"
- Kandinsky pitanje: "Којим осјетом" → "Кроз које чуло"
- Wittgenstein pitanje: "Kako ga мјеримо?" → "Kako га меримо?" (potpuna ćirilica)

Commit: `3991544`

---

## Stanje na kraju sesije

- Corpus: 38.333 rečenica / 189.182 prevoda / 19.683 pobjednika
- buchenberg: `51ae6f0` (s87) — nije mijenjano
- buchenweb: `3991544` (s88.9) ✅
- BB_VERSION: s88.9 · 17 Jun 2026

---

## Sljedeće

- SR ekavica fix — nastavak po stranicama (Geometry, Learn, NLP, Reader)
- Pipeline: hr/sr/it/de → s350; mk/bg → s51–s100 (prema Flaviovim resursima)
- bb_xray_export.py — pokrenuti za sve knjige i jezike s pobjednicima
- NLP Relation Extraction via Gemma4
- Favicon

---

*Flavio & Claude · Buchenberg · Session 88 · 17. jun 2026.*
