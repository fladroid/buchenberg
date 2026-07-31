#!/bin/bash
# run_root_gated.sh — "gated root", jedan poziv za cijeli obrazac iz s155/s156.
# Privremeno suzi root fazu (iskljuci glm) -> pusti root (mistral+nllb) -> sudija -> pobjednik
# -> pusti gated fazu (default 10: glm, base prompt, BEZ pivota, prag 0.95 default u bb_03).
# glm se UVIJEK vraca na aktivan=true za fazu 1 na kraju (trap na EXIT), cak i ako nesto padne.
# Faza 10 (ili druga --gated-faza) mora vec biti registrovana u bazi (bb_faze + bb_faze_a1/a2/a3)
# — ovaj skript je ne kreira, samo pokrece.
#
# Primjer:
#   bash run_root_gated.sh --knjiga 22 --jezici "de hr it sr" --od 741 --do 780

set -e
KNJIGA=""; JEZICI=""; OD=""; DO=""; GLM_MODEL="glm-5.2"; GATED_FAZA="10"
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga)     KNJIGA="$2"; shift 2 ;;
        --jezici)     JEZICI="$2"; shift 2 ;;
        --od)         OD="$2"; shift 2 ;;
        --do)         DO="$2"; shift 2 ;;
        --gated-faza) GATED_FAZA="$2"; shift 2 ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_root_gated.sh --knjiga ID --jezici 'de hr it sr' --od N --do M [--gated-faza N]"
    exit 1
fi

LOG_DIR="logs"; mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="$LOG_DIR/root_gated_k${KNJIGA}_${TIMESTAMP}.log"

cleanup() {
    echo "" | tee -a "$LOG"
    echo ">>> Cleanup: vrati $GLM_MODEL u fazu 1 (standardno stanje)" | tee -a "$LOG"
    venv/bin/python src/bb_toggle_model.py --faza 1 --model "$GLM_MODEL" --aktivan true 2>&1 | tee -a "$LOG"
}
trap cleanup EXIT

echo "======================================" | tee -a "$LOG"
echo "  GATED ROOT — k${KNJIGA} | $JEZICI | $OD-$DO | gated-faza=$GATED_FAZA" | tee -a "$LOG"
echo "  Start: $(date)" | tee -a "$LOG"
echo "======================================" | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo ">>> Korak 1: iskljuci $GLM_MODEL iz faze 1 (root)" | tee -a "$LOG"
venv/bin/python src/bb_toggle_model.py --faza 1 --model "$GLM_MODEL" --aktivan false 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo ">>> Korak 2: root faza (suzen bazen, bez $GLM_MODEL)" | tee -a "$LOG"
bash ./run_faza.sh --faza 1 --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO" 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo ">>> Korak 3: gated faza $GATED_FAZA ($GLM_MODEL, prag 0.95 default)" | tee -a "$LOG"
bash ./run_faza.sh --faza "$GATED_FAZA" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO" 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "======================================" | tee -a "$LOG"
echo "  ZAVRŠENO: $(date)" | tee -a "$LOG"
echo "======================================" | tee -a "$LOG"
