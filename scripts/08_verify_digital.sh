#!/bin/zsh
# Resumable strict verification of board digital experts (Codex, high effort)
P="$(cd "$(dirname "$0")/.." && pwd)"
CODEX=codex
run_batch() {
  b=$1; out="$P/data/gov_verify/rows_$b.csv"; todo="$P/data/gov_verify/todo_$b.txt"
  touch "$out"
  grep -vxF -f <(cut -d';' -f1,2 "$out" | tr ';' '\t') "$P/data/gov_verify/batch_$b.txt" | grep . > "$todo"
  [ -s "$todo" ] || { echo "batch $b complete"; return; }
  $CODEX exec --skip-git-repo-check -s workspace-write -C "$P" -m gpt-6-astra -c model_reasoning_effort=high "Строгая проверка: является ли член надзорного органа компании (совет директоров / Rada Nadzorcza / Supervisory Board) ЦИФРОВЫМ ЭКСПЕРТОМ по его биографии в годовом отчёте.
Список: data/gov_verify/todo_$b.txt — строки '<файл><TAB><имя>'. Текст отчёта: data/text/<файл>. Ищи биографию через grep по фамилии (смотри ~40 строк контекста: grep -n -A40). Не читай файл целиком.
ЦИФРОВОЙ ЭКСПЕРТ = в биографии ПРЯМО указан опыт: работа CIO/CTO/CDO/директором по IT/цифровизации/данным/кибербезопасности; работа в IT-, софтверной, телеком- или цифровой компании на технической или руководящей ИТ-роли; образование по информатике/IT/компьютерным наукам/data science; руководство цифровой трансформацией или IT-проектами. НЕ считается: юрист, финансист, экономист, общий менеджер без явного IT; членство в совете IT-компании без технической роли; упоминание «цифровизации» только как темы компании.
ПОСЛЕ КАЖДОГО человека сразу дописывай строку в data/gov_verify/rows_$b.csv (echo >>), разделитель ; , поля:
file;person;verdict(yes/no/no_bio/not_board);role_in_company(председатель/член совета/член правления/NA);evidence(дословная фраза из биографии ≤200 знаков без ; — обязательно для yes)
Если биографию не нашёл — verdict=no_bio. Если человек не член надзорного органа (например, член правления) — not_board. Ничего не выдумывай. Другие файлы не изменяй." < /dev/null > "$P/data/gov_verify/log_$b.txt" 2>&1
  echo "batch $b: $(grep -c . "$out") rows"
}
for round in 1 2; do
  for b in ${=BATCHES:-0 1 2 3 4 5}; do run_batch $b & done; wait
done
