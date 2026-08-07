#!/bin/bash
# run_kaskada4.sh — mjerni run za kalibraciju adaptivne kaskade.
# mistral@0.1 root (faza 1) -> 4 runde mistral@0.8 (faza 12), BEZ ranog izlaza.
# Svrha: snimiti punu krivu prinosa da se X, N, r i tolerancija mogu
# simulirati retroaktivno nad bazom, bez ponovnog prevodjenja.
set -e

FAZA_MISTRAL_08=12
BROJ_RUNDI=4

KNJIGA=""; JEZICI=""; OD=""; DO=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga) KNJIGA="$2"; shift 2 ;;
        --jezici) JEZICI="$2"; shift 2 ;;
        --od)     OD="$2"; shift 2 ;;
        --do)     DO="$2"; shift 2 ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_kaskada4.sh --knjiga ID --jezici 'nl es' --od N --do M"
    exit 1
fi

EMBEDDER="multilingual-e5-large"

echo ">>> KORAK 1: root (mistral-large-3:675b @ 0.1)"
venv/bin/python src/bb_03_prevod.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
    --model mistral-large-3:675b --temp 0.1 --faza 1 \
    --embedder "$EMBEDDER" --jezici $JEZICI

echo ">>> KORAK 1: sudija"
venv/bin/python src/bb_08_sudija.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI

echo ">>> KORAK 1: pobjednik"
venv/bin/python src/bb_04_pobjednik.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI

for RUNDA in $(seq 1 $BROJ_RUNDI); do
    echo ">>> mistral@0.8 gated<0.95 (faza $FAZA_MISTRAL_08, runda $RUNDA od $BROJ_RUNDI)"
    bash run_faza.sh --faza "$FAZA_MISTRAL_08" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO" --runda "$RUNDA"
done

echo ">>> ZAVRSENO: $(date)"
