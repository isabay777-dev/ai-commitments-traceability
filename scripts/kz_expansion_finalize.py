#!/usr/bin/env python3
import csv,json,shlex,subprocess
from pathlib import Path
from kz_expansion_verify import D,FIELDS,load,ticker,read
rows,baseline,found,missing,scope,metrics,raw=load()
# Prefer the current catalogue edition; retain all attempts in the requested URL log.
provenance=read('kz_expansion_provenance.json');preferred={}
for r in rows:
    if r['status']!='FOUND':continue
    key=(ticker(r['ticker']),r['year']);r=dict(r);r['ticker']=key[0]
    if key not in preferred or 'document' in provenance[r['url']]:preferred[key]=r
with (D/'kz_expansion_found_new.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS,delimiter=';',lineterminator='\n');w.writeheader()
    w.writerows(preferred[k] for k in sorted(found-baseline))
with (D/'kz_expansion_original_outcomes.csv').open('w') as f:
    fields=['ticker','company','year','status','url','attempted_urls','note']
    w=csv.DictWriter(f,fieldnames=fields,delimiter=';',lineterminator='\n');w.writeheader()
    for t,y in sorted(missing):
        attempts=[r for r in rows if ticker(r['ticker'])==t and r['year']==y]
        ok=preferred.get((t,y))
        note='Verified annual report' if ok else 'No verified PDF/HTML annual report after KASE catalogue, filename probes and targeted web search; NOT proof of nonpublication'
        if t=='ASTL' and y=='2021':note='KASE catalogue lists annual report in PPTX; not eligible under PDF/HTML-only criterion'
        w.writerow(dict(ticker=t,company=attempts[0]['company'],year=y,status='FOUND' if ok else 'NOT_FOUND',url=ok['url'] if ok else '',attempted_urls=len(attempts),note=note))
(D/'kz_expansion_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
# Replace only a prior trailer if this reconciliation is rerun.
p=D/'kz_expansion_urls.csv'
if any(r[0]=='SUMMARY' for r in raw):
    with p.open('w') as f:
        w=csv.writer(f,delimiter=';',lineterminator='\n');w.writerows(r for r in raw if r[0]!='SUMMARY')
summary=f'SUMMARY;новых компаний {metrics["new_companies"]};новых компания-лет {metrics["new_company_years"]}'
subprocess.run(['/bin/sh','-c','echo '+shlex.quote(summary)+' >> '+shlex.quote(str(p))],check=True)
print(json.dumps(metrics,ensure_ascii=False,indent=2))
