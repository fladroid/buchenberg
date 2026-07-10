# Session 126 — LLM NER: type reconciliation (Dio 1), method kolona, baseline

**Datum:** 10. jul 2026.
**Učesnici:** Flavio & Claude
**Fokus:** Početak LLM-potpomognute NER analize. Prvi dio od dva planirana:
type reconciliation (razrješavanje konfliktnih tipova entiteta preko LLM-a s
groundingom dokaznim rečenicama). Nova `method` kolona na NER tabelama za
"classic vs llm" paralelu i "prije/poslije" prikaz. Baseline izmjeren prije
gradnje. Relacije van rečenice + web + kompletiranje llm sloja = sljedeća sesija.
Usput: ispravka README header/footer koji je zaostajao na "sesija 122".

## Health snapshot
Početak: bb_recenice 50.624, bb_prevodi_recenica 1.518.170, bb_prev_recenica
296.578 (nepromijenjeno od s125 — Flavio nije pokretao runove). Git početak:
buchenberg HEAD d419f76 (s125), buchenweb 015efc5 (s125). Sve zeleno, Ollama
Cloud (glm-5.2, mistral-large-3:675b, gemma4:31b) OK. 8 poznatih `.bak` fajlova
+ poznati lažni "buchenweb zaostaje" alarm.

## Kontekst i cilj
Flavio otvorio rad na NER relacijama i type conflictima na nlp.html. Postojeći
"classic" NER (`bb_09_ner.py`: spaCy `en_core_web_sm` + gemma4:31b normalizacija)
ima dva ograničenja koja je Flavio identifikovao:
1. **Relacije samo unutar iste rečenice** — `get_ner_veze` u `bb_web_export.py`
   pravi co-occurrence isključivo self-joinom `bb_ner_recenica` po istoj
   `recenica_id`. Nema konteksta van rečenice → mreža izuzetno rijetka.
2. **Type conflict** — isto ime pod više tipova (Watson PERSON+GPE). Uzrok:
   spaCy nekonzistentnost + `bb_09` normalizacija ide tip-po-tip izolovano
   (`norm_map[tip][ime_orig]`), pa Gemma4 nikad ne vidi dva tipa istog imena
   zajedno da ih pomiri. UNIQUE(knjiga,ime_norm,tip) dozvoljava dupli red po tipu.

Flaviov predlog: propustiti knjigu kroz LLM koji radi ono što co-occurrence i
tip-po-tip normalizacija ne mogu. Cilj: zadržati classic NER + dodati LLM verziju,
s "prije/poslije" prikazom poboljšanja. UI: toggle "classic" / "with llm".

## Istraživanje (web) — nije izmišljanje tople vode
Provjereno da problemi imaju imena i poznata rješenja:
- **Relacije van rečenice** = Document-level Relation Extraction (DocRE);
  koreferencija je glavni tehnički korak. Postoji rad za dugu prozu (LlmLink,
  2025/26: dual LLM za entity linking u narativima) i korpus književne
  koreferencije (Openboek). LLM-bazirana koreferencija konkurentna specijalizovanim
  pipeline-ima (CRAC 2026).
- **Type conflict** = "entity type confusion" u NER literaturi; postoji obrazac
  SBERT embedding + cosine za pomirenje nekonzistentnih LLM entiteta (isti
  grounding princip kao naš s90/sudija dizajn).
Zaključak: Flaviova intuicija usklađena sa strukom.

## Odluke (dizajn)
- **`method` kolona, ne nove tabele** (Flaviov predlog). Dodata na `bb_ner_entiteti`
  + `bb_ner_recenica`. classic i llm koegzistiraju paralelno pod istom šemom.
  Type conflict se rješava sam kroz razdvajanje po metodu — bez diranja `tip` u
  ključu. (Claude prvo pogrešno mislio da `tip`-u-ključu smeta; Flavio ispravio:
  dupli tip po metodu classic nikad nije dupli u drugom metodu.)
- **Ulaz LLM-u = grounding rečenicama** (opcija B), ne samo statistika. Presudno:
  Baskerville je statistički 21:21 (izgleda kao prava dvojnost), ali tekst pokazuje
  da je većina PERSON/porodica a manjina GPE — statistika sama zavarala bi. Tek
  rečenice otkrivaju istinu.
- **Tri ishoda:** `greska` (manjinski tip = spaCy greška, spoji u primarni),
  `dvojnost` (dva legitimna smisla, npr. Baskerville osoba+imanje, zadrži oba),
  `ne_entitet` (uopšte nije entitet, npr. "I."=zamjenica, odbaci). LLM smije
  predložiti tip **van** postojećih labela (Coombe Tracey: classic PERSON/ORG →
  llm GPE).
- **Dvojnost — kompromis (Flavio prihvatio):** podjela veza prati postojeću
  classic (spaCy) raspodjelu po tipu. spaCy je pojedinačno nepouzdan, ali za
  dvojnost gdje LLM POTVRĐUJE oba tipa, spaCy podjela je razuman polazni proxy.
  Per-rečenica tačnost (drugi LLM prolaz) = opcija za kasnije ako zatreba.
- **Model: glm-5.2** (Flaviov izbor — noviji, na NVIDIA hardveru kod Ollame,
  poštuje think:false). NE gemma4:31b — sudija ostaje slijep/fiksan za svoj
  posao (s124 princip). Prevodilac radi NER analizu, sudija netaknut.
- **Prompt se prikazuje na stranici** (Flaviov zahtjev) — X-Ray prozirnost alata,
  ne samo rezultata. Radi se na KRAJU (poslije relacija + weba).

## Urađeno

### 1. README header/footer ispravka (commit af2cb63)
Header "Poslednje ažuriranje: ... sesija 122" i footer zaostajali kroz s123/s124/
s125 iako je sadržaj (§9, §14) ažuriran svaku sesiju. Ispravljeno na sesija 125.
Trajno pravilo (memorija): poslije SVAKE izmjene dokumenta provjeriti CIJELI fajl
(header+body+footer), ne samo dio koji se mijenja. Osnovna pažnja pri uređivanju,
ne posebna instrukcija po sesiji.

### 2. Baseline izmjeren (Hound, prije gradnje)
- **Type conflicti:** 18 imena s više od jednog tipa. Obrazac: većinom spaCy
  greške s ubjedljivom većinom (Watson PERSON:107/GPE:2), par pravih dvojnosti
  (Baskerville 21:21), par lažnih entiteta ("I.", "Neolithic").
- **Relacije:** 194 co-occurrence veze ukupno, samo **28 na default pragu ≥2**
  (nlp.html prikaz), 3 na ≥5, max težina 9 — na 3.852 rečenice. Mreža gotovo
  prazna: Holmes/Watson vezani samo kad su OBA imena doslovno u istoj rečenici.
- Baseline kao "prije" brojka za eksponat + informiše dizajn (širina prozora,
  prompt). X-Ray potez (isti kao k24, poluga A preduslov iz s124).

### 3. `method` kolona — DDL (backup + ALTER)
- **Backup prije DDL** (pravilo s123): pg_dump -Fc 1.5G →
  `/tmp/bb_backup_pre_method_20260710_145601.dump`, verifikovan pg_restore -l (30
  TABLE/DATA unosa).
- `ALTER TABLE bb_ner_entiteti/bb_ner_recenica ADD COLUMN method TEXT NOT NULL
  DEFAULT 'classic'` — postojeći redovi automatski 'classic' (3.302 entiteta +
  13.635 veza).
- `bb_ner_entiteti` UNIQUE: `(knjiga_id, ime_norm, tip)` → `(knjiga_id, ime_norm,
  tip, method)`. `bb_ner_recenica` UNIQUE netaknut (`entitet_id` FK već razdvaja
  metode). Sve u jednoj transakciji.

### 4. `bb_10_ner_llm.py` — nova skripta (Dio 1)
Struktura: učitaj konflikte (imena s >1 tip + do 4 dokazne rečenice po tipu,
ROW_NUMBER pattern) → sklopi grounded prompt → glm-5.2 (temp 0.0, isti
`ollama_call` obrazac kao bb_03) → parse JSON → upiši method='llm'.
- `ollama_call` identičan provjerenom bb_03 obrascu (stream:false, content.strip();
  glm-5.2 thinking u odvojenom polju, content čist).
- `ucitaj_konflikte`: SELECT imena s >1 tip, pa dokazne rečenice po (ime,tip).
- `sklopi_prompt`: grounding rečenicama, dozvoljava tip van labela, traži JSON
  {ishod, primarni_tip, sekundarni_tip, obrazlozenje, dokaz_pos}.
- `upisi_llm`: idempotentno (DELETE llm pa INSERT). greska→1 entitet (sve veze
  na primarni). dvojnost→2 entiteta (veze prate classic tip). ne_entitet→preskoči.

### 5. Dry-run + pravi upis (Hound)
- **Dry-run:** svih 18 konflikata, 0 JSON grešaka, ~2 min. Odluke provjerene
  golim okom naspram teksta: 17/18 očigledno tačne, Bradley (dvojnost ORG+PERSON,
  1:1) razumna ali diskutabilna — Flavio prihvatio kako jest. Watson: LLM čak
  objasnio uzrok greške ("GPE zbog blizine 'London'"). Coombe Tracey → GPE (tip
  van labela, radi). "I."/Neolithic → ne_entitet.
- **Pravi upis:** 18 llm entiteta (14 greška×1 + 2 dvojnost×2 = 18; 2 ne_entitet
  preskočeno), 364/365 veza. Verifikacija: Watson classic 2 reda→llm 1 (PERSON
  109); Coombe Tracey classic PERSON12+ORG1→llm GPE13; "I." classic 2 redova→llm
  nema; Baskerville/Bradley dvojnost sačuvana. classic 201 ent/1239 pojave, llm
  18 ent/365.

## Lekcije
- **Mjerenje mijenja dizajn PRIJE koda.** Tri puta ovu sesiju: (1) Baskerville
  21:21 izgleda kao ravnopravna dvojnost dok se ne pročitaju rečenice — dominantno
  PERSON; (2) Coombe Tracey pokazao da reconciliation mora dozvoliti tip van
  postojećih labela (svi classic tipovi pogrešni); (3) "I." = zamjenica iza tačke.
  Sva tri otkrivena baseline upitima, ugrađena u prompt prije pisanja skripte.
- Claude pogrešno zakomplikovao `tip`-u-ključu problem; Flavio ispravio jasnim
  argumentom (dupli tip po metodu nikad nije dupli u drugom metodu). Zabilježeno
  kao primjer — slušati Flaviov dizajn prije nego se gradi kontra-argument.

## Završno stanje
- Baza: `method` kolona na bb_ner_entiteti + bb_ner_recenica (DEFAULT 'classic').
  Hound (id 1): classic sloj netaknut, novi llm sloj = 18 razriješenih konflikata.
  Ostale knjige: samo classic (bb_10 pokrenut samo na Houndu).
- `src/bb_10_ner_llm.py`: nova skripta (Dio 1 — type reconciliation). buchenberg/main.
- Web NETAKNUT → BB_VERSION ostaje s125.5. bb_web_export.py NIJE još diran
  (mapiranje promjena zabilježeno za sljedeću sesiju: get_ner/get_ner_veze +
  method param, JSON izlaz, nlp.html toggle).
- Backup: /tmp/bb_backup_pre_method_20260710_145601.dump (u pgdb kontejneru).

## Sljedeći koraci (Dio 2 i dalje)
1. **Kompletiranje llm sloja** — trenutno llm ima SAMO 18 konfliktnih imena.
   Odluka (preporuka Claude, Flavio da potvrdi): opcija 1 = llm potpun sloj
   (kopirati i nekonfliktne classic entitete kao čiste), da "with llm" prikaz bude
   samostalan i potpun. Opcija 2 = llm samo delta, web spaja. Opcija 1 čišća za
   prije/poslije.
2. **Relacije van rečenice** — DocRE/koreferencija preko LLM-a. Prozor od N
   rečenica (ne cijela knjiga — izbjeći kombinatorni šum iz s90), s groundingom
   (LLM opravdava vezu citatom/pozicijom). Novo skladište relacija kao objekta
   (tip veze + dokaz + izvorne rečenice) — oblikovati kad vidimo prvi LLM izlaz.
3. **Web** — bb_web_export.py: get_ner/get_ner_veze + method param; JSON izlaz
   (jedan fajl s obje verzije ili dva lazy); nlp.html toggle "classic"/"with llm"
   (obrazac kao nlp-type-btn) za Entity Links/Type Conflicts/Network.
4. **Prompt na stranici** (Flaviov zahtjev) — prikaz korištenog prompta, X-Ray
   prozirnost alata. Radi se na kraju.
5. bb_10 na ostale knjige kad Dio 1+2 sazriju.

---
*Flavio & Claude · Buchenberg · Session 126 · 10. jul 2026.*
