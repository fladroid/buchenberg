# Session 23 — Addendum (nastavak iste sesije)

## Korak 5 — pivot_007: 3× init sekvencijalno, isti test_id

**Hipoteza:** Umjesto init s listom 3 modela odjednom (pivot_006), pokrenuti init 3 puta s jednim modelom — isti test_id, upsert samo poboljšava. Rezultat usporediv, ali lakše pratiti doprinos svakog modela.

**Konfiguracija:** de, hr, it, fr — 40 rečenica — 3 sekvencijalna init runa (gemma3:12b → ministral-3:14b → gemma4:31b)

| Lang | 🟢 | 🟡 | 🔴 | avg |
|------|----|----|-----|-----|
| DE | 18 | 14 | 8 | 0.8640 |
| FR | 20 | 16 | 4 | 0.8826 |
| HR | 17 | 19 | 4 | 0.8728 |
| IT | 18 | 16 | 6 | 0.8783 |

---

## Korak 6 — pivot_008: jezik po jezik, 3 modela, 40 rečenica

**Hipoteza:** Init jezik po jezik (1 jezik × 3 modela) umjesto 4 jezika × 3 modela. Fokus na jedan jezik odjednom.

**Redosljed:** fr → hr → it → de

| Lang | 🟢 | 🟡 | 🔴 | avg | Trajanje |
|------|----|----|-----|-----|---------|
| FR | 19 | 17 | 4 | 0.8874 | 1:58 |
| HR | 18 | 18 | 4 | 0.8823 | 1:24 |
| IT | 16 | 19 | 5 | 0.8772 | 1:31 |
| DE | 20 | 11 | 9 | 0.8665 | 2:57 |

**Ukupno: ~8 min** za 4 jezika × 40 rečenica × 3 modela.

---

## Korak 7 — pivot_009: jezik po jezik, 3 modela, 80 rečenica

**Cilj:** Provjera linearnosti skaliranja — 2× rečenica, hoće li 2× duže?

**Redosljed:** fr → hr → it → de

| Lang | 🟢 | 🟡 | 🔴 | avg | Trajanje |
|------|----|----|-----|-----|---------|
| FR | 45 | 25 | 10 | 0.8879 | 2:52 |
| HR | 38 | 30 | 12 | 0.8752 | 3:55 |
| IT | 39 | 30 | 11 | 0.8847 | 2:26 |
| DE | 45 | 23 | 12 | 0.8811 | 2:15 |

**Napomena o vremenima:** Nepouzdana zbog batch→single fallback varijabilnosti separatora. Opći zaključak: skaliranje je **linearno**, ne eksponencijalno. Broj API poziva raste linearno s brojem rečenica.

**Kvalitet stabilan:** proporcija crvenih ostaje ~10-15% kroz pivot_008 i pivot_009.

---

## Kompletna usporedba svih pristupa (40 rečenica, de/hr/it/fr)

| Pristup | FR 🟢 | HR 🟢 | IT 🟢 | DE 🟢 | FR 🔴 | HR 🔴 | IT 🔴 | DE 🔴 | Ukupno vrijeme |
|---------|-------|-------|-------|-------|-------|-------|-------|-------|--------------|
| p003 (stara strat.) | 22 | 17 | 17 | 18 | 5 | 6 | 7 | 8 | ~60 min |
| p006 (3mod init+pivot) | 23 | 19 | 17 | 19 | 3 | 3 | 4 | 7 | ~54 min |
| p007 (3× init seq.) | 20 | 17 | 18 | 18 | 4 | 4 | 6 | 8 | ~8 min |
| p008 (lang×lang) | 19 | 18 | 16 | 20 | 4 | 4 | 5 | 9 | ~8 min |

---

## Naučene lekcije (addendum)

- **Skaliranje je linearno** — broj API poziva proporcionalan broju rečenica; eksponencijalnosti nema
- **Jezik po jezik, 3 modela = optimalan omjer** za produkciju — ~2 min po jeziku × 40 rečenica, kvalitet blizu pivot_006 uz 6× manje vremena
- **Separator varijabilnost** ostaje otvoreni problem — batch→single fallback unosi nepredvidiv vremenski šum; rješavanje prompt engineeringom vrijedi istražiti
- **DE je persistentno najteži jezik** kroz sve testove i strategije

---

## Ažurirani handoff blok

- **pivot.yaml:** pivot_009, de, kraj sesije
- **Baza:** pivot_results sadrži pivot_001 kroz pivot_009
- **Git:** commit `1efa623`
- **Preporučeni sljedeći korak:** produkcijski run — jezik po jezik, 3 modela, puna knjiga (sent_from=1, sent_to=3852)

---

*Flavio & Claude · Session 23 Addendum · 26. maj 2026.*
