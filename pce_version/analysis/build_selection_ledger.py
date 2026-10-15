"""Reconstruct the 213 historical candidate keys; never re-adjudicate eligibility.

Run from any directory: python3 PCE_submission/analysis/build_selection_ledger.py
Uses the checked selection-flow reconstruction and archived per-record decisions.
No report downloads, model calls, validation keys or outcome changes are involved.
"""
import contextlib
import csv
import hashlib
import io
import json
from pathlib import Path
import runpy

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'repo'
OUT = ROOT / 'analysis/out'


def records(path, names=None):
    with path.open(encoding='utf-8', newline='') as handle:
        if names:
            rows = [dict(zip(names, row)) for row in csv.reader(handle, delimiter=';')]
        else:
            rows = list(csv.DictReader(handle))
    assert len({row['promise_id'] for row in rows}) == len(rows), f'Duplicate IDs in {path}'
    return {row['promise_id']: row for row in rows}


def packed(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def main():
    with contextlib.redirect_stdout(io.StringIO()):
        ns = runpy.run_path(str(ROOT / 'analysis/selection_flow.py'))
    candidates, fragments, panel = ns['k'], ns['q'], ns['elig']
    firm_of = ns['firm_of']
    initial = set(ns['uni']['promise_id'])
    f3 = records(REPO / 'data/coded/commitments_F3.csv')
    f4 = records(REPO / 'data/coded/commitments_F4.csv')
    final = records(REPO / 'data/coded/commitments_final.csv')
    model = records(REPO / 'data/promise_model_F5.csv')
    excluded = records(REPO / 'tables/excluded_nonpromises_F3.csv')
    third = records(REPO / 'data/coded/third_adjudicator_decisions.csv',
                    ['promise_id', 'decision', 'basis', 'reason', 'quote'])
    harmonised = records(REPO / 'article1/harmonise/run/all.csv',
                         ['promise_id', 'decision', 'first_year', 'changed',
                          'reason', 'quote', 'source'])
    idx = ns['idx'].set_index('fragment_id')
    coding_files = {}
    for name in ['main_coded.csv', 'pilot_coded.csv']:
        for line in (REPO / 'data/coded' / name).read_text().splitlines():
            if len(line.split(';')) >= 9:
                coding_files.setdefault(line.split(';', 1)[0], 'repo/data/coded/' + name)
    later = {}
    for row in panel.itertuples():
        country, firm, year = firm_of(row.fn[:-4] + '#0')
        later.setdefault((country, firm), []).append((year, row.fn))
    grouped = {key: group for key, group in fragments.groupby(ns['KC'], sort=False)}
    assert len(candidates) == 213 and candidates.pid.nunique() == 213
    assert len(initial) == 190 and len(f3) == 184 and len(f4) == len(final) == 183
    assert set(final) == set(model) == set(f4)
    assert set(final) <= set(f3) <= initial <= set(candidates.pid)
    assert set(excluded) == initial - set(f3)
    ledger = []
    links = []
    for row in candidates.itertuples(index=False):
        pid = row.pid
        key = (row.country, row.firm, row.category, int(row.year))
        group = grouped[key]
        retained = row.fragment_id
        assert retained == group.iloc[0].fragment_id
        followup = sorted(set((year, name) for year, name in later[(row.country, row.firm)]
                              if year > int(row.year)))
        assert len(followup) == int(row.n_later_rec)
        if pid in final:
            disposition = 'included_final'
            reason = 'Retained in the archived final F5 analytical dataset.'
            evidence = 'repo/data/coded/commitments_final.csv; repo/data/promise_model_F5.csv'
            reason_status = 'documented_membership'
        elif pid not in initial:
            disposition = 'omitted_before_initial_coding_unresolved'
            reason = ''
            evidence = 'Reconstructed 213-key population minus repo/data/coded/unified_recoding.csv'
            reason_status = 'unresolved_no_archived_per_key_verdict'
        elif pid not in f3:
            disposition = 'excluded_non_commitment_F3'
            assert third[pid]['decision'] == 'not_a_promise'
            reason = third[pid]['reason']
            evidence = 'repo/tables/excluded_nonpromises_F3.csv; repo/data/coded/third_adjudicator_decisions.csv'
            reason_status = 'documented_historical_decision'
        else:
            disposition = 'excluded_non_commitment_F4'
            assert harmonised[pid]['decision'] == 'not_a_promise'
            reason = harmonised[pid]['reason']
            evidence = 'repo/article1/harmonise/run/all.csv; repo/scripts/41_build_F4.py'
            reason_status = 'documented_historical_decision'
        for stage in [f3, f4, final, model]:
            if pid in stage:
                entry = stage[pid]
                assert (entry['country'], entry['firm'], entry['category'], int(entry['year'])) == key
        if pid in final:
            assert len(followup) == int(final[pid]['n_later_reports'])
        source_excerpt = str(idx.loc[retained, 'excerpt']) if retained in idx.index else ''
        record = dict(promise_id=pid, country=row.country, firm=row.firm,
                      category=row.category, year=int(row.year),
                      retained_fragment_id=retained, promise_status=row.status,
                      original_use_case=row.use_case,
                      retained_fragment_excerpt=source_excerpt,
                      original_source_code=row.source,
                      fragment_coding_file=coding_files[retained],
                      n_candidate_fragments=len(group),
                      candidate_fragment_ids=packed(group.fragment_id.tolist()),
                      n_later_reports=len(followup),
                      later_report_years=packed([y for y, _ in followup]),
                      later_report_files=packed([name for _, name in followup]),
                      in_initial190=int(pid in initial), in_F3=int(pid in f3),
                      in_F4=int(pid in f4), in_final_F5=int(pid in final),
                      disposition=disposition, reason_status=reason_status,
                      recorded_reason=reason, disposition_evidence=evidence,
                      final_outcome=final.get(pid, {}).get('verdict_final', ''),
                      eligibility_reassessed=0, project_identity_verified=0)
        ledger.append(record)
        for fragment in group.itertuples():
            links.append(dict(promise_id=pid, fragment_id=fragment.fragment_id,
                              retained_first=int(fragment.fragment_id == retained),
                              excerpt=str(idx.loc[fragment.fragment_id, 'excerpt'])
                              if fragment.fragment_id in idx.index else '',
                              original_source_code=fragment.source,
                              fragment_coding_file=coding_files[fragment.fragment_id]))
    data = pd.DataFrame(ledger)
    counts = data.groupby(['country', 'disposition']).size().unstack(fill_value=0)
    assert data.disposition.value_counts().to_dict() == {
        'included_final': 183, 'omitted_before_initial_coding_unresolved': 23,
        'excluded_non_commitment_F3': 6, 'excluded_non_commitment_F4': 1}
    assert data.groupby('country').size().to_dict() == {'KZ': 33, 'NL': 146, 'PL': 34}
    assert data[data.in_final_F5 == 1].groupby('country').size().to_dict() == {'KZ': 27, 'NL': 127, 'PL': 29}
    assert data[data.in_initial190 == 0].groupby('country').size().to_dict() == {'KZ': 4, 'NL': 15, 'PL': 4}
    assert data.retained_fragment_excerpt.ne('').all()
    data.to_csv(OUT / 'selection_ledger_213.csv', index=False)
    data[data.reason_status.str.startswith('unresolved')].to_csv(OUT / 'selection_ledger_unresolved_23.csv', index=False)
    pd.DataFrame(links).to_csv(OUT / 'selection_ledger_fragment_links.csv', index=False)
    counts.reset_index().to_csv(OUT / 'T_selection_dispositions.csv', index=False)
    # Hash actual inputs only; validation/key_hidden.csv is deliberately absent.
    inputs = [ROOT / 'analysis/selection_flow.py', REPO / 'scripts/21_follow_through.py',
              REPO / 'scripts/22_promise_packets.py', REPO / 'scripts/41_build_F4.py',
              *[REPO / 'data/coded' / name for name in [
                  'report_panel_ai_mentions.csv', 'ai_fragments_index.csv',
                  'main_coded.csv', 'pilot_coded.csv', 'unified_recoding.csv',
                  'commitments_F3.csv', 'commitments_F4.csv', 'commitments_final.csv',
                  'third_adjudicator_decisions.csv']],
              REPO / 'data/sources/esef_filings.csv', REPO / 'data/promise_model_F5.csv',
              REPO / 'data/alt_fragments_F5.csv',
              REPO / 'tables/excluded_nonpromises_F3.csv',
              REPO / 'article1/harmonise/run/all.csv']
    audit = dict(candidate_keys=213, initial_coded=190, final_included=183,
                 documented_non_commitment_exclusions=7, unresolved_initial_omissions=23,
                 candidate_fragment_links=len(links),
                 final_key_and_followup_matches=183,
                 unresolved_ids=data.loc[data.in_initial190 == 0, 'promise_id'].tolist(),
                 new_eligibility_decisions=0, outcome_labels_changed=0,
                 inputs_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in inputs},
                 caveats=['Reconstructed operational keys are not verified unique AI projects.',
                          'Historical script 21 uses file bytes >=50000; reconstruction uses panel characters >=50000. These are not identical filters. The final 183 follow-up counts match, but excluded source texts were not independently re-extracted.',
                          'Report availability is reconstructed from panel metadata; full report texts are not rechecked.',
                          'Excerpts are archived retrieval windows, not independently verified complete source context.',
                          'Blank recorded_reason means unknown; code-implied possibilities are not per-key evidence.'])
    (OUT / 'selection_ledger_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(counts.to_string())
    print('213 keys accounted for: 183 retained, 7 documented exclusions, 23 unresolved omissions.')


if __name__ == '__main__':
    main()
