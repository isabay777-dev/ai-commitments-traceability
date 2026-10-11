"""Build F5 from F4: (1) AI-function audit of all fulfilled/partial outcomes (4 downgrades, approved by the
corresponding author 2026-10-11); (2) specificity and its components recoded for ALL retained and alternative fragments
in one pass under the clarified rule (article1/specrecode/PROTOCOL_SPEC_F4.md). Earlier specificity codings are kept
for sensitivity analysis. Usage (from repository root): python3 scripts/45_build_F5.py"""
import pandas as pd
def rows(p, names): return pd.read_csv(p, sep=';', header=None, names=names, dtype=str).drop_duplicates(names[0], keep='last')
COMP = 'proc stage deadline result amount solution partner'.split()
d = pd.read_csv('data/promise_model_F4.csv')
a = pd.read_csv('data/alt_fragments_F4.csv')
fn = rows('article1/round5/fn/all.csv', 'promise_id fn_decision fn_reason fn_quote fn_file'.split())
sp = rows('article1/round5/spec/all.csv', ['id'] + COMP + ['spec_final', 'spec_evidence'])
assert set(d.promise_id) <= set(fn.promise_id) | set(d[~d.verdict_f4.isin(['fulfilled', 'partial'])].promise_id)
assert set(d.promise_id) | set(a[a.retained == 0].alt_id) <= set(sp.id), 'specificity recoding incomplete'
for c in COMP + ['spec_final']: sp[c] = sp[c].astype(int)
bad = sp[(sp.spec_final == 2) != ((sp.proc == 1) & sp[COMP[1:]].sum(axis=1).gt(0))]
assert bad.empty, f'spec does not follow the rule: {bad.id.tolist()}'
MAP = {'keep': None, 'downgrade_partial': 'partial', 'downgrade_not_fulfilled': 'not_fulfilled', 'downgrade_dropped': 'dropped', 'not_a_promise': 'not_a_promise'}
d = d.merge(fn, on='promise_id', how='left')
d['verdict_final'] = [MAP.get(x) or v if isinstance(x, str) else v for x, v in zip(d.fn_decision, d.verdict_f4)]
d = d[d.verdict_final != 'not_a_promise'].copy()
d['verdict_version'] = 'F5'
d['fulfilled'] = d.verdict_final.eq('fulfilled').astype(int)
d['fulfilled_or_partial'] = d.verdict_final.isin(['fulfilled', 'partial']).astype(int)
d['dropped'] = d.verdict_final.eq('dropped').astype(int)
d = d.rename(columns={c: f'{c}_sol' for c in COMP}).rename(columns={'spec_f4': 'spec_f4_reconciled'})
d = d.drop(columns=['spec_identify', 'spec_evaluable'])
d = d.merge(sp.rename(columns={'id': 'promise_id'}), on='promise_id', how='left')
d['spec_identify'] = ((d.solution == 1) | (d.partner == 1)).astype(int)
d['spec_evaluable'] = ((d.deadline == 1) | (d.result == 1) | (d.amount == 1)).astype(int)
d.to_csv('data/promise_model_F5.csv', index=False)
a = a.rename(columns={'spec_f4': 'spec_f4_reconciled'})
a = a.drop(columns=[c for c in COMP if c in a.columns]).merge(sp[['id', 'spec_final']], left_on='alt_id', right_on='id', how='left', suffixes=('', '_y'))
fin = d.set_index('promise_id')
a.loc[a.retained == 1, 'verdict_f4'] = a.loc[a.retained == 1, 'promise_id'].map(fin.verdict_final)
a = a.rename(columns={'verdict_f4': 'verdict_final'})
a = a[a.promise_id.isin(d.promise_id)]
a.to_csv('data/alt_fragments_F5.csv', index=False)
print('F5 N', len(d), d.verdict_final.value_counts().to_dict(), '| spec_final', d.spec_final.value_counts().to_dict(),
      '| changed outcomes', int((d.verdict_final != d.verdict_f4).sum()), '| spec differs from F4 reconciled', int((d.spec_final != d.spec_f4_reconciled).sum()))
