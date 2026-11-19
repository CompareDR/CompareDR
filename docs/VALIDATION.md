# Validation and distribution scope

Checked on 16 November 2026 with Python 3.11.15, NumPy 2.4.6 and SciPy 1.17.1.

| Check | Result |
|---|---|
| Sealed reproduction package | 207 payload hashes verified; original 208-file package retained |
| Paper numerical reproduction | 16 tables; 44,897 checks passed; main ordinal model refitted |
| Offline numerical tests | 26 passed |
| Distribution/materials tests | 7 passed |
| Website tests, including JavaScript interactions | 17 passed |
| Main pipeline tests, fake HTTP only | 38 passed |
| Provider adapter tests, fake HTTP only | 7 passed |
| Full report preprocessing | 40 queries / 360 main9 reports and 40 / 280 studies7 reports |
| Human annotation binding | 80 pairs / 128 reports; labels and A/B mappings checked |
| Controlled materials | Selected 40 bases and 120 revisions; unchanged sealed files |
| Fresh sparse-entry regression | Selected trial refitted; archived-score difference below 1e-3; hidden outcomes excluded |

The root resource verifier checks report and routing hashes, exact cohort counts,
human label bindings and documentation links. The private assembly audit additionally
checks every copied report against its original evaluation manifest, confirms
unchanged full-query strings, and compares human A/B pointwise scores with their
original pair mapping. Private workstation paths are not distributed.

Source code changes are limited to packaging and deployment interfaces, cohort-aware
entry, final-weight diagnostics, and the corresponding tests. Original code hashes
are recorded separately from distributed hashes. Search providers and API credentials
are external configuration; no live paid model call was made during packaging.

The privacy audit scans the Git payload for workstation paths, internal endpoints,
session URLs, known secret/key formats, private keys and application-ID artifacts.
It reports filenames and line numbers, not matching secret values. This is a scoped
scan, not a mathematical guarantee that arbitrary sensitive data cannot exist.
Temporary caches, runtime outputs and Git authentication material are excluded.

This validates resource integrity and numerical reproduction, not every empirical
claim, annotation quality, live provider compatibility, or redistribution permission.
The three controlled-study tables use the author-confirmed selected labels. Online
baseline services were not rerun, and the 4,200-fit sparse study was not fully
reoptimized during this packaging check; all archived trials were used in the table
replay. Licensing approval and public deployment remain separate gates.

## Leaderboard integration — 17 November 2026

The homepage, standalone leaderboard, repository leaderboard, and marked README
summary now share the manuscript-aligned result data. All 21 website regression
tests pass, including clean rebuilding, exported full-precision scores, static
HTML rows, shared sorting, and local links. Local Chromium checks cover 1440-pixel
desktop and 390-pixel mobile widths, both sorting directions, and the no-JavaScript
ranking. Screenshots were visually reviewed; no page-level overflow or JavaScript
errors were observed. Tables remain horizontally scrollable on narrow screens.

Scores, report collections, annotation files, manuscript source, and sealed
reproduction inputs were not changed. The resource verifier still binds 360 main9
reports, 280 studies7 reports, and 80 human-labeled pairs. Participation instructions
describe maintainer-mediated intake; no public upload service, hosted deployment,
or automatic acceptance of new scores has been enabled.

The GitHub system-submission form is supplied with a downloadable query-only ZIP,
a 40-record manifest template, and an offline format checker. Nine intake tests
pass: complete and failed-task handling, IDs, hashes, pinned queries, safe paths,
required metadata, and deterministic packaging. The form definition was checked
against GitHub's documented YAML schema. The connected GitHub integration cannot
read this private repository, so authenticated form rendering was not verified;
source synchronization uses the repository's existing Git transport. No test issue
or submission was created.

### Full-dimensional repository homepage correction

The README's overall-only summary has been replaced with the same complete table
as `LEADERBOARD.md`: nine systems, five dimensions, and overall score. The two
Markdown entry points share one renderer. Missing, duplicate, or reversed README
markers now stop the build. The resource guide also links the leaderboard,
full-precision exports, submission form, package format, and template ZIP.

All 23 website tests pass. Independent column and value checks cover all 54
displayed score cells in each Markdown/HTML table, alongside existing CSV/JSON,
manuscript, build, and interaction regressions. The sync audit binds the two
repository documents as well as the website artifacts. This is a presentation
correction only: report outputs, numerical results, paper source, and the frozen
seven-system studies are unchanged.
