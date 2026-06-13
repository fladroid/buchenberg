# Session 73 — Web fajlovi u git (buchenweb)

**Datum:** 13. jun 2026.
**Sesija:** 73
**Autor:** Flavio & Claude

---

## Što je urađeno

### 1. Checklist (standardni)
- Memorija osvježena, project files pročitani
- README pročitan (V3, s72)
- Sessions 70–72 pročitane
- Health check: sve zeleno — 38.333 rečenica, 124.128 prevoda (+2.510 od s72), 8.602 pobjednika (+150 od s72)
- Git čist (97c6492), 2 untracked fajla (`flanel.sh`, `nohup.out`) — nisu naši

### 2. Novi git repozitorijum: buchenweb

**Cilj:** Web fajlovi (`/var/www/buchenberg/`) pod verzijskom kontrolom.

**Što je probano i nije uspjelo:**

#### Pokušaj 1 — `web/` direktorijum s kopiranjem
Inicijalni prijedlog: kreirati `/home/balsam/buchenberg/web/` i kopirati HTML/CSS/JS fajlove tamo.

**Problem:** Flavio je postavio ključno pitanje — "zašto kopiramo?" Apache već servi fajlove iz `/var/www/buchenberg/`, kopiranje znači dvije kopije koje treba sinhronizirati. Prijedlog odbačen.

**Uzrok greške:** Claude je krenuo od pretpostavke (git → deploy pattern) umjesto da analizira konkretnu situaciju.

#### Pokušaj 2 — symlink `/home/balsam/buchenberg/web → /var/www/buchenberg/`
Prijedlog: symlink unutar buchenberg repoa koji pokazuje na Apache direktorijum — git bi "vidio" fajlove kroz symlink.

**Problem:** Git ne prati sadržaj kroz symlink direktorijum — čuva samo symlink sam po sebi (`web -> /var/www/buchenberg`), ne fajlove unutra. Otkriveno tek pri izvršavanju (`fatal: pathspec 'web/' is beyond a symbolic link`).

**Uzrok greške:** Claude je predložio rješenje bez prethodne verifikacije kako git tretira symlink direktorijume. Sinteza plauzibilne priče umjesto provjere premise (ista greška kao Fable 5 epizoda u s71).

**Čišćenje nakon neuspjelog pokušaja:**
1. `rm /home/balsam/buchenberg/web` — brisanje symlinka
2. `git restore --staged web` — unstage web
3. `git restore --staged .gitignore` — unstage .gitignore
4. `git checkout -- .gitignore` — vraćanje .gitignore na original

#### Pokušaj 3 — zasebni git repo u `/var/www/buchenberg/` ✅
Flaviov prijedlog: inicijalizirati git direktno u Apache direktorijumu, odvojen repozitorijum od buchenberg.

**Rezultat: uspješno.**

**Koraci:**
1. Flavio kreirao `fladroid/buchenweb` na GitHubu
2. `git init` u `/var/www/buchenberg/`
3. `git remote add origin git@github.com:fladroid/buchenweb.git`
4. `.gitignore` kreiran — isključuje `data/`, `books/`, `BBOLD/`, `*.bak`
5. `git config user.name/email` — isti podaci kao buchenberg repo
6. `git add .` — 12 fajlova (HTML, CSS, JS)
7. `git commit -m "initial commit: web portal s72"`
8. `git push -u origin master`

**Commit:** `b9ca62c` — potvrđen na `api.github.com/repos/fladroid/buchenweb`

### 3. Lekcije sesije

**Za Claudea:**
- Pretpostavke treba eksplicitno navesti i verificirati prije prijedloga
- "Mislim da može, ali da prvo provjerimo" je bolji odgovor od samouvjerenog "Da, može!"
- Flavio-ova pitanja ("zašto kopiramo?", "zašto nisi odmah predložio?") su X-Ray signal — trebaju odmah otvoriti preispitivanje premise
- Korak-po-korak pristup je obavezan za destruktivne operacije — duge kombinirane komande gube pregled

**Za workflow:**
- Web fajlovi i pipeline su sada u dva odvojena repozitorijuma — jasna separacija odgovornosti
- Svaka izmjena web fajlova zahtijeva commit u `buchenweb`, ne u `buchenberg`

---

## Stanje na kraju sesije

- `fladroid/buchenweb` — inicijalni commit b9ca62c, 12 fajlova (s72 stanje)
- `fladroid/buchenberg` — nepromijenjen, git čist
- bb_06_enkodiranje — završio noću (bio 81.920/121.238 na kraju s72)
- naturalness_score retroaktivno punjenje: TODO
- bb_06 u standardni pipeline redosljed: TODO

---

## Novi workflow za web fajlove

```bash
# Nakon izmjene web fajlova:
cd /var/www/buchenberg
git add .
git commit -m "opis izmjene"
git push
```

> ⚠️ Buchenberg repo (`/home/balsam/buchenberg/`) i buchenweb repo (`/var/www/buchenberg/`) su ODVOJENI. Git operacije za web idu isključivo iz `/var/www/buchenberg/`.

---

## Sljedeće (kumulativno)

- naturalness_score retroaktivno punjenje (nova skripta, analogna bb_06)
- bb_06 uvrstiti u standardni pipeline redosljed
- Prijevodi: hr/sr/it/de → s350; mk/bg → s51–100
- art.html: Sentence Fingerprints (zadnji eksponat)
- Cache-Control za js/css (.htaccess)
- about.html i18n; learn.html nove igre

---

*Flavio & Claude · Buchenberg · sesija 73 · 13. jun 2026.*
