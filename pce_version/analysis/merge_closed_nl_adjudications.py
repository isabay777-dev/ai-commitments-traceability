# -*- coding: utf-8 -*-
"""Merge only closed, hash-pinned source adjudication halves, without recoding."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'first_followup_adjudication';FROZEN=BASE/'frozen'
def main():
 rows=[];inputs=[]
 for part,start,end in [(1,28,92),(2,92,155)]:
  p=FROZEN/f'NL_part{part}_v1.json';actual=hashlib.sha256(p.read_bytes()).hexdigest()
  assert actual==p.with_suffix('.sha256').read_text().strip()
  data=json.loads(p.read_text());expected={f'FF{i:04d}' for i in range(start,end)}
  assert len(data)==len(expected) and {r['case_id'] for r in data}==expected
  rows+=data;inputs.append(dict(path=str(p.relative_to(ROOT)),sha256=actual))
 assert len(rows)==127 and len({r['case_id'] for r in rows})==127
 text=json.dumps(sorted(rows,key=lambda r:r['case_id']),ensure_ascii=False,indent=2)+'\n'
 out=BASE/'NL.json';tmp=BASE/'NL.merge.tmp';tmp.write_text(text);tmp.replace(out)
 pin=FROZEN/'NL_v1.json';pin.write_bytes(out.read_bytes());digest=hashlib.sha256(pin.read_bytes()).hexdigest();pin.with_suffix('.sha256').write_text(digest+'\n')
 (BASE/'NL_merge_provenance.json').write_text(json.dumps(dict(inputs=inputs,merged_sha256=digest,rows=127),indent=2))
 print('Merged127 closed adjudications',digest)
if __name__=='__main__':main()
