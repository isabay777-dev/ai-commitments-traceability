#!/bin/zsh
# Resumable Codex (high) semantic verification of promise fulfilment
P="$(cd "$(dirname "$0")/.." && pwd)"; cd "$P"; CODEX=codex
run_batch() {
  b=$1; out="data/promise_check/rows_$b.csv"; todo="data/promise_check/todo_$b.txt"; touch "$out"
  grep -vxF -f <(cut -d';' -f1 "$out") "data/promise_check/batch_$b.txt" | grep . > "$todo"
  [ -s "$todo" ] || { echo "batch $b complete"; return; }
  $CODEX exec --skip-git-repo-check -s workspace-write -C "$P" -m gpt-6-astra -c model_reasoning_effort=high "Ты проверяешь, выполнили ли компании свои обещания об искусственном интеллекте. Список ID: $todo. Для каждого ID прочитай data/promise_check/packets/<ID>.txt: там фрагмент годового отчёта с обещанием (год t) и все фрагменты про ИИ той же компании из более поздних отчётов (тексты могут быть с перемешанными колонками PDF).
Реши по смыслу, исполнено ли ИМЕННО ЭТО обещание (то же применение ИИ, тот же процесс или продукт), а не любое другое упоминание ИИ:
- fulfilled — в более позднем отчёте прямо сказано, что обещанное внедрено, запущено, используется или дало результат;
- partial — есть продвижение (пилот, частичный запуск, внедрение в одном подразделении), но не полное выполнение;
- not_fulfilled — тема упоминается позже, но без признаков внедрения (снова план, отложено, отменено);
- dropped — обещанная тема в поздних фрагментах больше не появляется;
- not_a_promise — исходный фрагмент на деле не обещание компании внедрить ИИ (тренд, риск, пересказ закона, обучение кадров).
После КАЖДОГО ID сразу дописывай строку в $out (echo >>), разделитель ; :
promise_id;verdict;evidence_year;promise_summary(≤80 знаков);evidence(дословная фраза ≤160 знаков из позднего фрагмента для fulfilled/partial/not_fulfilled, иначе NA)
Без ; и переносов внутри полей. Не выдумывай. Другие файлы не изменяй." < /dev/null > "data/promise_check/log_$b.txt" 2>&1
  echo "batch $b: $(grep -c . "$out") rows"
}
for round in 1 2; do for b in 0 1 2 3 4 5; do run_batch $b & done; wait; done
cat data/promise_check/rows_*.csv > data/promise_check/promise_verdicts.csv; echo "TOTAL $(grep -c . data/promise_check/promise_verdicts.csv)"
