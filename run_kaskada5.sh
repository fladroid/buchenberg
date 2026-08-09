#!/bin/bash
# run_kaskada5.sh — kaskada4 + parametrizovan prag.
# mistral@0.1 root (faza 1) -> 4 runde mistral@0.8 (faza 12), BEZ ranog izlaza.
#
# JEDINA razlika prema run_kaskada4.sh: --prag je opcionalan parametar
# (default 0.95) koji se PROSLJEDJUJE kroz run_faza.sh do bb_03_prevod.py.
# Do sada je prag zivio samo kao CLI default u bb_03 i run_faza.sh ga nije
# prosljedjivao (s162), pa je svaka gated runda uvijek isla na 0.95.
#
# Prag se primjenjuje SAMO na gated runde (faza >= 2). Root fazu ne dira -
# tamo gate ne postoji, pa bi slanje praga lazno sugerisalo da nesto radi.
set -e

FAZA_MISTRAL_08=12
BROJ_RUNDI=4
PRAG_DEFAULT=0.95

KNJIGA=""; JEZICI=""; OD=""; DO=""; PRAG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga) KNJIGA="$2"; shift 2 ;;
        --jezici) JEZICI="$2"; shift 2 ;;
        --od)     OD="$2"; shift 2 ;;
        --do)     DO="$2"; shift 2 ;;
        --prag)   PRAG="$2"; shift 2 ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_kaskada5.sh --knjiga ID --jezici 'nl es' --od N --do M [--prag 0.95]"
    exit 1
fi
PRAG="${PRAG:-$PRAG_DEFAULT}"

EMBEDDER="multilingual-e5-large"

# Okolina — neponovljiva poslije, a bez nje trajanja nisu uporediva.
# pgrep -fc uvijek ispise broj i vrati 1 kad nema pogodaka -> ':' samo cuva set -e.
okolina() {
    echo ">>> OKOLINA ($1): $(date)"
    echo "    bb_03 procesa vec aktivno: $(pgrep -fc bb_03_prevod.py || :)"
    echo "    load average:$(uptime | sed 's/.*load average://')"
    echo "    RAM: $(free -m | awk '/^Mem:/{print $7" MB dostupno od "$2" MB"}')"
}
okolina start
echo ">>> PARAMETRI: knjiga=$KNJIGA jezici='$JEZICI' opseg=$OD-$DO prag=$PRAG rundi=$BROJ_RUNDI"

echo ">>> KORAK 1: root (mistral-large-3:675b @ 0.1) — bez gatea, prag se ne primjenjuje"
time venv/bin/python src/bb_03_prevod.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
    --model mistral-large-3:675b --temp 0.1 --faza 1 \
    --embedder "$EMBEDDER" --jezici $JEZICI

echo ">>> KORAK 1: sudija"
time venv/bin/python src/bb_08_sudija.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI

echo ">>> KORAK 1: pobjednik"
time venv/bin/python src/bb_04_pobjednik.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI

for RUNDA in $(seq 1 $BROJ_RUNDI); do
    echo ">>> mistral@0.8 gated<$PRAG (faza $FAZA_MISTRAL_08, runda $RUNDA od $BROJ_RUNDI)"
    bash run_faza.sh --faza "$FAZA_MISTRAL_08" --knjiga "$KNJIGA" --jezici "$JEZICI" --od "$OD" --do "$DO" --runda "$RUNDA" --prag "$PRAG"
done

okolina kraj
echo ">>> ZAVRSENO (prag=$PRAG): $(date)"
