"""F5 exhibits: Tables 1-4, Figure 1 and supplementary model catalogue.
Inputs: data/promise_model_F5.csv, results/models_coefficients_F5.csv (from scripts/46_models_F5.R).
Usage (from repository root): python3 scripts/43_tables_F4.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT = Path('article1/tables_F5'); OUT.mkdir(parents=True, exist_ok=True)
d = pd.read_csv('data/promise_model_F5.csv'); assert d.verdict_version.eq("F5").all()
e = pd.read_csv('results/models_coefficients_F5.csv')
C = ['KZ', 'PL', 'NL']; LEVELS = ['fulfilled', 'partial', 'not_fulfilled', 'dropped']
LAB = {'fulfilled': 'Full confirmation', 'partial': 'Partial confirmation',
       'not_fulfilled': 'Continued disclosure without sufficient confirmation', 'dropped': 'Untraced follow-up'}
def ratio(n, N): return f'{int(n)}/{int(N)} ({100*n/N:.1f}%)'
def md(df): return '| ' + ' | '.join(df.columns) + ' |\n| ' + ' | '.join('---' for _ in df.columns) + ' |\n' + '\n'.join('| ' + ' | '.join(str(v) for v in r) + ' |' for r in df.values)
def coef(model, term):
    r = e[(e.model == model) & (e.term == term)].iloc[0]; return r
def fmt(model, term):
    r = coef(model, term); return f'{100*r.estimate:.1f} ({100*r.se:.1f})', f'{r.p_value:.3f}', int(r.N)
groups = lambda q: q.firm.nunique()

# Table 1
rows = []
def row(panel, name, f):
    rows.append([panel, name] + [f(d[d.country == c]) for c in C] + [f(d)])
row('A', 'Commitment records', len); row('A', 'Legal entities', groups)
row('A', 'Specific (specificity 2)', lambda q: ratio((q.spec_final == 2).sum(), len(q)))
row('A', 'Deadline stated', lambda q: ratio((q.deadline == 1).sum(), len(q)))
row('A', 'Quantitative target stated', lambda q: ratio((q.result == 1).sum(), len(q)))
row('A', 'Named solution or partner', lambda q: ratio(q.spec_identify.sum(), len(q)))
for lv in LEVELS: row('B', LAB[lv], lambda q, lv=lv: ratio((q.verdict_final == lv).sum(), len(q)))
row('B', 'Full or partial (combined summary)', lambda q: ratio(q.fulfilled_or_partial.sum(), len(q)))
t1 = pd.DataFrame(rows, columns=['Panel', 'Measure'] + C + ['Total'])
from sklearn.metrics import cohen_kappa_score as kap
K = {c: (int(((d.spec_final == 2) == (d[c] == 2)).sum()), round(kap(d.spec_final == 2, d[c] == 2), 2)) for c in ['specificity_original', 'spec_sol', 'spec_f4_reconciled']}
note1 = (f'KZ = Kazakhstan; PL = Poland; NL = the Netherlands. Panel A components and specificity come from one recoding of the wording of every commitment under the clarified written rule (Supplementary S3); the category equals the stated conjunction of components. Panel B contains four mutually exclusive F5 outcomes under one frozen evidential rule, after an audit requiring evidence of the AI function itself, and a separate combined summary. Outcomes concern corporate self-reports over unequal horizons. Rounding can prevent percentages from summing to 100. Source: F5.')

# Table 2
rng = np.random.default_rng(20261011)
def diff(q): return q[q.spec_final == 2].fulfilled.mean() - q[q.spec_final == 1].fulfilled.mean()
firms = {c: d[d.country == c].firm.unique() for c in C}; byf = {k: g for k, g in d.groupby(['country', 'firm'])}
bs = []
for _ in range(10000):
    q = pd.concat([byf[(c, f)] for c in C for f in rng.choice(firms[c], len(firms[c]), replace=True)])
    if q.spec_final.nunique() == 2: bs.append(diff(q))
lo, hi = np.percentile(bs, [2.5, 97.5])
kp = []
for _ in range(10000):
    q = pd.concat([byf[(c, f)] for c in ['KZ', 'PL'] for f in rng.choice(firms[c], len(firms[c]), replace=True)])
    kp.append(q[q.country == 'KZ'].fulfilled.mean() - q[q.country == 'PL'].fulfilled.mean())
kp_ci = np.percentile(kp, [2.5, 97.5])
pa = []
for lab, col in [('Uniform rule (main)', 'spec_final'), ('Original coding', 'specificity_original'), ('Blind recoding', 'spec_sol'), ('F4 reconciled', 'spec_f4_reconciled')]:
    for s in (1, 2):
        q = d[(d[col] == 2) == (s == 2)]
        pa.append([lab, s, len(q), ratio(q.fulfilled.sum(), len(q)), ratio(q.fulfilled_or_partial.sum(), len(q)), ratio(q.dropped.sum(), len(q))])
t2a = pd.DataFrame(pa, columns=['Specificity coding', 'Specificity', 'N', 'Full', 'Full or partial', 'Untraced'])
spec_rows = [('m2', 'spec2', 'Full', 'Baseline controls'), ('m2f', 'spec2', 'Full', '+ financial sector'),
             ('m3f', 'spec2', 'Full or partial', '+ financial sector'), ('md', 'spec2', 'Untraced', '+ financial sector'),
             ('m4', 'spec2', 'Full (logit, log-odds x100)', '+ financial sector'),
             ('m2f_grp', 'spec2', 'Full', 'SEs clustered by corporate group'),
             ('m2_orig', 'spec2_orig', 'Full', 'Original specificity coding'), ('m2_sol', 'spec2_sol', 'Full', 'Blind specificity recoding'), ('m2_rec', 'spec2_rec', 'Full', 'F4 reconciled specificity'),
             ('alt_max', 'spec2', 'Full', 'Most specific fragment per key'), ('alt_min', 'spec2', 'Full', 'Least specific fragment per key'),
             ('alt_all', 'spec2', 'Full', 'All distinct promised objects')]
pb = [['Specific minus partly specific, raw', 'Full', f'{len(d)}/{groups(d)}', f'{100*diff(d):.1f}; 95% CI [{100*lo:.1f}, {100*hi:.1f}]', '']]
for m, t, y, lab in spec_rows:
    est, p, N = fmt(m, t); pb.append([f'{m}: {lab}', y, N, est, p])
t2b = pd.DataFrame(pb, columns=['Specification', 'Outcome', 'N', 'Estimate, pp (SE)', 'p'])
t2b['p'] = t2b['p'].replace({'0.000': '<0.001'})
comp = pd.DataFrame([[t, *fmt('m2_comp', v)[:2]] for t, v in [('Named AI process', 'proc_n'), ('Named solution or partner', 'spec_identify'),
     ('Deadline, target or amount', 'spec_evaluable'), ('Current stage stated', 'stage_n')]], columns=['Component (m2_comp)', 'Estimate, pp (SE)', 'p'])
alt = pd.read_csv('data/alt_fragments_F5.csv'); nk = int(alt.groupby('promise_id').size().gt(1).sum())
nx = int(((alt.retained == 0) & (alt.same_object == 'no') & alt.verdict_final.isin(LEVELS)).sum())
note2 = (f'N = commitment records. Linear probability coefficients x100 with firm-clustered SEs unless stated; all models include country, initial pilot status, general category, number of later reports and year effects. The raw difference uses 10,000 whole-firm bootstrap resamples within countries (seed 20261011) and excludes coding uncertainty. Alternative-fragment rows replace the retained fragment in the {nk} firm-category-year keys with several eligible fragments; the all-distinct row adds {nx} alternative fragments describing a different promised object. Component estimates enter jointly. p-values are unadjusted and exploratory. Source: F5; full model catalogue in Supplementary S4.')

# Table 3: sector, records and episodes (earliest-year anchor; ties resolved by the most frequent outcome, then by ID order)
ep = []
for eid, q in d.groupby('episode_id'):
    a = q[q.year == q.year.min()].sort_values('promise_id')
    ep.append(dict(episode_id=eid, country=q.country.iloc[0], firm_group=q.firm_group.iloc[0], finance=q.finance.iloc[0],
                   full=int(a.verdict_final.mode().iloc[0] == 'fulfilled'), conflict=int(a.verdict_final.nunique() > 1)))
ep = pd.DataFrame(ep)
r3 = []
for c in C:
    for fin, lab in [(1, 'finance'), (0, 'non-finance'), (None, 'all')]:
        q = d[(d.country == c) & ((d.finance == fin) if fin is not None else True)]
        qe = ep[(ep.country == c) & ((ep.finance == fin) if fin is not None else True)]
        gw = qe.groupby('firm_group').full.mean()
        r3.append([f'{c} / {lab}', ratio(q.fulfilled.sum(), len(q)), ratio(qe.full.sum(), len(qe)), f'{100*gw.mean():.1f}', len(gw)])
t3 = pd.DataFrame(r3, columns=['Country / sector', 'Records, full', 'Episodes, full', 'Equal group weights (%)', 'Groups'])
note3 = (f'Episodes merge repeated statements of the same undertaking by the same group ({len(ep)} episodes, {d.firm_group.nunique()} corporate groups from {groups(d)} legal entities); each episode takes the F5 outcome of its earliest commitment ({int(ep.conflict.sum())} same-year anchor conflicts resolved by the modal outcome). Equal-group estimates average episodes within groups, then groups. Sector contrasts are descriptive. Source: F5.')

# Table 4: governance (secondary)
g = d.copy(); g['dig_any'] = (pd.to_numeric(g.dig, errors='coerce') > 0); g['dig_nar'] = (pd.to_numeric(g.dig_narrow, errors='coerce') > 0)
g = g[pd.to_numeric(g.dig, errors='coerce').notna() & pd.to_numeric(g.log_assets, errors='coerce').notna() & g.state.notna()]
r4 = []
for m, t, lab in [('g1', 'dig_any', 'Broad expertise, country/year only'), ('g2', 'dig_any', 'Broad expertise, + controls'),
                  ('g2f', 'dig_any', 'Broad expertise, + controls + finance'), ('g5', 'dig_nar', 'Narrow expertise, + controls'),
                  ('g5f', 'dig_nar', 'Narrow expertise, + controls + finance')]:
    est, p, N = fmt(m, t); r4.append([m, lab, est, p, N])
t4 = pd.DataFrame(r4, columns=['Model', 'Indicator and specification', 'Estimate, pp (SE)', 'p', 'N'])
nar = g[g.dig_nar]
import re
lv = [100*float(x) for x in re.findall(r'^\S+ \S+ (-?[0-9.]+) *$', open('results/promise_models_F5.txt').read().split('Leave-one-exposed-firm-out')[1].split('R version')[0], re.M)]
loo = (min(lv), max(lv))
note4 = (f'Secondary, exploratory analysis on one common sample of {len(g)} commitments from {g.firm.nunique()} firms with expertise, assets and state-affiliation data; all models use the same observations. Broad expertise is present for {int(g.dig_any.sum())} commitments; narrow expertise for {len(nar)} commitments from {nar.firm.nunique()} firms, none in finance. Controls: country, specificity, general category, within-country standardised log assets, state affiliation and year effects; SEs clustered by firm. Leave-one-exposed-firm-out estimates for g5f range from {loo[0]:.1f} to {loo[1]:.1f} pp. Board biographies were not dated against commitment years. Source: F5 and board data.')
blocks = [(1, 'Commitment wording and observed outcomes', md(t1), note1),
          (2, 'Specificity and reported confirmation: robustness', '#### Panel A. Outcome profiles\n\n' + md(t2a) + '\n\n#### Panel B. Specific minus partly specific commitments\n\n' + md(t2b) + '\n\n#### Panel C. Specificity components\n\n' + md(comp), note2),
          (3, 'Financial sector and alternative counting units', md(t3), note3),
          (4, 'Board digital expertise (secondary analysis)', md(t4), note4)]
tables = ''
for n_, title, body, note in blocks:
    b = f'### Table {n_}. {title}\n\n{body}\n\nNotes: {note}\n'; (OUT / f'Table_{n_}.md').write_text(b); tables += b + '\n'
(OUT / 'Tables_1_4.md').write_text(tables)
for name, df in [('Table_1', t1), ('Table_2_A', t2a), ('Table_2_B', t2b), ('Table_2_C', comp), ('Table_3', t3), ('Table_4', t4)]: df.to_csv(OUT / f'{name}.csv', index=False)
e.assign(estimate_pp=100*e.estimate, se_pp=100*e.se).to_csv(OUT / 'Supplementary_Table_S4_model_catalogue.csv', index=False)

# Figure 1
fd = pd.crosstab(d.spec_final, d.verdict_final).reindex(index=[1, 2], columns=LEVELS).fillna(0).astype(int); fd.to_csv(OUT / 'Figure_1_data.csv')
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'savefig.facecolor': 'white', 'pdf.fonttype': 42})
fig, ax = plt.subplots(figsize=(9, 4.4)); left = [0., 0.]; den = fd.sum(axis=1).tolist()
labels = ['Full confirmation', 'Partial confirmation', 'Continued disclosure without\nsufficient confirmation', 'Untraced follow-up']
for j, (lv, lab, col, h) in enumerate(zip(LEVELS, labels, ['0.2', '0.58', '0.88', 'white'], ['', '///', '...', 'xxx'])):
    v = fd[lv].tolist(); w = [100*n/N for n, N in zip(v, den)]
    ax.barh([0, 1], w, left=left, color=col, edgecolor='black', hatch=h, height=.48, label=lab, linewidth=.7)
    for i, (n, wi) in enumerate(zip(v, w)):
        if wi < 6: ax.annotate(str(n), (left[i]+wi/2, i), xytext=(102, i), ha='left', va='center', arrowprops={'arrowstyle': '-'}, annotation_clip=False)
        else: ax.text(left[i]+wi/2, i, str(n), ha='center', va='center', color='white' if j == 0 else 'black', bbox=dict(facecolor=col, edgecolor='none', pad=1))
    left = [l+wi for l, wi in zip(left, w)]
ax.set(xlim=(0, 100), ylim=(1.6, -.6), yticks=[0, 1], yticklabels=[f'Partly specific\nN = {den[0]}', f'Specific\nN = {den[1]}'], xlabel='Share of commitment records (%)')
ax.spines[['top', 'right']].set_visible(False); ax.legend(loc='upper center', bbox_to_anchor=(.46, -.25), ncol=2, frameon=False, fontsize=9)
fig.subplots_adjust(left=.19, right=.93, bottom=.36, top=.97)
for ext in ['png', 'pdf']: fig.savefig(OUT / f'Figure_1_specificity.{ext}', dpi=600)
plt.close(fig)
v = dict(records=len(d), firms=groups(d), groups=int(d.firm_group.nunique()), episodes=len(ep), outcomes=d.verdict_final.value_counts().to_dict(),
         spec_final=d.spec_final.value_counts().to_dict(), raw_diff=round(100*diff(d), 2), ci=[round(100*lo, 2), round(100*hi, 2)],
         bootstrap_valid=len(bs), kz_minus_pl=round(100*(d[d.country=='KZ'].fulfilled.mean()-d[d.country=='PL'].fulfilled.mean()),2), kz_pl_ci=[round(100*x,1) for x in kp_ci], spec_agreement_with_main=K, figure=fd.to_dict(), python=sys.version.split()[0], pandas=pd.__version__)
(OUT / 'validation_F5.json').write_text(json.dumps(v, indent=2, ensure_ascii=False, default=int) + '\n'); print(json.dumps(v, default=int))
