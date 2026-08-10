#!/bin/bash
# run_kaskada7.sh — kaskada BEZ fiksnog broja rundi.
# Pravilo zaustavljanja (Flavio, s169): vrti dok prethodna runda prebacuje
# bar jednu recenicu preko praga. Nema parametra za broj rundi.
#
# Mjera: broj 'ispod praga' koji gate ispise na pocetku svake runde. Taj broj
# je stanje PRIJE te runde, pa razlika izmedju dvije uzastopne runde = koliko
# je prethodna prebacila. Kad razlika padne na 0 (ili ispod), staje se.
# Posljedica: uvijek se plati jedna runda vise nego sto je bilo korisno —
# to je cijena saznanja da je stalo, i na repu je mala.
#
# --faza 12 (default) = bez seeda, prompt 'base'
# --faza 16           = sa seedom,  prompt 'refine'
set -e

FAZA=12
MAX_RUNDI=20
PRAG_DEFAULT=0.95

KNJIGA=""; JEZICI=""; OD=""; DO=""; PRAG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga) KNJIGA="$2"; shift 2 ;;
        --jezici) JEZICI="$2"; shift 2 ;;
        --od)     OD="$2"; shift 2 ;;
        --do)     DO="$2"; shift 2 ;;
        --prag)   PRAG="$2"; shift 2 ;;
        --faza)   FAZA="$2"; shift 2 ;;
        --max)    MAX_RUNDI="$2"; shift 2 ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_kaskada7.sh --knjiga ID --jezici 'es sl' --od N --do M [--prag 0.95] [--faza 12|16] [--max 20]"
    exit 1
fi
PRAG="${PRAG:-$PRAG_DEFAULT}"

EMBEDDER="multilingual-e5-large"

okolina() {
    echo ">>> OKOLINA ($1): $(date)"
    echo "    bb_03 procesa vec aktivno: $(pgrep -fc bb_03_prevod.py || :)"
    echo "    load average:$(uptime | sed 's/.*load average://')"
    echo "    RAM: $(free -m | awk '/^Mem:/{print $7" MB dostupno od "$2" MB"}')"
}
okolina start
echo ">>> PARAMETRI: knjiga=$KNJIGA jezici='$JEZICI' opseg=$OD-$DO prag=$PRAG faza=$FAZA max=$MAX_RUNDI (bez fiksnog broja rundi)"

echo ">>> KORAK 1: root (mistral-large-3:675b @ 0.1) — bez gatea"
time venv/bin/python src/bb_03_prevod.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
    --model mistral-large-3:675b --temp 0.1 --faza 1 \
    --embedder "$EMBEDDER" --jezici $JEZICI

echo ">>> KORAK 1: sudija"
time venv/bin/python src/bb_08_sudija.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI

echo ">>> KORAK 1: pobjednik"
time venv/bin/python src/bb_04_pobjednik.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI

TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
PRETHODNI=-1
RUNDA=1

while [ "$RUNDA" -le "$MAX_RUNDI" ]; do
    echo ">>> RUNDA $RUNDA (faza $FAZA, gated<$PRAG) — prethodno ispod praga: $PRETHODNI"
    bash run_faza.sh --faza "$FAZA" --knjiga "$KNJIGA" --jezici "$JEZICI" \
        --od "$OD" --do "$DO" --runda "$RUNDA" --prag "$PRAG" 2>&1 | tee "$TMP"

    GATE=$(grep -oE "ispod praga [0-9.]+: [0-9]+" "$TMP" | awk '{s+=$4} END{print s+0}')

    if [ "$PRETHODNI" -lt 0 ]; then
        echo ">>> BILANS runde $RUNDA: ispod praga $GATE (prva runda, nema poredjenja)"
    else
        DOBIT=$((PRETHODNI - GATE))
        echo ">>> BILANS runde $RUNDA: ispod praga $GATE — prethodna runda prebacila $DOBIT"
        if [ "$DOBIT" -le 0 ]; then
            echo ">>> STOP: runda $((RUNDA - 1)) nije prebacila nijednu recenicu preko praga."
            break
        fi
    fi

    if [ "$GATE" -eq 0 ]; then
        echo ">>> STOP: nijedna recenica nije ispod praga."
        break
    fi

    PRETHODNI=$GATE
    RUNDA=$((RUNDA + 1))
done

if [ "$RUNDA" -gt "$MAX_RUNDI" ]; then
    echo ">>> STOP: dosegnut sigurnosni maksimum od $MAX_RUNDI rundi."
fi

okolina kraj
echo ">>> ZAVRSENO (prag=$PRAG, faza=$FAZA, rundi izvrseno=$RUNDA): $(date)"
