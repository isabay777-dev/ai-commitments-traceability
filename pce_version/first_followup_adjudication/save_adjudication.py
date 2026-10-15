import json,os,re
from pathlib import Path
A={d['case_id']:d for d in json.load(open('first_followup_rounds/frozen/A_v1.json'))};B={d['case_id']:d for d in json.load(open('first_followup_rounds/frozen/B_v1.json'))}
OUT=Path('first_followup_adjudication/KZ_PL.json')
def save(n,status,rationale,stage='deployment',broad=False,eligibility='commitment',reason=None,quote_from='A',oq=None,fq=None,scope=None,deadline=None,extra_terms=None,original_path=None):
 k=f'FF{n:04}';p=json.load(open(f'first_followup_packets/{k}.json'));a=A[k];b=B[k];base=a if quote_from=='A' else b
 op=original_path or p['original_source']['text_path'];fp=p['followup_source']['text_path'];ot=Path(op).read_text();ft=Path(fp).read_text();
 def quote_loc(q,s,path):
  if not q:return '',path+'; full text searched; no attributable continuation quote located'
  pos=s.find(q)
  if pos<0:
   tokens=re.findall(r'\S+',q);pat=r'\s+'.join(re.escape(t) for t in tokens);m=re.search(pat,s)
   if m:pos=m.start();q=m.group()
   else:raise ValueError(k+' quote not source exact: '+q[:60])
  return q,f'{path}: chars {pos}–{pos+len(q)} (0-based, end-exclusive); PDF-text page {s[:pos].count(chr(12))+1}'
 oquote,oloc=quote_loc(oq if oq is not None else base['original_quote'],ot,op)
 fquote,floc=quote_loc(fq if fq is not None else base.get('followup_quote',''),ft,fp)
 terms=list(dict.fromkeys(a.get('search_terms',[])+b.get('search_terms',[])+(extra_terms or [])))
 counts={term:len(list(re.finditer(re.escape(term),ft,re.I))) for term in terms}
 row=dict(case_id=k,source_adequacy='assessable' if status is not None else 'unresolved',eligibility=eligibility,first_report_status=status,reason_code=reason or ('unresolved_evidence' if status is None else {'fulfilled':'achieved_promised_ai_function','partial':'achieved_ai_function_smaller_scope','not_fulfilled':'identifiable_ai_work_without_achieved_state','dropped':'no_ai_continuation_after_full_text_search','not_a_promise':'positive_original_ineligibility_evidence'}[status]),adjudication_rationale=rationale,original_quote=oquote,followup_quote=fquote,original_locator=oloc,followup_locator=floc,search_terms=terms,searched_full_text=True,entity_perimeter=a.get('entity_year_check','')+' Adjudication scope: '+(scope or a.get('promised_scope','unspecified')),object_linkage=rationale,promised_stage_normalized=stage,promised_scope=scope or a.get('promised_scope','unspecified'),broad_undertaking=broad,deadline_verbatim=deadline if deadline is not None else a.get('deadline','unspecified'),original_period_end='unknown',followup_period_end='unknown',original_publication_date='unknown',followup_publication_date='unknown',date_evidence='unknown; no dates inferred from reporting-year labels',original_ambition_evidence={'quote':oquote,'locator':oloc,'initial_maturity':'See original quotation; no maturity inferred from subsequent achievements','stage_basis':stage,'scope_basis':scope or a.get('promised_scope','unspecified')},coding_provenance='Provisional LLM adjudication of both frozen rounds with source verification; not human validation.',full_text_search_hit_counts=counts,round_A_status=a['first_report_status'],round_B_status=b['first_report_status'])
 rows=json.loads(OUT.read_text()) if OUT.exists() else [];rows=[r for r in rows if r['case_id']!=k]+[row];rows.sort(key=lambda r:r['case_id']);tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps(rows,ensure_ascii=False,indent=2));os.replace(tmp,OUT);print(k,status)
