#!/bin/bash
# Buchenberg · run30.sh
# GA runner orchestrator.
#
# Pokretanje:
#   # Jedna rečenica, jedan jezik:
#   bash run30.sh --sentence_id 5 --lang it
#
#   # Raspon rečenica, više jezika:
#   bash run30.sh --sent_from 1 --sent_to 5 --lang it fr de
#
#   # Sa GA parametrima:
#   bash run30.sh --sent_from 1 --sent_to 3 --lang it --max_gen 10

set -e
source /home/balsam/buchenberg/buch_env.sh

echo "======================================" | tee -a $BUCH_LOG/run30.log
echo "run30.sh START: $(date)"               | tee -a $BUCH_LOG/run30.log
echo "Args: $@"                              | tee -a $BUCH_LOG/run30.log
echo "======================================" | tee -a $BUCH_LOG/run30.log

time $BUCH_VENV $BUCH_SRC/run_ga.py "$@" 2>&1 | tee -a $BUCH_LOG/run30.log

echo "======================================" | tee -a $BUCH_LOG/run30.log
echo "run30.sh END: $(date)"                 | tee -a $BUCH_LOG/run30.log
echo "======================================" | tee -a $BUCH_LOG/run30.log
