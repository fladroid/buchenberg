# KAKO se dodaje nova faza

Referentni dokument (kao `KAKO-JeziciUI.md`, `KAKO-KeyConcepts.md`) — pročitati PRIJE improvizacije. Proširuje README §7 detaljima iz s142-s158, uključujući "gated" obrazac, poznati bug (ispravljen s156) i deklarisani svjetovi za paralelan rad (s158, zamjenjuje auto-toggle i relativni toggle).

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

## Protokol za "gated root" — deklarisani svjetovi (s158)

Prije s158, `run_root_gated.sh` je automatski toggle-ovao glm za fazu 1 unutar
svakog poziva (`trap` na EXIT) — globalna DB promjena bez izolacije po
procesu/jeziku, pa su paralelni pozivi (Flaviov standardni obrazac) tiho
kvarili jedan drugom root konfiguraciju (otkriveno s157, race condition).

Prvi pokušaj rješenja (relativni toggle jednog modela, `bb_toggle_model.py`,
pozvan ručno prije/poslije rada) je TAKOĐE pogrešan pristup — oslanja se na
pretpostavku da je SVE OSTALO (ostali modeli, temperature) već u ispravnom
stanju od ranije. Ne garantuje potpuno, samostalno stanje.

**Pravo rješenje (s158): svaki "svijet" je POTPUNA, eksplicitna deklaracija
cijelog stanja — svih modela (a1) i svih temperatura (a2) za tu fazu — ne
relativni toggle jedne stvari.** Svaki poziv postavlja aktivan=true SAMO za
navedeno, aktivan=false za SVE ostalo u katalogu, bez obzira šta je bilo
prije. Nema pretpostavki o prethodnom stanju.

### Mehanizam — `bb_deklarisi_svet.py`

Generički alat, prima eksplicitnu listu modela i temperatura koji treba da
budu aktivni za zadanu fazu; sve ostalo u katalogu (`bb_faze_a1`/`bb_faze_a2`)
se gasi:

```bash
venv/bin/python src/bb_deklarisi_svet.py --faza 1 \
    --modeli "mistral-large-3:675b,nllb-600M,glm-5.2" \
    --temperature "0.8,0.1,0.0"
```

Ispisuje kompletno rezultujuće stanje (svaki model/temperatura, aktivan ili
ugašen) — direktna verifikacija bez posebnog upita.

### Imenovani svjetovi — tanke skripte, svaka potpuna sama za sebe

- **`bb_svet_1.sh`** — puna 3-way root faza: mistral + nllb + glm, temp 0.8/0.1/0.0.
- **`bb_svet_2.sh`** — sužen root za gated obrazac: mistral + nllb (BEZ glm), temp 0.8/0.1/0.0.

Svaka skripta je nezavisna, potpuna izjava namjere — ne zna niti mari za druge
svjetove, ne referencira ih, ne "vraća" prethodno stanje. Aktiviraš svijet
koji ti treba, sa parametrima koji su ti potrebni, i siguran si da imaš SVE
što ti treba i ništa što bi smetalo:

```bash
bash bb_svet_1.sh   # standardni svijet
bash bb_svet_2.sh   # svijet za gated-root obrazac
```

Novi svijet ubuduće (npr. mistral isključen, ili neka temperatura isključena)
= nova tanka skripta s drugačijom eksplicitnom listom u pozivu
`bb_deklarisi_svet.py` — nula izmjena logike.

### Rad unutar svijeta

Dok neki svijet važi, `run_root_gated.sh` (ili `run_faza.sh` direktno) se
smije pozivati paralelno, po jeziku, koliko god puta treba — svi čitaju isto,
stabilno stanje. Skripta sama NE dira `bb_faze_a1`/`bb_faze_a2` — samo čita
trenutno stanje i pokreće fazu(e).

```bash
cd /home/balsam/buchenberg && PYTHONUNBUFFERED=1 nohup time bash ./run_root_gated.sh \
  --knjiga <ID> --jezici "de" --od <OD> --do <DO> \
  > logs/root_gated_k<ID>_de_<OD>_<DO>.log 2>&1 &
# ponovi za hr, it, sr... — paralelno, bez straha od sudara
```

Kad je sav rad u datom svijetu gotov, aktiviraj sljedeći svijet koji ti treba
— eksplicitno, provjeri (`ps aux`/logovi) da ništa trenutno ne trči nad
starim svijetom prije nego promijeniš stanje.

---

## Prag (gate) — hardkodiran default, nije potrebno unositi

`bb_03_prevod.py --prag` ima default `0.95`, automatski se primjenjuje za svaku fazu `>= 2`. `run_faza.sh` NE podržava `--prag` flag — nije ni potrebno, jer je default već ono što treba. Ako ikad zatreba drugačiji prag, mijenja se default u `bb_03_prevod.py`, ne prosljeđuje se kroz `run_faza.sh`.

---

## Oporavak nakon pada usred prevođenja (s160)

`bb_03_prevod.py` nema top-level try/except u `main()`. Ako i batch-poziv I
single-fallback za istu rečenicu potroše sva 3 pokušaja (vidi
`ollama_chat(max_retries=3)`), izuzetak probije neuhvaćen i **cijeli proces
umre odmah** — sve što nije `commit`-ovano PRIJE te tačke je izgubljeno
(uključujući djelimično prevedene, ali nezapisane rečenice u istom chunk-u), i
svaki sljedeći batch/jezik u tom istom pozivu se **nikad ne ni pokuša**.

Bash wrapperi (`run_faza.sh`, `run_root_gated.sh`) imaju `set -e`, ali svaki
poziv ide kroz `| tee -a "$LOG"` bez `set -o pipefail` — exit kod cijevi je
exit kod `tee`-a (skoro uvijek 0), NE pythona. Zato lanac **tiho nastavlja**
na Sudiju i Pobjednika i pored pada (poznata, NEPOPRAVLJENA rupa — vidi
"Otvoreno" ispod).

**Oporavak — nema posebne logike, postojeći mehanizam je dovoljan:**
`already_done()` + prag (za faze≥2) već ispravno određuju šta nedostaje.
Prosto pozovi ISTU komandu (`run_faza.sh` ili `run_root_gated.sh`) sa ISTIM
`--knjiga/--jezici/--od/--do/--faza` kao original — ne treba znati gdje je
tačno puklo. Dodaj `--uradi-ako-nema` (s160) kao eksplicitnu oznaku namjere u
logu ("REZIM: --uradi-ako-nema..." se ispiše na početku svakog poziva) —
**flag ne mijenja nikakvu logiku**, čisto dokumentaciono, da se u logu vidi da
je ovo namjeran nastavak a ne svjež posao.

⚠️ **Poznato ograničenje (ne bug — dizajn faze):** za faze≥2, prag se
PONOVO računa pri svakom pozivu preko TRENUTNOG pobjednika. Ako je Sudija
(automatski, zbog tiho-nastavlja rupe gore) između pada i oporavka već
proglasio pobjednika preko DRUGOG modela/temperature sa `finalni_score≥0.95`,
ta rečenica ispada iz `todo` na oporavku — namjerno, ne greška. Primjer (s160,
k12 de, glm@0.1 nakon pada glm@0.1 usred `run_root_gated.sh`): 7 rečenica je
ostalo bez glm@0.1 pokušaja jer je glm@**0.8** sam već prešao prag prije nego
je oporavak pokrenut.

⚠️ **Ograničenje za fazu 1 (root) specifično:** Sudija filtrira `AND
m.aktivan` bezuslovno (čak i sa `--force`). Ako je svijet promijenjen između
pada i oporavka, prevodi modela koji više nije aktivan **nikad neće biti
ocijenjeni** dok se model ponovo ne aktivira. Nema istorije "koji je svijet
bio aktivan kad" — `bb_faze_a1.aktivan` je obično polje, nema timestamp ni
audit tabelu. Provjeri prije oporavka fazu 1: da li je isti svijet i dalje
aktivan.

**Otvoreno (nepopravljeno, s160):** `set -o pipefail` (ili provjera
`${PIPESTATUS[0]}`) u `run_faza.sh`/`run_root_gated.sh`, da pad Pythona
stvarno zaustavi lanac umjesto tihog nastavka na Sudiju/Pobjednika.

---

## Prije pokretanja bilo koje nove faze — checklist

1. Provjeri da faza postoji: `venv/bin/python src/bb_faza_info.py --faza <N>` (exit 1 ako ne postoji).
2. Provjeri aktivne modele te faze: `venv/bin/python src/bb_aktivni_modeli.py --faza <N>`.
3. Provjeri da ciljni opseg pozicija stvarno ima ono što očekuješ (prazan ili popunjen) — vidi `KAKO-BrisanjePrevoda.md` odjeljak "Prije brisanja — provjeri obim" za isti obrazac provjere (radi identično i za provjeru prije dodavanja).
4. Za gated fazu bez seeda — provjeri da je `bb_faze_a3` vezan za `base` prompt, ne `refine`.
5. Uvijek `PYTHONUNBUFFERED=1 nohup time ... > logs/*.log 2>&1 &` za bilo koji poziv koji traje više od par sekundi — tool koji šalje komandu na server može timeout-ovati prije nego proces završi; bez `nohup` postoji rizik da se proces prekine zajedno s konekcijom (nepotvrđeno u ovom projektu da li bi se prekinuo, ali `nohup` je siguran podrazumijevani izbor i standard već svuda u projektu).
6. Za gated-root PARALELAN rad — aktiviraj odgovarajući svijet (`bash
   bb_svet_1.sh` ili `bb_svet_2.sh`, vidi sekciju "Protokol za gated root"
   iznad) PRIJE poziva. `run_root_gated.sh` sam više NE dira
   `bb_faze_a1`/`bb_faze_a2` — ako svijet nije eksplicitno deklarisan prije
   poziva, skripta radi nad KAKVIM GOD je trenutno stanje u bazi, tiho.
