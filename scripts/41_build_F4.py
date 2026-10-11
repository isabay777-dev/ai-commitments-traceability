"""Build F4: harmonised outcomes (frozen rule article1/harmonise/PROTOCOL_F4.md, 12 changes approved by the
corresponding author 2026-10-11) and reconciled specificity (original coding vs blind component recoding, disagreements
adjudicated under article1/specrecode/PROTOCOL_SPEC_F4.md). Also builds the alternative-fragment file for robustness.
Usage: python3 scripts/41_build_F4.py"""
import pandas as pd
def rows(p, names): return pd.read_csv(p, sep=';', header=None, names=names, dtype=str).drop_duplicates(names[0], keep='last')
f3 = pd.read_csv('data/promise_model_F3.csv', dtype={'specificity': str})
h = rows('article1/harmonise/run/all.csv', 'promise_id verdict_f4 first_year_f4 changed reason_f4 quote_f4 file_f4'.split())
sol = rows('article1/specrecode/run/all.csv', 'id proc stage deadline result amount solution partner spec_sol object'.split())
adj = rows('article1/specrecode/adj/all.csv', 'id spec_adj process_named detail_found evidence'.split())
alt = pd.read_csv('article1/altfrag/alt_fragments.csv', dtype=str)
ep = pd.read_csv('article1/analysis_B/episode_outcomes.csv', sep=';', dtype=str)
grp = {m: g for g, ms in zip(ep.firm_group, ep.member_ids) for m in ms.split(',')}
epi = {m: e for e, ms in zip(ep.episode_id, ep.member_ids) for m in ms.split(',')}

def reconcile(df, orig_col):
    df = df.merge(sol, on='id', how='left').merge(adj[['id', 'spec_adj']], on='id', how='left')
    o2, s2 = df[orig_col].eq('2'), df.spec_sol.eq('2')
    df['spec_f4'] = (o2 & s2).map({True: 2, False: 1})
    dis = o2 != s2
    assert df.loc[dis, 'spec_adj'].notna().all(), 'missing adjudication'
    df.loc[dis, 'spec_f4'] = df.loc[dis, 'spec_adj'].astype(int)
    df['spec_f4_source'] = dis.map({True: 'adjudicated', False: 'agreement'})
    df['spec_identify'] = ((df.solution == '1') | (df.partner == '1')).astype(int)
    df['spec_evaluable'] = ((df.deadline == '1') | (df.result == '1') | (df.amount == '1')).astype(int)
    return df

d = f3.merge(h, on='promise_id', how='left'); assert d.verdict_f4.notna().all()
d['id'] = d.promise_id; d = reconcile(d, 'specificity')
d = d[d.verdict_f4 != 'not_a_promise'].copy()
d['verdict_final'] = d.verdict_f4; d['verdict_version'] = 'F4'
d['fulfilled'] = d.verdict_f4.eq('fulfilled').astype(int)
d['fulfilled_or_partial'] = d.verdict_f4.isin(['fulfilled', 'partial']).astype(int)
d['dropped'] = d.verdict_f4.eq('dropped').astype(int)
d['finance'] = d.sector_group.eq('finance').astype(int)
d['firm_group'] = d.promise_id.map(grp); d['episode_id'] = d.promise_id.map(epi)
d['specificity_original'] = d.specificity
keep = [c for c in f3.columns if c not in ('verdict', 'verdict_f3', 'verdict_f3_source', 'verdict_source')] + \
       ['verdict_f3', 'verdict_f3_source', 'verdict_f4', 'first_year_f4', 'reason_f4', 'quote_f4', 'file_f4', 'specificity_original',
        'spec_sol', 'spec_f4', 'spec_f4_source', 'proc', 'stage', 'deadline', 'result', 'amount', 'solution', 'partner',
        'spec_identify', 'spec_evaluable', 'finance', 'firm_group', 'episode_id']
d = d[[c for c in dict.fromkeys(keep) if c not in ('specificity',)]]
d.to_csv('data/promise_model_F4.csv', index=False)

a = rows('article1/altfrag/run/all.csv', 'alt_id same_object verdict_f4 first_year_f4 criterion quote_f4 file_f4'.split())
x = alt.merge(a, on='alt_id', how='left'); x['id'] = x.alt_id; x = reconcile(x, 'specificity')
ret = d.set_index('promise_id').verdict_f4
x.loc[x.retained == '1', 'verdict_f4'] = x.loc[x.retained == '1', 'promise_id'].map(ret)
x.loc[x.retained == '1', 'spec_f4'] = x.loc[x.retained == '1', 'promise_id'].map(d.set_index('promise_id').spec_f4)
x = x[x.promise_id.isin(d.promise_id)]
x.to_csv('data/alt_fragments_F4.csv', index=False)
print('F4 N', len(d), d.verdict_f4.value_counts().to_dict(), '| spec_f4', d.spec_f4.value_counts().to_dict(),
      '| spec adjudicated', (d.spec_f4_source == 'adjudicated').sum(), '| alt rows', len(x))
