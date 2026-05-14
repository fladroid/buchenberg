# SESSION_LOG — Buchenberg

---

## Sesija 02 — 14. maj 2026.

### Šta smo radili

Ovo je bila sesija uspostavljanja radnog protokola — nije pisan ni jedan red koda. Umjesto toga, otkrili smo ozbiljan problem u načinu na koji Claude i Flavio komuniciraju na početku sesije, i definisali rješenje.

---

### Greške i šta smo naučili

#### 1. Fraza "Procitaj README" — glavni problem sesije

U prethodnoj sesiji Claude je Flaviju rekao:
> *"Jednostavno mi kažeš 'Procitaj README' i ja odem na /home/balsam/buchenberg i pročitam README."*

Ovo je bila **lažna tvrdnja**. Claude nije znao:
- Na kom serveru se README nalazi
- Na kojoj putanji
- Da li uopšte postoji

Kada je Flavio na početku ove sesije rekao "Procitaj README", desilo se sljedeće:
1. Claude je pokušao pristupiti Google Driveu (pogrešno)
2. Claude je pretražio cijeli filesystem na balsam serveru tražeći README fajlove
3. Claude je pronašao `SESSION_buchenberg_01.md` u `/home/balsam/TOBEDELETED/buchenberg/` i samoinicijativno zaključio da je to pravi projekat
4. Claude je nastavio rad na bazi toga — bez ikakvog upozorenja

**Zašto je ovo opasno:** Da je postojalo 3 README fajla, Claude bi otvorio pogrešan i nastavio rad na bazi pogrešnih informacija. Ni Flavio ni Claude ne bi to primijetili.

#### 2. Lažni optimizam u prethodnoj sesiji

Claude je tvrdio da zna gdje je README i da ga može automatski naći. Ovo je bila **preuzeta i neosnovana tvrdnja**. Claude ne pamti putanje između sesija — svaka sesija počinje od nule.

#### 3. "Search and reference past chats" — pogrešno shvaćeno

Claude je u prethodnoj sesiji tvrdio da ima aktiviranu opciju koja mu omogućava pristup prethodnim sesijama. Ovo je **djelimično tačno** — opcija postoji, ali ne funkcionira kao automatski kontekst. Claude ne može "znati" gdje je README bez eksplicitne putanje.

---

### Rješenje — usvojen protokol

**Svaka nova sesija počinje ovakvom komandom:**

```
Procitaj <username>@<hostname>:/putanja/do/README.md
```

**Primjer za Buchenberg:**
```
Procitaj balsam@foxuno.dynu.net:/home/balsam/buchenberg/README.md
```

**Zašto ovo funkcionira:**
- Jednoznačno — nema prostora za pogrešnu interpretaciju
- Server je eksplicitno naveden
- Putanja je eksplicitna
- Claude zna tačno šta treba uraditi

**Zašto "Procitaj README" ne funkcionira:**
- Claude ne zna na kom serveru
- Claude ne zna putanju
- Ako pronađe više README fajlova — otvoriće pogrešan
- Claude ne dobija nikakvu grešku — tiho radi pogrešnu stvar

---

### Šta je pročitano

Nakon ispravne komande `Procitaj balsam@foxuno.dynu.net:/home/balsam/buchenberg/README.md`, Claude je uspješno pročitao dokumentaciju projekta. Ključne informacije:

- Sav razvoj je na **foxuno** serveru, `/home/balsam/buchenberg/`
- PostgreSQL je na **balsam** serveru (Docker kontejner `pgdb`)
- Prevod: NLLB (lokalno na foxuno) + Gemma 3 12b via Ollama Cloud
- Status projekta: Setup završen, sljedeći korak je shema baze

---

### Zaključak sesije

Ova sesija nije bila izgubljena — naučili smo kako pravilno početi svaku narednu sesiju. README protokol je od sada **obavezan prvi korak** i mora biti eksplicitna putanja, nikad samo "procitaj README".

---

*Flavio & Claude · Sesija 02 · 14. maj 2026.*
