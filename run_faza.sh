#!/bin/bash
# run_faza.sh — izvršava JEDNU fazu. Faza = redni broj + jedinstveni ID izvršavanja.
# Šta se radi određuje METOD (bb_metode), a ne broj faze.
#   metod 'base'        (root) — bazni prevod, tačno jednom
#   metod 'self-refine'        — anchored mutation nad trenutnim pobjednikom, M puta
# Modeli se čitaju iz baze: aktivni modeli te faze (bb_aktivni_modeli.py --faza N).
# --faza je OBAVEZAN i ne izmišlja se sam: vidi se šta radiš.
# --force je svojstvo PROLAZA (kao u run_ner.sh) -> prosljeđuje se sudiji (ponovno ocjenjivanje).
# Primjer: bash run_faza.sh --faza 2 --knjiga 22 --jezici "de hr" --od 1 --do 20
set -e
set -o pipefail   # bez ovoga | tee guta izlazni kod Pythona i set -e ne vidi pad
FAZA=""; KNJIGA=""; JEZICI=""; OD=""; DO=""; FORCE=""; RUNDA="1"; URADI_AKO_NEMA=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --faza)   FAZA="$2"; shift 2 ;;
        --knjiga) KNJIGA="$2"; shift 2 ;;
        --jezici) JEZICI="$2"; shift 2 ;;
        --od)     OD="$2"; shift 2 ;;
        --do)     DO="$2"; shift 2 ;;
        --force)  FORCE="--force"; shift ;;
        --runda)  RUNDA="$2"; shift 2 ;;
        --uradi-ako-nema) URADI_AKO_NEMA="--uradi-ako-nema"; shift ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$FAZA" || -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_faza.sh --faza N --knjiga ID --jezici 'de hr' --od N --do M [--force]"
    exit 1
fi

EMBEDDER="multilingual-e5-large"
LOG_DIR="logs"; mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="$LOG_DIR/faza${FAZA}_k${KNJIGA}_${TIMESTAMP}.log"

# --- guard 1: faza mora postojati u bazi, i nosi metod ---
INFO=$(venv/bin/python src/bb_faza_info.py --faza "$FAZA")
IFS='|' read -r METOD_ID METOD_NAZIV METOD_ROOT <<< "$INFO"

# --- guard 2: faza mora imati aktivne modele ---
MODELI=$(venv/bin/python src/bb_aktivni_modeli.py --faza "$FAZA")

echo ">>> FAZA $FAZA | metod: $METOD_NAZIV (id=$METOD_ID, root=$METOD_ROOT)" | tee -a "$LOG"
echo ">>> k${KNJIGA} | $JEZICI | $OD-$DO | runda=$RUNDA ${FORCE:+force} $(date)" | tee -a "$LOG"
echo ">>> Modeli (aktivni, faza $FAZA):" | tee -a "$LOG"
echo "$MODELI" | sed 's/^/    /' | tee -a "$LOG"

while IFS='|' read -r MODEL TEMP; do
    echo "" | tee -a "$LOG"
    echo ">>> Prevod [$METOD_NAZIV]: $MODEL @ temp=$TEMP" | tee -a "$LOG"
    time venv/bin/python src/bb_03_prevod.py \
        --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
        --model "$MODEL" --temp "$TEMP" --faza "$FAZA" --runda "$RUNDA" \
        --embedder "$EMBEDDER" $URADI_AKO_NEMA \
        --jezici $JEZICI 2>&1 | tee -a "$LOG"
done <<< "$MODELI"

echo "" | tee -a "$LOG"
echo ">>> Sudija: gemma4:31b ${FORCE:+(force)}" | tee -a "$LOG"
time venv/bin/python src/bb_08_sudija.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI $FORCE 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo ">>> Pobjednik (argmax preko SVIH faza)" | tee -a "$LOG"
time venv/bin/python src/bb_04_pobjednik.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI 2>&1 | tee -a "$LOG"

echo ">>> ZAVRŠENO: $(date)" | tee -a "$LOG"
