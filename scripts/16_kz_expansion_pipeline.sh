#!/bin/zsh
# Governance -> strict verification -> controls for KZ expansion docs
S="$(cd "$(dirname "$0")" && pwd)"; cd "$S/.."
python3 scripts/14_kz_expansion_prep.py
BATCHES="8 9 10 11 12 13 14 15" scripts/07_run_gov.sh
python3 scripts/15_kz_verify_prep.py
BATCHES="6 7 8 9 10 11" scripts/08_verify_digital.sh &
BATCHES="6 7 8 9 10 11 12 13" scripts/10_run_controls.sh &
wait; echo PIPELINE DONE
