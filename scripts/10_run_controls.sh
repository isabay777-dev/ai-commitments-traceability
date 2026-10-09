#!/bin/zsh
# Resumable Codex extraction of firm size and industry controls (KZ, PL)
P="$(cd "$(dirname "$0")/.." && pwd)"
CODEX=codex
run_batch() {
  b=$1; out="$P/data/controls/rows_$b.csv"; todo="$P/data/controls/todo_$b.txt"
  touch "$out"
  grep -vxF -f <(cut -d';' -f1 "$out") "$P/data/controls/batch_$b.txt" | grep . > "$todo"
  [ -s "$todo" ] || { echo "batch $b complete"; return; }
  $CODEX exec --skip-git-repo-check -s workspace-write -C "$P" -m gpt-6-astra -c model_reasoning_effort=medium "Извлеки контрольные переменные из годовых отчётов казахстанских (KZ), польских (PL) и нидерландских (NL) компаний. Список: data/controls/todo_$b.txt. Текст: data/text/<файл> (имя = <страна>_<компания>_<год>.txt). Используй grep по ключевым словам (total assets / итого активы / aktywa razem / suma bilansowa, revenue / выручка / доход от реализации / przychody, employees / численность работников / zatrudnienie). Не читай файл целиком. Ничего не выдумывай: нет данных — NA.
ПОСЛЕ КАЖДОГО файла сразу дописывай строку в data/controls/rows_$b.csv (echo >>), разделитель ; :
file;currency;unit(как в отчёте: thousand/million/full);total_assets;revenue;net_profit;employees;consolidated(yes/no/NA);nace_section(A–U, одна буква по основному виду деятельности);sector_label(коротко по-английски, напр. banking, insurance, telecom, oil&gas, mining, utilities, retail, IT/software, construction, manufacturing, transport, real estate, other finance);listed_since_year(NA если нет);evidence(≤120 знаков без ; — откуда взяты активы)
Значения — числа без пробелов и разделителей тысяч, точка как десятичный разделитель; отчётный год — тот, что в имени файла (не предыдущий). Для банков revenue = операционный доход или процентный доход, укажи в evidence. Другие файлы не изменяй." < /dev/null > "$P/data/controls/log_$b.txt" 2>&1
  echo "batch $b: $(grep -c . "$out") rows"
}
for round in 1 2; do for b in ${=BATCHES:-0 1 2 3 4 5}; do run_batch $b & done; wait; done
