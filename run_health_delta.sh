#!/bin/bash
# run_health_delta.sh — satni health check monitoring (Cowork Scheduled task).
#
# DIZAJN (namjerno): Cowork prompt ostaje fiksan skelet — "pokreni ovu
# skriptu, posalji mi tacno njen izlaz". Sva logika, svi koraci i format
# zive OVDJE, u skripti. Dodavanje/mijenjanje/brisanje koraka ide ovdje,
# bez ikad diranja samog Cowork zadatka.
#
# Kratak izlaz (stdout, jedna linija) -> Cowork poruka / push notifikacija.
# Detaljan izvjestaj -> schedulogs/health_check.log, trajna hronoloska
# istorija na serveru, nezavisna od Cowork interfejsa (koji Claude ovdje
# ne moze citati unazad).

set -uo pipefail
cd "$(dirname "$0")"

SCHEDULOGS="schedulogs"
mkdir -p "$SCHEDULOGS"

STANJE="$SCHEDULOGS/rupa_stanje.txt"
DETALJNI_LOG="$SCHEDULOGS/health_check.log"

IZLAZ=$(venv/bin/python src/health_check.py 2>&1)
CISTO=$(echo "$IZLAZ" | sed -r 's/\x1B\[[0-9;]*[mK]//g')

BROJ=$(echo "$CISTO" | grep -oE "Rupe pronadjene[[:space:]]+[0-9]+" | grep -oE "[0-9]+" | head -1)
SADA=$(date '+%Y-%m-%d %H:%M:%S')

if [ -z "$BROJ" ]; then
    KRATKA="Health check GRESKA — nisam nasao broj rupa u izlazu. Detalji: $SCHEDULOGS/health_check.log"
    {
        echo "================================================================"
        echo "[$SADA] GRESKA — 'Rupe pronadjene' nije nadjeno u izlazu health checka"
        echo "$CISTO"
        echo "================================================================"
    } >> "$DETALJNI_LOG"
    echo "$KRATKA"
    exit 1
fi

if [ -f "$STANJE" ]; then
    PRETHODNI=$(cut -d' ' -f1 "$STANJE")
    RAZLIKA=$((BROJ - PRETHODNI))
else
    PRETHODNI="n/a"
    RAZLIKA=0
fi

BROJ_CRVENIH=$(echo "$CISTO" | grep "❌" | grep -vc "Rupe pronadjene")
BROJ_ZELENIH=$(echo "$CISTO" | grep -c "✅")

RECENICE=$(echo "$CISTO" | grep "bb_recenice" | grep -oE "[0-9,]+ redova" | head -1)
PREVODI=$(echo "$CISTO" | grep "bb_prevodi_recenica" | grep -oE "[0-9,]+ redova" | head -1)
POBJEDNICI=$(echo "$CISTO" | grep "bb_prev_recenica" | grep -oE "[0-9,]+ redova" | head -1)

OUSAGE=$(./run_ousage.sh --kratko 2>&1)

{
    echo "================================================================"
    echo "[$SADA] rupe=$BROJ prethodno=$PRETHODNI razlika=$RAZLIKA"
    echo "korpus: recenice=${RECENICE:-n/a} prevodi=${PREVODI:-n/a} pobjednici=${POBJEDNICI:-n/a}"
    echo "provjere (env/DB/Ollama/NLLB/venv/git): ${BROJ_ZELENIH:-0} OK / ${BROJ_CRVENIH:-0} problem(a) osim rupa"
    echo "$OUSAGE"
    echo "================================================================"
} >> "$DETALJNI_LOG"

echo "$BROJ $SADA" > "$STANJE"

if [ "$PRETHODNI" == "n/a" ]; then
    KRATKA="Health check OK — $BROJ rupa (prva provjera, nema baze za poredjenje). Detalji: $SCHEDULOGS/health_check.log"
elif [ "$RAZLIKA" -gt 0 ]; then
    KRATKA="Health check: +$RAZLIKA novih rupa ($PRETHODNI -> $BROJ). Detalji: $SCHEDULOGS/health_check.log"
elif [ "$RAZLIKA" -lt 0 ]; then
    KRATKA="Health check: rupa smanjeno ($PRETHODNI -> $BROJ, $RAZLIKA). Detalji: $SCHEDULOGS/health_check.log"
else
    KRATKA="Health check OK — $BROJ rupa, bez promjene. Detalji: $SCHEDULOGS/health_check.log"
fi

if [ "${BROJ_CRVENIH:-0}" -gt 0 ]; then
    KRATKA="$KRATKA ⚠️ ${BROJ_CRVENIH} problem(a) van rupa — vidi log."
fi

echo "$KRATKA"
echo "$OUSAGE"
