"""Prepare task 3 without inventing first-report outcomes or opening validation keys."""
import csv
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/out'


def main():
    ledger = list(csv.DictReader((OUT / 'selection_ledger_213.csv').open()))
    model = {r['promise_id']: r for r in csv.DictReader(
        (ROOT / 'repo/data/promise_model_F5.csv').open())}
    rows = []
    for entry in ledger:
        if entry['in_final_F5'] != '1':
            continue
        original = model[entry['promise_id']]
        years = json.loads(entry['later_report_years'])
        files = json.loads(entry['later_report_files'])
        assert years == sorted(years) and len(years) == len(files) and years[0] > int(entry['year'])
        firm = entry['firm']
        sector = ('holding' if any(s in firm for s in ['самрук_қазына', 'байтерек']) else
                  'other_fin' if firm in ['аграрная_кредитная_корпорация', 'мфо_эко_финанс'] else
                  'bank_ins' if original['finance'] == '1' else 'nonfin')
        rows.append(dict(promise_id=entry['promise_id'], country=entry['country'],
                         firm=firm, commitment_year=entry['year'], category=entry['category'],
                         sector4=sector, retained_fragment_id=entry['retained_fragment_id'],
                         original_excerpt=entry['retained_fragment_excerpt'],
                         first_available_report_year=years[0], first_available_report_file=files[0],
                         report_year_gap=years[0] - int(entry['year']),
                         total_available_later_reports=len(years),
                         source_report_retrieved='', full_source_context_checked='',
                         report_publication_date='', original_deadline='',
                         promised_stage='', promised_scope='',
                         first_report_status='', evidence_quote='', evidence_location='',
                         coder_name='', adjudication_notes='',
                         status='awaiting_first_report_source_review'))
    assert len(rows) == 183
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / 'first_followup_worklist_183.csv', index=False)
    # Metadata support only: there are no new outcome estimates in this table.
    cells = frame.groupby(['country', 'commitment_year', 'sector4',
                           'first_available_report_year', 'report_year_gap'], dropna=False).agg(
                               commitments=('promise_id', 'size'), firms=('firm', 'nunique')).reset_index()
    cells.to_csv(OUT / 'T_first_followup_support_cells.csv', index=False)
    assert cells.commitments.sum() == 183
    saved_sector = pd.read_csv(OUT / 'T_sector_country.csv')
    expected = {(r.country, r.sector4): r.N for r in saved_sector.itertuples()}
    assert frame.groupby(['country', 'sector4']).size().to_dict() == expected
    status = dict(snapshot_role='Metadata preparation only; not current coding progress. See task3_current_status.json.', task3_status='prepared_not_completed', retained_cases=183,
                  first_report_outcomes_newly_coded=0, full_reports_newly_checked=0,
                  source='Task2 reconstructed availability and unchanged F5 membership',
                  limits=['First available report is not necessarily the first report actually published.',
                          'Report-year gap is not elapsed months or time relative to a promised deadline.',
                          'The 23 unresolved omitted candidates require eligibility review separately.',
                          'Latest multi-report outcomes have not been copied into first-report fields.',
                          'No new outcome comparison or model has been estimated.'])
    (OUT / 'first_followup_preparation_status.json').write_text(json.dumps(status, indent=2))
    print(json.dumps(status, indent=2))


if __name__ == '__main__':
    main()
