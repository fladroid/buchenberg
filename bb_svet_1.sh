#!/bin/bash
# bb_svet_1.sh — deklarise svijet 1: puna 3-way root (mistral + nllb + glm), temp 0.8/0.1/0.0.
set -e
cd "$(dirname "$0")"
venv/bin/python src/bb_deklarisi_svet.py --faza 1 \
    --modeli "mistral-large-3:675b,nllb-600M,glm-5.2" \
    --temperature "0.8,0.1,0.0"
