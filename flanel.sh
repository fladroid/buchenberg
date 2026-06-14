#!/usr/bin/bash
#
set -x 

nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 17 --od 1 --do 200 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici af bs es fr nl  > /home/balsam/buchenberg/logs/k17_afbsesfrnl_nllb_200.log 2>&1

nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 17 --od 1 --do 200 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici pt ro sl bg mk  > /home/balsam/buchenberg/logs/k17_ptroslbgmk_nllb_200.log 2>&1

nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 8 --od 1 --do 200 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici af bs es fr nl  > /home/balsam/buchenberg/logs/k8_afbsesfrnl_nllb_200.log 2>&1

nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 8 --od 1 --do 200 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici pt ro sl bg mk  > /home/balsam/buchenberg/logs/k8_ptroslbgmk_nllb_200.log 2>&1

nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 5 --od 1 --do 200 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici af bs es fr nl  > /home/balsam/buchenberg/logs/k5_afbsesfrnl_nllb_200.log 2>&1

nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 5 --od 1 --do 200 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici pt ro sl bg mk  > /home/balsam/buchenberg/logs/k5_ptroslbgmk_nllb_200.log 2>&1

##ff##nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 18 --od 1 --do 600 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici it de hr sr  > /home/balsam/buchenberg/logs/k18_itdehrsr_nllb_600.log 2>&1
##ff##
##ff##nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 19 --od 1 --do 600 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici it de hr sr  > /home/balsam/buchenberg/logs/k19_itdehrsr_nllb_600.log 2>&1
##ff##
##ff##nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 20 --od 1 --do 600 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici it de hr sr  > /home/balsam/buchenberg/logs/k20_itdehrsr_nllb_600.log 2>&1
##ff##
##ff##nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 21 --od 1 --do 600 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici it de hr sr  > /home/balsam/buchenberg/logs/k21_itdehrsr_nllb_600.log 2>&1
##ff##
##ff##
##ff##
##ff##
##ff##
##ff##nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 12 --od 1 --do 700 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici it de hr sr  > /home/balsam/buchenberg/logs/k12_itdehrsr_nllb_700.log 2>&1
##ff##
##ff##nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 17 --od 1 --do 700 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici it de hr sr  > /home/balsam/buchenberg/logs/k17_itdehrsr_nllb_700.log 2>&1
##ff##
##ff##nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 18 --od 1 --do 700 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici it de hr sr  > /home/balsam/buchenberg/logs/k18_itdehrsr_nllb_700.log 2>&1
##ff##
##ff##nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 19 --od 1 --do 700 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici it de hr sr  > /home/balsam/buchenberg/logs/k19_itdehrsr_nllb_700.log 2>&1
##ff##
##ff##nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 20 --od 1 --do 700 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici it de hr sr  > /home/balsam/buchenberg/logs/k20_itdehrsr_nllb_700.log 2>&1
##ff##
##ff##nohup time /home/balsam/buchenberg/venv/bin/python /home/balsam/buchenberg/src/bb_03_prevod.py   --knjiga 21 --od 1 --do 700 --model "nllb-600M" --temp 0.0   --embedder "multilingual-e5-large" --jezici it de hr sr  > /home/balsam/buchenberg/logs/k21_itdehrsr_nllb_700.log 2>&1
