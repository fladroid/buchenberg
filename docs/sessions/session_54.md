# Session 54 — Buchenberg

**Datum:** 6. jun 2026.  
**Fokus:** Istraga nekonzistentnosti u bazi — otkrivanje i brisanje orphan pobjednika

---

## Što je urađeno

### 1. Inicijalizacija sesije
- README pročitan, session 51–53 pročitane
- Flavio napomenuo: ručno dodano 300 hr prevoda overnight → hr pobjednici 1800 → 2100

### 2. Health check
- Health check pokazao: hr=2105, it=206 umjesto očekivanih hr=2100, it=200
- Flavio primjetio anomaliju i pokrenuo istragu

### 3. Istraga anomalije

**Koraci istrage:**

1. `v_pobjednici` za hr i it → hr=2100, it=400 (it broji sve 3 knjige jer v_pobjednici nema filter na knjiga_id!)
2. Direktni COUNT na `bb_prev_recenica` JOIN `bb_prev_knjige` JOIN `bb_knjige` → it/knjiga=1 = **206** (potvrđeno)
3. Analiza prevoda po modelu za it/knjiga=1 → savršeno simetrično: 4×200 cloud + 3852 NLLB
4. Ključni upit:
```sql
SELECT pvr.*
FROM bb_prev_recenica pvr
WHERE prevodi_recenica_id NOT IN (SELECT id FROM bb_prevodi_recenica);
```
→ **11 orphana pronađeno**: 5 za prev_knjige_id=1, 6 za prev_knjige_id=2

### 4. Uzrok orphana

`bb_prev_recenica` ima FK na `bb_prevodi_recenica`, ali **bez `ON DELETE CASCADE`**. Negdje u prethodnim sesijama brisani su redovi iz `bb_prevodi_recenica` direktno, a pobjednici u `bb_prev_recenica` su ostali — dangling foreign keys.

### 5. Rješenje — brisanje 11 orphana

```sql
DELETE FROM bb_prev_recenica
WHERE prevodi_recenica_id NOT IN (SELECT id FROM bb_prevodi_recenica);
```
→ **DELETE 11** — izvršeno uspješno.

---

## Otvoreno

### Kratkoročno
- **`ON DELETE CASCADE`** na `bb_prev_recenica.prevodi_recenica_id` — dogovoreno ali odgođeno na sljedeću sesiju
- Health check poboljšanje: razlikovati pobjednike po knjizi (trenutno broji sve knjige zajedno)

### Dugoročni todo (nepromijenjeno)
- hr/sr/it/de → s350
- ostali jezici → s101–s350
- mk/bg → s51–s100
- Web export refaktor (v_pobjednici)
- Relation Extraction
- Favicon

---

## Stanje pobjednika (kraj sesije 54)

| Knjiga | Jezik | Pobjednici |
|--------|-------|-----------|
| Hound (id=1) | hr | 2100 |
| Hound (id=1) | sr | 300 |
| Hound (id=1) | bs | 350 |
| Hound (id=1) | it, de | 200 |
| Hound (id=1) | af, es, fr, nl, sl, pt, ro | 100 |
| Hound (id=1) | mk, bg | 50 |
| Big Four (id=5) | pt, it | 100 |
| Frankenstein (id=8) | ro, it | 100 |

---

## Ključna napomena

> Sesija je 75% potrošena na istragu skrivene greške u bazi (orphan pobjednici). Uzrok: FK bez ON DELETE CASCADE. Fix: jednoliniijski DELETE. Preporuka za sljedeće sesije: dodati ON DELETE CASCADE i poboljšati health check da detektuje orphane automatski.

---

*Flavio & Claude · Buchenberg · sesija 54 · 6. jun 2026.*
