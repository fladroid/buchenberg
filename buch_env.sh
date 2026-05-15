#!/bin/bash
# Buchenberg · buch_env.sh
# Sourcuj na početku svakog run skripte: source buch_env.sh

# Putanje
export BUCH_HOME=/home/balsam/buchenberg
export BUCH_SRC=$BUCH_HOME/src
export BUCH_LOG=$BUCH_HOME/logs
export BUCH_BOOKS=$BUCH_HOME/books
export BUCH_VENV=$BUCH_HOME/venv/bin/python

# .env (secrets)
set -a
source $BUCH_HOME/.env
set +a

# Kreiranje log direktorija ako ne postoji
mkdir -p $BUCH_LOG
