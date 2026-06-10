#!/usr/bin/bash
#
set -x 

PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_03_prevod.py \
  --knjiga 1 --od 3701 --do 3900 --model "gemma3:12b" --temp 0.8 0.1 \
  --embedder "multilingual-e5-large" --jezici hr \
  > logs/hound_hr_s3701_s3900_gemma3.log 2>&1
echo "PID: $!"

PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_03_prevod.py \
  --knjiga 1 --od 3701 --do 3900 --model "ministral-3:14b" --temp 0.8 0.1 \
  --embedder "multilingual-e5-large" --jezici hr \
  > logs/hound_hr_s3701_s3900_ministral.log 2>&1
echo "PID: $!"


PYTHONUNBUFFERED=1 nohup time venv/bin/python src/bb_08_sudija.py \
  --knjiga 1 --od 3701 --do 3900 --jezici hr \
  > logs/hound_hr_s3701_s3900_sudija.log 2>&1 
echo "PID: $!"

venv/bin/python src/bb_04_pobjednik.py --knjiga 1 --od 3701 --do 3900 --jezici hr

venv/bin/python src/bb_web_export.py
