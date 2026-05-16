#!/bin/bash
# RAM i swap monitor — loguje svake 5 sekundi dok postoji PID
# Pokretanje: bash src/ram_monitor.sh <PID> <logfile>

PID=$1
LOG=$2

echo "timestamp,ram_used_mb,swap_used_mb,ram_pct" > $LOG
while kill -0 $PID 2>/dev/null; do
    RAM=$(free -m | awk 'NR==2{print $3}')
    SWAP=$(free -m | awk 'NR==3{print $3}')
    RAM_TOTAL=$(free -m | awk 'NR==2{print $2}')
    PCT=$(echo "scale=1; $RAM*100/$RAM_TOTAL" | bc)
    echo "$(date +%H:%M:%S),$RAM,$SWAP,$PCT" >> $LOG
    sleep 5
done
echo "Monitor završen."
