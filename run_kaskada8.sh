#!/bin/bash
# run_kaskada8.sh — dvoetapna kaskada bez fiksnog broja rundi.
#
# ETAPA 1 (faza 12, base, bez seeda): vrti dok prebacuje bar jednu preko praga.
# ETAPA 2 (faza 16, refine, sa seedom): kad etapa 1 stane, NE staje se nego se
#         mijenja rezim i vrti se po istom pravilu do nove nule.
#
# Zasto (s169): nula u etapi 1 ne znaci da je recenica gotova, nego da je
# nezavisno izvlacenje iscrpljeno — klon-stopa base grane je 10-22%, seed grane
# 2-3%. Model na temp 0.8 vrti isti tekst u krug; seed mu kaze sta vec ima i
# trazi da ode dalje. Prelazak se ne procjenjuje — sistem ga sam prijavi nulom.
#
# Nula parametara za pogoditi: obje etape staju same.
set -e

FAZA_BASE=12
FAZA_SEED=16
MAX_RUNDI=30
PRAG_DEFAULT=0.95

KNJIGA=""; JEZICI=""; OD=""; DO=""; PRAG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga) KNJIGA="$2"; shift 2 ;;
        --jezici) JEZICI="$2"; shift 2 ;;
        --od)     OD="$2"; shift 2 ;;
        --do)     DO="$2"; shift 2 ;;
        --prag)   PRAG="$2"; shift 2 ;;
        --max)    MAX_RUNDI="$2"; shift 2 ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_kaskada8.sh --knjiga ID --jezici 'es' --od N --do M [--prag 0.95] [--max 30]"
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
echo ">>> PARAMETRI: knjiga=$KNJIGA jezici='$JEZICI' opseg=$OD-$DO prag=$PRAG etapa1=faza$FAZA_BASE etapa2=faza$FAZA_SEED max=$MAX_RUNDI"

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

# s170: zbir ocjena kao druga mjera. Cita se iz BILANS linije koju ispisuje bb_04.
citaj_zbir() { awk '/BILANS jezika:/{for(i=1;i<=NF;i++)if($i~/^zbir=/){split($i,a,"=");s+=a[2]}}END{printf "%.4f", s+0}' "$1"; }
citaj_n()    { awk '/BILANS jezika:/{for(i=1;i<=NF;i++)if($i~/^n=/){split($i,a,"=");s+=a[2]}}END{print s+0}' "$1"; }

ZBIR_PRETHODNI=$(citaj_zbir "$TMP")
NTOT=$(citaj_n "$TMP")
echo ">>> ZBIR root: $ZBIR_PRETHODNI/$NTOT (polazno stanje)"

ETAPA=1
FAZA=$FAZA_BASE
PRETHODNI=-1
RUNDA=1
R1_KRAJ=0

while [ "$RUNDA" -le "$MAX_RUNDI" ]; do
    echo ">>> ETAPA $ETAPA | RUNDA $RUNDA (faza $FAZA, gated<$PRAG) — prethodno ispod praga: $PRETHODNI"
    bash run_faza.sh --faza "$FAZA" --knjiga "$KNJIGA" --jezici "$JEZICI" \
        --od "$OD" --do "$DO" --runda "$RUNDA" --prag "$PRAG" 2>&1 | tee "$TMP"

    GATE=$(grep -oE "ispod praga [0-9.]+: [0-9]+" "$TMP" | awk '{s+=$4} END{print s+0}')

    ZBIR=$(citaj_zbir "$TMP")
    NTOT=$(citaj_n "$TMP")
    awk -v z="$ZBIR" -v p="$ZBIR_PRETHODNI" -v n="$NTOT" -v e="$ETAPA" -v r="$RUNDA" 'BEGIN{
        d=z-p; rez=n-p;
        printf ">>> ZBIR e%s runde %s: %.4f/%s (POSLIJE runde) — ova runda dodala %+.4f | %+.3f%% n | %+.2f%% rezerve\n",
               e, r, z, n, d, (n>0?100*d/n:0), (rez>0?100*d/rez:0) }'
    ZBIR_PRETHODNI=$ZBIR

    if [ "$PRETHODNI" -lt 0 ]; then
        echo ">>> BILANS e$ETAPA runde $RUNDA: ispod praga $GATE (prva runda etape, nema poredjenja)"
    else
        DOBIT=$((PRETHODNI - GATE))
        echo ">>> BILANS e$ETAPA runde $RUNDA: ispod praga $GATE — prethodna runda prebacila $DOBIT"
        if [ "$DOBIT" -le 0 ]; then
            if [ "$ETAPA" -eq 1 ]; then
                R1_KRAJ=$((RUNDA - 1))
                echo ">>> PRELAZAK: etapa 1 iscrpljena poslije runde $R1_KRAJ (ostalo $GATE ispod praga)."
                echo ">>> PRELAZAK: nastavlja se SA SEEDOM (faza $FAZA_SEED)."
                ETAPA=2
                FAZA=$FAZA_SEED
                PRETHODNI=-1
                RUNDA=$((RUNDA + 1))
                continue
            else
                echo ">>> STOP: etapa 2 iscrpljena poslije runde $((RUNDA - 1))."
                break
            fi
        fi
    fi

    if [ "$GATE" -eq 0 ]; then
        echo ">>> STOP: nijedna recenica nije ispod praga (etapa $ETAPA)."
        break
    fi

    PRETHODNI=$GATE
    RUNDA=$((RUNDA + 1))
done

if [ "$RUNDA" -gt "$MAX_RUNDI" ]; then
    echo ">>> STOP: dosegnut sigurnosni maksimum od $MAX_RUNDI rundi."
fi

echo ">>> SAZETAK: etapa 1 (base) rundi=$R1_KRAJ | ukupno rundi=$RUNDA | zavrsna etapa=$ETAPA"
okolina kraj
echo ">>> ZAVRSENO (prag=$PRAG): $(date)"
