#!/bin/bash
# run_kaskada9.sh — troetapna kaskada. Nadogradnja kaskade8 (s170).
#
# ETAPA 1 (faza 12, base, bez seeda)      : vrti dok prebacuje bar jednu preko praga.
# ETAPA 2 (faza 16, refine, sa seedom)    : isto pravilo, do nove nule.
# ETAPA 3 (faza 24, refine-strict, seed)  : DRUGO PRAVILO — vrti dok prirast ZBIRA
#          ocjena prelazi --prirast (% od n). Staje kad padne ispod.
#
# Zasto trece pravilo (s170): gate broji samo prelaske praga i slijep je za
# poboljsanja koja ne prebace 0.95. Izmjereno na 11 kaskada8 prolaza: sedam od
# jedanaest jezika stalo je dok je zbir jos rastao (bs +0.143, bg +0.117).
# Zasto refine-strict: formulisan za iscrpljenu distribuciju ("ako ne mozes
# bolje, napravi znacajno DRUGACIJE") — jedini prompt koji nikad nije koristen.
#
# Izvod za default --prirast 0.10 (s170, nad 133 runde): zavrsne runde
# iscrpljenog mehanizma daju 0.000-0.143% n, prve runde novog 0.195-3.238% n.
# x=0.10 stedi 39% rundi uz 7.3% prirasta i najmanje vaskrsenja (5).
# BROJ JE PARAMETAR, ne dogma — potvrditi prvim stvarnim prolazom.
set -e

FAZA_BASE=12
FAZA_SEED=16
FAZA_STRICT=24
MAX_RUNDI=30
PRAG_DEFAULT=0.95
PRIRAST_DEFAULT=0.10

KNJIGA=""; JEZICI=""; OD=""; DO=""; PRAG=""; PRIRAST=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga)  KNJIGA="$2"; shift 2 ;;
        --jezici)  JEZICI="$2"; shift 2 ;;
        --od)      OD="$2"; shift 2 ;;
        --do)      DO="$2"; shift 2 ;;
        --prag)    PRAG="$2"; shift 2 ;;
        --prirast) PRIRAST="$2"; shift 2 ;;
        --max)     MAX_RUNDI="$2"; shift 2 ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_kaskada9.sh --knjiga ID --jezici 'es' --od N --do M [--prag 0.95] [--prirast 0.10] [--max 30]"
    exit 1
fi
PRAG="${PRAG:-$PRAG_DEFAULT}"
PRIRAST="${PRIRAST:-$PRIRAST_DEFAULT}"

EMBEDDER="multilingual-e5-large"

okolina() {
    echo ">>> OKOLINA ($1): $(date)"
    echo "    bb_03 procesa vec aktivno: $(pgrep -fc bb_03_prevod.py || :)"
    echo "    load average:$(uptime | sed 's/.*load average://')"
    echo "    RAM: $(free -m | awk '/^Mem:/{print $7" MB dostupno od "$2" MB"}')"
}
okolina start
echo ">>> PARAMETRI: knjiga=$KNJIGA jezici='$JEZICI' opseg=$OD-$DO prag=$PRAG prirast=$PRIRAST% etapa1=faza$FAZA_BASE etapa2=faza$FAZA_SEED etapa3=faza$FAZA_STRICT max=$MAX_RUNDI"

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

ETAPA=1
FAZA=$FAZA_BASE
PRETHODNI=-1
RUNDA=1
R1_KRAJ=0
R2_KRAJ=0

while [ "$RUNDA" -le "$MAX_RUNDI" ]; do
    echo ">>> ETAPA $ETAPA | RUNDA $RUNDA (faza $FAZA, gated<$PRAG) — prethodno ispod praga: $PRETHODNI"
    bash run_faza.sh --faza "$FAZA" --knjiga "$KNJIGA" --jezici "$JEZICI" \
        --od "$OD" --do "$DO" --runda "$RUNDA" --prag "$PRAG" 2>&1 | tee "$TMP"

    GATE=$(grep -oE "ispod praga [0-9.]+: [0-9]+" "$TMP" | awk '{s+=$4} END{print s+0}')

    ZBIR=$(citaj_zbir "$TMP")
    NTOT=$(citaj_n "$TMP")
    DPCT=$(awk -v z="$ZBIR" -v p="$ZBIR_PRETHODNI" -v n="$NTOT" 'BEGIN{printf "%.4f", (n>0 ? 100*(z-p)/n : 0)}')
    awk -v z="$ZBIR" -v p="$ZBIR_PRETHODNI" -v n="$NTOT" -v e="$ETAPA" -v r="$RUNDA" 'BEGIN{
        d=z-p; rez=n-p;
        printf ">>> ZBIR e%s runde %s: %.4f/%s (POSLIJE runde) — ova runda dodala %+.4f | %+.3f%% n | %+.2f%% rezerve\n",
               e, r, z, n, d, (n>0?100*d/n:0), (rez>0?100*d/rez:0) }'
    ZBIR_PRETHODNI=$ZBIR

    if [ "$ETAPA" -le 2 ]; then
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
                    ETAPA=2; FAZA=$FAZA_SEED; PRETHODNI=-1
                    RUNDA=$((RUNDA + 1)); continue
                else
                    R2_KRAJ=$((RUNDA - 1))
                    echo ">>> PRELAZAK: etapa 2 iscrpljena poslije runde $R2_KRAJ (ostalo $GATE ispod praga)."
                    echo ">>> PRELAZAK: nastavlja se STRIKTNIM refineom (faza $FAZA_STRICT), pravilo = prirast zbira >= $PRIRAST% n."
                    ETAPA=3; FAZA=$FAZA_STRICT; PRETHODNI=-1
                    RUNDA=$((RUNDA + 1)); continue
                fi
            fi
        fi
    else
        echo ">>> BILANS e3 runde $RUNDA: ispod praga $GATE (informativno — odluka ide po zbiru)"
        if awk -v d="$DPCT" -v x="$PRIRAST" 'BEGIN{exit !(d < x)}'; then
            echo ">>> STOP: prirast zbira $DPCT% ispod praga prirasta $PRIRAST% (etapa 3, poslije runde $RUNDA)."
            break
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

echo ">>> SAZETAK: e1 (base) rundi=$R1_KRAJ | e2 (seed) kraj=$R2_KRAJ | ukupno rundi=$RUNDA | zavrsna etapa=$ETAPA"
okolina kraj
echo ">>> ZAVRSENO (prag=$PRAG prirast=$PRIRAST%): $(date)"
