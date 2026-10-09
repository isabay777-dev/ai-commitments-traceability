#!/bin/zsh
# Generic resumable Codex runner: one output row per ID, appended immediately.
# Usage: NAME=x MODEL=gpt-6-astra EFFORT=high IDS=file.txt DIR=article1/x PROMPT=prompt.txt NB=4 scripts/29_codex_rows.sh
# PROMPT may use {TODO} and {OUT}; rows must start with the ID followed by ';'.
P="$(cd "$(dirname "$0")/.." && pwd)"; cd "$P"; CODEX=codex
mkdir -p "$DIR"
for b in $(seq 0 $((NB-1))); do awk -v b=$b -v nb=$NB 'NF && (NR-1)%nb==b' "$IDS" > "$DIR/batch_$b.txt"; done
run_batch() {
  b=$1; out="$DIR/rows_$b.csv"; todo="$DIR/todo_$b.txt"; touch "$out"
  grep -vxF -f <(cut -d';' -f1 "$out" | sort -u) "$DIR/batch_$b.txt" | grep . > "$todo"
  [ -s "$todo" ] || { echo "$NAME batch $b complete"; return; }
  prompt="$(sed -e "s#{TODO}#$todo#g" -e "s#{OUT}#$out#g" "$PROMPT")"
  $CODEX exec --skip-git-repo-check -s workspace-write -C "$P" -m "$MODEL" -c model_reasoning_effort="$EFFORT" "$prompt" < /dev/null > "$DIR/log_$b.txt" 2>&1
  echo "$NAME batch $b: $(cut -d';' -f1 "$out" | sort -u | grep -c .) ids"
}
for round in 1 2 3; do for b in $(seq 0 $((NB-1))); do run_batch $b & done; wait; done
cat "$DIR"/rows_*.csv > "$DIR/all.csv"; echo "$NAME TOTAL $(cut -d';' -f1 "$DIR/all.csv" | sort -u | grep -c .)"
