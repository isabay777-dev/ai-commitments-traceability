import json,re,pathlib,os,sys
ROOT=pathlib.Path('.')
A={r['case_id']:r for r in json.load(open('first_followup_rounds/frozen/NL_A_v1.json'))};B={r['case_id']:r for r in json.load(open('first_followup_rounds/frozen/NL_B_v1.json'))}
def findquote(p,k,q):
 s=p[k+'_source']; paths=[x['text_path'] for x in s.get('supplementary_sources',[])]+[s['text_path']]
 for path in paths:
  t=pathlib.Path(path).read_text(); pos=t.find(q)
  if pos>=0:return q,f'{path}:chars {pos}-{pos+len(q)}'
  pattern=r'\s*'.join(re.escape(x) for x in re.split(r'\s+',q.strip()))
  m=re.search(pattern,t)
  if m:return m.group(),f'{path}:chars {m.start()}-{m.end()}'
 raise ValueError((k,q[:90]))
def save(n,status,rationale,stage='deployment',broad=False,oq=None,fq=None,terms=None,eligibility='commitment',scope=None,deadline=None,reason=None):
 c=f'FF{n:04}';p=json.load(open(f'first_followup_packets/{c}.json'));a=A[c];b=B[c]
 oq,ol=findquote(p,'original',oq or b['original_quote']);fq,fl=findquote(p,'followup',fq or b['followup_quote'])
 terms=list(dict.fromkeys([x for x in a['search_terms']+b['search_terms']+(terms or []) if len(x)>1]+['artificial intelligence','machine learning','generative AI']))
 searches={}
 for k in ['original','followup']:
  s=p[k+'_source'];path=s.get('supplementary_sources',[{}])[0].get('text_path',s['text_path']);t=pathlib.Path(path).read_text()
  searches[k]={'path':path,'characters':len(t),'matches':{term:len(re.findall(r'(?<!\w)'+re.escape(term)+r'(?!\w)',t,re.I)) for term in terms}}
 r=dict(case_id=c,source_adequacy='assessable' if status is not None else 'unresolved',eligibility=eligibility,first_report_status=status,reason_code=reason or ('ai_function_evidence_ambiguous' if status is None else {'fulfilled':'promised_ai_function_achieved','partial':'achieved_ai_function_below_explicit_scope_or_stage','not_fulfilled':'ai_component_continues_without_achieved_state','dropped':'no_identifiable_ai_component_continuation','not_a_promise':'no_prospective_company_undertaking'}[status]),adjudication_rationale=rationale+' Provisional LLM adjudication; not human validation. Both frozen rounds were considered and the source evidence rechecked.',original_quote=oq,followup_quote=fq,original_locator=ol,followup_locator=fl,search_terms=terms,searched_full_text=True,entity_perimeter=b['entity_year_check'],object_linkage=rationale,promised_stage_normalized=stage,promised_scope=scope or b.get('promised_scope') or a.get('promised_scope'),broad_undertaking=broad,deadline_verbatim=deadline or 'unspecified',original_period_end='unknown',followup_period_end='unknown',original_publication_date='unknown',followup_publication_date='unknown',date_evidence='Exact reporting period ends and publication dates not independently verified; report-year labels are not substituted.',original_ambition_evidence={'quote':oq,'locator':ol,'stage_basis':stage,'scope_basis':scope or b.get('promised_scope'),'deadline_basis':deadline or 'No explicit undertaking deadline established in reviewed context.'},full_text_search_audit=searches)
 out=pathlib.Path('first_followup_adjudication/NL_part2.json');rows=json.load(open(out)) if out.exists() else []
 rows=[x for x in rows if x['case_id']!=c]+[r];rows.sort(key=lambda x:x['case_id']);tmp=out.with_suffix('.json.tmp');tmp.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,out);print(c,status,'saved',len(rows))
