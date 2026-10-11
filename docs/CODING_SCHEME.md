# Supplementary file S3. Coding scheme and outcome rules

This is an English translation of the fragment coding scheme (versions 0.1, 0.2, and 0.2.1), followed by the single outcome standard specified in the later audit protocol. Versioned rules are retained in their historical order. The validation procedure in v0.1 was a plan, not a claim that it was completed.

## Version 0.1 (30 September 2026): coding AI-related fragments

**Unit of coding.** A fragment is a sentence found by the AI-term dictionary, together with one sentence immediately before and one immediately after it.

### 1. AI relevance filter

| Code | Meaning |
|---|---|
| `0` | False positive: the text is not about artificial intelligence; for example, “AI” abbreviates something else. |
| `1` | The text is about artificial intelligence. |

### 2. Topic: assign one primary topic

| Code | Topic | Example (translated) |
|---|---|---|
| `STR` | Strategy, goals, priorities | “We are increasing our focus on AI technologies.” |
| `APP` | Application in the company's own operations | “AI models in credit scoring.” |
| `PRD` | AI in products and services for customers | “A virtual assistant based on our AI.” |
| `RSK` | Risks, regulation (including the AI Act), ethics | “Risks associated with AI.” |
| `GOV` | AI governance: policy, committee, roadmap, accountable parties | “An AI project roadmap approved by the board.” |
| `INV` | Investment, partnerships, purchase of solutions | “A partnership with a conversational-AI provider.” |
| `ENV` | External trends, market, industry | “AI is changing the healthcare industry.” |
| `HR` | Personnel, training, skills | “Courses on ‘ChatGPT as an everyday assistant.’” |

### 3. Specificity: primary dependent variable

| Code | Rule |
|---|---|
| `0` | General: no named process, deadline, result, or object. |
| `1` | Partly specific: a process or area of application is named, but no status, deadline, or result is given. |
| `2` | Specific: a process **and** at least one of the following are named: implementation status (pilot or implemented), deadline, quantitative result, amount, named solution, or named partner. |

### 4. Status (in v0.1, only for `APP`/`PRD`/`INV`)

`PLAN` = planned; `PILOT` = pilot; `LIVE` = implemented; `NA` = not stated.

### Report-level variables

| Variable | Definition |
|---|---|
| `ai_any` | At least one fragment has AI-relevance code `1`. |
| `ai_per_1000` | AI fragments per 1,000 sentences in the narrative portion of the report. |
| `ai_specific` | Number of fragments with specificity `2`. |
| `ai_depth` | Score from 0 to 8 across four dimensions (`STR`, `APP/PRD`, `RSK/GOV`, `INV`): `0` absent, `1` general, `2` specific in each dimension. |
| `ai_generic_share` | Share of fragments with specificity `0`; undefined when there are no fragments. **Do not call this “AI washing.”** |

### Validation plan recorded in v0.1

The plan called for two independent coders on a stratified subsample by country, year, and language (600–1,000 fragments), with random sentences not detected by the dictionary to assess recall. It called for language-specific precision and recall, Cohen's κ, and Gwet's AC1. Polish-language material was assigned to a Polish-language coder, Kazakhstan material in Russian or Kazakh to a coder responsible for those languages, and Netherlands material to a second coder. These are planned assignments, not evidence that validation was performed.

### Known technical problems recorded in v0.1

Using `pdftotext -layout` can merge columns and break sentences. For coding, the plan specified extraction without `-layout`, followed by new sentence segmentation. Report lengths vary substantially, so counts should be normalized.

## Version 0.2 (5 October 2026): fields for commitment outcomes and AI source

One row represents one fragment. Fields are separated by semicolons:

```text
fragment_id;is_ai;topic;specificity;status;promise;use_case;source;note
```

| Field | Coding rule |
|---|---|
| `is_ai` | `1` = about AI; `0` = false positive. |
| `topic` | `STR`, `APP`, `PRD`, `RSK`, `GOV`, `INV`, `ENV`, or `HR`, as defined in v0.1. |
| `specificity` | `0`, `1`, or `2`, as defined in v0.1. |
| `status` | What the company says about **its own AI**: `PLAN` = intention (“we plan,” “we will”); `PILOT` = test, pilot, or proof of concept; `LIVE` = implemented, used, or a result exists; `NA` = not about the company's own AI, such as a general trend, risk, or regulation. |
| `promise` | `yes` = a future commitment by the company concerning its own AI (`PLAN`, or `PILOT` with an intention to scale); otherwise `no`. |
| `use_case` | A short 2–5-word English label for year-to-year tracing, such as `credit scoring`, `customer chatbot`, `predictive maintenance`, `document processing`, `fraud detection`, `demand forecasting`, `code generation`, or `general AI strategy`. Use `NA` when `status=NA`. |
| `source` | For the separate AI-source analysis: `own` = in-house development or team; `external_dev` = commissioned development or modification by an external developer; `off_the_shelf` = ready-made commercial solution, such as Copilot or ChatGPT Enterprise; `partnership` = joint work with a partner, higher-education institution, or startup; `unclear`; `NA` = not about the company's own AI. |
| `note` | Up to 120 characters, with no semicolon. |

The v0.2 prospective follow-through rule for the commitment analysis was: a commitment for `(firm, use_case)` coded `PLAN` or `PILOT` in year *t* would be counted as fulfilled if, in *t*+1 through 2025, the same firm had a `LIVE` record with the same or a similar `use_case`. The later single outcome standard below superseded this simple panel-matching rule for the final outcome assessment; the v0.2 rule is retained here as part of the scheme's history.

## Version 0.2.1: clarifications after a 100-fragment pilot

- Glossaries, lists of abbreviations, tables of contents, and repeated headings without substantive content receive `is_ai=0`.
- Unreadable text caused by PDF encoding failure receives `is_ai=0`, with `garbled` in `note`.
- `specificity` measures only what is said about the **company's own AI**. A detailed account of a law such as the AI Act, or of a market trend, is no higher than `1`. A general intention to “invest in AI and analytics” without a named process is `1`, not `2`.
- `promise=yes` applies only to a company commitment to implement, use, or scale AI in its own operations or products. An intention to train a board or employees in AI skills is `topic=HR` or `GOV` and `promise=no`.

## Later single standard for commitment outcomes (superseded by Version F4 below)

This block documents the rule used in the two coding rounds. Its phrase "concrete work on the same object" proved ambiguous and is **superseded** for all final outcomes by the frozen rule in Version F4.

The following outcome rules translate the later audit protocol, with the `not_a_promise` eligibility category from the scheme's `promise` rule and the subsequent blind-coding prompts. The unit is the original commitment and its identifiable follow-through in available later company reports. Assess the same object, function, and **explicitly promised** scale; do not infer an unspecified deadline or scale.

| Outcome | Definition |
|---|---|
| `fulfilled` | A later report provides sufficient confirmation of the result for the original object, function, and explicitly promised scale. If the original commitment was to conduct a study or pilot, a corresponding completed study or pilot suffices; a full-scale launch need not be added as a requirement. |
| `partial` | A later report confirms only part of the functions or scale, an active pilot when deployment was promised, or concrete work on the same object. It requires identifiable progress, not simply a repeated intention. |
| `not_fulfilled` | The same object remains a plan or intention without an achieved result, or a decision not to proceed is reported. A future deadline does not by itself mean the company is overdue. |
| `dropped` | No identifiable continuation of the commitment is found in the available later reports examined. This means it cannot be traced in those reports; it is not synonymous with cancellation or proven failure. |
| `not_a_promise` | The original fragment is not a company commitment to implement, use, or scale AI in its own operations or products. Such a candidate is excluded from the final set of commitment outcomes. |

The protocol also uses `NA` when the material is insufficient or a report pair cannot support a decision; a missing document is not evidence of failure. A general AI strategy does not become `fulfilled` through a repeated strategic statement: at least one matching implemented process is needed, and any explicitly broader promised scale still applies. Development or a pilot is judged against what was originally promised, not against isolated uses of “AI” or the label `LIVE`. For potentially `dropped` cases, searches should use product, process, and partner names and spelling variants even without AI keywords; record the searched reports and expressions. A missing supporting quotation means that no sufficient evidence was found, not that cancellation was documented. The first year marked as fully fulfilled is not itself evidence of fulfillment.

## Version F4 (11 October 2026): frozen outcome rule applied to all commitments

Fixed in writing before any re-review output was seen and applied to all 184 retained commitments, including those on which the two earlier rounds had agreed. Core principle: an outcome above `not_fulfilled` requires evidence of an **achieved state** (launched, deployed, operating, in use, completed, rolled out, piloted in live operation) for the **same** promised object or function. Activity language alone (developing, working on, progressing towards, preparing, continuing development, planning, on track, positioned to deliver) never counts as achievement.

| Outcome | Definition |
|---|---|
| `fulfilled` | A later report states that the promised object or function is implemented, launched or in use at the explicitly promised scale. If the commitment was to run a study, pilot or test, its completion or live operation suffices. A broad general-AI commitment requires at least one named, implemented AI process within its scope; repeating the strategy is not enough. Scope or deadline absent from the original is not invented. |
| `partial` | Achieved-state evidence for the same object that is incomplete: a live pilot where full deployment was promised, some of the promised functions live, or a smaller scale, unit, market or product line. Continuing development, readiness work, expenditure or a repeated intention alone does not qualify. |
| `not_fulfilled` | The same object reappears only as ongoing work, development, testing without a live pilot, renewed plan, postponement or explicit cancellation. |
| `dropped` | No identifiable continuation located in the available later reports; not a synonym for cancellation. |
| `not_a_promise` | The original fragment is not a company undertaking to implement AI. Excluded. |

Deadlines are recorded separately; a future deadline is not a failure. The harmonisation review changed 12 of 184 outcomes; an author reviewed and approved each change against the quoted source passages. One record was excluded as `not_a_promise`, leaving 183 commitments (F4).

### Specificity rule (clarified, F4)

Unit: the wording of one commitment about the company's own AI; later reports are not used. **Specific (2)** = a concrete AI process, function, product or area is named **and** at least one of the following is stated: a current achieved stage (a pilot or test already running, or a solution already implemented that is to be extended; a future intention to implement or develop is not a stage), a deadline or time frame, a quantitative target or result, an investment amount, a named AI solution, product, platform or model, or a named external partner, vendor or institution. **Partly specific (1)** = otherwise. Components are recorded separately as 0/1 indicators (`proc`, `stage`, `deadline`, `result`, `amount`, `solution`, `partner`).

Procedure: the original code and a blind recoding by a second model (from the wording only) were compared; 131/183 agreed (71.6%; Cohen's κ = 0.43). The 52 disagreements were resolved by a third model applying the clarified rule above, seeing only the wording.

### Alternative fragments

For each firm–category–year key with several eligible commitment fragments, every alternative fragment was coded for whether it describes the same promised object as the retained fragment and for its own outcome under the F4 rule. These codes support the robustness checks only.

### Disclosure content of continued commitments

For commitments coded `not_fulfilled`, the latest later report mentioning the object was classified as: `repeated_intention` (plan restated without progress information); `ongoing_development` (development, testing or preparation under way, no launch); `explained_revision` (postponement, changed scope, new timeline or reprioritisation with a reason or new date); `explained_closure` (stopped, cancelled or abandoned); `other`.
