# KAKO se brišu prevedene rečenice

Referentni dokument (kao `KAKO-JeziciUI.md`, `KAKO-KeyConcepts.md`) — pročitati PRIJE improvizacije. Nastao iz s156 (31. jul 2026), gdje je nejasnoća oko toga šta "obriši sve" tačno znači izazvala ozbiljan nesporazum u sesiji.

---

## Prvo — najvažnija razlika: "jedna faza" vs "sve faze"

Prije bilo kakvog brisanja, eksplicitno razjasniti (naglas, sa osobom koja traži brisanje) tačan obim:

- **"Obriši fazu N za opseg X-Y"** = briše se SAMO ta faza. Prevodi iz drugih faza (npr. root/faza 1) za iste rečenice OSTAJU netaknuti.
- **"Obriši sve prevode za opseg X-Y"** = briše se KROZ SVE FAZE koje ikad postoje za taj opseg — root (faza 1) i svaki refine/gated pokušaj. Original engleski tekst (`bb_recenice`) se NIKAD ne dira ni u jednom slučaju — brisanje je uvijek ograničeno na `bb_prevodi_recenica` i njene zavisnosti.

Ne pretpostavljati koje od ova dva neko misli. Ako fraza "sve" ili "40 rečenica" nije eksplicitno vezana za konkretnu fazu, pitati: "Misliš samo fazu N, ili kroz sve faze?"

---

## Zašto redoslijed brisanja mora biti tačan

`bb_prevodi_recenica` ima dvije FK zavisnosti prema sebi, OBJE `NO ACTION` (ne CASCADE):

```sql
SELECT conname, conrelid::regclass, confdeltype
FROM pg_constraint
WHERE confrelid = 'bb_prevodi_recenica'::regclass AND contype='f';
```

```
                    conname                     |       conrelid        | confdeltype
------------------------------------------------+------------------------+-------------
 bb_prev_recenica_prevodi_recenica_id_fkey      | bb_prev_recenica       | a
 bb_prev_recenica_faza_prevodi_recenica_id_fkey | bb_prev_recenica_faza  | a
```

`a` = NO ACTION. Direktan `DELETE FROM bb_prevodi_recenica` pući će na FK ako bilo koji red trenutno drži poziciju pobjednika (apsolutnog ili faznog). Zato je redoslijed OBAVEZAN:

1. `bb_prev_recenica_faza` (fazni pobjednici) — prvo
2. `bb_prev_recenica` (apsolutni pobjednici) — drugo
3. `bb_prevodi_recenica` (sami prevodi) — na kraju

---

## Recept A — briši SAMO jednu fazu (opseg + faza_id)

```sql
BEGIN;

DELETE FROM bb_prev_recenica_faza
WHERE prevodi_recenica_id IN (
  SELECT pr.id FROM bb_prevodi_recenica pr
  JOIN bb_prevodi_knjige pk ON pr.prevodi_knjige_id = pk.id
  WHERE pk.knjiga_id = <KNJIGA_ID> AND pk.faza_id = <FAZA_ID>
);

DELETE FROM bb_prev_recenica
WHERE prevodi_recenica_id IN (
  SELECT pr.id FROM bb_prevodi_recenica pr
  JOIN bb_prevodi_knjige pk ON pr.prevodi_knjige_id = pk.id
  WHERE pk.knjiga_id = <KNJIGA_ID> AND pk.faza_id = <FAZA_ID>
);

DELETE FROM bb_prevodi_recenica
WHERE id IN (
  SELECT pr.id FROM bb_prevodi_recenica pr
  JOIN bb_prevodi_knjige pk ON pr.prevodi_knjige_id = pk.id
  WHERE pk.knjiga_id = <KNJIGA_ID> AND pk.faza_id = <FAZA_ID>
);

COMMIT;
```

Ako želiš suziti i na konkretan opseg pozicija unutar te faze, dodaj `JOIN bb_recenice r ON pr.recenica_id = r.id ... AND r.pozicija BETWEEN X AND Y` u sva tri WHERE.

## Recept B — briši SVE faze za opseg (potpuno prazan opseg poslije)

Isti obrazac, ali BEZ filtera na `faza_id` — samo `knjiga_id` + opseg pozicija + (opciono) jezici:

```sql
BEGIN;

DELETE FROM bb_prev_recenica_faza
WHERE prevodi_recenica_id IN (
  SELECT pr.id FROM bb_prevodi_recenica pr
  JOIN bb_prevodi_knjige pk ON pr.prevodi_knjige_id = pk.id
  JOIN bb_recenice r ON pr.recenica_id = r.id
  JOIN bb_jezik j ON pk.jezik_id = j.id
  WHERE pk.knjiga_id = <KNJIGA_ID> AND r.pozicija BETWEEN <OD> AND <DO>
    AND j.kod IN (<'de','hr',...>)
);

DELETE FROM bb_prev_recenica
WHERE prevodi_recenica_id IN (
  SELECT pr.id FROM bb_prevodi_recenica pr
  JOIN bb_prevodi_knjige pk ON pr.prevodi_knjige_id = pk.id
  JOIN bb_recenice r ON pr.recenica_id = r.id
  JOIN bb_jezik j ON pk.jezik_id = j.id
  WHERE pk.knjiga_id = <KNJIGA_ID> AND r.pozicija BETWEEN <OD> AND <DO>
    AND j.kod IN (<'de','hr',...>)
);

DELETE FROM bb_prevodi_recenica
WHERE id IN (
  SELECT pr.id FROM bb_prevodi_recenica pr
  JOIN bb_prevodi_knjige pk ON pr.prevodi_knjige_id = pk.id
  JOIN bb_recenice r ON pr.recenica_id = r.id
  JOIN bb_jezik j ON pk.jezik_id = j.id
  WHERE pk.knjiga_id = <KNJIGA_ID> AND r.pozicija BETWEEN <OD> AND <DO>
    AND j.kod IN (<'de','hr',...>)
);

COMMIT;
```

---

## Prije brisanja — provjeri obim (read-only)

Uvijek prvo pokazati koliko će redova biti pogođeno, po fazi i jeziku:

```sql
SELECT pk.faza_id, j.kod, count(*) AS broj_prevoda
FROM bb_prevodi_recenica pr
JOIN bb_prevodi_knjige pk ON pr.prevodi_knjige_id = pk.id
JOIN bb_recenice r ON pr.recenica_id = r.id
JOIN bb_jezik j ON pk.jezik_id = j.id
WHERE pk.knjiga_id = <KNJIGA_ID> AND r.pozicija BETWEEN <OD> AND <DO>
GROUP BY pk.faza_id, j.kod
ORDER BY pk.faza_id, j.kod;
```

Pokazati taj rezultat prije predlaganja same DELETE transakcije — brojevi u DELETE izlazu (`DELETE N`) moraju se poklopiti sa ovim COUNT-om.

## Poslije brisanja — provjeri ciljni opseg je stvarno prazan

```sql
SELECT count(*) FROM bb_prevodi_recenica pr
JOIN bb_prevodi_knjige pk ON pr.prevodi_knjige_id = pk.id
JOIN bb_recenice r ON pr.recenica_id = r.id
WHERE pk.knjiga_id = <KNJIGA_ID> AND r.pozicija BETWEEN <OD> AND <DO>;
```

Očekivano `0` ako je Recept B korišten (sve faze obrisane); veći od 0 ako je korišten Recept A (samo jedna faza obrisana, ostale ostaju).

---

## Ako je obrisana samo jedna faza, a preostale faze imaju kandidate

Recept A ostavlja rečenice bez pobjednika tamo gdje je obrisana faza bila trenutni pobjednik — ali preostali kandidati (npr. root/faza 1) i dalje postoje. Da se pobjednik ispravno vrati na preostali bazen:

```bash
venv/bin/python src/bb_04_pobjednik.py --knjiga <ID> --od <OD> --do <DO> --jezici <lang1 lang2 ...>
```

Ova skripta ne prevodi ništa i ne zove nijedan model — samo ponovo računa argmax nad onim što već postoji u bazi. Ako je Recept B korišten (sve obrisano), ovaj korak nije potreban — opseg ostaje prazan dok se ponovo ne prevede.

---

## Originalne rečenice se NIKAD ne diraju

Ni jedan od gornjih recepata ne pominje `bb_recenice` (originalni engleski tekst). Brisanje prevoda je uvijek ograničeno na `bb_prevodi_recenica` + njene dvije zavisnosti. Ako se ikad postavi pitanje "da li su originalne rečenice obrisane" — odgovor je uvijek ne, osim ako je neko eksplicitno pisao DELETE na `bb_recenice`, što se ovim receptima nikad ne dešava.
