# Sesija 132 — Analiza runova: paralelno vs sekvencijalno (prvi kontrolisani A/B)

**Datum:** 13. jul 2026.
**Fokus:** Digresija od NER linije — analiza log fajlova prevoda koje je Flavio
pustio nakon duže pauze. Prvi put paralelni i sekvencijalni režim mjereni pod
istim uslovima (iste knjige, isti jezici, isti opseg, susjedne pozicije).
**Ishod:** Raniji zaključak o skaliranju (s119: ≈3.77×, "blizu linearnog")
OPOVRGNUT novim mjerenjem (≈2.47×). Otvoreni konfaundi imenovani, ne prikriveni.
Kod, baza i web NETAKNUTI.

---

## 1. Polazno stanje (health check)

Korpus **narastao** (Flaviovi runovi između sesija — normalno, ne anomalija):
50.624 rečenice · **1.544.460 prevoda** (bilo 1.518.170) · **301.368 pobjednika**
(bilo 296.578). Sve zeleno; 15 .bak fajlova; poznati lažni "buchenweb zaostaje".

**Napomena:** na ove prevode NIJE pokrenut nijedan export (web/xray) — Flavio
namjerno odgađa dok ne bude siguran u ispravnu upotrebu tih skripti. Sekundarno.

## 2. Struktura eksperimenta

| Režim | Logovi | Vrijeme (UTC) |
|---|---|---|
| **Paralelni** (4 istovremena) | k22 1–200 · k23 2501–2700 · k23 2701–2900 · k24 1–200 | start 15:31:42–15:32:39 |
| **Sekvencijalni** (lanac) | k22 201–400 → k23 2901–3100 → k24 201–400 | 20:29:40 → … |

Svi: jezici de/hr/it/sr, opseg 200 rečenica, faza 1.
Sekvencijalni lanac je čist — k23 startuje u sekundi kad k22 završi (22:59:35).
k24 201–400 još trčao na kraju sesije (elapsed 3:13:45, na 4. modelu).

**Zašto je ovo bolji eksperiment od s119:** iste knjige, isti jezici, susjedni
opsezi u istoj knjizi. Mijenja se samo režim. Ranije poređenje bilo je indirektno
(paralelne grupe iz jednog dana naspram "solo" toka drugog dana, druga knjiga,
drugi jezici).

## 3. Rezultati

### Paralelni prolaz

| Proces | Elapsed | rec/min | prevoda/min |
|---|---|---|---|
| k22 1–200 | 4:10:52 | 0.80 | 3.19 |
| k23 2501–2700 | 3:21:26 | 0.99 | 3.97 |
| k23 2701–2900 | 3:26:11 | 0.97 | 3.88 |
| k24 1–200 | 4:34:30 | 0.73 | 2.91 |
| **agregat** | | | **13.95** |

### Sekvencijalni prolaz

| Proces | Elapsed | rec/min | prevoda/min |
|---|---|---|---|
| k22 201–400 | 2:29:55 | 1.33 | 5.34 |
| k23 2901–3100 | 2:14:47 | 1.48 | 5.94 |
| **⌀ solo** | | | **5.64** |

## 4. NALAZ 1 — paralelizam nije besplatan (korekcija s119)

**13.95 / 5.64 = 2.47×**, ne 4×. Efikasnost ~62%.
Pojedinačni proces usporen **1.5–1.7×** kad trči u četvorci
(k22: 8995s solo → 15052s paralelno).

**Zašto je s119 dao 3.77×:** taj faktor izveden je iz solo baseline-a od
**0.924 rec/min** (k23 501–1000). Današnji pravi solo na istoj knjizi:
**1.33–1.48 rec/min**. Stari "solo" bio je precijenjen kao referenca —
vjerovatno i sam degradiran.

⚠️ **README §"Paralelno izvršavanje" i RUNOVI.md (s119) nose 3.77× kao činjenicu
("blizu linearnog skaliranja"). To treba korigovati.**

## 5. NALAZ 2 — dio usporenja je LOKALAN, ne cloud

NLLB je jedini kandidat koji ne dira Ollamu (lokalni CPU, foxuno):

| | paralelno | solo | faktor |
|---|---|---|---|
| k22 nllb | 13m43 | 10m50 | 1.27× |
| k23 nllb | 20m09 / 21m16 | 7m36 | **2.66×** |

Četiri procesa se bore za CPU na foxuno. **Nezavisan instrument** — usporenje nije
samo cloud kontencija, i ne može se objasniti dobom dana.

**Asimetrija po modelima (k22, cloud):**

| model | paralelno | solo | faktor |
|---|---|---|---|
| glm-5.2 @0.1 | 76m36 | 29m08 | **2.63×** |
| glm-5.2 @0.8 | 58m52 | 28m22 | 2.07× |
| mistral-large-3 @0.8 | 39m49 | 26m59 | 1.47× |
| mistral-large-3 @0.1 | 29m12 | 26m59 | **1.08×** |

**glm pati mnogo više od mistrala pod paralelizmom.** Nova, neobjašnjena asimetrija.

## 6. KONFAUND (imenovan, ne uklonjen)

Paralelni prolaz: 17:31–22:06 CEST. Sekvencijalni: 22:29–03:14 CEST.
**"Solo je brži" i "noć je brža" se iz ovih podataka NE MOGU razdvojiti.**
NLLB nalaz drži bez obzira (lokalni CPU), ali cloud faktori mogu biti dijelom
noćni bonus.

Dodatno: k24 201–400 (solo) leži u cjelosti unutar **balsam backup prozora**
(01:00–06:00 UTC) — i najmanje profitira od solo režima (~1.17× naspram 1.67×/1.51×).
Uslovno, run nije završen.

## 7. NALAZ 3 — k24 obrazac je jezično moduliran

Prvi put k24 (Frankenstein Copy) mjeren na core-4 (ranije samo bg/bs/mk/sl,
es/fr/pt/ro, af/nl):

| jezična grupa | k22 glm% | k24 glm% | Δ |
|---|---|---|---|
| bg/bs/mk/sl | 62.5 | 55.5 | 7.0 |
| es/fr/pt/ro | 58.1 | 48.5 | 9.6 |
| af/nl | 59.0 | 47.9 | 11.1 |
| **de/hr/it/sr** | **65.5** | **59.9** | **5.6** |

Efekat knjige je **realan i dosljedan** (k24 uvijek pomjeren ka mistralu), ali mu
**veličina zavisi od jezične grupe** — najslabiji baš na core-4. Dakle nije prosto
"Šelijeva gotska proza izjednačava modele" nego **interakcija sadržaj × jezik**.
Peti uzastopni run potvrđuje smjer, ali nijansira raniju formulaciju (s119/s122).

## 8. Kvalitet — nepromijenjen

Paralelni avg_final 0.9672–0.9705; sekvencijalni 0.9623–0.9666. Razlika je unutar
poznatog šuma (0.960–0.970) i **ne smije se pripisati režimu** — to su različite
rečenice (drugi opsezi). **Paralelizam ne kvari kvalitet.** To stoji.

## 9. Flaviova hipoteza — "umorna baza"

> "Ja sam dugo vrlo intenzivno pustao prevode... Sada je već više dana ništa
> intenzivno na bazi nije rađeno. Da li je baza imala vremena da izračuna neke
> statistike, da interno commituje podatke i metadata?"

**Ne objašnjava paralelno vs sekvencijalno** (oba istog dana, par sati razmaka;
`bb_04_pobjednik` = 20–24s naspram 2–4h ukupno → pipeline je LLM-bound).

**Ali objašnjava zašto se baseline pomjerio između s119 i danas.** Ako je baza tada
bila natovarena mjesecima neprekidnih upisa (dead tuples, bloat, zastarjele
statistike), a sad je imala danima mira za autovacuum/autoanalyze, onda stari
baseline nije bio "solo" nego **"solo na umornoj bazi"** — i ni 3.77× ni 2.47×
nisu čisti brojevi.

**Jeftina provjera (otvoreno):** `pg_stat_user_tables` → `last_autovacuum`,
`last_autoanalyze`, `n_dead_tup` na `bb_prevodi_recenica`. Read-only, jedan upit.

## 10. Lekcije

1. **Kontrolisani A/B obara indirektno poređenje.** s119 zaključak nije bio greška
   u računu — bio je greška u **izboru baseline-a**. Poređenje preko različitih
   knjiga/jezika/dana nosi konfaunde koje jedan broj sakrije.
2. **Traži nezavisan instrument u sopstvenim podacima.** NLLB (lokalni CPU) je
   slučajno savršena kontrola za cloud kontenciju — bio je tu cijelo vrijeme,
   samo ga nismo tako čitali.
3. **Imenuj konfaund umjesto da ga zaobiđeš.** Doba dana ostaje neuklonjeno;
   zapisano kao takvo, ne prešućeno.
4. **Peto ponavljanje može nijansirati obrazac, ne samo ga potvrditi.** k24 nalaz
   je preživio, ali je promijenio oblik kad se promijenila jezična grupa.

## 11. Otvoreno / sljedeći koraci

**Flaviov plan (automatizacija workflow-a prevođenja):** puštati prevode u
različito doba dana, s različitim redoslijedom paralelno/sekvencijalno, istim
jezicima — tražiti pravilo u ponašanju. Jedan run ne može razdvojiti tri konfaunda
(režim × doba dana × stanje baze).

**Neposredno (s133):**
1. **RUNOVI.md zapis** ovog runa — čeka k24 201–400 (dopuniti jednim
   `parse_run_logs.py` pozivom).
2. **Korekcija 3.77× → 2.47×** u README §"Paralelno izvršavanje" i u RUNOVI.md
   (s119 zapažanja), s imenovanim konfaundom.
3. **`pg_stat_user_tables` provjera** (Flaviova hipoteza).
4. **s132 web (odgođeno):** `bb_web_export` + `nlp.html` ZAJEDNO (Massey:
   fine/coarse/afinitet, boja po coarse, ventil/mjesta razlučivi, i18n ×5,
   browser test, BB_VERSION bump). ⚠️ Stoji od s131 — export ne pokretati bez
   nlp.html.
5. Dalje po s131 listi: koreferencija + type audit u bb_10; tek onda
   `run_ner.sh --knjiga all --force`.

## 12. Završno stanje

- **Baza:** netaknuta ovom sesijom (raste od Flaviovih runova).
- **Kod:** netaknut.
- **Web:** netaknut → **BB_VERSION ostaje s129.4**.
- Commit: samo `docs/sessions/session_132.md` + README.

---
*Flavio & Claude · Buchenberg · Sesija 132 · 13. jul 2026.*
