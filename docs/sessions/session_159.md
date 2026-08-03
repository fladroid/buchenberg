# Sesija 159 — 3. avgust 2026.

## Otvaranje sesije
Standardni checklist proveden (project files, README, zadnja 3 session dokumenta, health check). Memorija je na početku bila ažurna do s141 (stariji sažetak) — README/session dokumenti otkrili stvarno stanje s158, potvrđujući ponovo pravilo da se čita uživo, ne oslanja na memory sažetak.

## Dio 1 — Batch size fix za gated-base refine (bez seeda)
**Problem:** u `bb_03_prevod.py`, veličina batch-a je zavisila samo od `is_refine` (faza≥2), ne od toga da li se seed stvarno šalje modelu (`PROMPT_NAZIV != 'base'`). Gated faza 10 (glm, base prompt, bez seeda) je pogrešno dobijala `REFINE_BATCH_SIZE=5` umjesto `BATCH_SIZE=20`, iako pada u istu granu koda (`prevedi_batch()`) kao obični root prevod.

**Flaviov zahtjev:** ako nema seeda za prevođenje, batch=20; inače batch=5 kao do sada. Dodatno: log naslov ("Refine: X sa seedom") treba pratiti stvarno stanje — "bez seeda" kad se seed ne šalje.

**Izmjena:** nova promjenljiva `uses_seed = is_refine and PROMPT_NAZIV != 'base'`, korištena i za `step` (batch veličina) i za wording print-a (`"sa seedom"` / `"bez seeda"` uslovno, ne fiksni tekst).

**Mikro test:** k22 (Hound Copy), opseg 1000-1009 (provjereno upitom da je potpuno nedirnut prije testa), core-4 jezici (de/hr/it/sr), cijeli lanac (root→sudija→pobjednik→gated faza 10→sudija→pobjednik). Bez greške, bez exception-a; "bez seeda" ispravno ispisano u logu.

**Commit:** `f68d367` — "bb_03_prevod.py: batch=20 za refine bez seeda (gated-base), 5 za pravi refine sa seedom; naslov 'sa seedom'/'bez seeda' prati stvarno stanje umjesto fiksnog teksta".

## Dio 2 — Analiza k20 (kvalifikovane rečenice i pobjednici)
Dva ad-hoc SQL upita na knjizi 20 (Dracula), na Flaviov zahtjev:

1. Rečenice-jezik gdje SVAKI prisutan LLM model ima >1 prevoda I prosjek ocjena>0.95, I postoji barem jedan NLLB prevod>0.95 — razloženo po jeziku i modelu. Core-4 (de/hr/it/sr) dominira brojevima (186-685 po modelu, prosjek ~0.976-0.979); ostalih 10 jezika pokriveno samo starim gemma3/ministral parom u malim brojevima (2-12), jer nisu kasnije dopunjavani novim modelima.

2. Pobjednici (`v_pobjednici_full`, apsolutni) sa `finalni_score>0.95`, po jeziku/modelu. Core-4 jezici: glm-5.2/mistral-large-3 dominiraju (2000-3300 po modelu); ostali jezici samo stari par + malo NLLB.

Oba upita čisto informativna, bez promjena u bazi.

## Dio 3 — Ideja 1 iz s157 revisited: podjela glm gated faze po temperaturi ("treći svijet")
Flavio predložio: root kao sada (svijet 2), zatim glm@0.8 uslovno (za rečenice ispod praga), pa glm@0.1 uslovno — sekvencijalno umjesto zajedno kao sad (faza 10 trenutno šalje oba temp-a odjednom).

Claude upozorio na nijansu: README §3 pattern (izmjeren na starim gemma3/ministral modelima) predviđa različitu "bolju" temperaturu po jezičnoj porodici (de→0.8, hr/it/sr→0.1) — redoslijed bi trebalo prilagoditi, ne nagađati na osnovu novog modela.

**Retrospektivna analiza** na POSTOJEĆIM podacima faze 10 (oba temp-a već aktivna zajedno od s154, bez ijednog novog API poziva): usput otkriven i ispravljen float-precision bug — direktno poređenje `model_temperatura=0.8` tiho nije pogađalo (real kolona), ispravljeno sa `ROUND(model_temperatura::numeric,1)=0.8`.

Stvarni glm-5.2 nalaz (n=380-473 po core jeziku): **0.1 rješava isto ili više nego 0.8 u sva četiri core jezika** — uključujući de, gdje stari pattern predviđa suprotno:

| jezik | riješi 0.8 samo | riješi 0.1 samo |
|---|---|---|
| de | 85 | 89 |
| hr | 100 | 100 |
| it | 88 | 90 |
| sr | 99 | 109 |

Zaključak: stari pattern (izmjeren na drugim modelima) se ne prenosi direktno na glm-5.2. **Preporučen redoslijed: 0.1 prvo, pa 0.8** (ne 0.8-pa-0.1 kako je Flavio prvo predložio) — Flavio prihvatio.

Procjena uštede: ~23% rečenica (388/1688) riješi se jednim pozivom umjesto dva → ~11.5% manje glm poziva unutar ove populacije; gruba procjena ~10% dodatne ukupne uštede ako se prenese proporcionalno na potrošnju (neprovjereno na stvarnom radu).

Strukturna napomena data Flaviju (iz pouke s157/158): implementirati kao **dvije odvojene trajne faze**, ne toggle postojeće faze 10 — svaka faza svoj INSERT, nikad prepisivanje usred izvršavanja.

**STATUS: analiza/preporuka gotova, implementacija NIJE urađena.** Čeka se da Flavio završi tekući k12 prevod.

## Dio 4 — KAKO-NovaFaza.md potvrđen
Flavio pitao da li postoji how-to dokument za novu fazu/novi svijet. Potvrđeno: `docs/KAKO-NovaFaza.md` (ažuriran 2. avgusta, s158) pokriva standardnu novu fazu, gated (bez seeda) fazu, i protokol deklarisanih svjetova (`bb_deklarisi_svet.py`, imenovane skripte). Dovoljan za planirani "treći svijet" (koji strukturno nije nov root, nego dvije nove gated faze — root ostaje isti kao `bb_svet_2.sh`).

## Dio 5 — Digresija: real/user/sys vrijeme (edukativno)
Flavio pitao objašnjenje `time` izlaza (real vs user vs sys), konkretno njegov primjer (real=7m28s, user=9m47s, sys=9.8s). Objašnjena sva tri slučaja:
- real<user → paralelizam preko više jezgara (njegov slučaj, ~1.33 jezgra prosječno zauzeto — pipeline prirodno paralelizuje pozive po jeziku).
- real≈user → jednonitni CPU-bound rad.
- real>user → čekanje na mrežu/I/O (tipično za pojedinačan Ollama Cloud poziv).

## Dio 6 — Praćenje troška na k12 (Moby Dick, svijet 2 + gated faza 10)
Flavio pokrenuo normalan (ne test) prevod k12 na 4 jezika (de/hr/it/sr), segmentirano, prateći Ollama sedmičnu potrošnju:

| kumulativno rečenica | % (kumulativno) | %/100 (prosjek) |
|---|---|---|
| 100 | 1.1% | 1.1% |
| 200 | 1.5% | 0.75% |
| 400 | 2.9% | 0.725% |

Prva tačka (1.1%) potvrđuje ranije izmjereni efekat batch fixa iz Dijela 1 (1.7%→1.5%→1.1% progres istog dana) — ponovljivo, ne šum.

**Otkrivena značajna razlika po jeziku** u istom bloku (8601-9000, % rečenica koje trebaju glm nakon root gate-a):

| jezik | % treba glm |
|---|---|
| it | 36.0% |
| de | 42.25% |
| hr | 47.75% |
| sr | 49.5% |

Raspon do 14 procentnih poena na istom izvornom tekstu. Poklapa se sa jezičnim porodicama (romanski<germanski<južnoslovenski) — isti obrazac grupisanja kao README §3 pattern, ali mjeri drugu stvar (koliko root sam pokriva prije nego glm uđe u igru, ne koja glm temperatura je bolja).

## Dio 7 — Buduće knjige vs jezici (X-Ray refleksija + NLLB provjera)
Flavio pitao mišljenje: dodati još engleskih klasika ili dodati jezike. Claude dao argumentovan odgovor (jezička asimetrija iz X-Ray dokumenta pogl. XI, uporedivost troška ~42k vs ~50k novih prevoda, preporuka pilot-pristupa za nov jezik zbog tehničkog rizika NLLB/sudije na neprovjerenom jeziku).

Flavio otkrio dugogodišnju sklonost ka jezicima: grčki (najzanimljiviji), albanski, mađarski, turski — plus pitanje latinski/esperanto i da li postoji poseban kod za starogrčki.

**Provjera na zvaničnoj FLORES-200/NLLB-200 tabeli** (github.com/facebookresearch/flores):
- Grčki (`ell_Grek`), albanski (`als_Latn`, Tosk), mađarski (`hun_Latn`), turski (`tur_Latn`), esperanto (`epo_Latn`) — **svi podržani**.
- Latinski — **nije podržan** (nema `lat_Latn` u cijeloj listi od 200 jezika).
- Starogrčki — **ne postoji odvojen kod**, samo moderni (`ell_Grek`).

## Dio 8 — Preuzet Gutenberg katalog
`data/external/pg_catalog.csv` preuzet sa `https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv.gz` (zvanični "Offline Catalogs" feed), 21MB raspakovano, .gz original sačuvan.

**Pravi CSV parsing** (Python `csv` modul, ne `wc -l` zbog multi-line naslova u quoted poljima): **79.071 stvarnih zapisa** (ne 90.420 sirovih linija — razlika potvrđuje ranije upozorenje).

120 jedinstvenih jezika; top: en(62.643), fr(4.144), fi(3.665), de(2.417), it(1.106), nl(1.104), es(887), hu(654), pt(644), zh(436), sv(253), el(216), eo(124), la(103), ca(94).

Svih 9 naših izvornih Gutenberg ID-jeva potvrđeno prisutno u katalogu (unakrsna provjera Text# ↔ `bb_knjige.gutenberg_id`, tačno poklapanje naslova).

Nema kolone za veličinu fajla u ovom feed-u. Žanr aproksimiran preko `Subjects`/`Bookshelves`/`LoCC` kolona — demonstrirano na 4 postojeće knjige (Frankenstein, Flatland, Dracula, Hound).

Fajl NIJE dodat u git (`.gitignore` isključuje `data/` globalno, po ustaljenoj konvenciji) — živi samo na serveru, lako se ponovo preuzima po potrebi.

## Dio 9 — Timeout istraga na batch=20 (kritičan operativni nalaz)
Flavio zatražio provjeru logova, sumnjajući da je 800 rečenica "previše u jednom komadu" (opseg 9001-9800, k12, core-4).

**Nalaz:** nije ukupan broj rečenica problem, nego **batch=20** (direktna posljedica fixa iz Dijela 1) koji se sudara sa fiksnim 120s Ollama Cloud read-timeout-om na velikim generacijama — pogotovo kasnije unutar dugih (6+ satnih) neprekidnih sesija.

Konkretni brojevi za opseg 9001-9800 (764 stvarne rečenice × 4 jezika):

| jezik | timeout događaja | potpun neuspjeh (3/3 pokušaja) |
|---|---|---|
| de | 12 | 1 batch (~20 rečenica trajno bez glm pokušaja) |
| hr | 5 | 0 (retry spasio sve) |
| it | 17 | 2 batch-a (~40 rečenica) |
| sr | 6 | 0 (retry spasio sve) |

Poređenje sa ranijim opsezima istog runa (8401-8600, 8601-9000): 0-4 timeout-a, **nula** potpunih neuspjeha — jasna eskalacija kroz vrijeme unutar istog dugog runa, ne slučajan šum.

Pobjednik i dalje pokriva 100% rečenica (root kandidati mistral/nllb kao fallback čak i kad glm batch potpuno propadne) — nema gubitka finalnog rezultata, samo su neke "teške" rečenice ostale bez glm pokušaja u ovom krugu.

Usput: Claude prvo pogrešno prijavio "9-10 dodatnih grešaka" po fajlu — grep lažna uzbuna (pattern `503` pogodio brojeve pozicija poput `s8503`), ispravljeno i priznato odmah po provjeri.

Hipoteza (Claude, neprovjerena, ponuđena kao mogućnost): eskalacija kroz vrijeme mogla bi biti dodatno pojačana približavanjem Ollama-inom 5-satnom rolling limitu (ne samo latencijom batch-a).

**Flaviova odluka:** isključuje 5-satnu teoriju kao glavni uzrok (napominje da je to "mač sa dvije oštrice" otkad je batch=20 uveden — svjestan trade-offa). Preferira **stepenasti retry backoff**: 1. pokušaj čekanje 30s, 2. pokušaj 60s, 3. pokušaj 120s (umjesto sadašnjeg fiksnog 30/30/30s). Vjerovatno će se vratiti na **maksimalno 400 rečenica po sesiji prevoda** kao operativnu naviku.

**STATUS: nije implementirano** — samo odluka/preferenca zabilježena za sljedeću sesiju.

## Stanje na kraju sesije
- Korpus: **50.624 / 1.905.033 / 360.832** (rastao tokom sesije — Flaviov k12 rad paralelno sa analizom)
- Git (buchenberg): čist, zadnji commit `f68d367` (batch fix, Dio 1)
- Git (buchenweb): čist, nedirnut ove sesije
- BB_VERSION: ostaje s157 (web nedirnuto ove sesije)
- k12 (Moby Dick) prevod u toku na de/hr/it/sr, Flavio nastavlja nezavisno van sesije
- `data/external/pg_catalog.csv` dostupan na serveru za buduću analizu (nije u gitu)

## Otvoreno za sljedeću sesiju
1. Implementirati "treći svijet" — dvije nove trajne gated faze (glm@0.1 prvo, glm@0.8 uslovno drugo), redoslijed potvrđen retrospektivnom analizom ove sesije (Dio 3)
2. Implementirati stepenasti retry backoff (30/60/120s) u `bb_03_prevod.py` za Ollama pozive — Flaviova preferenca (Dio 9)
3. Pratiti da li se timeout eskalacija ponavlja u budućim dugim (>4-5h) runovima i sa produženim retry-em — provjeriti da li Flaviov zaključak (5h-limit isključen kao uzrok) i dalje drži na većem uzorku
4. Nastaviti/završiti k12 prevod (trenutno u toku)
5. Kad "treći svijet" proradi na k12, uporediti stvarni trošak sa svijet 1 (1.7%) i svijet 2 (1.1% nakon batch fixa) — direktno mjerenje umjesto procjene
6. (Dugoročno) Razmotriti pilot novog jezika (grčki/albanski/mađarski/turski/esperanto — svi NLLB-podržani, potvrđeno Dio 7) na par knjiga prije punog obima od 21; razmotriti nove engleske klasike iz `data/external/pg_catalog.csv` kao alternativu

## Lekcije sesije
- **Float poređenje na `real` koloni tiho ne pogađa** (`model_temperatura=0.8` u WHERE/FILTER) — mora `ROUND(x::numeric,1)`. Postojeće pravilo iz ledgera (`ROUND(temperatura::numeric,4)`) pokrivalo je prikaz/agregaciju; sad potvrđeno da isto važi i za direktno poređenje u filterima, ne samo za formatiranje izlaza.
- **Batch veličina i broj API poziva utiču na trošak nezavisno jedno od drugog** — manji broj poziva smanjuje overhead, ali veći batch povećava rizik od timeout-a. Optimizacija jedne ose (broj poziva, Dio 1) otkrila je osjetljivost na drugoj osi (pouzdanost/latencija, Dio 9) koja na starom batch=5 nije bila vidljiva.
- Prije predlaganja izmjene parametra koji mijenja broj/veličinu API poziva, projektovati efekat na stvarnu potrošnju/pouzdanost, ne samo na funkcionalnu ispravnost koda — Claude je ovo propustio kod prvog predloga batch fixa (priznato direktno Flaviju kad je pitao zašto nije uočeno unaprijed).
- Kad je pattern/metrika izvedena na starijem/drugom modelu (README §3, gemma3/ministral), ne treba je slijepo prenijeti na novi model (glm-5.2) — provjeriti retrospektivno na stvarnim podacima novog modela prije odluke, pogotovo kad ti podaci već postoje besplatno (bez novih API poziva), kao u Dijelu 3.
- Sesija zatvorena SAMOSTALNO od Claudea (Flavio eksplicitno autorizovao: "sve detaljno dokumentuj do kraja ovog puta bez moje provjere i odobrenja").
