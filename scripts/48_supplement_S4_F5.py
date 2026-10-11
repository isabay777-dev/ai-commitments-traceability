"""Supplementary file S4: full model catalogue, disclosure content of continued commitments, historical t+1 diagnostic.
Usage (from repository root): python3 scripts/44_supplement_S4.py"""
import pandas as pd
from pathlib import Path
OUT = Path('article1/tables_F5')
e = pd.read_csv('results/models_coefficients_F5.csv')
d = pd.read_csv('data/promise_model_F5.csv')
x = pd.read_csv('data/continued_disclosure_content_F5.csv').merge(d[['promise_id', 'country']], on='promise_id')
def md(df): return '| ' + ' | '.join(df.columns) + ' |\n| ' + ' | '.join('---' for _ in df.columns) + ' |\n' + '\n'.join('| ' + ' | '.join(str(v) for v in r) + ' |' for r in df.values)
desc = {'m1': 'Full ~ country, year FE', 'm2': 'Full ~ spec2 + controls', 'm2f': 'Full ~ spec2 + finance + controls',
        'm3': 'Full or partial ~ spec2 + controls', 'm3f': 'Full or partial ~ spec2 + finance + controls',
        'm4': 'Full, logit (log-odds) ~ spec2 + finance + controls', 'md': 'Untraced ~ spec2 + finance + controls',
        'm2_orig': 'Full ~ original specificity + finance + controls', 'm2_sol': 'Full ~ blind specificity + finance + controls', 'm2_rec': 'Full ~ F4 reconciled specificity + finance + controls',
        'm2_comp': 'Full ~ specificity components + finance + controls', 'm2f_grp': 'As m2f, SEs clustered by corporate group',
        'alt_max': 'As m2f, most specific fragment per key', 'alt_min': 'As m2f, least specific fragment per key',
        'alt_all': 'As m2f, all distinct promised objects', 'g1': 'Full ~ broad expertise + country, year FE',
        'g2': 'Full ~ broad expertise + governance controls', 'g2f': 'g2 + finance', 'g3f': 'Full or partial ~ broad expertise + governance controls + finance',
        'g5': 'Full ~ narrow expertise + governance controls', 'g5f': 'g5 + finance', 'g6f': 'Untraced ~ broad expertise + governance controls + finance'}
e = e[~e.term.str.startswith('year')]
t = pd.DataFrame({'Model': e.model, 'Specification': e.model.map(desc), 'Term': e.term, 'Estimate x100 (logit m4: log-odds x100)': (100*e.estimate).round(1),
                  'SE x100': (100*e.se).round(1), 'p': [('<0.001' if v < 0.001 else f'{v:.3f}') for v in e.p_value], 'N': e.N})
ct = pd.crosstab(x.disclosure_content, x.country, margins=True, margins_name='Total').reset_index().rename(columns={'disclosure_content': 'Latest disclosure of the object'})
t1 = open('article1/tables_F3/Table_4.md').read().split('#### Panel B')[0].split('#### Panel A. Historical next-reporting-year audit on retained F3 IDs')[1].strip()
txt = f"""# Supplementary file S4. Model catalogue, disclosure content and historical next-year diagnostic

## Table S4.1. All estimated specifications (F5)

Controls in m-models: country, initial pilot status, general-AI category, number of later reports and commitment-year fixed effects. Governance controls: country, reconciled specificity, general category, within-country standardised log assets, state affiliation and year effects, on one common sample of 123 commitments. Linear probability coefficients x100 unless stated; SEs clustered by legal entity unless stated. p-values are unadjusted and exploratory; this catalogue lists every specification estimated in the F5 analysis. Year fixed effects are omitted from the table.

{md(t)}

## Table S4.2. Disclosure content of the 39 continued commitments

{md(ct)}

Notes: Classification of the latest later report mentioning the object under the categories in Supplementary S3, by a first model (shown) and independently by a second model that did not see the first coding or the evidence file. The two codings agree on {int((x.disclosure_content == x.content_coder2).sum())} of {len(x)} cases. An explanation (reason or new date) was identified in {int((x.explanation_given == 'yes').sum())} cases by the first and {int((x.explanation_coder2 == 'yes').sum())} by the second coding. Neither identified an explicit discontinuation statement. Not human-checked.

## Table S4.3. Historical next-reporting-year diagnostic (pre-F3 labels, retained IDs)

{t1}

Notes: This diagnostic retains year-specific labels from an earlier temporal audit; they were not recoded under the F3, F4 or F5 rules, and eight records labelled full at t+1 were partial in F3. It is reported as methodological history, not as a robustness check of F5. Confidence intervals use 50,000 whole-firm resamples within country; missing-data bounds are extreme scenarios.
"""
(OUT / 'Supplementary_S4.md').write_text(txt); print(len(t), 'rows;', ct.to_dict())
