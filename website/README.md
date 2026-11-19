# CompareDR website package

Local preparation only; no deployment or public address is configured.
The numerical results, system names and title remain synchronized with the saved
16 November 2026 manuscript. Author order, name capitalization and affiliations
are presentation metadata in `site_metadata.json`, following the owner's latest
confirmed list. The current manuscript source, PDF metadata and both sites use
the same order and affiliation numbering. The historical numerical reference
in `reproduction/offline/paper/` remains frozen. For the current paper and
its asset hashes, see [the release snapshot](manuscript/source/PAPER_MANIFEST.json).

The 18 November presentation update retains the blue/white identity and the
baseline stylesheet, with layout changes isolated in `templates/project.css`:

- Authors, affiliations and contribution notes occupy one collapsed-by-default
  `Authors & affiliations` disclosure; keyboard and no-JavaScript access work
  through native HTML details/summary.
- The framework is the original `../docs/assets/framework.png`, with a vector
  PDF link. Both copies are checked byte-for-byte, not redrawn.
- The task viewer shows all 40 original queries, one concrete pointwise and one
  pairwise example per task, scoring anchors and scope. Visible task labels use
  fixed numbers 1–40 plus titles; language filtering preserves those numbers.
  Search accepts task numbers, titles and original text. Per-task source badges,
  raw identifiers and the source filter are omitted from the interface, while
  underlying identifiers, resource links and overall source attribution remain.
- Six resource groups distinguish evaluator code, offline experiments, main9
  reports, studies7 reports, criteria/annotations, and new-system participation.
- A manuscript BibTeX entry can be copied or downloaded. Unconfirmed paper/arXiv
  URLs remain explicitly unavailable; existing repository links require access.

No deployment, repository push, visibility change or public upload service is
part of this update. Baseline charts, queries, criteria, scores and study inputs
are unchanged. See `REVIEW_20261118.md` for scope and verification.

## Build and verify offline

Python 3.11 or later is sufficient; no third-party packages or model calls are used.
Build from the complete repository, including `docs/assets`, resource targets
and `website/site_metadata.json`: the submission-template builder reads
`../data/evaluation/main9/rubrics/` and uses `../submissions/` to package only the
original queries, metadata template, documentation, and offline format checker.
The optional JavaScript interaction unit test also uses Node.js when available
on PATH (or through `NODE_BINARY`); otherwise it is explicitly reported as skipped.

```
python -B sync_comparedr.py
python -B -m unittest -v test_website_public
```

Open `dist/index.html` directly, or serve `dist` using a local static web server.
`dist` is the complete static website payload. The separate site ZIP contains only
that payload; the project ZIP also includes the builder, tests and frozen inputs.

`dist/leaderboard.html` is the standalone leaderboard, linked from the homepage.
It shows all nine systems and five dimensions, uses full-precision sorting, and
includes a new-system participation section. Both pages include static result
rows, so the ranking remains readable with JavaScript disabled. The original
project stylesheet is unchanged; standalone layout additions are isolated in
`templates/leaderboard.css`, and shared presentation updates in
`templates/project.css`. Generated HTML includes content-hash query versions
for scripts and stylesheets to avoid mixing current markup with cached code.

The build also generates the repository's `../LEADERBOARD.md`, the shared HTML
table, CSV scores, and `dist/leaderboard.json` (scores with protocol metadata).
It updates the marked full-dimensional leaderboard block in `../README.md` and
refreshes `PACKAGE_HASHES.json`; no unrelated README content is rewritten. Both
repository tables use the same renderer. Missing or duplicate README markers
stop the build rather than silently leaving an outdated table.
Do not manually edit generated score cells. `participation.md` is copied into
`dist/` for download. The current evaluator CLI supports the two bundled cohorts;
new-system intake requires maintainer integration, not just an uploaded score.
The participation section links to the GitHub issue form and offers
`submission-template.zip` and `submission-format.md`. The form is defined in
`../.github/ISSUE_TEMPLATE/submit-system.yml`; sign in to GitHub to submit an issue.

`manuscript/source/PAPER_MANIFEST.json` binds the source snapshot to the manuscript
PDF. `manuscript/SYNC_AUDIT.json` records generated asset hashes. Stylesheet and
domain-chart baselines are in `baseline/assets`.

Downloads include 40 queries, 80 selected criterion examples, the leaderboard and
displayed experimental results, not every criterion or all report bodies. The
independent offline reproduction package contains additional frozen inputs.
One query citation URL has a search-tracking parameter removed, matching the
offline code package. Its substantive query text is unchanged; before/after hashes
and parameter counts are recorded in `manuscript/DISTRIBUTION_TRANSFORMS.json`.
Public paper and arXiv URLs remain unset until confirmed. Code/data links point
to the CompareDR organization repository. See the root LICENSE, DATA_LICENSE.md,
and THIRD_PARTY_NOTICES.md for the applicable license scopes.
