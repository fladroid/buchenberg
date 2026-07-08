# Session 121 — Re-orijentacija: propušteni referentni dokumenti + Cowork UI promjena

**Datum:** 8. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Nova Cowork sesija (promijenjena aplikacija) zahtijevala punu re-orijentaciju
umjesto uobičajenog brzog nastavka. Otkriveno da Claude nikad nije čitao sadržaj 6
ključnih referentnih dokumenata (ANALIZA.md, KONCEPT.md, KAKO-KeyConcepts.md,
KAKO-JeziciUI.md, WEB-FAZA1.md, STRANICE.md) niti WEB-FAZA3.md nacrt — oslanjao se
isključivo na sažetke u memoriji/session dokumentima. Nula izmjena na pipeline/web
kodu ili bazi — isključivo re-grounding i popravka checklist procedure.

## Health snapshot
Samo posmatrano, ništa mijenjano: bb_recenice 50.624, bb_prevodi_recenica
1.481.930+ (raste u pozadini, Flaviovi runovi), bb_prev_recenica 287.978+.
Git: buchenberg HEAD 439393f (s120), buchenweb HEAD 5d2f470 (s120) — oba netaknuta.

## Urađeno

### 1. Cowork UI promjena — razjašnjeno
Aplikacija uvela spojeni Chat+Cowork "home" (zvanično, release 7. jul) + eksplicitni
"Manual/Skip" switch, zatečen na Skip. Razjašnjena dva nezavisna sloja (sistemski
switch vs. chat-dogovor "prikaži→OK→izvrši"). Flavio vratio switch na Manual.

### 2. Prošireni checklist (6 umjesto 3 session doca, Flaviova odluka za ovu sesiju)
s115-s120 pročitani. Otkrivena s120 lekcija #1: kršenje protokola "prikaži→OK→izvrši"
(6+ pisanja bez pojedinačnog OK) desilo se ranije istog dana — vjerovatno isti
incident koji je Flavio pomenuo na početku ove sesije.

### 3. Šest referentnih dokumenata pročitano PRVI PUT (sirov sadržaj, ne sažetak)
ANALIZA.md, KONCEPT.md, KAKO-KeyConcepts.md, KAKO-JeziciUI.md, WEB-FAZA1.md,
STRANICE.md. Flavio eksplicitno insistirao — do sada oslanjanje samo na
memoriju/session sažetke.

### 4. WEB-FAZA3.md otkriven i verifikovan protiv koda
Nacrt (nema izvršenih izmjena), pisan 8. jula — konsoliduje "stats dvije tabele" i
"fazni pobjednik na webu" (otvoreno od s102/s104/s107/s108) u jedan plan (Nivo A:
dodati faza_id gdje JOIN već postoji; Nivo B: koristiti bb_prev_recenica_faza za
prije/poslije prikaz). Provjereno protiv `bb_web_export.py`/`bb_xray_export.py`:
tvrdnje dokumenta tačne (bb_xray_export već ima fazu; bb_web_export nema, ni
get_translations ni get_stats).

### 5. Provjera .bak fajlova i buchenweb stanja
30 `.bak_*` fajlova (8 buchenberg + 22 buchenweb, s96-s120), 1.4M ukupno — svi
prisutni, brisanje odgođeno. buchenweb git status čist, sinhronizovan.

## Lekcije

1. **Checklist korak 1 bio nepotpun** — pominjao samo buchenberg_napomena.md i
   "X-Ray dokumente", ne i KONCEPT/ANALIZA/KAKO-*/STRANICE/WEB-FAZA*. Ovi dokumenti
   pisani su TAČNO zato da Claude ne mora nagađati — a nisu bili dio rutine. Popravka
   u README ovaj session.
2. **Grep pretraga nije sveobuhvatna** — pretraga sadržaja "faza 3" nije pronašla
   WEB-FAZA3.md (naziv fajla, ne pokriven regexom). Ne pretpostavljati da jedan
   pokušaj pretrage pokriva sve varijante zapisa.
3. **buchenberg_napomena.md / _new.md zastarjeli** naspram aktivnih referentnih
   dokumenata — vrijedi razmotriti da li ih uopšte čitati ubuduće ili ih ukloniti iz
   checklista u korist KONCEPT.md.
4. **"Prevođenje/refine je Flaviov posao"** već zapisano u session_120.md, ali
   izgubljeno do danas — potvrđuje METHOD.md tezu da invarijante ne smiju živjeti
   samo u memoriji/session dokumentima. Premješteno u README ovaj session.

## Otvoreno / sljedeći koraci
1. WEB-FAZA3.md — čeka Flaviovu odluku (Nivo A/B, i dizajn-pitanje oko Tabele 1).
2. Refine faza (2) za copy knjige + puni runovi preostalih jezika — Flaviov posao.
3. `.bak_*` fajlovi (30) — brisanje odgođeno.
4. Razmotriti selidbu invarijanti (protokol, "refine je Flaviov posao") u Custom
   Instructions (METHOD.md §7).
5. Sitni nedirani bugovi iz s120: SR `geo_c4_p1` miješanje pisma, word cloud ćirilica.

## Git
- buchenberg: README.md ažuriran + session_121.md — commit slijedi.
- buchenweb: netaknuto.
- Baza: netaknuta.

---
*Flavio & Claude · Buchenberg · sesija 121 · 8. jul 2026.*
