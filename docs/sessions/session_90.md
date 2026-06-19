# Session 90 — 19. jun 2026.

**Fokus:** Key Concepts proširenje (sve stranice + Wikipedia linkovi knjiga) · NLP Relation Extraction koncept (odložen) · git cleanup

---

## Checklist

- Project files pročitani (buchenberg_napomena.md, buchenberg_napomena_new.md, X-Ray SR/EN)
- README pročitan (V3, s88)
- Sessions 85, 87, 88, 89 pročitane (4 umjesto 3, na Flaviov zahtjev; s86 ne postoji — vidi s89)
- Health check: sve zeleno
  - 38.333 rečenice
  - 290.488 prevoda (**+37.736 od s89** — pipeline radio između sesija)
  - 44.322 pobjednika (**+9.579 od s89**)
  - buchenberg: `820f1ce` (s89) ✅
  - buchenweb: `3991544` (s88.9) ✅
  - **Notable:** Hound hr/sr/de/it → 3852/3852 kompletni; Flatland hr/sr/de/it → 1341/1341 kompletni

---

## Napomena o nedokumentovanom radu (s89 → s90)

Dvije stavke iz "sljedećih koraka" su urađene između sesija, ali bez session doca — verifikovano na serveru ove sesije:
- **SR ekavica fix** — sve stranice osim reader (reader nema SR teksta) — commitovano u okviru s88 commitova
- **bb_xray_export.py** — pokrenut za sve knjige × jezike: **126 JSON fajlova** (`xray_<id>_<lang>.json`, 9 knjiga × 14 jezika)

---

## Šta je urađeno

### 1. Key Concepts — proširenje na sve stranice

Postojeća "Key Concepts" sekcija (Wikipedia-linkovani pojmovi iznad footera) bila je samo na 4 stranice (about, geometry, art, nlp). Prošireno na **svih 9 stranica**.

**Mehanika (postojeća, neizmijenjena u suštini):**
- Pojmovi u `data/concepts.json`, ključ po stranici
- `nav.js` renderuje sekciju iznad footera za stranice u `CONCEPT_PAGES`
- Kartica: `icon`, `name` (link na `en.wikipedia.org/wiki/<wiki>`), `description`
- Logika ponavljanja: isti pojam se javlja na svakoj stranici gdje je relevantan (npr. embedding, cosine, MT, LLM)

**nav.js izmjene:**
- `CONCEPT_PAGES` prošireno: `['index','about','geometry','art','nlp','stats','learn','reader','books']`
- Naslov konfigurabilan po stranici: `CONCEPT_TITLES = { books: 'The Books on Wikipedia' }`, default `'Key Concepts'`
- (`index` se ispravno prepoznaje iz praznog pathname preko `|| 'index'`)

**concepts.json — 87 kartica preko 9 stranica:**
- index 9 · about 15 · geometry 12 · art 11 · nlp 9 · stats 8 · learn 8 · reader 6 · books 9
- Princip (Flaviov): ne forsirati broj (reader ostao 6), ne ograničavati ako ima više važnih pojmova (about narastao na 15 zbog lineage pojmova)
- **books**: link po knjizi na Wikipedia članak djela (📖 ikona, autor+godina kao opis)

**Provjereni Wikipedia slugovi** (potencijalno problematični, verifikovani web pretragom):
- Knjige: `Moby-Dick` (crtica), `Strange_Case_of_Dr_Jekyll_and_Mr_Hyde` (bez "The"), `The_Big_Four_(novel)`, `Alice%27s_Adventures_in_Wonderland`
- Koncepti: `Attention_(machine_learning)`, `Tokenization_(lexical_analysis)`, `Ollama`, `Pierre_Menard,_Author_of_the_Quixote`, `Distributional_semantics`, `Family_resemblance`

### 2. NLP Relation Extraction — koncept (ODLOŽEN, "leži")

Duga konceptualna diskusija. Cilj zabilježiti da ne propadne; **nije implementirano, ostavljeno da odleži.**

**Polazni problem:** trenutni Entity Network (nlp.html) povezuje entitete samo ako su u **istoj rečenici** (co-occurrence). Htjeli smo veze između entiteta koji se nikad ne sreću u istoj rečenici.

**Ključni uvidi:**
1. **Summarization-klasa problema, ne co-occurrence.** Relacije između dalekih entiteta zahtijevaju razumijevanje narativa — to je ista sposobnost kao sažimanje (pročitaj cijeli dokument → zgusnut strukturirani izlaz). Sažimanje je riješen, korišten problem; "treba pročitati cijelu knjigu" nije prepreka nego definicija zadatka. Izlaz su relacijske trojke umjesto proze.

2. **Grounding-by-evidence kao nosivi princip.** Ne "kakva je relacija A–B" nego "kakva je relacija + koje rečenice je potkrepljuju". Time: relacija postaje provjerljiva (X-Ray), model je prisiljen u naš tekst umjesto u svoju trening-memoriju (Gutenberg kanon model već "zna"), i dokazne rečenice dolaze iz **različitih dijelova knjige** — što je upravo daleka veza koju co-occurrence ne hvata.

3. **Flaviova nedoumica (tačna):** grounding kao *provjera* vrijedi samo onome ko može prosuditi vezu. Za književno zaključivanje to ne umije ni "pešice". Analogija s množenjem: zna princip, ne može brzo izračunati. → **Rješenje istom logikom koju projekat već koristi:** kao što kvalitet prevoda procjenjuje kosinusom (ne čitanjem jezika), tako i relaciju može provjeriti kosinusnom blizinom tvrdnje i citiranih rečenica. Granica: kosinus daje "na temu/blizu", ne "logički uspostavlja smjer" — djelimična senka, ne dokaz (svjesna X-Ray granica).

4. **Osa: pozicija vs. značenje.** Flaviov prijedlog ±N rečenica = blizina po poziciji (mehanički, potpuno provjerljiv, ali samo blizu + bez tipa veze). RAG = blizina po značenju (hvata daleko, ali vraća LLM crnu kutiju + više mašinerije). Sinteza: semantička co-occurrence u embedding prostoru (bez LLM-a) — Flaviov instinkt + daleki domet + ostaje u kosinusnom svijetu kojem vjeruje. Nijedna mehanička metoda ne daje **tip/smjer** veze — za etiketu treba LLM.

5. **Najjača ideja (Flaviova) — rasplet kao ulaz:** detektivski roman na kraju eksplicitno izgovori relacije (autorov tekst, ne LLM halucinacija). Invertuje teški problem: mali pouzdani isječak (rasplet) → upit → semantička pretraga unazad za potkrepu. Prazni "stadion" (kombinatorni šum) jer juriš samo veze koje rasplet označi. Daje i **zlatni standard za evaluaciju** mehaničkih grafova. Žanrovski uslovljeno: radi za Hound i Big Four (detektivski s raspletom), ne za Moby Dick/Frankenstein/Romeo (nemaju "ko je s kim" rasplet).

**Status:** odloženo na Flaviovu odluku. Cijena greške niska → eventualni eksperiment na Houndu kad bude vremena.

### 3. Git cleanup

**buchenweb:**
- `.gitignore`: `data/` → `data/*` + `!data/concepts.json` (concepts.json je ručni sadržaj, sad pod gitom); `*.bak` → `*.bak*` (budući backupi se ignorišu)
- Obrisani bak fajlovi: nav.js.bak2, .bak_s88, .bak_s88_sr/_sr2/_sr3/_sr4, .bak_s90, reader.html.bak3, data/concepts.json.bak_s90

**buchenberg:**
- `.gitignore`: dodati `fla*`, `nohup.out`
- Odpraćeni `nohup.out` i `flanel.sh` (`git rm --cached`); `fla_llm0.sh`/`fla_llm01.sh` ignorisani (Flavio briše fajlove ručno)

---

## Lekcije

- **Verifikovati nedokumentovan rad prije tvrdnji.** SR ekavica i xray export su bili urađeni ali nezabilježeni — provjereno na serveru (`ls xray_*.json`, git log, grep ćirilice), ne pretpostavljeno.
- **Izuzeti fajl iz ignorisanog direktorija** zahtijeva `dir/*` + `!dir/file`, ne samo `!dir/file` (git ne ulazi u ignorisan direktorij).
- **`.gitignore` `*.bak` ne hvata `*.bak_s90`** — treba `*.bak*`.
- **Ne dati brzu procjenu da bi bilo brzo** (Flaviova primjedba, ponovljena). Kod konceptualnih pitanja ići u dubinu, priznati granice, ne racionalizovati.

---

## Stanje na kraju sesije

- Corpus: 38.333 rečenice / 290.488 prevoda / 44.322 pobjednika
- buchenberg: README ažuriran (s90), git cleanup
- buchenweb: concepts.json (87 kartica), nav.js (CONCEPT_PAGES, konfigurabilan naslov), git cleanup
- BB_VERSION: **s90.1** · 19 Jun 2026
- Browser test: ✅ (Flavio potvrdio)

---

## Sljedeće

- Favicon
- bb_web_export.py refaktor (v_pobjednici view)
- Cache-Control za JS/CSS
- NLP Relation Extraction — leži (vidi gore)
- Pipeline — Flavio vodi, kad ima slobodne resurse

---

*Flavio & Claude · Buchenberg · Session 90 · 19. jun 2026.*
