#!/bin/bash
# run_kaskada6.sh — kaskada5 sa SEEDOM.
# mistral@0.1 root (faza 1) -> 4 runde mistral@0.8 (faza 16), BEZ ranog izlaza.
#
# JEDINA razlika prema run_kaskada5.sh: gated faza je 16 (prompt 'refine')
# umjesto 12 (prompt 'base'). Posljedica u bb_03: uses_seed=True -> modelu se
# salje trenutni apsolutni pobjednik kao referenca, i batch pada 20 -> 5 (s159).
#
# Motiv (s169): na repu k12/es faza 16 preuzela 50.3% naspram 12.5% za petu
# base rundu, uz nula klonova naspram 8.3%. Ovaj skript mjeri isto OD PRVE
# RUNDE, ne samo na repu.
set -e

FAZA_REFINE=16
BROJ_RUNDI=4
PRAG_DEFAULT=0.95

KNJIGA=""; JEZICI=""; OD=""; DO=""; PRAG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga) KNJIGA="$2"; shift 2 ;;
        --jezici) JEZICI="$2"; shift 2 ;;
        --od)     OD="$2"; shift 2 ;;
        --do)     DO="$2"; shift 2 ;;
        --prag)   PRAG="$2"; shift 2 ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_kaskada6.sh --knjiga ID --jezici 'nl es' --od N --do M [--prag 0.95]"
    exit 1
fi
PRAG="${PRAG:-$PRAG_DEFAULT}"

EMBEDDER="multilingual-e5-large"

okolina() {
    echo ">>> OKOLINA ($1): $(date)"
    echo "    bb_03 procesa vec aktivno: $(pgrep -fc bb_03_prevod.py || :)"
    echo "    load average:$(uptime | sed 's/.*load average://')"
    echo "    RAM: $(free -m | awk '/^Mem:/{print $7" MB dostupno od "$2" MB"}')"
}
okolina start
echo ">>> PARAMETRI: knjiga=$KNJIGA jezici='$JEZICI' opseg=$OD-$DO prag=$PRAG rundi=$BROJ_RUNDI faza=$FAZA_REFINE (sa seedom)"

echo ">>> KORAK 1: root (mistral-large-3:675b @ 0.1) — bez gatea, prag se ne primjenjuje"
time venv/bin/python src/bb_03_prevod.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
    --model mistral-large-3:675b --temp 0.1 --faza 1 \
    --embedder "$EMBEDDER" --jezici $JEZICI

echo ">>> KORAK 1: sudija"
time venv/bin/python src/bb_08_sudija.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI

echo ">>> KORAK 1: pobjednik"
time venv/bin/python src/bb_04_pobjednik.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI

for RUNDA in $(seq 1 $BROJ_RUNDI); do
    echo ">>> mistral@0.8 SA SEEDOM gated<$PRAG (faza $FAZA_REFINE, runda $RUNDA od $BROJ_RUNDI)"
    bash run_faza.sh --faza "$FAZA_REFINE" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO" --runda "$RUNDA" --prag "$PRAG"
done

okolina kraj
echo ">>> ZAVRSENO (prag=$PRAG, faza=$FAZA_REFINE): $(date)"
