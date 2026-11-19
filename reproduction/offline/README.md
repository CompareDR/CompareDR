# CompareDR offline numerical reproduction

This is a local staging package, not a published or license-cleared release.
It computes results from archived criterion judgments, report scores, preferences,
and sampling trials. It does not call an LLM, regenerate reports, or fetch evidence.

## Run

Tested with Python 3.11.15, NumPy 2.4.6, and SciPy 1.17.1. Install the pinned
dependencies into your own environment if needed. No API credentials are required.

```bash
python -m pip install -r requirements.txt
python reproduce.py --output ../outputs/my_replay
python -m unittest -v test_reproduce
```

Choose a new output directory for each run. Existing outputs are never overwritten.
`reproduce.py` resolves inputs relative to its own location, so this directory can
be copied or renamed independently of the original research workspace. Python
socket entry points are disabled by the runner; it invokes no external process.
Dependency installation is separate from reproduction.

`--skip-refit` is a diagnostic shortcut; it does not count as reproducing the main
system table. A full default run performs the frozen nine-system ordinal refit.

## Inputs and computation

| Input | Meaning | Recomputed result |
|---|---|---|
| `benchmark.json` | 40 tasks, 776 PT criteria, 323 PW guidelines, 360 report hashes | Source/language and criterion counts |
| `main_judgments.json` | 6,984 PT scores and 23,256 restored-identity AB/BA levels | Nine-system ordinal fit and scores |
| `human80.json` | Anonymous labels, frozen per-pair scores and native baseline predictions | Preference metrics, bootstrap intervals, component comparisons |
| `seven_ordinal_source.json` | Seven-system frozen per-query dimension scores | Separate seven-system appendix table |
| `cross_judge.json` | Per-report dimension scores and physical pairwise levels | ICC(A,1), rank correlation, score bias, order agreement and cycles |
| `pilot_items.json` | Per-item repeat/order comparison indicators | Ten-query pilot rates and matched denominators |
| `usage_ledger.json` | Selected response-level usage; no raw prompts or credentials | Recorded token totals; missing usage remains unknown |
| `sparse_trials.json` | 4,200 successful frozen trial fits | Error, exact rank agreement and dependency-ledger token savings |
| `opponent_sampling.json` | Selected opponents, decoded through reference-system IDs | Reusable sampling design; new trial refits are not implemented here |
| `controlled_selected_packet.json` | Selected 120 revision labels, targets, and report hashes | Common-119 comparison and target-dimension identity mapping |
| `controlled_native_scores.json` | Archived candidate/base scores for four methods | Reconstruct differences; exhaustive absolute/percentage threshold search |
| `query_characteristics.json` | 40 query-matched classification records | Breadth, depth, and exploratory-scope distributions |

`frozen_ordinal.py` is copied byte-for-byte from the source used for the paper's
nine-system fit. It intentionally retains the 40-query shape, five ordinal levels,
regularization .002, initialization, optimizer and numerical checks.

Input hashes are verified before and after the calculation. `expected_*` files
are regression references, not replacement outputs. Paper rows are checked
against the frozen LaTeX source at its displayed precision. The main refit is
also compared with the archived full-precision per-query scores (tolerance 1e-6).

## Interpretation

- PT is converted by `(score - 1) * 25`; absent channels are not zero-filled.
- PT/PW are averaged where available; organization/expression are merged as
  Readability. Five-category weights are 30/30/10/10/20. Query weights are equal.
- Human preference prediction uses `abs(A - B) < 1` for a tie. Each component
  renormalizes over its actually covered dimensions. The paired sample has 80
  comparisons; the complete seven-system network is a different analysis.
- Query-cluster bootstrap uses 10,000 source-stratified samples and seed 20260923.
- Sparse-entry reproduction summarizes frozen fits, not a fresh online entry run.
  Token savings are neither currency savings nor measured wall-clock savings.
- Controlled revisions use the author-confirmed matching packet. The common
  comparison excludes only P049/equivalent (missing source score); dimension
  comparison retains all 120 revisions and 123 judgments.
- Threshold search enumerates prediction regimes, optimizing ACC and macro-F1
  separately; ties use the other metric, then the smaller boundary. Displayed
  representative thresholds are checked to attain the optimum. These are
  within-set calibration results, not held-out accuracy.
- Equivalent revisions use the union of the two corresponding changed targets,
  deduplicated before scoring. Targets are never selected from score changes.

## Outputs

`RESULTS.json` contains newly calculated tables and diagnostics. `AUDIT.json`
records input checks, numerical regressions, runtime and library versions. A
passing run validates the implemented computations, **not all paper claims** or
redistribution permission. Consult the top-level artifact map and release gates.

No license grant is implied by inclusion in this local preparation directory.
