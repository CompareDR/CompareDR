# Experiments: code, inputs and outputs

```bash
# From repository root; new output directory; no API calls.
python -B experiments/run.py --out outputs/paper_replay
```

This invokes the sealed implementation, produces `RESULTS.json` and `AUDIT.json`,
refits the main ordinal model and checks all 16 tables against the manuscript.

## Table-to-code map

Paths below are under `reproduction/offline/` unless stated otherwise.

| Paper result | Computation | Frozen inputs |
|---|---|---|
| Source inventory; rubric distribution | `reproduce.py:benchmark` | `data/benchmark.json`, `data/human80.json` |
| Nine-system main table | `reproduce.py:main_scores`, `frozen_ordinal.py` | `data/main_judgments.json`, `data/expected_main.json` |
| Human agreement | `reproduce.py:human` | `data/human80.json` (scores, native predictions, selected labels) |
| Component ablations | `reproduce.py:human` | Same 80 matched pairs; B0/A4/A5/A3/SUMMARY scores |
| Controlled response, thresholds, dimensions | `remaining_tables.py` | `data/controlled_selected_packet.json`, `data/controlled_native_scores.json`; 160 texts under `reproduction/materials/` |
| Judge selection, robustness, stability | `reproduce.py:judges` | `data/cross_judge.json`; GPT-5.5 reference |
| Repeated-judge pilot | `reproduce.py:pilot` | `data/pilot_items.json` |
| Token accounting | `reproduce.py:usage` | `data/usage_ledger.json` |
| New-system entry | `reproduce.py:sparse`; fresh refit: `experiments/sparse_entry.py` | `data/sparse_trials.json`, `data/opponent_sampling.json`; added judgments/initializations under `data/results/` |
| Seven-system appendix table | `reproduce.py:seven` | `data/seven_ordinal_source.json` |
| Query characteristics | `remaining_tables.py` | `data/query_characteristics.json` |

Machine-readable table labels are in [`TABLE_MAP.json`](../reproduction/TABLE_MAP.json).
Reports are at [`data/reports/`](../data/reports/); human A/B report bindings are at
[`data/annotations/`](../data/annotations/). Never attach a label to a different
cohort's report with the same ID.

## Refit sparse new-system entry

```bash
# R1 held out, two opponents/query, first fixed trial, IPW objective.
python -B experiments/sparse_entry.py --out outputs/sparse_trial
# 7 systems × 3 budgets × 100 designs × 2 methods = 4,200 fits.
python -B experiments/sparse_entry.py --all --out outputs/sparse_all
```

Each trial uses the supplied opponent design and old-system-only initialization.
Unselected new-system outcomes cannot enter the observations or weights. The
network and thresholds are jointly refitted. Hidden-label exclusion is tested;
trial means are compared against archived fits within 1e-3 score points, the
original optimizer-regression tolerance. The paper replay summarizes all 4,200
archived fits without rerunning them.

## Interpretation

- Human agreement uses 80 matched comparisons, not 360 independent human labels.
- Component ablations retain GPT-5.5; cross-judge comparisons use GPT-5.5 as the
  reference. deepseek-v4.1-flash is not substituted into every study.
- Controlled comparisons use 119 common items; dimension analysis uses all 120
  revisions / 123 targets. Threshold maxima are within-set, not held-out results.
- Token reductions replay recorded dependencies, not money or fresh elapsed time.
  Missing usage is not free.
- The main evaluator generates PT/PW decisions. Table reproduction uses supplied
  frozen baseline decisions/scores, not fresh runs of every third-party service
  or research-system harness.
