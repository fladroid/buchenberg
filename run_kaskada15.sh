#!/bin/bash
# run_kaskada15.sh — isto kao kaskada14 (s177), ali OBRNUT redoslijed poziva
# unutar svakog kruga: mesano PRVO, original DRUGO (kaskada14 je bilo obrnuto).
# Svrha: kontrola da li je efekat vezan za MESANJE samo po sebi, ili djelimicno
# za to sto original uvijek ide prvi (npr. stanje sistema/cache/redoslijed poziva
# ka Ollami). Runda-brojevi (koja runda = original, koja = mesano) ostaju identicni
# kaskadi14 — mijenja se samo REDOSLIJED POZIVA, ne dodjela runda.
#
# root (mistral-large-3:675b @ 0.1) — isto kao k14, bez mesanja
#   -> BLOK A (mistral@0.8), FIKSNO 2 kruga:
#        krug K (runda 2K-1=original, runda 2K=mesano):
#          faza 12 mesano -> faza 12 original -> faza 24 mesano -> faza 24 original
#   -> USLOV (isto kao k13/k14): ako je % iznad praga < X (default 60) -> BLOK B
#   -> BLOK B (glm@0.8), FIKSNO 1 krug (runda 1=original, runda 2=mesano):
#        faza 14 mesano -> faza 14 original -> faza 26 mesano -> faza 26 original
#
# Cijena: FIKSNO root + 8 (blok A) [+ 4 (blok B) ako uslov] = 9 ili 13 faza.
set -e
set -o pipefail

ROOT_MODEL="mistral-large-3:675b"
ROOT_TEMP="0.1"
X_DEFAULT=60
PRAG_DEFAULT=0.95
EMBEDDER="multilingual-e5-large"
SHUFFLE_SEED_DEFAULT=42

KNJIGA=""; JEZICI=""; OD=""; DO=""; PRAG=""; X=""; SHUFFLE_SEED=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --knjiga) KNJIGA="$2"; shift 2 ;;
        --jezici) JEZICI="$2"; shift 2 ;;
        --od)     OD="$2"; shift 2 ;;
        --do)     DO="$2"; shift 2 ;;
        --prag)   PRAG="$2"; shift 2 ;;
        --x)      X="$2"; shift 2 ;;
        --shuffle-seed) SHUFFLE_SEED="$2"; shift 2 ;;
        *) echo "Nepoznat argument: $1"; exit 1 ;;
    esac
done
if [[ -z "$KNJIGA" || -z "$JEZICI" || -z "$OD" || -z "$DO" ]]; then
    echo "Upotreba: bash run_kaskada15.sh --knjiga ID --jezici 'es sl' --od N --do M [--prag 0.95] [--x 60] [--shuffle-seed 42]"
    exit 1
fi
PRAG="${PRAG:-$PRAG_DEFAULT}"
X="${X:-$X_DEFAULT}"
SHUFFLE_SEED="${SHUFFLE_SEED:-$SHUFFLE_SEED_DEFAULT}"

TMP=$(mktemp); trap 'rm -f "$TMP"' EXIT

okolina() {
    echo ">>> OKOLINA ($1): $(date)"
    echo "    bb_03 procesa vec aktivno: $(pgrep -fc bb_03_prevod.py || :)"
    echo "    load average:$(uptime | sed 's/.*load average://')"
    echo "    RAM: $(free -m | awk '/^Mem:/{print $7" MB dostupno od "$2" MB"}')"
}

citaj_zbir()  { awk '/BILANS jezika:/{for(i=1;i<=NF;i++)if($i~/^zbir=/){split($i,a,"=");s+=a[2]}}END{printf "%.4f", s+0}' "$1"; }
citaj_n()     { awk '/BILANS jezika:/{for(i=1;i<=NF;i++)if($i~/^n=/){split($i,a,"=");s+=a[2]}}END{print s+0}' "$1"; }
citaj_ispod() { awk '/BILANS jezika:/{s+=$NF}END{print s+0}' "$1"; }
pct_iznad() { awk -v i="$1" -v n="$2" 'BEGIN{ printf "%d", (n>0 ? 100*(n-i)/n : 100) }'; }

okolina start
echo ">>> PARAMETRI: knjiga=$KNJIGA jezici='$JEZICI' opseg=$OD-$DO prag=$PRAG shuffle-seed=$SHUFFLE_SEED"
echo ">>> PLAN (s177 sonda redoslijeda, k15=mesano-prvo): root=$ROOT_MODEL@$ROOT_TEMP | blok A fiksno 2 kruga x [12,24]x[mesano,original] | X=$X% | blok B fiksno 1 krug x [14,26]x[mesano,original]"

# ─────────────────────────── ROOT ───────────────────────────
echo ">>> KORAK 1: root ($ROOT_MODEL @ $ROOT_TEMP) — bez gatea, bez mesanja"
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

# $1=faza  $2=runda  $3=redoslijed  $4=oznaka
izvrsi_fazu() {
    local FAZA="$1" RUNDA="$2" REDOSLIJED="$3" OZNAKA="$4"
    echo ">>> $OZNAKA | FAZA $FAZA runda=$RUNDA redoslijed=$REDOSLIJED (gated<$PRAG)"
    bash run_faza.sh --faza "$FAZA" --knjiga "$KNJIGA" --jezici "$JEZICI" \
        --od "$OD" --do "$DO" --runda "$RUNDA" --prag "$PRAG" \
        --redoslijed "$REDOSLIJED" --shuffle-seed "$SHUFFLE_SEED" 2>&1 | tee "$TMP"

    local Z N I D
    Z=$(citaj_zbir "$TMP"); N=$(citaj_n "$TMP"); I=$(citaj_ispod "$TMP")
    D=$((ISPOD - I))
    awk -v z="$Z" -v p="$ZBIR_PRETHODNI" -v n="$N" -v o="$OZNAKA" -v f="$FAZA" -v r="$RUNDA" -v rd="$REDOSLIJED" -v i="$I" -v d="$D" 'BEGIN{
        dz=z-p;
        printf ">>> %s FAZA %s runda=%s (%s): ispod praga %s (prebacila %+d) | zbir %.4f/%s dodala %+.4f | %+.3f%% n\n",
               o, f, r, rd, i, d, z, n, dz, (n>0?100*dz/n:0) }'
    ZBIR_PRETHODNI=$Z; NTOT=$N; ISPOD=$I
}

# ─────────────────────────── BLOK A — fiksno 2 kruga, mesano PRVO ───────────────────────────
for K in 1 2; do
    R_ORIG=$((2*K - 1))
    R_MES=$((2*K))
    echo ">>> ══════ BLOK A KRUG $K/2 (runda original=$R_ORIG, runda mesano=$R_MES) — ispod praga na ulazu: $ISPOD"
    izvrsi_fazu 12 "$R_MES"  mesano   "BLOK A KRUG $K"
    izvrsi_fazu 12 "$R_ORIG" original "BLOK A KRUG $K"
    izvrsi_fazu 24 "$R_MES"  mesano   "BLOK A KRUG $K"
    izvrsi_fazu 24 "$R_ORIG" original "BLOK A KRUG $K"
    echo ">>> BILANS blok A krug $K: ispod praga sada $ISPOD | iznad $(pct_iznad "$ISPOD" "$NTOT")%"
done

PCT=$(pct_iznad "$ISPOD" "$NTOT")
echo ">>> BILANS BLOK A: 2/2 kruga (fiksno, bez ranog izlaska) | iznad praga: $PCT% (prag odluke X=$X%)"

# ─────────────────────── USLOV -> BLOK B ───────────────────────
B_POKRENUT=0
if [ "$PCT" -lt "$X" ]; then
    echo ">>> ODLUKA: $PCT% < $X% -> pokrecem BLOK B (glm-5.2, skupi model, fiksno 1 krug, mesano prvo)"
    B_POKRENUT=1
    izvrsi_fazu 14 2 mesano   "BLOK B"
    izvrsi_fazu 14 1 original "BLOK B"
    izvrsi_fazu 26 2 mesano   "BLOK B"
    izvrsi_fazu 26 1 original "BLOK B"
    echo ">>> BILANS BLOK B: 1/1 krug (fiksno)"
else
    echo ">>> ODLUKA: $PCT% >= $X% -> BLOK B se PRESKACE (glm nije pozvan, ustedjeno 4 faze)"
fi

FAZA_UKUPNO=$((1 + 8 + B_POKRENUT * 4))
if [ "$B_POKRENUT" -eq 1 ]; then B_OZNAKA="1/1 (fiksno)"; else B_OZNAKA="0/1 (nije-pokrenut)"; fi
echo ">>> SAZETAK: blok A=2/2 (fiksno) | blok B=$B_OZNAKA | X=$X%"
echo ">>> SAZETAK: izvrseno faza ukupno=$FAZA_UKUPNO (ukljucujuci root)"
echo ">>> SAZETAK: ispod praga na kraju=$ISPOD | iznad=$(pct_iznad "$ISPOD" "$NTOT")% | zbir=$ZBIR_PRETHODNI/$NTOT"
okolina kraj
echo ">>> ZAVRSENO (prag=$PRAG, X=$X, shuffle-seed=$SHUFFLE_SEED): $(date)"
