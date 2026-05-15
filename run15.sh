#!/bin/bash
# Buchenberg · run15.sh
# Sentiment analiza + NER — popunjava sentences i named_entities tabele.
# Pokretanje: nohup time bash run15.sh > logs/run15.log 2>&1 &

set -e

source /home/balsam/buchenberg/buch_env.sh

echo "======================================" | tee -a $BUCH_LOG/run15.log
echo "run15.sh START: $(date)"               | tee -a $BUCH_LOG/run15.log
echo "======================================" | tee -a $BUCH_LOG/run15.log

echo "[$(date)] step5_sentiment_ner START" | tee -a $BUCH_LOG/run15.log
$BUCH_VENV $BUCH_SRC/step5_sentiment_ner.py 2>&1 | tee -a $BUCH_LOG/run15.log
echo "[$(date)] step5_sentiment_ner DONE"  | tee -a $BUCH_LOG/run15.log

echo "======================================" | tee -a $BUCH_LOG/run15.log
echo "run15.sh END: $(date)"                 | tee -a $BUCH_LOG/run15.log
echo "======================================" | tee -a $BUCH_LOG/run15.log
