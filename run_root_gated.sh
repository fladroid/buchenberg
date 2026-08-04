#!/bin/bash
# run_root_gated.sh — "gated root", pokreće root + gated fazu u jednom pozivu.
# PRETPOSTAVKA (s158): "svijet" (bb_faze_a1.aktivan za fazu 1) je VEĆ ručno
# postavljen PRIJE poziva ove skripte — ova skripta glm NE isključuje niti
# vraća. Ulazak/izlazak iz suženog stanja je ručan, protokolom-vođen čin
# (vidi docs/KAKO-NovaFaza.md), odvojen od ovog automatizovanog poziva.
# Razlog (s157): auto-toggle unutar skripte je globalno DB stanje bez izolacije
# po procesu/jeziku — paralelni pozivi su tiho kvarili jedan drugom root
# konfiguraciju. Ova skripta se sad smije pozivati paralelno (po jeziku),
# JEDNOM kad je svijet ručno postavljen za sve pozive koji dijele taj prozor.
#
# Faza 10 (ili druga --gated-faza) mora već biti registrovana u bazi
# (bb_faze + bb_faze_a1/a2/a3) — ovaj skript je ne kreira, samo pokreće.
#
# Primjer (poslije ručnog UPDATE bb_faze_a1 ... aktivan=false za glm/faza 1):
#   bash run_root_gated.sh --knjiga 22 --jezici "de hr it sr" --od 741 --do 780

set -e
KNJIGA=""; JEZICI=""; OD=""; DO=""; GATED_FAZA="10"; URADI_AKO_NEMA=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga)     KNJIGA="$2"; shift 2 ;;
        --jezici)     JEZICI="$2"; shift 2 ;;
        --od)         OD="$2"; shift 2 ;;
        --do)         DO="$2"; shift 2 ;;
        --gated-faza) GATED_FAZA="$2"; shift 2 ;;
        --uradi-ako-nema) URADI_AKO_NEMA="--uradi-ako-nema"; shift ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_root_gated.sh --knjiga ID --jezici 'de hr it sr' --od N --do M [--gated-faza N]"
    echo "Preduslov: bb_faze_a1 za fazu 1 vec rucno postavljen (vidi docs/KAKO-NovaFaza.md)."
    exit 1
fi

LOG_DIR="logs"; mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="$LOG_DIR/root_gated_k${KNJIGA}_${TIMESTAMP}.log"

echo "======================================" | tee -a "$LOG"
echo "  GATED ROOT — k${KNJIGA} | $JEZICI | $OD-$DO | gated-faza=$GATED_FAZA" | tee -a "$LOG"
echo "  (svijet pretpostavljen vec postavljen rucno)" | tee -a "$LOG"
echo "  Start: $(date)" | tee -a "$LOG"
echo "======================================" | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo ">>> Korak 1: root faza (bazen po vec postavljenom stanju bb_faze_a1)" | tee -a "$LOG"
bash ./run_faza.sh --faza 1 --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO" $URADI_AKO_NEMA 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo ">>> Korak 2: gated faza $GATED_FAZA (prag 0.95 default)" | tee -a "$LOG"
bash ./run_faza.sh --faza "$GATED_FAZA" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO" $URADI_AKO_NEMA 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "======================================" | tee -a "$LOG"
echo "  ZAVRŠENO: $(date)" | tee -a "$LOG"
echo "======================================" | tee -a "$LOG"
