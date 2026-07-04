# Session 110 — Test kandidata gemma3:27b + ministral-3:8b (Dracula/bs, swap-dizajn)

**Datum:** 4. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** produkcijski test kvaliteta kandidata za zamjenu (iz s109) kroz pravi bb_03+bb_08, uz otkriveni hardkod u bb_08_sudija.py i procesnu lekciju.

---

## Health snapshot (početak)
- bb_recenice: 38.333 · bb_prevodi_recenica: 1.274.200 · bb_prev_recenica: 246.760 (rast od s109 očekivan — Flaviovi noćni procesi)
- Git ulaz: buchenberg (s109 commit), buchenweb (s108.4). BB_VERSION s108.4.
- Aktivni paralelni proces zatečen na početku: ministral-3:14b na Frankenstein (knjiga 8), poz. 2801–3000, jezici bg/bs/mk/sl — nije diran, test je pušten paralelno (potvrđeno s100: 5 paralelnih cloud tokova rade bez grešaka).

## Kontekst
Nastavak s109: rok 15. jul 2026 (Ollama retire gemma3:12b + ministral-3:14b). Cilj sesije: test kvaliteta kandidata gemma3:27b + ministral-3:8b prije eventualne pune zamjene.

## 1. Registracija modela + float-trap u INSERT...SELECT
gemma3:27b i ministral-3:8b registrovani u `bb_modeli` (id 14–17, @0.8/@0.1, `faza_id`=1 nasljeđen od odgovarajućeg starog modela preko SELECT-a). Prvi pokušaj (`INSERT...SELECT...UNION ALL` s filterom `temperatura=0.8` bez ROUND) vratio `INSERT 0 0` bez ikakve greške — tiha posljedica float precision problema na izvoru SELECT-a, ne samo na čitanju. Fix: `ROUND(temperatura::numeric,4)=X` mora ići i u SELECT-izvor ove vrste upita, ne samo u obične čitajuće upite (postojeće pravilo prošireno na noviji slučaj).

## 2. Otkriven hardkod u bb_08_sudija.py (OCJENJIVANI_MODELI)
Sudija pokrenut na virgin opsegu (samo novi modeli, bez ijednog starog kandidata) javio "Nema rečenica za ocjenjivanje (sve već ocijenjene)" — dijagnoza netačna, `sudija_avg` je bio NULL na svih 84 provjerenih redova. Uzrok: `OCJENJIVANI_MODELI` (linija 37) je hardkodovana lista pet imena (gemma3:12b, ministral-3:14b, nllb-600M, + 2 refine varijante); upit filtrira isključivo po njoj. Novi modeli nisu na listi → 0 kandidata unutar filtera → prazan skup pogrešno prijavljen kao "sve ocijenjeno". Ovo uživo potvrđuje već poznati otvoreni TODO iz README §14 ("refaktor OCJENJIVANI_MODELI → kolona grupa u bb_modeli").

**Flaviova odluka:** ne dirati produkcijski `bb_08_sudija.py`. Napravljena kopija `bb_08_sudija1.py` s `OCJENJIVANI_MODELI` proširenim za gemma3:27b i ministral-3:8b. Kopija ostaje na disku za buduće testove — treba ponovnu izmjenu ako se doda refine.

## 3. Test dizajn (Flaviov, swap A/B/C)
Knjiga Dracula (id=20), jezik bs, 42 rečenice virgin opsega (5001–5021, 6001–6021):
- **A:** stari modeli (gemma3:12b, ministral-3:14b) na 5001–5021; novi (gemma3:27b, ministral-3:8b) na 6001–6021. Sudija (`bb_08_sudija1.py`). Rezultati sačuvani.
- Brisanje oba opsega (FK-safe — samo djeca u `bb_prevodi_recenica`; `bb_prevodi_knjige` roditelj netaknut jer novi modeli još trebaju drugi opseg).
- **B:** swap — novi modeli na 5001–5021, stari na 6001–6021. Sudija ponovo. Rezultati sačuvani.
- **C:** A+B kombinovano = svaki par modela preveo identičnih 42 rečenice, redoslijed prevođenja unakrsno kontrolisan.
- Finalno brisanje oba opsega — baza vraćena u prvobitno (virgin) stanje, ništa trajno u produkciji osim registracije modela.

## Rezultat testa

| Porodica | stari (avg fin) | novi (avg fin) | t (uparen, n=42) | head-to-head |
|---|---|---|---|---|
| gemma3 | 0.9085 | 0.8742 | 1.23 | 22:19 (1 nerešeno) |
| ministral | 0.8500 | 0.8346 | 0.70 | 20:21 (1 nerešeno) |

Pravac dosljedan (stari blago ispred u prosjeku, u obje porodice), ali statistički neodlučiv (t ispod praga značajnosti na n=42). Head-to-head gotovo 50/50. **ZAKLJUČAK (Flaviova korekcija na Claudeov prvi nacrt):** nedovoljno za odluku u bilo kom smjeru — treba veći uzorak ili ponavljanje na drugoj knjizi/opsegu prije odluke o zamjeni.

Flaviov komentar o očekivanjima: nije imao hipotezu unaprijed — zamjena je iznuđena (retirement), izabrani par je dovoljno sličan starom od ponuđenih opcija.

## Procesna lekcija (dvije odvojene Flaviove korekcije)
1. Claude je više puta predlagao provjere (grep/SELECT/`\d`) za pitanja koja su već odgovorena u ranijim sesijama — trebalo je prvo `conversation_search` + README/ANALIZA.md, tek onda probe na server ako info stvarno nedostaje.
2. Claude je kroz cijeli test izvršavao korak-po-korak i na kraju samo pitao "da obrišem?" bez da traži Flaviovo tumačenje rezultata ili iznosi svoje mišljenje — nekolegijalno. Ubuduće: iznijeti opažanje/mišljenje i pitati Flaviovo prije/uz prelazak na sljedeći korak, ne samo izvršavati i prijavljivati.

## Stanje na izlazu
- Baza: `bb_modeli` ima 4 nova trajna reda (gemma3:27b, ministral-3:8b, id 14–17, faza_id=1) — registracija ostaje. Sve test-rečenice (`bb_prevodi_recenica`) za opsege 5001–5021 i 6001–6021 na Dracula/bs OBRISANE — baza vraćena u prvobitno stanje za te opsege.
- Kod: `src/bb_08_sudija1.py` (nova, test-kopija s proširenom `OCJENJIVANI_MODELI` listom) → commit. Produkcijski `bb_08_sudija.py` NETAKNUT.
- Web: NETAKNUT → BB_VERSION ostaje s108.4.
- README: §3 napomena o registrovanim kandidatima, §7 nova skripta + float-trap napomena, §9 s110 snapshot red, §14 TODO ažuriran.

## Sljedeće
1. Odluka o punoj zamjeni ostaje OTVORENA — test neodlučiv, treba veći uzorak (npr. 100+ rečenica) ili ponavljanje na drugoj knjizi prije 15. jula.
2. Ako se ide na veći test: isti recept (`bb_08_sudija1.py`, swap A/B/C dizajn) na novom opsegu.
3. Kad/ako se odluka donese: pravi refaktor `OCJENJIVANI_MODELI` → kolona u `bb_modeli` (umjesto ručnih kopija `bb_08_sudija*.py`).
4. Otvoreno iz s107/s108/s109 nastavlja se nepromijenjeno (brojači faze 2, web fazni pobjednik, stats dvije tabele).

---

*Flavio & Claude · Buchenberg · session 110 · 4. jul 2026.*
