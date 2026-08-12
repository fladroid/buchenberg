#!/bin/bash
# run_kaskada13.sh — dvoblokovska kaskada s uslovnim skupim blokom (s172).
#
# root (mistral-large-3:675b @ 0.1)
#   -> BLOK A (jeftini model), max 4 kruga:
#        KRUG = faza 12 (mistral@0.8 base) -> faza 24 (mistral@0.8 refine-strict)
#        Izvrsava se NAJMANJE jednom. Izlaz: krug bez prirasta, ili plafon.
#   -> USLOV: ako je % pobjednika IZNAD praga < X (default 60) -> BLOK B, inace kraj.
#   -> BLOK B (skupi model), max 2 kruga:
#        KRUG = faza 14 (glm@0.8 base) -> faza 26 (glm@0.8 refine-strict)
#        Izvrsava se NAJMANJE jednom ako je uslov ispunjen. Isto pravilo izlaza.
#
# LOGIKA: glm pobjedjuje mistrala na svih 14 jezika (58-64% na zajednickom terenu),
# ali je Ollama klasa 3 naspram mistralove 2. Zato ulazi TEK kad jeftini model
# iscrpi svoje, i SAMO ako je stanje losije od X. Skupo — ali se zna zasto.
#
# X mjeri STANJE (% iznad praga), stop unutar bloka mjeri PRIRAST (prebaceno u krugu).
# Namjerno razlicito: X bira DA LI uopste platiti glm, prirast bira KOLIKO dugo.
#
# Cijena: najgori slucaj root + 4x2 + 2x2 = 13 faza; najbolji root + 2 = 3 faze.
#
# MJERE: GATE (prelasci praga) vodi odluku. ZBIR (prirast ocjena) je INFORMACIJA.
set -e
set -o pipefail

ROOT_MODEL="mistral-large-3:675b"
ROOT_TEMP="0.1"
A_FAZE="12 24"
B_FAZE="14 26"
A_MAX=4
B_MAX=2
X_DEFAULT=60
PRAG_DEFAULT=0.95
EMBEDDER="multilingual-e5-large"

KNJIGA=""; JEZICI=""; OD=""; DO=""; PRAG=""; X=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga) KNJIGA="$2"; shift 2 ;;
        --jezici) JEZICI="$2"; shift 2 ;;
        --od)     OD="$2"; shift 2 ;;
        --do)     DO="$2"; shift 2 ;;
        --prag)   PRAG="$2"; shift 2 ;;
        --x)      X="$2"; shift 2 ;;
        --amax)   A_MAX="$2"; shift 2 ;;
        --bmax)   B_MAX="$2"; shift 2 ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_kaskada13.sh --knjiga ID --jezici 'de hr' --od N --do M [--prag 0.95] [--x 60] [--amax 4] [--bmax 2]"
    exit 1
fi
PRAG="${PRAG:-$PRAG_DEFAULT}"
X="${X:-$X_DEFAULT}"

TMP=$(mktemp); trap 'rm -f "$TMP"' EXIT

okolina() {
    echo ">>> OKOLINA ($1): $(date)"
    echo "    bb_03 procesa vec aktivno: $(pgrep -fc bb_03_prevod.py || :)"
    echo "    load average:$(uptime | sed 's/.*load average://')"
    echo "    RAM: $(free -m | awk '/^Mem:/{print $7" MB dostupno od "$2" MB"}')"
}

# BILANS bb_04 = apsolutno stanje POSLIJE faze (s170). Zbir svih jezika.
citaj_zbir()  { awk '/BILANS jezika:/{for(i=1;i<=NF;i++)if($i~/^zbir=/){split($i,a,"=");s+=a[2]}}END{printf "%.4f", s+0}' "$1"; }
citaj_n()     { awk '/BILANS jezika:/{for(i=1;i<=NF;i++)if($i~/^n=/){split($i,a,"=");s+=a[2]}}END{print s+0}' "$1"; }
citaj_ispod() { awk '/BILANS jezika:/{s+=$NF}END{print s+0}' "$1"; }

pct_iznad() {   # $1=ispod  $2=ukupno  -> cijeli postotak IZNAD praga
    awk -v i="$1" -v n="$2" 'BEGIN{ printf "%d", (n>0 ? 100*(n-i)/n : 100) }'
}

okolina start
echo ">>> PARAMETRI: knjiga=$KNJIGA jezici='$JEZICI' opseg=$OD-$DO prag=$PRAG"
echo ">>> PLAN: root=$ROOT_MODEL@$ROOT_TEMP | blok A='$A_FAZE' max=$A_MAX | X=$X% | blok B='$B_FAZE' max=$B_MAX"

# ─────────────────────────── ROOT ───────────────────────────
echo ">>> KORAK 1: root ($ROOT_MODEL @ $ROOT_TEMP) — bez gatea"
time venv/bin/python src/bb_03_prevod.py \
    --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
    --model "$ROOT_MODEL" --temp "$ROOT_TEMP" --faza 1 \
    --embedder "$EMBEDDER" --jezici $JEZICI

echo ">>> KORAK 1: sudija"
time venv/bin/python src/bb_08_sudija.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" --jezici $JEZICI

echo ">>> KORAK 1: pobjednik"
time venv/bin/python src/bb_04_pobjednik.py --knjiga "$KNJIGA" --od "$OD" --do "$DO" \
    --jezici $JEZICI --prag "$PRAG" 2>&1 | tee "$TMP"

ZBIR_PRETHODNI=$(citaj_zbir "$TMP")
NTOT=$(citaj_n "$TMP")
ISPOD=$(citaj_ispod "$TMP")
echo ">>> ZBIR root: $ZBIR_PRETHODNI/$NTOT | ispod praga: $ISPOD | iznad: $(pct_iznad "$ISPOD" "$NTOT")% (polazno stanje)"

izvrsi_fazu() {   # $1=faza  $2=runda  $3=oznaka bloka
    local FAZA="$1" RUNDA="$2" BLOK="$3"
    echo ">>> $BLOK | FAZA $FAZA (gated<$PRAG)"
    bash run_faza.sh --faza "$FAZA" --knjiga "$KNJIGA" --jezici "$JEZICI" \
        --od "$OD" --do "$DO" --runda "$RUNDA" --prag "$PRAG" 2>&1 | tee "$TMP"

    local Z N I D
    Z=$(citaj_zbir "$TMP"); N=$(citaj_n "$TMP"); I=$(citaj_ispod "$TMP")
    D=$((ISPOD - I))
    awk -v z="$Z" -v p="$ZBIR_PRETHODNI" -v n="$N" -v b="$BLOK" -v f="$FAZA" -v i="$I" -v d="$D" 'BEGIN{
        dz=z-p;
        printf ">>> %s FAZA %s: ispod praga %s (prebacila %+d) | zbir %.4f/%s dodala %+.4f | %+.3f%% n\n",
               b, f, i, d, z, n, dz, (n>0?100*dz/n:0) }'
    ZBIR_PRETHODNI=$Z; NTOT=$N; ISPOD=$I
    PREBACILA=$D
}

# ── petlja bloka: $1=naziv  $2=faze  $3=max  $4=pocetna runda
#    Vraca u BLOK_KRUGOVA broj izvrsenih krugova, u BLOK_RAZLOG razlog izlaska.
izvrsi_blok() {
    local NAZIV="$1" FAZE="$2" MAXK="$3" RUNDA0="$4"
    local K=1 UKUPNO
    BLOK_KRUGOVA=0; BLOK_RAZLOG="plafon"
    while [ "$K" -le "$MAXK" ]; do
        echo ">>> ══════ BLOK $NAZIV KRUG $K/$MAXK (runda=$((RUNDA0 + K - 1))) — ispod praga na ulazu: $ISPOD"
        UKUPNO=0
        for FAZA in $FAZE; do
            izvrsi_fazu "$FAZA" "$((RUNDA0 + K - 1))" "BLOK $NAZIV KRUG $K"
            UKUPNO=$((UKUPNO + PREBACILA))
        done
        BLOK_KRUGOVA=$K
        echo ">>> BILANS blok $NAZIV krug $K: prebaceno ukupno $UKUPNO | ispod praga sada $ISPOD | iznad $(pct_iznad "$ISPOD" "$NTOT")%"
        if [ "$UKUPNO" -le 0 ]; then
            echo ">>> STOP blok $NAZIV: krug $K bez prirasta (obje faze nula)."
            BLOK_RAZLOG="gate-nula"; return 0
        fi
        if [ "$ISPOD" -eq 0 ]; then
            echo ">>> STOP blok $NAZIV: nijedna recenica nije ispod praga."
            BLOK_RAZLOG="prazan-lijevak"; return 0
        fi
        K=$((K + 1))
    done
    echo ">>> STOP blok $NAZIV: dosegnut plafon od $MAXK krugova."
    return 0
}

# ─────────────────────────── BLOK A ───────────────────────────
izvrsi_blok "A" "$A_FAZE" "$A_MAX" 1
A_KRUGOVA=$BLOK_KRUGOVA; A_RAZLOG=$BLOK_RAZLOG
PCT=$(pct_iznad "$ISPOD" "$NTOT")
echo ">>> BILANS BLOK A: krugova=$A_KRUGOVA/$A_MAX (izlazak: $A_RAZLOG) | iznad praga: $PCT% (prag odluke X=$X%)"

# ─────────────────────── USLOV -> BLOK B ───────────────────────
B_KRUGOVA=0; B_RAZLOG="nije-pokrenut"
if [ "$PCT" -lt "$X" ]; then
    echo ">>> ODLUKA: $PCT% < $X% -> pokrecem BLOK B (glm-5.2, skupi model)"
    izvrsi_blok "B" "$B_FAZE" "$B_MAX" "$((A_KRUGOVA + 1))"
    B_KRUGOVA=$BLOK_KRUGOVA; B_RAZLOG=$BLOK_RAZLOG
    echo ">>> BILANS BLOK B: krugova=$B_KRUGOVA/$B_MAX (izlazak: $B_RAZLOG)"
else
    echo ">>> ODLUKA: $PCT% >= $X% -> BLOK B se PRESKACE (glm nije pozvan, ustedjeno do $((B_MAX * 2)) faza)"
fi

FAZA_UKUPNO=$((1 + A_KRUGOVA * 2 + B_KRUGOVA * 2))
echo ">>> SAZETAK: blok A=$A_KRUGOVA/$A_MAX ($A_RAZLOG) | blok B=$B_KRUGOVA/$B_MAX ($B_RAZLOG) | X=$X%"
echo ">>> SAZETAK: izvrseno faza ukupno=$FAZA_UKUPNO (ukljucujuci root)"
echo ">>> SAZETAK: ispod praga na kraju=$ISPOD | iznad=$(pct_iznad "$ISPOD" "$NTOT")% | zbir=$ZBIR_PRETHODNI/$NTOT"
okolina kraj
echo ">>> ZAVRSENO (prag=$PRAG, X=$X): $(date)"
