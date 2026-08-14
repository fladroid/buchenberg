#!/bin/bash
# run_prazno.sh — report "prazno svuda": pozicije bez pobjednika ni na jednom
# jeziku, i pozicije sa bar jednim pobjednikom na bilo kom jeziku. Po knjizi.
#
# Upotreba:
#   ./run_prazno.sh                 # sve knjige
#   ./run_prazno.sh --knjiga 12     # samo knjiga 12

cd "$(dirname "$0")" || exit 1
venv/bin/python src/bb_prazno_svuda.py "$@"
