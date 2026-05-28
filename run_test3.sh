#!/bin/bash
# run_test3.sh — pokretanje run20.sh 3x serijalno
# Koristiti samo sa stohastičkim metodama (claude_t05, gemma_t05, nllb_t05...)

cd /home/balsam/buchenberg

# Prosljeđuje sve argumente run20.sh
ARGS="$@"
TEST_ID=""

# Izvuci test_id iz argumenata
for i in "$@"; do
    if [ "$prev" = "--test_id" ]; then
        TEST_ID=$i
    fi
    prev=$i
done

if [ -z "$TEST_ID" ]; then
    echo "ERROR: --test_id nije proslijeđen"
    exit 1
fi

LOG="logs/${TEST_ID}_init3.log"

echo "Test: $TEST_ID" | tee $LOG
echo "Start: $(date)" | tee -a $LOG

echo "=== Run 1/3 ===" | tee -a $LOG
bash run20.sh $ARGS 2>&1 | tee -a $LOG

echo "=== Run 2/3 ===" | tee -a $LOG
bash run20.sh $ARGS 2>&1 | tee -a $LOG

echo "=== Run 3/3 ===" | tee -a $LOG
bash run20.sh $ARGS 2>&1 | tee -a $LOG

echo "=== Završeno: $(date) ===" | tee -a $LOG
