# Tracing public AI commitments in corporate annual reports (Kazakhstan, Poland, the Netherlands, 2021–2025)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23296700.svg)](https://doi.org/10.5281/zenodo.23296700)

**Current version: v1.2.0 (dataset F5).** Archived on Zenodo; the concept DOI https://doi.org/10.5281/zenodo.23296699 always resolves to the latest version. Earlier versions: v1.1.0 (F4) https://doi.org/10.5281/zenodo.23298731; v1.0.0 (F3) https://doi.org/10.5281/zenodo.23296700.

Replication materials for the manuscript *Tracing public AI commitments in corporate annual reports: evidence from Kazakhstan, Poland and the Netherlands* (under review).

## Versions

| Version | Dataset | Records | What changed |
|---|---|---|---|
| **v1.2.0 (current)** | **F5** `data/promise_model_F5.csv` (= `data/coded/commitments_final.csv`) | 183 | AI-function audit of all confirmations (4 author-approved downgrades); specificity recoded for all fragments under one clarified rule (`spec_final`); second independent coding of disclosure content; firm-cluster bootstrap for country contrasts |
| v1.1.0 | F4 `data/promise_model_F4.csv` (= `data/coded/commitments_F4.csv`) | 183 | Frozen outcome rule reapplied to all commitments (12 author-approved changes); reconciled specificity; alternative-fragment robustness |
| v1.0.0 | F3 `data/promise_model_F3.csv` (= `data/coded/commitments_F3.csv`) | 184 | Two coding rounds and third-model adjudication |

## Reproduce the results (F5)

Requirements: Python ≥ 3.9 with pandas, numpy, matplotlib, scikit-learn; R ≥ 4.3 with fixest. From the repository root:

```sh
python3 scripts/41_build_F4.py            # F4 from F3 and the harmonisation outputs
python3 scripts/45_build_F5.py            # F5 from F4, the AI-function audit and the uniform specificity coding
Rscript scripts/46_models_F5.R            # all models -> results/promise_models_F5.txt, results/models_coefficients_F5.csv
python3 scripts/47_tables_F5.py           # Tables 1-4, Figure 1 -> article1/tables_F5/
python3 scripts/48_supplement_S4_F5.py    # Supplementary S4 -> article1/tables_F5/Supplementary_S4.md
```

`results/` and `article1/tables_F5/` are created by the scripts; bootstrap seeds are fixed (20261011). Scripts 42–44 reproduce the F4 exhibits of v1.1.0.

## Contents


| Path | What |
|---|---|
| `data/promise_model_F5.csv` | Final dataset: 183 commitments with F5 outcome (`verdict_final`), F4 and F3 outcomes, AI-function audit decision, uniform specificity (`spec_final`) and its components, earlier specificity codings, sector, corporate group, episode, board and firm variables |
| `data/promise_model_F4.csv` | F4 dataset: 183 commitments with F4 outcome (`verdict_f4`), evidence quote and file, F3 outcome, original/blind/reconciled specificity and its components, sector, corporate group, episode, board and firm variables |
| `data/alt_fragments_F4.csv` | All eligible fragments in each firm–category–year key, with same-object flag, F4 outcome and specificity (robustness) |
| `data/continued_disclosure_content_F5.csv` | Disclosure content of the 41 continued commitments, two independent model codings |
| `article1/round5/` | AI-function audit (`fn/`), uniform specificity coding (`spec/`) and second content coding (`expl/`) |
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
| `scripts/` | Retrieval, extraction, dictionary, coding runs, models and tables. Scripts 01–39 document earlier stages; 40–44 are the F4 pipeline; 45–48 the F5 pipeline. |
| `prompts/` | Prompts for all AI-assisted coding, review and drafting stages |
| `docs/CODING_SCHEME.md` | Coding rules v0.1–v0.2.1 and the final F4 rules |
| `docs/AI_USE_REGISTRY.md` | Registry of AI-tool use: stage, model, prompt, inputs, outputs, dates, human checks (`AI_USE_REGISTRY.csv` covers stages up to F3) |
| `tables/` | F3 exhibits (v1.0.0) |

## v1.3.0 — Post-Communist Economies version (`pce_version/`)

Materials for "Corporate AI commitments in annual reports: follow-up disclosure in Kazakhstan and Poland". The F5 data in `data/` are unchanged.

| Path | Contents |
|---|---|
| `pce_version/analysis/` | `final_analysis.R` (Tables 1–4, Figure 1, Kazakhstan–Poland contrasts and sensitivities, report-panel models), `selection_flow.py`, `build_selection_ledger.py` (213-key ledger), first-report scripts (`prepare_first_followup.py` … `first_followup_focal_models.R`, `build_first_report_supplement.py`), `make_S5.py`; outputs in `out/` |
| `pce_version/first_followup_rounds/`, `first_followup_adjudication/` | Frozen model coding rounds and source adjudication (rationales, quote pairs) for the first-available-report exercise |
| `pce_version/sources_first_followup/` | Retrieval, recovery, readability and ESEF manifests (URLs, hashes). Full report texts are not redistributed |
| `pce_version/research/` | First-report protocol, its SHA256, documented deviations and analysis decisions |
| `pce_version/work/` | Supplementary S2 (AI-use registry), S4 and S5 as Markdown |
| `pce_version/validation/`, `validation_first_report/` | Blind human-coding kits (legacy 76-case F5 kit; 183 source-only first-report cards). Answer keys are withheld; no human coding results are included |

`pce_version/repo` is a symbolic link to the repository root, so scripts can be run from `pce_version/` (e.g. `cd pce_version/analysis && Rscript final_analysis.R`). The first-report scripts that read report texts cannot be rerun without the source files; their outputs and hashes are included.

## Not included

- Full texts of annual reports (copyright of the issuers); they are publicly available at the listed URLs. Scripts that read report texts or full fragments (e.g. `40_alt_fragments.py`, the Codex coding runs) therefore cannot be rerun from this package; their outputs are included.
- Names of individual board members (personal data); only counts are released.

## AI use

Large language models (OpenAI gpt-6-astra, gpt-6-sol and gpt-6-luna via Codex CLI; Anthropic Claude Opus 5.5) performed retrieval, extraction, coding, outcome assessment and adjudication under written rules, wrote analysis code and drafted the manuscript, under the authors' supervision. An author reviewed and approved all 58 adjudicated decisions and all 16 outcome changes from the F4 harmonisation review and the F5 AI-function audit. See `docs/AI_USE_REGISTRY.md`.

## Licence

Data and documentation: CC BY 4.0. Code: MIT.
