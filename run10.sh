#!/bin/bash
# Buchenberg · run10.sh
# Inicijalno punjenje baze — kreiranje tabela, truncate, insert knjiga, parsiranje.
# Pokretanje: nohup time bash run10.sh > logs/run10.log 2>&1 &

set -e

cd /home/balsam/buchenberg
mkdir -p logs

VENV=./venv/bin/python
LOG=logs/run10.log

echo "======================================" | tee -a $LOG
echo "run10.sh START: $(date)"               | tee -a $LOG
echo "======================================" | tee -a $LOG

echo "[$(date)] step1_create_tables START" | tee -a $LOG
$VENV src/step1_create_tables.py >> $LOG 2>&1
echo "[$(date)] step1_create_tables DONE"  | tee -a $LOG

echo "[$(date)] step2_truncate START" | tee -a $LOG
$VENV src/step2_truncate.py >> $LOG 2>&1
echo "[$(date)] step2_truncate DONE"  | tee -a $LOG

echo "[$(date)] step3_insert_book START" | tee -a $LOG
$VENV src/step3_insert_book.py >> $LOG 2>&1
echo "[$(date)] step3_insert_book DONE"  | tee -a $LOG

echo "[$(date)] step4_parse_sentences START" | tee -a $LOG
$VENV src/step4_parse_sentences.py >> $LOG 2>&1
echo "[$(date)] step4_parse_sentences DONE"  | tee -a $LOG

echo "======================================" | tee -a $LOG
echo "run10.sh DONE: $(date)"                | tee -a $LOG
echo "======================================" | tee -a $LOG
