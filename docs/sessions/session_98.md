# Session 98 — 26. jun 2026.

**Fokus:** Infrastruktura (NE pipeline) — pgAdmin (`pgad`) kontejner na strato hostu nedostupan kroz proxy. Dijagnoza kroz slojeve (Docker → Apache proxy → gunicorn worker → FD limit) → privremena popravka. `pgdb` netaknut tokom cijele operacije (eksplicitan zahtjev). Pipeline/web/git buchenberg nedirnut.

## Kontekst i novi infra nalazi
- Flavio prijavio: pgAdmin "zeza od prije nekog dana", radio OK ranije. Adresa: https://viapola.dynu.net (Apache reverse proxy → 127.0.0.1:8080 → pgad).
- **NOVO saznanje o infrastrukturi (popunjena rupa):**
  - `balsam:run_command` me spušta na **strato host** kao user **balsam** (`hostname`=strato, `whoami`=balsam). To je ISTI fizički host gdje žive docker kontejneri (`pgdb` koji balsam alat koristi za SQL = baš taj iz vespinog docker-compose).
  - Docker kontejnere starta user **vespa** iz `/home/vespa/docker/pg/docker-compose.yml`. I balsam i vespa su u **docker grupi** → dijele docker socket, pa balsam user vidi/upravlja kontejnerima bez obzira ko ih je startao. **Sudo NIJE potreban za docker ps/logs/exec/stats** (read-only dijagnostika).
  - Podjela privilegija (Flavio podsjetio): Claude = samo user "balsam" na Ubuntu serverima; Flavio izvršava sudo + vespa-specifične komande (compose recreate, izmjene fajlova u /home/vespa, Apache log).
  - **Lekcija o epistemici:** `ls /home/vespa/...` vrati prazno → NE zaključivati "ne postoji". Kao balsam user nemam pravo gledati tuđi home → to je "nemam privilegiju da vidim", ne "ne postoji". Dvije različite stvari, ne brkati.

## Dijagnostički luk (X-Ray kroz slojeve, sve read-only kao balsam)
1. **Docker nivo zdrav:** `pgad` Up 2 weeks, port 8080→80 mapiran (IPv4+IPv6); `pgdb` Up 2 weeks, 5432. Kontejner gore, port otvoren → problem "iznad" docker sloja.
2. **Log pgad:** šum = botovi (Infrawatch) gađaju /mcp,/sse,/login → 404 (ignorisati). Pravi trag: `2026-06-25 17:41 [ERROR] OSError: [Errno 24] No file descriptors available` + `Worker exiting (pid 83)`. Datum se poklapa s "prije nekog dana".
3. **FD limit:** soft `nofile`=**1024** (hard 524288) — nisko za dugotrajan web servis s 25 threadova. Gunicorn config: `-w 1 --threads 25`.
4. **Proxy izolacija (ključni korak):** Flavio dao Apache vhost (viapola.dynu.net.conf) — "Proxy Error: Error reading from remote server". Lanac: browser → Apache 443 → 127.0.0.1:8080 → pgad. `curl -m 15 http://127.0.0.1:8080/` (zaobilazi Apache) → **timeout 15s, 0 bajta**. Dakle Apache OK; pgAdmin mrtav na 8080. Worker prima konekciju ali nikad ne vrati odgovor.
5. **Zombi-funkcionalno stanje:** `ps ELAPSED` = **18d02** za PID 1 i worker PID 83 (živi 18 dana, od kreiranja kontejnera). `docker stats`: CPU 0.02%, MEM 276MiB. Worker `STAT S` (sleeping), 0% CPU, ne loguje, ne odgovara. "Tehnički stabilan, funkcionalno mrtav" (X-Ray death spiral obrazac).

## Zašto restart NIJE pomogao
- Flavio pustio `docker compose restart pgadmin` → "prošlo" ali procesi unutra ostali isti (ELAPSED i dalje 18d, log staje na 25-Jun, nijedan svjež red). Restart nije napravio nove procese — kontejner se reattachovao na zaglavljeni proces.
- `docker compose up -d --force-recreate pgadmin` → **Conflict: container name "/pgad" already in use**. Docker nije mogao automatski ukloniti zaglavljeni stari kontejner (bio u FD-exhaustion stanju i na nivou daemona).

## Popravka — Opcija 1 (privremena, BEZ izmjene compose fajla)
Flavio izvršio kao vespa iz `~/docker/pg`:
```
docker rm -f pgad          # force ukloni zaglavljeni kontejner (volume pgad_data ostaje → konekcije sačuvane)
docker compose up -d pgadmin   # svjež kontejner od nule
```
- `pgad Started`. **Verifikacija (mjereno):** `curl 127.0.0.1:8080` → **HTTP 302 za 0.004s** (vs 15s timeout). Worker ELAPSED **2:21** (svjež, ne 18d). Log pokazuje stvaran saobraćaj 26-Jun 09:11 (Flavio već u SQL editoru, `/sqleditor/status/... 200` → konekcija ka bazi radi). **`pgdb` Up 2 weeks — netaknut.**

## Uzrok i trajna popravka (Opcija 2 — ODGOĐENA, Flaviova odluka)
- **Korijenski uzrok:** nizak soft `nofile`=1024. Worker s 25 threadova × dugotrajne konekcije vremenom napuni FD → udari Errno 24 → zaglavi se. Opcija 1 ne dira limit → problem će se vratiti (procjena: par sedmica).
- **Opcija 2 (trajna):** dodati u `pgadmin` servis u docker-compose.yml:
```yaml
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
```
  pa `docker compose up -d pgadmin` (izmjena YAML-a tjera recreate + podiže limit).
- **Plan (Flavio):** ostati na Opciji 1 dok se simptom ne vrati još jednom (potvrda obrasca), pa onda Opcija 2.

## Dijagnostički potpis za sljedeći put (kad se vrati)
`curl 127.0.0.1:8080` timeout + log staje na "Worker exiting / Errno 24" + `ps ELAPSED` pokazuje stare procese → to je signal za Opciju 2 (ne više rm -f/up -d).

## Lekcije
- **Izolovati sloj prije akcije:** proxy error ne znači proxy je kriv. `curl` direktno na upstream (zaobilazeći Apache) razdvojio "Apache problem" od "app problem" jednim potezom.
- **`ps ELAPSED` raskrinkava lažni restart:** "restart prošao" ≠ procesi novi. 18d elapsed = ništa se nije restartovalo. Uvijek provjeriti uptime procesa, ne vjerovati exit code-u komande.
- **Zaglavljen kontejner blokira i `--force-recreate`** (conflict na imenu) → `docker rm -f` pa `up -d`.
- **`restart` ≠ `up -d` ≠ `up -d --force-recreate` ≠ `rm -f + up -d`:** rastuća "tvrdoća". restart najmekši (često nedovoljan za zaglavljen proces); rm -f najtvrđi (kad daemon ne može sam očistiti).
- **Privilegija vs postojanje:** prazan `ls` tuđeg home-a = nemam pravo gledati, NE "ne postoji".
- **`docker rm -f` briše kontejner, NE volume** — pgAdmin konekcije/serveri žive u `pgad_data` volumeu, preživljavaju recreate.

## Stanje na kraju
- pgAdmin: živ (HTTP 302, svjež worker). Privremena popravka (Opcija 1). `pgdb` netaknut.
- buchenberg/buchenweb git: **nedirnut** ovom sesijom (infra, ne pipeline). BB_VERSION nepromijenjen (s96).
- Dokumentacija: session_98.md + README §10 (infra nota o strato/vespa/docker grupi + pgAdmin obrazac).

## Sljedeće
- **Infra:** Opcija 2 (FD limit 65536) kad se simptom vrati. Razmisliti o monitoringu FD broja po workeru (preventivno).
- **Pipeline (nepromijenjeno od s97):** isti fan-out pattern provjeriti u stats backendu/bb_web_export; length bucketing NLLB; proširenje prevoda; art.html v1 / about.html i18n / learn.html / bb_web_export refaktor (v_pobjednici); NLP Relation Extraction (leži od s90).

---

*Flavio & Claude · Buchenberg · Session 98 · 26. jun 2026.*
