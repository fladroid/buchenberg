# Session 113 — Copy knjige: kontrolna grupa za poređenje starih i novih modela

**Datum:** 5. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Flaviova ideja — fizičke kopije potpuno prevedenih knjiga kao nove knjige u library-ju; original (stari modeli) postaje zamrznuta referenca, Copy se prevodi novim modelima → direktno poređenje na punom korpusu umjesto n=42 (s110).

---

## Health snapshot (početak)
- bb_recenice: 38.333 · bb_prevodi_recenica: 1.361.660 · bb_prev_recenica: 262.936 (rast od s112 očekivan — Flaviovi procesi trče kroz sesiju)
- Git ulaz: buchenberg dcc1b6c (s112), buchenweb e1278f7 (s108.4). BB_VERSION s108.4.
- Health check čist, sve zeleno. Frankenstein rep pobjednika (3184/3384 na de/hr/it/sr) = tekući procesi; Flavio potvrdio: id 8 danas dovršen.

## Koncept (Flaviova ideja, prihvaćena)
- Copy knjiga = **obična nova knjiga**: svoj id, svoje rečenice, nula prevoda, pipeline/library/web je ne razlikuju. Nula posebnih slučajeva.
- Original ostaje netaknut → zamrznuta kontrolna grupa starih modela; poređenje ostaje validno i poslije retirementa 15. jula (swap-dizajn s110 to nije mogao — trebao je oba para živa).
- Copy se prevodi tek NOVIM parom (mistral-large-3:675b + glm-5.2) poslije implementacione sesije → original vs Copy = staro vs novo na 12.291 rečenici po jeziku.
- Sva analitika (v_prevodi_full, brojači, stats) pokriva Copy automatski — poređenje je samo SQL nad postojećim view slojem.
- U duhu KONCEPT.md: ne gradi se novi mehanizam, isti proces na novom ulazu.

## Odluke (Flavio)
1. **3 knjige** (ne svih 5 potpunih — 3 su dovoljne): Hound (1), Big Four (5), Frankenstein (8) — tri autora, tri žanra, tri epohe jezika; 12.291 rečenica po jeziku.
2. **Naziv:** sufiks " Copy".
3. **gutenberg_id konvencija:** string → original + "c" (kolona je varchar(50), nalaz sesije; README tabela prikazuje brojeve ali tip je string). UNIQUE constraint (s41) zadovoljen, porijeklo vidljivo.
4. **Bez backupa** — operacija aditivna, reverzibilna jednim DELETE-om.
5. Kopiranje izvršeno ODMAH (prije implementacione sesije) — bezbjedno: čita bb_knjige/bb_recenice, procesi pišu u bb_prevodi_*; ne dodiruju se.

## Izvršenje (2 koraka + 2 provjere)
1. `INSERT INTO bb_knjige ... SELECT naziv||' Copy', autor, gutenberg_id||'c' WHERE id IN (1,5,8) RETURNING ...` → **id 22 (2852c), 23 (70114c), 24 (84c)**
2. `INSERT INTO bb_recenice (knjiga_id, pozicija, tekst) SELECT CASE...END, pozicija, tekst WHERE knjiga_id IN (1,5,8)` → `INSERT 0 12291` (3852+5055+3384, tačno)
3. Kontrola COUNT/MIN/MAX pozicija: parovi 1↔22, 5↔23, 8↔24 identični, bez rupa.
4. Kontrola sadržaja (JOIN po poziciji, `COUNT FILTER WHERE o.tekst<>c.tekst`): **0 razlika u sva tri para** — kopije bit-identične.

## Stanje na izlazu
- Baza: +3 reda bb_knjige (id 22/23/24) · +12.291 red bb_recenice · ništa mijenjano ni brisano; korpus sada 50.624 rečenice (38.333+12.291)
- Kod: NETAKNUT
- Web: kod netaknut → BB_VERSION ostaje s108.4. Flavio pustio `bb_web_export.py` — Copy knjige vidljive u library-ju, bez prevoda (data-only regeneracija, potvrđeno vizuelno).
- Napomena za budućnost: `bb_02_insert_knjiga.py` KNJIGE lista ne zna za Copy knjige (išli smo direktno kroz bazu; baza je izvor istine, ali rekonstrukcija od nule ih ne bi obuhvatila).

## Sljedeće
1. **Implementaciona sesija ("jedan dah")** — nepromijenjeno iz s112: backup → shema → skripte → test, novi par mistral-large-3:675b + glm-5.2, rok prije 15. jula. Flavio prekida svoje procese kad završe i javlja se.
2. Prvi run novog para može ići direktno na Copy knjige (id 22/23/24) → poređenje kreće.
3. Otvoreno iz s107/s108 nastavlja se (brojači faze 2, stats dvije tabele, web fazni pobjednik).

---

*Flavio & Claude · Buchenberg · session 113 · 5. jul 2026.*
