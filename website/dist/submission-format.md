# Submit a system to CompareDR

**[Open the system-submission form](https://github.com/CompareDR/CompareDR/issues/new?template=submit-system.yml)** ·
**[Download the template ZIP](submission-template.zip)**

The entry point is a public GitHub issue form, not an automated scoring service.
Sign in to GitHub to submit an issue. Maintainers review the
submitted package, coordinate evaluation, and update the leaderboard after the
new comparison cohort has been consistently aggregated.

## Package layout

Unzip the template and keep these paths. The template contains the exact 40 query
IDs and original task text, **without rubrics or answer keys**.
Keep `QUERY_ATTRIBUTION.md`, `LICENSE`, and `licenses/` with redistributed queries.
Article credits are for attribution, not additional sources for answering the tasks.

```text
submission/
  submission.json       # System configuration and 40 report records
  queries.json          # Frozen queries; do not edit
  reports/
    drb1_19.md           # One UTF-8 Markdown file per query ID
    ...                 # All 40 IDs are already listed in submission.json
  assets/               # Optional images referenced by local relative paths
  validate.py           # Offline format checker; Python 3.11+
  README.md
```

1. Fill in the `system` object in `submission.json`: `name`, `model`, `harness`,
   `reasoning`, `generation_start`, `generation_end`, and `settings`.
   Dates use `YYYY-MM-DD`; settings is a JSON object describing tools and budgets.
   Use `undisclosed` for genuinely unavailable model or reasoning settings, not
   for empty required fields. Do not include account information or API keys.
2. Put the final, unabridged reports in `reports/<query_id>.md`. Preserve headings,
   tables, math, citations, source links, and original language. Report content
   must be the system output, not a rewritten or synthesized replacement.
3. Set `permission_to_evaluate` to `true` only if authorized. Describe any
   redistribution restrictions in `redistribution_notes`; this is not a blanket
   license grant or agreement to public release.
4. From the unzipped directory, fill hashes and run the check:

```bash
python validate.py . --fill-hashes
python validate.py .
```

`--fill-hashes` updates only the per-report SHA-256 values in `submission.json`.
It does not change reports, statuses, queries, or settings. Review changes and
rerun the read-only check after any report edit.

5. ZIP the directory and attach it in the submission form, or provide a download
   link accessible to the maintainers. Paste the validator's JSON output into
   the form. Do not submit raw scores as a substitute for report files.

## Manifest fields

```json
{
  "schema_version": "1.0",
  "benchmark": "CompareDR",
  "query_set": "comparedr-40",
  "system": {
    "name": "Example Research System",
    "model": "Exact exposed model identifier",
    "harness": "Research harness name/version",
    "reasoning": "Exposed setting or undisclosed",
    "generation_start": "2026-11-17",
    "generation_end": "2026-11-17",
    "settings": {"tools": "Describe search and browsing tools", "budget": "Describe configured budget"}
  },
  "permission_to_evaluate": true,
  "redistribution_notes": "Describe permission scope or restrictions",
  "reports": [
    {
      "query_id": "drb1_19",
      "status": "completed",
      "report_path": "reports/drb1_19.md",
      "sha256": "Filled by validate.py --fill-hashes",
      "notes": "Optional citation-preservation or provenance notes"
    }
  ]
}
```

This is a one-record illustration, **not a valid complete manifest**. The ZIP's
manifest already contains all 40 required records. Do not change query IDs.

For a failed task, keep its record, set `status` to `failed`, set `report_path` and
`sha256` to `null`, and add a nonempty `error` explanation. Do not replace failure
with invented report text. The check exits **0** for a structurally complete
40-report package, **2** for a well-formed but incomplete package, and **1** for a
format or integrity error. Only complete collections are candidates for a full
leaderboard entry. Missing citation links produce review warnings, not fabricated
links or automatic factual-quality claims.

The checker validates IDs, file locations, UTF-8 text, nonempty reports, SHA-256,
dates, query-set integrity, and required metadata. It does not authenticate
generation provenance, certify report completeness or quality, guarantee absence
of every secret, grant redistribution rights, or execute any report or model call.

## After submission

Maintainers check the package and permissions, bind a new cohort, and arrange
judging. The packaged evaluator CLI currently reruns `main9` and `studies7`; it
does not yet automatically ingest arbitrary submissions. Existing leaderboard
scores are comparison-pool dependent, so a newly evaluated system is integrated
through a new cohort snapshot rather than appended with a standalone score.

Implementation: `submissions/validate.py`; template construction:
`submissions/build_template.py`; GitHub form:
`.github/ISSUE_TEMPLATE/submit-system.yml`. The format follows
[GitHub issue-form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms).
