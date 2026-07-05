# Buchenberg — Koncept pipeline-a

*Šta je identitet projekta, a šta zamjenjiva komponenta*

## 1. Princip takmičenja

Prevod ne nastaje iz jednog modela nego iz **takmičenja kandidata**. Za svaku rečenicu više prevodilaca proizvodi prevod; ocjenjivanje bira pobjednika. Krajnji rezultat je hibridni prevod — najbolje od svakog takmičara, po rečenici.

Konkretna imena modela nisu dio arhitekture. Ona su **parametri** — prolazna, zamjenjiva, podložna povlačenju od strane provajdera bez najave. Arhitektura definiše samo *vrste* takmičara i njihov minimum.

## 2. Minimumi (identitet projekta)

Identitet projekta definisan je minimumima i procesom, ne komponentama:

- **najmanje 2 konkurentna LLM prevodioca** u baznoj fazi — bez konkurencije nema takmičenja
- **najmanje 1 namjenski MT model** (NLLB-tip) — deterministički kontrast LLM-ovima
- **tačno 1 sudija** (LLM, blind evaluacija: grammar / naturalness / fidelity)
- **tačno 1 embedder** (cosine similarity: back_score + translation_score)
- **fiksan odnos ocjenjivanja:** `finalni_score = 0.4 × kompozitni + 0.6 × sudija` — kvalitativna ocjena nosi većinu
- **mehanizam pobjednika:** argmax finalnog scorea nad populacijom kandidata

Minimum od 2 konkurentna LLM-a odnosi se na **baznu fazu**. U refine fazama minimum je **1 model** — konkurencija je već obezbijeđena postojećim bazenom kandidata iz prethodnih faza; ako refine kandidat pobijedi, automatski je pobjednik faze i možda apsolutni pobjednik.

Svaka konkretna komponenta — bilo koji LLM, sudija, embedder — može biti zamijenjena iz razloga van naše kontrole (retirement, cijena, dostupnost). Brojevi iznad minimuma su luksuz kad ga resursi dozvole; u bajci bismo uzeli 4 LLM-a i 2 sudije — u stvarnosti ne možemo bez sudije i barem 2 konkurentna modela. Identitet mora preživjeti zamjenu bilo koje komponente.

## 3. Model = model + konfiguracija

"Model" u ovom projektu uvijek znači **model s konfiguracijom**. Za sada je konfiguracija temperatura; koncept je otvoren za buduće parametre. Isti model na dvije temperature su dva različita takmičara.

Ovo je **svjesna dizajnerska odluka**, ne previd — s poznatim trade-offom u ER čistoći (konfiguracija denormalizovana u red takmičara umjesto u zasebnu tabelu). Jednostavnost identifikacije takmičara vrijedi tu cijenu.

## 4. Faze: iterabilnost procesa

Proces takmičenja je **iterabilan**. Svaka faza je jedno kompletno takmičenje — ista populacijska logika, isti sudija, isti score, isti izbor pobjednika:

- **Faza 1 (bazni prevod):** kandidati se generišu iz originala, bez sidra. Obavezna.
- **Faza 2+ (refine):** kandidati se generišu iz originala + trenutnog pobjednika (sidro). Opcionalne, sekvencijalne — faza N se sidri na pobjednika nakon faze N−1.

Broj faza nije dio identiteta. Jedno takmičenje je minimum; svako sljedeće je opciono. Refine nije nova komponenta — to je isti proces primijenjen na sopstveni izlaz (anchored mutation: LLM kao gramatički siguran operator mutacije). Seed je parametar ulaza, ne nova komponenta.

**Pobjednik faze ≠ apsolutni pobjednik. Apsolutni pobjednik je najbolji kandidat preko svih odigranih faza** — bira se iz ukupnog bazena, nijedna faza nema automatsku prednost.

Namjenski MT model učestvuje samo u baznoj fazi: deterministički je (ponavljanje na isti ulaz ne proizvodi mutaciju) i nema mehanizam sidra. Njegov bazni kandidat ostaje punopravni takmičar u ukupnom bazenu kroz sve faze.

## 5. Identifikacija porijekla

Svaki prevod nosi punu identifikaciju porijekla kao **strukturirane podatke, nikad kao dio imena**:

```
prevod → (model, konfiguracija, faza)
```

Iz ove trojke se zna: ko je preveo, s kojim parametrima, u kojoj fazi — i implicitno, na šta se sidrio (pobjednik prethodne faze). Sufiks-konvencije u imenu (`-refine`) su istorijski artefakt brzine koji je postao kočnica razvoja: dupliraju informaciju koja već postoji strukturirano (`faza_id`) i vežu skripte za string-manipulaciju.

## 6. Posljedice po implementaciju

Ovaj koncept čini sljedeće hardkodove prekršajima principa:

| Prekršaj | Gdje | Princip koji krši |
|---|---|---|
| Imena modela u petljama | `run_pipeline.sh` l.48, `run_refine.sh` l.25 | §1 — imena su parametri |
| `OCJENJIVANI_MODELI` lista | `bb_08_sudija.py` l.37 | §1 — imena su parametri |
| Test-lista modela | `health_check.py` l.~149 | §1 |
| Seed lista | `bb_01_init_lookup.py` | §1 (nizak prioritet) |
| `-refine` sufiks u `bb_modeli.naziv` | redovi id 12/13 + `bb_03` `.replace()` + `run_refine.sh` | §5 — porijeklo je struktura, ne string |
| `faza_id=NULL` legacy redovi | `bb_modeli` id 2, 4, 6–9 | §5 — svaki red mora imati definisan status |

Smjer rješenja (implementacija zasebno, poslije odluke i backupa baze):
- aktivni takmičari se čitaju iz baze (`bb_modeli` + status kolona, npr. `aktivan`), ne iz hardkodovanih listi
- faza se čita isključivo iz `faza_id`; sufiks-redovi (id 12/13) se **preimenuju** (skidanje `-refine` iz naziva) — FK iz `bb_prevodi_knjige` pokazuje na `id` koji se ne mijenja, postojeći prevodi ostaju netaknuti
- UNIQUE constraint `(naziv, temperatura)` → `(naziv, temperatura, faza_id)` — trojka iz §5 postaje prirodni ključ tabele
- legacy `faza_id=NULL` → UPDATE na `faza_id=1` (istorijski bazni prevodioci), zatim `SET NOT NULL` — nužno i zbog UNIQUE semantike (NULL se u constraintu ne poredi, rupa bi razvodnila ključ)
- lookup modela u `bb_03` postaje naziv+temperatura+**faza** — trojka je i ključ pretrage, ne samo identifikacija
- **trajno pravilo:** svako buduće `ADD COLUMN` ovog tipa ide s DEFAULT vrijednošću prve faze — NULL ne smije nastati tiho

---

*Flavio & Claude · Buchenberg · koncept v1 · 5. jul 2026.*
