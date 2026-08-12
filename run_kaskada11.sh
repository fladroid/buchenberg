#!/bin/bash
# run_kaskada11.sh — dvodijelna kaskada s tvrdim plafonom (s172).
#
# root (qwen3.5:397b @ 0.1)
#   -> PETLJA: ponavljaj KRUG { faza 12 (mistral@0.8 base) -> faza 27 (qwen@0.8 base) }
#      STOP: (a) obje faze kruga prebacile nulu, ili (b) dosegnut MAX_KRUGOVA=3.
#   -> SEED BLOK (uvijek, bez obzira ZASTO se izaslo iz petlje):
#      faza 24 (mistral@0.8 refine-strict) -> faza 28 (qwen@0.8 refine-strict)
#      Tacno jednom svaka, bez gate uslova.
#
# RAZLIKA OD KASKADE 10:
#   - u krugu su SAMO base faze (bez seeda); seed dolazi tek poslije petlje
#   - plafon je tvrd (3 kruga), ne sigurnosni (30)
#   - stajanje je NEODLOZENO: gate se cita iz BILANS-a bb_04 POSLIJE svake faze,
#     pa se nula vidi odmah. Desetka je gate citala iz bb_03 PRIJE prevoda, pa je
#     odluku o krugu donosila tek u sljedecem krugu (jedna faza u prazno).
#
# MJERE: GATE (prelasci praga) vodi odluku. ZBIR (prirast ocjena) je INFORMACIJA.
#        Obje se ispisuju za svaku fazu — i u petlji i u seed bloku.
set -e
set -o pipefail

ROOT_MODEL="qwen3.5:397b"
ROOT_TEMP="0.1"
KRUG_FAZE="12 27"
SEED_FAZE="24 28"
MAX_KRUGOVA=3
PRAG_DEFAULT=0.95
EMBEDDER="multilingual-e5-large"

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
    echo "Upotreba: bash run_kaskada11.sh --knjiga ID --jezici 'de hr' --od N --do M [--prag 0.95] [--max 3]"
    exit 1
fi
PRAG="${PRAG:-$PRAG_DEFAULT}"

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

okolina start
echo ">>> PARAMETRI: knjiga=$KNJIGA jezici='$JEZICI' opseg=$OD-$DO prag=$PRAG"
echo ">>> PLAN: root=$ROOT_MODEL@$ROOT_TEMP | krug='$KRUG_FAZE' max=$MAX_KRUGOVA | seed blok='$SEED_FAZE'"

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
echo ">>> ZBIR root: $ZBIR_PRETHODNI/$NTOT | ispod praga: $ISPOD (polazno stanje)"

# ─────────────────────────── PETLJA ───────────────────────────
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

KRUG=1
KRUG_ZAVRSENIH=0
RAZLOG="plafon"
while [ "$KRUG" -le "$MAX_KRUGOVA" ]; do
    echo ">>> ══════ KRUG $KRUG/$MAX_KRUGOVA (runda=$KRUG) — ispod praga na ulazu: $ISPOD"
    UKUPNO_KRUG=0
    for FAZA in $KRUG_FAZE; do
        izvrsi_fazu "$FAZA" "$KRUG" "KRUG $KRUG"
        UKUPNO_KRUG=$((UKUPNO_KRUG + PREBACILA))
    done
    KRUG_ZAVRSENIH=$KRUG
    echo ">>> BILANS krug $KRUG: prebaceno ukupno $UKUPNO_KRUG | ispod praga sada $ISPOD"

    if [ "$UKUPNO_KRUG" -le 0 ]; then
        echo ">>> STOP: krug $KRUG nije prebacio nijednu recenicu preko praga (obje faze nula)."
        RAZLOG="gate-nula"; break
    fi
    if [ "$ISPOD" -eq 0 ]; then
        echo ">>> STOP: nijedna recenica nije ispod praga."
        RAZLOG="prazan-lijevak"; break
    fi
    KRUG=$((KRUG + 1))
done
[ "$RAZLOG" = "plafon" ] && echo ">>> STOP: dosegnut plafon od $MAX_KRUGOVA krugova."

# ─────────────────────── SEED BLOK (uvijek) ───────────────────────
echo ">>> ══════ SEED BLOK (izlazak: $RAZLOG) — izvrsava se uvijek, po jednom svaka faza"
SEED_RUNDA=$((KRUG_ZAVRSENIH + 1))
SEED_UKUPNO=0
for FAZA in $SEED_FAZE; do
    izvrsi_fazu "$FAZA" "$SEED_RUNDA" "SEED"
    SEED_UKUPNO=$((SEED_UKUPNO + PREBACILA))
done
echo ">>> BILANS seed blok: prebaceno ukupno $SEED_UKUPNO | ispod praga sada $ISPOD"

echo ">>> SAZETAK: krugova=$KRUG_ZAVRSENIH/$MAX_KRUGOVA (izlazak: $RAZLOG) | seed runda=$SEED_RUNDA"
echo ">>> SAZETAK: ispod praga na kraju=$ISPOD | zbir=$ZBIR_PRETHODNI/$NTOT"
okolina kraj
echo ">>> ZAVRSENO (prag=$PRAG): $(date)"
