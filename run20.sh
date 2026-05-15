#!/bin/bash
# Buchenberg · run20.sh
# Test runner orchestrator.
# Pokretanje:
#   # Registracija (prvi put):
#   bash run20.sh --test_id test_001 --book hound_of_the_baskervilles \
#     --sent_from 1 --sent_to 20 --langs sr --methods nllb gemma
#
#   # Ponovni run:
#   bash run20.sh --test_id test_001

set -e
source /home/balsam/buchenberg/buch_env.sh

echo "======================================" | tee -a $BUCH_LOG/run20.log
echo "run20.sh START: $(date)"               | tee -a $BUCH_LOG/run20.log
echo "Args: $@"                              | tee -a $BUCH_LOG/run20.log
echo "======================================" | tee -a $BUCH_LOG/run20.log

$BUCH_VENV $BUCH_SRC/run_test.py "$@" 2>&1 | tee -a $BUCH_LOG/run20.log

echo "======================================" | tee -a $BUCH_LOG/run20.log
echo "run20.sh END: $(date)"                 | tee -a $BUCH_LOG/run20.log
echo "======================================" | tee -a $BUCH_LOG/run20.log
