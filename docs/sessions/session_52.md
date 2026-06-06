# Session 52 — Novi viewovi, analiza asimetrije prevoda

**Datum:** 6. jun 2026.
**Sesija:** 52
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Kontekst uspostavljanja

Health check pokazao neočekivano stanje baze u odnosu na README (sesija 51):
- hr: 1800 pobjednika (README: 450)
- sr: 300 pobjednika (README: 200)
- bs, de, hr, it, sl, sr: NLLB kompletnih 3852 rečenica

Flavio je između sesija 51 i 52 pokrenuo:
- Cloud prevode + sudija + pobjednici za hr i sr (u koracima do web exporta)
- NLLB prevode za sve rečenice Hounda za bs i sl (sinoć)
- NLLB prevode za hr, sr, de, it su bili urađeni ranije

Zaključak: health check je source of truth za stanje baze, ne README. README se ažurira samo na kraju sesije.

### 2. Novi viewovi

Kreirani novi viewovi za bolji uvid u stanje pipeline-a:

| View | Opis |
|------|------|
| `v_knjige_recenice` | knjiga_id, knjiga_naziv, ukupno rečenica |
| `v_prevodi_po_modelu` | knjiga_id, jezik, model, temperatura, broj prevedenih rečenica |
| `v_sudija_pokrivenost` | knjiga_id, jezik, broj rečenica s ocjenom sudije |
| `v_pobjednici_pokrivenost` | knjiga_id, jezik, broj pobjednika |
| `v_status_knjige` | JOIN svih gornjih — pivot po modelu/temperaturi, jedan red po knjiga×jezik |

**`v_status_knjige` kolone:**
`knjiga_id`, `knjiga_naziv`, `jezik`, `ukupno`, `gemma3_08`, `gemma3_01`, `ministral_08`, `ministral_01`, `nllb`, `sudija`, `pobjednici`

**Napomena o izradi:** Kompleksni monolitni view sa ugniježđenim subupitima je bio prepor — PostgreSQL query planner pravio eksploziju. Rješenje: multiview pristup — svaki jednostavan view radi jedan posao, finalni view ih joinuje. Testiranje korak po korak (1 join, 2 joina...) pokazalo gdje je problem.

### 3. Analiza asimetrije prevoda

`v_status_knjige` i direktni upiti po jeziku otkrili asimetriju u broju prevoda po modelu/temperaturi.

**Primjeri:**

| Jezik | Model | Temp | Count | Očekivano |
|-------|-------|------|-------|-----------|
| sl | gemma3:12b | 0.1 | 20 | 100 |
| sl | ministral-3:14b | 0.8 | 20 | 100 |
| de | gemma3:12b | 0.5 | 40 | 0 (obrisano) |
| fr | gemma3:12b | 0.5 | 40 | 0 (obrisano) |
| hr | nllb-600M | 0.0 | 3932 | 3852 |
| de | nllb-600M | 0.0 | 3932 | 3852 |

**Uzrok — rekonstrukcija historije:**

1. **Rana faza:** runovi od 20 i 40 rečenica, temperatura 0.5. Skripte nisu bile idempotentne — duplikati su ulazili u bazu.
2. **Prelazna faza:** prelaz sa 0.5 na 0.8/0.1. Brisanje 0.5 nije bilo konzistentno (fr, de još imaju 40 redova sa temp=0.5).
3. **Produkcijska faza:** `already_done()` + `ON CONFLICT DO NOTHING` uvedeni — skripte postale idempotentne. Od tada nema novih asimetrija ni duplikata.
4. **NLLB anomalija:** hr i de imaju 3932 umjesto 3852 (razlika 80) — duplikati iz ranih runova od 40+40 prije idempotentnosti.

**Praktična posljedica:** Asimetrije ne utiču na kvalitet pobjednika — sudija i pobjednici su konzistentni. Historijski artefakt, ne aktivni bug.

**Otvoreno pitanje:** Da li čistiti duplikate i asimetrije ili ostaviti? Analiza i odluka u sljedećoj sesiji.

---

## Stanje baze na kraju sesije

Nepromijenjeno u odnosu na početak sesije 52 (overnight runovi Flavia):

| Knjiga | ID | Jezik | Pobjednici |
|--------|-----|-------|-----------|
| Hound | 1 | hr | 1800 |
| Hound | 1 | bs | 350 |
| Hound | 1 | sr | 300 |
| Hound | 1 | it, de | 200 |
| Hound | 1 | af, es, fr, nl, sl, pt, ro | 100 |
| Hound | 1 | mk, bg | 50 |
| Big Four | 5 | pt, it | 100 |
| Frankenstein | 8 | ro, it | 100 |

---

## Otvoreno za sljedeće sesije

1. **Analiza i čišćenje asimetrije** — odluka o duplikatima i temp=0.5 ostacima
2. Nastavak prevoda hr, sr, it, de → s350 (cloud modeli)
3. Proširenje ostalih 10 jezika Hounda → s101–s350
4. Proširenje Hound mk/bg → s51–s100
5. Proširenje Big Four PT/IT → s101–s350
6. Proširenje Frankenstein RO/IT → s101–s350
7. Web fajlovi (nlp.html, stats.html) dodati u git
8. Favicon za buchenberg.opik.net
9. Relation Extraction (Gemma4)
10. Refaktorisati `bb_web_export.py` → `v_pobjednici` view

---

*Flavio & Claude · Buchenberg · Sesija 52 · 6. jun 2026.*
