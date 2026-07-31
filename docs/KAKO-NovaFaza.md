# KAKO se dodaje nova faza

Referentni dokument (kao `KAKO-JeziciUI.md`, `KAKO-KeyConcepts.md`) — pročitati PRIJE improvizacije. Proširuje README §7 detaljima iz s142-s156, uključujući "gated" obrazac i poznati bug (ispravljen s156).

---

## Osnovni koncept — faza = metod + tri nezavisne ose

Faza je redni broj + jedinstveni identifikator izvršavanja. Šta faza RADI određuje `metod_id` (FK → `bb_metode`: `base`=root, tačno jednom; `self-refine`=ponovljiv M puta). KOJI se model/temperatura/prompt koriste određuju tri nezavisne veze:

- `bb_faze_a1` → `bb_modeli` (koji model/modeli)
- `bb_faze_a2` → `bb_temperature` (koja temperatura/e)
- `bb_faze_a3` → `bb_promptovi` (koji prompt — `base`, `refine`, `refine-lenient`, `refine-strict`, ili novi)

Svaka osa se bira NEZAVISNO — nema sprege u shemi. Vidi `docs/PLAN-KONFIGURACIJA.md` za pun istorijat odluke (s141-143).

---

## Standardna nova faza (self-refine, sa seedom) — dva INSERT-a

```sql
-- 1) registruj fazu (metod_id 2 = self-refine)
INSERT INTO bb_faze (naziv, redoslijed, metod_id, opis)
VALUES ('naziv-faze', <redoslijed>, 2, 'Opis šta ova faza radi.');

-- 2) registruj a1/a2/a3 izbore (katalozi nemaju faza_id — isti model/temp/prompt
--    smije se ponoviti u novoj fazi bez sukoba)
INSERT INTO bb_faze_a1 (faza_id, model_id, aktivan)
    SELECT <NOVI_ID>, id, true FROM bb_modeli WHERE naziv IN ('model1','model2');
INSERT INTO bb_faze_a2 (faza_id, temperatura_id, aktivan)
    SELECT <NOVI_ID>, id, true FROM bb_temperature WHERE ROUND(vrijednost::numeric,4)=ROUND(0.8::numeric,4);
INSERT INTO bb_faze_a3 (faza_id, prompt_id, aktivan)
    SELECT <NOVI_ID>, id, true FROM bb_promptovi WHERE naziv='refine';
```

```bash
bash ./run_faza.sh --faza <NOVI_ID> --knjiga <ID> --jezici "de hr it sr" --od <OD> --do <DO>
```

**Pravila:**
- `--faza` je OBAVEZAN, ne auto-inkrementira se.
- Faze se ne popunjavaju unazad — jedini preduslov je postojanje pobjednika (faza 1/root).
- Seed = trenutni apsolutni pobjednik, iz bilo koje prethodne faze — faze nisu komutativne.
- ⚠️ `nextval` NIJE transakcijski — ako INSERT u `bb_faze` padne pa se ponovi, sekvenca odmakne i faza dobije pogrešan `id`. Provjeri `id` prije nego se osloniš na njega.

---

## Gated faza (BEZ seeda, npr. faza 10 iz s155/s156) — dodatna pravila

Neke faze namjerno NE treba da šalju seed/pivot modelu — npr. "gated root": jeftin bazen (mistral+nllb) prevodi original prvo, pa skuplji model (npr. glm) pokušava SAMO na rečenicama koje jeftini bazen nije riješio dobro (ispod praga), ali prevodi ORIGINAL nezavisno, ne popravlja tuđi prevod.

Za ovakvu fazu, `bb_faze_a3` MORA pokazivati na `base` prompt (ne `refine`):

```sql
INSERT INTO bb_faze_a3 (faza_id, prompt_id, aktivan)
    SELECT <NOVI_ID>, id, true FROM bb_promptovi WHERE naziv='base';
```

### ⚠️ Poznati bug (ispravljen s156) — provjeriti da je fix na mjestu

Prije s156, `bb_03_prevod.py` je odlučivao da li šalje seed ISKLJUČIVO na osnovu broja faze (`args.faza >= 2`), ignorišući `PROMPT_NAZIV`. Posljedica: faza sa `base` promptom je i dalje dobijala seed u pozivu modelu — suprotno namjeri. Ispravka (potvrditi da postoji u `src/bb_03_prevod.py`):

```python
elif is_refine and PROMPT_NAZIV != 'base':
    # ... šalje seed (prevedi_refine_batch) ...
else:
    # ... čist prevod originala, bez seeda (prevedi_batch) ...
```

Prag/gate logika (`if is_refine: seed_map = ...`) OSTAJE vezana samo za broj faze — to je namjerno i ispravno (odlučuje KOJE rečenice ulaze u pokušaj, ne šalje li se seed).

Verifikacija da fix radi na konkretnom runu — grep log za prompt header i uvjeriti se da piše `base`:

```bash
grep -n "Model:" logs/<log_fajl>.log
```

Očekivano: `prompt: base` za svaki model u toj fazi.

---

## Wrapper za "gated root" obrazac — `run_root_gated.sh`

Za tačno ovaj scenario (suzi root, pusti ga, vrati root, pusti gated fazu) postoji gotov skript — nema potrebe za ručnim SQL toggle-om niti za tri odvojena poziva:

```bash
cd /home/balsam/buchenberg && PYTHONUNBUFFERED=1 nohup time bash ./run_root_gated.sh \
  --knjiga <ID> --jezici "de hr it sr" --od <OD> --do <DO> \
  > logs/root_gated_k<ID>_<OD>_<DO>.log 2>&1 &
```

Radi sve automatski: isključi glm iz faze 1 → root (faza 1, suzen bazen) → gated faza (default `--gated-faza 10`, može se promijeniti) → **glm se UVIJEK vraća na `aktivan=true` za fazu 1 na kraju** (preko `trap` na EXIT, radi i ako nešto usput padne). Pretpostavka: gated faza (10 ili druga) je VEĆ registrovana u bazi (bb_faze + a1/a2/a3) — skript je ne kreira, samo pokreće.

Za ručni toggle jednog modela (van wrappera, npr. za debug): `venv/bin/python src/bb_toggle_model.py --faza <N> --model <naziv> --aktivan true|false`.

---

## Prag (gate) — hardkodiran default, nije potrebno unositi

`bb_03_prevod.py --prag` ima default `0.95`, automatski se primjenjuje za svaku fazu `>= 2`. `run_faza.sh` NE podržava `--prag` flag — nije ni potrebno, jer je default već ono što treba. Ako ikad zatreba drugačiji prag, mijenja se default u `bb_03_prevod.py`, ne prosljeđuje se kroz `run_faza.sh`.

---

## Prije pokretanja bilo koje nove faze — checklist

1. Provjeri da faza postoji: `venv/bin/python src/bb_faza_info.py --faza <N>` (exit 1 ako ne postoji).
2. Provjeri aktivne modele te faze: `venv/bin/python src/bb_aktivni_modeli.py --faza <N>`.
3. Provjeri da ciljni opseg pozicija stvarno ima ono što očekuješ (prazan ili popunjen) — vidi `KAKO-BrisanjePrevoda.md` odjeljak "Prije brisanja — provjeri obim" za isti obrazac provjere (radi identično i za provjeru prije dodavanja).
4. Za gated fazu bez seeda — provjeri da je `bb_faze_a3` vezan za `base` prompt, ne `refine`.
5. Uvijek `PYTHONUNBUFFERED=1 nohup time ... > logs/*.log 2>&1 &` za bilo koji poziv koji traje više od par sekundi — tool koji šalje komandu na server može timeout-ovati prije nego proces završi; bez `nohup` postoji rizik da se proces prekine zajedno s konekcijom (nepotvrđeno u ovom projektu da li bi se prekinuo, ali `nohup` je siguran podrazumijevani izbor i standard već svuda u projektu).
