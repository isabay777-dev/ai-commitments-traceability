"""Builds coding_sheet.csv and key_hidden.csv (run from PCE_submission/). Seed 20261015."""
import pandas as pd, re, numpy as np
R='repo/data/'; V='validation/'
SEED=20261015
def norm(s): return re.sub(r'[\W_]+','',str(s).lower())
def rd(f): return pd.read_csv(R+'sources/'+f,sep=';',engine='python',on_bad_lines='skip',dtype=str)
ok={'FOUND','FOUND_INDEXED','VERIFIED','VERIFIED_LINK','PARTIAL','CHECKED'}
u=pd.concat([rd(f)[['company','year','url','status']] for f in
  ['kz_report_urls_full.txt','pl_report_urls_full.txt','pl_kz_report_urls_raw.txt','kz_expansion_urls.csv']])
u=u[u.status.isin(ok)&u.url.str.startswith('http',na=False)].copy()
u['n']=u.company.map(norm); u['year']=pd.to_numeric(u.year,errors='coerce')
u=u.drop_duplicates(['n','year'])
es=pd.read_csv(R+'sources/esef_filings.csv'); es=es[es.country=='NL'].copy()
es['y']=es.period_end.str[:4].astype(int); es['lei']=es.lei.str.lower()
pan=pd.read_csv(R+'coded/kz_pl_firm_panel.csv')

d=pd.read_csv(R+'promise_model_F5.csv')
a=pd.read_csv(R+'alt_fragments_F5.csv'); a=a[a.retained==1][['promise_id','fragment_id','object']]
ix=pd.read_csv(R+'coded/ai_fragments_index.csv')[['fragment_id','file','excerpt']]
d=d.merge(a,on='promise_id').merge(ix,on='fragment_id')
d['stem']=d.file.str.replace(r'^[A-Z]{2}_|_\d{4}\.txt$','',regex=True)

# sample
parts=[d[d.country.isin(['KZ','PL'])]]
nl=d[d.country=='NL']
parts.append(pd.concat([g.sample(5,random_state=SEED) for _,g in nl.groupby('verdict_final')]))
s=pd.concat(parts).sample(frac=1,random_state=SEED).reset_index(drop=True)
s['vid']=['V%03d'%(i+1) for i in range(len(s))]
print(s.country.value_counts().to_dict(), s[s.country=='NL'].verdict_final.value_counts().to_dict())

def src(r):
    if r.country=='NL':
        x=es[(es.lei==r.firm)&(es.y==r.year)]
        return ('https://filings.xbrl.org'+x.report_url.iloc[0]) if len(x) else ''
    x=u[(u.n==norm(r.stem))&(u.year==r.year)]
    return x.url.iloc[0] if len(x) else ''
def later(r):
    out=[]
    if r.country=='NL':
        for _,x in es[(es.lei==r.firm)&(es.y>r.year)].sort_values('y').drop_duplicates('y').iterrows():
            out.append(f"{x.y}: https://filings.xbrl.org{x.report_url}")
    else:
        ys=sorted(pan[(pan.country==r.country)&(pan.firm.map(norm).isin({norm(r.firm),norm(r.stem)}))&(pan.year>r.year)].year.unique())
        for y in ys:
            x=u[(u.n==norm(r.stem))&(u.year==y)]
            out.append(f"{y}: "+(x.url.iloc[0] if len(x) else 'URL not listed (see company IR page)'))
    return ' | '.join(out)
s['company']=s.apply(lambda r: (es[es.lei==r.firm].name.iloc[0] if r.country=='NL' and (es.lei==r.firm).any() else r.stem.replace('_',' ')),axis=1)
s['url']=s.apply(src,axis=1); s['later']=s.apply(later,axis=1)
s['source_report']=s.apply(lambda r: r.file.replace('.txt','')+(' | '+r.url if r.url else ' | URL not found'),axis=1)
s['original_commitment_text']=s.excerpt.str.replace(r'\s+',' ',regex=True)
cols=['coder_name','specificity_specific(0/1)','process_named(0/1)','stage','deadline','target','amount','solution_or_partner','later_status(full/partial/ongoing/untraced/not_a_commitment)','evidence_quote','evidence_report_year','evidence_page','report_language','minutes_spent','notes']
out=s.rename(columns={'year':'commitment_year'})[['vid','country','company','commitment_year','original_commitment_text','source_report','later']].rename(columns={'later':'later_reports_to_search'})
for c in cols: out[c]=''
out.to_csv(V+'coding_sheet.csv',index=False,encoding='utf-8-sig')
s[['vid','promise_id','verdict_final','spec_final']].to_csv(V+'key_hidden.csv',index=False)
print(len(out),'orig text',(out.original_commitment_text.str.len()>0).sum(),'url',(s.url!='').sum(),'later',(s.later!='').sum())
print(s.groupby('country').apply(lambda g: pd.Series({'url':(g.url!='').sum(),'n':len(g)})))
