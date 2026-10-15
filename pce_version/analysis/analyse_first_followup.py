# -*- coding: utf-8 -*-
"""Descriptive first-report comparison from separately adjudicated provisional codes.

No historical outcomes are copied into missing first-report values. Run only after
analysis/out/first_followup_adjudicated.csv exists with all 183 worklist IDs.
"""
import json,hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'analysis/out'
STATUS = ['fulfilled','partial','not_fulfilled','dropped']


def main():
    metadata_columns = ['promise_id','country','firm','commitment_year','category','sector4',
                        'retained_fragment_id','original_excerpt','first_available_report_year',
                        'first_available_report_file','report_year_gap','total_available_later_reports']
    # Preparation-only blank/status fields are not carried into completed data.
    validation=json.loads((OUT/'first_followup_adjudication_validation.json').read_text())
    assert validation['passed'] and not validation['partial'] and validation['rows']==183
    assert hashlib.sha256((OUT/'first_followup_adjudicated.csv').read_bytes()).hexdigest()==validation['derived_csv_sha256']
    for path,digest in validation['adjudication_inputs'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
    agreement=json.loads((OUT/'first_report_agreement_status.json').read_text())
    assert agreement['complete_both_183']
    for info in agreement['frozen_inputs'].values():assert hashlib.sha256((ROOT/info['path']).read_bytes()).hexdigest()==info['sha256']
    work = pd.read_csv(OUT/'first_followup_worklist_183.csv')[metadata_columns]
    codes = pd.read_csv(OUT/'first_followup_adjudicated.csv', keep_default_na=False)
    assert len(codes)==183 and codes.case_id.nunique()==183
    ids = pd.read_csv(OUT/'first_followup_id_crosswalk.csv')
    data = work.merge(ids,on='promise_id',validate='one_to_one').merge(codes,on='case_id',validate='one_to_one')
    assert len(data)==183
    data['assessable'] = data.first_report_status_provisional.isin(STATUS) & data.eligibility.eq('commitment')
    data['full'] = np.where(data.assessable, data.first_report_status_provisional.eq('fulfilled').astype(int), np.nan)
    data['cohort'] = data.commitment_year.astype(str)  # exact years; no unsupported 2021–22 pooling
    # Separate finite worklist coverage from assessable-case outcome proportions.
    summary = []
    for country,group in data.groupby('country'):
        valid = group[group.assessable]
        row = dict(country=country,retained_worklist=len(group),worklist_firms=group.firm.nunique(),
                   assessable=len(valid),assessable_firms=valid.firm.nunique(),ineligible=int(group.eligibility.eq('not_a_promise').sum()),
                   unresolved=int((~group.assessable & ~group.eligibility.eq('not_a_promise')).sum()),
                   confirmed_eligible=int(group.eligibility.eq('commitment').sum()),
                   eligibility_unresolved=int(group.eligibility.eq('unresolved').sum()),
                   confirmed_eligible_missing=int((group.eligibility.eq('commitment') & ~group.assessable).sum()),
                   non_assessable_total=len(group)-len(valid))
        for status in STATUS:row[status]=int(valid.first_report_status_provisional.eq(status).sum())
        row['full_percent_assessable'] = 100*row['fulfilled']/len(valid) if len(valid) else None
        summary.append(row)
    pd.DataFrame(summary).to_csv(OUT/'T_first_report_outcomes_country.csv',index=False)
    cells=[]
    for key,group in data.groupby(['country','cohort','sector4','first_available_report_year','report_year_gap']):
        valid=group[group.assessable]
        row=dict(zip(['country','cohort','sector4','first_report_year','report_year_gap'],key))
        row.update(worklist_N=len(group),worklist_firms=group.firm.nunique(),assessable_N=len(valid),assessable_firms=valid.firm.nunique(),confirmed_eligible_N=int(group.eligibility.eq('commitment').sum()),eligibility_unresolved_N=int(group.eligibility.eq('unresolved').sum()),confirmed_eligible_missing_N=int((group.eligibility.eq('commitment') & ~group.assessable).sum()),ineligible_N=int(group.eligibility.eq('not_a_promise').sum()),unresolved_N=int((~group.assessable & ~group.eligibility.eq('not_a_promise')).sum()))
        row.update({status:int(valid.first_report_status_provisional.eq(status).sum()) for status in STATUS})
        cells.append(row)
    pd.DataFrame(cells).to_csv(OUT/'T_first_report_sector_cohort_cells.csv',index=False)
    # Descriptive sensitivities retain each subset's assessable denominator.
    sensitivity=[]
    groups={'all_assessable':data.assessable,
            'one_report_year_gap':data.assessable & data.report_year_gap.eq(1),
            'banks_insurers':data.assessable & data.sector4.eq('bank_ins'),
            'non_financial':data.assessable & data.sector4.eq('nonfin')}
    if 'broad_undertaking' in data:
        precise=data.broad_undertaking.astype(str).str.lower().eq('false')
        groups['exclude_broad_and_uncertain']=data.assessable & precise
    for name,mask in groups.items():
        for country,group in data[mask].groupby('country'):
            sensitivity.append(dict(subset=name,country=country,N=len(group),firms=group.firm.nunique(),
                                    fulfilled=int(group.full.sum()),full_percent=100*group.full.mean()))
    pd.DataFrame(sensitivity).to_csv(OUT/'T_first_report_descriptive_sensitivities.csv',index=False)
    if 'promised_stage_normalized' in data:
        ambition=data.groupby(['country','commitment_year','promised_stage_normalized'],dropna=False).agg(N=('case_id','size'),
                    firms=('firm','nunique'),assessable=('assessable','sum')).reset_index()
        ambition.to_csv(OUT/'T_first_report_original_stage_support.csv',index=False)
    # Explicit reason-coded flow for every non-assessable record.
    missing=data[~data.assessable].copy()
    reason_fields=['country','commitment_year','report_year_gap','sector4','eligibility','source_adequacy','reason_code']
    missing.groupby(reason_fields,dropna=False).agg(N=('case_id','size'),firms=('firm','nunique')).reset_index().to_csv(OUT/'T_first_report_missing_reasons_cells.csv',index=False)
    missing.groupby(['country','eligibility','reason_code'],dropna=False).agg(N=('case_id','size'),firms=('firm','nunique')).reset_index().to_csv(OUT/'T_first_report_missing_reasons_country.csv',index=False)
    # Exact common support; no merging of unmatched 2021 and 2022 cohorts.
    focal_valid=data[data.country.isin(['KZ','PL']) & data.assessable].copy()
    keys=['sector4','commitment_year','report_year_gap']
    overlap=focal_valid.groupby(keys).country.nunique().eq(2)
    focal_valid['common_support']=[bool(overlap.loc[tuple(row)]) for row in focal_valid[keys].itertuples(index=False,name=None)]
    focal_valid.groupby(keys+['country']).agg(N=('case_id','size'),firms=('firm','nunique'),fulfilled=('full','sum'),common_support=('common_support','first')).reset_index().to_csv(OUT/'T_first_report_exact_overlap.csv',index=False)
    # Broadness is coded; detailed scope and deadline precision were not uniformly categorised.
    data.groupby(['country','commitment_year','broad_undertaking'],dropna=False).agg(N=('case_id','size'),firms=('firm','nunique'),assessable=('assessable','sum')).reset_index().to_csv(OUT/'T_first_report_broadness_support.csv',index=False)
    data['timing_wording_recorded']=~data.deadline_verbatim.astype(str).str.strip().str.lower().str.match(r'^(?:unknown|unspecified|not stated|not specified|not reported|not available|no deadline|none|nan|$)')
    data.groupby(['country','timing_wording_recorded']).agg(N=('case_id','size'),firms=('firm','nunique')).reset_index().to_csv(OUT/'T_first_report_timing_wording.csv',index=False)
    raw={}
    focal=data[data.country.isin(['KZ','PL']) & data.assessable]
    if set(focal.country)=={'KZ','PL'}:
        rng=np.random.default_rng(20261015);boot={}
        for country in ['KZ','PL']:
            group=focal[focal.country==country].groupby('firm').full.agg(['sum','count'])
            draws=rng.integers(0,len(group),size=(10000,len(group)))
            boot[country]=group['sum'].to_numpy()[draws].sum(axis=1)/group['count'].to_numpy()[draws].sum(axis=1)
        point=focal.groupby('country').full.mean()
        lo,hi=np.quantile(100*(boot['KZ']-boot['PL']),[.025,.975])
        raw=dict(estimand='KZ minus PL full-confirmation share among assessable retained commitments',
                 difference_pp=float(100*(point['KZ']-point['PL'])),firm_bootstrap_95_lo=float(lo),firm_bootstrap_95_hi=float(hi),resamples=10000,seed=20261015)
    # Extreme-case bounds retain the original 27/29 worklist denominators. They
    # assume all retained keys are eligible, including records newly judged ineligible. These bounds refer only to the legacy worklist; corrected eligibility results are separately reported.
    grouped={r['country']:r for r in summary}
    kz,pl=grouped['KZ'],grouped['PL']
    bounds=dict(lower_pp=100*(kz['fulfilled']/kz['retained_worklist']-(pl['fulfilled']+pl['non_assessable_total'])/pl['retained_worklist']),
                upper_pp=100*((kz['fulfilled']+kz['non_assessable_total'])/kz['retained_worklist']-pl['fulfilled']/pl['retained_worklist']),
                assumption='All original 27 KZ and 29 PL retained keys are eligible; all non-assessable legacy-worklist keys (including new ineligibility judgements) receive hypothetical full outcomes 0 or 1. This is solely a sensitivity retaining legacy eligibility, not a corrected-eligibility estimate. Not a confidence interval or national-population bound.')
    fixed={}
    for country in ['KZ','PL']:
        group=data[(data.country==country) & data.eligibility.eq('commitment')]
        full=int(group.first_report_status_provisional.eq('fulfilled').sum())
        missing_n=int((~group.assessable).sum())
        fixed[country]=dict(confirmed_eligible=len(group),fulfilled=full,eligible_missing=missing_n,
                            lower=full/len(group),upper=(full+missing_n)/len(group))
    fixed_bounds=dict(lower_pp=100*(fixed['KZ']['lower']-fixed['PL']['upper']),
                      upper_pp=100*(fixed['KZ']['upper']-fixed['PL']['lower']),by_country=fixed,
                      assumption='Eligibility fixed to cases adjudicated commitment; unresolved eligibility and newly ineligible keys excluded. Only missing binary outcomes vary. Not confidence intervals or national bounds.')
    (OUT/'first_report_comparison_summary.json').write_text(json.dumps(dict(raw_complete_case=raw,finite_worklist_extreme_bounds=bounds,fixed_confirmed_eligibility_bounds=fixed_bounds,human_validated=False),ensure_ascii=False,indent=2))
    # Agreement is computed separately from frozen rounds by first_followup_agreement.py.
    data.to_csv(OUT/'first_followup_analysis_data.csv',index=False)
    print(json.dumps(dict(country_summary=summary,raw=raw,bounds=bounds),ensure_ascii=False))


if __name__=='__main__':main()
