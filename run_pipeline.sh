#!/bin/bash
# run_pipeline.sh
# Pokreće kompletan pipeline za zadanu knjigu, jezike i raspon rečenica.
# Redosljed: 4x Ollama (serijski) + NLLB → sudija → pobjednik
#
# Primjer:
#   bash run_pipeline.sh --knjiga 5 --jezici "hr sr" --od 1 --do 100

set -e

KNJIGA=""
JEZICI=""
OD=""
DO=""

# Parsiranje argumenata
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga) KNJIGA="$2"; shift 2 ;;
        --jezici) JEZICI="$2"; shift 2 ;;
        --od)     OD="$2";     shift 2 ;;
        --do)     DO="$2";     shift 2 ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done

# Validacija
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_pipeline.sh --knjiga ID --jezici 'lang1 lang2' --od N --do M"
    exit 1
fi

EMBEDDER="multilingual-e5-large"
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="$LOG_DIR/pipeline_k${KNJIGA}_${TIMESTAMP}.log"

echo "======================================" | tee -a "$LOG"
echo "  BUCHENBERG PIPELINE" | tee -a "$LOG"
echo "  Knjiga : $KNJIGA" | tee -a "$LOG"
echo "  Jezici : $JEZICI" | tee -a "$LOG"
echo "  Raspon : $OD – $DO" | tee -a "$LOG"
echo "  Start  : $(date)" | tee -a "$LOG"
echo "======================================" | tee -a "$LOG"

# 1. Prijevodi — 4 Ollama modela (serijski)
for MODEL in "gemma3:12b" "ministral-3:14b"; do
    for TEMP in 0.8 0.1; do
        echo "" | tee -a "$LOG"
        echo ">>> Prevod: $MODEL @ temp=$TEMP" | tee -a "$LOG"
        time venv/bin/python src/bb_03_prevod.py \
            --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
            --model "$MODEL" --temp "$TEMP" \
            --embedder "$EMBEDDER" \
            --jezici $JEZICI 2>&1 | tee -a "$LOG"
    done
done

# 2. NLLB
echo "" | tee -a "$LOG"
echo ">>> Prevod: nllb-600M" | tee -a "$LOG"
time venv/bin/python src/bb_03_prevod.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
    --model "nllb-600M" \
    --embedder "$EMBEDDER" \
    --jezici $JEZICI 2>&1 | tee -a "$LOG"

# 3. Sudija
echo "" | tee -a "$LOG"
echo ">>> Sudija: gemma4:31b" | tee -a "$LOG"
time venv/bin/python src/bb_08_sudija.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
    --jezici $JEZICI 2>&1 | tee -a "$LOG"

# 4. Pobjednik
echo "" | tee -a "$LOG"
echo ">>> Pobjednik" | tee -a "$LOG"
time venv/bin/python src/bb_04_pobjednik.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
    --jezici $JEZICI 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "======================================" | tee -a "$LOG"
echo "  ZAVRŠENO: $(date)" | tee -a "$LOG"
echo "======================================" | tee -a "$LOG"
