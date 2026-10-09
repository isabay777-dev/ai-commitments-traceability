#!/bin/zsh
# Article 1: history (astra) + consilium stage 1: blind coder (sol), fact-checker (luna), skeptic (astra)
S="$(cd "$(dirname "$0")" && pwd)"; cd "$S/.."
NAME=history  MODEL=gpt-6-astra EFFORT=high IDS=article1/promise_ids.txt          DIR=article1/history            PROMPT=article1/p_history.txt   NB=5 scripts/29_codex_rows.sh &
NAME=blind    MODEL=gpt-6-sol   EFFORT=high IDS=article1/promise_ids.txt          DIR=article1/consilium/blind    PROMPT=article1/p_blind.txt     NB=3 scripts/29_codex_rows.sh &
NAME=factchk  MODEL=gpt-6-luna  EFFORT=high IDS=article1/promise_ids.txt          DIR=article1/consilium/factcheck PROMPT=article1/p_factcheck.txt NB=3 scripts/29_codex_rows.sh &
NAME=skeptic  MODEL=gpt-6-astra EFFORT=high IDS=article1/promise_ids_positive.txt DIR=article1/consilium/skeptic  PROMPT=article1/p_skeptic.txt   NB=3 scripts/29_codex_rows.sh &
wait; echo STAGE1 DONE
