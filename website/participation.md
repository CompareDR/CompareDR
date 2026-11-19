# Evaluate a new system with CompareDR

CompareDR compares complete research **systems**: a model together with its
research harness. The current leaderboard is a frozen nine-system, 40-query
snapshot, not an open service that accepts a self-reported total score.

**[Submit through the GitHub form](https://github.com/CompareDR/CompareDR/issues/new?template=submit-system.yml)**.
The leaderboard's participation section provides a downloadable ZIP template,
the complete package-format guide, and an offline validation tool.

The public GitHub issue form is the submission entry point. Sign in to GitHub
to submit a reproducible report package for maintainer-coordinated evaluation.
The form collects packages for maintainer review, not automatic judging.

## 1. Generate reports

- Use the 40 original query strings and IDs supplied with the benchmark. Preserve
  their language, time constraints, source restrictions, and other requirements.
- Generate one complete report per query. Preserve headings, tables, formulas,
  references, and external citation links; do not replace reports with summaries.
- Record the model identifier, research harness, exposed reasoning setting,
  generation dates, and any other material configuration. Report unavailable
  settings as undisclosed, rather than guessing them.
- Report failures and missing tasks explicitly. A partial collection is not a
  complete leaderboard entry; do not omit difficult queries or fabricate outputs.

The website's data download includes the queries and selected criterion examples.
The repository's `data/evaluation/main9/` directory contains the complete frozen
evaluation inputs. Do not supply evaluation answer keys to the generation system.

## 2. Assemble an intake package

Provide report files plus a manifest with these fields:

| Level | Required information |
|---|---|
| System | Display name, model, harness, generation settings, generation date range |
| Per task | Original query ID, report path, SHA-256, completion status |
| Provenance | Original export or accessible report URL where available; citation-preservation notes |
| Permission | Confirmation that the submitted material may be shared for evaluation; any redistribution restrictions |

Keep the original outputs. Exclude API keys, tokens, cookies, personal account
identifiers, private session URLs, and unrelated local files. Do not include
predicted or desired rankings as evaluation inputs.

## 3. Validate, evaluate, and integrate

Maintainers check query coverage, identities, report completeness, citations,
permissions, and hashes before binding the inputs to a new evaluation cohort.
Evaluation then uses the frozen pointwise rubrics, pairwise guidelines, judging
configuration, bidirectional comparisons, and aggregation protocol.

The current reference leaderboard uses GPT-5.5 with medium reasoning for judging,
and deepseek-v4.1-flash with reasoning disabled for external verification. It uses
all within-query report pairs. The sparse-entry study is a separate retrospective
experiment, not an automatically interchangeable leaderboard protocol.

Scores use a 0–100 scale with weights of 30% Responsiveness, 30% Evidence, 10%
Reasoning, 10% Synthesis, and 20% Readability; queries receive equal weight.
Scores depend on the comparison pool. New systems must be evaluated and aggregated
consistently in an explicitly identified expanded cohort. Do not append an
independently computed score to the existing nine-system snapshot.

Publish a new snapshot only after validation and release approval, with model and
harness identities, task coverage, judging settings, cohort definition, dimension
scores, overall scores, and the underlying reproducible artifacts.

## Current software boundary

`evaluation/run.py` currently supports the bundled `main9` and `studies7` cohorts.
It can prepare, rerun, and aggregate those inputs; it is **not** a generic
new-system upload command. A new system requires maintainer integration and an
explicit cohort binding before execution. Online evaluation consumes provider
resources; no paid evaluation or report generation is triggered by this guide.
