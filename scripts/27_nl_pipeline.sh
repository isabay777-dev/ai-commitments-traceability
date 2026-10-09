#!/bin/zsh
# NL promise firm-years: governance -> strict expert verification + controls (Codex high)
S="$(cd "$(dirname "$0")" && pwd)"; cd "$S/.."
BATCHES="16 17 18 19" scripts/07_run_gov.sh
python3 scripts/26_nl_verify_prep.py
BATCHES="12 13 14 15" scripts/08_verify_digital.sh &
BATCHES="14 15 16 17" scripts/10_run_controls.sh &
wait; echo NL PIPELINE DONE
