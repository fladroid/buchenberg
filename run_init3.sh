#!/bin/bash
# run_init3.sh — pokretanje init skripte 3x serijalno
# Koristiti samo sa stohastičkim modelima (nllb_t05, temp>0)

cd /home/balsam/buchenberg

TEST_ID=$(python3 -c "import yaml; c=yaml.safe_load(open('tests/pivot.yaml')); print(c['test_id'])")
LOG="logs/${TEST_ID}_init3.log"

echo "Test: $TEST_ID" | tee $LOG
echo "Start: $(date)" | tee -a $LOG

echo "=== Init run 1/3 ===" | tee -a $LOG
venv/bin/python src/run_pivot_init.py 2>&1 | tee -a $LOG

echo "=== Init run 2/3 ===" | tee -a $LOG
venv/bin/python src/run_pivot_init.py 2>&1 | tee -a $LOG

echo "=== Init run 3/3 ===" | tee -a $LOG
venv/bin/python src/run_pivot_init.py 2>&1 | tee -a $LOG

echo "=== Završeno: $(date) ===" | tee -a $LOG
