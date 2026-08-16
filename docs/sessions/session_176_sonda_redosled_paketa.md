# Sonda: efekat redoslijeda unutar batcha

*Prilog uz session_176.md. Nastavak s170 (kloniranje pri ponavljanju). Ovo pitanje: mijenja li mešanje redoslijeda 20 rečenica u paketu prevod/ocjenu VIŠE nego što to čini sama nezavisna varijacija (šum)?*

**Postavka (Flaviov dizajn):** knjiga 22, pozicije 2000–2019, 20 rečenica, mistral-large-3:675b @ 0.8, prompt 'base', jezici hr+de. Četiri runde na istih 20 rečenica:
- Runda 1 (O1) — originalan redoslijed
- Runda 2 (S2) — promiješan redoslijed (fiksan shuffle)
- Runda 3 (O3) — originalan redoslijed ponovo → bazna linija šuma za original
- Runda 4 (S4) — isti shuffle kao S2 ponovo → bazna linija šuma za mešano

Za svaku rečenicu: kosinus sličnost (multilingual-e5-large) između sve 4 verzije, plus sudijina (gemma4:31b) ocjena sve 4 verzije zajedno u jednom pozivu. Skripta: `src/sandbox_redosled_paketa.py`, READ-ONLY, nula upisa u produkcionu bazu. Pokrenuto sa `nohup`, log: `logs/sandbox_redosled_paketa.log`.

---

## Rezultat — sličnost teksta (kosinus)

| mjera | prosjek | sd |
|---|---|---|
| O1↔O3 (šum, original) | 0.9935 | 0.0239 |
| S2↔S4 (šum, mešano) | 0.9950 | 0.0099 |
| unakrsno O×S (efekat mešanja) | 0.9880 | 0.0139 |

Upareno bazna linija (prosjek O1↔O3 i S2↔S4) naspram unakrsnog poređenja, upareni t-test na svih 40 rečenica (hr+de):

**t=4.73, p=0.00003 — visoko značajno.** Razlika mala u apsolutnom iznosu (+0.0062), ali dosljedna i statistički čvrsta.

**Zaključak: sastav batcha stvarno mijenja tekst prevoda**, mjerljivo iznad šuma. Potvrđuje i produbljuje s170 nalaz — sad izmjereno preko cijelog paketa od 20, ne samo na ponovljenim duplikatima.

---

## Rezultat — sudijina ocjena

| grupa | prosjek |
|---|---|
| O-grupa (O1, O3) | 0.9420 |
| S-grupa (S2, S4) | 0.9587 |
| razlika (O − S) | −0.0167 |

Upareni t-test: **t=−1.35, p=0.186 — nije statistički značajno.** Cohen's d = −0.21 (mali efekat).

| jezik | O prosjek | S prosjek | razlika | p |
|---|---|---|---|---|
| hr | 0.9400 | 0.9625 | −0.0225 | 0.207 |
| de | 0.9441 | 0.9549 | −0.0109 | 0.557 |

Smjer isti u oba jezika (S nešto viša ocjena), ali razlika ne prelazi šum na ovom uzorku (n=20 po jeziku).

---

## Sinteza

Tekst i ocjena pričaju dvije različite priče:

- **Riječi se mijenjaju pouzdano** (p<0.0001) — mešanje redoslijeda garantovano proizvodi drugačiju formulaciju.
- **Kvalitet se ne mijenja pouzdano** (p=0.19) — ne može se tvrditi da je mešanje bolje ili gore od ponovljenog originala, na ovom uzorku.

Batch sastav je dokazano "neregistrovan parametar" (kao što je s170 već imenovao) za SAM TEKST — dokaz da bi to bio i parametar za KVALITET još ne postoji na ovom uzorku.

**Za kaskada ideju:** mešanje redoslijeda kao izvor **raznolikosti** — potkrijepljeno, jeftino, radi. Kao izvor **boljeg kvaliteta** — nije potkrijepljeno; treba mnogo veće n (stotine rečenica) da se razlika od ~0.02 razdvoji od šuma (~0.07-0.08).

## Napomena o trošku

8 batch-prevoda (4 runde × 2 jezika) + 40 sudijskih poziva. Nula upisa u `bb_prevodi_recenica`.
