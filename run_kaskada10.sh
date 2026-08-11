#!/bin/bash
# run_kaskada10.sh — jednopetljana kaskada (s171).
#
# root -> ponavljaj KRUG { faza 12 (base) -> faza 16 (seed) -> faza 24 (strict) }
# KRUG = jedan prolaz kroz sve tri faze, sve tri s ISTOM vrijednoscu --runda.
#   Faza kaze STA se radi, runda KOJI PUT. U bazi ih razlikuje faza_id, pa runda
#   postoji samo da drugi krug smije ponoviti vec potrosenu fazu.
# STAJANJE: krug u kojem nijedna faza nije prebacila nijednu recenicu preko praga.
#
# Zasto (s171): u kaskadi 8/9 svaki mehanizam se posjeti tacno jednom i zatvori
# zauvijek. Faze 16 i 24 rade nad SIDROM (trenutni apsolutni pobjednik) — kad se
# sidro promijeni, to vise nije isti posao. Povod: faza 24 mjerena jednom, na
# terenu koji su base i seed upravo procesljali, dala je 0.005-0.032% n (es/ro/nl)
# — klasa "zavrsna runda iscrpljenog mehanizma", ne "prva runda novog".
#
# MJERE: GATE (prelasci praga) vodi odluku — najstariji kriterij, nepromijenjen.
#        ZBIR (prirast ocjena) je INFORMACIJA, ne zaustavlja.
#        Klon-stopa se ne ispisuje — izvodi se iz baze po (faza, runda).
set -e

FAZE="12 16 24"
MAX_KRUGOVA=30
PRAG_DEFAULT=0.95

KNJIGA=""; JEZICI=""; OD=""; DO=""; PRAG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga) KNJIGA="$2"; shift 2 ;;
        --jezici) JEZICI="$2"; shift 2 ;;
        --od)     OD="$2"; shift 2 ;;
        --do)     DO="$2"; shift 2 ;;
        --prag)   PRAG="$2"; shift 2 ;;
        --max)    MAX_KRUGOVA="$2"; shift 2 ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_kaskada10.sh --knjiga ID --jezici 'es' --od N --do M [--prag 0.95] [--max 30]"
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
echo ">>> PARAMETRI: knjiga=$KNJIGA jezici='$JEZICI' opseg=$OD-$DO prag=$PRAG faze='$FAZE' max=$MAX_KRUGOVA krugova"

echo ">>> KORAK 1: root (mistral-large-3:675b @ 0.1) — bez gatea"
time venv/bin/python src/bb_03_prevod.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
    --model mistral-large-3:675b --temp 0.1 --faza 1 \
    --embedder "$EMBEDDER" --jezici $JEZICI

echo ">>> KORAK 1: sudija"
time venv/bin/python src/bb_08_sudija.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI

echo ">>> KORAK 1: pobjednik"
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

time venv/bin/python src/bb_04_pobjednik.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI --prag "$PRAG" 2>&1 | tee "$TMP"

citaj_zbir() { awk '/BILANS jezika:/{for(i=1;i<=NF;i++)if($i~/^zbir=/){split($i,a,"=");s+=a[2]}}END{printf "%.4f", s+0}' "$1"; }
citaj_n()    { awk '/BILANS jezika:/{for(i=1;i<=NF;i++)if($i~/^n=/){split($i,a,"=");s+=a[2]}}END{print s+0}' "$1"; }

ZBIR_PRETHODNI=$(citaj_zbir "$TMP")
NTOT=$(citaj_n "$TMP")
echo ">>> ZBIR root: $ZBIR_PRETHODNI/$NTOT (polazno stanje)"

KRUG=1
PRETHODNI=-1
STANI=0
KRUG_ZAVRSENIH=0

while [ "$KRUG" -le "$MAX_KRUGOVA" ]; do
    echo ">>> ══════ KRUG $KRUG (runda=$KRUG) — ispod praga na ulazu prethodnog kruga: $PRETHODNI"
    PRVA=1
    for FAZA in $FAZE; do
        echo ">>> KRUG $KRUG | FAZA $FAZA (gated<$PRAG)"
        bash run_faza.sh --faza "$FAZA" --knjiga "$KNJIGA" --jezici "$JEZICI" \
            --od "$OD" --do "$DO" --runda "$KRUG" --prag "$PRAG" 2>&1 | tee "$TMP"

        GATE=$(grep -oE "ispod praga [0-9.]+: [0-9]+" "$TMP" | awk '{s+=$4} END{print s+0}')
        ZBIR=$(citaj_zbir "$TMP")
        NTOT=$(citaj_n "$TMP")

        awk -v z="$ZBIR" -v p="$ZBIR_PRETHODNI" -v n="$NTOT" -v k="$KRUG" -v f="$FAZA" 'BEGIN{
            d=z-p; rez=n-p;
            printf ">>> ZBIR krug %s faza %s: %.4f/%s (POSLIJE faze) — dodala %+.4f | %+.3f%% n | %+.2f%% rezerve\n",
                   k, f, z, n, d, (n>0?100*d/n:0), (rez>0?100*d/rez:0) }'
        ZBIR_PRETHODNI=$ZBIR

        # Odluka o PRETHODNOM krugu — gate prve faze izvjestava o cijelom prethodnom krugu.
        if [ "$PRVA" -eq 1 ]; then
            if [ "$PRETHODNI" -ge 0 ]; then
                DOBIT=$((PRETHODNI - GATE))
                echo ">>> BILANS krug $((KRUG-1)): ispod praga $GATE — prethodni krug prebacio $DOBIT"
                if [ "$DOBIT" -le 0 ]; then
                    echo ">>> STOP: krug $((KRUG-1)) nije prebacio nijednu recenicu preko praga."
                    STANI=1
                fi
            else
                echo ">>> BILANS krug $KRUG: ispod praga $GATE (prvi krug, nema poredjenja)"
            fi
            PRETHODNI=$GATE
            PRVA=0
            [ "$STANI" -eq 1 ] && break
            if [ "$GATE" -eq 0 ]; then
                echo ">>> STOP: nijedna recenica nije ispod praga."
                STANI=1; break
            fi
        fi
    done

    [ "$STANI" -eq 1 ] && break
    KRUG_ZAVRSENIH=$KRUG
    KRUG=$((KRUG + 1))
done

if [ "$KRUG" -gt "$MAX_KRUGOVA" ]; then
    echo ">>> STOP: dosegnut sigurnosni maksimum od $MAX_KRUGOVA krugova."
fi

echo ">>> SAZETAK: punih krugova=$KRUG_ZAVRSENIH | zadnji zapoceti krug=$KRUG | ispod praga na kraju=$PRETHODNI | zbir=$ZBIR_PRETHODNI/$NTOT"
okolina kraj
echo ">>> ZAVRSENO (prag=$PRAG): $(date)"
