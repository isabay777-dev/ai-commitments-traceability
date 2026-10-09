#!/usr/bin/env python3
"""F3 adaptation of 36_tables_v2.py. Run R scripts 37/38 first.
Original model specifications, episode membership and A/C bootstrap methods retained.
t+1 is historical audit A restricted to F3 IDs, not reclassified F3 evidence.
Writes only article1/tables_F3 and results/tables_F3.txt.
"""
from pathlib import Path
import csv, hashlib, json, os, random, sys
from decimal import Decimal, ROUND_HALF_UP
os.environ.setdefault('MPLCONFIGDIR', '/tmp/article1_mpl_F3')
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'article1/tables_F3'
OUT.mkdir(exist_ok=True)
INPUTS = []
COUNTRIES = ['KZ','PL','NL']
LEVELS = ['fulfilled','partial','not_fulfilled','dropped']
def read(path, sep=',', **kwargs):
    INPUTS.append(path)
    return pd.read_csv(ROOT/path, sep=sep, **kwargs)
def pct(x): return str(Decimal(str(x)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
def ratio(n,d): return f'{int(n)}/{int(d)} ({pct(100*n/d)}%)'
def firms(q): return len(q[['country','firm']].drop_duplicates())
def mdtable(df):
    lines = ['| '+' | '.join(map(str,df.columns))+' |','| '+' | '.join(['---']*len(df.columns))+' |']
    for row in df.itertuples(index=False,name=None):
        lines.append('| '+' | '.join(str(v).replace('|','/') for v in row)+' |')
    return '\n'.join(lines)
def panel(filename,rows):
    df=pd.DataFrame(rows)
    assert not df.isna().any().any(),filename
    df.to_csv(OUT/filename,index=False)
    return mdtable(df)
def coef(frame,model,term):
    q=frame[frame.model.eq(model)&frame.term.eq(term)]
    assert len(q)==1
    return q.iloc[0]
d=read('data/promise_model_F3.csv')
f2=read('data/promise_model_final_v2.csv')
old=read('data/promise_model_final.csv')
assert len(d)==d.promise_id.nunique()==184 and firms(d)==81
assert d.verdict_version.eq('F3').all() and d.verdict_final.equals(d.verdict_f3)
assert d.verdict_final.value_counts().to_dict()==dict(fulfilled=75,partial=55,not_fulfilled=32,dropped=22)
assert d.verdict_f3_source.value_counts().to_dict()=={'agreement_two_rounds':132,'third_adjudicator_confirmed_by_first_author_2026-10-09':52}
for col,vals in [('fulfilled',['fulfilled']),('fulfilled_or_partial',['fulfilled','partial']),('dropped',['dropped'])]:
    assert d[col].eq(d.verdict_final.isin(vals).astype(int)).all()
u=read('article1/unified/run/all.csv',';',header=None,names=['promise_id','criterion','round2','first_year','quote','file','note'])
adj=read('article1/adjudication/run/all.csv',';',header=None,names=['promise_id','adjudicated','choice','reason','quote'])
assert len(u)==u.promise_id.nunique()==190 and len(adj)==adj.promise_id.nunique()==58
comp=f2[['promise_id','verdict_final']].rename(columns={'verdict_final':'F2'}).merge(u[['promise_id','round2']],validate='one_to_one')
agree=comp.F2.eq(comp.round2)
assert agree.sum()==132 and set(comp.loc[~agree,'promise_id'])==set(adj.promise_id)
comp=comp.merge(adj[['promise_id','adjudicated']],how='left',validate='one_to_one')
comp['expected_F3']=comp.adjudicated.fillna(comp.F2)
assert comp.expected_F3.eq('not_a_promise').sum()==6
expected=comp[comp.expected_F3.ne('not_a_promise')].set_index('promise_id').expected_F3
assert d.set_index('promise_id').verdict_final.eq(expected.reindex(d.promise_id)).all()
comp=comp.merge(d[['promise_id','verdict_final','verdict_f3_source']],how='left',validate='one_to_one')
comp.to_csv(OUT/'round_reconciliation_F3.csv',index=False)
pd.crosstab(comp.F2,comp.round2).to_csv(OUT/'round_confusion_F3.csv')
excluded=f2[~f2.promise_id.isin(d.promise_id)]
excluded.to_csv(OUT/'excluded_nonpromises_F3.csv',index=False)
pe=sum(comp.F2.eq(v).mean()*comp.round2.eq(v).mean() for v in set(comp.F2)|set(comp.round2))
kappa=(agree.mean()-pe)/(1-pe)
assert round(kappa,2)==.57
INPUTS.append('article1/history/all.csv')
spec=[]
with (ROOT/INPUTS[-1]).open() as f:
    for r in csv.reader(f,delimiter=';'):
        if len(r)>=8 and r[1]=='SPEC' and r[0] in set(d.promise_id):
            spec.append(dict(promise_id=r[0],deadline_stated=int(r[3]),measurable_target=int(r[4])))
s=pd.DataFrame(spec)
assert len(s)==s.promise_id.nunique()==184
ds=d.merge(s,validate='one_to_one')
assert ds.measurable_target.sum()==11 and ds.deadline_stated.sum()==40
deadline=read('article1/analysis_A/deadline_notes.csv',';')
deadline=deadline[deadline.ID.isin(d.promise_id)]
assert len(deadline)==40 and deadline.deadline_year.notna().sum()==30 and deadline.deadline_year.gt(2025).sum()==4
rows=[]
for name,kind,fun in [
 ('Commitment records','A',lambda q:str(len(q))),('Legal entities','A',lambda q:str(firms(q))),
 ('Specificity 2','A',lambda q:ratio(q.specificity.eq(2).sum(),len(q))),
 ('Measurable target flagged','A',lambda q:ratio(q.measurable_target.sum(),len(q))),
 ('Deadline flagged','A',lambda q:ratio(q.deadline_stated.sum(),len(q))),
 ('Full confirmation','B',lambda q:ratio(q.fulfilled.sum(),len(q))),
 ('Partial confirmation','B',lambda q:ratio(q.verdict_final.eq('partial').sum(),len(q))),
 ('Continued disclosure without sufficient confirmation','B',lambda q:ratio(q.verdict_final.eq('not_fulfilled').sum(),len(q))),
 ('Untraced follow-up','B',lambda q:ratio(q.dropped.sum(),len(q))),
 ('Full or partial (combined summary)','B',lambda q:ratio(q.fulfilled_or_partial.sum(),len(q)))]:
    rows.append({'Panel':kind,'Measure':name,**{c:fun(ds[ds.country.eq(c)]) for c in COUNTRIES},'Total':fun(ds)})
t1=panel('Table_1.csv',rows)
note1=('KZ = Kazakhstan; PL = Poland; NL = the Netherlands. Panel A contains preliminary model-coded components. Panel B contains four mutually exclusive F3 outcomes and a separate combined summary; full confirmation is included in the combined measure. Thirty of 40 deadline flags have an identifiable calendar year or window end; ten are indeterminate and four extend beyond 2025. Targets and negative deadline flags were not independently validated as complete sets. All 190 F2 records underwent the protocol-C blind pass; third-model adjudication and first-author approval produced 184 F3 commitments. Outcomes concern corporate self-reports over unequal horizons. Rounding can prevent percentages from summing to 100. Source: F3 outcomes and retained preliminary component codes.')
# C's country-stratified whole-firm bootstrap, including original RNG algorithm.
rng=random.Random(20261007); cells={}
for c in COUNTRIES:
    stats=[]
    for firm in sorted(d.loc[d.country.eq(c),'firm'].unique()):
        q=d[d.country.eq(c)&d.firm.eq(firm)]
        stats.append([int(q[q.specificity.eq(1)].fulfilled.sum()),int(q.specificity.eq(1).sum()),int(q[q.specificity.eq(2)].fulfilled.sum()),int(q.specificity.eq(2).sum())])
    cells[c]=stats
reps=[]
for _ in range(10000):
    totals=[0,0,0,0]
    for stats in cells.values():
        for j in rng.choices(range(len(stats)),k=len(stats)):
            totals=[a+b for a,b in zip(totals,stats[j])]
    if totals[1] and totals[3]: reps.append(100*(totals[2]/totals[3]-totals[0]/totals[1]))
ci=np.quantile(reps,[.025,.975]).tolist()
diff=100*(d[d.specificity.eq(2)].fulfilled.mean()-d[d.specificity.eq(1)].fulfilled.mean())
bootstrap=dict(seed=20261007,replicates=len(reps),difference_pp=diff,lower_pp=ci[0],upper_pp=ci[1],firm_counts={c:len(v) for c,v in cells.items()})
rows=[]
for version,frame in [('F3 (final)',d),('F2 (pre-adjudication)',f2),('F (archived)',old)]:
    for level in [1,2]:
        q=frame[frame.specificity.eq(level)]
        rows.append({'Version':version,'Specificity':level,'N':len(q),'Full':ratio(q.fulfilled.sum(),len(q)),'Full or partial':ratio(q.fulfilled_or_partial.sum(),len(q)),'Untraced':ratio(q.dropped.sum(),len(q))})
t2a=panel('Table_2_A.csv',rows)
mc=read('results/promise_models_coefficients_F3.csv'); gc=read('results/governance_promise_models_coefficients_F3.csv')
rows=[{'Estimate':'Specificity 2 minus 1','Outcome':'Full','N/G':f'{len(d)}/{firms(d)}','Estimate, percentage points':f'{diff:.1f}; 95% CI [{ci[0]:.1f}; {ci[1]:.1f}]'}]
for model,outcome in [('m2','Full'),('m3','Full or partial')]:
    r=coef(mc,model,'spec2')
    rows.append({'Estimate':model+', spec2','Outcome':outcome,'N/G':f'{int(r.N)}/{int(r.G)}','Estimate, percentage points':f'{100*r.estimate:.1f} (SE {100*r.se:.1f})'})
t2b=panel('Table_2_B.csv',rows)
# Historical A labels restricted to the retained population, never overwritten.
a=read('article1/analysis_A/t1_outcomes.csv',';')
at=a[a.ID.isin(d.promise_id)].merge(d[['promise_id','specificity','verdict_final']],left_on='ID',right_on='promise_id',validate='one_to_one',suffixes=('_A','_F3'))
assert len(at)==184 and at.report_available_verified.sum()==169
assert at.loc[at.report_available_verified.eq(1),'outcome_A'].notna().all()
at.to_csv(OUT/'t1_retained_F3_ids.csv',index=False)
conflicts=at[at.full.eq(1)&at.verdict_final_F3.ne('fulfilled')]
assert len(conflicts)==8
conflicts.to_csv(OUT/'t1_full_vs_F3_conflicts.csv',index=False)
t1spec=[{'Specificity':i,'Historical t+1 full on retained IDs':ratio(q.full.sum(),len(q))} for i in [1,2] for q in [at[at.report_available_verified.eq(1)&at.specificity.eq(i)]]]
panel('Supplementary_specificity_t1.csv',t1spec)
dr=d[d.specificity.eq(2)].dropped.mean()/d[d.specificity.eq(1)].dropped.mean()
note2=(f'N = commitment records; G = firms. F3 is the main release; F2 and F retain their original 190-record denominators. The untraced-share ratio is {dr:.2f} in F3, 5.39 in F2 and 5.67 in F. The F3 full-confirmation difference uses 10,000 whole-firm bootstrap resamples within countries (seed 20261007). This is not an interval for the untraced-share ratio and does not include coding uncertainty. m2/m3 retain country, specificity, initial pilot status, general category, later-report count and year effects; SEs are clustered by firm. The earlier targeted re-search changed one of 24 originally untraced cases (P0058) to partial and none to full. The separate historical t+1 diagnostic, restricted to F3 IDs, is reported in Supplementary_specificity_t1.csv; its labels were not re-adjudicated under F3.')
# Retain B membership and earliest-year rule; recompute anchors with F3 outcomes.
old_ep=read('article1/analysis_B/episode_outcomes.csv',';'); ep_rows=[]
for r in old_ep.itertuples(index=False):
    q=d[d.promise_id.isin(r.member_ids.split(','))]
    if q.empty: continue
    anchors=q[q.year.eq(q.year.min())]
    assert anchors.verdict_final.nunique()==1,f'Conflicting F3 anchors: {r.episode_id}'
    assert q.country.nunique()==q.sector_group.nunique()==1
    ep_rows.append(dict(episode_id=r.episode_id,country=r.country,firm_group=r.firm_group,sector_group=r.sector_group,first_year=int(q.year.min()),anchor_ids=','.join(sorted(anchors.promise_id)),member_ids=','.join(sorted(q.promise_id)),verdict_episode=anchors.verdict_final.iloc[0],n_rows=len(q)))
episodes=pd.DataFrame(ep_rows)
assert episodes.n_rows.sum()==184
assert {x for members in episodes.member_ids for x in members.split(',')}==set(d.promise_id)
episodes.to_csv(OUT/'episode_outcomes_F3.csv',index=False)
def sector_rows(all_sectors=False):
    rows=[]
    for country in COUNTRIES:
        for sector in (['all'] if all_sectors else ['finance','non-finance']):
            q=d[d.country.eq(country)]; e=episodes[episodes.country.eq(country)]
            if sector!='all':
                q=q[q.sector_group.eq('finance')==(sector=='finance')]; e=e[e.sector_group.eq('finance')==(sector=='finance')]
            rates=e.assign(full=e.verdict_episode.eq('fulfilled')).groupby('firm_group').full.mean()
            rows.append({'Country / sector':country+' / '+sector,'Records, full n/N (%)':ratio(q.fulfilled.sum(),len(q)),'Episodes, full n/N (%)':ratio(e.verdict_episode.eq('fulfilled').sum(),len(e)),'Equal group weights (%)':pct(100*rates.mean()),'Groups':len(rates)})
    return rows
t3a=panel('Table_3_A.csv',sector_rows()); t3b=panel('Table_3_B.csv',sector_rows(True))
ngroups=len(episodes[['country','firm_group']].drop_duplicates())
note3=(f'All main outcomes use F3. The fixed repetition-audit membership, restricted to retained records, gives {len(episodes)} episodes and {ngroups} corporate groups from {firms(d)} legal entities after combining related ING entities. Empty episodes are removed; each remaining episode retains the F3 outcome of its earliest retained commitment. All same-year anchors agree in F3. Equal-group estimates first average full-confirmation indicators across episodes within each group, then give each group equal weight. These are different estimands from record-weighted shares. Sector contrasts are descriptive; no comparison of the explanatory power of country and sector is estimated. Source: F3 and the fixed repetition-audit mapping.')
# A's bootstrap draws all firms, including those without an available t+1 report.
country_t1=[]; boot_meta=[]
for ci_country,c in enumerate(COUNTRIES):
    q=at[at.country.eq(c)]
    sums=[(len(g),int(g.report_available_verified.sum()),int(g.full.eq(1).sum()),int(g.full_or_partial.eq(1).sum())) for _,g in q.groupby('firm',sort=False)]
    gnum=len(sums); rng=random.Random(20261007+ci_country); draws={'full':[],'full_or_partial':[]}; empty=0
    for _ in range(50000):
        sample=[sums[rng.randrange(gnum)] for _ in range(gnum)]
        nn,aa,ff,pp=(sum(x[j] for x in sample) for j in range(4))
        if aa: draws['full'].append(ff/aa); draws['full_or_partial'].append(pp/aa)
        else: empty+=1
    N=len(q); A=int(q.report_available_verified.sum())
    for metric in ['full','full_or_partial']:
        num=int(q[metric].eq(1).sum()); lo,hi=np.quantile(draws[metric],[.025,.975])
        country_t1.append(dict(country=c,outcome=metric,numerator=num,denominator_available=A,denominator_all=N,firms_available=q.loc[q.report_available_verified.eq(1),'firm'].nunique(),firms_total=q.firm.nunique(),ci95_low=float(lo),ci95_high=float(hi),missing_all_zero=num/N,missing_all_one=(num+N-A)/N))
    boot_meta.append(dict(country=c,seed=20261007+ci_country,replicates=50000,zero_available_replicates=empty))
ct=pd.DataFrame(country_t1); ct.to_csv(OUT/'country_t1_F3_population.csv',index=False)
rows=[]
for r in ct[ct.outcome.eq('full')].itertuples(index=False):
    rows.append({'Country':r.country,'Available / all records':f'{r.denominator_available}/{r.denominator_all}','Available / all firms':f'{r.firms_available}/{r.firms_total}','Full, n/N (%)':ratio(r.numerator,r.denominator_available),'95% CI (%)':f'{100*r.ci95_low:.1f}–{100*r.ci95_high:.1f}','Missing-data bounds (%)':f'{100*r.missing_all_zero:.1f}–{100*r.missing_all_one:.1f}'})
t4a=panel('Table_4_A.csv',rows); rows=[]
for model,term,outcome in [('g1','dig_any','Full'),('g2','dig_any','Full'),('g3','dig_any','Full or partial'),('g5','dig_nar','Full')]:
    r=coef(gc,model,term)
    rows.append({'Model / indicator':model+' / '+term,'Outcome':outcome,'Estimate, percentage points (SE)':f'{100*r.estimate:.1f} ({100*r.se:.1f})','N/G':f'{int(r.N)}/{int(r.G)}'})
t4b=panel('Table_4_B.csv',rows)
combined='; '.join(f'{r.country} {ratio(r.numerator,r.denominator_available)}' for r in ct[ct.outcome.eq('full_or_partial')].itertuples(index=False))
note4=('Panel A retains the pre-F3 audit A next-reporting-year outcomes on the 184 retained F3 IDs; 169 records have an available next-year report. It is a historical temporal diagnostic, not a fresh protocol-C/F3 classification of t+1 evidence. Eight records classified full at t+1 by A are partial in the final full-horizon F3 coding; these unresolved cross-protocol differences prevent treating Panel A as validation of F3. The next labelled reporting year is not exactly twelve months after publication. CIs use 50,000 whole-firm resamples within country, including firms without available t+1 reports (seeds 20261007–20261009). Missing-data bounds are extreme scenarios, not confidence intervals. Historical full-or-partial shares on retained IDs: '+combined+'. Panel B uses F3 outcomes over the available horizon. LPM coefficients are multiplied by 100; SEs are clustered by country–firm. g1 includes country/year effects and requires expertise and assets. g2/g3/g5 additionally include specificity, general category, within-country standardised log assets and state affiliation. Size is standardised over 159 records before 35 missing state observations reduce N to 124. Sector and director independence are not controlled. Source: historical audit A restricted to F3 IDs (Panel A); F3 governance models (Panel B).')
blocks=[(1,'Verifiability components and observed commitment outcomes',t1,note1),(2,'Specificity and sensitivity of reported confirmation','#### Panel A. Outcome profiles\n\n'+t2a+'\n\n#### Panel B. Full-confirmation difference and adjusted associations\n\n'+t2b,note2),(3,'Financial sector comparisons and alternative counting units','#### Panel A. Within-country sector profiles\n\n'+t3a+'\n\n#### Panel B. All sectors\n\n'+t3b,note3),(4,'Temporal comparability and board digital expertise','#### Panel A. Historical next-reporting-year audit on retained F3 IDs\n\n'+t4a+'\n\n#### Panel B. Governance models using F3 outcomes\n\n'+t4b,note4)]
tables=''
for number,title,body,note in blocks:
    block=f'### Table {number}. {title}\n\n{body}\n\nNotes: {note}\n'
    (OUT/f'Table_{number}.md').write_text(block); tables+=block+'\n'
(OUT/'Tables_1_4.md').write_text(tables)
figdata=pd.crosstab(d.specificity,d.verdict_final).reindex(index=[1,2],columns=LEVELS)
assert figdata.loc[1].tolist()==[49,28,16,4] and figdata.loc[2].tolist()==[26,27,16,18]
assert figdata.to_numpy().sum()==184
figdata.to_csv(OUT/'Figure_1_data.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'savefig.facecolor':'white','pdf.fonttype':42})
fig,ax=plt.subplots(figsize=(9,4.4)); left=[0.,0.]; denoms=figdata.sum(axis=1).tolist()
labels=['Full confirmation','Partial confirmation','Continued disclosure without\nsufficient confirmation','Untraced follow-up']
for j,(outcome,label,color,hatch) in enumerate(zip(LEVELS,labels,['0.2','0.58','0.88','white'],['','///','...','xxx'])):
    values=figdata[outcome].tolist(); widths=[100*n/N for n,N in zip(values,denoms)]
    ax.barh([0,1],widths,left=left,color=color,edgecolor='black',hatch=hatch,height=.48,label=label,linewidth=.7)
    for i,(n,w) in enumerate(zip(values,widths)):
        if w<6: ax.annotate(str(n),(left[i]+w/2,i),xytext=(102,i),ha='left',va='center',arrowprops={'arrowstyle':'-','color':'black'},annotation_clip=False)
        else: ax.text(left[i]+w/2,i,str(n),ha='center',va='center',color='white' if j==0 else 'black',bbox=dict(facecolor=color,edgecolor='none',pad=1))
    left=[l+w for l,w in zip(left,widths)]
ax.set(xlim=(0,100),ylim=(1.6,-.6),yticks=[0,1],yticklabels=[f'Specificity {i}\nN = {N}' for i,N in zip([1,2],denoms)],xlabel='Share of commitment records (%)')
ax.spines[['top','right']].set_visible(False); ax.legend(loc='upper center',bbox_to_anchor=(.46,-.25),ncol=2,frameon=False,fontsize=9)
fig.subplots_adjust(left=.19,right=.93,bottom=.36,top=.97)
for ext in ['png','pdf']: fig.savefig(OUT/f'Figure_1_specificity.{ext}',dpi=600,metadata={'Creator':'F3 replication script'} if ext=='pdf' else None)
plt.close(fig)
figcap=('### Figure 1. Reported outcomes by initial commitment specificity\n\nTwo horizontal stacked bars show the four F3 outcomes. Specificity 1 (N=97) contains 49 full, 28 partial, 16 continued-without-sufficient-confirmation and four untraced records. Specificity 2 (N=87) contains 26 full, 27 partial, 16 continued-without-sufficient-confirmation and 18 untraced records. Segment widths use unrounded shares; labels give counts. Outcomes concern corporate disclosure over unequal horizons, not causal effects or independently verified implementation. Source: F3. Grayscale and hatching; PNG at 600 dpi and vector PDF.\n')
(OUT/'Figure_1.md').write_text(figcap+'\n![Figure 1](Figure_1_specificity.png)\n\n[Vector PDF](Figure_1_specificity.pdf).\n')
p=read('data/panel_ai_disclosure.csv'); assert len(p)==1098
trend=p.groupby(['country','year']).ai_any.agg(['sum','count']).reset_index(); trend['share']=trend['sum']/trend['count']
trend.to_csv(OUT/'Supplementary_Figure_S1_data.csv',index=False)
fig,ax=plt.subplots(figsize=(8,4.8))
for c,marker,ls in zip(COUNTRIES,['o','s','^'],['-','--',':']):
    q=trend[trend.country.eq(c)]; ax.plot(q.year,q.share*100,marker=marker,linestyle=ls,color='black',label=c)
ax.set(xticks=[2021,2022,2023,2024,2025],ylim=(0,100),xlabel='Reporting year',ylabel='Reports with dictionary mentions of AI (%)')
ax.legend(frameon=False); ax.spines[['top','right']].set_visible(False); fig.tight_layout()
for ext in ['png','pdf']: fig.savefig(OUT/f'Supplementary_Figure_S1.{ext}',dpi=600,metadata={'Creator':'F3 replication script'} if ext=='pdf' else None)
plt.close(fig)
denoms_text='; '.join(c+': '+', '.join(f'{int(r.year)}: {int(r["sum"])}/{int(r["count"])}' for _,r in trend[trend.country.eq(c)].iterrows()) for c in COUNTRIES)
s1cap=('### Supplementary Figure S1. Dictionary mentions of AI in the original report panel\n\nReports with dictionary matches in the original 1,098-report panel, with annual country-specific denominators: '+denoms_text+'. The composition changes between years; four texts designated unusable during subsequent-report matching remain in this source panel. Matches may reflect extraction damage. This figure describes retrieval, not AI adoption, a fixed company cohort or commitment outcomes. It is not evidence for the specificity association. F3 changes commitment outcomes, not this source panel. Source: original report panel.\n')
(OUT/'Supplementary_Figure_S1.md').write_text(s1cap+'\n![Supplementary Figure S1](Supplementary_Figure_S1.png)\n\n[Vector PDF](Supplementary_Figure_S1.pdf).\n')
validation=dict(records=len(d),firms=firms(d),countries=d.country.value_counts().to_dict(),outcomes=d.verdict_final.value_counts().to_dict(),episodes=len(episodes),groups=ngroups,round_agreement=int(agree.sum()),round_pairs=len(comp),kappa=kappa,round2_full_or_partial=int(u.round2.isin(['fulfilled','partial']).sum()),excluded=excluded.promise_id.tolist(),specificity_bootstrap=bootstrap,t1_available=int(at.report_available_verified.sum()),t1_bootstrap=boot_meta,t1_full_F3_nonfull=conflicts.ID.tolist(),python=sys.version.split()[0],pandas=pd.__version__,matplotlib=matplotlib.__version__)
(OUT/'validation_F3.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False)+'\n')
INPUTS+=['scripts/37_models_F3.R','scripts/38_governance_F3.R','scripts/39_tables_F3.py','article1/analysis_C/analyze.py','article1/analysis_A/analyse.py','article1/analysis_B/reproduce.py']
(OUT/'source_manifest.json').write_text(json.dumps({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS},indent=2,ensure_ascii=False)+'\n')
(OUT/'README.md').write_text('# F3 release exhibits\n\nRun from the project root:\n\n```sh\nRscript scripts/37_models_F3.R\nRscript scripts/38_governance_F3.R\npython3 scripts/39_tables_F3.py\n```\n\nTables 1–4 and captions are English submission materials. CSV files retain exact counts; R exports retain full-precision coefficients and actual estimation samples. Figure 1 and Supplementary Figure S1 have grayscale 600 dpi PNG and vector PDF exports.\n\nThe script validates all 190 round pairs, 58 adjudications and six exclusions. It preserves the episode mapping and applies F3 verdicts to the earliest retained anchors. Temporal audit A retains its historical t+1 labels on the F3 population; eight full-at-t+1 versus F3-partial conflicts are exported and disclosed in Table 4. This diagnostic is not harmonised F3 validation. No source data or earlier releases are rewritten.\n\nvalidation_F3.json records checks, bootstrap settings and versions. source_manifest.json records input SHA-256 values; preserved_source_hashes.json is the pre-edit snapshot.\n')
summary=json.dumps(validation,indent=2,ensure_ascii=False)+'\n'
(ROOT/'results/tables_F3.txt').write_text(summary)
print(summary)
