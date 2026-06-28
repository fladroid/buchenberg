#!/bin/bash
# run_refine.sh — self-refine prolaz: pobjednik kao hint.
# 2 modela (gemma3-refine, ministral-refine) @0.8, single. Bez NLLB.
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
echo ">>> SELF-REFINE k${KNJIGA} | $JEZICI | $OD-$DO | $(date)" | tee -a "$LOG"

for MODEL in "gemma3:12b-refine" "ministral-3:14b-refine"; do
    echo "" | tee -a "$LOG"
    echo ">>> Refine prevod: $MODEL @ 0.8" | tee -a "$LOG"
    time venv/bin/python src/bb_03_prevod.py \
        --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
        --model "$MODEL" --refine \
        --embedder "$EMBEDDER" \
        --jezici $JEZICI 2>&1 | tee -a "$LOG"
done

echo "" | tee -a "$LOG"
echo ">>> Sudija: gemma4:31b" | tee -a "$LOG"
time venv/bin/python src/bb_08_sudija.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo ">>> Pobjednik" | tee -a "$LOG"
time venv/bin/python src/bb_04_pobjednik.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI 2>&1 | tee -a "$LOG"

echo ">>> ZAVRŠENO: $(date)" | tee -a "$LOG"
