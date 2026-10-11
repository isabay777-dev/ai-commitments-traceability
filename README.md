# Tracing public AI commitments in corporate annual reports (Kazakhstan, Poland, the Netherlands, 2021–2025)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23296700.svg)](https://doi.org/10.5281/zenodo.23296700)

Archived on Zenodo. All versions: https://doi.org/10.5281/zenodo.23296699 (concept DOI, resolves to the latest version). Version v1.0.0: https://doi.org/10.5281/zenodo.23296700.

Replication materials for the manuscript *Tracing public AI commitments in corporate annual reports: evidence from Kazakhstan, Poland and the Netherlands* (under review).

## Versions

| Version | Dataset | Records | What changed |
|---|---|---|---|
| v1.1.0 (current) | **F4** `data/promise_model_F4.csv` (= `data/coded/commitments_final.csv`) | 183 | One frozen outcome rule reapplied to all commitments (12 changes, author-approved; one non-commitment excluded); reconciled specificity (original + blind recoding + adjudication); alternative-fragment robustness; disclosure content of continued commitments |
| v1.0.0 | F3 `data/promise_model_F3.csv` (= `data/coded/commitments_F3.csv`) | 184 | Two coding rounds, third-model adjudication of 58 disagreements |

## Reproduce the results (F4)

Requirements: Python ≥ 3.9 with pandas, numpy, matplotlib; R ≥ 4.3 with fixest. From the repository root:

```sh
python3 scripts/41_build_F4.py          # builds data/promise_model_F4.csv and data/alt_fragments_F4.csv from the coded inputs
Rscript scripts/42_models_F4.R          # all models -> results/promise_models_F4.txt, results/models_coefficients_F4.csv
python3 scripts/43_tables_F4.py         # Tables 1-4, Figure 1 -> article1/tables_F4/
python3 scripts/44_supplement_S4.py     # Supplementary S4 -> article1/tables_F4/Supplementary_S4.md
```

`results/` and `article1/tables_F4/` are created by the scripts. The bootstrap seed is fixed (20261011).

## Contents

| Path | What |
|---|---|
| `data/promise_model_F4.csv` | Final dataset: 183 commitments with F4 outcome (`verdict_f4`), evidence quote and file, F3 outcome, original/blind/reconciled specificity and its components, sector, corporate group, episode, board and firm variables |
| `data/alt_fragments_F4.csv` | All eligible fragments in each firm–category–year key, with same-object flag, F4 outcome and specificity (robustness) |
| `data/continued_disclosure_content_F4.csv` | Disclosure content of the 39 continued (`not_fulfilled`) commitments |
| `article1/harmonise/` | Frozen rule `PROTOCOL_F4.md` and harmonisation review output (`run/all.csv`) |
| `article1/specrecode/` | Clarified specificity rule, blind recoding (`run/all.csv`) and adjudication of disagreements (`adj/all.csv`) |
| `article1/altfrag/`, `article1/explain/` | Coding of alternative fragments; coding of disclosure content |
| `article1/analysis_B/episode_outcomes.csv` | Episode and corporate-group mapping |
| `article1/tables_F3/Table_4.md` | Historical next-year diagnostic reproduced in Supplementary S4 |
| `data/coded/unified_recoding.csv`, `third_adjudicator_decisions.csv` | Second (blind) coding round of 190 records and third-model adjudication of 58 disagreements (F3 stage) |
| `data/coded/main_coded.csv`, `pilot_coded.csv` | Coding of 4,672 AI-related text fragments |
| `data/coded/ai_fragments_index.csv` | Fragment identifiers, country, year and a short excerpt (≤300 characters) |
| `data/coded/report_panel_ai_mentions.csv` | Report-level panel (1,098 reports) |
| `data/coded/kz_pl_firm_panel.csv` | Kazakhstan and Poland firm-year panel (board counts, verified digital expertise counts, ownership, size, sector) |
| `data/sources/` | Report URLs (Kazakhstan, Poland) and ESEF filings index (filings.xbrl.org) |
| `scripts/` | Retrieval, extraction, dictionary, coding runs, models and tables. Scripts 01–39 document earlier stages; 40–44 are the F4 pipeline. |
| `prompts/` | Prompts for all AI-assisted coding, review and drafting stages |
| `docs/CODING_SCHEME.md` | Coding rules v0.1–v0.2.1 and the final F4 rules |
| `docs/AI_USE_REGISTRY.md` | Registry of AI-tool use: stage, model, prompt, inputs, outputs, dates, human checks (`AI_USE_REGISTRY.csv` covers stages up to F3) |
| `tables/` | F3 exhibits (v1.0.0) |

## Not included

- Full texts of annual reports (copyright of the issuers); they are publicly available at the listed URLs. Scripts that read report texts or full fragments (e.g. `40_alt_fragments.py`, the Codex coding runs) therefore cannot be rerun from this package; their outputs are included.
- Names of individual board members (personal data); only counts are released.

## AI use

Large language models (OpenAI gpt-6-astra, gpt-6-sol and gpt-6-luna via Codex CLI; Anthropic Claude Opus 5.5) performed retrieval, extraction, coding, outcome assessment and adjudication under written rules, wrote analysis code and drafted the manuscript, under the authors' supervision. An author reviewed and approved all 58 adjudicated decisions and all 12 changes from the F4 harmonisation review. See `docs/AI_USE_REGISTRY.md`.

## Licence

Data and documentation: CC BY 4.0. Code: MIT.
