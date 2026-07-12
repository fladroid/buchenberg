#!/usr/bin/env bash
# run_ner.sh — proizvodni ulaz za NER lanac (s130)
#   bb_09 (classic) → bb_10 (llm) → bb_10c (docre)
# Redoslijed nosi značenje: svaki sloj je ulaz sljedećem.
# --force je svojstvo PROLAZA, ne faze: ko forsira temelj, forsira i sve iznad.
set -euo pipefail

KNJIGA="all"
FORCE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --knjiga) KNJIGA="$2"; shift 2 ;;
    --force)  FORCE="--force"; shift ;;
    *) echo "Nepoznat argument: $1"; exit 1 ;;
  esac
done

cd /home/balsam/buchenberg
PY="venv/bin/python"

echo "═══ run_ner.sh — knjiga=$KNJIGA ${FORCE:+(force)} ═══"

echo "── 1/3 bb_09 (classic) ──"
PYTHONUNBUFFERED=1 $PY src/bb_09_ner.py     --knjiga "$KNJIGA" $FORCE

echo "── 2/3 bb_10 (llm) ──"
PYTHONUNBUFFERED=1 $PY src/bb_10_ner_llm.py --knjiga "$KNJIGA" $FORCE

echo "── 3/3 bb_10c (docre) ──"
PYTHONUNBUFFERED=1 $PY src/bb_10c_docre.py  --knjiga "$KNJIGA" $FORCE

echo "═══ run_ner.sh gotov ═══"
