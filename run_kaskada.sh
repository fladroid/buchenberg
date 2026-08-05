#!/bin/bash
# run_kaskada.sh — nllb root -> 4 nezavisne gated faze (mistral 0.1/0.8, glm 0.1/0.8)
# Svaka gated faza je odvojen red u bazi — redoslijed je izbor, ne nuznost (s147).
# Registrovano u sesiji 163: faze 11-14 (bez seeda, prompt 'base').
set -e

FAZA_MISTRAL_01=11
FAZA_MISTRAL_08=12
FAZA_GLM_01=13
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
    echo "Upotreba: bash run_kaskada.sh --knjiga ID --jezici 'de hr' --od N --do M"
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

echo ">>> KORAK 2: mistral@0.1 gated<0.95 (faza $FAZA_MISTRAL_01)"
bash run_faza.sh --faza "$FAZA_MISTRAL_01" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO"

echo ">>> KORAK 3: mistral@0.8 gated<0.95 (faza $FAZA_MISTRAL_08)"
bash run_faza.sh --faza "$FAZA_MISTRAL_08" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO"

echo ">>> KORAK 4: glm@0.1 gated<0.95 (faza $FAZA_GLM_01)"
bash run_faza.sh --faza "$FAZA_GLM_01" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO"

echo ">>> KORAK 5: glm@0.8 gated<0.95 (faza $FAZA_GLM_08)"
bash run_faza.sh --faza "$FAZA_GLM_08" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO"

echo ">>> ZAVRSENO: $(date)"
