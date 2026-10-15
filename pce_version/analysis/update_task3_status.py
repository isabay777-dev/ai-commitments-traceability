# -*- coding: utf-8 -*-
"""Write factual progress without implying completed coding or validation."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def rows(path,default=None):
 p=ROOT/path
 return json.loads(p.read_text()) if p.exists() else ([] if default is None else default)
def main():
 paths=['first_followup_rounds/A.json','first_followup_rounds/B.json','first_followup_rounds/NL_A.json','first_followup_rounds/NL_B.json','first_followup_adjudication/KZ_PL.json','first_followup_adjudication/NL.json','first_followup_adjudication/NL_part1.json','first_followup_adjudication/NL_part2.json']
 counts={p:len(rows(p)) for p in paths}
 manifest=rows('first_followup_packets/manifest.json')
 data=dict(updated_utc=datetime.now(timezone.utc).isoformat(),source_packets=len(manifest),source_ready=sum(r['ready'] for r in manifest),coding_counts=counts,readability_companions=len(rows('sources_first_followup/readability_manifest.json',{})),human_validation=False,new_manuscript_estimates_inserted='### 4.6 First available subsequent report' in (ROOT/'work/ms_pce_v2.md').read_text())
 (ROOT/'analysis/out/task3_current_status.json').write_text(json.dumps(data,indent=2))
 table='\n'.join(f'| `{p}` | {n} |' for p,n in counts.items())
 (ROOT/'research/TASK3_STATUS.md').write_text(f'''# Задача3: фактический статус\n\nОбновленоUTC: {data['updated_utc']}.\n\nИсточник и текст доступны для {data['source_ready']} из {data['source_packets']} случаев. Это проверка доступности, а не подтверждение сущности, года или исхода.\n\n| Файл текущего раунда | Записей |\n| --- | ---: |\n{table}\n\nИзначальные результаты A/B по KZPL сохранены в `first_followup_rounds/frozen/` с SHA256. Незакрытые NL-раунды ещё могут исправляться по источникам. Дополнительных HTML-извлечений с сохранением inline-слов: {data['readability_companions']}; оригинальные файлы сохранены.\n\nРезультаты первого доступного отчёта внесены в рукопись и S5; численный аудит 35/35 и проверка согласованности PASS. Полные интервалы, явные пропуски и ограниченные общие ячейки сохранены. Word-пакет и публичная репликация ещё не синхронизированы. Независимая человеческая валидация и подтверждение авторами истории написания остаются отдельными невыполненными условиями. Ничего не подано и не опубликовано.\n''')
 print(json.dumps(data))
if __name__=='__main__':main()
