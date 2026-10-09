#!/bin/zsh
# Resumable Codex governance extraction: each batch appends rows to data/gov/rows_<b>.csv
P="$(cd "$(dirname "$0")/.." && pwd)"
CODEX=codex
run_batch() {
  b=$1
  todo="$P/data/gov/todo_$b.txt"
  touch "$P/data/gov/rows_$b.csv"
  grep -vxF -f <(cut -d';' -f1 "$P/data/gov/rows_$b.csv") "$P/data/gov/batch_$b.txt" | grep . > "$todo"
  [ -s "$todo" ] || { echo "batch $b complete"; return; }
  $CODEX exec --skip-git-repo-check -s workspace-write -C "$P" -m gpt-6-astra -c model_reasoning_effort=medium "Извлеки переменные корпоративного управления из фрагментов годовых отчётов казахстанских (KZ), польских (PL) и нидерландских (NL) компаний. Список файлов: data/gov/todo_$b.txt. Каждый файл лежит в data/gov_snippets/<имя>; полный текст, если нужно, в data/text/<имя> (используй grep, не читай целиком). Имя = <страна>_<компания>_<год>.txt. Ничего не выдумывать: нет данных — NA.
ВАЖНО: после обработки КАЖДОГО файла сразу дописывай одну строку в data/gov/rows_$b.csv (echo ... >> файл), без заголовка. Разделитель ;. Поля по порядку:
file;board_structure(one-tier/two-tier/NA);board_name;board_size;n_independent;n_women_board;n_foreign_board;n_digital_expert_board;digital_expert_names;bios_available(yes/partial/no);has_cdo_cto_cio_exec(yes/no/NA);state_owned_major(yes/no/NA);largest_shareholder;largest_shareholder_pct;foreign_parent(yes/no/NA);ai_or_digital_committee(yes/no/NA);evidence(≤150 знаков, без символа ;)
Правила: состав надзорного органа (совет директоров / Rada Nadzorcza / Supervisory Board) на конец отчётного года. n_digital_expert_board — члены надзорного органа с опытом по биографии в IT, цифровизации, технологиях, данных, кибербезопасности, телеком или бывшие CIO/CTO/CDO; общая управленческая биография не считается; без биографий — NA. has_cdo_cto_cio_exec — есть ли в правлении/Zarząd/management board ответственный за IT/цифровизацию/технологии/данные. Внутри полей не использовать ; и переносы строк. Другие файлы не изменять." < /dev/null > "$P/data/gov/log_$b.txt" 2>&1
  echo "batch $b: $(wc -l < "$P/data/gov/rows_$b.csv") rows"
}
for round in 1 2; do
  for b in ${=BATCHES:-0 1 2 3 4 5 6 7}; do run_batch $b & done; wait
done
