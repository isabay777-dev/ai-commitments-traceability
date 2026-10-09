#!/bin/zsh
# Resumable Codex coding of AI fragments. Usage: IN=data/coding/pilot_fragments.tsv OUT=data/coding/pilot_coded.csv EFFORT=high scripts/20_run_coding.sh
P="$(cd "$(dirname "$0")/.." && pwd)"; cd "$P"
CODEX=codex
NB=${NB:-4}
python3 - "$IN" "$NB" <<'PY'
import csv, sys
inp, nb = sys.argv[1], int(sys.argv[2])
rows = list(csv.DictReader(open(inp), delimiter="\t"))
for b in range(nb):
    with open(f"data/coding/_batch_{b}.tsv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys(), delimiter="\t"); w.writeheader(); w.writerows(rows[b::nb])
PY
run_batch() {
  b=$1; out="${OUT%.csv}_$b.csv"; touch "$out"
  python3 - "$b" "$out" <<'PY'
import csv, sys
b, out = sys.argv[1], sys.argv[2]
done = {l.split(";")[0] for l in open(out) if l.strip()}
rows = [r for r in csv.DictReader(open(f"data/coding/_batch_{b}.tsv"), delimiter="\t") if r["fragment_id"] not in done]
with open(f"data/coding/_todo_{b}.tsv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["fragment_id","country","year","text"], delimiter="\t", extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print(len(rows))
PY
  [ "$(wc -l < data/coding/_todo_$b.tsv)" -le 1 ] && { echo "batch $b complete"; return; }
  $CODEX exec --skip-git-repo-check -s workspace-write -C "$P" -m gpt-6-astra -c model_reasoning_effort=${EFFORT:-high} "Ты кодируешь фрагменты годовых отчётов компаний (Казахстан, Польша, Нидерланды) об искусственном интеллекте. Схема — раздел v0.2 файла CODING_SCHEME.md (прочитай его; разделы v0.1 — определения topic и specificity). Входной файл: data/coding/_todo_$b.tsv (TSV: fragment_id, country, year, text; текст — окно ±350 знаков вокруг слова про ИИ, колонки PDF могут быть перемешаны — интерпретируй по смыслу, а если смысл восстановить нельзя, ставь unclear/NA).
После КАЖДОГО фрагмента сразу дописывай одну строку в $out (echo >>), без заголовка, разделитель ; :
fragment_id;is_ai;topic;specificity;status;promise;use_case;source;note
Строго по схеме; не выдумывай того, чего нет в тексте; в полях не использовать ; и переносы строк. Другие файлы не изменяй." < /dev/null > "data/coding/log_${OUT:t:r}_$b.txt" 2>&1
  echo "batch $b: $(grep -c . "$out") rows"
}
for round in 1 2; do for b in $(seq 0 $((NB-1))); do run_batch $b & done; wait; done
cat ${OUT%.csv}_*.csv > "$OUT"; echo "TOTAL $(grep -c . "$OUT")"
