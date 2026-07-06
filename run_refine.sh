#!/bin/bash
# run_refine.sh — refine prolaz: pobjednik kao hint (anchored mutation).
# Modeli se čitaju iz baze: aktivni modeli faze 2 (bb_aktivni_modeli.py).
# Primjer: bash run_refine.sh --knjiga 19 --jezici "hr" --od 1 --do 100
set -e
KNJIGA=""; JEZICI=""; OD=""; DO=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga) KNJIGA="$2"; shift 2 ;;
        --jezici) JEZICI="$2"; shift 2 ;;
        --od) OD="$2"; shift 2 ;;
        --do) DO="$2"; shift 2 ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_refine.sh --knjiga ID --jezici 'hr' --od N --do M"; exit 1
fi
EMBEDDER="multilingual-e5-large"
LOG_DIR="logs"; mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="$LOG_DIR/refine_k${KNJIGA}_${TIMESTAMP}.log"

MODELI=$(venv/bin/python src/bb_aktivni_modeli.py --faza 2)

echo ">>> REFINE k${KNJIGA} | $JEZICI | $OD-$DO | $(date)" | tee -a "$LOG"
echo ">>> Modeli (faza 2, aktivni):" | tee -a "$LOG"
echo "$MODELI" | sed 's/^/    /' | tee -a "$LOG"

while IFS='|' read -r MODEL TEMP; do
    echo "" | tee -a "$LOG"
    echo ">>> Refine prevod: $MODEL @ temp=$TEMP" | tee -a "$LOG"
    time venv/bin/python src/bb_03_prevod.py \
        --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
        --model "$MODEL" --temp "$TEMP" --faza 2 \
        --embedder "$EMBEDDER" \
        --jezici $JEZICI 2>&1 | tee -a "$LOG"
done <<< "$MODELI"

echo "" | tee -a "$LOG"
echo ">>> Sudija: gemma4:31b" | tee -a "$LOG"
time venv/bin/python src/bb_08_sudija.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo ">>> Pobjednik" | tee -a "$LOG"
time venv/bin/python src/bb_04_pobjednik.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI 2>&1 | tee -a "$LOG"

echo ">>> ZAVRŠENO: $(date)" | tee -a "$LOG"
