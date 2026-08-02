#!/bin/bash
# bb_svet_2.sh — deklarise svijet 2: suzen root (mistral + nllb, BEZ glm), temp 0.8/0.1/0.0.
set -e
cd "$(dirname "$0")"
venv/bin/python src/bb_deklarisi_svet.py --faza 1 \
    --modeli "mistral-large-3:675b,nllb-600M" \
    --temperature "0.8,0.1,0.0"
