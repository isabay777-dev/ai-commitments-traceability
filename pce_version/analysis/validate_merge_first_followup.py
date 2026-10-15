# -*- coding: utf-8 -*-
"""Validate source-only adjudications, preserving missingness, before estimation."""
import csv,json,argparse,hashlib
from pathlib import Path
from check_first_followup_rounds import present
ROOT=Path(__file__).resolve().parents[1]
STATUS={'fulfilled','partial','not_fulfilled','dropped'}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--partial',action='store_true');args=parser.parse_args()
 paths=[ROOT/'first_followup_adjudication'/x for x in ['KZ_PL.json','NL.json']]
 if args.partial and not paths[1].exists():paths += [ROOT/'first_followup_adjudication'/x for x in ['NL_part1.json','NL_part2.json']]
 if not args.partial and not all(p.exists() for p in paths):raise SystemExit('Adjudication not complete: both KZ_PL.json and NL.json required')
 rows=[r for p in paths if p.exists() for r in json.loads(p.read_text())]
 manifest={r['case_id']:r for r in json.loads((ROOT/'first_followup_packets/manifest.json').read_text())}
 assert len(rows)==len({r['case_id'] for r in rows}) and {r['case_id'] for r in rows} <= set(manifest)
 if not args.partial:assert len(rows)==183 and {r['case_id'] for r in rows}==set(manifest)
 flags=[]
 for row in rows:
  cid=row['case_id'];packet=json.loads((ROOT/manifest[cid]['packet_path']).read_text());issues=[]
  for key in ['source_adequacy','eligibility','first_report_status','adjudication_rationale','original_quote','original_locator','promised_stage_normalized','promised_scope','broad_undertaking','deadline_verbatim','entity_perimeter','object_linkage']:
   if key not in row:issues.append('missing_field_'+key)
  for key in ['adjudication_rationale','original_quote','original_locator','entity_perimeter','object_linkage','reason_code']:
   if not row.get(key):issues.append('empty_provenance_'+key)
  status=row.get('first_report_status');eligible=row.get('eligibility')
  if row.get('promised_stage_normalized') not in {'study','pilot','deployment','other','unspecified'}:issues.append('invalid_promised_stage')
  if row.get('broad_undertaking') not in [True,False,'uncertain']:issues.append('invalid_broadness')
  if status not in STATUS | {'not_a_promise',None}:issues.append('invalid_status')
  if eligible not in {'commitment','not_a_promise','unresolved'}:issues.append('invalid_eligibility')
  if row.get('source_adequacy') not in {'assessable','unresolved'}:issues.append('invalid_source_adequacy')
  if eligible=='not_a_promise' and status!='not_a_promise':issues.append('noncanonical_ineligibility_status')
  if eligible=='commitment' and row.get('source_adequacy')=='assessable' and status not in STATUS:issues.append('assessable_commitment_missing_outcome')
  if status in ['fulfilled','partial','not_fulfilled'] and not row.get('followup_locator'):issues.append('empty_followup_locator')
  if status is None and not row.get('reason_code'):issues.append('missing_reason_for_unresolved')
  if status in STATUS and (eligible!='commitment' or row.get('source_adequacy')!='assessable'):issues.append('outcome_without_assessable_commitment')
  if status=='not_a_promise' and eligible!='not_a_promise':issues.append('ineligibility_conflict')
  for source,key in [('original_source','original_quote'),('followup_source','followup_quote')]:
   required=key=='original_quote' or status in ['fulfilled','partial','not_fulfilled']
   texts=[(ROOT/packet[source]['text_path']).read_text()]+[(ROOT/x['text_path']).read_text() for x in packet[source].get('supplementary_sources',[])]
   if required and not any(present(row.get(key),t) for t in texts):issues.append(key+'_literal_check_failed')
  if status=='dropped' and (not row.get('search_terms') or not row.get('searched_full_text')):issues.append('negative_search_audit_missing')
  if issues:flags.append(dict(case_id=cid,issues=issues))
 audit=dict(rows=len(rows),flags=flags,human_validation=False,passed=not flags,partial=args.partial,adjudication_inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.exists()})
 audit_path=ROOT/'analysis/out'/('first_followup_adjudication_validation_partial.json' if args.partial else 'first_followup_adjudication_validation.json')
 audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2))
 if flags:raise SystemExit(json.dumps(audit,ensure_ascii=False))
 if args.partial:
  print(json.dumps(audit));return
 fields=sorted(set().union(*(r.keys() for r in rows)))
 fields.remove('first_report_status');fields.append('first_report_status_provisional')
 with (ROOT/'analysis/out/first_followup_adjudicated.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for row in rows:
   record={k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()}
   record['first_report_status_provisional']=record.pop('first_report_status');w.writerow(record)
 audit['derived_csv_sha256']=hashlib.sha256((ROOT/'analysis/out/first_followup_adjudicated.csv').read_bytes()).hexdigest()
 audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2))
 print(json.dumps(audit))
if __name__=='__main__':main()
