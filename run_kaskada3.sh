#!/bin/bash
# run_kaskada3.sh — mistral@0.1 root -> 2x mistral@0.8 -> 1x glm@0.8.
# Razlika od kaskade2: root je LLM (mistral@0.1), ne nllb; gated koraci koriste
# samo temp 0.8; skupi model (glm) se poziva jednom, na kraju, na ostatku.
# Redoslijed: root(f1) -> 12(r1) -> 12(r2) -> 14(r1).
set -e

FAZA_MISTRAL_08=12
FAZA_GLM_08=14

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
    echo "Upotreba: bash run_kaskada3.sh --knjiga ID --jezici 'de hr' --od N --do M"
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

for RUNDA in 1 2; do
    echo ">>> mistral@0.8 gated<0.95 (faza $FAZA_MISTRAL_08, runda $RUNDA)"
    bash run_faza.sh --faza "$FAZA_MISTRAL_08" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO" --runda "$RUNDA"
done

echo ">>> glm@0.8 gated<0.95 (faza $FAZA_GLM_08, runda 1)"
bash run_faza.sh --faza "$FAZA_GLM_08" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO" --runda 1

echo ">>> ZAVRSENO: $(date)"
