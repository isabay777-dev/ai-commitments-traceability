# Tracing public AI commitments in corporate annual reports (Kazakhstan, Poland, the Netherlands, 2021–2025)

Replication materials for the manuscript *Tracing public AI commitments in corporate annual reports: evidence from Kazakhstan, Poland and the Netherlands* (under review).

## Contents

| Folder | What |
|---|---|
| `data/coded/commitments_final.csv` | 190 AI commitments with final outcome (`verdict_final`), first full-confirmation year, specificity, category, firm characteristics |
| `data/coded/unified_recoding.csv` | Blind single-standard recoding of all 190 commitments: `ID;criterion;outcome;first_year;quote;file;note` |
| `data/coded/main_coded.csv`, `pilot_coded.csv` | Coding of 4,672 AI-related text fragments: `fragment_id;is_ai;topic;specificity;status;promise;use_case;source;note` |
| `data/coded/ai_fragments_index.csv` | Fragment identifiers, country, year and a short excerpt (≤300 characters) |
| `data/coded/report_panel_ai_mentions.csv` | Report-level panel (1,098 reports): AI mention counts and text length |
| `data/coded/kz_pl_firm_panel.csv` | Kazakhstan and Poland firm-year panel: board size, independent directors, verified board digital expertise (counts only), state ownership, size, sector |
| `data/sources/` | Source lists: URLs of annual reports (Kazakhstan, Poland) and ESEF filings index (filings.xbrl.org) |
| `scripts/` | Python, R and shell scripts for retrieval, text extraction, AI dictionary, coding runs, models and tables |
| `prompts/` | Prompts used for AI-assisted coding, verification and drafting |
| `docs/CODING_SCHEME.md` | Coding rules (v0.1–v0.2.1) |
| `docs/AI_USE_REGISTRY.*` | Registry of AI-tool use: stage, model, prompt, inputs, outputs, dates, human checks |
| `tables/` | Tables 1–4, Figure 1 and Supplementary Figure S1 |

## Not included

- Full texts of annual reports (copyright of the issuers); they are publicly available at the listed URLs.
- Names of individual board members (personal data); only counts are released.

## AI use

Large language models (OpenAI GPT-6 Astra, Sol and Luna via Codex CLI; Anthropic Claude) were used for report retrieval, extraction, coding of text fragments, assessment of commitment outcomes, code assistance and drafting support, under the authors' supervision. See `docs/AI_USE_REGISTRY.md`. Final outcome decisions on disputed cases and a verification sample were made by the authors.

## Licence

Data and documentation: CC BY 4.0. Code: MIT.
