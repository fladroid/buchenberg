#!/bin/bash
# run_ousage.sh — Ollama Cloud potrosnja (session + sedmicno), sa deltom
# od poslednje provjere. Vidi src/bb_ollama_usage.py za napomenu o
# nezvanicnom endpointu.
#
# Upotreba:
#   ./run_ousage.sh              # pun izvjestaj
#   ./run_ousage.sh --kratko     # jedna linija

cd "$(dirname "$0")" || exit 1
venv/bin/python src/bb_ollama_usage.py "$@"
