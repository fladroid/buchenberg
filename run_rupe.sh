#!/bin/bash
# run_rupe.sh — report rupa pobjednika po (knjiga, jezik), kompaktni intervali.
#
# Upotreba:
#   ./run_rupe.sh                     # sve knjige, svi jezici
#   ./run_rupe.sh --knjiga 12         # samo knjiga 12, svi jezici
#   ./run_rupe.sh --knjiga 12 --jezik ja

cd "$(dirname "$0")" || exit 1
venv/bin/python src/bb_rupe_pobjednika.py "$@"
