# -*- coding: utf-8 -*-
"""Generate a standalone S5 extension only from completed provisional analysis."""
import json,csv,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'analysis/out'
def table(file,columns=None):
 rows=list(csv.reader((OUT/file).open()))
 if columns:
  positions=[rows[0].index(x) for x in columns];rows=[[row[i] for i in positions] for row in rows]
 def cell(value):
  try:
   if '.' in value or 'e-' in value:
    number=float(value);value=f'{number:.2g}' if 0<abs(number)<0.001 else f'{number:.3f}'
  except ValueError:pass
  return value.replace('|','\\|').replace('\n',' ')
 return '\n'.join(['| '+' | '.join(map(cell,rows[0]))+' |','| '+' | '.join(['---']*len(rows[0]))+' |']+['| '+' | '.join(map(cell,row))+' |' for row in rows[1:]])
def main():
 provenance_path=OUT/'first_report_production_provenance.json'
 provenance=json.loads(provenance_path.read_text())
 for group in ['inputs','outputs']:
  for path,digest in provenance[group].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest, 'Stale production artifact: '+path
 audit=json.loads((OUT/'first_followup_adjudication_validation.json').read_text());assert audit['passed'] and audit['rows']==183
 stats=json.loads((OUT/'first_report_comparison_summary.json').read_text())
 text='''# Provisional first-available-report comparison

This extension concerns the original 183-key retained worklist. It uses original report context and the first available subsequent report in the frozen inventory, rather than the full set of later reports used by the original F5 exercise. All sources are public. Frozen source-only independent model rounds were followed by source-based adjudication. These procedures do not constitute independent human validation. Country and source language were evident to the models.

The outcome is confirmation at the original undertaking's AI function, stage and scope. It is not implementation, timeliness, technological success or disclosure quality. Reporting-year gaps do not measure exact exposure. Exact publication dates are not inferred from report-year labels. Cases with uncertain eligibility, entity/perimeter, linkage or adequate context remain unresolved; newly identified non-promises are separately excluded. Eligibility and fresh coding changes mean differences from the original F5 classification cannot be attributed exclusively to the follow-up window.

Structured independent entity/object-linkage agreement was not collected in a common categorical field; source-adequacy and eligibility agreement do not replace it. Narrative linkage checks are retained in adjudication.

The 23 previously unresolved selection omissions are outside this retained-worklist comparison and remain explicitly documented in the selection ledger. These results therefore do not resolve the corpus-selection objection.

## Country outcomes and denominators

Complete-case percentages condition on an assessable retained undertaking. The eligible national population is not known and no national-population estimate is claimed. Outcome codes map to the manuscript categories as follows: `fulfilled` = full confirmation, `partial` = partial confirmation, `not_fulfilled` = ongoing, `dropped` = untraced. In these tables, `not_fulfilled` means ongoing/preparatory or other non-achieved reporting, including reported postponement or cancellation; `dropped` means no located continuation after an adequate search, not abandonment. Worklist firms and assessable firms are shown separately. A newly ineligible row is not counted as an outcome zero or an unresolved eligible commitment.

'''
 text+=table('T_first_report_outcomes_country.csv',['country','retained_worklist','worklist_firms','confirmed_eligible','eligibility_unresolved','ineligible'])+'\n\n'
 text+=table('T_first_report_outcomes_country.csv',['country','assessable','assessable_firms','fulfilled','partial','not_fulfilled','dropped','full_percent_assessable'])+'\n\n'
 text+='Non-assessable retained keys have three separate components: confirmed-eligible cases without an outcome, unresolved eligibility and new ineligibility (keys judged not to be commitments). The three components sum to the non-assessable total; only the first two are unresolved eligible or possibly eligible cases.\n\n'+table('T_first_report_outcomes_country.csv',['country','confirmed_eligible_missing','eligibility_unresolved','ineligible','non_assessable_total'])+'\n\n'
 text+='## Missingness and unresolved eligibility\n\nThe country flow separates confirmed eligibility, unresolved eligibility, new ineligibility, and confirmed eligible cases lacking an outcome. Reason-coded full support cells are in `T_first_report_missing_reasons_cells.csv`.\n\n'+table('T_first_report_missing_reasons_country.csv')+'\n\n'
 text+='## Observed sector/cohort and follow-up support\n\nSparse and empty overlap cannot be repaired by covariate adjustment. Sector4 separates holdings, banks/insurers, other lenders and non-financial firms.\n\n'+table('T_first_report_sector_cohort_cells.csv',['country','cohort','sector4','first_report_year','report_year_gap','worklist_N','assessable_N','assessable_firms'])+'\n\n'
 text+='## Descriptive sensitivity subsets\n\nEach row uses its own assessable denominator and firm count. Broad or uncertain original undertakings are excluded together in the not-broad-undertaking sensitivity; this is distinct from the original F5 specificity indicator and does not harmonise all ambition differences.\n\n'+table('T_first_report_descriptive_sensitivities.csv')+'\n\n'
 text+='## Original ambition and timing support\n\nPromised stages and broadness of scope are shown by exact commitment year. Detailed scope remains in the quote-level adjudication register; it was not uniformly assigned a further categorical scale. Timing wording is recorded verbatim. Its presence does not establish a precise deadline; deadline precision and elapsed/not-yet-elapsed status were not uniformly coded. No timeliness comparison is reported.\n\n'+table('T_first_report_original_stage_support.csv')+'\n\n'+table('T_first_report_broadness_support.csv')+'\n\n'+table('T_first_report_timing_wording.csv')+'\n\n'
 text+='## Conditional focal contrast and uncertainty\n\nThe unadjusted contrast is Kazakhstan minus Poland among assessable retained undertakings. The firm bootstrap resamples observed firms within each country, keeping their commitments together; it does not represent uncertainty from purposive corpus selection, coding error or unresolved eligibility.\n\n'
 raw=stats['raw_complete_case']
 text+='| Contrast | Difference, pp | Bootstrap 95% lower | Bootstrap 95% upper |\n| --- | ---: | ---: | ---: |\n'
 text+=f"| Observed complete cases | {raw['difference_pp']:.2f} | {raw['firm_bootstrap_95_lo']:.2f} | {raw['firm_bootstrap_95_hi']:.2f} |\n\n"
 text+='Two separate extreme-case bounds are shown below. Fixed-confirmed-eligibility bounds exclude unresolved eligibility and new ineligibility, varying only missing binary outcomes. Legacy-worklist bounds hypothetically retain all originally included keys as eligible. Neither is a confidence interval or national-population bound. Full formulas, denominators and bootstrap settings are in `first_report_comparison_summary.json`.\n\n| Fixed finite target | Lower difference, pp | Upper difference, pp |\n| --- | ---: | ---: |\n'
 for key,label in [('fixed_confirmed_eligibility_bounds','Confirmed eligible cases'),('finite_worklist_extreme_bounds','Legacy 27/29 worklist, all keys assumed eligible')]:
  bound=stats[key];text+=f"| {label} | {bound['lower_pp']:.2f} | {bound['upper_pp']:.2f} |\n"
 text+='\n'
 text+='## Exact observed overlap and exploratory models\n\nCommon cells require both countries within the exact sector, commitment year and reporting-year gap. This restricts extrapolation but does not harmonise promised scope, exact publication dates or unobserved selection. Raw all-case and one-year-gap contrasts, common-cell raw contrasts, and a common-cell fixed-effect coefficient are separate estimands. Standard errors are clustered by firm; all model results are exploratory. The raw model uses a firm-clustered interval, whereas the primary raw descriptive contrast above uses a percentile firm bootstrap. The former excludes zero and the latter includes zero; this difference illustrates uncertainty-construction sensitivity with only 14 Kazakhstani and 11 Polish assessable firms, rather than a resolved national-country difference.\n\n'+table('T_first_report_exact_overlap.csv')+'\n\n'+table('T_first_report_model_support.csv')+'\n\n'
 for name in ['raw','one_year_gap','common_cells_raw','common_cells_FE']:
  text+='### '+name+'\n\n'+table('T_first_report_model_'+name+'.csv')+'\n\n'
 text+='## Inter-model reproducibility\n\nCountry/language were visible. These figures measure reproducibility of model decisions before adjudication; agreement is not accuracy and does not replace a language-competent independent human exercise.\n\n'+table('first_report_agreement_by_country.csv')+'\n\n'
 text+='## Provenance and remaining requirements\n\n`first_followup_rounds/frozen/` retains closed rounds and SHA256 values; `first_followup_adjudication/` retains adjudication rationales and quote pairs; `analysis/out/first_followup_adjudicated.csv` provides the derived codes. Source URLs, raw and text hashes, exact ZIP report members, recovery attempts and source-preserving extraction variants are recorded in `sources_first_followup/`. Raw full reports are not automatically included in the replication package. The hidden human-validation key was not used. Author verification of drafting provenance and independent human validation remain outstanding.\n'
 (ROOT/'work/S5_first_report_extension.md').write_text(text)
 extension=ROOT/'work/S5_first_report_extension.md'
 (OUT/'first_report_supplement_provenance.json').write_text(json.dumps(dict(production_manifest_sha256=hashlib.sha256(provenance_path.read_bytes()).hexdigest(),extension_sha256=hashlib.sha256(extension.read_bytes()).hexdigest()),indent=2))
 print('Generated provisional extension; not automatically inserted into S5 or submitted.')
if __name__=='__main__':main()
