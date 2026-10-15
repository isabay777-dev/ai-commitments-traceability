import json,re,sys,pathlib
A={r['case_id']:r for r in json.load(open('first_followup_rounds/frozen/NL_A_v1.json'))};B={r['case_id']:r for r in json.load(open('first_followup_rounds/frozen/NL_B_v1.json'))}
def source(p,k):
 s=p[k+'_source'];return s.get('supplementary_sources',[{}])[0].get('text_path',s['text_path'])
def norm(s):return re.sub(r'\s+',' ',s).strip()
for n in range(int(sys.argv[1]),int(sys.argv[2])+1):
 c=f'FF{n:04}';p=json.load(open(f'first_followup_packets/{c}.json'));a=A[c];b=B[c]
 print('\n###',c,p['company_identifier'],p['commitment_year'],p['first_available_report_year'])
 print('ANCHOR',p['original_excerpt']);print('OQUOTE',b['original_quote']);print('OSCOPE',b.get('promised_scope'),b.get('promised_stage'),b.get('deadline'))
 print('A',a['first_report_status'],a['rationale']);print('B',b['first_report_status'],b['rationale']);print('BQ',b['followup_quote'])
 path=source(p,'followup');t=norm(pathlib.Path(path).read_text());terms=list(dict.fromkeys([x for x in a['search_terms']+b['search_terms'] if len(x)>2]+['artificial intelligence','machine learning','generative AI']))
 hits=[]
 for term in terms:
  for m in re.finditer(re.escape(term),t,re.I):hits.append((max(0,m.start()-100),min(len(t),m.end()+300)))
 merged=[]
 for s,e in sorted(hits):
  if merged and s<=merged[-1][1]:merged[-1][1]=max(e,merged[-1][1])
  else:merged.append([s,e])
 print('FOLLOWUP FULL SEARCH',path,'CHARS',len(t),'TERMS',terms,'HIT WINDOWS',len(merged))
 
 for s,e in merged:
  chunk=t[s:e]
  if re.search(sys.argv[3] if len(sys.argv)>3 else r'artificial|machine.learn|\bAI\b|DataRobot|Energy data|connected brewer',chunk,re.I):print('NORMALIZED CHARS',s,e,norm(chunk)[:1800])
