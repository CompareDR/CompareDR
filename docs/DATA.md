# Reports, criteria and annotation identities

| Resource | Coverage | Intended use |
|---|---:|---|
| `data/reports/main9/` | 40 × 9 = 360 | Final main leaderboard |
| `data/reports/studies7/` | 40 × 7 = 280 | Seven-system result, human-pair bindings and sampling studies |
| `reproduction/materials/controlled_revisions/` | 40 bases + 120 variants | Controlled-change study; own frozen identities |

Main9 uses R1/R2/R3/R4/R5/R6/R7/R9/R10. Studies7 uses R1–R7. R8 is not part of
these cohorts; IDs are not renumbered. Each manifest lists the system name.
There are 40 shared query identities: DRB-I 6, DRB-II 22, ResearchRubrics 12;
20 Chinese and 20 English queries.

## Report manifest

Each item contains `query_id`, `report_id`, `system`, a repository-relative `path`,
`evaluation_sha256` (original evaluated report), `file_sha256` (distributed file),
and counts of `removed_tracking_parameters`. Known URL tracking parameters are
removed deterministically; prose is not rewritten, translated or regenerated.
Both hashes are retained because this operation can change bytes. Query strings,
including prohibited-source clauses, are preserved exactly in the rubric files.
Routing hashes bind the distributed JSON-serialized rubric files.

## Human preferences

[`human_preferences.json`](../data/annotations/human_preferences.json) has 80 pairs
covering 128 distinct studies7 reports. `sides.A` and `sides.B` each bind a report
ID, path and both hashes. Labels cover `overall`, `D1`, `D2`, `D3`, `D4`, and
`D5_D6`, with values `A`, `tie`, or `B`. A is a presented side, not the better
system. Pair identities and orientation are checked against experiment mappings;
labels match the paper's frozen `human80.json`. Annotator identities are omitted.

## Controlled revisions

Texts are at `reproduction/materials/controlled_revisions/<case>/`: `base.md`,
`improve.md`, `degrade.md`, and `equivalent.md`. The selected packet and materials
manifest bind their identities. The procedure is three reviewers' suggestions
with majority decisions, Codex implementation, then one human check of consistency
with the selected instructions. No discarded review packets are included.

The four-method comparison uses 119 common revisions: P049/equivalent has no
source-protocol score. Target-dimension analysis retains 120 revisions and 123
target judgments. These denominators are not interchangeable.

## Numerical records

`reproduction/offline/data/main_judgments.json` stores main-table criterion scores
and restored-system AB/BA levels, with column definitions in the file.
`data/results/studies7_judgments.json` contains seven-system PT dimension means
and 13,566 physical PW levels. Six-dimension observation arrays use
`[query_index, system_i_index, system_j_index, level_plus_2]`; indices refer to
the accompanying `queries` and `systems` arrays.

There are 1,440 unordered main-cohort pairs and 840 study-cohort pairs. Each PW
guideline is judged in two physical orders: 23,256 items are not 23,256 independent
report pairs. See [experiment inputs](../experiments/README.md) for all score,
prediction, usage and sampling resources. Inclusion does not grant permission
to redistribute third-party content publicly.
