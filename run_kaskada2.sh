#!/bin/bash
# run_kaskada2.sh — nllb root -> mistral-only kaskada, dvije runde po fazi.
# Redoslijed: 11(r1) -> 12(r1) -> 11(r2) -> 12(r2).
# Hipoteza (s164): ponovni poziv istog modela daje vise novih kandidata nego
# promjena temperature (sonda: unutar-T varijacija 0.9888 na temp 0.8, veca od
# razlike 0.8-vs-1.0 = 0.9909).
# Runda mijenja prevodi_knjige_id -> already_done() propusta; gate (prag) i dalje
# vazi jer zavisi samo od faza>=2. Svaki poziv run_faza.sh je pun ciklus
# (prevod -> sudija -> pobjednik), pa svaka runda mjeri prag protiv prethodne.
# Bez glm faza (13/14) — namjerno.
set -e

FAZA_MISTRAL_01=11
FAZA_MISTRAL_08=12
RUNDE="1 2"

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
    echo "Upotreba: bash run_kaskada2.sh --knjiga ID --jezici 'de hr' --od N --do M"
    exit 1
fi

EMBEDDER="multilingual-e5-large"

echo ">>> KORAK 1: root (nllb-600M @ 0.0)"
venv/bin/python src/bb_03_prevod.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
    --model nllb-600M --temp 0.0 --faza 1 \
    --embedder "$EMBEDDER" --jezici $JEZICI

echo ">>> KORAK 1: sudija"
venv/bin/python src/bb_08_sudija.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI

echo ">>> KORAK 1: pobjednik"
venv/bin/python src/bb_04_pobjednik.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI

for RUNDA in $RUNDE; do
    echo ">>> mistral@0.1 gated<0.95 (faza $FAZA_MISTRAL_01, runda $RUNDA)"
    bash run_faza.sh --faza "$FAZA_MISTRAL_01" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO" --runda "$RUNDA"

    echo ">>> mistral@0.8 gated<0.95 (faza $FAZA_MISTRAL_08, runda $RUNDA)"
    bash run_faza.sh --faza "$FAZA_MISTRAL_08" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO" --runda "$RUNDA"
done

echo ">>> ZAVRSENO: $(date)"
