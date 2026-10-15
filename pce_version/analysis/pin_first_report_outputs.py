# -*- coding: utf-8 -*-
"""Pin actual analysis inputs and outputs after Python and R production finish."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'analysis/out'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 inputs=['analysis/analyse_first_followup.py','analysis/first_followup_focal_models.R','analysis/first_followup_agreement.py','analysis/validate_merge_first_followup.py','analysis/build_first_report_supplement.py','analysis/out/first_followup_adjudicated.csv','analysis/out/first_followup_adjudication_validation.json','analysis/out/first_report_agreement_status.json','analysis/out/first_followup_worklist_183.csv','analysis/out/first_followup_id_crosswalk.csv','research/FIRST_FOLLOWUP_PROTOCOL_V1.md','research/FIRST_FOLLOWUP_PROTOCOL_V1_DEVIATIONS_2026-10-15.md']
 agreement=json.loads((OUT/'first_report_agreement_status.json').read_text());assert agreement['complete_both_183']
 inputs += [r['path'] for r in agreement['frozen_inputs'].values()]
 audit=json.loads((OUT/'first_followup_adjudication_validation.json').read_text());assert audit['passed'] and audit['rows']==183 and not audit['partial']
 inputs += list(audit['adjudication_inputs'])
 outputs=list(OUT.glob('T_first_report*.csv'))+[OUT/x for x in ['first_report_comparison_summary.json','first_followup_analysis_data.csv','first_report_agreement_by_country.csv','first_report_confusion_by_country.csv','first_report_R_session.txt','first_report_model_diagnostics.txt']]
 assert len(outputs)>10
 data=dict(inputs={x:digest(ROOT/x) for x in inputs},outputs={str(x.relative_to(ROOT)):digest(x) for x in outputs},human_validation=False)
 (OUT/'first_report_production_provenance.json').write_text(json.dumps(data,indent=2));print('Pinned',len(inputs),'inputs and',len(outputs),'outputs')
if __name__=='__main__':main()
