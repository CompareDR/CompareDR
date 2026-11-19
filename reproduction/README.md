# CompareDR: offline reproduction package

Offline numerical reproduction for the CompareDR manuscript. The nine-system
leaderboard includes GPT-6 and LongCat-DeepResearch. The manuscript and input
checksums are recorded in `MANUSCRIPT_VERSION.json` and `offline/INPUT_HASHES.json`.
This package does not imply approval for public redistribution.

## Run

Use Python 3.11 or later with the pinned dependencies in `offline/requirements.txt`.
From this directory:

```bash
python -m pip install -r offline/requirements.txt
python -B verify_materials.py
python -B verify_package.py
python -B offline/reproduce.py --output ../comparedr_replay
python -B -m unittest -v test_package
cd offline
python -B -m unittest -v test_reproduce
```

Dependency installation may require network access; the replay itself is offline.
Choose a new results directory outside this package each time. Computation is offline, without model
calls or API credentials. Installing dependencies, if needed, is a separate step.
Run `verify_package.py` before generating additional files in this directory;
it checks the exact delivered inventory and rejects unlisted files.

## Contents

- `offline/`: code, frozen numerical inputs, paper table references and input hashes.
- `materials/controlled_revisions/`: 40 base reports and 120 corresponding revisions,
  with one selected version for each item.
- `offline/data/controlled_selected_packet.json`: author-confirmed labels, target
  dimensions and exact report hashes.
- `materials/MANIFEST.json`: report paths and SHA-256 checksums.
- `materials/REPORT_ORIGIN.json`: explicit base-to-revision records, with
  experiment-scoped IDs, original system attribution and exact body hashes.
- `materials/CONTROLLED_PROTOCOL.json`: the manuscript-aligned revision procedure.
- `TABLE_MAP.json`: manuscript table labels and reproduced scope.
- `VALIDATION.md`: verification results and limitations.

Evaluation-input identities were checked byte-for-byte against the selected
reports. For distribution, tracking parameters are removed from citation URLs;
all other report text and all labels remain unchanged. `sha256` records the
original evaluation identity and `file_sha256` records distributed report bytes.
`materials/DISTRIBUTION_TRANSFORMS.json` documents these limited transformations,
including citation-link normalization in the benchmark inputs.
As described in the manuscript, three human reviewers independently assess the
editing plans and reconcile them by majority judgment. Codex Astra implements the
agreed plans. Subsequent human review compares the revisions with their base
reports and confirms quality directions and target dimensions. The retained labels
refer to this final human-reviewed version, not an intermediate construction stage.

Report IDs are scoped to each experiment. The included bodies are the actual
controlled-study bases; they are not replaced by main-table reports.
Use `REPORT_ORIGIN.json` and SHA-256 for exact matching.
The total-score and threshold comparisons use 119 common items; the target-dimension
comparison uses 123 judgments from all 120 revisions. P049/equivalent lacks a source
protocol score and is excluded only from the common-method comparison.

## Reproduction boundary

All 16 numerical tables are checked at the manuscript's displayed precision.
The nine-system main table is refitted from criterion-level judgments. Human
agreement, controlled revisions and judge comparisons are recomputed from frozen
scores or predictions. Sparse-entry statistics are recomputed from 4,200 archived
fits, without rerunning those optimizations. No new annotation or model study is
performed. Controlled thresholds are within-set calibration, not held-out results.

See `offline/README.md` for formulas, denominators and data descriptions. The
`expected_*` inputs are regression checks, not replacement calculation outputs.
The frozen LaTeX is a numerical reference, not a complete standalone paper project.

## Before publication

Code licensing, third-party data permissions, report privacy and redistribution
rights require author review. The online evaluator, editable figure sources and
full evidence-retrieval pipeline are outside this offline package. No license
grant or publication approval is implied by inclusion here.

`PRIVACY_CHECK.md` records the package privacy/security screening. It does not
grant redistribution rights or claim that automated screening proves universal
absence of sensitive material.
