# Session 53 — Čišćenje asimetrije svih jezika, --force sudija

**Datum:** 6. jun 2026.
**Sesija:** 53
**Autor:** Flavio & Claude

---

## Šta smo uradili

### 1. Sistemska provjera svih jezika (knjiga 1 — Hound)

Pokrenuti count upiti po jeziku za sve modele i temperature. Otkriveno:

| Jezik | Problem | Opseg |
|-------|---------|-------|
| af, nl, es, sl | gemma3@0.1=20, ministral@0.8=20 | s1–s80 nedostajali |
| sr | gemma3@0.1=220, ministral@0.8=220 | s221–s300 nedostajali |
| hr, it, fr | NLLB duplikati | obrisani u ovoj sesiji |

Čisti jezici (bez intervencije): bg, mk, bs, pt, ro, de, fr (nakon čišćenja).

### 2. Masovno brisanje duplikata

Backup baze kreiran: `/home/balsam/backups/bb_backup_before_dedup_20260606_093729.sql` (1.8GB).

Korišten `SET session_replication_role = 'replica'` za zaobilaženje FK constrainta. Obrisano 360 duplikata odjednom za hr, it, fr.

### 3. bb_08_sudija.py — dvije izmjene

- Dodat `--force` parametar: kada se koristi, sudija ocjenjuje sve prevode bez obzira na postojeće ocjene (`sudija_avg IS NULL` uslov se preskače)
- Popravljen zastario uslov `len(prevodi) < 2` → `len(prevodi) < 5`

### 4. Dopunjeni prevodi i regenerisani pobjednici

| Jezik | Akcija |
|-------|--------|
| af | gemma3+ministral s1–s80, sudija --force s1–s100, pobjednici s1–s100 |
| nl | gemma3+ministral s1–s80, sudija --force s1–s100, pobjednici s1–s100 |
| es | gemma3+ministral s1–s80, sudija --force s1–s100, pobjednici s1–s100 |
| sl | gemma3+ministral s1–s80, sudija --force s1–s100, pobjednici s1–s100 |
| de | regenerisani pobjednici s1–s200 (orphani nakon čišćenja) |
| fr | regenerisani pobjednici s1–s100 (orphani nakon čišćenja) |
| hr | regenerisani pobjednici s1–s1800 (orphani nakon čišćenja) |
| it | regenerisani pobjednici s1–s200 (orphani nakon čišćenja) |

**sr — preskočen** (300 rečenica × sudija --force = previše resursa; odgođeno za sljedeću sesiju)

### 5. Web export

Finalni brojevi (provjereni):

| Knjiga | Jezik | Pobjednici |
|--------|-------|-----------|
| Hound | hr | 1800 |
| Hound | bs | 350 |
| Hound | sr | 300 |
| Hound | de, it | 200 |
| Hound | af, es, fr, nl, sl, pt, ro | 100 |
| Hound | mk, bg | 50 |
| Big Four | pt, it | 100 |
| Frankenstein | ro, it | 100 |

---

## TODO za sljedeću sesiju

1. **sr** — gemma3+ministral s221–s300, sudija --force s1–s300, bb_sr_cirilica, pobjednici s1–s300
2. Nastavak prevoda hr, sr, it, de → s350
3. Proširenje ostalih 10 jezika → s101–s350
4. Proširenje mk/bg → s51–s100

---

## Ključne lekcije

- `session_replication_role = 'replica'` — elegantno zaobilaženje FK bez DROP/ADD constrainta
- `--force` na sudiji eliminira potrebu za ručnim resetovanjem `sudija_avg`
- Svaki run mora biti kompletan i simetričan (sve temperature, svi modeli) prije nastavka
- `v_status_knjige` je pouzdan dashboard — koristiti na početku svake sesije

---

*Flavio & Claude · Buchenberg · Sesija 53 · 6. jun 2026.*
