# -*- coding: utf-8 -*-
"""Frozen pre-adjudication reproducibility, with explicit decision denominators."""
import json,csv,hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
def frozen(name):
 p=ROOT/'first_followup_rounds/frozen'/f'{name}_v1.json'
 expected=p.with_suffix('.sha256').read_text().strip();actual=hashlib.sha256(p.read_bytes()).hexdigest();assert actual==expected
 return json.loads(p.read_text()),dict(path=str(p.relative_to(ROOT)),sha256=actual)
def main():
 sources={};rounds={}
 for name in ['A','B','NL_A','NL_B']:rounds[name],sources[name]=frozen(name)
 aa=rounds['A']+rounds['NL_A'];bb=rounds['B']+rounds['NL_B']
 manifest=json.loads((ROOT/'first_followup_packets/manifest.json').read_text());expected={r['case_id'] for r in manifest}
 assert len(aa)==len(bb)==len(expected)==183
 assert {r['case_id'] for r in aa}=={r['case_id'] for r in bb}==expected
 a={r['case_id']:r for r in aa};b={r['case_id']:r for r in bb};assert len(a)==len(b)==183
 countries={r['case_id']:r['country'] for r in manifest};ids=sorted(expected);result=[];confusion=[]
 for scope in ['ALL','KZ','PL','NL']:
  selected=[i for i in ids if scope=='ALL' or countries[i]==scope]
  dimensions={field:(selected,field) for field in ['source_adequacy','eligibility','first_report_status']}
  joint=[i for i in selected if all(r.get('source_adequacy')=='assessable' and r.get('eligibility')=='commitment' and r.get('first_report_status') in ['fulfilled','partial','not_fulfilled','dropped'] for r in [a[i],b[i]])]
  dimensions['substantive_status_jointly_assessable_eligible']=(joint,'first_report_status')
  for label,(chosen,field) in dimensions.items():
   x=[a[i].get(field) or 'unresolved' for i in chosen];y=[b[i].get(field) or 'unresolved' for i in chosen];n=len(x)
   agree=sum(u==v for u,v in zip(x,y));expected_agree=sum(x.count(v)*y.count(v) for v in set(x+y))/n**2 if n else None
   kappa=((agree/n)-expected_agree)/(1-expected_agree) if n and expected_agree<1 else None
   result.append(dict(scope=scope,dimension=label,paired_N=n,agree_N=agree,agreement_fraction=agree/n if n else None,kappa=kappa))
   for (left,right),count in Counter(zip(x,y)).items():confusion.append(dict(scope=scope,dimension=label,round_A=left,round_B=right,N=count))
 out=ROOT/'analysis/out'
 for name,rows in [('first_report_agreement_by_country',result),('first_report_confusion_by_country',confusion)]:
  with (out/(name+'.csv')).open('w') as f:
   w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 summary=dict(round_A=183,round_B=183,paired=183,complete_both_183=True,frozen_inputs=sources,human_validation=False,
 linkage_agreement='Not calculated: independent rounds did not collect a common structured entity/object-linkage decision. Narrative linkage is retained for source adjudication; source/eligibility agreement is not a substitute.',
 interpretation='All-case decision-path agreement includes unresolved/ineligible decisions; substantive four-status agreement conditions on joint assessable eligibility. Neither is accuracy or human validation.')
 (out/'first_report_agreement_status.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
