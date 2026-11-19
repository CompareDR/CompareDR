# Final local project validation

- All 16 numerical tables match the frozen manuscript at its displayed precision.
- 44,897 numerical checks pass, with no failures.
- All 26 offline-reproduction tests and 7 distribution tests pass.
- The nine-system main table is refitted; its maximum absolute per-query error
  against the frozen scores is 0.0.
- Forty base reports, 120 revisions, 120 labels and 123 target-dimension judgments
  have explicit identity bindings and file-integrity checks.
- Numerical `RESULTS.json` is byte-identical before and after privacy normalization.

The current manuscript reference contains the nine-system GPT-6 and
LongCat-DeepResearch leaderboard. The table is refitted from 6,984 pointwise
ratings and 23,256 directional pairwise judgments. Report identities are checked
by query and SHA-256. The pinned numerical environment is Python 3.11 with
NumPy 2.4.6 and SciPy 1.17.1; other optimizer versions may differ numerically.

The human-preference, controlled-revision, judge-reliability and sparse-entry
results retain their fixed experimental inputs. No model calls were made.

## Controlled-revision procedure

The project follows the frozen manuscript: three human reviewers independently
assess the plans, disagreements are reconciled by majority judgment, Codex Astra
implements the plans, and subsequent human review compares revisions with their
bases and confirms direction and target dimensions. The manuscript does not give
the number of reviewers at that last stage. It is preserved without rewriting.

`materials/REPORT_ORIGIN.json` binds each revision to the actual base used in the
controlled study. Experiment-specific base identities are explicitly retained and checked
against the main-table manifest without rebinding labels.

## Distribution and scope

Only URL tracking parameters are removed from distributed content. Original
evaluation identities and distributed-file hashes are distinguished; no reports
are substituted and no labels or scores are changed. See `PRIVACY_CHECK.md`.

The ZIP is integrity-checked, extracted to an independent temporary directory,
screened again and used for a fresh offline replay. No original workspace or API
credentials are required. `PACKAGE_HASHES.json` verifies every delivered payload
file; the ZIP also has an external SHA-256 checksum.

This package reproduces archived numerical computations, not fresh model runs or
a new annotation study. Sparse-entry statistics summarize 4,200 frozen fits, not
new optimizations. Controlled thresholds are within-set calibration. Online
evaluation code, editable figure sources and redistribution/license clearance
remain outside this offline deliverable. Public redistribution requires separate author approval.
