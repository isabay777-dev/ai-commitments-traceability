import json,re,sys
from pathlib import Path
A={d['case_id']:d for d in json.load(open('first_followup_rounds/frozen/A_v1.json'))}
B={d['case_id']:d for d in json.load(open('first_followup_rounds/frozen/B_v1.json'))}
def show(n):
 k=f'FF{n:04}';p=json.load(open(f'first_followup_packets/{k}.json'));a=A[k];b=B[k]
 print('\n===',k,p['company_identifier'],p['commitment_year'],p['first_available_report_year'],'===')
 print('ANCHOR',p['original_excerpt']);print('A',a['first_report_status'],a['rationale']);print('B',b['first_report_status'],b['rationale'])
 for side,qkey in [('original','original_quote'),('followup','followup_quote')]:
  path=p[side+'_source']['text_path'];s=Path(path).read_text() if path and Path(path).exists() else ''; print(side,path,'CHARS',len(s))
  spans=[]
  for d in [a,b]:
   q=d.get(qkey,'');pos=s.find(q) if q else -1
   if pos>=0:spans.append((max(0,pos-250),min(len(s),pos+len(q)+250)))
   elif q:print('QUOTE NOT EXACT:',repr(q))
  merged=[]
  for st,en in sorted(spans):
   if merged and st<=merged[-1][1]:merged[-1][1]=max(en,merged[-1][1])
   else:merged.append([st,en])
  for st,en in merged: print('SOURCE chars',st,en,'PDFpage',s[:st].count('\f')+1,':',s[st:en])
for n in map(int,sys.argv[1:]):show(n)
